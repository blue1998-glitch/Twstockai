"""Explicit read-only CLI; no output files, recovery, migration or RUN route."""
import argparse
import hashlib
import json
from pathlib import Path
from .lifecycle import summarize_saved, render_text


def main():
    parser=argparse.ArgumentParser(description='只讀已保存研究批次，不重算、不建單')
    parser.add_argument('path');parser.add_argument('--format',choices=('text','json'),default='text')
    args=parser.parse_args();path=Path(args.path)
    try:
        raw=path.read_bytes();saved=json.loads(raw)
        summary=summarize_saved(saved)
    except (OSError,ValueError) as exc:
        parser.exit(2,'READ_FAILED: '+str(exc)+'\n')
    if args.format=='json':
        print(json.dumps(dict(summary=summary,read_metadata=dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest())),ensure_ascii=False,indent=2))
    else:print(render_text(summary),end='')
    return 0 if summary['status'] in ('READABLE','NO_SAVED_EXECUTION') else 2


if __name__=='__main__':raise SystemExit(main())
