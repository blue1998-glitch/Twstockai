"""Audit existing P1-7 windows without rerunning/reinterpreting old strategies.

Writes only action_data_20261022. No downloads, UI, or old-result overwrite.
"""
from copy import deepcopy
from pathlib import Path
import csv
from datetime import date,timedelta
import hashlib
import json
from graph_core.core import fingerprint,number
from .action_sources import HERE,ROOT,OUT,build_catalog,dump
from .action_ledger import days,replay
from .study import build_input


def verified_quotes():
    data=json.loads((HERE/'generated/input.json').read_text())
    rebuilt,manifest=build_input()  # Reuse existing exact archive reader, no old replay.
    if rebuilt!=data or manifest!=json.loads((HERE/'generated/sources.json').read_text()):
        raise ValueError('Existing input/archive mismatch; do not rewrite old artifacts')
    return data,manifest


def candidate_input(old,catalog,manifest,start,end,a):
    sources=deepcopy(catalog['sources'])
    for i,s in enumerate(manifest):sources['quote-'+str(i)]=dict(s,kind='OFFICIAL_ARCHIVE')
    observed={b['date'] for asset in old['assets'].values() for b in asset['bars']}
    return dict(schema='rotation-action-input/0.1',mode='RAW',start=start,end=end,
        sources=sources,assets={c:dict(source_id=v['source_id'],basis_id=v['basis_id'],
            quote_source_ids=['quote-'+str(i) for i,s in enumerate(manifest) if Path(s['path']).name.startswith(c+'_')],
            quotes={b['date']:b['close'] for b in v['bars'] if start<=b['date']<=end}) for c,v in old['assets'].items()},
        events=deepcopy(catalog['events']),coverage=deepcopy(catalog['coverage']),
        calendar=[dict(date=d,trading=d in observed,flag_qualification='SAVED_ROWS_ONLY_NOT_AUTHENTICATED') for d in days(start,end)],
        qualification=dict(calendar='MATCHED_SAVED_DATES_NOT_EXHAUSTIVE',opening_claims='UNKNOWN_NO_ACQUISITION_OR_ENTITLEMENT_HISTORY',
            net_distributions='UNKNOWN_INVESTOR_TAX_AND_PAYMENT',execution_costs='SCENARIO_DAILY_OHLC_NOT_ACTUAL_FILLS',
            investor_cashflows='NOT_AUTHENTICATED',historical_availability='RETROSPECTIVE_NOT_AUTHENTICATED'),
        opening=dict(cash=old['initial_cash'],shares={c:str(old['initial_shares']) if c==a else '0' for c in old['assets']},
                     cash_claims=[],share_claims=[]),
        fills=[],terminal_costs={k:old['execution'][k] for k in ('fee_rate','minimum_fee','sell_tax','slippage_bps')},
        scope='QUALIFICATION_PROBE_ONLY_NO_SIX_PLAN_REPLAY_OR_NEW_FILL_PATH',
        opening_note='Empty claim lists are NOT evidence of no existing rights; qualification UNKNOWN blocks replay')


def audit_windows(old,catalog,manifest):
    design=json.loads((HERE/'generated/design.json').read_text())
    dates=[b['date'] for b in next(iter(old['assets'].values()))['bars']];windows=[]
    for cutoff in design['cutoffs']:
        for a,b in [('1101','2884'),('2884','1101')]:
            for horizon in design['horizons']:
                i=dates.index(cutoff);base=dict(A=a,B=b,start=cutoff,horizon=horizon,
                    plans={p:dict(status='NOT_CALCULATED_UNQUALIFIED_INPUT',total_net_return=None) for p in design['plans']})
                if i+horizon>=len(dates):
                    windows.append(dict(base,end=None,status='INSUFFICIENT_SAVED_FORWARD_ROWS',refusal_reasons=['INSUFFICIENT_FORWARD_OBSERVATIONS']))
                    continue
                end=dates[i+horizon];inp=candidate_input(old,catalog,manifest,cutoff,end,a);r=replay(inp)
                if r['daily'] or r['total_net_return'] is not None:raise AssertionError('Unqualified actual source was calculated')
                missing=[dict(code=c,date=x['date']) for c,v in old['assets'].items() for x in v['bars'] if cutoff<=x['date']<=end and x.get('missing')]
                windows.append(dict(base,end=end,status=r['status'],refusal_reasons=r['refusal_reasons'],input_id=r['input_id'],
                    source_missing_quotes=missing,
                    events_in_window=[e['id'] for e in catalog['events'] if cutoff<e['ex_date']<=end],
                    ex_events_on_opening_close=[e['id'] for e in catalog['events'] if e['ex_date']==cutoff]))
    return dict(schema='rotation-action-window-audit/0.1',windows=windows,planned_windows=len(windows),
                source_price_windows=sum(w['end'] is not None for w in windows),
                total_net_return_qualified_windows=0,ranking=None,policy_authorized=False,
                historical_signal_eligible=False,primary_pressure_id=None,
                six_plan_replay='NOT_RUN_INSUFFICIENT_EVIDENCE_DO_NOT_REUSE_OLD_PRICE_ONLY_FILLS')


