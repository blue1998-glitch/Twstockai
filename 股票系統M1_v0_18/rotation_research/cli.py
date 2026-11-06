"""Explicit RUN writes a new immutable record; READ only loads saved bytes."""
import argparse, json
from .store import Journal

def main():
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['RUN','READ'])
    p.add_argument('--store',required=True);p.add_argument('--id',required=True)
    p.add_argument('--input');p.add_argument('--A');p.add_argument('--B');p.add_argument('--cutoff');p.add_argument('--horizon',type=int)
    a=p.parse_args();store=Journal(a.store)
    if a.operation=='RUN':
        from .core import compare
        data=json.load(open(a.input));result=compare(data,a.A,a.B,a.cutoff,a.horizon)
        record=store.save(a.id,result)
    else: record=store.read(a.id)
    print(json.dumps(record,ensure_ascii=False,sort_keys=True))
if __name__=='__main__': main()
