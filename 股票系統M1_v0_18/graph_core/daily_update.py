"""Prepared private daily coordinator. No scheduler is installed or enabled."""
import argparse
import fcntl
import json
import os
from pathlib import Path

from graph_core.market_daily import outside,capture,process,encode,Journal
from graph_core.market_preview import build


def update(root, *, finmind_start=None, finmind_limit=240):
    root=outside(root);root.mkdir(parents=True,exist_ok=True)
    # One writer only; never overlap an existing daily run.
    with (root/'daily.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=root/'current-run.json';parent=json.loads(state.read_text())['id'] if state.exists() else None
        cap=capture(root)
        if finmind_start is not None:
            # Explicit alternative source run, not a cross-feed history merge.
            from graph_core.market_finmind import reference,run
            ref=reference(root,cap)
            result=run(root,ref,finmind_start,limit=finmind_limit)
            result['private_preview']=build(root,result['id'])
            # Preserve the original official daily head and all older evidence.
            state=root/'current-finmind-run.json';tmp=root/'current-finmind.pending'
            tmp.write_bytes(encode(dict(id=result['id'],private_preview=result['private_preview'])))
            with tmp.open('rb') as f:os.fsync(f.fileno())
            os.replace(tmp,state)
            return result
        try:result=process(root,cap,parent_run=parent)
        except ValueError as e:
            # No silent stale-data success: preserve the last head and report why
            # this new capture could not be accepted (date, version or source).
            return dict(status='BLOCKED',reason=str(e),capture_id=cap,last_saved_run=parent,
                last_saved_summary=Journal(root/'runs').read(parent)['value']['summary'] if parent else None,
                new_capture_applied=False,head_unchanged=True)
        summary=result['summary']
        if summary['both_market_universes_read'] and summary['both_market_quotes_read'] and summary['all_known_members_have_terminal']:
            tmp=root/'current-run.pending';tmp.write_bytes(encode({'id':result['id']}))
            with tmp.open('rb') as f:os.fsync(f.fileno())
            os.replace(tmp,state)
        try:result['private_preview']=build(root,result['id'])
        except ValueError as e:result['private_preview']={'status':'BLOCKED','reason':str(e)}
        return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--finmind-start');p.add_argument('--finmind-limit',type=int,default=240);p.add_argument('--increment',action='store_true');p.add_argument('--seed-run');p.add_argument('--capture');p.add_argument('--correction-of');p.add_argument('--correction-reason');a=p.parse_args();
    if a.increment:
        if a.finmind_start:p.error('Historical refetch and incremental continuation are separate actions')
        from graph_core.market_increment import update as incremental_update
        result=incremental_update(a.root,seed_run=a.seed_run,capture_id=a.capture,fetch=not bool(a.capture),correction_of=a.correction_of,correction_reason=a.correction_reason)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        raise SystemExit(2 if result.get('status') in ('BLOCKED','COMMITTED_DURABILITY_UNKNOWN') else 0)
    print(json.dumps(update(a.root,finmind_start=a.finmind_start,finmind_limit=a.finmind_limit),ensure_ascii=False,indent=2))
