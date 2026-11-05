"""Small formal shell using LITE1's original viewer and exact saved facts."""
import copy,json
from pathlib import Path
from graph_core.lite1_20261103.render import compile_view
from .flow import BASE,WORK,read,sha,encode,put,descriptor,capacity
LABELS={'EXECUTED_INSUFFICIENT_HISTORY':'歷史不足','SOURCE_REFUSED':'來源拒用','ENGINEERING_FAILURE':'分析失敗','ENGINEERING_FAILURE_UNKNOWN_OUTCOME':'結果待核'}

def build(scanwork,work):
    numeric=read(scanwork/'manifest-private.json');index=read(scanwork/'complete-index.json')
    state=read(BASE/'scan1_20261104/view-state-private.json')
    oldby={s['identity']:s for s in state['stocks']};rows={r['identity']:r for r in index['records']}
    folder=Path(numeric['stocks'][0]['fact_path']).parent
    if any(Path(s['fact_path']).parent!=folder for s in numeric['stocks']):raise ValueError('FACT_FOLDER_CONFLICT')
    counts=index['counts'];ss=dict(as_of=index['as_of'],scan_id=index['scan_id'],total=index['expected'],executed=sum(r['core_calls']==1 for r in index['records']),insufficient=counts.get('EXECUTED_INSUFFICIENT_HISTORY',0),refused=counts.get('SOURCE_REFUSED',0),failed=sum(n for k,n in counts.items() if k.startswith('ENGINEERING_FAILURE')),descriptive=0)
    stocks=[];actions=[]
    for s in numeric['stocks']:
        f=read(s['fact_path']);r=rows[s['identity']];label=LABELS[r['status']]
        key=sha(encode([index['scan_id'],r['record_sha256'],s['fact']['sha256']]))
        st={k:f[k] for k in ['identity','code','market','isin','cfi','as_of','name']}
        st.update(status=f['source_status'],preview_evidence=s['fact'],result_key=None,quote_card=dict(close=f['bar']['close'],volume=f['bar']['volume_shares_scaled']) if f['bar'] else None,scan=dict(status=r['status'],label=label,core_calls=r['core_calls'],record_sha256=r['record_sha256']),decision=dict(headline=label,key_caption='尚無合格結構價位',risk='僅單日可比資料' if r['core_calls']==1 else f['source_label'],volume_label='缺少可比前筆量',can_judge=False),lazy_graph=dict(path='lazy-'+key+'.json',request_id=key))
        stocks.append(st)
        actions.append(dict(**{k:s[k] for k in ['identity','code','market','isin','cfi','as_of']},fact=s['fact'],fact_path=s['fact_path'],request_id=key,local_route=st['lazy_graph']['path']))
    state.update(stocks=stocks,scan_summary=ss,batch_id=read(numeric['stocks'][0]['fact_path'])['batch_id'],quote_capture_id=numeric['capture_id'],daily_sources=numeric['daily_sources'],radar_dates=[],radar_types=[],radar_routes={},asset_index=None)
    state['summary']=dict(as_of=index['as_of'],status='ANALYSIS_COMPLETE_WITH_LIMITATIONS',expected=index['expected'],charts=0,quotes_available=ss['executed'],quotes_refused=ss['refused'])
    # This shell reuses the exact original viewer; latest status is authenticated
    # and loaded separately so a blocked future intake never changes old prices.
    raw,_=compile_view(state,index['as_of'])
    extra=Path(__file__).with_name('product.js').read_text()
    raw=raw.replace(b'</body>',('<script>'+extra+'</script></body>').encode())
    target=folder/('market-product-'+sha(raw)+'.html')
    capacity(work,len(raw)+4096)
    from rotation_research.artifact_codec import immutable
    immutable(target,raw)
    entry=dict(run_id='formal-'+index['scan_id'],as_of=index['as_of'],**descriptor(target))
    original=read(BASE/'scan1_20261104/view-build-private.json')
    oldcatalog=read(original['catalogue'])['batches']
    previous=[]
    head=work/'head-private.json'
    if head.exists():
        from .flow import bound
        prev=bound(read(head));previous=read(prev['view']['catalogue'])['batches']
    seen={entry['path']};entries=[entry]
    for item in previous+oldcatalog:
        if item['path'] not in seen:entries.append(item);seen.add(item['path'])
    catalogue=encode(dict(schema='private-saved-batches/0.1',batches=entries));cp=work/('batches-'+sha(catalogue)+'.json');put(work,cp,catalogue)
    prefix='batch-'+entry['sha256']+'/'
    for a in actions:a['route']=prefix+a.pop('local_route');a['fact_route']=prefix+a['fact']['path']
    template=read(original['action_manifest'])
    template.update(actions=actions,capture_id=numeric['capture_id'],metrics_route=prefix+'lazy-status.json',scan_index=descriptor(scanwork/'complete-index.json'),scan_manifest=descriptor(scanwork/'manifest-private.json'),original_daily_sources={m:numeric['original_sources'][lower+'-daily.json'] for m,lower in [('TWSE','twse'),('TPEX','tpex')]})
    actionbody=encode(template);ap=work/('actions-'+sha(actionbody)+'.json');put(work,ap,actionbody)
    providers=[descriptor(ap)]
    if head.exists():providers+=prev['view']['providers']
    providers+=[dict(path=original['action_manifest'],bytes=Path(original['action_manifest']).stat().st_size,sha256=original['action_sha256'])]
    unique={d['sha256']:d for d in providers}
    return dict(catalogue=str(cp),catalogue_descriptor=descriptor(cp),entry=entry,providers=list(unique.values()),html_bytes=len(raw),scan_summary=ss)
