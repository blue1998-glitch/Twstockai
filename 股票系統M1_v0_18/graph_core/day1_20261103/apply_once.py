"""Apply exactly one already-qualified capture with existing DU1/DU2 engine.
No provider requests, schedule, listener, original rewrites or cleanup.
"""
import argparse,json,os,resource,shutil,time
from pathlib import Path
from unittest.mock import patch
from graph_core import market_increment as increment
from graph_core import market_preview
from graph_core.day1_20261103.capacity_guard import guarded_writes,MINIMUM
from graph_core.day1_20261103.probe_once import heads,stamp
from rotation_research import artifact_codec as codec
from rotation_research.private_portability import private


def file_state(root):
    return {str(p.relative_to(root)):(p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ino) for p in root.rglob('*') if p.is_file() and not p.is_symlink()}

def allocated(root,old_inodes):
    """New unique regular-file blocks only; directory/auxiliary cost is
    measured separately by actual filesystem free-space change.
    """
    seen=set();total=0
    for p in [root,*root.rglob('*')]:
        if not p.is_file() or p.is_symlink():continue
        s=p.lstat();key=(s.st_dev,s.st_ino)
        if key not in old_inodes and key not in seen:seen.add(key);total+=s.st_blocks*512
    return total

def apply(root,work,capture_root):
    root=private(root);work=private(work);capture_root=private(capture_root);work.mkdir(mode=0o700,parents=True,exist_ok=True)
    if (work/'increment-started.json').exists():raise FileExistsError('REAL_INCREMENT_ALREADY_ATTEMPTED_NO_AUTOMATIC_RETRY')
    qualification=json.loads((capture_root/'probe-private.json').read_bytes())
    if qualification['status']!='READY_FOR_REAL_INCREMENT':raise ValueError('QUALIFIED_SAVED_CAPTURE_REQUIRED')
    cap=qualification['capture_id'];as_of,maps,markets,signatures=increment.sources(capture_root,cap)
    seed_state=json.loads((root/'fm3-continuation.json').read_bytes());old_heads=heads(root);parent_id=json.loads((root/'current-increment-run.json').read_bytes())['id'] if (root/'current-increment-run.json').exists() else seed_state['result']['id'];parent=increment.seed(root,parent_id)
    forecast=json.loads((Path(__file__).resolve().parents[1]/'du2_20261102/capacity-forecast.json').read_bytes())
    # Existing DU2 small-sample estimate + measured REAL1 private artifacts + source/catalogue margin; not an actual-write promise.
    estimate=forecast['full_market_compact_first_day_estimate_bytes']+195633152+128*1024*1024
    closing_reserve=64*1024*1024;guard_floor=MINIMUM+closing_reserve;free=shutil.disk_usage(root).free
    if free<estimate+guard_floor:
        blocked=dict(status='CAPACITY_PREFLIGHT_BLOCKED',estimated_bytes=estimate,guard_floor_bytes=guard_floor,available_bytes=free,new_core_calls=0,head_unchanged=True)
        codec.immutable(work/'increment-result-private.json',codec.encoded(blocked));print(json.dumps(blocked));return blocked
    originals=file_state(root);old_inodes={(p.stat().st_dev,p.stat().st_ino) for base in (root,capture_root) for p in base.rglob('*') if p.is_file()}
    codec.immutable(work/'increment-started.json',codec.encoded(dict(capture_id=cap,source_date=as_of,started_at=stamp(),minimum_free_bytes=MINIMUM,closing_reserve_bytes=closing_reserve,guard_floor_bytes=guard_floor,estimated_new_bytes=estimate,free_before_bytes=free,estimate_is_extrapolation=True)))
    start=time.monotonic();calls=0;original_analyze=increment.analyze
    def counted(*args,**kwargs):
        nonlocal calls
        calls+=1
        if calls==1 or calls%20==0:print(json.dumps(dict(phase='REAL_INCREMENT_CORE',core_calls=calls,free_bytes=shutil.disk_usage(root).free)),flush=True)
        return original_analyze(*args,**kwargs)
    try:
        with guarded_writes(root,minimum_free=guard_floor),patch.object(increment,'analyze',counted):
            # Import the very same captured bytes by safe hardlink, not by a new fetch.
            for sub in ('raw','captures'):
                (root/sub).mkdir(exist_ok=True)
                for src in (capture_root/sub).iterdir():
                    target=root/sub/src.name
                    if target.exists():
                        if codec.sha(target.read_bytes())!=codec.sha(src.read_bytes()):raise ValueError('CAPTURE_IMPORT_CONFLICT_OLD_SOURCE_PRESERVED')
                    else:
                        if shutil.disk_usage(root).free<guard_floor+64*1024:raise OSError('CAPACITY_RESERVE_BEFORE_SOURCE_ALIAS')
                        os.link(src,target)
            result=increment.update(root,seed_run=parent_id,capture_id=cap,fetch=False,storage_mode='compact')
    except Exception as error:
        result=dict(status='REAL_INCREMENT_BLOCKED',reason=type(error).__name__+': '+str(error),new_capture_applied=False)
    snapshot=file_state(root)
    changed_old=[name for name,metadata in originals.items() if snapshot.get(name)!=metadata]
    if changed_old:raise ValueError('OLD_ORIGINAL_PATH_METADATA_CHANGED')
    result.update(actual_counted_core_calls=calls,real_source_date=as_of,original_as_of=parent['as_of'],elapsed_seconds=time.monotonic()-start,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        source_api_calls=0,minimum_free_bytes=MINIMUM,guard_floor_bytes=guard_floor,free_before_bytes=free,free_after_bytes=shutil.disk_usage(root).free,new_root_allocated_bytes=allocated(root,old_inodes),
        old_original_paths_checked=len(originals),old_original_path_metadata_unchanged=True,heads_before=old_heads,heads_after=heads(root),schedule_started=False,server_started=False)
    codec.immutable(work/'increment-result-private.json',codec.encoded(result))
    if result.get('id') and (root/'current-increment-run.json').exists() and json.loads((root/'current-increment-run.json').read_bytes())['id']==result['id']:
        before_repeat=file_state(root)
        with guarded_writes(root,minimum_free=guard_floor),patch.object(increment,'analyze',side_effect=AssertionError('Same source must not reanalyze')),patch.object(market_preview,'build',side_effect=AssertionError('Same source must not republish preview')):
            repeat=increment.update(root,capture_id=cap,fetch=False,storage_mode='compact')
        if file_state(root)!=before_repeat or repeat['new_core_calls']!=0:raise ValueError('SAME_SOURCE_REPLAY_NOT_ZERO_WRITE_OR_CALC')
        codec.immutable(work/'repeat-private.json',codec.encoded(dict(status='PASS_REAL_SAME_SOURCE_ZERO_RECALC_ZERO_NEW_FILES',id=repeat['id'],new_core_calls=0,source_api_calls=0,root_file_state_unchanged=True,head_unchanged=repeat['head_unchanged'])))
    print(json.dumps({k:v for k,v in result.items() if k not in ('private_preview','heads_before','heads_after','terminal_diagnostic')},ensure_ascii=False),flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--work',required=True);p.add_argument('--capture-root',required=True);a=p.parse_args();v=apply(a.root,a.work,a.capture_root)
    if v.get('status') in ('CAPACITY_PREFLIGHT_BLOCKED','REAL_INCREMENT_BLOCKED','BLOCKED','COMMITTED_DURABILITY_UNKNOWN'):raise SystemExit(2)
