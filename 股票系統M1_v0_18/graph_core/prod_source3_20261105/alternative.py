"""The one Issue6-permitted official alternate inspection; no fallback loop.
Explicit issue authorization + existing TPEX private-API parent scope permit
inspection only. Unknown units/license/identity/date never authorize adoption.
"""
import json,resource
from urllib.request import build_opener
from graph_core.prod_day2_20261105.transport import receive,TransferFailure
from graph_core.day1_20261103.probe_once import NoRedirect
from . import resume as m
URL='https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes'

def assess(raw,target):
    value=json.loads(raw)
    if not isinstance(value,list) or not value or not all(isinstance(r,dict) for r in value):return dict(status='REFUSED_SCHEMA',reason='No nonempty official row list')
    keys=set.intersection(*(set(row) for row in value));required={'Date','SecuritiesCompanyCode','Open','High','Low','Close','TradingShares'}
    missing=sorted(required-keys);dates=None
    if 'Date' in keys:
        try:dates=sorted({m.daily.day(row['Date']) for row in value})
        except (ValueError,TypeError):pass
    reasons=[]
    if dates!=[target]:reasons.append('SOURCE_DATE_MISMATCH_OR_NOT_EXPLICIT')
    if missing:reasons.append('MISSING_ORIGINAL_OHLCV_FIELDS')
    # Field names alone do not prove the unit or ordinary-share/ISIN membership.
    reasons+=['NATIVE_SHARE_UNIT_NOT_PROVEN','SIX_SOURCE_ORDINARY_ISIN_CFI_CROSSWALK_NOT_CERTIFIED','ALTERNATE_DATASET_LICENSE_NOT_NEWLY_ATTESTED']
    return dict(status='NOT_ADOPTED',rows=len(value),common_fields=sorted(keys),source_dates=dates,missing_fields=missing,reasons=reasons,normalized_or_relabelled=False)

def run(work=m.WORK,opener=None):
    work=m.store.init(work);done=work/'alternative-result-private.json'
    if done.exists():
        r=m.flow.read(done)
        if r.get('body'):m.store.c.read_bytes(r['body']['path'],expected_bytes=r['body']['bytes'],expected_sha=r['body']['sha256'])
        return dict(r,this_execution_GETs=0,reused=True)
    prior=m.flow.read(work/'range-result-private.json');status=prior['trace'].get('http_status')
    if status in (301,302,303,307,308,401,403,429):raise ValueError('DENIAL_NO_ALTERNATE_BYPASS')
    if prior['status']=='COMPLETE_HTTP_BODY':raise ValueError('PRIMARY_COMPLETE_USE_PRIMARY_NO_ALTERNATE')
    marker=work/'single-alternative-attempt.json'
    if marker.exists():raise ValueError('ALTERNATIVE_UNKNOWN_OUTCOME_NO_RETRY')
    m.store.put(work,marker,m.store.c.encoded(dict(url=URL,started_at=m.store.STAMP(),maximum_GETs=1,authorization='Issue6 named official API inspection + inherited TPEX private noncommercial API scope',permission_limit='No redistribution or adoption without complete exact contract')))
    r=dict(url=URL,this_execution_GETs=1,reused=False,body=None)
    try:
        raw,t=receive(opener or build_opener(NoRedirect()),URL,stamp=m.store.STAMP,max_seconds=120,max_body=8*1024**2)
        h=m.store.c.sha(raw);p=work/'alternative-original'/h;m.store.save_exact(work,p,raw);r.update(trace=t,body=dict(path=str(p),bytes=len(raw),sha256=h))
        try:r['assessment']=assess(raw,'2026-11-04')
        except (ValueError,KeyError,TypeError) as error:r['assessment']=dict(status='REFUSED_PARSER',reason=type(error).__name__+': '+str(error))
    except TransferFailure as error:
        r.update(trace=error.trace,assessment=dict(status='REFUSED_TRANSPORT',reason=str(error)))
        if error.partial:
            h=m.store.c.sha(error.partial);p=work/'alternative-partial-not-qualified'/h;m.store.save_exact(work,p,error.partial);r['partial']=dict(path=str(p),bytes=len(error.partial),sha256=h)
    m.store.put(work,done,m.store.c.encoded(r));return r
if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));r=run();print(json.dumps(dict(assessment=r['assessment'],HTTP=r['trace'].get('http_status'),this_execution_GETs=r['this_execution_GETs'],reused=r['reused']),ensure_ascii=False))
