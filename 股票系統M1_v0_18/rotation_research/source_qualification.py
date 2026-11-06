"""Independent, offline source qualification. Never writes prior action/P1-7 outputs."""
from copy import deepcopy
from datetime import date,datetime
from pathlib import Path
import csv
import hashlib
import json
from urllib.parse import urlsplit
from graph_core.core import fingerprint,number
from .action_sources import ROOT,HERE,dump,iso
from .action_ledger import days,replay
from .action_study import verified_quotes,candidate_input
from .source_capture import OUT

START='2025-07-01'
END='2026-10-16'


def months(start,end):
    a,b=date.fromisoformat(start),date.fromisoformat(end)
    if a>b:raise ValueError('Reversed calendar window')
    y,m=a.year,a.month;result=[]
    while (y,m)<=(b.year,b.month):
        result.append(f'{y}{m:02d}');y,m=(y+1,1) if m==12 else (y,m+1)
    return result


def load_capture(name):
    meta=json.loads((OUT/'raw'/f'{name}.meta.json').read_text())
    if meta['status']!='CAPTURED':raise ValueError('Source failed, not an empty report: '+name)
    if meta.get('http')!=200 or any(urlsplit(meta[k]).netloc!='www.twse.com.tw' for k in ('url','final_url')):raise ValueError('Unverified official response origin')
    path=OUT/'raw'/f'{name}.response';raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=meta['sha256'] or len(raw)!=meta['bytes']:raise ValueError('Capture fingerprint mismatch')
    source=dict(path=str(path.relative_to(ROOT)),url=meta['url'],sha256=meta['sha256'],captured_at=meta['attempted_at'],kind='OFFICIAL_ARCHIVE',
                historical_publication_time='NOT_AUTHENTICATED_RETROSPECTIVE_CAPTURE')
    return json.loads(raw),source


def calendar_from_reports(reports,start,end):
    """Use official full monthly market rows, not weekday-minus-holiday inference."""
    expected=months(start,end)
    if set(reports)!=set(expected):raise ValueError('All and only requested month reports required')
    sessions={};sources={}
    for key in expected:
        data,source=reports[key];sid='market-'+key;sources[sid]=deepcopy(source)
        if datetime.fromisoformat(source['captured_at']).date()<=date.fromisoformat(end):raise ValueError('Capture must be after the completed calendar endpoint')
        if data.get('stat')!='OK' or data.get('date')!=key+'01':raise ValueError('Wrong month/status')
        if data.get('fields',[])[:4]!=['日期','成交股數','成交金額','成交筆數'] or not data.get('data'):raise ValueError('Unknown/empty market report')
        ds=[]
        for idx,row in enumerate(data['data']):
            when=iso(row[0],True)
            if when[:7].replace('-','')!=key:raise ValueError('Out-of-month row')
            if len(row)!=len(data['fields']):raise ValueError('Invalid market row shape')
            ds.append(when)
            if start<=when<=end:
                if any(number(row[i].replace(',',''))<=0 for i in (1,2,3)):raise ValueError('Invalid market totals')
                sessions[when]=dict(source_id=sid,locator=f'data[{idx}][0]',raw_date=row[0])
        if ds!=sorted(set(ds)):raise ValueError('Duplicate/unsorted official dates')
    # The provided reports are the exchange's observed session register for this window.
    # This never certifies broker settlement dates, historic publication, other exchanges, or other years.
    calendar=[dict(date=d,trading=d in sessions,source_ids=[sessions[d]['source_id']] if d in sessions else ['market-'+d[:7].replace('-','')],
                   observation='OFFICIAL_REPORTED_MARKET_SESSION' if d in sessions else 'NO_SESSION_IN_COMPLETE_OFFICIAL_MONTH_REPORT') for d in days(start,end)]
    result=dict(schema='rotation-observed-calendar/0.1',exchange='TWSE',start=start,end=end,
        qualification='VERIFIED_OFFICIAL_REPORTED_SESSIONS_FOR_WINDOW',calendar=calendar,sessions=sessions,sources=sources,
        trading_dates=len(sessions),calendar_days=len(calendar),settlement_calendar='NOT_VERIFIED_NOT_INFERRED_T_PLUS_2',
        historical_signal_eligible=False,publication_time='NOT_AUTHENTICATED',scope='ONLY_THIS_EXCHANGE_AND_WINDOW')
    result['id']=fingerprint(result);return result


def build_calendar():
    return calendar_from_reports({m:load_capture('market-'+m) for m in months(START,END)},START,END)


