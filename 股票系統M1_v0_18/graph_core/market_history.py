"""Attach retained, provenance-checked history to the existing market Journal.

No historical website requests: provider-approved automation scope is unresolved.
This is an input adapter and batch coordinator, not a recognition engine.
"""
from collections import Counter
from copy import deepcopy
from decimal import Context,localcontext,ROUND_HALF_EVEN
import json
from pathlib import Path
import resource
import time
import inspect

from graph_core.market_daily import ROOT,outside,Journal,encode,digest
from graph_core.core import analyze,fingerprint
from graph_core_chart.build import input_for,PARENT_SHA256,HISTORY
from graph_core_chart.evidence import bind_input,validate_source_spec
from candle_region_chart.build import load_parent
from pressure_chart.history_adapter import validate_intake
from product_candidate.build import publish_immutable
from product_candidate.macd import macd
from graph_core.market_preview import source_segment_ma

HERE=Path(__file__).parent/'fm2_20261101'
VERSION='retained-market-history-adapter/0.2'


def checked_result(payload,as_of,expected):
    """Read only the supplied prefix under a fixed numerical environment."""
    with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999)):
        result=analyze(payload,as_of=as_of)
    if result!=expected:raise ValueError('Retained core result/source mismatch; no oracle rewriting')
    return result


def _load_retained():
    frozen=json.loads((HERE/'frozen.json').read_text())
    for item in frozen['files']:
        if item['path']=='graph_core/market_preview.py':continue  # authorized source-role display extension
        raw=(ROOT/item['path']).read_bytes()
        if len(raw)!=item['bytes'] or digest(raw)!=item['sha256']:raise ValueError('Frozen source changed: '+item['path'])
    # Reuses original strict monthly parsers and every retained response SHA.
    ledger=validate_intake(HISTORY);parent=load_parent()
    spec=json.loads((ROOT/'graph_core_chart/mg3_20261101/source-input-spec.json').read_text())
    validate_source_spec(spec,ROOT,PARENT_SHA256)
    return ledger,parent,spec


def load_retained():
    # The original monthly unit conversions also perform Decimal arithmetic;
    # guard the source adapter, not just the recognition call.
    with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999)):
        return _load_retained()


