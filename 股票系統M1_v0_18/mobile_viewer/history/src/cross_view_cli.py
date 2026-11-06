"""Read-only catalog/explicit selection/HTML export. No calculation operation."""
import argparse
import json
import sys
from pathlib import Path
from contracts import DataError
from period_store import StoreFailure
from period_store_contracts import pairs
from store_contracts import canonical
from cross_view import catalog, select, validate_config
from cross_view_export import export, protect, write_text


def read_config(path):
    path=Path(path);c=json.loads(path.read_text(encoding='utf-8-sig'),object_pairs_hook=pairs)
    validate_config(c)
    for key in ('daily_stores','period_stores'):
        c[key]={alias:str((path.parent/p).resolve()) for alias,p in c[key].items()}
    return c


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    group=p.add_mutually_exclusive_group();group.add_argument('--html',action='store_true');group.add_argument('--selection')
    a=p.parse_args(argv)
    try:
        config=read_config(a.config);inputs=[a.config]+([a.selection] if a.selection else [])
        if a.html:receipt=export(config,a.output,inputs)
        else:
            protect(config,a.output,inputs);payload=catalog(config)
            if a.selection:payload=select(payload,json.loads(Path(a.selection).read_text(encoding='utf-8-sig'),object_pairs_hook=pairs))
            write_text(a.output,canonical(payload)+'\n');receipt=dict(status='OUTPUT_WRITTEN',schema_version=payload['schema_version'],database_access='READ_ONLY_NO_RECOVERY')
        print(json.dumps(receipt,ensure_ascii=False));return 0
    except (DataError,StoreFailure,OSError,ValueError,UnicodeError) as e:
        error=e.as_dict() if isinstance(e,(DataError,StoreFailure)) else dict(status='VIEW_ERROR',detail=type(e).__name__)
        error.update(database_access='READ_ONLY_NO_RECOVERY',action_qualification='NOT_EVALUATED')
        print(json.dumps(error,ensure_ascii=False),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