def action_source_audit(catalog):
    result=dict(schema='rotation-action-source-audit/0.1',start=START,end=END,
        original_catalog_id=fingerprint(catalog),event_components_unchanged=deepcopy(catalog['events']),
        complete_corporate_action_coverage=False,primary_pressure_id=None,observations=[])
    for name,scope in [('reduction-notices','CURRENT_FORWARD_NOTICES_NOT_HISTORICAL_REGISTER'),
                       ('shares-change','FILING_PROCESS_REGISTER_NOT_ALL_COMPLETED_CORPORATE_ACTIONS')]:
        payload,source=load_capture(name)
        if payload.get('stat',payload.get('status','')).lower()!='ok' or not payload.get('fields') or not isinstance(payload.get('data'),list):raise ValueError('Unrecognized action source')
        matches=[dict(row_index=i,raw_row=r) for i,r in enumerate(payload['data']) if any(str(v).strip() in ('1101','2884') for v in r)]
        result['observations'].append(dict(name=name,scope=scope,source=source,fields=payload['fields'],rows=len(payload['data']),
            target_rows=matches,no_target_rows_proves_no_events=False,notes=payload.get('notes',[])))
    failed=json.loads((OUT/'raw/reduction-resumptions.meta.json').read_text())
    # A future successful retry needs a new capture identity, changed prerequisite and a new producer decision.
    result['observations'].append(dict(name='reduction-resumptions',capture=failed,coverage='UNKNOWN_FAILED_REQUEST_NOT_ZERO_EVENTS'))
    result['gaps']=['FULL_CAPITAL_REDUCTION_AND_OTHER_ACTION_COVERAGE_NOT_VERIFIED',
        'EXRIGHT_CAPTURE_2026-07-25_TO_2026-10-16_MISSING_NO_PROHIBITED_RETRY',
        '2884_STOCK_RATIO_TRADABILITY_AND_FRACTIONS_UNKNOWN',
        'NET_DISTRIBUTIONS_AND_OPENING_CLAIMS_NOT_PUBLICLY_AUTHENTICATED']
    return result


def bind_observed_calendar(inp,calendar):
    if not calendar['start']<=inp['start']<inp['end']<=calendar['end']:raise ValueError('Calendar cannot extrapolate outside verified window')
    if calendar['qualification']!='VERIFIED_OFFICIAL_REPORTED_SESSIONS_FOR_WINDOW':raise ValueError('Calendar evidence not qualified')
    if calendar['id']!=fingerprint({k:v for k,v in calendar.items() if k!='id'}):raise ValueError('Calendar fingerprint mismatch')
    result=deepcopy(inp);result['sources'].update(deepcopy(calendar['sources']))
    result['calendar']=[deepcopy(r) for r in calendar['calendar'] if inp['start']<=r['date']<=inp['end']]
    result['qualification']['calendar']='VERIFIED_COMPLETE'
    result['calendar_evidence_id']=calendar['id']
    result['calendar_scope']='OFFICIAL_OBSERVED_TWSE_TRADING_SESSIONS_NOT_SETTLEMENT_OR_PUBLICATION'
    return result


def window_audit(old,catalog,manifest,calendar):
    design=json.loads((HERE/'generated/design.json').read_text());dates=[b['date'] for b in old['assets']['1101']['bars']];windows=[]
    for cutoff in design['cutoffs']:
        for a,b in [('1101','2884'),('2884','1101')]:
            for horizon in design['horizons']:
                i=dates.index(cutoff)
                if i+horizon>=len(dates):
                    windows.append(dict(A=a,B=b,start=cutoff,end=None,horizon=horizon,status='INSUFFICIENT_SAVED_FORWARD_ROWS'));continue
                end=dates[i+horizon];probe=bind_observed_calendar(candidate_input(old,catalog,manifest,cutoff,end,a),calendar)
                result=replay(probe)
                if result['daily'] or result['total_net_return'] is not None or 'CALENDAR_NOT_VERIFIED_COMPLETE' in result['refusal_reasons']:
                    raise AssertionError('Source qualification boundary violated')
                windows.append(dict(A=a,B=b,start=cutoff,end=end,horizon=horizon,status=result['status'],input_id=result['input_id'],
                    refusal_reasons=result['refusal_reasons'],calendar_qualified=True,
                    plans={p:dict(status='NOT_CALCULATED_UNQUALIFIED_ACTION_INPUT',total_net_return=None) for p in design['plans']}))
    return dict(schema='rotation-source-qualified-window-audit/0.1',calendar_id=calendar['id'],windows=windows,
        calendar_qualified_windows=sum(w['end'] is not None for w in windows),total_net_return_qualified_windows=0,
        six_plan_replay='NOT_RUN_NO_COMPLETE_EVENT_NET_DISTRIBUTION_OR_OPENING_CLAIMS',ranking=None)


