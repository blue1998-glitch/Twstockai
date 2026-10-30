"""Only new candidate RUNs; source reference IO and exclusive evidence writes."""
import json
from pathlib import Path
import sys
import traceback

from capital_research.quantity_after_retry import generate_after_retry
from .fixtures import ROOT, load, materialize, fingerprint
from .verify import verify


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main(stage):
    folder = ROOT / stage
    folder.mkdir(exist_ok=False)
    rows, results = [], {}
    for case in sorted((ROOT / 'cases').iterdir()):
        spec = load(case / 'input.json')
        request = materialize(spec)
        assert fingerprint(request) == spec['materialized_input_id']
        expected = load(case / 'expected.json')
        actual = generate_after_retry(request)
        save(folder / case.name / 'actual.json', actual)
        results[case.name] = actual
        try:
            verify(request, expected, actual)
            status, error = 'PASS', None
        except Exception:
            status, error = 'FAIL', traceback.format_exc()
        rows.append(dict(case=case.name, status=status, error=error))
        print(case.name, status, error or '', flush=True)
    for case in sorted((ROOT / 'cases').iterdir()):
        expected = load(case / 'expected.json')
        if 'same_research_as' in expected:
            a = results[case.name]['adapter']['generation']['research']
            b = results[expected['same_research_as']]['adapter']['generation']['research']
            if a != b:
                next(r for r in rows if r['case'] == case.name).update(status='FAIL', error='Integrity metadata changed numeric research')
    save(folder / 'summary.json', rows)
    if any(r['status'] != 'PASS' for r in rows):
        raise SystemExit(1)


if __name__ == '__main__':
    main(sys.argv[1])
