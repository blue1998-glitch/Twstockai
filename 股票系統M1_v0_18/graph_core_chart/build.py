"""Build a compact self-contained real-data research result chart."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from graph_core.core import analyze,fingerprint,trace_reference,number
from candle_region_chart.build import load_parent,PARENT_SHA256
from technical_chart.build import pack,unpack
from product_candidate.build import publish_immutable

NAME='M1_v019_graph_recognition_v01.html'
VERSION='graph-recognition-view/0.1'
HISTORY=ROOT/'pressure_chart/data/history-20261018/history-candidate.json'
AUDIT_FILES=['docs/visual-discussion/20261019_latest_close_anchor/boundary_review_1617.json',
 'docs/visual-discussion/20261019_major_pressure_hierarchy/user_review.json',
 'docs/visual-discussion/20261019_previous_box_pressure/reviewed_1635/user_review.json']


def input_for(series,frame):
    base=series['bases'][frame['chart_base']]
    return dict(schema_version='graph-recognition-input/0.1',context=dict(code=series['code'],exchange=series['exchange'],
        source_id=series['source']['id'],price_basis_id=frame['chart_base'],price_mode=series['price_mode'],volume_unit='SHARES_REPORTED',
        corporate_action_comparability='RAW_CROSS_YEAR_UNVERIFIED',source_kind='RETAINED_OFFICIAL_DAILY_OHLCV',historical_publication_timing='UNVERIFIED'),
        bars=deepcopy(base['bars']),basis_break_dates=[e['effective_date'] for e in base['known_events']])


def display_ids(result):
    boxes=result['boxes'];by_id={b['id']:b for b in boxes};front=[by_id[i] for i in result['comparison']['pareto_frontier_ids']];ids=[];reasons={}
    def keep(pool,key,title,reverse=False):
        if pool:
            b=sorted(pool,key=key,reverse=reverse)[0]
            if b['id'] not in ids:ids.append(b['id'])
            reasons.setdefault(b['id'],[]).append(title)
    keep(front,lambda b:b['duration_records'],'LONG_CONTEXT_DISPLAY_NOT_PRIMARY_RANK',True)
    keep(front,lambda b:number(b['pressure_distance_fraction']),'NEAREST_UPPER_BAND_DISPLAY_NOT_SIGNIFICANCE')
    keep(front,lambda b:b['turns'],'REPEATED_TURNS_DISPLAY',True)
    keep(boxes,lambda b:b['confirmed_at'],'LATEST_FORMED_DISPLAY',True)
    keep([b for b in boxes if b['usable_at_anchor'] and b['anchor_relation']=='ABOVE'],lambda b:b['duration_records'],'CROSSED_RANGE_CONTEXT_DISPLAY',True)
    return dict(ids=ids,reasons=reasons,qualification='PRESENTATION_DIVERSITY_ONLY_ALL_CANDIDATES_RETAINED_NO_UNIQUE_IMPORTANCE')


def audit(result,rows):
    reviews=[json.loads((ROOT.parent/p).read_text()) for p in AUDIT_FILES]
    boundary,major,previous=reviews
    if result['context']['code']!=boundary['code'] or result['as_of']!=boundary['analysis_as_of']:return None
    price=boundary['case_resolution']['preferred_representative']['high'];day=boundary['case_resolution']['preferred_representative']['date']
    actual=next(r for r in rows if r['date']==day)
    if actual['high']!=price:raise ValueError('Existing manual reference source mismatch')
    matched=[p for p in result['pivots'] if p['kind']=='HIGH' and day in p['source_dates'] and p['price']==price]
    exact=[b['id'] for b in result['boxes'] if (b['start'],b['source_end'])==(previous['start'],previous['end'])]
    first=next(i for i,r in enumerate(rows) if r['date']==day)
    local=[r for r in rows if previous['start']<=r['date']<=previous['end']]
    if len(local)!=previous['records'] or local[0]!=previous['start_ohlcv'] or local[-1]!=previous['end_ohlcv']:raise ValueError('Old manual case source changed')
    return dict(schema_version='graph-manual-case-audit/0.1',qualification='LATER_MANUAL_REVIEW_LOOKBACK_OUTSIDE_AUTOMATIC_INPUT_NOT_RECOGNITION_ACCURACY',
        core_input_manual_case_count=0,source_reviews=[dict(path=p,sha256=hashlib.sha256((ROOT.parent/p).read_bytes()).hexdigest()) for p in AUDIT_FILES],
        review_date=boundary['recorded_at'],as_of=result['as_of'],reference=dict(date=day,price=price,automatic_matches=matched,
            retrospective_close_path=trace_reference(rows,price,first)),
        previous_manual_box=dict(start=previous['start'],end=previous['end'],records=previous['records'],automatic_exact_interval_ids=exact,
            verdict='EXACT_INTERVAL_FOUND_NOT_GENERAL_APPROVAL' if exact else 'NO_EXACT_AUTOMATIC_INTERVAL_MATCH'),
        larger_manual_band=major['major_pressure_band'],
        larger_band_verdict='MONTH_ONLY_USER_CONTEXT_NOT_AN_AUTOMATIC_GROUND_TRUTH_INTERVAL',
        excluded_bar_source=next(r for r in rows if r['date']==boundary['case_resolution']['excluded_bar']['date']),
        auto_membership_approved=False,accuracy=None,core_usefulness='NOT_ESTABLISHED')


def selection(bundle,code,as_of):
    s=next(s for s in bundle['series'] if s['code']==code);f=next(f for f in s['results'] if f['as_of']==as_of);n=f['source_records']
    return dict(schema_version='graph-recognition-selection/0.1',view_version=VERSION,code=code,as_of=as_of,
        source=deepcopy(s['source']),source_frame_id=s['numeric_frame_ids'][as_of],source_prefix_fingerprint=f['source_prefix_fingerprint'],
        bars=deepcopy(s['bars'][:n]),macd=deepcopy(s['macd'][:n]),moving_averages={k:deepcopy(v[:n]) for k,v in s['moving_averages'].items()},
        core=deepcopy(f),manual_case_audit=deepcopy(s['manual_audits'].get(as_of)),
        classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED',physical_android='NOT_TESTED_NEW_BUILD')


def make(*,extra_dates=()):
    parent=load_parent();history=json.loads(HISTORY.read_text());allseries=[];oracles=[]
    for series in parent['history_series']:
        last=series['frames'][-1];base=series['bases'][last['chart_base']];bars=base['bars'];payload=input_for(series,last)
        # Price records are never sampled. Only expensive analysis snapshots are
        # explicitly selected; replay shows these computed dates, not every day.
        indices=set(range(119,len(bars),120))|set(range(max(0,len(bars)-5),len(bars)))
        indices|={i for i,r in enumerate(bars) if r['date'] in extra_dates};results=[];audits={};presentations={}
        for i in sorted(indices):
            result=analyze(payload,as_of=bars[i]['date']);results.append(result);presentations[result['as_of']]=display_ids(result)
            checked=audit(result,bars[:i+1])
            if checked:audits[result['as_of']]=checked
        source=next(s for s in history['series'] if s['code']==series['code'])
        allseries.append(dict(code=series['code'],exchange=series['exchange'],source=deepcopy(series['source']),
            price_basis_id=last['chart_base'],bars=deepcopy(bars),macd=deepcopy(base['macd']),moving_averages=deepcopy(base['moving_averages']),
            results=results,presentations=presentations,manual_audits=audits,numeric_frame_ids={r['as_of']:next(f['frame_id'] for f in series['frames'] if f['as_of']==r['as_of']) for r in results},
            source_gaps={k:deepcopy(source[k]) for k in ['known_calendar_missing_dates','calendar_status','actions_coverage','historical_publication_timing']},
            macd_parameters=deepcopy(series['macd_parameters'])))
    bundle=dict(schema_version='graph-recognition-chart-bundle/0.1',view_version=VERSION,series=allseries,
        immutable_numeric_parent_sha256=PARENT_SHA256,source_history_sha256=hashlib.sha256(HISTORY.read_bytes()).hexdigest(),
        sampling=dict(prices='ALL_RETAINED_ROWS_NO_SYNTHETIC_CANDLES',analysis='EVERY_120TH_RECORD_PLUS_LAST_5_AND_EXPLICIT_EXTRA_DATES',
                      replay='ONLY_PRECOMPUTED_ANALYSIS_DATES_NOT_ALL_HISTORICAL_DAYS'),physical_android='NOT_TESTED_NEW_BUILD')
    bundle['artifact_id']=fingerprint(bundle)
    for s in bundle['series']:
        for f in s['results']:oracles.append(dict(code=s['code'],as_of=f['as_of'],fingerprint=fingerprint(selection(bundle,s['code'],f['as_of']))))
    return bundle,dict(cases=oracles)


def render(bundle):
    here=Path(__file__).parent;raw=json.dumps(pack(bundle),ensure_ascii=False,separators=(',',':'),allow_nan=False)
    for char,escape in [('&','\\u0026'),('<','\\u003c'),('>','\\u003e'),('\u2028','\\u2028'),('\u2029','\\u2029')]:raw=raw.replace(char,escape)
    return (here/'template.html').read_text().replace('@@STYLE@@',(here/'viewer.css').read_text()).replace('@@DATA@@',raw).replace('@@SCRIPT@@',(here/'viewer.js').read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);p.add_argument('--as-of',action='append',default=[]);a=p.parse_args();out=Path(a.output_dir).resolve()
    if 'output' not in out.parts:raise ValueError('Separate immutable output leaf required')
    bundle,oracle=make(extra_dates=a.as_of)
    if unpack(pack(bundle))!=bundle:raise ValueError('Transport precision mismatch')
    files={NAME:render(bundle).encode(),'selection-oracle.json':json.dumps(oracle,ensure_ascii=False,indent=2).encode(),
        'build-verification.json':json.dumps(dict(status='PASS',source_records={s['code']:len(s['bars']) for s in bundle['series']},analysis_frames=len(oracle['cases']),
            numeric_parent_sha256=PARENT_SHA256,view_version=VERSION,physical_android='NOT_TESTED_NEW_BUILD'),ensure_ascii=False,indent=2).encode()}
    for s in bundle['series']:files[f"core-{s['code']}-latest.json"]=json.dumps(s['results'][-1],ensure_ascii=False,indent=2).encode()
    for name,raw in files.items():print(name,publish_immutable(out/name,raw),len(raw),hashlib.sha256(raw).hexdigest(),flush=True)


if __name__=='__main__':main()
