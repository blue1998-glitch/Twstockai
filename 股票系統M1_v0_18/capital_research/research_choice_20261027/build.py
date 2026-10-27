"""New selection records only; exclusive evidence writes outside pure code."""
import json
from pathlib import Path
import sys
import traceback
from capital_research.research_choice import choose_saved
from .fixtures import ROOT, load, materialize, fp
from .verify import verify


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main(stage):
    output = ROOT / stage
    output.mkdir(exist_ok=False)
    rows = []
    for folder in sorted((ROOT / 'cases').iterdir()):
        spec = load(folder / 'input.json'); request = materialize(spec)
        assert fp(request) == spec['materialized_input_id']
        actual = choose_saved(request)
        save(output / folder.name / 'actual.json', actual)
        try:
            verify(request, load(folder / 'expected.json'), actual)
            status, error = 'PASS', None
        except Exception:
            status, error = 'FAIL', traceback.format_exc()
        rows.append(dict(case=folder.name, status=status, error=error))
        print(folder.name, status, flush=True)
        if error:
            print(error, flush=True)
    save(output / 'summary.json', rows)
    if any(v['status'] != 'PASS' for v in rows):
        raise SystemExit(1)


if __name__ == '__main__':
    main(sys.argv[1])