def main():
    old,manifest=verified_quotes();catalog=json.loads((HERE/'action_data_20261022/events.json').read_text());cal=build_calendar()
    comparisons={}
    for code,asset in old['assets'].items():
        saved={b['date'] for b in asset['bars']};observed=set(cal['sessions'])
        comparisons[code]=dict(saved_dates=len(saved),official_market_dates=len(observed),missing_saved_rows=sorted(observed-saved),
            saved_dates_without_market_session=sorted(saved-observed),
            open_market_no_security_quote=[dict(date=b['date'],source_id=asset['source_id'],basis_id=asset['basis_id'],
                status='MARKET_OPEN_SECURITY_NO_QUOTE_CAUSE_UNKNOWN_NOT_IMPUTED') for b in asset['bars'] if b.get('missing') and b['date'] in observed])
        if saved!=observed:raise ValueError('Market/source calendar disagreement: keep source input unchanged')
    planned=[]
    for year in (2025,2026):
        p=HERE.parent/'pressure_chart/data/calendars-20261018'/f'TWSE_{year}.calendar.json';x=json.loads(p.read_text())
        raw=p.with_name(f'TWSE_{year}.raw.json');meta=json.loads(p.with_name(f'TWSE_{year}.meta.json').read_text())
        if hashlib.sha256(raw.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('Planned calendar original changed')
        planned.append(dict(year=year,path=str(p.relative_to(ROOT)),source_url=meta['url'],source_sha256=meta['sha256'],
            planned_closed_but_market_open=sorted(set(x['closed_dates'])&set(cal['sessions'])),
            weekday_no_market_row_not_in_planned=[r['date'] for r in cal['calendar'] if r['date'].startswith(str(year)) and not r['trading'] and date.fromisoformat(r['date']).weekday()<5 and r['date'] not in x['closed_dates']]))
    dump(OUT/'observed-calendar.json',cal);dump(OUT/'quote-calendar-comparison.json',dict(assets=comparisons,planned_calendar_crosscheck=planned))
    audit=window_audit(old,catalog,manifest,cal)
    dump(OUT/'action-source-audit.json',action_source_audit(catalog));dump(OUT/'window-qualification.json',audit)
    probe=bind_observed_calendar(candidate_input(old,catalog,manifest,'2026-06-30','2026-07-29','1101'),cal)
    dump(OUT/'real-input-probe.json',probe);dump(OUT/'real-input-refusal.json',replay(probe))
    # Empty lists in the prior input were probes, never evidence of no rights.
    requirements=dict(schema='rotation-entitlement-source-requirements/0.1',investor_identity_or_tax_profile=None,
        opening_acquisition_and_cum_rights_history=None,opening_cash_claims=None,opening_share_claims=None,
        cash_dividends=[dict(event_id=e['id'],code=e['code'],ex_date=e['ex_date'],scheduled_pay_date=e['pay_date'],
            sourced_gross_per_share=e['gross_per_share'],net_per_share=None,actual_received_amount=None,actual_received_at=None,
            net_requirement='BROKER_OR_ISSUER_NET_STATEMENT_OR_EXPLICIT_SOURCED_TAX_COST_MODEL_WITH_CONTEXT',source_status='NOT_AUTHENTICATED') for e in catalog['events'] if e['type']=='CASH_DIVIDEND'],
        stock_dividends=[dict(event_id=e['id'],code=e['code'],money_per_share=e['stock_dividend_money_per_share'],shares_per_share=None,
            par_value_at_event=None,tradable_date=None,fractional_treatment=None,source_status='NOT_AUTHENTICATED') for e in catalog['events'] if e['type']=='STOCK_DIVIDEND'],
        full_action_history_required=True,zero_is_not_default=True,total_net_return=None)
    dump(OUT/'entitlement-requirements.json',requirements)
    with (OUT/'calendar.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['date','official_twse_trading','1101_raw_close','1101_quote_status','2884_raw_close','2884_quote_status'])
        bs={c:{b['date']:b for b in v['bars']} for c,v in old['assets'].items()}
        for r in cal['calendar']:
            cells=[r['date'],str(r['trading']).lower()]
            for c in ('1101','2884'):
                b=bs[c].get(r['date']);cells.extend(['' if b is None or b['close'] is None else b['close'],
                    'NO_MARKET_SESSION' if not r['trading'] else 'OPEN_NO_SECURITY_QUOTE' if b is None or b.get('missing') else 'ORIGINAL_RAW_CLOSE'])
            w.writerow(cells)
    summary=dict(market_months=len(cal['sources']),official_trading_dates=cal['trading_dates'],calendar_days=cal['calendar_days'],
        original_quote_archives_rechecked=len(manifest),calendar_qualified_windows=audit['calendar_qualified_windows'],total_net_return_qualified_windows=audit['total_net_return_qualified_windows'],
        insufficient_forward_windows=sum(w['end'] is None for w in audit['windows']),security_no_quote_rows=sum(len(v['open_market_no_security_quote']) for v in comparisons.values()),
        original_engine_or_old_results_modified=False,new_strategy_replays=0,browser_runs=0,android='NOT_TESTED_NEW_BUILD')
    dump(OUT/'verification.json',summary);print(json.dumps(summary))


if __name__=='__main__':main()
