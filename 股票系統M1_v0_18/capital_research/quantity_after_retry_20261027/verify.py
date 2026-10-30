"""Frozen candidate and conservation expectations; no second account model."""
from capital_research.quantity_after_retry import FLAGS


def verify(request, expected, saved):
    a = saved['adapter']
    assert a['status'] == expected['status'], (a['status'], a['reasons'])
    assert all(a[k] is False for k in FLAGS) and a['primary_pressure_id'] is None
    assert a['ranking'] is None and a['selected_id'] is None
    assert a['order_generation'] == a['execution'] == 'NOT_PERFORMED'
    if a['status'] not in ('GENERATED', 'STOPPED_QUANTITY_GATE'):
        assert expected['reason'] in a['reasons'], a['reasons']
        assert a['generation'] is None
        return
    g = a['generation']['research']
    if a['status'] == 'STOPPED_QUANTITY_GATE':
        assert expected['reason'] in a['reasons']
        assert g['candidates'] == [] and g['enumeration_complete'] is False
        return
    assert g['enumeration_complete'] is True and g['grid_points'] == 4
    assert g['selected_id'] is None and g['ranking'] is None
    assert all(g[k] is False for k in FLAGS)
    q = a['quantity_request']
    assert q['continuation']['checkpoint'] == request['checkpoint']
    assert q['continuation']['previous_decision']['decision']['decision_id'] == request['predecessor']['latest_decision_id']
    assert set(request['checkpoint']['state']['reviewed_evidence_tokens']) <= set(q['decision_input']['consumed_evidence_tokens'])
    assert q['batch_context']['phase'] == 'ADDITIONAL_BATCH'
    assert q['batch_context']['origin'] == 'CHECKPOINT_EPISODE'
    assert a['account']['reserved_cash'] == '100' and a['account']['settled_cash'] == '275.100'
    assert a['account']['holdings'] == dict(A=dict(shares='60', sellable='60'), B=dict(shares='25', sellable='25'), C=dict(shares='2', sellable='2'))
    assert a['binding']['origin_initial_capital'] == '1430'
    assert a['binding']['current_net_accrual_equity'] == '1425.100'
    assert g['baseline']['continuity']['origin_initial_capital'] == '1430'
    assert g['baseline']['continuity']['latest_predecessor_id'] == request['predecessor']['latest_decision_id']
    assert set(a['binding']['reviewed_evidence_tokens']) <= set(g['baseline']['reviewed_evidence_tokens'])
    candidates = g['candidates']
    for c in candidates:
        if c['plan']:
            assert c['plan']['targets']['C'] == '2'
            if int(c['additional_B']) > 0:
                assert c['plan']['family'] == 'C'
    buys = [c for c in candidates if c['plan'] and int(c['additional_B']) > 0]
    assert buys
    if expected['buying'] == 'ALL_REJECTED':
        assert all(not c['feasible_for_research'] and expected['reason'] in c['reasons'] for c in buys)
    else:
        assert any(c['feasible_for_research'] for c in buys)
    if 'grid_targets' in expected:
        grid = [c['plan']['targets'] for c in candidates if c['plan'] and
            0 <= int(c['sold_A']) <= 1 and 0 <= int(c['additional_B']) <= 1]
        assert {tuple(sorted(t.items())) for t in grid} == {tuple(sorted(t.items())) for t in expected['grid_targets']}
