"""Read existing qualified six sources; never fetch or join history."""
from pathlib import Path
import json,shutil
from graph_core import market_increment as inc
from graph_core.storage1_20261104.facts import project
from .engine import WORK,BASE,PROJECT,write,read,sha,encode,VERSION

def prepare(as_of,*,work=WORK,state_path=None,capture_root=None,capture_id=None):
    work=Path(work);work.mkdir(mode=0o700,parents=True,exist_ok=True)
    if not (work/"baseline-private.json").exists():
        from rotation_research.artifact_codec import immutable
        immutable(work/"baseline-private.json",encode(dict(free_bytes=shutil.disk_usage(work).free,preferred_budget_bytes=33554432,reserve_bytes=536870912)))
    state_path=Path(state_path or BASE/"graph_lazy1_20261104/source-state-private.json");state=read(state_path)
    if state["summary"]["as_of"]!=as_of:raise ValueError("EXACT_SAVED_DATE_REQUIRED")
    capture_root=Path(capture_root or BASE/"day2_compact_20261104/capture")
    capture_id=capture_id or read(BASE/"day2_compact_20261104/repaired-source-private.json")["capture_id"]
    day,maps,markets,sigs=inc.sources(capture_root,capture_id)
    if day!=as_of or state["quote_capture_id"]!=capture_id:raise ValueError("SOURCE_DATE_CAPTURE_CONFLICT")
    members={m["market"]+":"+m["code"]:m for g in markets.values() for m in g["members"]}
    if set(members)!={s["identity"] for s in state["stocks"]}:raise ValueError("EXPLICIT_UNIVERSE_CROSSWALK_REQUIRED")
    oldbuild=read(BASE/"graph_lazy1_20261104/build-private.json");folder=Path(oldbuild["new_entry"]["path"]).parent
    stocks=[]
    for s in state["stocks"]:
        desc=s["preview_evidence"];p=folder/desc["path"];b=p.read_bytes()
        if len(b)!=desc["bytes"] or sha(b)!=desc["sha256"]:raise ValueError("STORED_FACT_TAMPERED")
        f=json.loads(b);member=members[s["identity"]];lower="twse" if s["market"]=="TWSE" else "tpex"
        expected=project(member,maps[s["market"]].get(s["code"]),as_of=day,capture_id=capture_id,daily_sha256=sigs[lower+"-daily.json"],parent_isin=s["isin"]);expected["batch_id"]=state["batch_id"]
        if expected!=f:raise ValueError("SOURCE_RAW_FACT_PRECISION_CONFLICT")
        stocks.append(dict(**{k:s[k] for k in ["identity","code","market","isin","cfi","as_of"]},fact=desc,fact_path=str(p)))
    files=[Path(__file__),Path(__file__).with_name("engine.py"),PROJECT/"graph_core/core.py",PROJECT/"graph_core/graph_lazy1_20261104/worker.py",PROJECT/"graph_core/graph_lazy1_20261104/provider.py",PROJECT/"graph_core/lite1_20261103/decision.py",PROJECT/"product_candidate/macd.py",PROJECT/"src/moving_averages.py"]
    src={}
    for name,h in sigs.items():
        p=capture_root/"raw"/h;s=p.stat();src[name]=dict(path=str(p),sha256=h,metadata=[s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev])
    spec=dict(version=VERSION,as_of=day,capture_id=capture_id,source_state_sha256=sha(state_path.read_bytes()),protected_code={str(p):sha(p.read_bytes()) for p in files},original_sources=src,daily_sources=state["daily_sources"],stocks=stocks)
    spec["id"]=sha(encode(spec));write(work,work/"manifest-private.json",encode(spec));return dict(as_of=day,stocks=len(stocks),scan_id=spec["id"],source_GETs=0)
if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser();a.add_argument("--as-of",required=True);v=a.parse_args();print(json.dumps(prepare(v.as_of)))
