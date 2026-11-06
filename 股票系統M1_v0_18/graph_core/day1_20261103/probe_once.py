"""One M-DAY1 bounded capture through existing six-source daily pipeline.
No engine/indicator calls, retries, alternate sources, schedules or head writes.
Full originals/HTTP trace stay private; stdout is non-reconstructable summary.
"""
import argparse,hashlib,json,os,resource,shutil,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import build_opener,HTTPRedirectHandler
from unittest.mock import patch
from zoneinfo import ZoneInfo
from graph_core import market_daily as daily,market_increment as increment
from rotation_research import artifact_codec as codec
from rotation_research.private_portability import private,quiet_source

RESERVE=512*1024*1024
SAFE_HEADERS={'content-type','content-length','date','last-modified','etag','content-encoding','transfer-encoding','location'}
def stamp():return datetime.now(timezone.utc).isoformat()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def heads(root):
    return {name:dict(exists=(root/name).exists(),sha256=sha((root/name).read_bytes()) if (root/name).exists() else None) for name in ['fm3-continuation.json','current-increment-run.json','current-run.json','current-finmind-run.json']}
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def probe(root,destination):
    started=time.monotonic();root=private(root);dest=private(destination)
    if not root.is_dir():raise ValueError('ORIGINAL_FM3_REQUIRED_NO_BACKFILL')
    if root==dest or dest.is_relative_to(root) or root.is_relative_to(dest):raise ValueError('SEPARATE_PRIVATE_CAPTURE_REQUIRED')
    dest.mkdir(mode=0o700,parents=True,exist_ok=True)
    marker=dest/'single-attempt.json'
    if marker.exists():raise FileExistsError('ATTEMPT_ALREADY_STARTED_NO_RETRY')
    before=heads(root);free=shutil.disk_usage(root).free
    if free<RESERVE+16*1024*1024:raise OSError('CAPACITY_BELOW_SAFE_CAPTURE_RESERVE_NO_REQUEST')
    codec.immutable(marker,codec.encoded(dict(started_at=stamp(),planned_urls=list(daily.URLS.values()),maximum_gets=len(daily.URLS),retry=False)))
    source=json.loads((root/'fm3-continuation.json').read_bytes());seed_id=json.loads((root/'current-increment-run.json').read_bytes())['id'] if (root/'current-increment-run.json').exists() else source['result']['id']
    parent=increment.seed(root,seed_id);trace=[];opener=build_opener(NoRedirect())
    def capture_open(url,timeout):
        if url not in daily.URLS.values() or any(t['url']==url for t in trace):raise ValueError('DUPLICATE_OR_UNAUTHORIZED_SOURCE_REQUEST')
        item=dict(name=next(k for k,v in daily.URLS.items() if v==url),url=url,started_at=stamp(),http_status=None,headers={},redirect_followed=False,read_completed=False);trace.append(item)
        try:response=opener.open(url,timeout=timeout)
        except Exception as error:
            if isinstance(error,HTTPError):item.update(http_status=error.code,headers={k:v for k,v in error.headers.items() if k.lower() in SAFE_HEADERS})
            item.update(completed_at=stamp(),error_type=type(error).__name__)
            raise
        item.update(http_status=response.status,headers={k:v for k,v in response.headers.items() if k.lower() in SAFE_HEADERS},effective_url=response.geturl())
        class Meter:
            def __enter__(self):return self
            def __exit__(self,*args):response.close()
            def read(self):
                try:
                    raw=response.read();item.update(bytes=len(raw),sha256=sha(raw),read_completed=True)
                    length=response.headers.get('Content-Length');item['declared_bytes']=int(length) if length else None
                    if response.status!=200 or response.geturl()!=url or (length and int(length)!=len(raw)):raise ValueError('HTTP_STATUS_URL_OR_COMPLETENESS_MISMATCH')
                    return raw
                except Exception as error:
                    partial=getattr(error,'partial',None)
                    if partial:
                        codec.immutable(dest/'partial-not-qualified'/sha(partial),partial);item.update(partial_bytes=len(partial),partial_sha256=sha(partial))
                    item.update(read_completed=False,error_type=type(error).__name__)
                    raise
                finally:item['completed_at']=stamp()
        return Meter()
    with quiet_source(root),patch.object(daily,'urlopen',capture_open):
        capture_id=daily.capture(dest)
        receipts=json.loads((dest/'captures'/(capture_id+'.json')).read_bytes())
        dates={};counts={};parse_errors={}
        for market,lower in [('TWSE','twse'),('TPEX','tpex')]:
            r=next(x for x in receipts if x['name']==lower+'-daily.json')
            if r['status']!='RECEIVED':parse_errors[market]='SOURCE_NOT_RECEIVED';continue
            try:dt,rows=daily.quote_map(json.loads((dest/'raw'/r['sha256']).read_bytes()),market);dates[market]=dt;counts[market]=len(rows)
            except Exception as error:parse_errors[market]=type(error).__name__+': '+str(error)
        try:
            as_of,maps,markets,signatures=increment.sources(dest,capture_id)
            if as_of<=parent['as_of']:raise ValueError('SOURCE_NOT_NEWER_THAN_LAST_VALID_HEAD')
            qualification=dict(status='READY_FOR_REAL_INCREMENT',as_of=as_of,ordinary_reference={m:len(v['members']) for m,v in markets.items()},source_signatures=signatures)
        except Exception as error:qualification=dict(status='BLOCKED_REAL_NEW_SESSION',reason=type(error).__name__+': '+str(error))
        after=heads(root)
        if before!=after:raise ValueError('HEAD_CHANGED_DURING_READONLY_CAPTURE')
    trace_record=dict(capture_id=capture_id,attempts=trace,retries=0,alternate_urls=0,private_raw_payloads=True,original_root_unchanged=True)
    codec.immutable(dest/'http-trace-private.json',codec.encoded(trace_record))
    report=dict(milestone='M-DAY1',status=qualification['status'],qualification=qualification,candidate_date='2026-11-02',actual_market_dates=dates,daily_source_rows=counts,source_parse_errors=parse_errors,
        original_as_of=parent['as_of'],original_reference_count=len(parent['stocks']),actual_new_stock_processing=0,new_core_calls=0,indicator_calls=0,real_new_workspace=False,source_get_attempts=len(trace),complete_sources=sum(x['status']=='RECEIVED' for x in receipts),source_failures=[dict(name=x['name'],error_type=next(t for t in trace if t['name']==x['name']).get('error_type')) for x in receipts if x['status']!='RECEIVED'],
        capture_id=capture_id,heads_before=before,heads_after=after,head_unchanged=before==after,free_before_bytes=free,free_after_bytes=shutil.disk_usage(root).free,reserve_bytes=RESERVE,
        wall_seconds=time.monotonic()-started,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,observed_at=stamp(),qualification_clock_taipei=datetime.now(ZoneInfo('Asia/Taipei')).isoformat(),capture_new_file_allocated_bytes=sum(p.stat().st_blocks*512 for p in dest.rglob('*') if p.is_file()),
        same_source_rerun='NOT_EXECUTED_SOURCE_NOT_YET_APPLIED',du2_increment='NOT_EXECUTED_PENDING_SOURCE_QUALIFICATION',schedule_started=False,server_started=False,external_deployment=False,independent_backup='UNKNOWN')
    codec.immutable(dest/'probe-private.json',codec.encoded(report));print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--destination',required=True);a=p.parse_args();v=probe(a.root,a.destination)
    if v['status']!='READY_FOR_REAL_INCREMENT':raise SystemExit(2)
