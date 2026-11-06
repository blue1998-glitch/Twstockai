"""Read-only verification of one supplied Android export against pinned release.
AST extracts producer selection functions; no module builds or store access.
"""
import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import zipfile

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--html', type=Path, default=HERE/'M1_v0_19_three_hurdles.html')
p.add_argument('--export', type=Path, default=HERE.parent/'upload/M1_1101_RAW_CANDIDATE_2026-10-16 (1).json')
p.add_argument('--screenshot', type=Path, default=HERE.parent/'upload/01-Screenshot_20261018-171319.png')
p.add_argument('--source-root', type=Path, default=HERE/'pinned_source')
p.add_argument('--case-zip', type=Path, default=HERE/'M1_v019_three_hurdles_page.zip')
p.add_argument('--output', type=Path, default=HERE/'android-export-verification-1713.json')
a = p.parse_args()
def digest(b): return hashlib.sha256(b).hexdigest()
def fp(obj): return 'sha256:'+digest(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
source_digests = {}
def extract(relative, function, extra=None):
    raw=(a.source_root/relative).read_bytes();source_digests[relative]=digest(raw)
    tree=ast.parse(raw.decode());ns={'deepcopy':deepcopy,**(extra or {})}
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VERSION' for t in n.targets):ns['VERSION']=ast.literal_eval(n.value)
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==function]
    assert len(functions)==1
    exec(compile(ast.Module(body=functions,type_ignores=[]),relative,'exec'),ns)
    return ns[function]
html=a.html.read_bytes();assert digest(html)=='4cbe923936f9841652e7a303ec60029f9159dffe3b266e468d04b573f060706c'
transport=json.loads(re.search(r'<script type="application/json" id="payload">(.*?)</script>',html.decode(),re.S).group(1))
payload=extract('technical_chart/build.py','unpack')(transport)
history_selection=extract('pressure_chart/history_adapter.py','history_selection')
pressure_selection=extract('pressure_chart/build.py','selection',{'history_selection':history_selection,'FACT_VERSION':payload['facts_version']})
selection=extract('hurdle_chart/build.py','selection',{'pressure_selection':pressure_selection})
raw=a.export.read_bytes();actual=json.loads(raw)
assert actual['schema_version']=='hurdle-chart-selection/0.1'
s=next(s for s in payload['history_series'] if s['code']=='1101')
expected=selection(payload,s['key'],'2026-10-16')
assert actual==expected,'Full parsed JSON does not equal pinned release selection'
analysis=actual['new_history_analysis'];bars=analysis['bars'];manual=actual['manual_hurdles']
assert len(bars)==1213 and bars[0]['date']=='2021-10-18' and bars[-1]['date']=='2026-10-16'
assert analysis['frame']['as_of']=='2026-10-16'
assert all(b['date']<='2026-10-16' for b in bars)
assert len(analysis['macd'])==1213 and all(len(v)==1213 for v in analysis['moving_averages'].values())
assert actual['saved_analysis'] is None and actual['retrospective_review'] is None
assert manual['integration_status']=='EXACT_MANUAL_CASE_DISPLAY_ONLY'
assert manual['review']['product_integration']=='NOT_IMPLEMENTED'
assert manual['source_fingerprints']['source_id']==analysis['source']['id']
assert manual['source_fingerprints']['frame_id']==analysis['frame']['frame_id']
assert manual['source_fingerprints']['chart_base']==analysis['frame']['chart_base']
assert manual['source_fingerprints']['data_prefix']==analysis['frame']['data_fingerprint']==fp(bars)
with zipfile.ZipFile(a.case_zip) as z:case_raw=z.read('20261018_1101_selected_hurdles.json')
assert digest(case_raw)==manual['source_fingerprints']['review_file_sha256']
assert json.loads(case_raw)==manual['review']
references=manual['references'];assert [r['reference']['id'] for r in references]==['G1','G2','G3']
assert [r['reference']['raw_high'] for r in references]==['35.50','40.25','50.20']
g3=references[2]['reference'];assert g3['source_date'] is None
assert g3['matching_source_dates']==['2021-10-18','2022-03-29','2022-03-31','2022-04-06','2022-04-07']
for r in references:
    ref=r['reference'];assert r['current_close_relation']=='BELOW'
    assert [bars[i] for i in r['source_indices']]==ref['source_bars']
    assert all(ref[k] is None for k in ['region_start','region_end','region_price_bounds','region_total_volume','volume_expansion_rule','automatic_selection_rule'])
report={
    'status':'PASS_ONE_UPLOADED_EXPORT_FULL_PARSED_VALUE_EQUALITY',
    'scope':'Full parsed export equals pinned HTML producer selection; verifies stored precision and source bindings, not byte-format equality or independent OHLCV/indicator recomputation',
    'product_commit':'87ec609ef51d7346554e2546e520a9dbc4ac2235',
    'producer_source_read_commit':'8b99c715c481bf7ec20f054651affc63134a159d',
    'source_function_files_sha256':source_digests,
    'html_sha256':digest(html),
    'upload':{'filename':a.export.name,'bytes':len(raw),'sha256':digest(raw),'canonical_sha256':fp(actual).removeprefix('sha256:')},
    'screenshot':{'filename':a.screenshot.name,'bytes':a.screenshot.stat().st_size,'sha256':digest(a.screenshot.read_bytes())},
    'schema_version':actual['schema_version'],'view_version':actual['view_version'],
    'as_of':analysis['frame']['as_of'],'source_id':analysis['source']['id'],'frame_id':analysis['frame']['frame_id'],'chart_base':analysis['frame']['chart_base'],
    'bars':len(bars),'last_bar':bars[-1],
    'macd_rows':len(analysis['macd']),'ma_rows':{k:len(v) for k,v in analysis['moving_averages'].items()},
    'manual_layer_present':True,'integration_status':manual['integration_status'],
    'original_review_historical_integration':manual['review']['product_integration'],
    'g3_source_date':g3['source_date'],'g3_matching_source_dates':g3['matching_source_dates'],
    'source_fingerprints':manual['source_fingerprints'],
    'all_supplied_bars_not_after_analysis_date':True,
    'manual_layer_count_in_pinned_bundle':sum(v is not None for frames in payload['manual_hurdle_layers'].values() for v in frames),
    'android_overall':'PARTIAL_EVIDENCE_OBSERVED',
    'not_observed_this_turn':['landscape main chart','return to 24-month window','all five G3 locate interactions','long-ID/JSON expansion interactions','pan/zoom','moving K/volume/MACD cursor synchronization','rotation preservation','10/15 or other source exclusion','product usefulness acceptance'],
}
assert report['manual_layer_count_in_pinned_bundle']==1
a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
