"""One bounded repair of TWO HTTP200 reads cut by our local 4MiB guard.
Never retry source denials; reuse the four complete original bodies unchanged.
"""
import json,shutil,time
from urllib.request import build_opener
from graph_core.day1_20261103.probe_once import NoRedirect,SAFE_HEADERS,stamp,heads
from graph_core.day2_compact_20261104.capture_once import ROOT,WORK,CAPTURE,MIN_FREE
from graph_core import market_daily as d,market_increment as inc
from rotation_research import artifact_codec as c

LIMIT=16*1024**2

def write(p,b):
    if not Path(p).resolve().is_relative_to(WORK.resolve()):raise ValueError('OUTSIDE_PRIVATE_STAGE')
    if not Path(p).exists() and shutil.disk_usage(WORK).free<MIN_FREE+len(b)+8*1024**2:raise OSError('MINIMUM_RESERVE_NO_WRITE')
    c.immutable(p,b)
from pathlib import Path

def run():
    marker=WORK/'local-size-repair-attempt.json'
    if marker.exists():raise FileExistsError('REPAIR_ALREADY_ATTEMPTED_NO_REPEAT')
    prior=json.loads((WORK/'capture-summary-private.json').read_bytes());capture_id=prior['capture_id']
    rows=json.loads((CAPTURE/'captures'/(capture_id+'.json')).read_bytes());trace=json.loads((CAPTURE/'http-trace-private.json').read_bytes())
    failed=[r for r in rows if r['status']!='RECEIVED']
    if {r['name'] for r in failed}!={'tpex-daily.json','TWSE-classification.html'}:raise ValueError('NOT_THE_TWO_LOCAL_GUARD_FAILURES')
    for r in failed:
        observed=next(t for t in trace['attempts'] if t['name']==r['name'])
        if r['error']!='ValueError: BOUNDED_OFFICIAL_SOURCE_SIZE_EXCEEDED' or observed['http_status']!=200:raise ValueError('EXTERNAL_FAILURE_OR_DENIAL_MUST_NOT_BE_RETRIED')
    if shutil.disk_usage(WORK).free < MIN_FREE+2*LIMIT+8*1024**2:raise OSError('REPAIR_CAPACITY_PREFLIGHT')
    before=heads(ROOT);write(marker,c.encoded(dict(started_at=stamp(),reason='OWN_LOCAL_LIMIT_TOO_SMALL_NOT_PROVIDER_DENIAL',urls=[r['url'] for r in failed],maximum_extra_GETs=2,limit_per_response=LIMIT,original_complete_sources_reused=4)))
    opener=build_opener(NoRedirect());newtrace=[];complete={}
    for r in failed:
        item=dict(name=r['name'],url=r['url'],started_at=stamp(),http_status=None,redirects_followed=False,headers={});parts=[]
        print(json.dumps(dict(phase='REPAIR_LOCAL_LIMIT_ONLY',source=r['name'],started_at=item['started_at'])),flush=True)
        try:
            with opener.open(r['url'],timeout=35) as response:
                item.update(http_status=response.status,headers={k:v for k,v in response.headers.items() if k.lower() in SAFE_HEADERS})
                if response.status!=200 or response.geturl()!=r['url']:raise ValueError('HTTP_STATUS_OR_REDIRECT_STOP')
                declared=response.headers.get('Content-Length')
                if declared and int(declared)>LIMIT:raise ValueError('DECLARED_BODY_EXCEEDS_REPAIR_LIMIT')
                start=time.monotonic();n=0
                while True:
                    block=response.read(min(1024**2,LIMIT+1-n))
                    if not block:break
                    parts.append(block);n+=len(block)
                    if n>LIMIT or time.monotonic()-start>480:raise ValueError('REPAIR_SIZE_OR_WALL_LIMIT_STOP_NO_RETRY')
                raw=b''.join(parts)
                if declared and int(declared)!=len(raw):raise ValueError('INCOMPLETE_HTTP_BODY')
                sha=d.digest(raw);write(CAPTURE/'raw'/sha,raw)
                complete[r['name']]=dict(name=r['name'],url=r['url'],sha256=sha,bytes=len(raw),fetched_at=stamp(),status='RECEIVED')
                item.update(bytes=len(raw),sha256=sha,complete=True)
        except Exception as e:
            item.update(complete=False,error=type(e).__name__+': '+str(e))
            if parts:
                partial=b''.join(parts);h=d.digest(partial);write(WORK/'partial-not-qualified'/h,partial);item.update(partial_bytes=len(partial),partial_sha256=h)
        item['completed_at']=stamp();newtrace.append(item)
        print(json.dumps({k:v for k,v in item.items() if k in ('name','http_status','bytes','complete','error','completed_at')}),flush=True)
    assembled=[complete.get(r['name'],r) for r in rows];new_id=d.digest(d.encode(assembled));write(CAPTURE/'captures'/(new_id+'.json'),d.encode(assembled))
    try:
        as_of,maps,markets,signatures=inc.sources(CAPTURE,new_id)
        parent=inc.seed(ROOT,json.loads((ROOT/'current-increment-run.json').read_bytes())['id'])
        if as_of<=parent['as_of']:raise ValueError('SOURCE_NOT_NEWER_THAN_LAST_VALID_HEAD')
        q=dict(status='READY_FOR_REAL_INCREMENT',as_of=as_of,ordinary_reference={m:len(v['members']) for m,v in markets.items()},source_signatures=signatures,daily_rows={m:len(v) for m,v in maps.items()})
    except Exception as e:q=dict(status='BLOCKED_REAL_NEW_SESSION',reason=type(e).__name__+': '+str(e))
    after=heads(ROOT)
    if before!=after:raise ValueError('ORIGINAL_HEAD_CHANGED')
    result=dict(milestone='M-DAY2-COMPACT',candidate_date='2026-11-03',qualification=q,capture_id=new_id,
        prior_incomplete_capture_id=capture_id,GETs_total=8,first_attempt_GETs=6,local_limit_repair_GETs=2,
        complete_old_bodies_reused=4,repair_requests=newtrace,provider_denials_retried=0,alternate_urls=0,
        original_heads_before=before,original_heads_after=after,head_unchanged=True,
        free_bytes=shutil.disk_usage(WORK).free,new_core_calls=0,source_errors_not_hidden=True)
    write(WORK/'repaired-source-private.json',c.encoded(result))
    print(json.dumps({k:v for k,v in result.items() if k not in ('repair_requests','original_heads_before','original_heads_after')},ensure_ascii=False),flush=True)
if __name__=='__main__':run()
