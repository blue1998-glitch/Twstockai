"""Only this milestone's explicit new synthetic retry requests; exclusive IO."""
import json
from pathlib import Path
import sys
import traceback

from capital_research.conditional_retry import retry_rejected
from .verify import verify

ROOT = Path(__file__).parent


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
        request = json.loads((case / 'input.json').read_text())
        expected = json.loads((case / 'expected.json').read_text())
        try:
            actual = retry_rejected(request)
            save(folder / case.name / 'actual.json', actual)
            results[case.name] = actual
            verify(request, expected, actual)
            reference = expected.get('same_decision_as')
            if reference:
                # Compare cutoff decisions, never later fills or integrity IDs.
                source = results.get(reference)
                if source is None:
                    source_request = json.loads((ROOT / 'cases' / reference / 'input.json').read_text())
                    # Reuse the frozen reference after all cases, without rerunning.
                    rows.append(dict(case=case.name, status='PENDING', reference=reference))
                    print(case.name, 'PENDING_PREFIX_CHECK', flush=True)
                    continue
                assert actual['review']['review_decision'] == source['review']['review_decision']
            rows.append(dict(case=case.name, status='PASS', error=None))
            print(case.name, 'PASS', flush=True)
        except Exception:
            error = traceback.format_exc()
            rows.append(dict(case=case.name, status='FAIL', error=error))
            print(case.name, 'FAIL', error, flush=True)
    for row in rows:
        if row['status'] == 'PENDING':
            try:
                assert results[row['case']]['review']['review_decision'] == results[row['reference']]['review']['review_decision']
                row.update(status='PASS', error=None)
            except Exception:
                row.update(status='FAIL', error=traceback.format_exc())
    save(folder / 'summary.json', rows)
    if any(r['status'] != 'PASS' for r in rows):
        raise SystemExit(1)


if __name__ == '__main__':
    main(sys.argv[1])
