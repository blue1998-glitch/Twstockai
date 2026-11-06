"""One Range/If-Range GET using the longest verified immutable prefix.
Default daily transport remains HTTP200 only. This caller alone allows206 after
version/window/header checks; a whole200 is independent and NEVER concatenated.
"""
import json,re,resource,time
from pathlib import Path
from urllib.request import Request,build_opener
from graph_core.prod_day2_20261105 import capture as store
from graph_core.prod_day2_20261105.transport import receive,TransferFailure,Refused
from graph_core.prod_core1_20261105 import flow
from graph_core.day1_20261103.probe_once import NoRedirect
from graph_core import market_daily as daily
WORK=flow.BASE/'prod_source3_20261105'
URL=daily.URLS['tpex-daily.json']

def choose_prefix(candidates):
    if not candidates:raise ValueError('NO_VERIFIED_PREFIX')
    versions=set();items=[]
    for path,t in candidates:
        headers={k.lower():v for k,v in t['headers'].items()};etag=headers.get('etag','')
        if not re.fullmatch(r'"[^"\r\n]+"',etag):raise ValueError('STRONG_ETAG_REQUIRED')
        if t['url']!=URL or t['http_status']!=200 or t['complete']:raise ValueError('ORIGINAL_PARTIAL_ROLE_REQUIRED')
        total=int(headers['content-length']);body=store.c.read_bytes(path,expected_bytes=t['partial_bytes'],expected_sha=t['partial_sha256'])
        if not 0<len(body)<total or not headers.get('last-modified'):raise ValueError('PARTIAL_LENGTH_OR_VERSION_INVALID')
        versions.add((etag,headers['last-modified'],total));items.append((body,dict(path=str(path),bytes=len(body),sha256=store.c.sha(body))))
    if len(versions)!=1:raise ValueError('PREFIX_VERSION_CONFLICT')
    items.sort(key=lambda x:len(x[0]));body,desc=items[-1]
    if any(not body.startswith(b) for b,_ in items):raise ValueError('PARTIAL_PREFIX_CONFLICT')
    etag,modified,total=versions.pop()
    return body,dict(prefix=desc,all_prefixes=[d for _,d in items],etag=etag,last_modified=modified,total=total,start=len(body),missing=total-len(body),url=URL)

def original_prefix():
    old=flow.read(store.OLD/'receipts/3.json')['trace'];new=flow.read(store.WORK/'result-private.json')['http_trace'][0]
    return choose_prefix([(store.OLD/'partial-not-qualified'/old['partial_sha256'],old),(store.WORK/'partial-not-qualified'/new['partial_sha256'],new)])

class RangeOpener:
    def __init__(self,opener,proof):self.opener=opener;self.proof=proof;self.calls=0
    def open(self,url,timeout):
        if url!=URL or self.calls:raise ValueError('SINGLE_EXACT_RANGE_REQUEST_ONLY')
        self.calls+=1
        req=Request(url,headers={'Range':'bytes='+str(self.proof['start'])+'-','If-Range':self.proof['etag'],'Accept-Encoding':'identity'})
        return self.opener.open(req,timeout=timeout)

def recover(prefix,proof,opener):
    version={}
    def headers(status,h):
        if status==206:
            match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',h.get('content-range',''))
            if not match or tuple(map(int,match.groups()))!=(proof['start'],proof['total']-1,proof['total']):raise Refused('CONTENT_RANGE_WINDOW_OR_TOTAL_CONFLICT')
            if h.get('etag')!=proof['etag'] or h.get('last-modified')!=proof['last_modified']:raise Refused('RANGE_VERSION_CONFLICT')
            if h.get('content-length') is not None and h['content-length']!=str(proof['missing']):raise Refused('RANGE_DECLARED_LENGTH_CONFLICT')
            version.update(mode='EXACT_206_SUFFIX',content_range=h['content-range'])
        elif status==200:
            if h.get('content-range'):raise Refused('WHOLE_RESPONSE_HAS_CONTENT_RANGE')
            version.update(mode='INDEPENDENT_WHOLE_200',old_prefix_used=False)
    bound=RangeOpener(opener,proof)
    raw,trace=receive(bound,URL,stamp=store.STAMP,allowed_statuses=(200,206),validate_headers=headers,max_seconds=180)
    if trace['http_status']==206:
        if len(raw)!=proof['missing'] or len(prefix)!=proof['start']:raise ValueError('RANGE_ACTUAL_LENGTH_CONFLICT')
        result=prefix+raw
        if len(result)!=proof['total']:raise ValueError('ASSEMBLED_LENGTH_CONFLICT')
    else:result=raw
    trace.update(version,range_sent='bytes='+str(proof['start'])+'-',if_range_sent=proof['etag'],body_bytes=len(raw),body_sha256=store.c.sha(raw),complete_body_bytes=len(result),complete_body_sha256=store.c.sha(result),old_prefix_used=trace['http_status']==206)
    return result,raw,trace

def run(work=WORK,opener=None):
    work=store.init(work);prefix,proof=original_prefix();done=work/'range-result-private.json'
    if done.exists():
        r=flow.read(done)
        if r['proof']!=proof:raise ValueError('SAVED_RANGE_PREFIX_CHANGED')
        for key in ['body','complete_body','partial']:
            if r.get(key):store.c.read_bytes(r[key]['path'],expected_bytes=r[key]['bytes'],expected_sha=r[key]['sha256'])
        return dict(r,this_execution_GETs=0,reused=True)
    marker=work/'single-range-attempt.json'
    if marker.exists():raise ValueError('RANGE_OUTCOME_UNKNOWN_NO_RETRY')
    store.guard(work,1024**2);store.put(work,marker,store.c.encoded(dict(proof=proof,started_at=store.STAMP(),maximum_GETs=1)))
    result=dict(schema='official-source-range/1.0',proof=proof,this_execution_GETs=1,reused=False,body=None,complete_body=None,partial=None)
    try:
        complete,body,trace=recover(prefix,proof,opener or build_opener(NoRedirect()))
        for key,b in [('body',body),('complete_body',complete)]:
            h=store.c.sha(b);p=work/key/h;store.save_exact(work,p,b);result[key]=dict(path=str(p),bytes=len(b),sha256=h)
        result.update(status='COMPLETE_HTTP_BODY',trace=trace)
        try:
            day,rows=daily.quote_map(json.loads(complete),'TPEX');result.update(source_date=day,rows=len(rows))
            if day!='2026-11-04':result.update(status='BLOCKED_SOURCE_DATE',reason='Complete source day is '+day)
        except (ValueError,KeyError,TypeError) as error:result.update(status='BLOCKED_SOURCE_PARSER',reason=type(error).__name__+': '+str(error))
    except TransferFailure as error:
        error.trace.update(range_sent='bytes='+str(proof['start'])+'-',if_range_sent=proof['etag'])
        result.update(status='BLOCKED_RANGE',trace=error.trace,reason=str(error))
        if error.partial:
            h=store.c.sha(error.partial);p=work/'partial-not-qualified'/h;store.save_exact(work,p,error.partial);result['partial']=dict(path=str(p),bytes=len(error.partial),sha256=h)
    store.put(work,done,store.c.encoded(result));return result
if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    r=run();print(json.dumps({k:r.get(k) for k in ['status','source_date','rows','reason','this_execution_GETs','reused']},ensure_ascii=False))
