"""Frozen field expectations, not policy performance or an oracle rewrite."""
def verify(expected,actual):
    assert actual['status']==expected['status'],actual
    assert actual['ranking'] is None and actual['selected_label'] is None
    assert all(actual[k] is False for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'))
    if actual['status']=='REFUSED':
        assert actual['columns']==[] and actual['common_identity_ids'] is None
        if 'reason' in expected:assert any(expected['reason'] in r['reason'] for r in actual['refusals']),actual['refusals']
        if 'difference_path' in expected:assert any(r['path']==expected['difference_path'] for r in actual['differences']),actual['differences']
    else:
        assert actual['comparable'] is True and actual['total_mismatches']==0
        columns=actual['columns']
        if expected.get('identical_orders'):assert columns[0]['summary']['orders']==columns[1]['summary']['orders']
        if 'fills' in expected:
            assert [next(o['filled_quantity'] for o in c['summary']['orders'] if o['order_id']=='r1-B') for c in columns]==expected['fills']
        if 'payables' in expected:assert [c['summary']['account']['saved_row']['purchase_payable'] for c in columns]==expected['payables']
        if expected.get('full_ledger_ids_different'):
            assert actual['provenance'][0]['origin_ledger_input_id']!=actual['provenance'][1]['origin_ledger_input_id']
