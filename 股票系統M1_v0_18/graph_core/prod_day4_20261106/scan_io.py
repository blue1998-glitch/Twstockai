"""I/O-only adapter of original scan1.run/_run for NEW minified Journals.
Original source remains unchanged. No core/indicator/qualification formula here.
Journal.read and schema unchanged; exact new wire bytes are hashed and checked.
"""
from graph_core.scan1_20261104.engine import *
from graph_core.prod_day4_20261106 import intake
from rotation_research.store import Journal as OriginalJournal
read=lambda p:json.loads(c.read_bytes(p))
class Journal(OriginalJournal):
    def save(self,key,value):
        body=encode(dict(schema="rotation-record/0.1",id=key,value=value));p=self.path(key)
        if len(body)>4096:raise ValueError("MINIFIED_RECORD_BOUND")
        c.immutable(p,body);return self.read(key)
def write(work,p,b):
    if Path(p).name=="complete-index.json":intake.store.save_exact(intake.WORK,Path(p),b)
    else:
        budget(work,0 if Path(p).exists() else ((len(b)+4095)//4096)*4096);c.immutable(p,b)
def run(work=WORK,*,limit=None,runner=None,max_seconds=600):
    work=Path(work);spec=read(work/"manifest-private.json");protected=spec["protected_code"]
    if spec.get("journal_encoding")!="MINIFIED_UTF8_V1":raise ValueError("EXPLICIT_NEW_JOURNAL_ENCODING_REQUIRED")
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
    done=work/"complete-index.json";expected_index=read(done) if c.exists(done) else None
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
            body=encode(dict(schema="rotation-record/0.1",id=key,value=v))
            if len(body)>4096:raise ValueError("SINGLE_RECORD_BOUND_STOP")
            budget(work,4096);journal.save(key,v);raw=p.read_bytes();assert raw==body
            append(work,dict(identity=s["identity"],phase="DONE",record_sha256=sha(raw)));new_records+=1
        maxrss=max(maxrss,v.get("profile",{}).get("peak_RSS_KiB",0));unknown+=v["core_calls"] is None
        rows.append(dict(identity=s["identity"],market=s["market"],key=key,bytes=len(raw),record_sha256=sha(raw),status=v["status"],core_calls=v["core_calls"],result_id=v["result"]["result_id"] if v["result"] else None))
        if new_records and new_records%250==0:print(json.dumps(dict(progress=len(rows),new_core_calls=calls)),flush=True)
    counts=Counter(r["status"] for r in rows);completed=len(rows)==len(spec["stocks"])
    if completed and not expected_index:
        index=dict(schema="private-market-scan-index/0.1",scan_id=spec["id"],as_of=spec["as_of"],expected=len(spec["stocks"]),records=rows,counts=dict(counts),markets={m:dict(Counter(r["status"] for r in rows if r["market"]==m)) for m in ["TWSE","TPEX"]})
        write(work,done,encode(index))
    return dict(status="COMPLETE" if completed else "PARTIAL",processed=len(rows),expected=len(spec["stocks"]),counts=dict(counts),new_core_calls=calls,new_records=new_records,unknown_core_outcomes=unknown,reused=bool(expected_index),wall_seconds=time.monotonic()-started,parent_ru_maxrss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,max_worker_RSS_KiB=maxrss)

