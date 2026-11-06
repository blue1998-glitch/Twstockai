"""Explicit RUN for only this milestone; outputs created exclusively."""
import hashlib
import json
from pathlib import Path
from capital_research.conditional_quantity_review import reassess_conditional
from .verify import verify

ROOT=Path(__file__).parent


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def main(stage='after-final'):
    summary=[];outputs={}
    for case in sorted((ROOT/'cases').iterdir()):
        request=json.loads((case/'input.json').read_text());expected=json.loads((case/'expected.json').read_text())
        actual=reassess_conditional(request);save(ROOT/stage/case.name/'actual.json',actual);outputs[case.name]=actual
        try:verify(request,expected,actual);status='PASS';error=None
        except (AssertionError,KeyError,TypeError) as exc:status='FAIL';error=repr(exc)
        summary.append(dict(case=case.name,status=status,error=error,actual_status=actual['review']['status'],reasons=actual['review']['reasons']))
        print(case.name,status,actual['review']['status'],error or '',flush=True)
    for case in sorted((ROOT/'cases').iterdir()):
        expected=json.loads((case/'expected.json').read_text())
        if 'same_numeric_as' in expected:
            row=next(x for x in summary if x['case']==case.name)
            if outputs[case.name]['review']['numeric_result']!=outputs[expected['same_numeric_as']]['review']['numeric_result']:
                row.update(status='FAIL',error='future numeric result differs')
    save(ROOT/stage/'summary.json',summary)
    if any(r['status']!='PASS' for r in summary):raise SystemExit(1)


if __name__=='__main__':
    import sys
    main(sys.argv[1] if len(sys.argv)>1 else 'after-final')
