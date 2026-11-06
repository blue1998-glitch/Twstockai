"""One dated stage; never requests the already captured TPEX daily endpoint."""
import json,time,resource,shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.request import build_opener
from graph_core import market_daily as d,market_increment as inc
from graph_core.prod_core1_20261105 import flow as f
from graph_core.prod_day2_20261105 import capture as store
from graph_core.prod_day2_20261105.transport import receive,TransferFailure
from graph_core.day1_20261103.probe_once import NoRedirect,heads
WORK=f.BASE/'prod_day4_20261106'
TARGET='2026-11-05'
EXPECTED_SHA='90417d229be64406bc7ac59a858093445746d4d4a47f9b098c37e4ac687e2e54'
EXPECTED_BYTES=5329099
ORDER=['twse-daily.json','twse-universe.json','tpex-universe.json','TWSE-classification.html','TPEX-classification.html']

def saved_tpex():
    r=f.read(f.BASE/'prod_source3_20261105/range-result-private.json');desc=r['complete_body'];t=r['trace']
    if (desc['bytes'],desc['sha256'],r['source_date'],t['http_status'],t['complete'],t['old_prefix_used'],t['effective_url'])!=(EXPECTED_BYTES,EXPECTED_SHA,TARGET,200,True,False,d.URLS['tpex-daily.json']):raise ValueError('SAVED_TPEX_ROLE_VERSION_CONFLICT')
    raw=store.c.read_bytes(desc['path'],expected_bytes=EXPECTED_BYTES,expected_sha=EXPECTED_SHA)
    day,rows=d.quote_map(json.loads(raw),'TPEX')
    if day!=TARGET:raise ValueError('SAVED_TPEX_DATE_CONFLICT')
    return dict(name='tpex-daily.json',url=d.URLS['tpex-daily.json'],status='RECEIVED',sha256=EXPECTED_SHA,bytes=EXPECTED_BYTES,fetched_at=t['completed_at']),dict(path=desc['path'],bytes=EXPECTED_BYTES,sha256=EXPECTED_SHA,role='REUSED_COMPLETE_INDEPENDENT_HTTP200'),dict(original_HTTP=t['http_status'],original_started_at=t['started_at'],original_completed_at=t['completed_at'],etag=t['headers']['etag'],last_modified=t['headers']['last-modified'],date=day,rows=len(rows),new_GETs=0)

