"""Extract exact fixed-artifact data, without invoking any analysis engine."""
import argparse
from copy import deepcopy
from decimal import Decimal
import base64
import gzip
import hashlib
import json
from pathlib import Path
import re
import zipfile

from graph_core.core import fingerprint
from product_candidate.build import publish_immutable

ROOT=Path(__file__).resolve().parents[1]
FIXED_COMMIT='57e3d9e55c226c5dd0e69fcbd26883d0da81667e'
OLD_NAME='M1_v019_graph_diagnostics_v01.html'
NAME='M1_v019_cross_scale_real_v01.html'
ZIP=ROOT.parent/'deliveries/m1-v019-graph-diagnostics-20261019/M1_v019_graph_diagnostics_v01.zip'
ZIP_SHA='c8a534f517bdd0e5f648d6b94c0bde992b9b869d72ead727ce84a4a75c3c69ff'
HTML_SHA='eb6d1e82da13db58a592d0868822fec9209bedfaf1ff4843440749677cad1baa'
VERSION='cross-scale-real-chart/0.1'


def sha(blob):return hashlib.sha256(blob).hexdigest()


def load_fixed():
    blob=ZIP.read_bytes()
    if sha(blob)!=ZIP_SHA:raise ValueError('Fixed diagnostic ZIP changed')
    with zipfile.ZipFile(ZIP) as archive:
        if archive.testzip() is not None:raise ValueError('Fixed ZIP CRC failed')
        for line in archive.read('SHA256SUMS.txt').decode().splitlines():
            digest,name=line.split('  ',1)
            if sha(archive.read(name))!=digest:raise ValueError('Fixed member SHA failed: '+name)
        raw=archive.read(OLD_NAME)
        if sha(raw)!=HTML_SHA:raise ValueError('Fixed HTML changed')
        diag_raw=archive.read('diagnostics-1101-latest.json')
        retained=ROOT/'graph_diagnostics/generated/diagnostics-1101-latest.json.gz'
        if gzip.decompress(retained.read_bytes())!=diag_raw:raise ValueError('Current retained diagnostic differs from fixed artifact')
    transport=json.loads(re.search(r'id="payload"[^>]*>(.*?)</script>',raw.decode(),re.S).group(1))
    packed=json.loads(gzip.decompress(base64.b64decode(transport['data'],validate=True)))
    nodes=packed['nodes'];memo={}
    def field(index,key):
        if nodes[index][0]!='o':raise ValueError('Object required')
        return dict(nodes[index][1:])[key]
    def decode(index):
        if index not in memo:
            n=nodes[index];memo[index]=n[1] if n[0]=='s' else [decode(i) for i in n[1:]] if n[0]=='a' else {k:decode(i) for k,i in n[1:]}
        return memo[index]
    series_indices=nodes[field(packed['root'],'series')][1:]
    chosen=next(i for i in series_indices if decode(field(i,'code'))=='1101')
    s={k:decode(field(chosen,k)) for k in ['code','exchange','source','price_basis_id','bars','macd','moving_averages','source_gaps','macd_parameters','numeric_frame_ids']}
    r=decode(nodes[field(chosen,'results')][-1]);as_of=r['as_of']
    s['core']=r;s['manual_case_audit']=decode(field(field(chosen,'manual_audits'),as_of))
    diagnostic=json.loads(diag_raw)
    if diagnostic['core_result_id']!=r['result_id'] or fingerprint(s['bars'])!=r['source_prefix_fingerprint']:
        raise ValueError('Fixed source/diagnostic identity mismatch')
    if fingerprint({k:v for k,v in r.items() if k!='result_id'})!=r['result_id']:raise ValueError('Core fingerprint mismatch')
    return s,diagnostic


