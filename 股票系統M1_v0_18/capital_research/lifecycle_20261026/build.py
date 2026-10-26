"""New READ projections only. No numerical producer or old test execution."""
import json
import sys
import traceback
from pathlib import Path
from capital_research.lifecycle import summarize_saved, render_text
from .fixtures import materialize
from .verify import verify

ROOT=Path(__file__).parent


def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')


def main(stage):
    rows=[];actuals={}
    for p in sorted((ROOT/'cases').iterdir()):
        spec=json.loads((p/'input.json').read_text());expected=json.loads((p/'expected.json').read_text())
        actual=summarize_saved(materialize(spec));actuals[p.name]=actual
        save(ROOT/stage/p.name/'actual.json',actual)
        with (ROOT/stage/p.name/'readable.txt').open('x') as f:f.write(render_text(actual))
        try:verify(expected,actual);status='PASS';error=None
        except Exception:status='FAIL';error=traceback.format_exc()
        rows.append(dict(case=p.name,status=status,error=error));print(p.name,status,flush=True)
    for p in sorted((ROOT/'cases').iterdir()):
        expected=json.loads((p/'expected.json').read_text())
        if 'same_orders_as' in expected:
            if actuals[p.name]['orders']!=actuals[expected['same_orders_as']]['orders']:
                row=next(r for r in rows if r['case']==p.name);row.update(status='FAIL',error='future saved tail changed order summary')
    save(ROOT/stage/'summary.json',rows)
    if any(r['status']!='PASS' for r in rows):raise SystemExit(1)


if __name__=='__main__':main(sys.argv[1])
