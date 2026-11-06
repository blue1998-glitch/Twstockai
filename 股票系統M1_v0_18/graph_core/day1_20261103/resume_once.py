"""Explicit single-writer resume after a proven dead DAY1 process.
Saved source/batch/checkpoints only; new capture or core calls are forbidden.
"""
import json,os,resource,shutil,time,sys
from pathlib import Path
from unittest.mock import patch
from graph_core import market_increment as inc,market_preview
from graph_core.day1_20261103.capacity_guard import guarded_writes,MINIMUM
from graph_core.day1_20261103.apply_once import file_state,allocated
from graph_core.day1_20261103.probe_once import stamp,heads
from rotation_research import artifact_codec as c
from rotation_research.store import Journal

def resume(root,work,dead_pid):
 root=Path(root);work=Path(work);proc=Path('/proc')/str(dead_pid)/'stat'
 state=proc.read_text().split() if proc.exists() else None
 if state and state[2]!='Z':raise ValueError('PREVIOUS_WRITER_NOT_PROVEN_STOPPED')
 if (work/'resume-started.json').exists():raise ValueError('NO_AUTOMATIC_REPEATED_RESUME')
 original=json.loads((work/'increment-started.json').read_bytes());cap=original['capture_id'];dt,maps,markets,sigs=inc.sources(root,cap)
 seed=json.loads((root/'fm3-continuation.json').read_bytes())['result']['id'];batches=[]
 for path in (root/'runs').glob('du1-*.json'):
  b=Journal(root/'runs').read(path.stem)['value']
  if b['capture_id']==cap:batches.append((path.stem,b))
 if len(batches)!=1:raise ValueError('EXACT_ONE_COMPLETED_SAVED_BATCH_REQUIRED')
 run_id,batch=batches[0]
 if batch['parent_run']!=seed or batch['summary']['processed']!=sum(len(v['members']) for v in markets.values()) or batch['sources']!=sigs:raise ValueError('SAVED_BATCH_SOURCE_OR_SEED_CONFLICT')
 if batch['producer_sha256']!=c.sha(Path(inc.__file__).read_bytes()) or batch['engine_sha256']!=c.sha((Path(inc.__file__).parent/'core.py').read_bytes()):raise ValueError('ORIGINAL_PRODUCER_OR_ENGINE_CHANGED')
 if (root/'current-increment-run.json').exists():raise ValueError('HEAD_ALREADY_EXISTS_REVIEW_INSTEAD_OF_RESUME')
 snapshot=file_state(root);inodes={(p.stat().st_dev,p.stat().st_ino) for p in root.rglob('*') if p.is_file()};free=shutil.disk_usage(root).free;start=time.monotonic();charts=0;existing=0
 c.immutable(work/'resume-started.json',c.encoded(dict(started_at=stamp(),prior_pid=dead_pid,prior_state=state[2] if state else 'ABSENT',prior_wait_status=int(state[-1]) if state else None,prior_cpu_seconds=(int(state[13])+int(state[14]))/os.sysconf('SC_CLK_TCK') if state else None,prior_oom_kills=0,reason='SIGKILL observed; exact sender/cause unknown; not evidence of OOM',same_capture_id=cap,saved_terminals=len(batch['stocks']),existing_preview_sidecars=len(list((root/'preview'/run_id).glob('series-*.json.du2'))),free_before_bytes=free)))
 original_publish=c.publish_interned
 def progress(path,raw,**kw):
  nonlocal charts,existing
  if Path(path).parent==root/'preview'/run_id:
   charts+=1;existing+=int(c.exists(path))
   if charts==1 or charts%20==0:print(json.dumps(dict(phase='SAVED_BATCH_PREVIEW_RESUME',charts_visited=charts,existing_charts=existing,free_bytes=shutil.disk_usage(root).free)),flush=True)
  return original_publish(path,raw,**kw)
 with guarded_writes(root,minimum_free=MINIMUM+64*1024*1024),patch.object(inc,'analyze',side_effect=AssertionError('Saved batch must not reanalyze')),patch.object(c,'publish_interned',progress):
  result=inc.update(root,seed_run=seed,capture_id=cap,fetch=False,storage_mode='compact')
 changed=[n for n,m in snapshot.items() if file_state(root).get(n)!=m] if False else None
 after=file_state(root);changed=[n for n,m in snapshot.items() if after.get(n)!=m]
 if changed:raise ValueError('PRE_RESUME_FILE_CHANGED')
 result.update(resume_elapsed_seconds=time.monotonic()-start,resume_max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_api_calls=0,resume_core_calls=0,charts_visited=charts,existing_charts_verified=existing,pre_resume_paths_unchanged=len(snapshot),free_before_bytes=free,free_after_bytes=shutil.disk_usage(root).free,resume_new_allocated_bytes=allocated(root,inodes),completed_at=stamp(),head=heads(root),schedule_started=False,server_started=False)
 c.immutable(work/'resume-result-private.json',c.encoded(result))
 if result.get('id') and (root/'current-increment-run.json').exists():
  before=file_state(root)
  with guarded_writes(root,minimum_free=MINIMUM),patch.object(inc,'analyze',side_effect=AssertionError('Repeat core call')),patch.object(market_preview,'build',side_effect=AssertionError('Repeat preview build')):
   repeat=inc.update(root,capture_id=cap,fetch=False,storage_mode='compact')
  assert repeat['new_core_calls']==0 and repeat['head_unchanged'] and file_state(root)==before
  c.immutable(work/'repeat-private.json',c.encoded(dict(status='PASS_REAL_SAME_SOURCE_ZERO_RECALC_ZERO_NEW_FILES',source_api_calls=0,new_core_calls=0,root_file_state_unchanged=True,head_unchanged=True)))
 print(json.dumps({k:v for k,v in result.items() if k not in ('private_preview','terminal_diagnostic','head')},ensure_ascii=False),flush=True)
 if result.get('status') in ('BLOCKED','COMMITTED_DURABILITY_UNKNOWN'):raise SystemExit(2)
if __name__=='__main__':resume(Path(sys.argv[1]),Path(sys.argv[2]),int(sys.argv[3]))
