"""Append one new LITE shell beside old quote shards; no copies of data/graphs."""
from pathlib import Path
import json,time
from .common import BASE,ROOT,WORK,PROJECT,REPO,read_json,write,encode,sha,budget,heads
from graph_core.lite1_20261103.render import compile_view
from rotation_research import artifact_codec as c

def run():
    budget(6*1024**2);start=time.monotonic()
    pointer=BASE/'lite1_20261103/view-head-private.json';old_bytes=pointer.read_bytes();old_catalogue=read_json(json.loads(old_bytes)['batch_index']);entry=old_catalogue['batches'][0]
    if entry['as_of']!='2026-11-03':raise ValueError('EXPECTED_QUOTE_DAY_NOT_CURRENT')
    quote_folder=Path(entry['path']).parent;state=read_json(quote_folder/'prepared-state-private.json')
    if state.get('presentation')!='DAILY_QUOTES' or state['quote_capture_id']!=read_json(BASE/'storage1_20261104/facts-build-private.json')['binding']['capture_id']:raise ValueError('M_STORAGE1_SOURCE_BINDING')
    original_heads=heads();before=sha(old_bytes)
    protected=[PROJECT/'graph_core/core.py',PROJECT/'graph_core/graph_lazy1_20261104/worker.py',PROJECT/'graph_core/graph_lazy1_20261104/provider.py',PROJECT/'product_candidate/macd.py',PROJECT/'src/moving_averages.py',PROJECT/'graph_core/lite1_20261103/decision.py']
    code={str(p):sha(p.read_bytes()) for p in protected};actions=[]
    for s in state['stocks']:
        desc=s['preview_evidence'];key=sha(encode(dict(identity=s['identity'],as_of=s['as_of'],fact=desc,protected_code=code)))
        s['lazy_graph']=dict(path='lazy-'+key+'.json',request_id=key)
        actions.append(dict(**{k:s[k] for k in ('identity','code','market','isin','cfi','as_of')},request_id=key,local_route='lazy-'+key+'.json',fact=desc,fact_path=str(quote_folder/desc['path'])))
    state['lazy_enabled']=True;state['summary']['lazy_graph_mode']='SINGLE_VERIFIED_SEGMENT_OR_ABSTAIN_NO_HISTORY_JOIN'
    raw,ui_sha=compile_view(state,state['summary']['as_of']);name='market-lazy1-'+sha(raw)[:16]+'.html';target=quote_folder/name
    # Unique append only. Never overwrite old prepared state, data, HTML or catalogue.
    if target.exists() and target.read_bytes()!=raw:raise ValueError('IMMUTABLE_VIEW_CONFLICT')
    budget(len(raw));c.immutable(target,raw)
    new_entry=dict(entry,path=str(target),bytes=len(raw),sha256=sha(raw));new_catalogue=encode(dict(schema='private-saved-batches/0.1',batches=[new_entry,*old_catalogue['batches'][1:]]));catalogue=WORK/('batches-'+sha(new_catalogue)+'.json');write(catalogue,new_catalogue)
    prefix='batch-'+new_entry['sha256']+'/'
    for a in actions:a['route']=prefix+a.pop('local_route');a['fact_route']=prefix+a['fact']['path']
    receipts=read_json(BASE/'day2_compact_20261104/repaired-source-private.json');sources={}
    for m,lower in [('TWSE','twse'),('TPEX','tpex')]:
        h=state['daily_sources'][m];p=BASE/'day2_compact_20261104/capture/raw'/h;s=p.stat();sources[m]=dict(path=str(p),sha256=h,metadata=[s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev])
    spec=encode(dict(schema='private-lazy-graph-actions/0.1',capture_id=state['quote_capture_id'],actions=actions,original_daily_sources=sources,protected_code=code,metrics_route=prefix+'lazy-status.json'))
    manifest=WORK/('actions-'+sha(spec)+'.json');write(manifest,spec);write(WORK/'source-state-private.json',encode(state));write(WORK/'original-view-head-private.json',old_bytes)
    if heads()!=original_heads:raise ValueError('SOURCE_HEAD_CHANGED')
    report=dict(status='BUILT_NOT_YET_ACTIVE',catalogue=str(catalogue),new_entry=new_entry,old_entries=old_catalogue['batches'][1:],previous_latest_entry=entry,action_manifest=str(manifest),action_sha256=sha(spec),original_view_head_sha256=before,original_source_heads=original_heads,static_quote_shards_copied=0,new_stock_core_calls=0,graph_actions=len(actions),lazy_status_route=prefix+'lazy-status.json',new_appended_file=str(target),elapsed_seconds=time.monotonic()-start)
    write(WORK/'build-private.json',encode(report));return report
if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False))
