"""Explicit local M-R2 RUN over saved snapshots and supplied research summaries.

No graph generation, market fetching, READ framework or source authentication.
"""
import argparse
import json
from pathlib import Path

from .event_diary import build, public_summary
from .finmind_run import external_path
from rotation_research.store import Journal


def run(request_path, journal_dir, *, as_of, key):
    request_path=external_path(request_path); journal_dir=external_path(journal_dir)
    request=json.loads(request_path.read_text())
    result=build(request,as_of=as_of)
    journal=Journal(journal_dir)
    record=journal.save(key,result)
    if journal.read(key)!=record or record['value']!=result:
        raise ValueError('DIARY_SAVE_READBACK_MISMATCH')
    return dict(storage_status='SAVED_AND_READ_BACK',research_status=result['real_research_connection'],
                summary=public_summary(record['value']))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',required=True);p.add_argument('--journal-dir',required=True)
    p.add_argument('--as-of',required=True);p.add_argument('--key',required=True)
    args=p.parse_args()
    result=run(args.request,args.journal_dir,as_of=args.as_of,key=args.key)
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
