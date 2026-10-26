"""Frozen synthetic outcomes and original-account invariants."""
from decimal import Decimal


def verify(request,expected,actual):
    r=actual['review'];assert r['status']==expected['status'],(r['status'],r['reasons'])
    if 'reason' in expected:assert any(expected['reason'] in x for x in r['reasons']),r['reasons']
    assert all(r[k] is False for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'))
    if not r['status'].startswith('REPLAYED_'):return
    e=r['execution'];d=r['review_decision'];cp=r['checkpoint'];scope=d['same_order_continuation']
    assert d['schema']=='capital-decision/0.9' and e['schema']=='capital-execution/0.9' and cp['schema']=='capital-account-checkpoint/0.8'
    assert r['prefix_execution']['schema']=='capital-execution/0.8' and r['prefix_checkpoint']['schema']=='capital-account-checkpoint/0.7'
    assert e['order_history']==r['prefix_execution']['order_history']
    assert scope['order_id']=='r1-B' and scope['remaining']=='20' and scope['original_order_quantity']=='20'
    p=next(p for p in d['layer3']['alternatives'] if p['id']==scope['plan_id'])
    assert p['family']=='C' and p['trigger_ids']==['B-event'] and scope['trigger_ids']==['B-event']
    assert scope['latest_predecessor_id']==r['prefix_execution']['latest_decision_id']
    assert scope['checkpoint_id']==r['prefix_checkpoint']['checkpoint_id']
    assert set(r['prefix_execution']['reviewed_evidence_tokens'])<=set(e['reviewed_evidence_tokens'])
    assert set(scope['original_trigger_tokens'])<=set(d['reviewed_evidence_tokens'])
    if 'new_tokens' in expected:assert d['new_evidence_tokens']==expected['new_tokens']
    fills=[f for f in e['fills'] if f['code']=='B' and f['side']=='BUY']
    assert str(sum(int(f['shares']) for f in fills))==expected['B_filled']
    assert all(e['fill_order_ids'][f['id']]=='r1-B' for f in fills)
    st=e['order_states']['r1-B'];assert st['remaining']==expected['remaining']
    if 'order_status' in expected:assert st['status']==expected['order_status']
    assert int(expected['B_filled'])+int(st['remaining'])==20
    assert len(e['fills'])==len({f['id'] for f in e['fills']})
    assert cp['state']['origin_initial_capital']==expected['capital']
    assert cp['state']['general_reserved_cash']=='100' and cp['state']['external_flow']=='0'
    assert cp['state']['row']['shares']['B']==str(5+int(expected['B_filled']))
    assert cp['state']['row']['shares']['C']=='2'
    if expected.get('end_settled'):
        assert cp['state']['row']['cash_claims']==[] and cp['state']['row']['share_receivables']==[]
        assert cp['state']['row']['shares']['A']=='60'
        assert Decimal(cp['state']['row']['settled_cash'])==Decimal('535.36')
        assert Decimal(cp['state']['row']['purchase_payable'])==0
    else:
        assert cp['state']['row']['cash_claims'][0]['amount']=='80'
        assert cp['state']['row']['share_receivables'][0]['shares']=='10'
        assert Decimal(cp['state']['row']['settled_cash'])==Decimal('596.5')
    assert e['reassessment_attempts'][-1]['outcome']==('ACCEPTED' if expected['status']=='REPLAYED_ACCEPTED_REVIEW' else 'REJECTED')
