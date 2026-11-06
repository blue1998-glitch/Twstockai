"""Repair the one failed TPEX transfer, reuse the three complete originals.
The exact existing source gate reads lossless DU2 bytes through a small IO view;
no parser/date/identity/company-action policy is replaced. New bytes stay private.
"""
import argparse,gzip,json,os,shutil,time,resource,math
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import build_opener
from graph_core import market_daily as daily,market_increment as inc
from graph_core.daily_chain1_20261104.intake import safe_target
from graph_core.day1_20261103.probe_once import NoRedirect,heads
from graph_core.prod_core1_20261105 import flow
from rotation_research import artifact_codec as c
from .transport import receive,TransferFailure
WORK=flow.BASE/'prod_day2_20261105'
OLD=flow.WORK/'intake/2026-11-04'
STAMP=lambda:datetime.now(timezone.utc).isoformat()
LIMIT=32*1024**2

def init(work=WORK):
    work=flow.daily.outside(work)
    if shutil.disk_usage(work.parent).free<flow.RESERVE+1024**2:raise OSError('DAY2_RESERVE_PREFLIGHT')
    work.mkdir(mode=0o700,parents=True,exist_ok=True)
    if not (work/'baseline-private.json').exists():c.immutable(work/'baseline-private.json',c.encoded(dict(free_bytes=shutil.disk_usage(work).free)))
    return work

def guard(work,n=0):
    free=shutil.disk_usage(work).free
    if free-n<flow.RESERVE+65536 or flow.read(work/'baseline-private.json')['free_bytes']-free+n>LIMIT:raise OSError('DAY2_CAPACITY_STOP')

def put(work,path,body):
    c.regular(path,work);guard(work,0 if path.exists() else math.ceil(len(body)/4096)*4096);c.immutable(path,body)

def save_exact(work,path,raw):
    if c.exists(path):
        if c.read_bytes(path)!=raw:raise ValueError('IMMUTABLE_SOURCE_CONFLICT')
        return
    # Only NEW source bodies use the original DU2 lossless codec. Old raw bytes
    # and old partials stay untouched; this is storage, not source qualification.
    estimated=sum(math.ceil(len(gzip.compress(b,mtime=0))/4096)*4096 for _,b in c.chunks(raw))+65536
    guard(work,estimated);c.publish(path,raw,root=work)
    assert c.read_bytes(path,expected_bytes=len(raw),expected_sha=c.sha(raw))==raw

class SourcePath:
    def __init__(self,root,parts=()):self.root=root;self.parts=parts
    def __truediv__(self,value):return SourcePath(self.root,self.parts+(str(value),))
    def actual(self):
        if len(self.parts)==2 and self.parts[0]=='raw':
            desc=self.root.files.get(self.parts[1])
            if not desc or desc['sha256']!=self.parts[1]:raise ValueError('SOURCE_NOT_ALLOWLISTED')
            return Path(desc['path'])
        if len(self.parts)==2 and self.parts[0]=='captures' and self.parts[1].endswith('.json'):return self.root.path.joinpath(*self.parts)
        raise ValueError('SOURCE_IO_VIEW_PATH_REFUSED')
    def is_symlink(self):return self.actual().is_symlink()
    def read_bytes(self):
        p=self.actual()
        if any(x.is_symlink() for x in (p,*p.parents)):raise ValueError('SOURCE_SYMLINK_REFUSED')
        if self.parts[0]=='raw':
            d=self.root.files[self.parts[1]]
            return c.read_bytes(p,expected_bytes=d['bytes'],expected_sha=d['sha256'])
        return p.read_bytes()
class Sources(SourcePath):
    def __init__(self,path,files):self.path=Path(path);self.files=files;super().__init__(self)

