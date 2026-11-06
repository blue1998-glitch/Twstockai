"""Immutable tiny daily facts and existing LITE shell. No original root writes."""
import json,time,resource,collections,shutil
from pathlib import Path
from unittest.mock import patch
from graph_core import market_increment as inc,market_daily as d
from graph_core.lite1_20261103.render import render
from rotation_research import artifact_codec as c
from rotation_research.store import Journal
from .common import ROOT,WORK,BASE,CAPTURE,write,encode,sha,read_json,budget,protected_heads
from .facts import project

def build():
    started=time.monotonic();budget()
    capture=read_json(BASE/'day2_compact_20261104/repaired-source-private.json')['capture_id']
    producer_sha=sha(Path(__file__).with_name('facts.py').read_bytes());binding=dict(capture_id=capture,producer_sha256=producer_sha,version='official-daily-facts/0.1')
    batch_id='quotes-'+sha(encode(binding));done=WORK/'facts-build-private.json'
    if done.exists():
        r=read_json(done)
        if r['binding']!=binding:raise ValueError('NEW_SOURCE_OR_PRODUCER_REQUIRES_NEW_VERSION')
        state=read_json(r['state_path'])
        for s in state['stocks']:
            desc=s['preview_evidence'];raw=(Path(r['state_path']).parent/desc['path']).read_bytes()
            if len(raw)!=desc['bytes'] or sha(raw)!=desc['sha256']:raise ValueError('EXISTING_FACT_CHANGED_NO_REPAIR')
        return dict(r,reused=True,new_stock_writes=0,new_bytes=0,new_core_calls=0)
    budget(12*1024**2)
    heads_before=protected_heads()
    # Existing same-source/date/CFI checks; no provider capture or engine call.
    as_of,maps,markets,signatures=inc.sources(CAPTURE,capture)
    head=read_json(ROOT/'current-increment-run.json');prior=Journal(ROOT/'runs').read(head['id'])['value'];previous={s['identity']:s for s in prior['stocks']}
    members=[m for x in markets.values() for m in x['members']]
    if set(previous)!={m['market']+':'+m['code'] for m in members}:raise ValueError('REFERENCE_CHANGED_EXPLICIT_CROSSWALK_REQUIRED')
    folder=WORK/'view'/as_of;folder.mkdir(mode=0o700,parents=True,exist_ok=True)
    stocks=[];data=[];counts={m:collections.Counter() for m in markets};pointers=[]
    for m in members:
        identity=m['market']+':'+m['code'];lower={'TWSE':'twse','TPEX':'tpex'}[m['market']]
        fact=project(m,maps[m['market']].get(m['code']),as_of=as_of,capture_id=capture,daily_sha256=signatures[lower+'-daily.json'],parent_isin=previous[identity].get('isin'))
        fact['batch_id']=batch_id;body=encode(fact);h=sha(body);desc=dict(path='series-'+h+'.json',sha256=h,bytes=len(body));write(folder/desc['path'],body)
        actual=(folder/desc['path']).read_bytes()
        if actual!=body:raise ValueError('NEW_FACT_EXACT_READBACK_FAILED')
        bar=fact['bar'];stocks.append(dict(identity=identity,code=m['code'],name=m['name'],market=m['market'],as_of=as_of,isin=m['isin'],cfi=m['cfi'],status=fact['source_status'],result_key=None,preview_evidence=desc,quote_card=dict(close=bar['close'],volume=bar['volume_shares_scaled']) if bar else None,decision=dict(headline=fact['source_label'],key_caption='尚未分析',volume_label='量未比較',risk='未執行當日圖形分析',can_judge=False)))
        data.append(desc);counts[m['market']][fact['source_status']]+=1
    asset=encode(dict(schema='private-lite-linked-assets/0.1',charts=[],data=data));h=sha(asset);write(folder/('assets-'+h+'.json'),asset)
    valid=sum(x['SOURCE_BAR_AVAILABLE'] for x in counts.values())
    old_index=read_json(read_json(BASE/'lite1_20261103/view-head-private.json')['batch_index'])
    links=[dict(as_of=e['as_of'],href='/batch-'+e['sha256']+'/'+Path(e['path']).name) for e in old_index['batches']]
    state=dict(saved_analysis_links=links,schema='private-lite-workbench/0.1',presentation='DAILY_QUOTES',summary=dict(as_of=as_of,expected=len(stocks),charts=0,status='OFFICIAL_QUOTES_ONLY_NOT_ANALYZED',quotes_available=valid,quotes_refused=len(stocks)-valid),stocks=stocks,radar_routes={},radar_dates=[],radar_types=[],batch_id=batch_id,quote_capture_id=capture,daily_sources={m:signatures[{'TWSE':'twse','TPEX':'tpex'}[m]+'-daily.json'] for m in markets},source_preview_sha256=None,asset_index=dict(path='assets-'+h+'.json',sha256=h,bytes=len(asset)))
    state_path=folder/'prepared-state-private.json';write(state_path,encode(state))
    preparation=dict(batches=[dict(as_of=as_of,folder=str(folder),source_run=batch_id,stocks=len(stocks),charts=0,original_events=0)])
    write(WORK/'view/preparation-private.json',encode(preparation))
    if protected_heads()!=heads_before:raise ValueError('ORIGINAL_HEAD_CHANGED')
    receipt=dict(binding=binding,batch_id=batch_id,as_of=as_of,state_path=str(state_path),identities=len(stocks),counts={m:dict(v) for m,v in counts.items()},source_bar_available=valid,source_refused=len(stocks)-valid,
        source_signatures=signatures,original_heads=heads_before,core_calls=0,source_GETs=0,history_copies=0,chart_copies=0,graph_analysis='NOT_EXECUTED',elapsed_seconds=time.monotonic()-started,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write(done,encode(receipt));return receipt

def make_view():
    # Existing renderer, template, search, CSS and original owner whitelist schema.
    with patch.object(c,'immutable',write):r=render(WORK/'view')
    prior_head=BASE/'lite1_20261103/view-head-private.json';saved=WORK/'original-view-head-private.json';old=saved.read_bytes() if saved.exists() else prior_head.read_bytes();old_index=read_json(json.loads(old)['batch_index']);new=read_json(r['catalogue'])
    combined=encode(dict(schema='private-saved-batches/0.1',batches=new['batches']+old_index['batches']))
    path=WORK/('batches-'+sha(combined)+'.json');write(path,combined)
    write(WORK/'original-view-head-private.json',old)
    return dict(new_catalogue=str(path),new_entry=new['batches'][0],old_entries=old_index['batches'],old_view_head_sha256=sha(old))
def run():
    if not (WORK/'classification-private.json').exists():raise ValueError('CLASSIFICATION_MUST_FINISH_FIRST')
    r=build();view=make_view();write(WORK/('view-build-'+sha(encode(view))+'.json'),encode(view))
    return dict(facts=r,view=view)
if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False))
