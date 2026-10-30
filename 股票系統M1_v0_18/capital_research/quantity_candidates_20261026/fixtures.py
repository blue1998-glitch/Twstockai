"""Frozen bounded synthetic cases. No import of the new generator."""
from copy import deepcopy
import json
from pathlib import Path

BASELINE='1b200d681a6b68168c45591775e107174f064138'
OLD=Path(__file__).parents[1]/'repair_ab_20261025/after/A-own-evidence/input.json'


def request():
    data=deepcopy(json.loads(OLD.read_text())['decision_input'])
    data['plans']=[]
    # Keep actual other holdings and rights common to every alternative.
    data['account']['holdings']['C']=dict(shares='2',sellable='2')
    data['assets']['C']['group']='other'
    data['risk_limits']['group_value']['other']='3000'
    return dict(schema='capital-quantity-candidates-input/0.1',synthetic=True,
        decision_input=data,incumbent='A',destination='B',
        bounds=dict(retained_A=dict(minimum='98',maximum='100'),additional_B=dict(minimum='0',maximum='2')),
        max_grid_combinations='32',trigger_ids=['B-event'],continuation=None,
        policy=dict(version='synthetic-quantity-domain/0.1',parameter_source='EXPLICIT_SYNTHETIC_ENUMERATION_NOT_USER_RULE',
                    available_at=data['data_cutoff'],edge_budget='1000'))


def renew(data, checkpoint, at, cancelled=()):
    from capital_research.continuity import account_at_checkpoint
    close=checkpoint['state']['through_at']
    data['decision_at']=at;data['data_cutoff']=close
    data['account']=account_at_checkpoint(checkpoint,decision_at=at,cancelled_order_ids=cancelled)
    for asset in data['assets'].values():
        mark=deepcopy(asset['marks'][0]);mark.update(occurred_at=close,available_at=close)
        asset['marks']=[mark]
        review=asset['capital_eligibility'];review.update(data_cutoff=close,assessed_at=at,available_at=at)
    return data


def continued(*, fill=False, settled=False, revoked=False):
    """Existing 0.8 execution builds fixture provenance, not new candidate orders."""
    from capital_research.core import decide
    from capital_research.execution import simulate
    from capital_research.continuity import make_checkpoint
    first=deepcopy(json.loads(OLD.read_text()))
    if revoked:
        first['decision_input']['assets']['B']['evidence'][0]['validity']['invalidation']=dict(
            evidence_id='B-known-revocation',occurred_at='2026-01-07T14:00:00+08:00',
            available_at='2026-01-07T14:00:00+08:00',source_ids=['fixture'])
    if not fill:first.update(plan_id='A-zero',orders=[],tape=[])
    through='2026-01-12T16:00:00+08:00' if settled else '2026-01-08T16:00:00+08:00'
    first['observed_until']=through
    if not settled:first['tape']=[x for x in first['tape'] if x['at']<=through]
    executed=simulate(first)
    cp=make_checkpoint(first['ledger_input'],executed,through_at=through)
    previous=dict(decision=executed['decision_records'][executed['latest_decision_id']])
    cancelled=[x['order']['id'] for x in cp['state']['unfilled_orders']]
    data=renew(deepcopy(first['decision_input']),cp,through.replace('16:00','17:00'),cancelled)
    data['plans']=[]
    result=request();result['decision_input']=data
    n=int(data['account']['holdings']['A']['shares'])
    result['bounds']['retained_A']=dict(minimum=str(n-1),maximum=str(n))
    result['bounds']['additional_B']=dict(minimum='0',maximum='1')
    result['continuation']=dict(previous_decision=previous,checkpoint=cp,cancelled_order_ids=cancelled)
    result['policy']['available_at']=data['data_cutoff']
    return result,dict(input=first,execution=executed,checkpoint=cp)


def independent(result):
    data=result['decision_input'];fact=deepcopy(data['assets']['B']['evidence'][0])
    fact.update(id='B-independent-next',event_id='B-independent-next',formation_id='B-formation-next',
                volume_bar_id='B-bar-next',occurred_at=data['data_cutoff'],available_at=data['data_cutoff'])
    fact['validity'].update(invalidation=None,valid_from=data['data_cutoff'],available_at=data['data_cutoff'])
    data['assets']['B']['evidence'].append(fact)
    data['assets']['B']['capital_eligibility']['evidence_ids'].append(fact['id'])
    result['trigger_ids']=[fact['id']]
    return result


