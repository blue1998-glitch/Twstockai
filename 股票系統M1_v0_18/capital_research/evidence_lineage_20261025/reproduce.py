"""Save exact inputs and fixed oracles before evaluating each continuation."""
import argparse
import hashlib
import json
from pathlib import Path
from copy import deepcopy
from capital_research.core import decide, VERSION as DECISION_VERSION
from capital_research.execution import simulate, VERSION as EXECUTION_VERSION
from capital_research.continuity import CHECKPOINT
from .fixtures import BASELINE, ROOT, EXPECTED, first_input, pair


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')


def attempt(call):
    try: return dict(value=call(), error=None)
    except (ValueError, KeyError) as e: return dict(value=None, error=type(e).__name__ + ': ' + str(e))


def capture(output):
    out = Path(output)
    sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(ROOT.glob('*.py'))}
    sources.update({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(Path(__file__).parent.glob('*.py'))})
    save(out/'source-versions.json', dict(baseline=BASELINE, decision=DECISION_VERSION,
        execution=EXECUTION_VERSION, checkpoint=CHECKPOINT, sources=sources, synthetic=True))
    for name, expected in EXPECTED.items():
        first = first_input(name)
        save(out/name/'first-input.json', first)
        save(out/name/'expected.json', dict(expected=expected, synthetic=True))
    summary = {}
    for name in EXPECTED:
        first = json.loads((out/name/'first-input.json').read_text())
        built = pair(name, first)
        save(out/name/'input.json', built)
        nxt = built['next']; continuation = nxt['continuation']
        resumed = attempt(lambda: __import__('capital_research.core', fromlist=['resume_decision']).resume_decision(
            continuation['previous_decision'], nxt['decision_input'], checkpoint=continuation['checkpoint'],
            cancelled_order_ids=continuation['cancelled_order_ids']))
        execution = attempt(lambda: simulate(nxt))
        prefix_equal = None
        if name.startswith('future-'):
            plain = deepcopy(first['decision_input']); plain['assets']['B']['evidence'][0]['validity']['invalidation'] = None
            prefix_equal = decide(plain)['decision'] == built['first_decision']['decision']
        actual = dict(resumed=resumed, execution=execution, prefix_equal=prefix_equal)
        save(out/name/'actual.json', actual)
        d = resumed['value']['decision'] if resumed['value'] else None
        r = execution['value']
        row = dict(error=resumed['error'] or execution['error'], prefix_equal=prefix_equal,
                   B_qualified=d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'] if d else None,
                   new_B_fills=[f['shares'] for f in r['fills'] if f['code']=='B' and f['side']=='BUY' and f['id'] in r.get('new_fill_ids',[])] if r else [],
                   status=r['status'] if r else None,
                   B_order_status=r.get('order_states',{}).get('next-B-buy',{}).get('status') if r else None)
        summary[name] = row; print(name, json.dumps(row))
    save(out/'summary.json', summary)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', required=True)
    capture(p.parse_args().output)