def run(work=WORK,opener=None):
    work=f.daily.outside(work)
    if TARGET>=datetime.now(ZoneInfo('Asia/Taipei')).date().isoformat():raise ValueError('PRIOR_CLOSED_DATE_ONLY')
    reused,desc,provenance=saved_tpex();done=work/'source-result-private.json'
    if done.exists():
        r=f.read(done)
        for x in f.read(work/'source-files-private.json').values():store.c.read_bytes(x['path'],expected_bytes=x['bytes'],expected_sha=x['sha256'])
        for t in r['http_trace']:
            if t.get('partial'):store.c.read_bytes(t['partial']['path'],expected_bytes=t['partial']['bytes'],expected_sha=t['partial']['sha256'])
        return dict(r,this_execution_GETs=0,reused=True)
    work=store.init(work)
    receipts={'tpex-daily.json':reused};files={EXPECTED_SHA:desc};trace=[];calls=0;started=time.monotonic();total=EXPECTED_BYTES;failure=None
    before=heads(f.BASE/'fm3_20261101/runtime');product=f.descriptor(f.WORK/'head-private.json');opener=opener or build_opener(NoRedirect())
    for name in ORDER:
        url=d.URLS[name];marker=work/'attempts'/(name+'.json');saved=work/'receipts'/(name+'.json')
        if saved.exists():
            item=f.read(saved);trace.append(item['trace'])
            if item['receipt']['status']!='RECEIVED':failure=item['receipt'].get('error','REFUSED_SOURCE');break
            receipts[name]=item['receipt'];files.update(item['files']);total+=item['receipt']['bytes'];continue
        if marker.exists():failure='INTERRUPTED_OUTCOME_UNKNOWN_NO_RETRY';break
        store.guard(work,1024**2);store.put(work,marker,store.c.encoded(dict(url=url,started_at=store.STAMP(),maximum_GETs=1)))
        calls+=1;newfiles={}
        try:
            raw,t=receive(opener,url,stamp=store.STAMP,max_seconds=min(180,max(0,600-(time.monotonic()-started))),max_body=min(16*1024**2,32*1024**2-total))
            h=store.c.sha(raw);path=work/'capture/raw'/h;store.save_exact(work,path,raw);total+=len(raw)
            row=dict(name=name,url=url,status='RECEIVED',sha256=h,bytes=len(raw),fetched_at=t['completed_at']);newfiles[h]=dict(path=str(path),bytes=len(raw),sha256=h,role='NEW_COMPLETE_HTTP_BODY_DU2')
            if name=='twse-daily.json':
                day,_=d.quote_map(json.loads(raw),'TWSE');t['parsed_source_date']=day
                if day!=TARGET:row.update(status='DATE_MISMATCH',error='TWSE_SOURCE_DAY_'+day+'_NOT_'+TARGET)
        except TransferFailure as error:
            t=error.trace;row=dict(name=name,url=url,status='SOURCE_FAILURE',error=str(error))
            if error.partial:
                h=store.c.sha(error.partial);path=work/'partial-not-qualified'/h;store.save_exact(work,path,error.partial);t['partial']=dict(path=str(path),bytes=len(error.partial),sha256=h)
        t['name']=name;store.put(work,saved,store.c.encoded(dict(receipt=row,trace=t,files=newfiles)));trace.append(t);files.update(newfiles)
        print(json.dumps(dict(source=name,status=row['status'],HTTP=t.get('http_status'),bytes=t.get('bytes'),reason=row.get('error'))),flush=True)
        if row['status']!='RECEIVED':failure=row.get('error','REFUSED_SOURCE');break
        receipts[name]=row
    ordered=[receipts[name] for name in d.URLS if name in receipts];cid=store.c.sha(d.encode(ordered));store.put(work,work/'capture/captures'/(cid+'.json'),d.encode(ordered));store.put(work,work/'source-files-private.json',store.c.encoded(files))
    try:
        if failure:raise ValueError(failure)
        day,maps,markets,sigs=inc.sources(store.Sources(work/'capture',files),cid)
        if day!=TARGET:raise ValueError('SIX_SOURCE_DATE_CONFLICT')
        gate=dict(status='SOURCE_QUALIFIED',as_of=day,ordinary_reference={m:len(u['members']) for m,u in markets.items()},membership_time_coverage={m:u['historical_membership_at_as_of'] for m,u in markets.items()})
    except Exception as error:gate=dict(status='BLOCKED_SOURCE',reason=type(error).__name__+': '+str(error))
    if heads(f.BASE/'fm3_20261101/runtime')!=before or f.descriptor(f.WORK/'head-private.json')!=product:raise ValueError('ORIGINAL_HEAD_CHANGED')
    result=dict(schema='prod-day4-intake/1.0',target_date=TARGET,qualification=gate,reused_tpex=provenance,receipts=ordered,capture_id=cid,http_trace=trace,this_execution_GETs=calls,reused=False,retries=0,remaining_not_requested=[x for x in ORDER if x not in {t['name'] for t in trace}],old_product_head=product,source_heads=before,wall_seconds=time.monotonic()-started,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,free_bytes=shutil.disk_usage(work).free)
    store.put(work,done,store.c.encoded(result));return result
if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));r=run();print(json.dumps({k:r[k] for k in ['qualification','this_execution_GETs','reused','remaining_not_requested','free_bytes']},ensure_ascii=False))