def cases():
    output={};prefixes={}
    def add(name,r,**expected):output[name]=dict(input=r,expected=expected)
    add('legal-grid',request(),status='COMPLETE',grid_points=9,probe=dict(A='99',B='1',classification='CURRENTLY_FEASIBLE'))
    r=request();r['decision_input']['consumed_evidence_tokens']=['fixture:event_id:B-event']
    add('consumed-trigger',r,status='COMPLETE',all_buys_rejected=True,required_reason='NO_NEW_INDEPENDENT_TRIGGER')
    r=request();r['trigger_ids']=['A-event']
    add('foreign-trigger',r,status='COMPLETE',all_buys_rejected=True,required_reason='BATCH_TRIGGER_NOT_OWNED_BY_DESTINATION')
    r=request();r['decision_input']['assets']['B']['capital_eligibility']['status']='UNKNOWN'
    add('unknown-capital',r,status='COMPLETE',all_buys_rejected=True,required_reason='NEW_CAPITAL_NOT_QUALIFIED:B')
    r=request();r['decision_input']['assets']['B']['evidence'][0]['validity']['invalidation']=dict(
        evidence_id='B-revocation',occurred_at=r['decision_input']['data_cutoff'],available_at=r['decision_input']['data_cutoff'],source_ids=['fixture'])
    add('invalidated-fact',r,status='COMPLETE',all_buys_rejected=True,required_reason='NEW_CAPITAL_NOT_QUALIFIED:B')
    r=request();r['decision_input']['account']['settled_cash']='101';r['decision_input']['account']['reserved_cash']='100'
    r['bounds']['retained_A']=dict(minimum='100',maximum='100')
    add('reserve-insufficient',r,status='COMPLETE',probe=dict(A='100',B='1',classification='REJECTED'),required_reason='JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS')
    r=request();r['decision_input']['account']['settled_cash']='100';r['decision_input']['account']['reserved_cash']='100'
    r['bounds']['retained_A']=dict(minimum='95',maximum='95');r['bounds']['additional_B']=dict(minimum='1',maximum='1')
    add('wait-settlement',r,status='COMPLETE',probe=dict(A='95',B='1',classification='WAIT_SETTLEMENT_REASSESSMENT'))
    r=request();d=r['decision_input'];d['account']['share_claims']=[]
    d['scenario_set']['scenarios']=[dict(id='synthetic-hedge',prices=dict(A='0.01',B='40',C='25'))]
    d['risk_limits']['account_stress_loss']='900';d['risk_limits']['group_value']['new']='40'
    r['bounds']=dict(retained_A=dict(minimum='100',maximum='100'),additional_B=dict(minimum='0',maximum='3'))
    add('non-monotone',r,status='COMPLETE',fixed_A='100',B_feasibility={'0':'REJECTED','1':'CURRENTLY_FEASIBLE','2':'CURRENTLY_FEASIBLE','3':'REJECTED'})
    r=request();r['max_grid_combinations']='8'
    add('grid-over-limit',r,status='REFUSED_SEARCH_LIMIT',candidate_count=0)
    r=request();r['decision_input']['account']['settled_cash']='1000000'
    add('full-over-limit',r,status='REFUSED_SEARCH_LIMIT',candidate_count=0)
    r=request();r['decision_input']['account']['pending_orders']=[dict(id='synthetic-old-buy',side='BUY',code='B',remaining_shares='1',limit_price='20.03',reserved_cash='22')]
    add('existing-order-full-unsupported',r,status='COMPLETE',full_classification='NOT_IMPLEMENTED')
    r,p=continued();prefixes['review-old-valid']=p
    add('review-old-valid',r,status='COMPLETE',all_buys_rejected=True,required_reason='NO_NEW_INDEPENDENT_TRIGGER',capital_qualified=True)
    add('review-independent-new',independent(deepcopy(r)),status='COMPLETE',probe=dict(A=r['decision_input']['account']['holdings']['A']['shares'],B='1',classification='CURRENTLY_FEASIBLE'),capital_qualified=True)
    r,p=continued(fill=True);prefixes['after-fill-no-new-event']=p
    add('after-fill-no-new-event',r,status='COMPLETE',all_buys_rejected=True,required_reason='NO_NEW_INDEPENDENT_TRIGGER',prefix_nonempty_fills=True)
    r,p=continued(settled=True);prefixes['after-settlement-no-new-event']=p
    add('after-settlement-no-new-event',r,status='COMPLETE',all_buys_rejected=True,required_reason='NO_NEW_INDEPENDENT_TRIGGER',settled_cash='1080')
    r,p=continued(revoked=True);prefixes['history-revocation-not-erased']=p
    r['decision_input']['assets']['B']['evidence'][0]['validity']['invalidation']=None
    add('history-revocation-not-erased',r,status='COMPLETE',all_buys_rejected=True,required_reason='NEW_CAPITAL_NOT_QUALIFIED:B',capital_qualified=False)
    r=request();fact=deepcopy(r['decision_input']['assets']['B']['evidence'][0]);fact.update(id='B-alias-label',event_id='new-label',formation_id='new-label')
    r['decision_input']['assets']['B']['evidence'].append(fact);r['trigger_ids']=[fact['id']]
    add('shared-volume-trigger',r,status='COMPLETE',all_buys_rejected=True,required_reason='NO_NEW_INDEPENDENT_TRIGGER')
    for name,prices in [('future-A-wins',dict(A='100',B='1',C='25')),('future-B-wins',dict(A='1',B='100',C='25')),('future-both-fall',dict(A='1',B='1',C='25'))]:
        r=request()
        for c,a in r['decision_input']['assets'].items():
            mark=deepcopy(a['marks'][0]);mark.update(price=prices[c],occurred_at='2026-01-12T14:00:00+08:00',available_at='2026-01-12T14:00:00+08:00');a['marks'].append(mark)
        r['decision_input']['source_integrity_metadata']['full_source_fingerprint']=name
        add(name,r,status='COMPLETE',same_research_as='legal-grid')
    return output,prefixes
