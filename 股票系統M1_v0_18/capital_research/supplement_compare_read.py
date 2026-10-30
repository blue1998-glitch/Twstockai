"""Stdout-only explicit manifest reader; delegates all original integrity checks."""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
from .selection_supplement import read_supplement
from .supplement_compare import INPUT,compare_read_receipts,validate_items,empty_result,render_text

READ_INPUT='capital-supplement-comparison-read-input/0.1'
FIELDS={'label','parent_store','parent_id','store','id'}


def read_and_compare(request):
    try:
        if set(request)!={'schema','synthetic','items'} or request['schema']!=READ_INPUT or request['synthetic'] is not True:
            raise ValueError('EXPLICIT_SYNTHETIC_READ_MANIFEST_REQUIRED')
        validate_items(request['items'],FIELDS)
        for item in request['items']:
            if not all(isinstance(item[k],str) and bool(item[k].strip()) for k in FIELDS-{'label'}):
                raise ValueError('EXPLICIT_PARENT_AND_SUPPLEMENT_LOCATORS_REQUIRED')
        items=[dict(label=i['label'],receipt=read_supplement(i['parent_store'],i['parent_id'],i['store'],i['id']))
            for i in request['items']]
        result=compare_read_receipts(dict(schema=INPUT,synthetic=True,items=items))
    except (ValueError,KeyError,TypeError,AttributeError) as exc:
        result=empty_result();result['refusals'].append(dict(reason=str(exc)))
    return dict(comparison=result,read_metadata=dict(items=deepcopy(request.get('items')) if isinstance(request,dict) else None))


def main():
    p=argparse.ArgumentParser(description='只讀核對同父補選共同條件並列，不排名')
    p.add_argument('--input',required=True);p.add_argument('--format',choices=('text','json'),default='text');a=p.parse_args()
    try:
        path=Path(a.input);raw=path.read_bytes();request=json.loads(raw);result=read_and_compare(request)
        result['read_metadata'].update(input_path=str(path),input_sha256=hashlib.sha256(raw).hexdigest())
        text=render_text(result['comparison']) if a.format=='text' else json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    except (OSError,ValueError,KeyError,TypeError) as exc:p.exit(2,'SUPPLEMENT_COMPARISON_READ_FAILED: '+str(exc)+'\n')
    print(text,end='')
    return 0 if result['comparison']['status']=='COMPARABLE' else 2


if __name__=='__main__':raise SystemExit(main())
