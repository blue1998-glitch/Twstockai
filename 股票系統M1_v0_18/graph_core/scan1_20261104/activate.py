"""Controlled SAME owner reload; all data and old rollback argv preserved."""
from pathlib import Path
import os,subprocess,time,signal,json
from .engine import WORK,BASE,PROJECT,read,write,sha,encode,budget
from .provider import Provider
from graph_core_chart.mobile_private import batch_index
from graph_core.graph_lazy1_20261104.activate import alive,ready
from graph_core.storage1_20261104.activate import request
from graph_core.day1_20261103.probe_once import heads
ROOT=BASE/"fm3_20261101/runtime"
def pointer(body,tag):
    p=BASE/"lite1_20261103/view-head-private.json";tmp=WORK/("pointer-"+tag+".json");write(WORK,tmp,body);os.replace(tmp,p)
    fd=os.open(p.parent,os.O_DIRECTORY|os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def launch(argv,tag):
    env=dict(os.environ,PYTHONPATH=str(PROJECT)+os.pathsep+str(PROJECT/"src"),PYTHONDONTWRITEBYTECODE="1")
    with (WORK/(tag+".stdout.log")).open("ab") as out,(WORK/(tag+".stderr.log")).open("ab") as err:
        return subprocess.Popen(argv,cwd=PROJECT.parent,env=env,stdout=out,stderr=err,start_new_session=True)
def activate():
    if (WORK/"service-current-private.json").exists():raise ValueError("ALREADY_ACTIVATED_NO_SECOND_OWNER")
    budget(WORK,1048576);b=read(WORK/"view-build-private.json");conn=read(BASE/"graph_lazy1_20261104/browser-config-private.json");active=read(BASE/"graph_lazy1_20261104/service-current-private.json")
    old=(BASE/"lite1_20261103/view-head-private.json").read_bytes()
    if sha(old)!=b["old_view_sha256"]:raise ValueError("VIEW_ADVANCED")
    Provider(b["action_manifest"],b["action_sha256"])
    batch_index(b["catalogue"],linked_roots=[ROOT])
    pid=active["pid"];p=Path("/proc")/str(pid)/"cmdline";cmd=p.read_bytes();argv=[x.decode() for x in cmd.split(bytes([0])) if x]
    if "graph_core_chart.mobile_private" not in argv or "--lazy-manifest" not in argv or "--scan-manifest" in argv or argv[argv.index("--port")+1]!="8765":raise ValueError("ORIGINAL_OWNER_IDENTITY_CONFLICT")
    write(WORK,WORK/"original-service-private.json",encode(dict(pid=pid,argv=argv,view_sha256=sha(old))))
    newargs=[];i=0
    while i<len(argv):
        if argv[i] in ("--lazy-manifest","--lazy-sha"):i+=2;continue
        newargs.append(argv[i]);i+=1
    newargs += ["--scan-manifest",b["action_manifest"],"--scan-sha",b["action_sha256"]]
    before=heads(ROOT);started=time.monotonic();request(conn,"/",401,authorized=False)
    if p.read_bytes()!=cmd:raise ValueError("OWNER_PID_CHANGED")
    os.kill(pid,signal.SIGTERM)
    for _ in range(50):
        if not alive(pid):break
        time.sleep(.1)
    if alive(pid):raise ValueError("OWNER_NOT_STOPPED_NO_SECOND_LISTENER")
    newbody=encode(dict(batch_index=b["catalogue"]));pointer(newbody,"active");new=None
    try:
        new=launch(newargs,"owner-scan");ready(conn,new);h,_=request(conn,"/",303);e=b["new_entry"]
        if h["Location"]!="/batch-"+e["sha256"]+"/"+Path(e["path"]).name:raise ValueError("DEFAULT_PAGE_MISMATCH")
        _,raw=request(conn,"/"+b["metrics_route"],200);assert json.loads(raw)["core_calls"]==0
    except Exception as error:
        if new and new.poll() is None:new.terminate();new.wait(timeout=8)
        if (BASE/"lite1_20261103/view-head-private.json").read_bytes()==newbody:pointer(old,"rollback")
        restored=launch(argv,"owner-rollback");ready(conn,restored);write(WORK,WORK/"activation-failure-private.json",encode(dict(error=type(error).__name__+": "+str(error),rollback_pid=restored.pid)));raise
    assert heads(ROOT)==before
    report=dict(status="ACTIVE_SAVED_SCAN",pid=new.pid,old_pid=pid,port=8765,owner_reloaded_once=True,cloud_restart=False,source_heads_same=True,view_sha256=sha(newbody),initial_core_calls=0,reload_seconds=time.monotonic()-started)
    write(WORK,WORK/"service-current-private.json",encode(report))
    cfg=dict(conn);cfg.update(url=conn["origin"]+h["Location"],status_url=conn["origin"]+"/"+b["metrics_route"])
    byid={s["identity"]:s for s in read(WORK/"view-state-private.json")["stocks"]}
    for c in cfg["cases"]:c["lazy_graph"]=byid[c["identity"]]["lazy_graph"];c["scan"]=byid[c["identity"]]["scan"]
    cfg["short_case"]=byid[cfg["short_case"]["identity"]];cfg["refused"]=byid[cfg["refused"]["identity"]]
    write(WORK,WORK/"browser-config-private.json",encode(cfg));return report
if __name__=="__main__":print(json.dumps(activate()))
