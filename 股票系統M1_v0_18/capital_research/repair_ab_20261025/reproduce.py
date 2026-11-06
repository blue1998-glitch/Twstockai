"""Create-only input/expectation first, then actual A/B results; no old outputs."""
import argparse
import hashlib
import json
from pathlib import Path
from capital_research.core import decide, VERSION as DECISION_VERSION
from capital_research.execution import simulate, VERSION as EXECUTION_VERSION
from capital_research.continuity import CHECKPOINT
from .fixtures import BASELINE, EXPECTED, ROOT, cases


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def capture(output, *, current_lineage=False):
    directory = Path(output)
    inputs = cases(current_lineage=current_lineage)
    sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(ROOT.glob('*.py'))}
    sources.update({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(Path(__file__).parent.glob('*.py'))})
    save(directory / 'source-versions.json', dict(
        baseline=BASELINE, decision=DECISION_VERSION, execution=EXECUTION_VERSION,
        checkpoint=CHECKPOINT, sources=sources, synthetic=True,
        current_lineage_reminted=current_lineage))
    # Preserve every exact input and oracle before evaluating any case.
    for name, job in inputs.items():
        save(directory / name / 'input.json', job)
        save(directory / name / 'expected.json', dict(expected=EXPECTED[name], synthetic=True))
    summary = {}
    for name, job in inputs.items():
        actual = dict(decision=None, execution=None, error=None)
        try:
            if not job.get('continuation'):
                actual['decision'] = decide(job['decision_input'])
            actual['execution'] = simulate(job)
        except (ValueError, KeyError) as e:
            actual['error'] = type(e).__name__ + ': ' + str(e)
        save(directory / name / 'actual.json', actual)
        e = actual['execution']
        row = dict(error=actual['error'], status=e['status'] if e else None,
                   new_fills=[dict(code=f['code'], side=f['side'], shares=f['shares'], date=f['date'])
                              for f in e['fills'] if f['id'] in e['new_fill_ids']] if e else [])
        if actual['decision']:
            d = actual['decision']['decision']
            row.update(B_qualified=d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'],
                       recommendations=d['research_recommendation']['candidate_ids'])
        summary[name] = row
        print(name, json.dumps(row, ensure_ascii=False))
    save(directory / 'summary.json', summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--current-lineage', action='store_true')
    args = parser.parse_args()
    capture(args.output, current_lineage=args.current_lineage)
