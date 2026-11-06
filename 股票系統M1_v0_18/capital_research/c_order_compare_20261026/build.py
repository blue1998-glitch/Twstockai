"""Save new READ projections only; exclusive output, never replay old jobs."""
import json
from pathlib import Path
import sys
import traceback

from capital_research.lifecycle_compare import compare_saved, render_comparison
from .fixtures import ROOT, load, load_request
from .verify import verify


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for case in sorted((ROOT / 'cases').iterdir()):
        folder = output / case.name
        folder.mkdir()
        request = load_request(case.name)
        expected = load(case / 'expected.json')
        result = compare_saved(request)
        save(folder / 'actual.json', result)
        with (folder / 'readable.txt').open('x') as stream:
            stream.write(render_comparison(result))
        try:
            verify(expected, result)
            status, error = 'PASS', None
        except Exception:
            status, error = 'FAIL', traceback.format_exc()
        rows.append(dict(case=case.name, status=status, error=error))
        print(case.name, status, flush=True)
    save(output / 'summary.json', rows)
    if any(r['status'] != 'PASS' for r in rows):
        raise SystemExit(1)


if __name__ == '__main__':
    main(sys.argv[1])
