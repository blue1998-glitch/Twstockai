"""Minimal A/B counterexamples cloned from the fixed v0.3 synthetic record."""
from copy import deepcopy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '34b5dfa22b77cfe5c85a818e156389d5d0f9a444'
EXPECTED = {
    'A-foreign-ABC': 'REJECT_B_NEW_CAPITAL: A evidence cannot qualify B',
    'A-foreign-BAC': 'REJECT_B_NEW_CAPITAL: asset object order cannot change qualification',
    'A-own-evidence': 'ACCEPT: B own evidence permits this synthetic partial buy',
    'B-delayed-cancel': 'REFUSE_ACTIVE_ORDER_GAP: old orders could execute before cancellation',
    'B-delayed-omitted-tape': 'REFUSE_ACTIVE_ORDER_GAP: omitted observations do not prove no fills',
    'B-same-close-review': 'ACCEPT: explicit review before the next declared trading day',
    'B-already-expired': 'ACCEPT: expired orders do not create an active-order gap',
}


def saved_pair(expired=False):
    name = 'partial-expiry-chain' if expired else 'partial-cancel-chain'
    path = ROOT / 'repair_20261025/artifacts/after' / (name + '.json')
    return deepcopy(json.loads(path.read_text())['value']['input'])


def rebind(pair):
    """Mint this engine's lineage from the SAME opening, fills and market prefix.

    This is a new directed synthetic execution, never migration of a saved result.
    Account values, original ledger and economic intent are left untouched.
    """
    from capital_research.core import decide
    from capital_research.execution import simulate
    from capital_research.continuity import make_checkpoint
    first = pair['first']
    result = simulate(first)
    cp = make_checkpoint(first['ledger_input'], result, through_at=first['observed_until'])
    old = pair['next']['continuation']['checkpoint']['state']
    for key in ('row', 'accepted_fills', 'origin_initial_capital', 'general_reserved_cash'):
        if cp['state'][key] != old[key]:
            raise ValueError('Version rebind changed economic prefix: ' + key)
    pair['next']['continuation'].update(
        checkpoint=cp, previous_decision=decide(first['decision_input']))
    return pair


def delayed(job):
    job = deepcopy(job)
    at = '2026-01-09T10:00:00+08:00'
    job['decision_input']['decision_at'] = at
    job['decision_input']['account']['available_at'] = at
    for order in job['orders']:
        order.update(decision_at=at, submitted_at='2026-01-09T10:01:00+08:00')
    # Retain the 09:00/09:01 observations BEFORE cancellation. New orders can
    # execute only on Jan12, consistent with the existing prior-day ledger rule.
    later = deepcopy(job['tape'])
    for obs in later:
        obs['at'] = obs['at'].replace('2026-01-09', '2026-01-12')
        obs['available_at'] = obs['at']
    job['tape'] += later
    return job


def cases(*, current_lineage=False):
    pair = saved_pair()
    expired = saved_pair(True)
    if current_lineage:
        pair = rebind(pair)
        expired = rebind(expired)
    foreign = deepcopy(pair['first'])
    foreign['decision_input']['assets']['B']['evidence'] = []
    foreign['decision_input']['assets']['B']['capital_eligibility']['evidence_ids'] = ['A-event']
    reordered = deepcopy(foreign)
    assets = reordered['decision_input']['assets']
    reordered['decision_input']['assets'] = {c: assets[c] for c in ('B', 'A', 'C')}
    late = delayed(pair['next'])
    omitted = deepcopy(late)
    omitted['tape'] = [o for o in omitted['tape'] if o['at'][:10] == '2026-01-12']
    expired_late = delayed(expired['next'])
    expired_late['tape'] = [o for o in expired_late['tape'] if o['at'][:10] == '2026-01-12']
    return {
        'A-foreign-ABC': foreign, 'A-foreign-BAC': reordered,
        'A-own-evidence': deepcopy(pair['first']),
        'B-delayed-cancel': late, 'B-delayed-omitted-tape': omitted,
        'B-same-close-review': deepcopy(pair['next']),
        'B-already-expired': expired_late,
    }
