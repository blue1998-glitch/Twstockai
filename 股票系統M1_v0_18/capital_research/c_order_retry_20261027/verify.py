"""Check frozen outcomes and original-book links, not strategy performance."""
from decimal import Decimal

FLAGS = ('data_qualified', 'execution_model_qualified', 'historical_signal_eligible',
         'policy_authorized', 'live_execution_authorized')


def verify(request, expected, saved):
    r = saved['review']
    assert r['schema'] == 'capital-conditional-quantity-review/0.3'
    assert r['status'] == expected['status'], (r['status'], r['reasons'])
    assert all(r[k] is False for k in FLAGS) and r['primary_pressure_id'] is None and r['ranking'] is None
    if 'reason' in expected:
        assert expected['reason'] in r['reasons'], r['reasons']
    if not r['status'].startswith('REPLAYED_'):
        return
    e, d, cp = r['execution'], r['review_decision'], r['checkpoint']
    old = request['previous_result']['review']['execution']
    assert e['order_history'] == old['order_history']
    assert e['fills'][:len(old['fills'])] == old['fills']
    assert e['reassessment_attempts'][:len(old['reassessment_attempts'])] == old['reassessment_attempts']
    assert [a['outcome'] for a in e['reassessment_attempts']] == expected['attempts']
    assert set(old['reviewed_evidence_tokens']) <= set(e['reviewed_evidence_tokens'])
    assert e['origin_ledger_input_id'] == old['origin_ledger_input_id']
    assert e['origin_common_account_id'] == old['origin_common_account_id']
    assert d['new_evidence_tokens'] == []
    scope = d['same_order_continuation']
    assert scope['order_id'] == 'r1-B' and scope['remaining'] == '20'
    assert scope['trigger_ids'] == ['B-event']
    assert scope['latest_predecessor_id'] == old['latest_decision_id']
    assert scope['checkpoint_id'] == request['predecessor']['checkpoint_id']
    plan = next(p for p in d['layer3']['alternatives'] if p['id'] == scope['plan_id'])
    assert plan['family'] == 'C' and plan['trigger_ids'] == ['B-event']
    assert scope['original_order_quantity'] == '20'
    fills = [f for f in e['fills'] if f['code'] == 'B' and f['side'] == 'BUY']
    assert str(sum(int(f['shares']) for f in fills)) == expected['B_filled']
    assert len({f['id'] for f in e['fills']}) == len(e['fills'])
    assert all(e['fill_order_ids'][f['id']] == 'r1-B' for f in fills)
    state = e['order_states']['r1-B']
    assert state['remaining'] == expected['remaining'] and state['status'] == expected['order_status']
    assert int(state['remaining']) + int(expected['B_filled']) == 20
    assert cp['state']['origin_initial_capital'] == '1430'
    assert cp['state']['general_reserved_cash'] == '100' and cp['state']['external_flow'] == '0'
    assert cp['state']['accepted_fills'] == e['fills']
    assert cp['state']['reviewed_evidence_tokens'] == e['reviewed_evidence_tokens']
    row = cp['state']['row']
    assert row['cash_claims'] == [] and row['share_receivables'] == []
    assert row['shares']['A'] == '60' and row['shares']['C'] == '2'
    assert row['shares']['B'] == str(5 + int(expected['B_filled']))
    assert Decimal(row['purchase_payable']) == 0 and Decimal(state['reserved_cash']) == 0
    if 'settled_cash' in expected:
        assert Decimal(row['settled_cash']) == Decimal(expected['settled_cash'])
    if 'shares' in expected:
        assert row['shares'] == expected['shares']
    if expected.get('restriction_conflict'):
        assert cp['state']['fact_history']['restriction_conflicts']
    latest = d['decision_id'] if expected['attempts'][-1] == 'ACCEPTED' else old['latest_decision_id']
    assert e['latest_decision_id'] == latest and cp['state']['latest_decision_id'] == latest
