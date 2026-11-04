"""Finite live owner verification. Private reports stay outside the Git tree.
Does not fetch provider data, invoke a batch or re-audit historical large files.
"""
import json,time,shutil,os,hashlib
from pathlib import Path
from urllib.parse import urlsplit
from graph_core.storage1_20261104.activate import request
from .common import BASE,ROOT,WORK,read_json,write,encode,sha,budget,heads

def inventory():
    return {str(p.relative_to(WORK)):[p.stat().st_size,p.stat().st_mtime_ns] for p in WORK.rglob('*') if p.is_file()}

def run():
    budget(1024**2);cfg=read_json(WORK/'browser-config-private.json');built=read_json(WORK/'build-private.json');active=read_json(WORK/'service-current-private.json')
    if read_json(WORK/'browser-final/verification-private.json')['status']!='PASS':raise ValueError('BROWSER_NOT_PASS')
    origin=cfg['origin'];prefix=urlsplit(cfg['url']).path.rsplit('/',1)[0]+'/'
    conn=dict(origin=origin,auth=cfg['auth']);route=prefix+cfg['cases'][0]['lazy_graph']['path'];metrics_path=urlsplit(cfg['status_url']).path
    _,raw=request(conn,metrics_path,200);before_metrics=json.loads(raw);before_files=inventory();checks=[]
    cases=[(route,401,False,'GET',{}),(route,403,True,'GET',{'Origin':'https://invalid.example'}),(route,405,True,'POST',{}),(route,204,True,'HEAD',{}),(route+'?path=secret',404,True,'GET',{}),(prefix+'lazy-unknown.json',404,True,'GET',{}),('/../private',404,True,'GET',{})]
    for path,status,authorized,method,headers in cases:
        request(conn,path,status,authorized=authorized,method=method,headers=headers);checks.append(dict(kind='actual owner '+method,status=status,result='PASS'))
    timings=[];bodies=[]
    for i in range(2):
        t=time.monotonic();h,body=request(conn,route,200);timings.append(time.monotonic()-t)
        if sha(body)!=h.get('X-Artifact-SHA256') or h.get('X-Lazy-Cache')!='HIT':raise ValueError('REPEAT_NOT_IDENTICAL_CACHE')
        bodies.append(body)
    _,raw=request(conn,metrics_path,200);after_metrics=json.loads(raw)
    if before_metrics['core_calls']!=after_metrics['core_calls'] or bodies[0]!=bodies[1]:raise ValueError('REPEAT_RECALCULATED_OR_CHANGED')
    if inventory()!=before_files:raise ValueError('GET_CREATED_FILES')
    checks.append(dict(kind='two same-source cache hits /zero new core /zero persisted files /SHA',status='PASS'))
    if heads()!=built['original_source_heads']:raise ValueError('SOURCE_HEAD_CHANGED')
    if sha((BASE/'lite1_20261103/view-head-private.json').read_bytes())!=active['new_view_head_sha256']:raise ValueError('VIEW_HEAD_CHANGED')
    if not (Path('/proc')/str(active['pid'])).exists():raise ValueError('ORIGINAL_OWNER_NOT_RUNNING')
    for e in built['old_entries']+[built['previous_latest_entry']]:
        p=Path(e['path']);raw=p.read_bytes()
        if len(raw)!=e['bytes'] or sha(raw)!=e['sha256']:raise ValueError('OLD_PAGE_CHANGED')
    spec=read_json(built['action_manifest'])
    for file,digest in spec['protected_code'].items():
        if sha(Path(file).read_bytes())!=digest:raise ValueError('CORE_OR_BOUND_CODE_CHANGED')
    for row in spec['original_daily_sources'].values():
        h=hashlib.sha256()
        with Path(row['path']).open('rb') as f:
            while b:=f.read(1024**2):h.update(b)
        if h.hexdigest()!=row['sha256']:raise ValueError('DAILY_SOURCE_CHANGED')
    checks.append(dict(kind='original daily sources /protected core /old pages /source heads',status='PASS'))
    initial=read_json(WORK/'baseline-private.json')['free_bytes'];free=shutil.disk_usage(WORK).free
    report=dict(status='PASS',checks=checks,http_security_cases=len(cases),repeat_gets=2,repeat_seconds=timings,repeat_persisted_file_changes=0,repeat_new_core_calls=0,live_metrics=after_metrics,resource=dict(baseline_free_bytes=initial,observed_free_bytes=free,filesystem_net_added_bytes=initial-free,required_reserve_bytes=536870912,preferred_budget_bytes=16*1024**2,within_budget=initial-free<16*1024**2),original_source_heads=heads(),old_pages_same_bytes=True,protected_numeric_code_same_bytes=True,original_daily_source_sha_pass=True,android='NOT_TESTED_NEW_BUILD',real_daily_full_graph='INSUFFICIENT_COMPARABLE_HISTORY',backup='UNKNOWN',restart_persistence='UNKNOWN')
    if free<536870912 or not report['resource']['within_budget']:raise ValueError('FINAL_CAPACITY')
    write(WORK/'verification-private.json',encode(report));print(json.dumps({k:v for k,v in report.items() if k not in ['original_source_heads','live_metrics']},ensure_ascii=False));return report
if __name__=='__main__':run()
