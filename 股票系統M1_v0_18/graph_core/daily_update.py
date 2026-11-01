"""Prepared private daily coordinator. No scheduler is installed or enabled."""
import argparse
import fcntl
import json
import os
from pathlib import Path

from graph_core.market_daily import outside,capture,process,encode,Journal
from graph_core.market_preview import build


def update(root):
    root=outside(root);root.mkdir(parents=True,exist_ok=True)
    # One writer only; never overlap an existing daily run.
    with (root/'daily.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=root/'current-run.json';parent=json.loads(state.read_text())['id'] if state.exists() else None
        cap=capture(root)
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
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();print(json.dumps(update(a.root),ensure_ascii=False,indent=2))
