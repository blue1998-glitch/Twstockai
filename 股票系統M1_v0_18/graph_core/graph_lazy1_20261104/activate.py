"""Controlled reload of the SAME loopback owner service; no Cloud restart.
Save all old control bytes/argv, retain old immutable pages/data, roll back on
failed startup. No second simultaneous listener or scheduled/background worker.
"""
from pathlib import Path
import subprocess,os,time,signal,json
from .common import BASE,ROOT,WORK,PROJECT,read_json,write,encode,sha,budget,heads
from .provider import Provider
from graph_core_chart.mobile_private import batch_index
from graph_core.storage1_20261104.activate import request

def atomic_view(body,tag):
    p=BASE/'lite1_20261103/view-head-private.json'
    if any(a.is_symlink() for a in (p,*p.parents)):raise ValueError('VIEW_SYMLINK')
    temp=WORK/('pointer-'+tag+'.json');write(temp,body);os.replace(temp,p)
    fd=os.open(p.parent,os.O_DIRECTORY|os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def alive(pid):
    p=Path('/proc')/str(pid)/'stat'
    return p.exists() and p.read_text().split(') ',1)[1].split()[0]!='Z'
def ready(conn,proc):
    end=time.monotonic()+70
    while time.monotonic()<end:
        if proc.poll() is not None:raise RuntimeError('OWNER_STARTUP_FAILED')
        try:request(conn,'/',401,authorized=False);return
        except (OSError,ValueError):time.sleep(.5)
    raise TimeoutError('OWNER_READY_BOUND')
def launch(argv,tag):
    env=dict(os.environ,PYTHONPATH=str(PROJECT)+os.pathsep+str(PROJECT/'src'),PYTHONDONTWRITEBYTECODE='1')
    out=(WORK/(tag+'.stdout.log')).open('ab');err=(WORK/(tag+'.stderr.log')).open('ab')
    try:p=subprocess.Popen(argv,cwd=PROJECT.parent,env=env,stdout=out,stderr=err,start_new_session=True)
    finally:out.close();err.close()
    return p

def run():
    if (WORK/'service-current-private.json').exists():raise FileExistsError('LAZY_OWNER_ALREADY_HANDLED_DO_NOT_RESTART_AGAIN')
    if read_json(WORK/'tests-private.json')['status']!='PASS':raise ValueError('TESTS_REQUIRED')
    budget(1024**2);built=read_json(WORK/'build-private.json');conn=read_json(BASE/'lite1_20261103/connection-private.json')
    pointer=BASE/'lite1_20261103/view-head-private.json';before=pointer.read_bytes()
    if sha(before)!=built['original_view_head_sha256'] or before!=(WORK/'original-view-head-private.json').read_bytes():raise ValueError('VIEW_ADVANCED')
    Provider(built['action_manifest'],built['action_sha256']) # source/role/byte validation, zero core
    _,_,summary,_=batch_index(built['catalogue'],linked_roots=[ROOT]);assert [s['as_of'] for s in summary['batches']]==['2026-11-03','2026-11-02','2026-10-30']
    pid=conn['service_pid'];procdir=Path('/proc')/str(pid);cmd=(procdir/'cmdline').read_bytes();argv=[a.decode() for a in cmd.split(bytes([0])) if a]
    if 'graph_core_chart.mobile_private' not in argv or '--lazy-manifest' in argv:raise ValueError('NOT_ORIGINAL_OWNER_STOP')
    if '--port' not in argv or argv[argv.index('--port')+1]!='8765':raise ValueError('OWNER_PORT_DIFFERENT')
    request(conn,'/',401,authorized=False);oldheads=heads();write(WORK/'original-service-private.json',encode(dict(pid=pid,argv=argv,view_sha256=sha(before))))
    if (procdir/'cmdline').read_bytes()!=cmd:raise ValueError('OWNER_PID_CHANGED')
    started=time.monotonic();os.kill(pid,signal.SIGTERM)
    for _ in range(50):
        if not alive(pid):break
        time.sleep(.1)
    if alive(pid):raise RuntimeError('ORIGINAL_OWNER_NOT_STOPPED_NO_SECOND_LISTENER')
    after=encode(dict(batch_index=built['catalogue']));atomic_view(after,'active')
    new=None
    try:
        new=launch(argv+['--lazy-manifest',built['action_manifest'],'--lazy-sha',built['action_sha256']],'owner-lazy')
        ready(conn,new);h,_=request(conn,'/',303);entry=built['new_entry'];expected='/batch-'+entry['sha256']+'/'+Path(entry['path']).name
        if h.get('Location')!=expected:raise ValueError('NEW_VIEW_DEFAULT_MISMATCH')
        _,b=request(conn,'/'+built['lazy_status_route'],200);status=json.loads(b)
        if status['core_calls']!=0:raise ValueError('UNREQUESTED_CORE_CALCULATION')
    except Exception as error:
        if new and new.poll() is None:new.terminate();new.wait(timeout=8)
        if pointer.read_bytes()==after:atomic_view(before,'rollback')
        old=launch(argv,'owner-rollback');ready(conn,old)
        write(WORK/'activation-failure-private.json',encode(dict(error_type=type(error).__name__,restored_original_view=True,restored_owner_pid=old.pid)))
        raise
    if heads()!=oldheads:raise ValueError('SOURCE_HEAD_CHANGED')
    oldcases=[]
    for e in built['old_entries']:
        state=read_json(Path(e['path']).parent/'prepared-state-private.json');stocks=[s for s in state['stocks'] if s.get('preview_series')][:2]
        oldcases.append(dict(as_of=e['as_of'],url=conn['origin']+'/batch-'+e['sha256']+'/'+Path(e['path']).name,stocks=stocks))
    state=read_json(WORK/'source-state-private.json');byid={s['identity']:s for s in state['stocks']};cases=read_json(BASE/'storage1_20261104/real-cases-private.json')
    for c in cases:c['lazy_graph']=byid[c['identity']]['lazy_graph']
    oldstate=read_json(Path(built['old_entries'][0]['path']).parent/'prepared-state-private.json');short_ids={s['identity'] for s in oldstate['stocks'] if s['status']=='INSUFFICIENT_HISTORY'}
    short=next(s for s in state['stocks'] if s['identity'] in short_ids and s['quote_card'] and s['identity'] not in {c['identity'] for c in cases})
    refused=next(s for s in state['stocks'] if s['status']!='SOURCE_BAR_AVAILABLE')
    cfg=dict(auth=conn['auth'],origin=conn['origin'],url=conn['origin']+expected,cases=cases,short_case=short,refused=refused,old_cases=oldcases,status_url=conn['origin']+'/'+built['lazy_status_route'])
    write(WORK/'browser-config-private.json',encode(cfg));report=dict(status='ACTIVE_ORIGINAL_OWNER_LAZY',pid=new.pid,old_pid=pid,port=8765,source_heads=oldheads,old_view_head_sha256=sha(before),new_view_head_sha256=sha(after),source_heads_changed=False,cloud_restart=False,owner_process_reloaded_once=True,new_website=False,initial_runtime_core_calls=0,old_credentials_changed=False,elapsed_seconds=time.monotonic()-started)
    write(WORK/'service-current-private.json',encode(report));print(json.dumps(report),flush=True);return report
if __name__=='__main__':run()
