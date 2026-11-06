"""Synthetic cross-round fact cases; original v0.4 artifacts stay read-only."""
from copy import deepcopy
import json
from pathlib import Path
from graph_core.core import fingerprint
from capital_research.core import decide
from capital_research.execution import simulate
from capital_research.continuity import make_checkpoint
from capital_research.repair_20261025.fixtures import advance, continuation_job

BASELINE = '4339a146d22dd849a6131a8c13f08f2e56145a2f'
ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'drop-known-revocation': 'REJECT_NEW_B_CAPITAL',
    'extend-expiry-to-null': 'REJECT_NEW_B_CAPITAL',
    'extend-expiry-later': 'REJECT_NEW_B_CAPITAL',
    'alias-drop-revocation': 'REJECT_NEW_B_CAPITAL',
    'rename-keep-revocation': 'REJECT_NEW_B_CAPITAL',
    'valid-old-fact': 'ACCEPT_B20_WITHOUT_NEW_EVENT',
    'independent-new-fact': 'ACCEPT_B20_KEEP_OLD_INVALID_FACT',
    'future-revocation': 'SAME_PREFIX_THEN_CANCEL_B_AT_KNOWN_TIME',
    'future-stripped-at-review': 'SAME_PREFIX_THEN_CANCEL_B_FROM_PRIOR_SOURCE',
}


def first_input(name):
    path = ROOT / 'repair_ab_20261025/after/A-own-evidence/input.json'
    job = deepcopy(json.loads(path.read_text()))
    job.update(plan_id='A-zero', orders=[])
    fact = job['decision_input']['assets']['B']['evidence'][0]
    if name.startswith('extend-expiry'):
        fact['validity'].update(valid_until='2026-01-07T16:00:00+08:00',
                                qualification='EXPLICIT_SYNTHETIC_INTERVAL')
    elif name not in ('valid-old-fact',):
        future = name.startswith('future-')
        fact['validity']['invalidation'] = dict(evidence_id='B-revocation-1',
            occurred_at='2026-01-09T09:00:00+08:00' if future else '2026-01-05T14:00:00+08:00',
            available_at='2026-01-09T09:01:00+08:00' if future else '2026-01-05T14:00:00+08:00',
            source_ids=['fixture'])
    return job


def pair(name, first):
    d = first['decision_input']; old = decide(d); execution = simulate(first)
    cp = make_checkpoint(first['ledger_input'], execution, through_at=first['observed_until'])
    fresh, ids = advance(d, cp, at='2026-01-08T17:00:00+08:00')
    asset = fresh['assets']['B']; fact = asset['evidence'][0]
    if name in ('drop-known-revocation', 'alias-drop-revocation', 'future-stripped-at-review'):
        fact['validity']['invalidation'] = None
    if name == 'extend-expiry-to-null':
        fact['validity'].update(valid_until=None, qualification='EXPLICIT_SYNTHETIC_ONGOING_REQUIRES_REVIEW')
    if name == 'extend-expiry-later':
        fact['validity']['valid_until'] = '2026-01-12T16:00:00+08:00'
    if name in ('alias-drop-revocation', 'rename-keep-revocation'):
        fact['id'] = 'B-renamed'
        if name == 'alias-drop-revocation':
            fact['fact_link'] = dict(schema='capital-fact-alias/0.1', code='B',
                source_id=asset['source_id'], basis_id=asset['basis_id'], adjustment_version=asset['adjustment_version'],
                target_id='B-event', target_content_id=fingerprint(d['assets']['B']['evidence'][0]),
                available_at=fresh['data_cutoff'], source_ids=['fixture'])
    if name == 'independent-new-fact':
        new = deepcopy(fact)
        new.update(id='B-independent', event_id='B-independent', formation_id='B-independent',
                   volume_bar_id='B-independent', occurred_at=fresh['data_cutoff'], available_at=fresh['data_cutoff'])
        new['validity'].update(invalidation=None, valid_from=fresh['data_cutoff'], available_at=fresh['data_cutoff'])
        asset['evidence'].append(new)
        asset['capital_eligibility']['evidence_ids'] = [new['id']]
    else:
        asset['capital_eligibility']['evidence_ids'] = [fact['id']]
    next_job = continuation_job(first, execution, old, plan='E-partial', fresh=fresh, ids=ids)
    return dict(first=first, first_decision=old, first_execution=execution, checkpoint=cp, next=next_job)
