"""Explicit new RUN or numerical-engine-free READ of saved evaluation stages."""
import argparse
import json
from pathlib import Path
from .evaluated_replay import run_evaluated_replay,read_evaluated_replay,render_text


def main():
    p=argparse.ArgumentParser(description='明示合成回放完成後另存評估，READ不重算')
    p.add_argument('operation',choices=('RUN','READ'));p.add_argument('--store',required=True);p.add_argument('--id',required=True)
    p.add_argument('--input');p.add_argument('--format',choices=('text','json'),default='text');a=p.parse_args()
    if a.operation=='READ':
        if a.input:p.error('READ does not accept --input')
        receipt=read_evaluated_replay(a.store,a.id)
    else:
        if not a.input:p.error('RUN requires explicit --input')
        try:request=json.loads(Path(a.input).read_text())
        except (OSError,ValueError) as exc:p.exit(2,'EVALUATED_REPLAY_INPUT_FAILED: '+str(exc)+'\n')
        receipt=run_evaluated_replay(a.store,a.id,request)
    print(json.dumps(receipt,ensure_ascii=False,indent=2) if a.format=='json' else render_text(receipt),
        end='\n' if a.format=='json' else '')
    return 0 if receipt['workflow_status'] in ('COMPLETED_EVALUATED','READ_ONLY') and receipt['operation'] and receipt['operation']['outcome']=='COMPLETED_EVALUATED' else 2


if __name__=='__main__':raise SystemExit(main())
