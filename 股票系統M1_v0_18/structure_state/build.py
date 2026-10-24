"""Explicit file IO coordinator; pure P0-3 logic is in core.evaluate."""
import argparse
import json
from pathlib import Path
from product_candidate.build import publish_immutable
from .source import prepare
from .core import evaluate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', required=True)
    parser.add_argument('--selection', required=True)
    parser.add_argument('--as-of', required=True)
    parser.add_argument('--output', required=True)
    a = parser.parse_args()
    payload, scenario = prepare(json.loads(Path(a.data).read_text()),
                                json.loads(Path(a.selection).read_text()))
    result = evaluate(payload, scenario, as_of=a.as_of)
    raw = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    print(publish_immutable(Path(a.output), raw), len(raw), result['result_id'])


if __name__ == '__main__':
    main()
