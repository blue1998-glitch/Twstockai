"""Explicit event-ledger RUN; reuse immutable Journal; READ never imports engines."""
import argparse
import json
from pathlib import Path
from .store import Journal


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('operation',choices=['RUN','READ'])
    parser.add_argument('--store',required=True);parser.add_argument('--id',required=True)
    parser.add_argument('--input')
    args=parser.parse_args();journal=Journal(args.store)
    if args.operation=='RUN':
        if not args.input:parser.error('RUN requires --input')
        from .action_ledger import replay
        record=journal.save(args.id,replay(json.loads(Path(args.input).read_text())))
    else:record=journal.read(args.id)
    print(json.dumps(record,ensure_ascii=False,sort_keys=True,allow_nan=False))


if __name__=='__main__':main()