def run(target='2026-11-04',*,work=WORK,old=OLD,opener=None):
    safe_target(target);work=init(work);done=work/'result-private.json'
    if done.exists():
        report=flow.read(done);assert report['target_date']==target
        files=flow.read(work/'source-files-private.json')
        for d in files.values():c.read_bytes(d['path'],expected_bytes=d['bytes'],expected_sha=d['sha256'])
        for t in report['http_trace']:
            if t.get('partial_sha256'):c.read_bytes(work/'partial-not-qualified'/t['partial_sha256'],expected_bytes=t['partial_bytes'],expected_sha=t['partial_sha256'])
        return dict(report,this_execution_GETs=0,reused=True)
    original=flow.read(old/'result-private.json')
    if original['target_date']!=target:raise ValueError('REPAIR_TARGET_CONFLICT')
    if any(t.get('http_status') in (301,302,303,307,308,401,403,429) for t in original['http_trace']):raise ValueError('PRIOR_DENIAL_NO_REPAIR_ATTEMPT')
    previous=original['receipts'];receipts=[];files={};trace=[];calls=0;started=time.monotonic()
    before=heads(flow.BASE/'fm3_20261101/runtime');product_head=flow.descriptor(flow.WORK/'head-private.json')
    opener=opener or build_opener(NoRedirect())
    for i,(name,url) in enumerate(daily.URLS.items()):
        oldrow=next((r for r in previous if r['name']==name and r['status']=='RECEIVED'),None)
        if oldrow:
            if oldrow['url']!=url:raise ValueError('OLD_SOURCE_URL_CONFLICT')
            p=old/'capture/raw'/oldrow['sha256'];b=p.read_bytes()
            if len(b)!=oldrow['bytes'] or c.sha(b)!=oldrow['sha256']:raise ValueError('OLD_COMPLETE_SOURCE_CHANGED')
            files[oldrow['sha256']]=dict(path=str(p),bytes=len(b),sha256=c.sha(b),role='REUSED_COMPLETE_ORIGINAL')
            receipts.append(oldrow);continue
        marker=work/'attempts'/(name+'.json');saved=work/'receipts'/(name+'.json')
        if saved.exists():
            item=flow.read(saved);trace.append(item['trace']);receipts.append(item['receipt']);files.update(item['files'])
            if item['receipt']['status']!='RECEIVED':break
            continue
        if marker.exists():
            trace.append(dict(name=name,url=url,complete=False,error='INTERRUPTED_OUTCOME_UNKNOWN_NO_RETRY'));break
        guard(work,1024**2);put(work,marker,c.encoded(dict(name=name,url=url,started_at=STAMP(),new_whole_GET=True,no_retry=True)))
        added={};calls+=1
        try:
            raw,t=receive(opener,url,stamp=STAMP,max_seconds=min(180,max(0,480-(time.monotonic()-started))))
            digest=c.sha(raw);path=work/'capture/raw'/digest;save_exact(work,path,raw)
            added[digest]=dict(path=str(path),bytes=len(raw),sha256=digest,role='NEW_EXACT_HTTP_BODY_DU2')
            receipt=dict(name=name,url=url,status='RECEIVED',sha256=digest,bytes=len(raw),fetched_at=t['completed_at'])
        except TransferFailure as error:
            t=error.trace;receipt=dict(name=name,url=url,status='SOURCE_FAILURE',error=str(error))
            if error.partial:
                digest=c.sha(error.partial);path=work/'partial-not-qualified'/digest;save_exact(work,path,error.partial);t.update(partial_bytes=len(error.partial),partial_sha256=digest)
        t['name']=name;put(work,saved,c.encoded(dict(receipt=receipt,trace=t,files=added)))
        receipts.append(receipt);files.update(added);trace.append(t)
        print(json.dumps(dict(source=name,status=receipt['status'],HTTP=t.get('http_status'),bytes=t.get('bytes'),received=t.get('received_bytes'),reason=t.get('error'))),flush=True)
        if receipt['status']!='RECEIVED':break
    cid=c.sha(daily.encode(receipts));put(work,work/'capture/captures'/(cid+'.json'),daily.encode(receipts));put(work,work/'source-files-private.json',c.encoded(files))
    source_root=Sources(work/'capture',files);dates={}
    for market,lower in [('TWSE','twse'),('TPEX','tpex')]:
        row=next((r for r in receipts if r['name']==lower+'-daily.json' and r['status']=='RECEIVED'),None)
        if row:dates[market]=daily.quote_map(json.loads((source_root/'raw'/row['sha256']).read_bytes()),market)[0]
    try:
        day,maps,markets,sigs=inc.sources(source_root,cid)
        if day!=target:raise ValueError('SOURCE_DATE_NOT_TARGET')
        gate=dict(status='SOURCE_QUALIFIED',as_of=day,markets={m:len(x['members']) for m,x in markets.items()})
    except Exception as error:gate=dict(status='BLOCKED_SOURCE',reason=type(error).__name__+': '+str(error))
    if heads(flow.BASE/'fm3_20261101/runtime')!=before or flow.descriptor(flow.WORK/'head-private.json')!=product_head:raise ValueError('ORIGINAL_PRODUCT_OR_SOURCE_HEAD_CHANGED')
    report=dict(schema='prod-day2-source-repair/1.0',target_date=target,qualification=gate,actual_market_dates=dates,capture_id=cid,receipts=receipts,http_trace=trace,reused_complete_originals=sum(r.get('status')=='RECEIVED' for r in previous),this_execution_GETs=calls,reused=False,retries=0,original_product_head=product_head,old_attempt_unchanged=True,wall_seconds=time.monotonic()-started,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,free_bytes=shutil.disk_usage(work).free)
    put(work,done,c.encoded(report));return report
if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    p=argparse.ArgumentParser();p.add_argument('--date',default='2026-11-04');a=p.parse_args();r=run(a.date);print(json.dumps({k:r[k] for k in ['qualification','actual_market_dates','this_execution_GETs','reused','free_bytes']},ensure_ascii=False))
