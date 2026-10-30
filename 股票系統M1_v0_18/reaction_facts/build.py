"""External read-only coordinator; source facts and selectors in, new JSON out."""
import argparse
import json
from pathlib import Path
from product_candidate.build import publish_immutable
from .source import make_input
from .core import evaluate


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', required=True)
    p.add_argument('--selection', required=True)
    p.add_argument('--as-of', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    data = json.loads(Path(a.data).read_text())
    selection = json.loads(Path(a.selection).read_text())
    result = evaluate(make_input(data, selection), as_of=a.as_of)
    raw = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    print(publish_immutable(Path(a.output), raw), len(raw), result['result_id'])


if __name__ == '__main__':
    main()
