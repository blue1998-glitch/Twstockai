"""Compare new summaries to frozen manual field expectations only."""
def verify(expected,actual):
    assert actual['status']==expected['status'],(actual['status'],actual['reasons'])
    if 'reason' in expected:assert any(expected['reason'] in x for x in actual['reasons']),actual['reasons']
    if actual['status']!='READABLE':
        assert actual['account'] is None and actual['orders']==[]
        return
    if 'view' in expected:assert actual['source']['view']==expected['view']
    if 'order' not in expected:return
    order=next(x for x in actual['orders'] if x['order_id']==expected['order'])
    fields=dict(filled='filled_quantity',live='live_remaining_quantity',cancelled='cancelled_unfilled_quantity',
        expired='expired_unfilled_quantity',pending='pending_settlement_quantity',unknown_settlement='unknown_settlement_quantity')
    for key,field in fields.items():
        if key in expected:assert order[field]==expected[key],(key,order[field],expected[key])
    assert order['saved_order_state']['reserved_cash']==expected['reserved']
    assert [r['outcome'] for r in order['reviews']]==expected['reviews']
    if 'cash' in expected:assert actual['account']['saved_row']['settled_cash']==expected['cash']
    if 'payable' in expected:assert actual['account']['saved_row']['purchase_payable']==expected['payable']
    if 'new_order' in expected:
        new=next(x for x in actual['orders'] if x['order_id']==expected['new_order'])
        assert new['filled_quantity']==expected['new_filled']
        assert new['origin_decision_id']!=order['origin_decision_id']
