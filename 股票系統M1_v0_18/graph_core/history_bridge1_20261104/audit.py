"""Four bounded real-history cases + one already rejected source counterexample.
Do not call a source provider or numerical core, invent qualification, or publish
an unproven bridge. Original row precision and private data stay outside Git.
"""
from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
import json,hashlib,shutil,time,resource
from rotation_research.store import Journal
from rotation_research import artifact_codec as codec
from graph_core import market_daily as d,market_increment as inc
from graph_core.market_finmind import capture_key
from graph_core.finmind_run import _parse
from graph_core.finmind_adapter import history_payload
from graph_core.day1_20261103.probe_once import heads
BASE=Path("/workspace/twstockai-local-data")
ROOT=BASE/"fm3_20261101/runtime"
WORK=BASE/"history_bridge1_20261104"
PROJECT=Path(__file__).resolve().parents[2]
CODES=["TWSE:1101","TWSE:1102","TPEX:1295","TPEX:1336"]
FIELDS=["open","high","low","close","volume_shares_scaled"]
sha=codec.sha
encode=codec.encoded
read=lambda p:json.loads(Path(p).read_bytes())

def write(p,b):
    p=codec.regular(p,WORK);free=shutil.disk_usage(WORK).free;initial=read(WORK/"baseline-private.json")["free_bytes"]
    if free-len(b)<536870912+65536 or initial-free+len(b)>33554432:raise OSError("BRIDGE_CAPACITY_STOP")
    codec.immutable(p,b)

def bounded_bytes(p,limit=16777216):
    p=codec.regular(Path(p))
    if p.stat().st_size>limit:raise ValueError("CASE_SOURCE_SIZE_BOUND")
    return p.read_bytes()

def saved(journal,key):
    p=journal.path(key)
    if codec.sidecar(p).exists():
        desc=json.loads(codec.sidecar(p).read_bytes())
        if desc["bytes"]>16777216:raise ValueError("CASE_LOGICAL_JOURNAL_SIZE_BOUND")
    elif p.stat().st_size>16777216:raise ValueError("CASE_JOURNAL_SIZE_BOUND")
    return journal.read(key)["value"]

def field_matches(left,right):
    return {k:left.get(k) is not None and right.get(k) is not None and Decimal(left[k])==Decimal(right[k]) for k in FIELDS}

def diagnostic_status(identity_ok,matches,*,existing_refusal=False):
    # This is only a negative-evidence diagnostic, not a new positive-source gate.
    if existing_refusal:return "REFUSED_EXISTING_HISTORY_QUALITY"
    if not identity_ok or not all(matches.values()):return "SOURCE_CONFLICT"
    return "NEEDS_INTERVAL_BASIS_ACTION_EVIDENCE"

def load_map(root,receipt,market):
    p=root/"raw"/receipt["sha256"];b=bounded_bytes(p)
    if sha(b)!=receipt["sha256"] or len(b)!=receipt["bytes"]:raise ValueError("ORIGINAL_OFFICIAL_SOURCE_CHANGED")
    dt,rows=d.quote_map(json.loads(b),market);return dt,rows,dict(path=str(p),sha256=sha(b),bytes=len(b),source_url=receipt["url"],captured_at=receipt["fetched_at"])

