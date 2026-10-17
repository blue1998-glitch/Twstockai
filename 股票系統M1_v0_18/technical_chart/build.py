"""Explicit offline build: unchanged candidate numbers + exact saved structure evidence.
The browser never opens stores or computes analysis. No network requests.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from analysis_store import AnalysisStore
from contracts import fingerprint
from cross_view_cli import read_config
from source_audit import parse_twse_month, planned_dates, apply_evidenced_closures
from product_candidate.build import bundle, selection_payload, publish_immutable

VERSION = 'technical-chart-view/0.1'
NAME = 'M1_v0_19_technical_chart.html'


def audit(saved):
    q = saved['request']; rows = q['candles']; dates = [r['date'] for r in rows]
    supplied = q.get('expected_dates')
    if supplied is None:
        # Older TPEX jobs do not embed expected_dates. Audit against the retained
        # reviewed schedules; absence of a calendar is never an empty calendar.
        schedules = [json.loads((ROOT/'data_audit'/f'TPEX_{year}_計畫開休市.json').read_text())
                     for year in (2025, 2026)]
        closures = json.loads((ROOT/'data_audit/臨時休市證據.json').read_text())
        supplied = apply_evidenced_closures(planned_dates(schedules, dates[0], dates[-1]),
                                          closures, exchange=q['exchange'])['dates']
    expected = {d for d in supplied if dates[0] <= d <= dates[-1]}
    raw_checks = []
    if q['code'] in ('1101', '2884'):
        parsed = []
        for month, meta in enumerate(q['source']['source_records'], 1):
            path = ROOT / 'data_audit/raw' / f"{q['code']}_2026{month:02d}.json"
            content = path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            if digest != meta['sha256']:
                raise ValueError('Official response checksum mismatch: ' + str(path))
            parsed += parse_twse_month(json.loads(content), code=q['code'], year=2026, month=month)
            raw_checks.append(dict(file=str(path.relative_to(ROOT)), sha256=digest, url=meta['url']))
        if parsed != rows:
            raise ValueError('Saved OHLCV differs from captured official response')
    duplicates = [d for d, count in Counter(dates).items() if count > 1]
    if duplicates or dates != sorted(dates):
        raise ValueError('Unordered or duplicate source dates')
    return dict(code=q['code'], exchange=q['exchange'], price_mode=q['price_mode'],
        source_id=q['source']['id'], original_record_id=saved['record_id'],
        first_date=dates[0], last_date=dates[-1], bars=len(rows),
        missing_ohlc_dates=[r['date'] for r in rows if any(r.get(k) is None for k in ('open','high','low','close'))],
        missing_volume_dates=[r['date'] for r in rows if r.get('volume_shares_scaled') is None],
        duplicate_dates=duplicates, missing_supplied_calendar_dates=sorted(expected - set(dates)),
        unexpected_supplied_calendar_dates=sorted(set(dates) - expected),
        calendar_scope='SUPPLIED_PLANNED_AND_REVIEWED_EXCEPTIONS_NOT_EXHAUSTIVE',
        volume_unit=q['source']['volume_unit'], volume_normalization=q['source'].get('volume_normalization'),
        actions_coverage=q['corporate_actions']['coverage_status'],
        action_publication_timing='UNVERIFIED', historical_availability='NOT_AUTHENTICATED_POINT_IN_TIME',
        captured_official_response_checks=raw_checks,
        gaps=['NO_BARS_BEFORE_' + dates[0], 'NO_BARS_AFTER_' + dates[-1],
              'MULTI_YEAR_HISTORY_NOT_PRESENT', 'REAL_INTRADAY_NOT_PRESENT',
              'COMPLETE_CORPORATE_ACTIONS_AND_PUBLICATION_TIMING_NOT_VERIFIED'])


def make(config):
    original = bundle(config, 'structure-0.3-research')
    stores = {alias: AnalysisStore(path) for alias, path in config['daily_stores'].items()}
    evidence, coverage, entries = {}, {}, {}
    for series in original['series']:
        saved = stores[series['store']].load(series['original_record_id'])
        coverage[series['key']] = audit(saved)
        entries[series['key']] = '2026-09-30'  # Explicit artifact entry, never a latest-date search.
        snaps = saved['result']['components']['structure']['snapshots']
        evidence[series['key']] = []
        for frame, snap in zip(series['frames'], snaps):
            if frame['structure_snapshot_id'] != snap['snapshot_id']:
                raise ValueError('Exact source snapshot required')
            evidence[series['key']].append(dict(as_of=snap['as_of'], snapshot_id=snap['snapshot_id'],
                rule_version=snap['rule_version'], parameters=deepcopy(snap['parameters']),
                parameters_fingerprint=snap['parameters_fingerprint'], adjustment_anchor=snap['adjustment_anchor'],
                pivots=deepcopy(snap['pivots']), zones=deepcopy(snap['zones']),
                daily_events=[dict(id=fingerprint(dict(snapshot_id=snap['snapshot_id'], ordinal=i, event=e)),
                    original=deepcopy(e), source_snapshot_id=snap['snapshot_id']) for i,e in enumerate(snap['daily_events'])]))
            if any(p['confirmed_at'] > frame['as_of'] for p in snap['pivots']):
                raise ValueError('Future confirmed pivot')
    initial = next(s['key'] for s in original['series'] if s['code']=='1101' and s['price_mode']=='RAW_CANDIDATE')
    payload = dict(schema_version='technical-chart-bundle/0.1', view_version=VERSION,
        numbers=original, evidence=evidence, coverage=coverage,
        entry=dict(series=initial, as_of='2026-09-30', per_series_as_of=entries,
                   rule='EXPLICIT_FIXED_ARTIFACT_ENTRY_NOT_AUTOMATIC_LATEST'),
        classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED',
        physical_android='NOT_TESTED', intraday='NO_REAL_INTRADAY_SOURCE_DAILY_CLOSED_ASSUMPTION_ONLY')
    payload['artifact_id'] = fingerprint(payload)
    return payload


def selection(payload, key, as_of):
    series = next(s for s in payload['numbers']['series'] if s['key']==key)
    f = next(f for f in series['frames'] if f['as_of']==as_of)
    return dict(schema_version='technical-chart-selection/0.1', view_version=VERSION,
        analysis=selection_payload(payload['numbers'], key, as_of),
        structure_evidence=deepcopy(payload['evidence'][key][f['index']]),
        historical_structure_events=deepcopy([dict(as_of=e['as_of'], source_snapshot_id=e['snapshot_id'],
            adjustment_anchor=e['adjustment_anchor'], price_mode=series['price_mode'],
            chart_base=series['frames'][i]['chart_base'], daily_events=e['daily_events'])
            for i,e in enumerate(payload['evidence'][key][:f['index']+1])]),
        coverage_of_selected_prefix=dict(first_date=series['available_start'], last_date=as_of, bars=f['index']+1,
            calendar_scope=payload['coverage'][key]['calendar_scope'],
            source_id=series['source']['id'], actions_coverage=series['coverage'],
            historical_availability='NOT_AUTHENTICATED_POINT_IN_TIME'),
        interpretation='SAVED_RESEARCH_CANDIDATES_NOT_TRADE_SIGNALS', intraday=payload['intraday'])


def pack(value):
    """Lossless interned JSON tree transport; repeated subtrees share IDs, not numbers.
    This only changes HTML serialization, never the common data contracts.
    """
    nodes, seen = [], {}
    def visit(v):
        if isinstance(v, bool) or v is None or isinstance(v, str):
            node = ['s',v]
        elif isinstance(v, (int,float)):
            if not isinstance(v,int) or abs(v)>9007199254740991:
                raise ValueError('Non-safe number; use original decimal/string contract')
            node = ['s',v]
        elif isinstance(v,list): node = ['a',*[visit(x) for x in v]]
        elif isinstance(v,dict): node = ['o',*[[k,visit(v[k])] for k in sorted(v)]]
        else: raise TypeError(type(v))
        token = json.dumps(node,ensure_ascii=False,separators=(',',':'))
        if token in seen: return seen[token]
        index=len(nodes);seen[token]=index;nodes.append(node);return index
    root=visit(value)
    return dict(schema_version='chart-interned-json/0.1',root=root,nodes=nodes)


def unpack(transport):
    memo={}
    def get(i):
        if i not in memo:
            n=transport['nodes'][i]
            memo[i] = n[1] if n[0]=='s' else [get(x) for x in n[1:]] if n[0]=='a' else {k:get(v) for k,v in n[1:]}
        return memo[i]
    return get(transport['root'])


def render(payload):
    folder=Path(__file__).parent
    raw=json.dumps(pack(payload),ensure_ascii=False,separators=(',',':'),allow_nan=False)
    for char,escape in [('&','\\u0026'),('<','\\u003c'),('>','\\u003e'),('\u2028','\\u2028'),('\u2029','\\u2029')]:
        raw=raw.replace(char,escape)
    return (folder/'template.html').read_text().replace('@@DATA@@',raw).replace('@@STYLE@@',(folder/'viewer.css').read_text()).replace('@@SCRIPT@@',(folder/'viewer.js').read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args()
    out=Path(a.output_dir).resolve()
    # Constrain writes to a separate output leaf; never replace project assets or stores.
    if out.name in ('technical_chart','product_candidate','src') or out==ROOT or ROOT in out.parents and 'output' not in out.relative_to(ROOT).parts:
        raise ValueError('Use a new dedicated output directory')
    payload=make(read_config(a.config));transport=pack(payload)
    if unpack(transport)!=payload: raise ValueError('Transport roundtrip mismatch')
    cases=[]
    for s in payload['numbers']['series']:
        for i in sorted({0,33,60,len(s['frames'])//2,len(s['frames'])-1}):
            f=s['frames'][i];v=selection(payload,s['key'],f['as_of'])
            cases.append(dict(series=s['key'],as_of=f['as_of'],fingerprint=fingerprint(v),frame_id=f['frame_id']))
    files={NAME:render(payload).encode(), 'coverage.json':json.dumps(payload['coverage'],ensure_ascii=False,indent=2).encode(),
           'selection-oracle.json':json.dumps(dict(cases=cases),ensure_ascii=False,indent=2).encode()}
    # Validate all outputs before the first write, including symlinks.
    for name,content in files.items():
        dest=out/name
        if dest.exists() and (dest.is_symlink() or dest.read_bytes()!=content):
            raise ValueError('Existing different artifact; choose new output directory: '+str(dest))
    for name,content in files.items():print(name,publish_immutable(out/name,content),len(content),flush=True)
    print(json.dumps(dict(artifact_id=payload['artifact_id'],series=len(payload['numbers']['series']),frames=sum(len(s['frames']) for s in payload['numbers']['series']),transport_nodes=len(transport['nodes']))))

if __name__=='__main__': main()
