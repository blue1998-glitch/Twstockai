"""Independent expected outcomes and original-book invariants, not a producer."""
from decimal import Decimal


def verify(request,expected,actual):
    r=actual['review']
    assert r['status']==expected['status'],(r['status'],r['reasons'])
    if 'reason' in expected:assert any(expected['reason'] in x for x in r['reasons']),r['reasons']
    assert all(r[k] is False for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'))
    if not r['status'].startswith('REPLAYED_'):return
    e=r['execution'];p=r['prefix_execution'];cp=r['checkpoint']['state'];origin=request['replay_input']['origin_ledger']
    assert e['status']=='SYNTHETIC_EXECUTION_REPLAY'
    assert e['orders']==p['orders'] and e['order_history']==p['order_history']
    assert len(e['fills'])==len({f['id'] for f in e['fills']})
    assert e['fills'][:len(p['fills'])]==p['fills']
    assert e['origin_common_account_id']==p['origin_common_account_id']
    assert cp['origin_initial_capital']=='1330' and cp['external_flow']=='0'
    assert cp['general_reserved_cash']=='100'
    assert set(p['reviewed_evidence_tokens'])<=set(e['reviewed_evidence_tokens'])
    assert r['review_decision']['continuity']['latest_predecessor_id']==p['latest_decision_id']
    assert r['review_decision']['continuity']['checkpoint_id']==r['prefix_checkpoint']['checkpoint_id']
    assert r['review_request']['decision_input']['account']['as_of']==request['review']['decision_template']['data_cutoff']
    fills=[f for f in e['fills'] if f['code']=='B' and f['side']=='BUY']
    assert str(sum(int(f['shares']) for f in fills))==expected['B_filled']
    assert all(e['fill_order_ids'][f['id']]=='r1-B' for f in fills)
    assert all(f['decision_date']=='2026-01-08' for f in fills)
    state=e['order_states']['r1-B'];assert state['remaining']==expected['remaining']
    assert int(expected['B_filled'])+int(state['remaining'])==20
    if 'order_status' in expected:assert state['status']==expected['order_status'],state
    attempt=e['reassessment_attempts'][-1];assert attempt['outcome']==expected['attempt']
    assert attempt['request']==r['review_request']
    assert attempt['decision']==r['review_decision']
    if 'new_tokens' in expected:assert r['review_decision']['new_evidence_tokens']==expected['new_tokens']
    assert set(e['fill_order_ids'])=={f['id'] for f in e['fills']}
    assert e['latest_decision_id']==(r['review_decision']['decision_id'] if expected['attempt']=='ACCEPTED' else p['latest_decision_id'])
    row=cp['row']
    # Before Jan12 the unchanged pre-existing entitlements remain assets once.
    if request['replay_input']['rounds'][-1]['observed_until'][:10]<'2026-01-12':
        assert len(row['cash_claims'])==len(origin['opening']['cash_claims'])
        for saved,opening in zip(row['cash_claims'],origin['opening']['cash_claims']):
            assert {k:saved[k] for k in opening}==opening
            assert saved['kind']=='OPENING_RECEIVABLE'
        assert row['share_receivables']==origin['opening']['share_claims']
    assert Decimal(row['settled_cash'])>=100
    assert row['shares']['C']=='2'

