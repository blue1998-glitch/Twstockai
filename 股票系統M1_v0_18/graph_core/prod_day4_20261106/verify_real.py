"""Real day4 source/fact/Journal/readback, fresh-process zero-write replay.
All detailed market values stay outside Git. No source GET or core recomputation.
"""
import json,sys,subprocess,time,shutil,resource
from pathlib import Path
from . import intake
from graph_core.prod_core1_20261105 import flow as f
from graph_core.storage1_20261104.activate import request
from graph_core.day1_20261103.probe_once import heads
from rotation_research.store import Journal

def inventory(root):
    return {str(p):[p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ino] for p in root.rglob('*') if p.is_file()}
def main():
    w=intake.WORK;spec=f.source_check(w/'scan',intake.TARGET);index=f.read(w/'scan/complete-index.json');byid={s['identity']:s for s in spec['stocks']};rows={r['identity']:r for r in index['records']}
    conn=f.read(f.BASE/'scan1_20261104/browser-config-private.json');cases=[];journal=Journal(w/'scan/results')
    for case in conn['cases']:
        s=byid[case['identity']];fact=f.scan.fact(spec,s);row=rows[s['identity']];v=journal.read(row['key'])['value'];f.scan.validate(v,s,spec)
        assert fact['bar'] is not None and v['result']['source_prefix_fingerprint']==f.scan.fingerprint([fact['bar']])
        cases.append(dict(market=case['market'],code=case['code'],identity=s['identity'],fact=fact))
    refused=next(s for s in spec['stocks'] if rows[s['identity']]['status']=='SOURCE_REFUSED')
    bc=dict(conn,cases=cases,refused=dict(identity=refused['identity'],code=refused['code']),expected_date=intake.TARGET,expected_counts=index['counts'])
    intake.store.put(w,w/'browser-config-private.json',f.encode(bc))
    before={str(root):inventory(root) for root in [w,f.WORK,f.scan.WORK]};start=time.monotonic()
    proc=subprocess.run([sys.executable,'-m','graph_core.prod_day4_20261106.run'],capture_output=True,check=True,timeout=180)
    r=json.loads(proc.stdout);elapsed=time.monotonic()-start
    assert r['source_GETs']==r['new_core_calls']==r['new_records']==0 and r['reused']
    assert before=={str(root):inventory(root) for root in [w,f.WORK,f.scan.WORK]}
    source=f.read(w/'source-result-private.json');assert heads(f.BASE/'fm3_20261101/runtime')==source['source_heads']
    control=f.read(f.WORK/'original-control-private.json');assert f.descriptor(f.BASE/'lite1_20261103/view-head-private.json')==control['view_head']
    _,raw=request(conn,'/product-status.json',200);live=json.loads(raw);assert live['active_date']==intake.TARGET and live['reference']==1986 and live['latest_intake']['status']=='COMPLETE'
    report=dict(status='PASS',as_of=intake.TARGET,reference=len(rows),markets=index['markets'],counts=index['counts'],all_source_to_fact_exact=True,all_Journals_read_and_validated_by_replay=True,real_case_markets=[c['market'] for c in cases],real_case_count=len(cases),replay=r,replay_file_changes=0,replay_seconds=elapsed,FM3_heads_unchanged=True,old_scan_unchanged=True,old_lite_head_unchanged=True,free_bytes=shutil.disk_usage(w).free,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,child_peak_RSS_KiB=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,cloud_restart='NOT_PERFORMED',independent_backup='UNKNOWN',android='NOT_TESTED_NEW_BUILD')
    intake.store.put(w,w/'real-verification-private.json',f.encode(report));print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
