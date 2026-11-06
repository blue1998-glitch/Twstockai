import argparse,json,os,time,shutil,hashlib,resource,fcntl
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from rotation_research.store import Journal
from rotation_research import artifact_codec as c
from graph_core.core import fingerprint
from graph_core.graph_lazy1_20261104.provider import Provider as OriginalProvider
BASE=Path("/workspace/twstockai-local-data")
WORK=BASE/"scan1_20261104"
PROJECT=Path(__file__).resolve().parents[2]
RESERVE=536870912
BUDGET=33554432
VERSION="single-source-market-scan/0.1"
sha=c.sha
encode=c.encoded
read=lambda p:json.loads(Path(p).read_bytes())
stamp=lambda:datetime.now(timezone.utc).isoformat()

def budget(work,n=0):
    free=shutil.disk_usage(work).free;initial=read(Path(work)/"baseline-private.json")["free_bytes"]
    if free-n<RESERVE+65536 or initial-free+n>BUDGET:raise OSError("SCAN_CAPACITY_STOP")
    return free

def write(work,p,b):
    p=c.regular(p,work);budget(work,0 if p.exists() else ((len(b)+4095)//4096)*4096);c.immutable(p,b)

def append(work,event):
    p=c.regular(Path(work)/"attempts.jsonl",work);body=encode(event)
    if len(body)>2048 or (p.exists() and p.stat().st_size>4194304):raise ValueError("BOUNDED_AUDIT_LOG")
    budget(work,len(body)+4096)
    with p.open("ab") as f:f.write(body);f.flush();os.fsync(f.fileno())

def events(work):
    p=Path(work)/"attempts.jsonl"
    if not p.exists():return {}
    b=c.regular(p,work).read_bytes()
    if len(b)>4194304 or (b and not b.endswith(b"\n")):raise ValueError("PARTIAL_AUDIT_LOG_UNKNOWN_NO_REPAIR")
    last={}
    for line in b.splitlines():
        e=json.loads(line);last[e["identity"]]=e
    return last

def fact(spec,s):
    p=c.regular(Path(s["fact_path"]));b=p.read_bytes()
    if len(b)>65536 or len(b)!=s["fact"]["bytes"] or sha(b)!=s["fact"]["sha256"]:raise ValueError("FACT_BYTES_CHANGED")
    f=json.loads(b)
    for k in ("identity","code","market","isin","cfi","as_of"):
        if f[k]!=s[k]:raise ValueError("FACT_IDENTITY_DATE_ROLE_CHANGED")
    src=f["source"]
    if src["capture_id"]!=spec["capture_id"] or src["daily_sha256"]!=spec["daily_sources"][f["market"]] or src["price_mode"]!="RAW_CANDIDATE" or src["volume_unit"]!="SHARES_REPORTED":raise ValueError("FACT_SOURCE_BASIS_CHANGED")
    if src["price_basis_id"]!=f["identity"]+"-OFFICIAL-RAW-UNBRIDGED-"+f["as_of"] or f["continuity"]!="NOT_CERTIFIED_NO_HISTORY_APPENDED":raise ValueError("NO_IMPLICIT_HISTORY_BRIDGE")
    return f

def key_for(spec,s):return "scan-"+sha(encode([spec["id"],s["identity"],s["fact"]["sha256"]]))

def validate(v,s,spec):
    if (v["identity"],v["as_of"],v["fact_sha256"],v["scan_id"])!=(s["identity"],s["as_of"],s["fact"]["sha256"],spec["id"]):raise ValueError("CHECKPOINT_BINDING_CONFLICT")
    f=fact(spec,s);r=v.get("result")
    if r is not None:
        q=dict(r);rid=q.pop("result_id")
        if fingerprint(q)!=rid or r["source_records"]!=1 or r["as_of"]!=f["as_of"] or r["context"]["code"]!=f["code"] or r["context"]["exchange"]!=f["market"] or r["context"]["source_id"]!="sha256:"+f["source"]["daily_sha256"] or r["context"]["price_basis_id"]!=f["source"]["price_basis_id"]:raise ValueError("CORE_RESULT_BINDING_CONFLICT")
        if r["anchor"]["close"]!=f["bar"]["close"] or r["anchor_volume"]["current_shares"]!=f["bar"]["volume_shares_scaled"] or r["boxes"] or r["reference_candidates"]:raise ValueError("SINGLE_BAR_RESULT_CONFLICT")
        if v["status"]!="EXECUTED_INSUFFICIENT_HISTORY" or v["core_calls"]!=1:raise ValueError("CORE_TERMINAL_CONFLICT")
    elif v["status"]=="SOURCE_REFUSED":
        if f["source_status"]=="SOURCE_BAR_AVAILABLE" or v["core_calls"]!=0:raise ValueError("SOURCE_REFUSAL_CONFLICT")
    elif not v["status"].startswith("ENGINEERING_FAILURE"):raise ValueError("UNKNOWN_TERMINAL")
    return v

def run(work=WORK,*,limit=None,runner=None,max_seconds=600):
    work=Path(work);spec=read(work/"manifest-private.json");protected=spec["protected_code"]
    check=dict(spec);sid=check.pop("id")
    if sha(encode(check))!=sid or not 0<len(spec["stocks"])<=5000 or len({s["identity"] for s in spec["stocks"]})!=len(spec["stocks"]):raise ValueError("MANIFEST_DIGEST_OR_UNIVERSE_CONFLICT")
    for path,h in protected.items():
        if sha(Path(path).read_bytes())!=h:raise ValueError("SCAN_CODE_VERSION_CHANGED_NO_RECALC")
    for row in spec.get("original_sources",{}).values():
        p=c.regular(Path(row["path"]));st=p.stat()
        if [st.st_size,st.st_mtime_ns,st.st_ino,st.st_dev]!=row["metadata"]:raise ValueError("ORIGINAL_SOURCE_CHANGED")
    if spec["as_of"]!=spec["stocks"][0]["as_of"] or spec["version"]!=VERSION:raise ValueError("EXACT_DATE_VERSION_REQUIRED")
    lock=work/"scan.lock"
    if not lock.exists():write(work,lock,b"")
    with lock.open("rb") as lf:
        fcntl.flock(lf,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return _run(work,spec,limit,runner or (lambda f:OriginalProvider._worker(None,f)),max_seconds)

def _run(work,spec,limit,runner,max_seconds):
    started=time.monotonic();journal=Journal(work/"results");last=events(work);rows=[];new_records=0;calls=0;unknown=0;maxrss=0
    done=work/"complete-index.json";expected_index=read(done) if done.exists() else None
    expected={r["identity"]:r for r in expected_index["records"]} if expected_index else {}
    for s in spec["stocks"]:
        key=key_for(spec,s);p=journal.path(key);prior=last.get(s["identity"])
        if p.exists():
            raw=c.regular(p,work).read_bytes();v=validate(journal.read(key)["value"],s,spec)
            known=expected.get(s["identity"],prior or {})
            if known.get("record_sha256") and sha(raw)!=known["record_sha256"]:raise ValueError("SAVED_CHECKPOINT_TAMPERED")
            if not expected_index and (not prior or prior["phase"]!="DONE"):
                append(work,dict(identity=s["identity"],phase="DONE",record_sha256=sha(raw),recovered_committed_record=True))
        else:
            if expected_index:raise ValueError("COMPLETE_RECORD_MISSING_NO_REPAIR")
            if (limit is not None and new_records>=limit) or time.monotonic()-started>=max_seconds:break
            v=dict(identity=s["identity"],as_of=s["as_of"],scan_id=spec["id"],fact_sha256=s["fact"]["sha256"],core_calls=0,result=None,status="ENGINEERING_FAILURE",reason=None)
            called=False
            try:
                budget(work,12288);f=fact(spec,s)
                if prior and prior["phase"]=="START":
                    v.update(status="ENGINEERING_FAILURE_UNKNOWN_OUTCOME",core_calls=None,reason="Previous attempt outcome unknown; no automatic repeat")
                elif f["source_status"]!="SOURCE_BAR_AVAILABLE" or f["bar"] is None:v.update(status="SOURCE_REFUSED",reason=f["source_status"])
                else:
                    append(work,dict(identity=s["identity"],phase="START",at=stamp(),fact_sha256=s["fact"]["sha256"]))
                    t=time.monotonic();called=True;a=runner(f);calls+=a["core_calls"]
                    v.update(status="EXECUTED_INSUFFICIENT_HISTORY",core_calls=a["core_calls"],result=a["series"]["results"][0],profile=dict(wall_seconds=time.monotonic()-t,worker_seconds=a["metrics"]["worker_seconds"],peak_RSS_KiB=a["metrics"]["peak_RSS_KiB"]))
                    validate(v,s,spec)
            except OSError as error:
                if str(error)=="SCAN_CAPACITY_STOP":raise
                v.update(status="ENGINEERING_FAILURE",core_calls=None if called else 0,result=None,reason=type(error).__name__+": "+str(error)[:180])
            except Exception as error:v.update(status="ENGINEERING_FAILURE",core_calls=None if called else 0,result=None,reason=type(error).__name__+": "+str(error)[:180])
            body=(json.dumps(dict(schema="rotation-record/0.1",id=key,value=v),ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
            if len(body)>8192:raise ValueError("SINGLE_RECORD_BOUND_STOP")
            budget(work,8192);journal.save(key,v);raw=p.read_bytes();assert raw==body
            append(work,dict(identity=s["identity"],phase="DONE",record_sha256=sha(raw)));new_records+=1
        maxrss=max(maxrss,v.get("profile",{}).get("peak_RSS_KiB",0));unknown+=v["core_calls"] is None
        rows.append(dict(identity=s["identity"],market=s["market"],key=key,bytes=len(raw),record_sha256=sha(raw),status=v["status"],core_calls=v["core_calls"],result_id=v["result"]["result_id"] if v["result"] else None))
        if new_records and new_records%250==0:print(json.dumps(dict(progress=len(rows),new_core_calls=calls)),flush=True)
    counts=Counter(r["status"] for r in rows);completed=len(rows)==len(spec["stocks"])
    if completed and not expected_index:
        index=dict(schema="private-market-scan-index/0.1",scan_id=spec["id"],as_of=spec["as_of"],expected=len(spec["stocks"]),records=rows,counts=dict(counts),markets={m:dict(Counter(r["status"] for r in rows if r["market"]==m)) for m in ["TWSE","TPEX"]})
        write(work,done,encode(index))
    return dict(status="COMPLETE" if completed else "PARTIAL",processed=len(rows),expected=len(spec["stocks"]),counts=dict(counts),new_core_calls=calls,new_records=new_records,unknown_core_outcomes=unknown,reused=bool(expected_index),wall_seconds=time.monotonic()-started,parent_ru_maxrss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,max_worker_RSS_KiB=maxrss)

if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--as-of",required=True);a.add_argument("--work",default=str(WORK));a.add_argument("--limit",type=int);v=a.parse_args()
    if read(Path(v.work)/"manifest-private.json")["as_of"]!=v.as_of:raise ValueError("NO_DATE_FALLBACK_OR_FETCH")
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    print(json.dumps(run(v.work,limit=v.limit),ensure_ascii=False))
