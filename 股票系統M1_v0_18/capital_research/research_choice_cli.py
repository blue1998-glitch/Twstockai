"""Explicit SELECT or READ. Neither operation computes a generation or trade."""
import argparse
import json
from pathlib import Path
from .research_choice_workflow import select_and_save, read_choice


def main():
    parser = argparse.ArgumentParser(description='保存明示研究選擇；不重算、不下單')
    parser.add_argument('operation', choices=('SELECT', 'READ'))
    parser.add_argument('--store', required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--input')
    args = parser.parse_args()
    try:
        if args.operation == 'READ':
            if args.input:
                parser.error('READ does not accept --input')
            result = read_choice(args.store, args.id)
        else:
            if not args.input:
                parser.error('SELECT requires explicit --input')
            request = json.loads(Path(args.input).read_text())
            result = select_and_save(args.store, args.id, request)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, 'CHOICE_IO_FAILED: ' + str(exc) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result['record'] is None:
        return 2
    return 2 if result['record']['value']['choice']['status'] == 'REFUSED' else 0


if __name__ == '__main__':
    raise SystemExit(main())
