"""Create-only evidence writer. Expected results never depend on actuals."""
import argparse
import hashlib
import json
from pathlib import Path
from capital_research.core import VERSION as DECISION
from capital_research.execution import VERSION as EXECUTION
from capital_research.continuity import CHECKPOINT
from capital_research.reassessment_history import ATTEMPT
from .fixtures import ROOT,CASES,specification,materialize,observed


def save(path,x):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def capture(output):
    out=Path(output)
    paths=list(ROOT.glob('*.py'))+list(Path(__file__).parent.glob('*.py'))
    save(out/'source-versions.json',dict(decision=DECISION,execution=EXECUTION,
        checkpoint=CHECKPOINT,attempt=ATTEMPT,
        sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}))
    specs={name:specification(name) for name in CASES}
    for name,s in specs.items():
        for tag,value in [('specification',s),('first-input',s['first_input']),('expected',s['expected'])]:save(out/name/(tag+'.json'),value)
    summary={}
    for name,s in specs.items():
        try:
            r=materialize(s,record=lambda tag,x:save(out/name/(tag+'.json'),x))
            summary[name]=observed(r)
        except Exception as exc:
            save(out/name/'diagnostic.json',dict(type=type(exc).__name__,message=str(exc)))
            raise
        print(name,json.dumps({k:v for k,v in summary[name].items() if k!='order_states'}),flush=True)
    save(out/'summary.json',summary)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    capture(p.parse_args().output)
