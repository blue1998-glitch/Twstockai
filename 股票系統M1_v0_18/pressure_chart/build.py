"""Additive pressure chart. Reads the immutable old chart and official intake.
New descriptive facts are computed OFFLINE; JS renders prepared values only.
"""
import argparse
from calendar import monthrange
from datetime import date
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from contracts import fingerprint
from product_candidate.build import publish_immutable
from technical_chart.build import unpack,pack,selection as original_selection
from pressure_chart.facts import frame_facts,reviewed_layer,VERSION as FACT_VERSION
from pressure_chart.history_adapter import validate_intake,series_from_intake,history_selection,followup

VERSION='pressure-chart-view/0.1';NAME='M1_v0_19_pressure_chart.html'


def load_original():
    html=ROOT/'technical_chart/generated/M1_v0_19_technical_chart.html'
    raw=html.read_bytes();expected=json.loads((ROOT/'technical_chart/validation_20261017/artifact-delivery-report.json').read_text())['source_html_sha256']
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Original chart fingerprint mismatch')
    match=re.search(r'<script type="application/json" id="payload">(.*?)</script>',raw.decode(),re.S)
    if not match:raise ValueError('Original embedded payload missing')
    return unpack(json.loads(match.group(1)))


def make(history_file,regions=()):
    old=load_original();payload=deepcopy(old)
    history=validate_intake(history_file)
    if history['schema_version']!='official-history-candidate/0.1':raise ValueError('Unsupported intake')
    # This explicit offline build imports verified captures into NEW RAW series,
    # while the old numeric bundle stays byte-value identical. Never DB writes.
    case=json.loads((ROOT.parent/'docs/visual-discussion/20261018_1101_user_reviewed_case.json').read_text())
    audit_path=Path(history_file).with_name('coverage-audit.json')
    audit=json.loads(audit_path.read_text()) if audit_path.exists() else None
    walls={};reviews={};followups={};new_series=[]
    for item in history['series']:
        if not item['candles']:continue
        s,e=series_from_intake(item,old['numbers']['series']);new_series.append(s);payload['evidence'][s['key']]=e
        payload['entry']['per_series_as_of'][s['key']]=s['available_end']
        payload['coverage'][s['key']]=dict(code=s['code'],exchange=s['exchange'],price_mode=s['price_mode'],source_id=s['source']['id'],
            first_date=s['available_start'],last_date=s['available_end'],bars=len(s['frames']),volume_unit=s['source']['volume_unit'],
            actions_coverage=s['coverage'],missing_ohlc_dates=[],missing_volume_dates=[],
            missing_supplied_calendar_dates=item['known_calendar_missing_dates'],unexpected_supplied_calendar_dates=None,
            calendar_scope=item['calendar_status'],source_kind='NEW_RAW_OFFICIAL_HISTORY_NOT_OLD_STRUCTURE')
        if audit:
            checked=next(c for c in audit['series'] if c['code']==s['code'])
            payload['coverage'][s['key']].update(missing_supplied_calendar_dates=checked['missing_price_bars_vs_reviewed_planned_calendar'],
                unexpected_supplied_calendar_dates=checked['unexpected_price_dates'],source_gap_audit=deepcopy(checked))
    for s in [*payload['numbers']['series'],*new_series]:
        walls[s['key']]=[];reviews[s['key']]=[]
        followups[s['key']]=[]
        detail_dates={f['as_of'] for i,f in enumerate(s['frames']) if i==len(s['frames'])-1 or s['frames'][i+1]['as_of'][:7]!=f['as_of'][:7]}
        for f,e in zip(s['frames'],payload['evidence'][s['key']]):
            rows=s['bases'][f['chart_base']]['bars'][:f['index']+1]
            walls[s['key']].append(frame_facts(rows,code=s['code'],mode=s['price_mode'],basis_id=f['chart_base'],as_of=f['as_of'],regions=regions,details=f['as_of'] in detail_dates))
            reviews[s['key']].append(reviewed_layer(case,s,f,e,rows))
            followups[s['key']].append(followup(case,s,f,rows,old['numbers']['series']) if s.get('kind')=='NEW_OFFICIAL_RAW_HISTORY' else None)
    payload.update(schema_version='pressure-chart-bundle/0.1',view_version=VERSION,facts_version=FACT_VERSION,
        wall_frames=walls,review_layers=reviews,followup_layers=followups,history_series=new_series,
        intake_summary={k:deepcopy(history[k]) for k in ('target_start','target_end','requests','blocked_hosts','five_year_target','calendar_evidence')},
        intake_coverage={s['code']:{k:deepcopy(v) for k,v in s.items() if k not in ('candles','source_records','corporate_actions')} for s in history['series']},
        review_case_file_sha256=hashlib.sha256((ROOT.parent/'docs/visual-discussion/20261018_1101_user_reviewed_case.json').read_bytes()).hexdigest(),history_audit=audit,
        window_policy='REQUESTED18_OR24_CALENDAR_MONTHS_CLIPPED_TO_ACTUAL_DAILY_PREFIX_NOT_WEEKLY_AGGREGATION',
        five_year_browser_acceptance='SEE_ACTUAL_BROWSER_AND_COVERAGE_REPORTS_NOT_LIFETIME_HISTORY',physical_android='NOT_TESTED_NEW_BUILD')
    payload['review_case_entry']=deepcopy(old['entry'])
    payload['entry']['preferred_series_by_code']={s['code']:s['key'] for s in new_series}
    if new_series:
        initial=next(s for s in new_series if s['code']=='1101')
        payload['entry'].update(series=initial['key'],as_of=initial['available_end'],rule='EXPLICIT_OFFICIAL_INTAKE_END_ENTRY_NOT_LIVE_QUERY')
    payload.pop('artifact_id');payload['artifact_id']=fingerprint(payload)
    if payload['numbers']!=old['numbers']:raise ValueError('Original numeric candidate changed')
    return payload


