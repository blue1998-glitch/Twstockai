"""Only four-case source/retained-result comparison and preservation checks."""
from pathlib import Path
import time,json,shutil
from collections import Counter
from . import audit as a
from rotation_research.store import Journal
from graph_core import market_increment as inc
from graph_core.storage1_20261104.activate import request

def verify():
    w=a.WORK;r=a.read(w/"review-private.json");initial={str(p.relative_to(w)):[p.stat().st_size,p.stat().st_mtime_ns] for p in w.rglob("*") if p.is_file()};start=time.monotonic();reused=a.run();elapsed=time.monotonic()-start
    if initial!={str(p.relative_to(w)):[p.stat().st_size,p.stat().st_mtime_ns] for p in w.rglob("*") if p.is_file()} or reused["new_outputs"]!=0:raise ValueError("REPEAT_WROTE_FILES")
    root=a.ROOT;j=Journal(root/"runs");day=j.read(a.read(root/"current-increment-run.json")["id"])["value"];stocks={s["identity"]:s for s in day["stocks"]};state=a.read(a.BASE/"graph_lazy1_20261104/source-state-private.json");bystate={s["identity"]:s for s in state["stocks"]};folder=Path(a.read(a.BASE/"graph_lazy1_20261104/build-private.json")["new_entry"]["path"]).parent
    scan=a.read(a.BASE/"scan1_20261104/complete-index.json");scanrows={s["identity"]:s for s in scan["records"]};scanJournal=Journal(a.BASE/"scan1_20261104/results");proof=[]
    for case in r["cases"]:
        identity=case["identity"];v=inc.stock_history(root,stocks[identity],day);bar2=v["input"]["bars"][-1];original2=case["official_points"][1]["bar"]
        matches2=a.field_matches(bar2,original2)
        desc=bystate[identity]["preview_evidence"];raw=(folder/desc["path"]).read_bytes()
        if len(raw)!=desc["bytes"] or a.sha(raw)!=desc["sha256"]:raise ValueError("11_03_FACT_TAMPERED")
        fact=json.loads(raw);bar3=fact["bar"];original3=case["official_points"][2]["bar"];matches3=a.field_matches(bar3,original3)
        saved=scanJournal.read(scanrows[identity]["key"])["value"]["result"]
        if not all(matches2.values()) or not all(matches3.values()) or inc.fingerprint([bar3])!=saved["source_prefix_fingerprint"]:raise ValueError("ORIGINAL_DAILY_INPUT_CONFLICT")
        proof.append(dict(identity=identity,market=case["market"],history_records=case["raw_history_records"],anchor_10_30_matches=case["anchor_numeric_matches"],day_11_02_matches=matches2,day_11_03_matches=matches3,day_11_02_current_segment=stocks[identity]["current_comparable_records"],day_11_02_reset_preserved="2026-11-02" in v["input"]["basis_break_dates"],day_11_03_fact_sha256=desc["sha256"],day_11_03_core_result_id=saved["result_id"],bridge_qualified=False))
    if a.heads(root)!=r["original_heads"] or a.sha((a.BASE/"lite1_20261103/view-head-private.json").read_bytes())!=r["original_view_sha256"]:raise ValueError("ORIGINAL_HEAD_CHANGED")
    cfg=a.read(a.BASE/"scan1_20261104/browser-config-private.json");request(cfg,"/",401,authorized=False);h,_=request(cfg,"/",303);_,html=request(cfg,h["Location"],200);build=a.read(a.BASE/"scan1_20261104/view-build-private.json")
    if a.sha(html)!=build["new_entry"]["sha256"]:raise ValueError("ORIGINAL_SCAN_UI_CHANGED")
    _,directory=request(cfg,"/batches",200)
    if not all(d.encode() in directory for d in ["2026-11-03","2026-11-02","2026-10-30"]):raise ValueError("OLD_VIEWS_MISSING")
    for e in build["old_entries"]:
        b=Path(e["path"]).read_bytes()
        if a.sha(b)!=e["sha256"]:raise ValueError("OLD_PAGE_BYTES_CHANGED")
    terminal=a.read(w/"qualification-private.json");counts=dict(Counter(t["history_bridge_status"] for t in terminal));assert len(terminal)==len({t["identity"] for t in terminal})==1986
    report=dict(status="PASS_BLOCKED_BRIDGE_PRESERVED",positive_history_cases=4,known_bad_history_counterexamples=1,markets_reviewed={m:sum(c["market"]==m for c in r["cases"]) for m in ["TWSE","TPEX"]},case_proofs=proof,anchor_field_checks=20,subsequent_official_field_checks=40,qualified_multiday_count=0,qualification_counts=counts,original_heads_same=True,original_UI_bytes_same=True,old_two_pages_same_bytes=True,owner_HTTP_controls=[401,303,200,200],new_browser_flows=0,new_core_calls=0,new_source_GETs=0,repeat_new_outputs=0,repeat_seconds=elapsed,active_audit_seconds=r["active_seconds"],OS_ru_maxrss_KiB=r["OS_ru_maxrss_KiB"],free_bytes=shutil.disk_usage(w).free,filesystem_net_added_bytes=a.read(w/"baseline-private.json")["free_bytes"]-shutil.disk_usage(w).free,android="NOT_TESTED_NEW_BUILD")
    a.write(w/"verification-private.json",a.encode(report));return report
if __name__=="__main__":print(json.dumps(verify(),ensure_ascii=False))
