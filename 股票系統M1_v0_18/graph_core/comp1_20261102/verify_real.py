"""Read retained four results and frozen M-C2 projection; no market/engine RUN."""
from pathlib import Path
from unittest.mock import patch
import hashlib,json
from graph_core.market_daily import Journal
from graph_core.stock_comparison import project
from graph_core.market_preview import build
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
root=Path('/workspace/twstockai-local-data/fm1/runtime');key='fm2-0d6ccbe63fbec6678f19f22eefe48976643759ce9e9fad6936f7558f08659257';batch=Journal(root/'runs').read(key)['value'];index=json.loads((ROOT/'graph_core_chart/mc2_20261101/index.json').read_text());rows=[]
for s in batch['stocks']:
    if not s.get('result_key'):continue
    saved=Journal(root/'results').read(s['result_key'])['value'];x=project(saved,s,{'id':saved['result']['context']['source_id'],**s.get('history_source_provenance',{})});expected=next(t for t in index['stocks'] if t['code']==s['code'])
    for k in ['result_id','source_prefix_fingerprint','anchor','anchor_volume','latest_confirmed_by_scale','pending_extrema','nearest_above']:assert x[k]==expected[k],(s['code'],k)
    boxes=[]
    for desc in expected['box_shards']:
        raw=(ROOT/'graph_core_chart/mc2_20261101'/desc['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==desc['sha256'];boxes.extend(json.loads(raw)['boxes'])
    assert len(x['boxes'])==len(boxes)
    for a,b in zip(x['boxes'],boxes):
        for k in a:assert a[k]==b[k],(s['code'],k)
    rows.append(dict(code=s['code'],as_of=x['as_of'],result_id=x['result_id'],box_count=len(boxes),nearest_ties=len(x['nearest_above']['candidate_ids']),status='PASS_ALL_SELECTED_FIELDS_AND_ALL_BOXES_MATCH_MC2'))
with patch('graph_core.core.analyze',side_effect=AssertionError('No analysis')):preview=build(root,key)
Path('/tmp/comp1-real-preview.json').write_text(json.dumps(preview));(HERE/'real-verification.json').write_text(json.dumps(dict(status='PASS_FOUR_RETAINED_ONLY',rows=rows,private_preview=preview,source_requests=0,core_runs=0,full_fm3='BLOCKED_ROOT_ABSENT'),ensure_ascii=False,indent=2)+'\n');print(rows)