def selection(payload,key,as_of):
    s=next(s for s in [*payload['numbers']['series'],*payload['history_series']] if s['key']==key);f=next(f for f in s['frames'] if f['as_of']==as_of)
    return dict(schema_version='pressure-chart-selection/0.1',view_version=VERSION,facts_version=FACT_VERSION,
        saved_analysis=original_selection(payload,key,as_of) if s.get('kind')!='NEW_OFFICIAL_RAW_HISTORY' else None,
        new_history_analysis=history_selection(payload,s,f) if s.get('kind')=='NEW_OFFICIAL_RAW_HISTORY' else None,
        pressure_evidence=deepcopy(payload['wall_frames'][key][f['index']]),
        retrospective_review=deepcopy(payload['review_layers'][key][f['index']]),
        retrospective_followup=deepcopy(payload['followup_layers'][key][f['index']]),
        historical_review_is='LATER_MANUAL_ANNOTATION_NOT_BACKTEST_ASOF_AUTOMATIC_SIGNAL',
        requested_history_coverage=dict(target_start=payload['intake_summary']['target_start'],target_end=payload['intake_summary']['target_end'],
            status=payload['intake_coverage'][s['code']]['status'],missing_months=payload['intake_coverage'][s['code']]['missing_months'],
            full_history_high='NOT_ESTABLISHED',older_pressure='CANNOT_EXCLUDE'),
        action_qualification='NOT_EVALUATED',classification_quality='NOT_VALIDATED')


def render(payload):
    p=Path(__file__).parent;raw=json.dumps(pack(payload),ensure_ascii=False,separators=(',',':'),allow_nan=False)
    for char,esc in [('&','\\u0026'),('<','\\u003c'),('>','\\u003e'),('\u2028','\\u2028'),('\u2029','\\u2029')]:raw=raw.replace(char,esc)
    return (p/'template.html').read_text().replace('@@DATA@@',raw).replace('@@STYLE@@',(p/'viewer.css').read_text()).replace('@@SCRIPT@@',(p/'viewer.js').read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--history',required=True);p.add_argument('--output-dir',required=True);p.add_argument('--regions');a=p.parse_args()
    out=Path(a.output_dir).resolve()
    if 'output' not in out.parts or out==ROOT:raise ValueError('Use a separate dedicated output leaf')
    payload=make(a.history,() if a.regions is None else json.loads(Path(a.regions).read_text()))
    packed=pack(payload)
    if unpack(packed)!=payload:raise ValueError('Lossless transport verification failed')
    cases=[]
    windows=[]
    for s in [*payload['numbers']['series'],*payload['history_series']]:
        for i in sorted({0,33,60,len(s['frames'])//2,len(s['frames'])-1}):
            f=s['frames'][i];cases.append(dict(series=s['key'],as_of=f['as_of'],fingerprint=fingerprint(selection(payload,s['key'],f['as_of'])),frame_id=f['frame_id']))
        f=s['frames'][-1];bars=s['bases'][f['chart_base']]['bars'][:f['index']+1];last=date.fromisoformat(f['as_of'])
        for n in (18,24,60):
            total=last.year*12+last.month-1-n;y,m=divmod(total,12);m+=1
            start=date(y,m,min(last.day,monthrange(y,m)[1])).isoformat()
            index=next(i for i,r in enumerate(bars) if r['date']>=start)
            windows.append(dict(series=s['key'],as_of=f['as_of'],months=n,requested_start=start,start=index,end=f['index'],bars=f['index']-index+1,first_actual=bars[index]['date']))
    files={NAME:render(payload).encode(),'selection-oracle.json':json.dumps(dict(cases=cases),ensure_ascii=False,indent=2).encode(),
        'data-gaps.json':json.dumps(dict(reviewed_calendar_audit=payload['history_audit'],
            interpretation='Use reviewed_calendar_audit for final date gaps; stock known_calendar_missing_dates below are the original planned-calendar parse before cited no-trading-note corrections',
            intake=payload['intake_summary'],stocks=payload['intake_coverage']),ensure_ascii=False,indent=2).encode()}
    files['window-oracle.json']=json.dumps(dict(cases=windows),ensure_ascii=False,indent=2).encode()
    for n,b in files.items():
        q=out/n
        if q.is_symlink() or q.exists() and q.read_bytes()!=b:raise ValueError('Existing different output: '+str(q))
    for n,b in files.items():print(n,publish_immutable(out/n,b),len(b),flush=True)
    print(json.dumps(dict(artifact_id=payload['artifact_id'],frames=sum(len(s['frames']) for s in [*payload['numbers']['series'],*payload['history_series']]),original_numbers_unchanged=True)))

if __name__=='__main__':main()
