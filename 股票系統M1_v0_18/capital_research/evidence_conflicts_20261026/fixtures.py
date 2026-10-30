"""Explicit synthetic three-round inputs; no new market prices or calendar."""
from copy import deepcopy
import json
from pathlib import Path
from graph_core.core import fingerprint
from capital_research.core import resume_decision
from capital_research.execution import simulate
from capital_research.continuity import make_checkpoint
from capital_research.repair_20261025.fixtures import advance, continuation_job

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    'mixed-null-revocation', 'mixed-later-revocation',
    'rejected-value-revocation', 'rejected-value-earlier-expiry',
    'alias-after-conflict', 'independent-new-fact',
    'restore-valid-original', 'restore-after-extension-only',
    'future-revocation', 'late-revocation', 'equal-expiry-revocation',
    'future-no-tape',
)


def specification(name):
    if name not in CASES:
        raise ValueError('Unknown directed case')
    first = json.loads((ROOT/'evidence_lineage_20261025/after-final/valid-old-fact/first-input.json').read_text())
    first.update(plan_id='A-zero', orders=[])
    fact = first['decision_input']['assets']['B']['evidence'][0]
    fact['validity'].update(valid_until='2026-01-20T16:00:00+08:00',
                            qualification='EXPLICIT_SYNTHETIC_INTERVAL', invalidation=None)
    early = name in ('future-revocation', 'late-revocation', 'equal-expiry-revocation', 'future-no-tape')
    if early:
        first['observed_until'] = '2026-01-06T16:00:00+08:00'
    second = deepcopy(fact)
    if name in ('rejected-value-revocation', 'rejected-value-earlier-expiry', 'restore-valid-original'):
        second['value'] = 'EXPLICIT_REJECTED_REWRITE'
    else:
        second['validity'].update(valid_until=None, qualification='EXPLICIT_SYNTHETIC_ONGOING_REQUIRES_REVIEW')
    if name == 'mixed-later-revocation':
        second['validity'].update(valid_until='2026-01-21T16:00:00+08:00', qualification='EXPLICIT_SYNTHETIC_INTERVAL')
    if name == 'rejected-value-earlier-expiry':
        second['validity']['valid_until'] = '2026-01-07T16:00:00+08:00'
    elif name not in ('restore-valid-original', 'restore-after-extension-only'):
        second['validity']['invalidation'] = dict(evidence_id='B-revocation-mixed', source_ids=['fixture'],
            occurred_at='2026-01-09T09:00:00+08:00' if early else '2026-01-08T16:00:00+08:00',
            available_at=('2026-01-09T09:02:00+08:00' if name=='late-revocation' else
                          '2026-01-09T09:01:00+08:00') if early else '2026-01-08T16:00:00+08:00')
    qualified = early or name in ('independent-new-fact','restore-valid-original','restore-after-extension-only')
    order_status = ('FILLED' if name=='late-revocation' else
                    'EXPIRED_UNFILLED' if name=='equal-expiry-revocation' else 'CANCELLED_EVIDENCE') if early else None
    return dict(schema='capital-conflict-case/0.1', name=name, synthetic=True,
        first_input=first, second_fact=second,
        second_at='2026-01-06T17:00:00+08:00' if early else '2026-01-08T17:00:00+08:00',
        second_through='2026-01-08T16:00:00+08:00' if early else '2026-01-12T16:00:00+08:00',
        third_at='2026-01-08T17:00:00+08:00' if early else '2026-01-12T17:00:00+08:00',
        execute_third=early,
        expected=dict(B_qualified=qualified, E_partial_candidate=qualified,
            new_tokens_empty=name!='independent-new-fact',
            B_order_status=order_status, new_B_fill_shares=['20'] if name=='late-revocation' else [],
            qualification='SYNTHETIC_MECHANISM_NOT_MARKET_PERFORMANCE',
            third_execution_evaluated=early))


def materialize(spec, *, record=lambda name, value: None):
    first = deepcopy(spec['first_input']); r1 = simulate(first)
    cp1 = make_checkpoint(first['ledger_input'], r1, through_at=first['observed_until'])
    previous1 = dict(decision=r1['decision_records'][r1['latest_decision_id']])
    d2, ids = advance(first['decision_input'], cp1, at=spec['second_at'])
    d2['assets']['B']['evidence'] = [deepcopy(spec['second_fact'])]
    d2['assets']['B']['capital_eligibility']['evidence_ids'] = [spec['second_fact']['id']]
    second = deepcopy(first)
    second.update(decision_input=d2, observed_until=spec['second_through'], tape=[],
        continuation=dict(previous_decision=previous1, checkpoint=cp1, cancelled_order_ids=ids))
    record('round2-input', second)
    r2 = simulate(second)
    cp2 = make_checkpoint(first['ledger_input'], r2, through_at=second['observed_until'])
    previous2 = dict(decision=r2['decision_records'][r2['latest_decision_id']])
    d3, ids = advance(d2, cp2, at=spec['third_at'])
    asset = d3['assets']['B']; original = deepcopy(first['decision_input']['assets']['B']['evidence'][0])
    asset['evidence'] = [original]
    if spec['name']=='alias-after-conflict':
        original['id'] = 'B-restored-alias'
        original['fact_link'] = dict(schema='capital-fact-alias/0.1', code='B',
            **{k:asset[k] for k in ('source_id','basis_id','adjustment_version')},
            target_id='B-event', target_content_id=fingerprint(first['decision_input']['assets']['B']['evidence'][0]),
            available_at=d3['data_cutoff'], source_ids=['fixture'])
    if spec['name']=='independent-new-fact':
        new = deepcopy(original)
        new.update(id='B-independent-conflict', event_id='B-independent-conflict',
            formation_id='B-independent-conflict', volume_bar_id='B-independent-conflict',
            occurred_at=d3['data_cutoff'], available_at=d3['data_cutoff'])
        new['validity'].update(valid_from=d3['data_cutoff'], available_at=d3['data_cutoff'])
        asset['evidence'].append(new)
        asset['capital_eligibility']['evidence_ids'] = [new['id']]
    else:
        asset['capital_eligibility']['evidence_ids'] = [original['id']]
    concrete = dict(decision_input=d3, previous_decision=previous2, checkpoint=cp2,
                    cancelled_order_ids=ids, proposed_plan_id='E-partial')
    record('input', concrete)
    resumed = resume_decision(previous2, d3, checkpoint=cp2, cancelled_order_ids=ids)
    execution = None
    if spec['execute_third']:
        third = continuation_job(first, r2, previous2, plan='E-partial', fresh=d3, ids=ids)
        if spec['name']=='future-no-tape':
            third['tape'] = []
        if spec['name']=='equal-expiry-revocation':
            next(o for o in third['orders'] if o['side']=='BUY')['expires_at'] = '2026-01-09T09:01:00+08:00'
        record('execution-input', third)
        execution = simulate(third)
    return dict(resumed=resumed, execution=execution, input=concrete,
                first_execution=r1, second_execution=r2, checkpoints=[cp1, cp2])


def observed(result):
    d = result['resumed']['decision']; r = result['execution']
    return dict(B_qualified=d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'],
        E_partial_candidate='E-partial' in d['research_recommendation']['candidate_ids'],
        reasons=d['layer2']['B']['capital_eligibility']['reasons'], new_tokens=d['new_evidence_tokens'],
        B_order_status=r['order_states']['next-B-buy']['status'] if r else None,
        new_B_fill_shares=[f['shares'] for f in r['fills'] if f['side']=='BUY' and f['code']=='B' and f['id'] in r['new_fill_ids']] if r else [],
        third_execution_evaluated=r is not None)
