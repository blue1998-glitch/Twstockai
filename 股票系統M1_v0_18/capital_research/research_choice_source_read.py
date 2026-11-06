"""Explicit two-original READ entry. Stdout only; no SELECT or RUN route."""
import argparse
import hashlib
import json
from pathlib import Path
from .research_choice_workflow import read_choice
from .research_choice_source import check_saved
from .research_choice_source_view import render_text


def main():
    parser = argparse.ArgumentParser(description='只讀核對研究選擇與明示完整來源，不重選')
    parser.add_argument('--store', required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--format', choices=('text','json'), default='text')
    args = parser.parse_args()
    try:
        record = read_choice(args.store, args.id)['record']
        path = Path(args.source); raw = path.read_bytes(); source = json.loads(raw)
        result = check_saved(record['value'], source)
        if args.format == 'text':
            text = render_text(result)
        else:
            text = json.dumps(dict(result=result, read_metadata=dict(source_path=str(path),
                source_bytes=len(raw), source_sha256=hashlib.sha256(raw).hexdigest(),
                record_id=record['id'])), ensure_ascii=False, indent=2) + '\n'
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, 'CHOICE_SOURCE_READ_FAILED: ' + str(exc) + '\n')
    print(text, end='')
    return 0 if result['check_status'] == 'MATCHED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
