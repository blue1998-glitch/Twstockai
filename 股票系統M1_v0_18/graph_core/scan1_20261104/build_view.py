from pathlib import Path
import copy,json
from graph_core.lite1_20261103.render import compile_view
from graph_core.lite1_20261103.decision import project
from .engine import WORK,BASE,PROJECT,read,sha,encode,write,budget
LABELS={"EXECUTED_INSUFFICIENT_HISTORY":"已執行·歷史不足","SOURCE_REFUSED":"來源拒用","ENGINEERING_FAILURE":"工程失敗","ENGINEERING_FAILURE_UNKNOWN_OUTCOME":"工程結果未知"}
def build():
    budget(WORK,7*1024**2);index_path=WORK/"complete-index.json";index=read(index_path);numeric=read(WORK/"manifest-private.json")
    oldbuild=read(BASE/"graph_lazy1_20261104/build-private.json");oldspec=read(oldbuild["action_manifest"]);state=read(BASE/"graph_lazy1_20261104/source-state-private.json")
    if index["as_of"]!=state["summary"]["as_of"] or len(index["records"])!=len(state["stocks"]):raise ValueError("COMPLETE_SAME_DATE_REQUIRED")
    byid={r["identity"]:r for r in index["records"]};counts=index["counts"];executed=sum(r["core_calls"]==1 for r in index["records"])
    ss=dict(as_of=index["as_of"],scan_id=index["scan_id"],total=index["expected"],executed=executed,insufficient=counts.get("EXECUTED_INSUFFICIENT_HISTORY",0),refused=counts.get("SOURCE_REFUSED",0),failed=sum(n for k,n in counts.items() if k.startswith("ENGINEERING_FAILURE")),descriptive=0)
    state["scan_summary"]=ss;actions=[];oldactions={a["identity"]:a for a in oldspec["actions"]}
    for s in state["stocks"]:
        r=byid[s["identity"]];s["scan"]=dict(status=r["status"],label=LABELS[r["status"]],core_calls=r["core_calls"],record_sha256=r["record_sha256"])
        s["decision"]["headline"]=s["scan"]["label"]
        key=sha(encode([index["scan_id"],r["record_sha256"],s["preview_evidence"]["sha256"]]));s["lazy_graph"]=dict(path="lazy-"+key+".json",request_id=key)
        a=copy.deepcopy(oldactions[s["identity"]]);a.update(request_id=key);a["local_route"]=s["lazy_graph"]["path"];actions.append(a)
    raw,_=compile_view(state,state["summary"]["as_of"]);oldcatalog=read(read(BASE/"lite1_20261103/view-head-private.json")["batch_index"]);old=oldcatalog["batches"][0];folder=Path(old["path"]).parent
    name="market-scan1-"+sha(raw)[:16]+".html";target=folder/name
    from rotation_research.artifact_codec import immutable
    immutable(target,raw) # unique new shell beside existing static fact shards, no copies.
    new=dict(old,path=str(target),bytes=len(raw),sha256=sha(raw));catalogue=encode(dict(schema="private-saved-batches/0.1",batches=[new,*oldcatalog["batches"][1:]]));cp=WORK/("batches-"+sha(catalogue)+".json");write(WORK,cp,catalogue)
    prefix="batch-"+new["sha256"]+"/"
    for a in actions:a["route"]=prefix+a.pop("local_route");a["fact_route"]=prefix+a["fact"]["path"]
    oldspec.update(actions=actions,metrics_route=prefix+"lazy-status.json",scan_index=dict(path=str(index_path),bytes=index_path.stat().st_size,sha256=sha(index_path.read_bytes())),scan_manifest=dict(path=str(WORK/"manifest-private.json"),bytes=(WORK/"manifest-private.json").stat().st_size,sha256=sha((WORK/"manifest-private.json").read_bytes())))
    for f in [Path(__file__).with_name("provider.py"),Path(__file__).with_name("present.py"),Path(__file__).with_name("engine.py")]:oldspec["protected_code"][str(f)]=sha(f.read_bytes())
    body=encode(oldspec);ap=WORK/("actions-"+sha(body)+".json");write(WORK,ap,body);write(WORK,WORK/"view-state-private.json",encode(state))
    pointer=BASE/"lite1_20261103/view-head-private.json";write(WORK,WORK/"original-view-head-private.json",pointer.read_bytes())
    r=dict(catalogue=str(cp),new_entry=new,old_entries=oldcatalog["batches"][1:],action_manifest=str(ap),action_sha256=sha(body),scan_summary=ss,old_view_sha256=sha(pointer.read_bytes()),metrics_route=oldspec["metrics_route"]);write(WORK,WORK/"view-build-private.json",encode(r));return r
if __name__=="__main__":print(json.dumps(build()))