def run(root,parent_run,as_of='2026-10-16'):
    root=outside(root);start=time.monotonic();journal=Journal(root/'runs');reference=journal.read(parent_run)['value']
    ledger,parent,spec=load_retained()
    if as_of!='2026-10-16':raise ValueError('This retained source snapshot only supports its explicit common end date; no backfill guessed')
    signature=dict(version=VERSION,producer_sha256=digest(Path(__file__).read_bytes()),engine_sha256=digest((ROOT/'graph_core/core.py').read_bytes()),
                   ledger_sha256=digest(HISTORY.read_bytes()),numeric_parent_sha256=PARENT_SHA256,
                   indicator_glue_sha256=digest(inspect.getsource(source_segment_ma).encode()),reference=parent_run,as_of=as_of)
    identity='fm2-'+digest(encode(signature))
    try:
        saved=journal.read(identity)['value'];return dict(id=identity,reused=True,new_core_calls=0,summary=saved['summary'])
    except FileNotFoundError:pass
    histories=Journal(root/'histories');results=Journal(root/'results');outcomes=[];calls=0;known_dates=set()
    source_by_code={s['code']:s for s in parent['history_series']}
    ledger_by_code={s['code']:s for s in ledger['series']}
    checkpoints=Journal(root/'checkpoints')
    for member in reference['stocks']:
        row={k:deepcopy(member[k]) for k in ('code','name','market','identity','isin','cfi','listed_at','registry_present')}
        row.update(as_of=as_of,status='HISTORY_SOURCE_UNAVAILABLE',history_records=0,history_key=None,result_key=None,
            reason='No retained permitted history; no automated historical download authorization proved',historical_available_at='UNKNOWN',
            classification_quality='NOT_VALIDATED',primary_pressure_id=None,data_qualified=False,execution_model_qualified=False,
            historical_signal_eligible=False,policy_authorized=False,live_execution_authorized=False)
        checkpoint_key=identity+'-'+row['market']+'-'+row['code']
        try:
            prior=checkpoints.read(checkpoint_key)['value']
            if prior['source_signature']!=signature or prior['stock']['identity']!=row['identity']:raise ValueError('Checkpoint source/identity mismatch')
            cached=prior['stock']
            if cached.get('result_key'):
                saved=results.read(cached['result_key'])['value']
                original=json.loads((ROOT/f"graph_core_chart/output/mg3_20261101/core-{row['code']}-latest.json").read_text())
                if saved['result']!=original or cached['result_id']!=original['result_id']:raise ValueError('Checkpoint original result mismatch')
                h=histories.read(cached['history_key'])['value']
                if h['bars']!=saved['input']['bars']:raise ValueError('Checkpoint history missing or different')
                known_dates.update(b['date'] for b in h['bars'])
            outcomes.append(cached);continue
        except FileNotFoundError:
            # Only absence of the checkpoint itself permits work. A checkpoint
            # claiming a missing dependent result is not proof of no execution.
            if checkpoints.path(checkpoint_key).exists():
                row.update(status='CHECKPOINT_DEPENDENCY_MISSING',reason='Original checkpoint preserved; no automatic repair')
                outcomes.append(row);continue
        except Exception as e:
            row.update(status='CHECKPOINT_INVALID',reason=str(e));outcomes.append(row);continue
        if row['listed_at']>as_of:
            row.update(status='OUTSIDE_CURRENT_REFERENCE_LISTING_WINDOW',reason='Current reference lists a later listing; not a historical-universe certification')
        elif row['code'] in source_by_code:
            series=source_by_code[row['code']]
            try:
                if series['exchange']!=row['market']:raise ValueError('Historical market differs; no cross-market identity merge')
                frame=next(f for f in series['frames'] if f['as_of']==as_of);base=series['bases'][frame['chart_base']]
                payload=bind_input(input_for(series,frame),spec,row['code']);payload['bars']=[b for b in payload['bars'] if b['date']<=as_of]
                if payload['bars']!=ledger_by_code[row['code']]['candles']:raise ValueError('Retained parent candles differ from parsed monthly originals')
                expected=json.loads((ROOT/f"graph_core_chart/output/mg3_20261101/core-{row['code']}-latest.json").read_text())
                calls+=1;result=checked_result(payload,as_of,expected)
                hk='history-'+fingerprint(dict(bars=payload['bars'],basis_break_dates=payload['basis_break_dates'])).split(':')[1]
                histories.save(hk,dict(bars=payload['bars'],basis_break_dates=payload['basis_break_dates']))
                n=result['source_records'];retained_indicators=dict(macd=base['macd'][:n],moving_averages={k:v[:n] for k,v in base['moving_averages'].items()},
                    numeric_parent_sha256=PARENT_SHA256,role='EXACT_RETAINED_NUMERIC_PARENT_NOT_NEW_INDICATOR_RULE')
                resets=[i for i,b in enumerate(payload['bars']) if b['date'] in result['data_gaps']['basis_resets']]
                with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999)):
                    indicators=dict(macd=macd([b['close'] for b in payload['bars']],resets=resets),moving_averages=source_segment_ma(payload['bars'],resets),
                        role='FM2_SEGMENTED_INDICATORS_EXISTING_FORMULAS_NOT_RELABELED_PARENT',version='fm2-segment-indicators/0.1',
                        reset_dates=result['data_gaps']['basis_resets'],reference_numeric_parent_sha256=PARENT_SHA256)
                stored=dict(input=payload,result=result,indicators=indicators,retained_indicators=retained_indicators)
                rk='fm2-result-'+fingerprint(stored).split(':')[1];results.save(rk,stored)
                source=series['source'];units=sorted({r['source_volume_field'] for r in source['source_records']})
                row.update(status='ANALYZED_RETAINED_HISTORY',reason='Research core completed; no classification/strategy qualification promoted',history_records=n,
                    history_key=hk,result_key=rk,source_start=payload['bars'][0]['date'],source_end=payload['bars'][-1]['date'],
                    source_volume_field=units,volume_unit=source['volume_unit'],
                    history_source_provenance=dict(role='RETAINED_OFFICIAL_MONTHLY_NOT_NEW_BULK_NATIVE_FEED',source_id=source['id'],
                        source_volume_fields=units,volume_normalization=source['volume_normalization'],source_ledger_sha256=signature['ledger_sha256'],
                        monthly_originals=len(source['source_records']),corporate_action_comparability='UNVERIFIED',historical_available_at='UNKNOWN',
                        retained_source_gaps={k:deepcopy(ledger_by_code[row['code']][k]) for k in ('known_calendar_missing_dates','calendar_status','actions_coverage','historical_publication_timing')},
                        exact_native_share_precision=source['exchange']=='TWSE'),
                    result_id=result['result_id'],source_prefix_fingerprint=result['source_prefix_fingerprint'],
                    confirmed_pivots=len(result['pivots']),box_candidates=len(result['boxes']),stopped_boxes=sum(not b['usable_at_anchor'] for b in result['boxes']))
                known_dates.update(b['date'] for b in payload['bars'])
            except Exception as e:row.update(status='HISTORY_SOURCE_OR_CORE_FAILURE',reason=type(e).__name__+': '+str(e))
        outcomes.append(row)
        # Checkpoints use the original immutable Journal, so interruption loses
        # neither already verified stock results nor the source manifest.
        checkpoints.save(checkpoint_key,dict(batch=identity,source_signature=signature,stock=row))
    counts=dict(Counter(s['status'] for s in outcomes));n=len(outcomes)
    summary=dict(status='PARTIAL',as_of=as_of,expected=n,processed=n,expected_by_market=dict(Counter(s['market'] for s in outcomes)),
        terminal_counts=counts,actual_core_calls=calls,new_historical_dates_downloaded=0,retained_unique_dates=len(known_dates),
        history_bar_distribution=dict(Counter(str(s['history_records']) for s in outcomes)),all_known_members_have_terminal=n==len(reference['stocks']),
        universe_historical_qualification='UNKNOWN_CURRENT_FM1_REFERENCE_NOT_1016_HISTORICAL_UNIVERSE',historical_automation='BLOCKED_PROVIDER_APPROVED_SCOPE_NOT_PROVED',
        wall_seconds=time.monotonic()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        fixed_android_url='NOT_DEPLOYED',scheduling='NOT_ENABLED',storage_persistence='UNKNOWN')
    journal.save(identity,dict(version=VERSION,as_of=as_of,sources=signature,reference_current_run=parent_run,observed_sessions=sorted(known_dates),
        stocks=outcomes,summary=summary,current_FM1_head_unchanged=True,scope='RETAINED_HISTORY_COVERAGE_AUDIT_NOT_FULL_HISTORICAL_UNIVERSE'))
    return dict(id=identity,reused=False,new_core_calls=calls,summary=summary)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--reference-run',required=True);a=p.parse_args()
    print(json.dumps(run(a.root,a.reference_run),ensure_ascii=False,indent=2))
