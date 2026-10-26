"""Produce only new read projections; source files remain unchanged."""
import json
import sys
import traceback
from pathlib import Path
from capital_research.lifecycle_compare import compare_saved, render_comparison
from .fixtures import materialize
from .verify import verify

ROOT=Path(__file__).parent


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def main(stage):
    rows=[]
    for p in sorted((ROOT/'cases').iterdir()):
        request=materialize(json.loads((p/'input.json').read_text()))
        expected=json.loads((p/'expected.json').read_text());actual=compare_saved(request)
        save(ROOT/stage/p.name/'actual.json',actual)
        with (ROOT/stage/p.name/'readable.txt').open('x') as f:f.write(render_comparison(actual))
        try:verify(expected,actual);status='PASS';error=None
        except Exception:status='FAIL';error=traceback.format_exc()
        rows.append(dict(case=p.name,status=status,error=error));print(p.name,status,flush=True)
    save(ROOT/stage/'summary.json',rows)
    if any(r['status']!='PASS' for r in rows):raise SystemExit(1)


if __name__=='__main__':main(sys.argv[1])
