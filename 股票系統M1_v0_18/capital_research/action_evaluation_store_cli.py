"""Explicit immutable IMPORT or READ; no RUN or automatic source selection."""
import argparse,json
from pathlib import Path
from .action_evaluation_store import import_evaluation,read_evaluation


def main():
    p=argparse.ArgumentParser(description='匯入既有行動評估或純讀回，不重算')
    p.add_argument('operation',choices=('IMPORT','READ'))
    p.add_argument('--root',required=True);p.add_argument('--id',required=True);p.add_argument('--input')
    a=p.parse_args()
    if a.operation=='READ' and a.input:p.error('READ does not accept an input or recalculate')
    if a.operation=='IMPORT' and not a.input:p.error('IMPORT requires a full explicitly pinned input')
    try:
        receipt=read_evaluation(a.root,a.id) if a.operation=='READ' else import_evaluation(a.root,a.id,json.loads(Path(a.input).read_text()))
        print(json.dumps(receipt,ensure_ascii=False,sort_keys=True,allow_nan=False))
        return 0 if receipt['storage_status'] in ('SAVED_AND_READ_BACK','READ_ONLY') else 2
    except (OSError,ValueError,TypeError) as exc:p.exit(2,'ACTION_EVALUATION_STORAGE_FAILED: '+str(exc)+'\n')


if __name__=='__main__':raise SystemExit(main())
