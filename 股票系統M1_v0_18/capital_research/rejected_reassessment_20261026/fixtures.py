"""Explicit synthetic specifications. Expected outcomes precede numeric replay."""
from copy import deepcopy
import json
from pathlib import Path
from capital_research.core import decide, resume_decision
from capital_research.execution import simulate
from capital_research.continuity import make_checkpoint
from capital_research.repair_20261025.fixtures import advance, prefix

ROOT = Path(__file__).resolve().parents[1]
CASES = ('restrictive-unfilled', 'restrictive-funded-fill',
         'value-only-rejection', 'valid-review', 'conditional-rejection',
         'future-prefix', 'future-known', 'future-partial')


def specification(name):
    if name not in CASES:
        raise ValueError(name)
    j = json.loads((ROOT/'evidence_conflicts_20261026/after-final/mixed-null-revocation/first-input.json').read_text())
    j['plan_id'] = 'B-full' if name == 'conditional-rejection' else 'E-partial'
    if name == 'conditional-rejection':
        # B99 cannot pay its costs with reserve100. B90 is feasible only after
        # sale settlement, so this control reaches the intended re-review gate.
        next(p for p in j['decision_input']['plans'] if p['id']=='B-full')['targets']['B'] = '90'
    j['orders'] = [dict(id='B-buy', code='B', side='BUY', shares='20',
        limit_price='20.03', decision_at=j['decision_input']['decision_at'],
        submitted_at='2026-01-06T08:00:00+08:00', expires_at='2026-01-12T16:00:00+08:00')]
    # Original opening, cash/share claims, reserve, calendar and prices unchanged.
    for obs in j['tape']:
        obs['capacity_shares'] = '0'  # standing B buy is demonstrably unfilled
    for code, minute in [('A', '00'), ('B', '01')]:
        obs = deepcopy(next(x for x in j['tape'] if x['code'] == code))
        obs.update(at=f'2026-01-09T09:{minute}:00+08:00',
            available_at=f'2026-01-09T09:{minute}:00+08:00',
            settlement_date='2026-01-12',
            capacity_shares='0' if name == 'restrictive-unfilled' else '100')
        j['tape'].append(obs)
    j['observed_until'] = '2026-01-09T16:00:00+08:00'
    future = name.startswith('future-')
    if future:
        j['tape'][-1]['capacity_shares'] = '7' if name=='future-partial' else '0'
        if name!='future-prefix':
            for obs in deepcopy(j['tape'][-2:]):
                obs.update(at=obs['at'].replace('01-09','01-12'),
                    available_at=obs['available_at'].replace('01-09','01-12'),
                    capacity_shares='100')
                j['tape'].append(obs)
            j['observed_until']='2026-01-12T16:00:00+08:00'
    restrictive = name.startswith('restrictive-') or name == 'conditional-rejection'
    expected = dict(restrictive=restrictive, review_feasible=name == 'valid-review',
        rejected_attempt_retained=name != 'valid-review',
        standing_B_fill_shares='0' if restrictive or name in ('future-prefix','future-known') else '7' if name=='future-partial' else '20',
        restored_B_qualified=False if name == 'restrictive-unfilled' else None,
        preserve_original_capital='2180', preserve_general_reserve='100')
    return dict(schema='rejected-reassessment-specification/0.1', name=name,
        synthetic=True, first_input=j, edit=dict(rewrite_value=name != 'valid-review',
            earlier_expiry='2026-01-10T16:00:00+08:00' if restrictive else None,
            future_invalidation='2026-01-12T09:01:00+08:00' if future else None),
        expected=expected)


def materialize(spec, record=lambda name, value: None):
    j = deepcopy(spec['first_input'])
    initial = decide(j['decision_input'])
    first = prefix(j)
    record('prefix-input', first)
    prior = simulate(first)
    record('prefix-actual', prior)
    cp = make_checkpoint(j['ledger_input'], prior, through_at=first['observed_until'])
    record('checkpoint-before-review', cp)
    fresh, ids = advance(j['decision_input'], cp)
    fact = fresh['assets']['B']['evidence'][0]
    if spec['edit'].get('independent_C_token'):
        c=fresh['assets']['C'];new=deepcopy(c['evidence'][0])
        new.update(id='C-observed-new',event_id='C-observed-new',formation_id='C-observed-formation',
            volume_bar_id='C-observed-bar',value='INDEPENDENT_KNOWN_C_REPAIR',
            occurred_at=fresh['data_cutoff'],available_at=fresh['data_cutoff'])
        new['validity'].update(available_at=fresh['data_cutoff'],valid_from=fresh['data_cutoff'])
        c['evidence'].append(new);c['capital_eligibility']['evidence_ids'].append(new['id'])
    if spec['edit']['rewrite_value']:
        fact['value'] = 'EXPLICIT_REJECTED_REWRITE_NOT_A_SOURCE_CORRECTION'
    if spec['edit']['earlier_expiry']:
        fact['validity']['valid_until'] = spec['edit']['earlier_expiry']
    if spec['edit'].get('future_invalidation'):
        fact['validity']['invalidation']=dict(evidence_id='B-future-revocation',
            occurred_at=spec['edit']['future_invalidation'],
            available_at=spec['edit']['future_invalidation'],source_ids=['fixture'])
    record('review-input', fresh)
    proposed = resume_decision(initial, fresh, checkpoint=cp, cancelled_order_ids=ids)
    record('review-actual', proposed)
    j['reassessments'] = [dict(id='inflight-review', order_id='B-buy',
        decision_input=fresh, decision_id=proposed['decision']['decision_id'],
        plan_id=j['plan_id'], checkpoint_id=cp['checkpoint_id'], cancelled_order_ids=ids)]
    record('input', j)
    actual = simulate(j)
    record('execution-actual', actual)
    result = dict(initial=initial, proposed=proposed, execution=actual, plan_id=j['plan_id'])
    if spec['name'] == 'restrictive-unfilled':
        cp2 = make_checkpoint(j['ledger_input'], actual, through_at=j['observed_until'])
        record('checkpoint-after-review', cp2)
        restored, ids2 = advance(j['decision_input'], cp2)
        # advance preserves the exact original B-event bytes; only marks/review advance.
        previous = dict(decision=actual['decision_records'][actual['latest_decision_id']])
        record('restore-input', dict(previous=previous, decision_input=restored,
            checkpoint=cp2, cancelled_order_ids=ids2))
        result['restored'] = resume_decision(previous, restored, checkpoint=cp2,
            cancelled_order_ids=ids2)
        record('restore-actual', result['restored'])
    return result


def observed(result):
    e = result['execution']; p = result['proposed']['decision']
    return dict(review_feasible=next(x['feasible'] for x in p['layer3']['alternatives'] if x['id']==result['plan_id']),
        review_B_qualified=p['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'],
        review_restriction_conflicts=p['fact_history']['restriction_conflicts'],
        B_fill_shares=str(sum(int(f['shares']) for f in e['fills'] if f['code']=='B' and f['side']=='BUY')),
        order_state=e['order_states']['B-buy'],
        retained_attempts=e.get('reassessment_attempts', []),
        restored_B_qualified=result.get('restored',{}).get('decision',{}).get('layer2',{}).get('B',{}).get('capital_eligibility',{}).get('qualified_for_synthetic_proposal'),
        restored_candidate_ids=result.get('restored',{}).get('decision',{}).get('research_recommendation',{}).get('candidate_ids'))