def run():
    started=time.monotonic();done=WORK/"review-private.json"
    if done.exists():
        report=read(done)
        for item in report["dependencies"]:
            p=Path(item["path"]);s=p.stat()
            if [s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev]!=item["metadata"]:raise ValueError("REVIEW_DEPENDENCY_CHANGED")
        return dict(report,reused=True,new_source_GETs=0,new_core_calls=0,new_outputs=0)
    deps={}
    def dep(p):
        p=codec.regular(p);s=p.stat();deps[str(p)]=dict(path=str(p),metadata=[s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev]);return p
    before=heads(ROOT);pointer=BASE/"lite1_20261103/view-head-private.json";view_sha=sha(pointer.read_bytes())
    fm_id=read(ROOT/"fm3-continuation.json")["result"]["id"];day_id=read(ROOT/"current-increment-run.json")["id"]
    runs=Journal(ROOT/"runs");results=Journal(ROOT/"results");fm=saved(runs,fm_id);day=saved(runs,day_id);ref=saved(runs,fm["reference_current_run"])
    byfm={s["identity"]:s for s in fm["stocks"]};byday={s["identity"]:s for s in day["stocks"]};state=read(BASE/"graph_lazy1_20261104/source-state-private.json");bystate={s["identity"]:s for s in state["stocks"]}
    dep(ROOT/"fm3-continuation.json");dep(ROOT/"current-increment-run.json");dep(BASE/"graph_lazy1_20261104/source-state-private.json")
    capture=BASE/"day2_compact_20261104/capture";cid=read(BASE/"day2_compact_20261104/repaired-source-private.json")["capture_id"];receipts3=read(capture/"captures"/(cid+".json"));receipts2=read(ROOT/"captures"/(day["capture_id"]+".json"))
    maps={};source={}
    for date,root,receipts in [("2026-10-30",ROOT,ref["source_receipts"]),("2026-11-02",ROOT,receipts2),("2026-11-03",capture,receipts3)]:
        for market,lower in [("TWSE","twse"),("TPEX","tpex")]:
            rr=next(r for r in receipts if r["name"]==lower+"-daily.json");dt,rows,receipt=load_map(root,rr,market)
            if dt!=date:raise ValueError("DATE_ROLE_CONFLICT")
            maps[(date,market)]=rows;source[(date,market)]=receipt;dep(Path(receipt["path"]))
    catalog_path=PROJECT/"rotation_research/subsidiary_proposal_20261023/catalog-v010.json";catalog=read(catalog_path);dep(catalog_path)
    events_path=PROJECT/"rotation_research/action_resolution_20261023/events-v04.json";actions=read(events_path);dep(events_path)
    cases=[]
    for identity in CODES:
        stock=byfm[identity]
        if stock["status"]!="ANALYZED_FINMIND_HISTORY":raise ValueError("PLANNED_LONG_HISTORY_CASE_MISSING")
        v=inc.stock_history(ROOT,stock,fm);request=v["request"];acq=v["acquisition"];rawpath=dep(ROOT/"source-raw"/acq["sha256"]);raw=bounded_bytes(rawpath)
        if sha(raw)!=acq["sha256"] or len(raw)!=acq["bytes"] or acq["http_status"]!=200 or acq["api_status"]!=200:raise ValueError("ORIGINAL_FINMIND_ACQUISITION_CONFLICT")
        response=_parse(raw);reparsed=history_payload(response,request);raw_anchor=next(r for r in response["data"] if r["date"]==fm["as_of"])
        if reparsed["bars"]!=v["input"]["bars"] or reparsed["context"]!=v["input"]["context"]:raise ValueError("ORIGINAL_FINMIND_INPUT_REPRODUCTION_CONFLICT")
        for key in [stock["result_key"],stock["history_key"]]:
            p=results.path(key) if key.startswith("fm3-result-") else Journal(ROOT/"histories").path(key)
            dep(codec.sidecar(p) if codec.sidecar(p).exists() else p)
        bars=v["input"]["bars"];official=[]
        for date in ["2026-10-30","2026-11-02","2026-11-03"]:
            row=maps[(date,stock["market"])].get(stock["code"]);bar,reason=d.candle(row,stock["market"]) if row else (None,"MISSING_QUOTE")
            official.append(dict(date=date,original_record=row,bar=bar,refusal=reason,source=source[(date,stock["market"])]))
        matched=field_matches(bars[-1],official[0]["bar"] or {});identity_ok=stock["isin"]==byday[identity]["isin"]==bystate[identity]["isin"] and stock["market"]==byday[identity]["market"]==bystate[identity]["market"]
        partial_coverage=catalog.get("coverage",{}).get(stock["code"]);known=[a for a in actions["events"] if a["code"]==stock["code"] and bars[0]["date"]<=a["ex_date"]<=fm["as_of"]]
        case=dict(identity=identity,name=stock["name"],market=stock["market"],status=diagnostic_status(identity_ok,matched),raw_history_records=len(bars),history_start=bars[0]["date"],history_end=bars[-1]["date"],isin=stock["isin"],identity_same_current_snapshots=identity_ok,historical_identity_completeness="UNKNOWN",acquisition=acq,calendar_acquisition=v["calendar_acquisition"],request=request,raw_source_path=str(rawpath),raw_source_sha256=sha(raw),raw_anchor_fields={k:str(raw_anchor[k]) for k in ["date","stock_id","open","max","min","close","Trading_Volume"]},normalized_original_anchor=bars[-1],official_points=official,anchor_numeric_matches=matched,original_comparison=v["official_comparison"],original_core_context=v["result"]["context"],original_core_result_id=v["result"]["result_id"],original_basis_resets=v["input"]["basis_break_dates"],exact_native_share_precision=stock["history_source_provenance"]["exact_native_share_precision"],corporate_action_coverage=partial_coverage,known_action_counterexamples=[dict(event_id=a["id"],code=a["code"],ex_date=a["ex_date"],type=a["type"],source_ids=a["source_ids"],announced_at=a["announced_at"],observed_at=a["observed_at"],in_original_reset_list=a["ex_date"] in v["input"]["basis_break_dates"]) for a in known],official_to_official_boundary=dict(from_date="2026-11-02",to_date="2026-11-03",both_native_bars=all(o["bar"] is not None for o in official[1:]),price_basis_ids=[identity+"-OFFICIAL-RAW-UNBRIDGED-"+d for d in ["2026-11-02","2026-11-03"]],action_coverage="UNKNOWN_NO_INTERVAL_CERTIFICATE"),qualified_multiday=False,historical_signal_eligible=False)
        cases.append(case)
    # One necessary already-rejected OHLC counterexample; do not calculate core.
    bad=byfm["TPEX:1240"];params=dict(dataset="TaiwanStockPrice",data_id=bad["code"],start_date=max(fm["sources"]["start"],bad["listed_at"]),end_date=fm["as_of"]);receipt=Journal(ROOT/"source-receipts").read(capture_key(params))["value"];p=dep(ROOT/"source-raw"/receipt["sha256"]);raw=bounded_bytes(p)
    if sha(raw)!=receipt["sha256"]:raise ValueError("COUNTEREXAMPLE_ORIGINAL_CHANGED")
    counter=dict(identity=bad["identity"],status="REFUSED_EXISTING_HISTORY_QUALITY",saved_reason=bad["reason"],source_receipt=receipt,source_path=str(p),raw_sha256=sha(raw),raw_invalid_rows=[])
    data=_parse(raw)["data"]
    for row in data:
        prices=[Decimal(row[k]) for k in ["open","max","min","close"]];volume=Decimal(row["Trading_Volume"])
        if any(x<=0 for x in prices) and not (all(x==0 for x in prices) and volume==0):
            counter["raw_invalid_rows"].append({k:str(row[k]) for k in ["date","stock_id","open","max","min","close","Trading_Volume"]})
            break
    if not counter["raw_invalid_rows"]:raise ValueError("SAVED_COUNTEREXAMPLE_NOT_REPRODUCED")
    terminals=[]
    for s in state["stocks"]:
        status="SOURCE_REFUSED_11_03" if s["status"]!="SOURCE_BAR_AVAILABLE" else "NOT_REVIEWED_THIS_SCOPE"
        if s["identity"] in CODES:status=next(c["status"] for c in cases if c["identity"]==s["identity"])
        if s["identity"]==counter["identity"]:status=counter["status"]
        terminals.append(dict(identity=s["identity"],history_bridge_status=status,qualified_multiday=False))
    assert heads(ROOT)==before and sha(pointer.read_bytes())==view_sha
    report=dict(schema="history-bridge-evidence-review/0.1",status="BLOCKED_INTERVAL_BASIS_ACTION_EVIDENCE",observed_at=datetime.now(timezone.utc).isoformat(),as_of="2026-11-03",cases=cases,counterexample=counter,qualified_multiday=0,reviewed_positive_history_cases=4,reviewed_counterexamples=1,reference=1986,new_source_GETs=0,new_core_calls=0,new_UI=False,original_heads=before,original_view_sha256=view_sha,dependencies=list(deps.values()),active_seconds=time.monotonic()-started,OS_ru_maxrss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source010_catalog_sha256=sha(catalog_path.read_bytes()),known_event_catalog_sha256=sha(events_path.read_bytes()))
    write(WORK/"qualification-private.json",encode(terminals));write(done,encode(report));return report
if __name__=="__main__":
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));r=run();print(json.dumps({k:v for k,v in r.items() if k not in ["cases","counterexample","dependencies","original_heads"]},ensure_ascii=False))
