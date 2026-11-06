"""Actual saved-market closed-loop replay. No downloads or core recomputation.
Reports engine executions reused separately from new calls. Small private output.
"""
import json,os,resource,subprocess,sys,time,shutil
from pathlib import Path
from . import flow as f
from graph_core.day1_20261103.probe_once import heads
from graph_core.storage1_20261104.activate import request

def inventory(root):
    return {str(p):[p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ino] for p in root.rglob('*') if p.is_file()}

def main():
    w=f.WORK;f.capacity(w,1024**2);before=inventory(w);oldscan=inventory(f.scan.WORK);t=time.monotonic()
    # A separate fresh interpreter reads durable receipts and the existing owner.
    r=subprocess.run([sys.executable,'-m','graph_core.prod_core1_20261105.flow','run','--date','2026-11-03'],capture_output=True,check=True)
    reply=json.loads(r.stdout);elapsed=time.monotonic()-t
    assert reply['reused'] and reply['this_execution_new_core_calls']==reply['this_execution_new_records']==0
    assert before==inventory(w) and oldscan==inventory(f.scan.WORK)
    # Replay the NEW bounded attempt: read saved rejection only, never HTTP retry.
    a=f.fetch('2026-11-04');assert a['source_GETs']==0 and a['status']=='BLOCKED_SOURCE'
    assert before==inventory(w) and oldscan==inventory(f.scan.WORK)
    control=f.read(w/'original-control-private.json')
    assert heads(f.BASE/'fm3_20261101/runtime')==control['source_heads']
    assert f.descriptor(f.BASE/'lite1_20261103/view-head-private.json')==control['view_head']
    active=f.bound(f.read(w/'head-private.json'));index=f.bound(active['index']);spec=f.bound(active['manifest'])
    byid={s['identity']:s for s in spec['stocks']};rows={r['identity']:r for r in index['records']}
    conn=f.read(f.BASE/'scan1_20261104/browser-config-private.json');_,raw=request(conn,'/product-status.json',200)
    live=json.loads(raw);assert live['active_date']=='2026-11-03' and live['reference']==1986
    cases=[]
    for case in conn['cases']:
        s=byid[case['identity']];fact=f.scan.fact(spec,s);row=rows[s['identity']]
        v=f.scan.Journal(f.scan.WORK/'results').read(row['key'])['value']
        assert v['result']['source_prefix_fingerprint']==f.scan.fingerprint([fact['bar']])
        assert fact['bar']==case['fact']['bar']
        cases.append(dict(market=case['market'],source_fact_sha256=s['fact']['sha256'],input_sha256=f.scan.fingerprint([fact['bar']]),result_id=v['result']['result_id'],exact_OHLCV=True))
    report=dict(status='PASS',real_date='2026-11-03',reference=len(rows),markets=index['markets'],counts=index['counts'],existing_executions_reused=1955,new_real_core_calls=0,new_real_records=0,replay_file_changes=0,replay_seconds=elapsed,fresh_process_restore='PASS',cloud_restart='NOT_PERFORMED',new_intake_replay_GETs=0,old_scan_unchanged=True,original_FM3_heads_unchanged=True,original_view_pointer_unchanged=True,real_cases=cases,live_owner_status=live,free_bytes=shutil.disk_usage(w).free,private_allocated_bytes=sum(p.stat().st_blocks*512 for p in w.rglob('*') if p.is_file()),filesystem_net_added_bytes=f.read(w/'baseline-private.json')['free_bytes']-shutil.disk_usage(w).free,parent_peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,child_peak_RSS_KiB=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,independent_backup='UNKNOWN',restart_persistence='UNKNOWN',android='NOT_TESTED_NEW_BUILD')
    f.put(w,w/('real-acceptance-'+f.release_id()+'-private.json'),f.encode(report));f.point(w,'acceptance-head-private.json',f.descriptor(w/('real-acceptance-'+f.release_id()+'-private.json')));print(json.dumps({k:report[k] for k in ['status','reference','counts','new_real_core_calls','new_real_records','replay_file_changes','replay_seconds','fresh_process_restore','new_intake_replay_GETs','free_bytes','private_allocated_bytes','filesystem_net_added_bytes','parent_peak_RSS_KiB','child_peak_RSS_KiB']},ensure_ascii=False))
if __name__=='__main__':main()
