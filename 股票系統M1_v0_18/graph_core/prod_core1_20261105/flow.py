"""Manual-once formal daily flow. Private immutable checkpoints, no scheduler.
All source projection, numerical recognition and Journal semantics are reused.
Uncertified history is never joined; successful receipt precedes publication.
"""
import argparse,copy,fcntl,json,os,re,resource,shutil,time
from contextlib import contextmanager
from datetime import datetime,date
from zoneinfo import ZoneInfo
from pathlib import Path
from graph_core import market_increment as inc,market_daily as daily
from graph_core.scan1_20261104 import engine as scan
from graph_core.storage1_20261104.facts import project
from rotation_research import artifact_codec as codec
BASE=scan.BASE
WORK=BASE/'prod_core1_20261105'
VERSION='twstockai-daily-product/1.0'
RESERVE=536870912
BUDGET=32*1024**2
read=scan.read
sha=scan.sha
encode=scan.encode

def capacity(work,n=0):
    free=shutil.disk_usage(work).free
    initial=read(Path(work)/'baseline-private.json')['free_bytes']
    if free-n<RESERVE+65536 or initial-free+n>BUDGET:raise OSError('PRODUCT_CAPACITY_STOP')
    return free

def put(work,path,body):
    path=codec.regular(path,work);capacity(work,0 if path.exists() else ((len(body)+4095)//4096)*4096)
    codec.immutable(path,body)

def init(work=WORK):
    work=daily.outside(work)
    if any(a.is_symlink() for a in (work,*work.parents)):raise ValueError('PRIVATE_ROOT_SYMLINK')
    if not work.exists():
        if shutil.disk_usage(work.parent).free<RESERVE+2*1024**2:raise OSError('PRODUCT_PREFLIGHT_STOP')
        work.mkdir(mode=0o700)
    if not (work/'baseline-private.json').exists():
        codec.immutable(work/'baseline-private.json',encode(dict(free_bytes=shutil.disk_usage(work).free,reserve_bytes=RESERVE,budget_bytes=BUDGET)))
    return work

@contextmanager
def lease(work):
    put(work,work/'flow.lock',b'')
    with (work/'flow.lock').open('rb') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);yield

def point(work,name,value):
    body=encode(value);p=codec.regular(work/name,work)
    if p.exists() and p.read_bytes()==body:return
    temp=work/(name+'.pending-'+sha(body));put(work,temp,body)
    os.replace(temp,p)
    fd=os.open(work,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def descriptor(path):
    b=codec.regular(path).read_bytes();return dict(path=str(path),bytes=len(b),sha256=sha(b))

def bound(desc,limit=4*1024**2):
    p=codec.regular(Path(desc['path']));b=p.read_bytes()
    if len(b)>limit or len(b)!=desc['bytes'] or sha(b)!=desc['sha256']:raise ValueError('PRODUCT_DESCRIPTOR_CHANGED')
    return json.loads(b)

def source_check(scanwork,target):
    spec=read(scanwork/'manifest-private.json')
    if spec['as_of']!=target:raise ValueError('EXACT_DATE_REQUIRED_NO_FALLBACK')
    roots={str(Path(x['path']).parent.parent) for x in spec['original_sources'].values()}
    if len(roots)!=1:raise ValueError('SOURCE_CAPTURE_ROOT_CONFLICT')
    day,maps,markets,sigs=inc.sources(Path(next(iter(roots))),spec['capture_id'])
    if day!=target:raise ValueError('SOURCE_DATE_CONFLICT')
    current={m['market']+':'+m['code']:m for g in markets.values() for m in g['members']}
    # Retained previous identities can be absent from the current ordinary list,
    # but must remain explicit source-refused terminals, never silently disappear.
    stocks={s['identity']:s for s in spec['stocks']}
    if len(stocks)!=len(spec['stocks']) or not set(current)<=set(stocks):raise ValueError('INCOMPLETE_UNIVERSE')
    for identity,s in stocks.items():
        f=scan.fact(spec,s);m=current.get(identity)
        if m is None:
            if f['source_status']!='MISSING_QUOTE' or f['bar'] is not None:raise ValueError('REMOVED_IDENTITY_MUST_REFUSE')
            continue
        lower='twse' if m['market']=='TWSE' else 'tpex'
        expected=project(m,maps[m['market']].get(m['code']),as_of=day,capture_id=spec['capture_id'],daily_sha256=sigs[lower+'-daily.json'],parent_isin=s.get('parent_isin',s['isin']))
        expected['batch_id']=f['batch_id']
        if f!=expected:raise ValueError('EXACT_SOURCE_FACT_CONFLICT')
    return spec

def materialize(capture_root,capture_id,target,work):
    day,maps,markets,sigs=inc.sources(Path(capture_root),capture_id)
    if day!=target:raise ValueError('SOURCE_DATE_NOT_TARGET')
    old=read(BASE/'scan1_20261104/manifest-private.json')
    prior={s['identity']:s for s in old['stocks']}
    members={m['market']+':'+m['code']:m for g in markets.values() for m in g['members']}
    # Historical identity is retained with an explicit missing quote if absent.
    oldstate=read(BASE/'scan1_20261104/view-state-private.json')
    for s in oldstate['stocks']:
        if s['identity'] not in members:members[s['identity']]={k:s[k] for k in ['code','market','isin','cfi','name']}
    sw=work/'scans'/capture_id;sw.mkdir(mode=0o700,parents=True,exist_ok=True)
    put(work,sw/'baseline-private.json',encode(read(work/'baseline-private.json')))
    stocks=[]
    active={m['market']+':'+m['code'] for g in markets.values() for m in g['members']}
    for identity,m in sorted(members.items()):
        lower='twse' if m['market']=='TWSE' else 'tpex'
        raw=maps[m['market']].get(m['code']) if identity in active else None
        f=project(m,raw,as_of=day,capture_id=capture_id,daily_sha256=sigs[lower+'-daily.json'],parent_isin=prior.get(identity,{}).get('isin'))
        f['batch_id']=capture_id
        body=encode(f);h=sha(body);p=sw/'facts'/('series-'+h+'.json');put(work,p,body)
        stocks.append(dict(**{k:f[k] for k in ['identity','code','market','isin','cfi','as_of']},fact=dict(path=p.name,bytes=len(body),sha256=h),fact_path=str(p),parent_isin=prior.get(identity,{}).get('isin',f['isin'])))
    original={}
    for name,h in sigs.items():
        p=Path(capture_root)/'raw'/h;s=p.stat();original[name]=dict(path=str(p),sha256=h,metadata=[s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev])
    spec=dict(version=scan.VERSION,as_of=day,capture_id=capture_id,source_state_sha256=sha(encode(members)),protected_code=old['protected_code'],original_sources=original,daily_sources={m:sigs[lower+'-daily.json'] for m,lower in [('TWSE','twse'),('TPEX','tpex')]},stocks=stocks)
    spec['id']=sha(encode(spec));put(work,sw/'manifest-private.json',encode(spec));return sw

def release_id():
    folder=Path(__file__).parent
    return sha(encode({p.name:sha(p.read_bytes()) for p in sorted(folder.iterdir()) if p.suffix in ('.py','.js') and not p.name.startswith('test_')}))

def saved(target,*,scanwork=scan.WORK,work=WORK,limit=None):
    work=init(work);scanwork=Path(scanwork);started=time.monotonic()
    spec=source_check(scanwork,target)
    ident=sha(encode([VERSION,spec['id'],release_id()]))
    receipt_path=work/'runs'/(ident+'.json')
    # Original runner checks raw facts, original code pins and saved Journals on
    # every replay, including completed runs. Missing records are not repaired.
    result=scan.run(scanwork,limit=limit)
    if result['status']!='COMPLETE':
        return dict(status='PARTIAL',as_of=target,scan=result,publication_changed=False)
    if receipt_path.exists():
        receipt=read(receipt_path);bound(receipt['index']);bound(receipt['manifest'])
        point(work,'prepared-head-private.json',descriptor(receipt_path))
        return dict(receipt,reused=True,this_execution_new_core_calls=result['new_core_calls'],this_execution_new_records=result['new_records'],wall_seconds=time.monotonic()-started)
    index=read(scanwork/'complete-index.json')
    from .view import build
    view=build(scanwork,work)
    receipt=dict(schema=VERSION,status='COMPLETE',as_of=target,run_id=ident,scan=result,reference=index['expected'],markets=index['markets'],counts=index['counts'],manifest=descriptor(scanwork/'manifest-private.json'),index=descriptor(scanwork/'complete-index.json'),view=view,continuity='NOT_CERTIFIED_NO_HISTORY_APPENDED',meaningful_structure=0,execution_qualified=False,historical_signal_eligible=False,policy_authorized=False,primary_pressure_id=None,imputed_close=None,valuation=None,wall_seconds=time.monotonic()-started,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    put(work,receipt_path,encode(receipt))
    point(work,'prepared-head-private.json',descriptor(receipt_path))
    return dict(receipt,reused=False,this_execution_new_core_calls=result['new_core_calls'],this_execution_new_records=result['new_records'])

def fetch(target,*,work=WORK,attempt=None):
    from graph_core.daily_chain1_20261104 import intake
    intake.safe_target(target)
    if attempt is not None and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,31}',attempt):raise ValueError('EXPLICIT_SAFE_ATTEMPT_NAME_REQUIRED')
    work=init(work)
    if target>=datetime.now(ZoneInfo('Asia/Taipei')).date().isoformat():raise ValueError('PRIOR_CLOSED_DATE_ONLY')
    # Only an operator's explicit NEW name can recapture an incomplete transport.
    # Never turn an auth/rate/redirect denial into a new-name/date bypass.
    prior_reports=list((work/'intake').glob('*/result-private.json'))
    if len(prior_reports)>64:raise ValueError('INTAKE_HISTORY_REVIEW_REQUIRED')
    for previous in prior_reports:
        if any(x.get('http_status') in (301,302,303,307,308,401,403,429) for x in read(previous).get('http_trace',[])):raise ValueError('PRIOR_SOURCE_DENIAL_REQUIRES_REVIEW_NO_NEW_ATTEMPT')
    label=target if attempt is None else target+'--'+attempt
    stage=work/'intake'/label
    stage.mkdir(mode=0o700,parents=True,exist_ok=True)
    if not (stage/'baseline-private.json').exists():put(work,stage/'baseline-private.json',encode(read(work/'baseline-private.json')))
    report=intake.run(target,work=stage)
    # intake deliberately has no multiday authority. A SOURCE_QUALIFIED day may
    # be scanned as its OWN single-day segment, never as a history bridge.
    if report['qualification']['status']=='SOURCE_QUALIFIED':
        sw=materialize(stage/'capture',report['capture_id'],target,work)
        result=saved(target,scanwork=sw,work=work)
    else:result=dict(status='BLOCKED_SOURCE',target_date=target,reason=report['qualification']['reason'],observed_dates=report['actual_market_dates'],source_GETs=report['this_execution_GETs'],retry_same_attempt=False,active_head_preserved=True)
    record=work/'attempt-results'/(label+'-'+report['capture_id']+'.json')
    if not record.exists():put(work,record,encode(result))
    point(work,'latest-attempt-private.json',descriptor(record))
    return result

def status(work=WORK):
    work=Path(work);h=bound(read(work/'head-private.json')) if (work/'head-private.json').exists() else None
    a=bound(read(work/'latest-attempt-private.json')) if (work/'latest-attempt-private.json').exists() else None
    return dict(schema=VERSION,active_date=h['as_of'] if h else None,status=h['status'] if h else 'NOT_STARTED',reference=h['reference'] if h else None,counts=h['counts'] if h else {},latest_intake={k:a[k] for k in ['status','target_date','as_of','reason','observed_dates'] if a and k in a} if a else None,scheduled=False,android='ANDROID_EXTERNAL_NOT_CONNECTED',independent_backup='UNKNOWN',formal_strategy_authorized=False)

def main():
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['run','fetch','status','activate']);p.add_argument('--date');p.add_argument('--attempt');p.add_argument('--work',default=str(WORK));p.add_argument('--scan-work',default=str(scan.WORK));v=p.parse_args();
    if v.command=='status':
        print(json.dumps(status(Path(v.work)),ensure_ascii=False));return
    work=init(Path(v.work))
    with lease(work):
        if v.command in ('run','fetch') and not v.date:p.error('--date required')
        if v.command=='run':r=saved(v.date,scanwork=Path(v.scan_work),work=work)
        elif v.command=='fetch':r=fetch(v.date,work=work,attempt=v.attempt)
        elif v.command=='status':r=status(work)
        else:
            from .serve import activate
            r=activate(work)
    if v.command in ('run','fetch') and r.get('status')=='COMPLETE':
        from .serve import activate
        with lease(work):activate(work)
    print(json.dumps({k:r[k] for k in ['status','as_of','target_date','reference','counts','reused','this_execution_new_core_calls','this_execution_new_records','reason','active_date','latest_intake','scheduled','android'] if k in r},ensure_ascii=False))
if __name__=='__main__':main()
