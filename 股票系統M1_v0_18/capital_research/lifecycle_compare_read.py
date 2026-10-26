"""Explicit stdout-only comparison of saved files; no numerical RUN path."""
import argparse
import hashlib
import json
from pathlib import Path
from .lifecycle_compare import compare_saved, render_comparison, INPUT, MAX_ITEMS


def main():
    parser=argparse.ArgumentParser(description='已保存生命週期摘要唯讀並列')
    parser.add_argument('items',nargs='+',metavar='標籤=路徑');parser.add_argument('--format',choices=('text','json'),default='text')
    args=parser.parse_args()
    if not 2<=len(args.items)<=MAX_ITEMS:parser.exit(2,'READ_REFUSED: COMPARISON_RESOURCE_LIMIT_EXCEEDED\n')
    items=[];metadata=[]
    try:
        for spec in args.items:
            label,path=spec.split('=',1);raw=Path(path).read_bytes()
            items.append(dict(label=label,saved_result=json.loads(raw)))
            metadata.append(dict(label=label,path=path,sha256=hashlib.sha256(raw).hexdigest()))
        result=compare_saved(dict(schema=INPUT,synthetic=True,items=items))
    except (ValueError,OSError) as exc:parser.exit(2,'READ_FAILED: '+str(exc)+'\n')
    if args.format=='json':print(json.dumps(dict(comparison=result,read_metadata=metadata),ensure_ascii=False,indent=2))
    else:print(render_comparison(result),end='')
    return 0 if result['comparable'] else 2


if __name__=='__main__':raise SystemExit(main())