def make(source=None,diagnostic=None):
    if source is None:source,diagnostic=load_fixed()
    s=deepcopy(source);r=s['core'];d=diagnostic;rows=s['bars'];as_of=r['as_of']
    if fingerprint({k:v for k,v in r.items() if k!='result_id'})!=r['result_id']:
        raise ValueError('Original core identity changed')
    if (s['code']!=r['context']['code'] or r['as_of']!=d['as_of']
            or fingerprint(rows)!=r['source_prefix_fingerprint'] or len(rows)!=r['source_records']
            or rows[-1]['date']!=as_of or s['source']['id']!=r['context']['source_id']
            or s['price_basis_id']!=r['context']['price_basis_id']):raise ValueError('Source prefix, basis, anchor or identity changed')
    # Saved MACD is an ordinal series without a date in each row. Its exact
    # values and ordering are inherited from the verified fixed source.
    if len(s['macd'])!=len(rows) or any(v.get('date',row['date'])!=row['date'] for v,row in zip(s['macd'],rows)):
        raise ValueError('Saved MACD time axis differs')
    review_path=ROOT/'graph_diagnostics/generated/review-diagnostics.json'
    review=json.loads(review_path.read_text())
    if review['core_result_id']!=r['result_id'] or review['diagnostic_id']!=d['diagnostic_id']:raise ValueError('Existing review identity mismatch')
    byid={b['id']:b for b in r['boxes']};cases={b['label']:b['box']['id'] for b in review['selected_case_diagnostics']}
    layers=[]
    def add(key,title,kind,start,end,color,*,box_ids=(),trace=None,manual=None):
        indices=[i for i,row in enumerate(rows) if start<=row['date']<=end]
        if not indices:raise ValueError('Empty real display interval')
        a,b=indices[0],indices[-1];selected=rows[a:b+1]
        if selected[0]['date']!=start or selected[-1]['date']!=end:raise ValueError('Exact retained endpoints required')
        boxes=[byid[i] for i in box_ids];dates=[]
        for box in boxes:
            dates.extend([dict(kind='SOURCE_LAST_TURN',date=box['source_end'],box_id=box['id']),dict(kind='CONFIRMED',date=box['confirmed_at'],box_id=box['id'])])
            w=next(v for v in d['boxes'] if v['box_id']==box['id'])['windows']['date_semantics']
            if w['first_outside_close_at']:dates.append(dict(kind='FIRST_OUTSIDE_RESEARCH_CLOSE',date=w['first_outside_close_at'],box_id=box['id']))
        if trace:dates.extend([dict(kind='SOURCE_LAST_TURN',date=end),dict(kind='TRIAL_OBSERVED',date=trace['observed_at'])])
        if manual and kind=='MANUAL_EXACT_TIME':dates.append(dict(kind='MANUAL_WHOLE_END',date=end))
        layers.append(dict(id=key,title=title,kind=kind,color=color,first_index=a,last_index=b,source_start=start,source_end=end,
            display_extent=dict(low=min(selected,key=lambda v:Decimal(v['low']))['low'],high=max(selected,key=lambda v:Decimal(v['high']))['high'],
                maximum_volume=max(selected,key=lambda v:Decimal(v['volume_shares_scaled']))['volume_shares_scaled'],records=len(selected),source_rows_fingerprint=fingerprint(selected),
                qualification='RAW_WICK_ENVELOPE_FOR_DISPLAY_NOT_FORMAL_PRESSURE_BOUNDS'),
            box_ids=list(box_ids),trace=deepcopy(trace),manual=deepcopy(manual),date_markers=dates,
            formal_price_bounds=None,formal_membership=None))
    m=s['manual_case_audit']['larger_manual_band'];month_rows=[v for v in rows if m['start_month']<=v['date'][:7]<=m['end_month']]
    add('major','人工月份主帶','MANUAL_MONTH_CONTEXT',month_rows[0]['date'],month_rows[-1]['date'],'#91a4bc',manual=m)
    b77=byid[review['B77']['id']]
    add('b77','B77 原候選','ORIGINAL_RESEARCH_BOX',b77['start'],b77['source_end'],'#5ed2b3',box_ids=[b77['id']])
    for key,title,ref,color in [('left','左擴被拒串','nearest_earlier_confirmed_start_trial','#f5bd68'),('right','右延被拒串','first_later_confirmed_end_trial','#f18e9b')]:
        trial=next(t for t in d['enumeration'] if t['id']==review['B77'][ref]['id'])
        if trial['decision']!='REJECTED_GEOMETRY':raise ValueError('Existing rejected trial changed')
        add(key,title,'REJECTED_SOURCE_RUN',trial['source_start'],trial['source_last_turn'],color,trace=trial)
    previous=s['manual_case_audit']['previous_manual_box']
    add('manual39','人工39筆前箱','MANUAL_EXACT_TIME',previous['start'],previous['end'],'#81b7ff',manual=previous)
    b44,b80=[byid[cases[k]] for k in ['B44','B80']]
    if (b44['start'],b44['source_end'])!=(b80['start'],b80['source_end']):raise ValueError('Existing same geometry source changed')
    add('same','B44／B80 同幾何','CROSS_SCALE_SAME_GEOMETRY',b44['start'],b44['source_end'],'#dab3ff',box_ids=[b44['id'],b80['id']])
    b88=byid[cases['B88']]
    add('recent','B88 近期箱','ORIGINAL_RESEARCH_BOX',b88['start'],b88['source_end'],'#e2a6e7',box_ids=[b88['id']])
    relevant={i for layer in layers for i in layer['box_ids']}|{b['id'] for b in r['boxes'] if b['id'] in next(v for v in d['boxes'] if v['box_id']==b77['id'])['all_source_prefix_ancestor_ids']}|{cases['B89']}
    report=dict(schema_version=VERSION,code=s['code'],as_of=as_of,anchor=deepcopy(r['anchor']),bars=rows,macd=s['macd'],moving_averages=s['moving_averages'],
        source=s['source'],price_basis_id=s['price_basis_id'],source_frame_id=s['numeric_frame_ids'][as_of],source_prefix_fingerprint=r['source_prefix_fingerprint'],
        source_gaps=s['source_gaps'],macd_parameters=s['macd_parameters'],core=r,manual_case_audit=s['manual_case_audit'],layers=layers,
        diagnostics=dict(schema_version=d['schema_version'],diagnostic_id=d['diagnostic_id'],summary=d['summary'],
            selected_box_diagnostics=[deepcopy(v) for v in d['boxes'] if v['box_id'] in relevant],
            source_prefix_version_edges=[deepcopy(e) for e in d['source_prefix_version_edges'] if e['to_id'] in relevant]),
        provenance=dict(fixed_commit=FIXED_COMMIT,fixed_zip_sha256=ZIP_SHA,fixed_html_sha256=HTML_SHA,macd_axis_binding='EXACT_SAVED_ORDINAL_SERIES_TO_SOURCE_BAR_INDEX',
            review_path=str(review_path.relative_to(ROOT.parent)),review_sha256=sha(review_path.read_bytes()),
            original_core_result_id=r['result_id'],original_core_unchanged=True),
        lookback_qualification='LATER_MANUAL_AUDIT_DISPLAY_NOT_HISTORICAL_SIGNALS_OR_ANALYSIS_REPLAY',
        core_usefulness='NOT_ESTABLISHED',classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED',physical_android='NOT_TESTED_NEW_BUILD')
    report['artifact_id']=fingerprint(report)
    return report


def render(payload):
    here=Path(__file__).parent;raw=json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    for char,escape in [('&','\\u0026'),('<','\\u003c'),('>','\\u003e'),('\u2028','\\u2028'),('\u2029','\\u2029')]:raw=raw.replace(char,escape)
    return (here/'template.html').read_text().replace('@@STYLE@@',(here/'viewer.css').read_text()).replace('@@DATA@@',raw).replace('@@SCRIPT@@',(here/'viewer.js').read_text())


def read_new(path):return json.loads(re.search(r'id="payload"[^>]*>(.*?)</script>',Path(path).read_text(),re.S).group(1))


def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',required=True);a=p.parse_args();out=Path(a.output_dir)
    if 'output' not in out.parts:raise ValueError('New output leaf required')
    data=make();report=dict(status='PASS',fixed_zip_sha256=ZIP_SHA,fixed_html_sha256=HTML_SHA,records=len(data['bars']),
        first_date=data['bars'][0]['date'],last_date=data['bars'][-1]['date'],missing_ohlcv_dates=[r['date'] for r in data['bars'] if any(r[k] is None for k in ['open','high','low','close','volume_shares_scaled'])],
        source_id=data['source']['id'],price_basis_id=data['price_basis_id'],source_frame_id=data['source_frame_id'],source_prefix_fingerprint=data['source_prefix_fingerprint'],
        core_result_id=data['core']['result_id'],source_gaps=data['source_gaps'],raw_price_basis_qualification='UNVERIFIED_CORPORATE_ACTION_COMPARABILITY',
        layers=[dict(id=l['id'],records=l['display_extent']['records'],start=l['source_start'],end=l['source_end'],kind=l['kind']) for l in data['layers']],
        core_engine_executed=False,physical_android='NOT_TESTED_NEW_BUILD')
    for name,raw in {NAME:render(data).encode(),'comparison-data.json':json.dumps(data,ensure_ascii=False,indent=2).encode(),'source-acquisition.json':json.dumps(report,ensure_ascii=False,indent=2).encode()}.items():
        print(name,publish_immutable(out/name,raw),len(raw),sha(raw))


if __name__=='__main__':main()
