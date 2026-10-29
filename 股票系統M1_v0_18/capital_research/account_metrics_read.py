"""Explicit file IO outside the pure evaluator; stdout only, no replay."""
import argparse
import hashlib
import json
from pathlib import Path
from .account_metrics import INPUT,evaluate_saved,render_text


def main():
    p=argparse.ArgumentParser(description='評估完整保存合成帳務，不重播、不排名')
    p.add_argument('--source',required=True);p.add_argument('--evaluation-at',required=True)
    p.add_argument('--source-kind',choices=('quantity','action'),default='quantity')
    p.add_argument('--format',choices=('text','json'),default='text');a=p.parse_args()
    try:
        raw=Path(a.source).read_bytes();saved=json.loads(raw)
        evaluator=evaluate_saved;schema=INPUT
        if a.source_kind=='action':
            from .action_account_metrics import evaluate_saved as evaluator, INPUT as schema
        result=evaluator(dict(schema=schema,synthetic=True,evaluation_at=a.evaluation_at,saved_result=saved))
        envelope=dict(evaluation=result,read_metadata=dict(source_path=a.source,source_sha256=hashlib.sha256(raw).hexdigest()))
        print(render_text(result) if a.format=='text' else json.dumps(envelope,ensure_ascii=False,indent=2)+'\n',end='')
        return 0 if result['status']=='EVALUATED' else 2
    except (OSError,ValueError,TypeError) as exc:p.exit(2,'ACCOUNT_METRICS_READ_FAILED: '+str(exc)+'\n')


if __name__=='__main__':raise SystemExit(main())
