"""Explicit RUN or EXECUTE; READ lazily avoids all decision/accounting engines."""
import argparse
import json
from pathlib import Path
from rotation_research.store import Journal


def main():
    p=argparse.ArgumentParser()
    p.add_argument('operation', choices=['RUN','EXECUTE','READ'])
    p.add_argument('--input');p.add_argument('--store',required=True);p.add_argument('--id',required=True)
    p.add_argument('--prior-id',help='For a later RUN, carry reviewed event identities from a saved decision')
    p.add_argument('--checkpoint',help='Original-ledger execution checkpoint required with --prior-id')
    p.add_argument('--cancel-orders',nargs='*',default=[],help='Explicit unfilled order identities cancelled at this review')
    a=p.parse_args();store=Journal(a.store)
    if a.operation=='READ':
        saved=store.read(a.id)
    else:
        if not a.input:p.error('Explicit input required')
        value=json.loads(Path(a.input).read_text())
        if a.operation=='RUN':
            from .core import decide, resume_decision
            if a.prior_id and not a.checkpoint:p.error('--prior-id requires --checkpoint; tokens alone do not prove account continuity')
            result=resume_decision(store.read(a.prior_id)['value'],value,
                checkpoint=json.loads(Path(a.checkpoint).read_text()),cancelled_order_ids=a.cancel_orders) if a.prior_id else decide(value)
        else:
            from .execution import simulate
            result=simulate(value)
        saved=store.save(a.id,result)
    print(json.dumps(saved,ensure_ascii=False,sort_keys=True,allow_nan=False))


if __name__=='__main__':main()
