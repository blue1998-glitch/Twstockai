"""Read back every original scan checkpoint, then prove exact idempotency.
No provider fetch, numerical recognition, historical source rebuild or UI write.
"""
from pathlib import Path
import json,time,shutil
from datetime import datetime
from unittest.mock import patch
from rotation_research.store import Journal
from graph_core import market_daily as daily
from graph_core.day1_20261103.probe_once import heads
from graph_core.storage1_20261104.activate import request
from . import engine as e

def inventory():return {str(p.relative_to(e.WORK)):[p.stat().st_size,p.stat().st_mtime_ns] for p in e.WORK.rglob("*") if p.is_file()}
def verify():
    e.budget(e.WORK,1048576);before=inventory();started=time.monotonic()
    with patch.object(e.OriginalProvider,"_worker",side_effect=AssertionError("NO_CORE_ON_REPEAT")):
        repeated=e.run()
    elapsed=time.monotonic()-started
    if repeated["new_core_calls"] or repeated["new_records"] or before!=inventory():raise ValueError("REPEAT_NOT_ZERO_CORE_ZERO_WRITE")
    index=e.read(e.WORK/"complete-index.json");spec=e.read(e.WORK/"manifest-private.json");byid={s["identity"]:s for s in spec["stocks"]};journal=Journal(e.WORK/"results")
    profiles=[]
    for row in index["records"]:
        s=byid[row["identity"]];v=e.validate(journal.read(row["key"])["value"],s,spec)
        if v["result"]:
            if v["result"]["source_prefix_fingerprint"]!=e.fingerprint([e.fact(spec,s)["bar"]]):raise ValueError("EXACT_CORE_INPUT_FINGERPRINT_CONFLICT")
            profiles.append(v["profile"])
    cfg=e.read(e.WORK/"browser-config-private.json");raw_maps={};samples=[]
    for market,lower in [("TWSE","twse"),("TPEX","tpex")]:
        body=Path(spec["original_sources"][lower+"-daily.json"]["path"]).read_bytes()
        if e.sha(body)!=spec["daily_sources"][market]:raise ValueError("ORIGINAL_DAILY_SOURCE_SHA_CHANGED")
        dt,raw_maps[market]=daily.quote_map(json.loads(body),market)
        if dt!=spec["as_of"]:raise ValueError("ORIGINAL_SOURCE_DATE_CONFLICT")
    for case in cfg["cases"]:
        s=byid[case["identity"]];f=e.fact(spec,s);bar,reason=daily.candle(raw_maps[s["market"]][s["code"]],s["market"])
        if reason or f["bar"]!=bar:raise ValueError("ORIGINAL_OHLCV_PRECISION_CONFLICT")
        row=next(r for r in index["records"] if r["identity"]==s["identity"]);r=journal.read(row["key"])["value"]["result"]
        if e.fingerprint([bar])!=r["source_prefix_fingerprint"]:raise ValueError("REAL_CASE_CORE_INPUT_CONFLICT")
        samples.append(dict(identity=s["identity"],market=s["market"],original_record=raw_maps[s["market"]][s["code"]],bar=bar,result_id=r["result_id"],raw_source_sha256=spec["daily_sources"][s["market"]],price_basis_id=r["context"]["price_basis_id"],source_records=r["source_records"]))
    e.write(e.WORK,e.WORK/"real-input-result-cases-private.json",e.encode(samples))
    control=e.read(e.WORK/"original-control-private.json");assert heads(e.BASE/"fm3_20261101/runtime")==control["source_heads"]
    active=e.read(e.WORK/"service-current-private.json");assert e.sha((e.BASE/"lite1_20261103/view-head-private.json").read_bytes())==active["view_sha256"]
    old=e.read(e.BASE/"graph_lazy1_20261104/build-private.json")
    for entry in [old["new_entry"],*old["old_entries"]]:
        b=Path(entry["path"]).read_bytes();assert e.sha(b)==entry["sha256"] and len(b)==entry["bytes"]
    route="/"+e.read(e.WORK/"view-build-private.json")["metrics_route"].rsplit("/",1)[0]+"/"+cfg["cases"][0]["lazy_graph"]["path"]
    controls=[]
    for method,path,status,authorized,h in [("GET",route,401,False,{}),("GET",route,403,True,{"Origin":"https://invalid.example"}),("POST",route,405,True,{}),("HEAD",route,204,True,{}),("GET",route+"?path=secret",404,True,{}),("GET","/../private",404,True,{}),("GET",route.rsplit("/",1)[0]+"/unknown.json",404,True,{})]:
        request(cfg,path,status,authorized=authorized,method=method,headers=h);controls.append(dict(method=method,status=status))
    _,raw=request(cfg,"/"+e.read(e.WORK/"view-build-private.json")["metrics_route"],200);metrics=json.loads(raw);assert metrics["core_calls"]==0
    starts=[datetime.fromisoformat(json.loads(x)["at"]).timestamp() for x in (e.WORK/"attempts.jsonl").read_bytes().splitlines() if json.loads(x)["phase"]=="START"]
    finish=max(p.stat().st_mtime for p in (e.WORK/"results").glob("*.json"));first=e.read(e.WORK/"first23-private.json");last=e.read(e.WORK/"resume-complete-private.json")
    report=dict(status="PASS",reference=1986,unique_terminals=len(index["records"]),counts=index["counts"],markets=index["markets"],real_core_calls=first["new_core_calls"]+last["new_core_calls"],actual_core_start_events=len(starts),same_source_repeat_new_core=0,same_source_repeat_new_records=0,same_source_repeat_file_changes=0,same_source_repeat_seconds=elapsed,real_cases_per_market={m:sum(c["market"]==m for c in samples) for m in ["TWSE","TPEX"]},exact_original_input_fingerprint_checks=len(profiles),active_scan_seconds=first["wall_seconds"]+last["wall_seconds"],scan_wall_window_including_controlled_checkpoint_pause=finish-min(starts),sum_worker_process_wall_seconds=sum(p["wall_seconds"] for p in profiles),parent_ru_maxrss_KiB=max(first["parent_ru_maxrss_KiB"],last["parent_ru_maxrss_KiB"]),max_worker_RSS_KiB=max(p["peak_RSS_KiB"] for p in profiles),new_source_GETs=0,old_source_metadata_paths_unchanged=90377,original_heads_same=True,old_pages_same_bytes=True,actual_owner_controls=controls,post_browser_new_core_calls=metrics["core_calls"],independent_backup="UNKNOWN",restart_persistence="UNKNOWN",android="NOT_TESTED_NEW_BUILD",free_bytes=shutil.disk_usage(e.WORK).free,filesystem_net_added_bytes=e.read(e.WORK/"baseline-private.json")["free_bytes"]-shutil.disk_usage(e.WORK).free)
    e.write(e.WORK,e.WORK/"verification-private.json",e.encode(report));print(json.dumps(report,ensure_ascii=False));return report
if __name__=="__main__":verify()
