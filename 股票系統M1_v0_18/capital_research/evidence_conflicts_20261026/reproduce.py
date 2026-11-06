"""Create-only evidence writer; fixed expected inputs precede all replay calls."""
import argparse
import hashlib
import json
from pathlib import Path
from capital_research.core import VERSION as DECISION
from capital_research.execution import VERSION as EXECUTION
from capital_research.continuity import CHECKPOINT
from capital_research.fact_lineage import SCHEMA as HISTORY
from .fixtures import ROOT, CASES, specification, materialize, observed


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def capture(output):
    out = Path(output)
    sources = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(ROOT.glob('*.py'))}
    sources.update({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(Path(__file__).parent.glob('*.py'))})
    save(out/'source-versions.json', dict(decision=DECISION, execution=EXECUTION,
        checkpoint=CHECKPOINT, history=HISTORY, sources=sources, synthetic=True))
    specs = {name:specification(name) for name in CASES}
    for name, spec in specs.items():
        save(out/name/'specification.json', spec)
        save(out/name/'first-input.json', spec['first_input'])
        save(out/name/'expected.json', spec['expected'])
    summary = {}
    for name, spec in specs.items():
        result = materialize(spec, record=lambda tag, value:save(out/name/(tag+'.json'), value))
        actual = dict(resumed=result['resumed'], execution=result['execution'],
            checkpoint_states=[c['state'] for c in result['checkpoints']])
        save(out/name/'actual.json', actual)
        summary[name] = observed(result)
        print(name, json.dumps(summary[name]))
    save(out/'summary.json', summary)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    capture(parser.parse_args().output)
