"""Only this milestone's explicit new synthetic cases; exclusive evidence."""
import json
import sys
import traceback
from pathlib import Path
from capital_research.conditional_quantity_review import reassess_conditional
from .verify import verify

ROOT=Path(__file__).parent


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def main(stage):
    rows=[];results={}
    for p in sorted((ROOT/'cases').iterdir()):
        request=json.loads((p/'input.json').read_text());expected=json.loads((p/'expected.json').read_text())
        try:
            actual=reassess_conditional(request);save(ROOT/stage/p.name/'actual.json',actual);results[p.name]=actual
            verify(request,expected,actual);status='PASS';error=None
        except Exception:status='FAIL';error=traceback.format_exc()
        rows.append(dict(case=p.name,status=status,error=error));print(p.name,status,error or '',flush=True)
    if 'valid-C-same-order' in results and 'future-revocation-prefix' in results:
        a=results['valid-C-same-order']['review'];b=results['future-revocation-prefix']['review']
        if a['numeric_result']!=b['numeric_result']:
            next(r for r in rows if r['case']=='future-revocation-prefix').update(status='FAIL',error='future restriction changed numeric prefix')
    save(ROOT/stage/'summary.json',rows)
    if any(r['status']!='PASS' for r in rows):raise SystemExit(1)


if __name__=='__main__':main(sys.argv[1])