def gross_schedule_preview(old,catalog):
    """Known gross entitlements for explicit hypothetical holdings, NOT a net ledger."""
    previews=[]
    for e in catalog['events']:
        if e['type']!='CASH_DIVIDEND':continue
        asset=old['assets'][e['code']];bars={b['date']:b for b in asset['bars']}
        prior=max(d for d in bars if d<e['ex_date']);quantity=number(str(old['initial_shares']))
        gross=quantity*number(e['gross_per_share'])
        daily=[]
        for when in days(prior,e['pay_date']):
            after=when>=e['ex_date'];paid=when>=e['pay_date'];bar=bars.get(when)
            daily.append(dict(date=when,raw_close=None if bar is None else bar['close'],
                quote_status='NO_SAVED_ROW_NO_HOLIDAY_INFERENCE' if bar is None else ('SAVED_NULL_NO_QUOTE' if bar.get('missing') else 'ORIGINAL_RAW_CLOSE'),
                gross_dividend_receivable=str(gross if after and not paid else number('0')),
                issuer_scheduled_cumulative_gross_paid=str(gross if paid else number('0')),
                investor_actual_cash_received=None,available_net_cash=None,net_equity=None,total_net_return=None))
        previews.append(dict(event_id=e['id'],code=e['code'],source_id=asset['source_id'],basis_id=asset['basis_id'],
            entitled_shares_assumption=str(quantity),ownership_assumption='ENGINEERED_CONSTANT_PRIOR_CLOSE_HOLDING_NOT_USER_PORTFOLIO',
            ex_date=e['ex_date'],pay_date=e['pay_date'],gross_per_share=e['gross_per_share'],gross_entitlement=str(gross),
            eligibility='GROSS_ISSUER_SCHEDULE_PREVIEW_ONLY_NOT_TOTAL_OR_NET_RETURN',
            stock_or_other_actions_not_applied=True,actual_payment_confirmed=False,daily=daily))
    return dict(schema='rotation-gross-schedule-preview/0.1',previews=previews,total_net_return=None)


def main():
    OUT.mkdir(exist_ok=True);old,manifest=verified_quotes();catalog=build_catalog()
    if json.loads((OUT/'events.json').read_text())!=catalog:raise ValueError('Catalog drift; explicitly rebuild and inspect first')
    audit=audit_windows(old,catalog,manifest);preview=gross_schedule_preview(old,catalog)
    dump(OUT/'window-qualification.json',audit);dump(OUT/'gross-schedule-preview.json',preview)
    probe=candidate_input(old,catalog,manifest,'2026-06-30','2026-07-29','1101')
    dump(OUT/'real-input-probe.json',probe);dump(OUT/'real-input-refusal.json',replay(probe))
    # Deliberately engineered accounting cases; never inserted into actual source data.
    from .action_fixtures import fixture,event
    examples={}
    for name,kind in [('cash-net-withholding','CASH_DIVIDEND'),('stock-delivery','STOCK_DIVIDEND'),('capital-reduction','CAPITAL_REDUCTION')]:
        inp=fixture();event(inp,kind)
        if kind=='CASH_DIVIDEND':
            inp['assets']['A']['quotes'].update({d:'9' for d in inp['assets']['A']['quotes'] if d>inp['start']})
        if kind=='STOCK_DIVIDEND':inp['assets']['A']['quotes'][inp['start']]='11'
        examples[name]=dict(qualification='ENGINEERED_ACCOUNTING_ONLY_NOT_MARKET_DATA',input=inp,result=replay(inp))
    dump(OUT/'engineered-examples.json',examples)
    dump(OUT/'engineered-input.json',examples['cash-net-withholding']['input'])
    with (OUT/'engineered-daily-ledger.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,lineterminator='\n',fieldnames=['case','date','settled_cash','available_cash_strict','cash_receivable','purchase_payable','net_accrual_equity','shares','share_receivables'])
        writer.writeheader()
        for name,example in examples.items():
            for r in example['result']['daily']:
                writer.writerow({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r.get(k),(dict,list)) else name if k=='case' else r[k] for k in writer.fieldnames})
    verification=dict(original_price_archives_verified=len(manifest),original_input_equal_to_existing_reader=True,
        actual_catalog_components=len(catalog['events']),source_events_id=fingerprint(catalog),
        actual_price_windows_audited=audit['source_price_windows'],insufficient_forward_windows=audit['planned_windows']-audit['source_price_windows'],
        total_net_return_qualified_windows=0,new_strategy_replays=0,new_browser_or_android_runs=0,
        old_price_research_rerun=False,engineered_accounting_examples=len(examples))
    dump(OUT/'study-verification.json',verification);print(json.dumps(verification,ensure_ascii=False))


if __name__=='__main__':main()
