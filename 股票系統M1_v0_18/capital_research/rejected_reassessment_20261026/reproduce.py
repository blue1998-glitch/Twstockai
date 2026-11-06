"""Create-only artifacts: input/oracle/source hashes before each actual call."""
import argparse
import hashlib
import json
from pathlib import Path
from capital_research.core import VERSION as DECISION
from capital_research.execution import VERSION as EXECUTION
from capital_research.continuity import CHECKPOINT
from .fixtures import ROOT, CASES, specification, materialize, observed


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def capture(out):
    out = Path(out)
    sources = list(ROOT.glob('*.py')) + list(Path(__file__).parent.glob('*.py'))
    save(out/'source-versions.json', dict(decision=DECISION, execution=EXECUTION,
        checkpoint=CHECKPOINT, sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(sources)}, synthetic=True))
    specs = {name:specification(name) for name in CASES}
    for name, spec in specs.items():
        save(out/name/'specification.json', spec)
        save(out/name/'first-input.json', spec['first_input'])
        save(out/name/'expected.json', spec['expected'])
    summary = {}
    for name, spec in specs.items():
        try:
            actual = materialize(spec, record=lambda tag, x:save(out/name/(tag+'.json'), x))
            summary[name] = observed(actual)
        except Exception as exc:
            save(out/name/'diagnostic.json', dict(type=type(exc).__name__, message=str(exc)))
            raise
        print(name, json.dumps({k:v for k,v in summary[name].items()
            if k not in ('review_restriction_conflicts','retained_attempts','order_state')}))
    save(out/'summary.json', summary)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    capture(parser.parse_args().output)
