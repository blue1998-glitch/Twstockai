"""Add a mobile comparison tab to the unchanged, retained graph view bundle."""
import json
import re
from pathlib import Path

from graph_core_chart.build import ROOT,render,selection
from graph_core.core import fingerprint
from graph_core_chart.comparison_export import sha
from technical_chart.build import unpack
from product_candidate.build import publish_immutable

HERE=Path(__file__).parent/'mvp_m2_20261101'
OUT=Path(__file__).parent/'output/mvp_m2_20261101'
NAME='M1_graph_comparison_mvp_m2_v01.html'


def validate(bundle,index):
    if index['as_of']!='2026-10-16' or [s['code'] for s in index['stocks']]!=['1101','2884','6488','8069']:
        raise ValueError('Fixed common date/stocks required')
    for s in index['stocks']:
        series=next(v for v in bundle['series'] if v['code']==s['code'])
        r=next(r for r in series['results'] if r['as_of']==index['as_of'])
        if any(s[k]!=r[k] for k in ('result_id','source_prefix_fingerprint')):raise ValueError('M-C2 result mismatch')
        if s['source_input_binding']!=series['input_bindings'][index['as_of']]:raise ValueError('Source binding mismatch')
        if s['box_count']!=len(r['boxes']) or s['pending_extrema']!=r['pending_extrema']:raise ValueError('Evidence collection mismatch')
        valid={b['id'] for b in r['boxes']}
        if not set(s['nearest_above']['candidate_ids'])<=valid:raise ValueError('Unknown comparison box')
        if s['primary_pressure_id'] is not None or s['classification_quality']!='NOT_VALIDATED':raise ValueError('Qualification promotion refused')


def build():
    frozen=json.loads((HERE/'frozen.json').read_text())
    for row in frozen['files']:
        raw=(ROOT/row['path']).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise ValueError('Frozen source mismatch: '+row['path'])
    original=(ROOT/frozen['files'][0]['path']).read_text()
    bundle=unpack(json.loads(re.search(r'id="payload"[^>]*>(.*?)</script>',original,re.S)[1]))
    if fingerprint({k:v for k,v in bundle.items() if k!='artifact_id'})!=bundle['artifact_id']:raise ValueError('Bundle identity mismatch')
    index=json.loads((ROOT/'graph_core_chart/mc2_20261101/index.json').read_text());validate(bundle,index)
    if render(bundle)!=original:raise ValueError('Original view renderer changed')
    payload=json.dumps(index,ensure_ascii=False,separators=(',',':'))
    for char,escape in [('&','\\u0026'),('<','\\u003c'),('>','\\u003e'),('\u2028','\\u2028'),('\u2029','\\u2029')]:payload=payload.replace(char,escape)
    added='<style>'+(HERE/'comparison.css').read_text()+'</style><script id="comparison-payload" type="application/json">'+payload+'</script><script>'+(HERE/'comparison.js').read_text()+'</script>'
    html=original.replace('</body>',added+'</body>').replace('<title>M1 圖形辨識研究主圖 0.2</title>','<title>MVP-M2 同期四股比較與研究主圖</title>')
    publish_immutable(OUT/NAME,html.encode())
    report=dict(shell_version='mvp-m2/0.1',graph_version=bundle['view_version'],core_version='graph-recognition-research/0.2',
        html_sha256=sha(html.encode()),html_bytes=len(html.encode()),embedded_comparison_bytes=len(payload.encode()),
        original_bundle_id=bundle['artifact_id'],no_recognition=True,no_candidate_shards_embedded=True,
        prior_android='USER_REPORTED_MG3_NORMAL_FIRST_CASE',new_android='NOT_TESTED_USER_DEVICE')
    publish_immutable(HERE/'build-verification.json',(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode())
    oracle={'cases':[dict(code=s['code'],fingerprint=fingerprint(selection(bundle,s['code'],index['as_of']))) for s in index['stocks']]}
    publish_immutable(HERE/'download-oracle.json',(json.dumps(oracle,indent=2)+'\n').encode())
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':build()
