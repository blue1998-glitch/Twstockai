"""Switch only the existing mutable VIEW pointer; never change source heads.
All old pointer bytes, immutable catalogues/pages/shards remain recoverable.
No server launch/restart, public endpoint, migration or root mutation.
"""
import base64,http.client,json,os,time
from pathlib import Path
from urllib.parse import urlsplit
from graph_core_chart.mobile_private import batch_index
from .common import BASE,ROOT,WORK,read_json,write,encode,sha,budget,protected_heads

def request(conn,path,expected,*,authorized=True,headers=None,method='GET'):
    u=urlsplit(conn['origin'])
    if u.hostname not in ('127.0.0.1','localhost') or u.port!=8765:raise ValueError('ORIGINAL_LOOPBACK_SERVICE_ONLY')
    h=dict(headers or {})
    if authorized:h['Authorization']='Basic '+base64.b64encode((conn['auth']['username']+':'+conn['auth']['password']).encode()).decode()
    client=http.client.HTTPConnection(u.hostname,u.port,timeout=90);client.request(method,path,headers=h);r=client.getresponse();body=r.read();status=r.status;hdr=dict(r.getheaders());client.close()
    if status!=expected:raise ValueError('OWNER_STATUS_'+str(status)+'_EXPECTED_'+str(expected))
    return hdr,body

def switch_pointer(body,tag):
    p=BASE/'lite1_20261103/view-head-private.json'
    if any(a.is_symlink() for a in (p,*p.parents)):raise ValueError('VIEW_POINTER_SYMLINK')
    tmp=WORK/('view-pointer-'+tag+'.json');write(tmp,body);os.replace(tmp,p)
    fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def run():
    report_path=WORK/'activation-private.json'
    if report_path.exists():
        saved=read_json(report_path);current=read_json(WORK/'nav-refinement-private.json') if (WORK/'nav-refinement-private.json').exists() else saved
        live=BASE/'lite1_20261103/view-head-private.json'
        if sha(live.read_bytes())!=current['new_view_head_sha256'] or protected_heads()!=saved['original_source_heads']:raise ValueError('VIEW_OR_SOURCE_ADVANCED_DO_NOT_REUSE_STALE_STATUS')
        return dict(saved,new_view_head_sha256=current['new_view_head_sha256'],new_catalogue=current['new_catalogue'],reused=True)
    if read_json(WORK/'python-tests-private.json')['status']!='PASS':raise ValueError('TARGETED_TESTS_REQUIRED')
    view=read_json(WORK/'view-build-private.json');p=BASE/'lite1_20261103/view-head-private.json';before=p.read_bytes()
    if sha(before)!=view['old_view_head_sha256'] or before!=(WORK/'original-view-head-private.json').read_bytes():raise ValueError('VIEW_ADVANCED_DO_NOT_OVERWRITE')
    start=time.monotonic();budget(2*1024**2)
    _,allowed,summary,_=batch_index(view['new_catalogue'],linked_roots=[ROOT])
    if [x['as_of'] for x in summary['batches']]!=['2026-11-03','2026-11-02','2026-10-30']:raise ValueError('EXPECTED_SAVED_DATES')
    new_entry=view['new_entry'];prefix='/batch-'+new_entry['sha256']+'/'
    state=read_json(Path(new_entry['path']).parent/'prepared-state-private.json')
    if len(state['stocks'])!=1986 or any(s.get('preview_series') for s in state['stocks']):raise ValueError('QUOTE_MODE_NOT_GRAPH_RUN')
    for s in state['stocks']:
        desc=s['preview_evidence'];item=allowed[(prefix+desc['path']).lstrip('/')]
        if item['sha256']!=desc['sha256'] or item['bytes']!=desc['bytes']:raise ValueError('INCOMPLETE_OWNER_QUOTE_WHITELIST')
    conn=read_json(BASE/'lite1_20261103/connection-private.json');checks=[]
    for path,code,auth in [('/',401,False),('/batches',200,True)]:request(conn,path,code,authorized=auth);checks.append(dict(check='old owner auth',status=code))
    heads=protected_heads();after=encode(dict(batch_index=view['new_catalogue']))
    try:
        switch_pointer(after,'activate')
        hdr,_=request(conn,'/',303)
        if hdr.get('Location')!=prefix+Path(new_entry['path']).name:raise ValueError('LATEST_QUOTE_DEFAULT_NOT_ACTIVE')
        _,body=request(conn,'/batches',200)
        if not all(d.encode() in body for d in ['2026-11-03','2026-11-02','2026-10-30']):raise ValueError('OLD_DATES_MISSING')
    except Exception as exc:
        if p.read_bytes()==after:switch_pointer(before,'rollback')
        write(WORK/'activation-failure-private.json',encode(dict(error_type=type(exc).__name__,error=str(exc),original_source_heads_preserved=protected_heads()==heads,view_rollback=True)))
        raise
    if protected_heads()!=heads:raise ValueError('ORIGINAL_SOURCE_HEAD_CHANGED')
    cases=read_json(WORK/'real-cases-private.json');old_cases=[]
    for entry in view['old_entries']:
        old=read_json(Path(entry['path']).parent/'prepared-state-private.json');case=next(s for s in old['stocks'] if s.get('preview_series'))
        old_cases.append(dict(as_of=entry['as_of'],url=conn['origin']+'/batch-'+entry['sha256']+'/'+Path(entry['path']).name,code=case['code'],identity=case['identity']))
    cfg=dict(auth=conn['auth'],origin=conn['origin'],url=conn['origin']+prefix+Path(new_entry['path']).name,cases=cases,old_cases=old_cases,rejected=[s for s in state['stocks'] if s['status']!='SOURCE_BAR_AVAILABLE'][:1],state_path=str(Path(new_entry['path']).parent/'prepared-state-private.json'))
    write(WORK/'browser-config-private.json',encode(cfg))
    report=dict(status='ACTIVE_EXISTING_OWNER_QUOTES',new_catalogue=view['new_catalogue'],new_view_head_sha256=sha(after),old_view_head_sha256=sha(before),old_pointer_bytes_saved=True,mutable_view_pointer_changed=True,source_heads_changed=False,old_payload_files_overwritten=0,server_restart=False,new_listener=False,original_source_heads=heads,as_of=state['summary']['as_of'],stocks=1986,quote_routes=1986,original_chart_routes={e['as_of']:e['charts'] for e in summary['batches'][1:]},new_graphs=0,owner_catalogue_routes=len(allowed),elapsed_seconds=time.monotonic()-start)
    write(report_path,encode(report));print(json.dumps(report),flush=True);return report
if __name__=='__main__':run()
