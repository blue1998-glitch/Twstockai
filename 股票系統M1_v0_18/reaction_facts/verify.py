"""Read back exact JSON and re-evaluate facts, never the old analysis engines."""
import argparse
import hashlib
import json
from pathlib import Path
from .core import evaluate
from .source import make_input


def verify(data_path, selection_path, result_path):
    data = json.loads(Path(data_path).read_text())
    selection = json.loads(Path(selection_path).read_text())
    result = json.loads(Path(result_path).read_text())
    expected = evaluate(make_input(data, selection), as_of=result['as_of'])
    if result != expected:
        raise ValueError('Serialized facts differ from source-derived observations')
    return dict(status='PASS', result_id=result['result_id'], records=len(result['records']),
                references=len(result['reference_catalog']), transition_records=len(result['transitions']),
                files={str(p):dict(bytes=len(Path(p).read_bytes()), sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
                       for p in (data_path, selection_path, result_path)},
                original_core_recomputed=False, macd_recomputed=False, physical_android='NOT_TESTED_NEW_BUILD',
                browser_tests='NOT_RUN_NO_UI_CHANGED', primary_pressure_id=result['primary_pressure_id'])


def main():
    p = argparse.ArgumentParser()
    for name in ('data', 'selection', 'result'):
        p.add_argument('--' + name, required=True)
    a = p.parse_args()
    print(json.dumps(verify(a.data, a.selection, a.result), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
