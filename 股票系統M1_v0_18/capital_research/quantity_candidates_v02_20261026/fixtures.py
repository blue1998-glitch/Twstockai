"""Read fixed v0.1 raw inputs; no producer, replay, test or generator calls."""
from copy import deepcopy
import json
from pathlib import Path
from graph_core.core import fingerprint

PRIOR=Path(__file__).parents[1]/'quantity_candidates_20261026'


def previous(name):
    return json.loads((PRIOR/'cases'/name/'input.json').read_text())


def convert(data,phase='FIRST_ENTRY',sell=(0,2),buy=(0,2)):
    r=deepcopy(data);r['schema']='capital-quantity-candidates-input/0.2'
    r['bounds']=dict(sell_A=dict(minimum=str(sell[0]),maximum=str(sell[1])),additional_B=dict(minimum=str(buy[0]),maximum=str(buy[1])))
    a=r['decision_input']['assets']['B'];d=r['decision_input']
    r['batch_context']=dict(version='synthetic-batch-phase/0.1',parameter_source='EXPLICIT_SYNTHETIC_RESEARCH_EPISODE_NOT_AUTHENTICATED_HISTORY',
        available_at=d['decision_at'],phase=phase,origin='CHECKPOINT_EPISODE' if r['continuation'] else 'DECLARED_SYNTHETIC_OPENING',
        code='B',source_id=a['source_id'],basis_id=a['basis_id'],adjustment_version=a['adjustment_version'],account_id=fingerprint(d['account']))
    if phase=='FIRST_ENTRY':r['trigger_ids']=[]
    return r


def cases():
    out={}
    def add(name,r,**expected):out[name]=dict(input=r,expected=expected)
    manual=[['100','0'],['100','1'],['100','2'],['99','0'],['99','1'],['99','2'],['98','0'],['98','1'],['98','2']]
    add('first-manual-grid',convert(previous('legal-grid')),status='COMPLETE',manual_grid=manual,
        probe=dict(A='99',B='1',classification='CURRENTLY_FEASIBLE'),buy_family='E')
    add('all-A-sale-partial-B',convert(previous('legal-grid'),sell=(99,100)),status='COMPLETE',grid_points=6,
        probe=dict(A='0',B='1',classification='CURRENTLY_FEASIBLE'),preserve_C='2')
    add('first-old-fact-reviewed',convert(previous('review-old-valid'),sell=(0,1),buy=(0,1)),status='COMPLETE',
        probe=dict(A='100',B='1',classification='CURRENTLY_FEASIBLE'),capital_qualified=True,buy_family='E')
    add('additional-old-trigger',convert(previous('review-old-valid'),'ADDITIONAL_BATCH',sell=(0,1),buy=(0,1)),status='COMPLETE',all_buys='REJECTED',reason='NO_NEW_INDEPENDENT_TRIGGER')
    add('additional-independent',convert(previous('review-independent-new'),'ADDITIONAL_BATCH',sell=(0,1),buy=(0,1)),status='COMPLETE',
        probe=dict(A='100',B='1',classification='CURRENTLY_FEASIBLE'),buy_family='C')
    add('cannot-relabel-first-after-fill',convert(previous('after-fill-no-new-event'),sell=(0,1),buy=(0,1)),status='COMPLETE',all_buys='REJECTED',reason='FIRST_ENTRY_CONTRADICTS_B_EPISODE_HISTORY')
    add('cannot-reset-first-without-history',convert(previous('consumed-trigger')),status='COMPLETE',all_buys='REJECTED',reason='FIRST_ENTRY_HISTORY_NOT_ESTABLISHED')
    add('additional-after-partial-fill',convert(previous('after-fill-no-new-event'),'ADDITIONAL_BATCH',sell=(0,1),buy=(0,1)),status='COMPLETE',all_buys='REJECTED',reason='NO_NEW_INDEPENDENT_TRIGGER')
    add('unknown-batch-phase',convert(previous('legal-grid'),'UNKNOWN'),status='COMPLETE',all_buys='REJECTED',reason='BATCH_PHASE_UNKNOWN')
    add('first-capital-unknown',convert(previous('unknown-capital')),status='COMPLETE',all_buys='REJECTED',reason='NEW_CAPITAL_NOT_QUALIFIED:B')
    add('first-invalidated',convert(previous('invalidated-fact')),status='COMPLETE',all_buys='REJECTED',reason='NEW_CAPITAL_NOT_QUALIFIED:B')
    add('known-history-not-erased',convert(previous('history-revocation-not-erased'),'ADDITIONAL_BATCH',sell=(0,1),buy=(0,1)),status='COMPLETE',all_buys='REJECTED',reason='NEW_CAPITAL_NOT_QUALIFIED:B')
    for field,value in [('source_id','OTHER-SOURCE'),('basis_id','OTHER-BASIS')]:
        r=convert(previous('legal-grid'));r['decision_input']['assets']['B']['capital_eligibility'][field]=value
        add('review-mismatch-'+field,r,error_type='ValueError',error_contains='Capital review source/basis/asset mismatch')
    r=convert(previous('legal-grid'));r['decision_input']['assets']['B']['entry_context']['liquidity_shares']='1'
    add('liquidity-limit',r,status='COMPLETE',probe=dict(A='100',B='2',classification='REJECTED'),reason='ENTRY_LIQUIDITY_LIMIT:B')
    r=convert(previous('legal-grid'));r['decision_input']['risk_limits']['group_value']['new']='25'
    add('common-risk-limit',r,status='COMPLETE',probe=dict(A='100',B='2',classification='REJECTED'),reason='RISK_LIMIT_EXCEEDED')
    r=previous('legal-grid');r['decision_input']['account']['settled_cash']='121'
    add('cost-cannot-be-free',convert(r,sell=(0,0),buy=(1,1)),status='COMPLETE',probe=dict(A='100',B='1',classification='REJECTED'),available='21',reason='JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS')
    r=previous('legal-grid');r['decision_input']['account']['settled_cash']='100'
    add('receivable-not-spendable',convert(r,sell=(0,0),buy=(1,1)),status='COMPLETE',probe=dict(A='100',B='1',classification='REJECTED'),available='0',reason='JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS')
    add('wait-sale-settlement',convert(previous('wait-settlement'),sell=(5,5),buy=(1,1)),status='COMPLETE',probe=dict(A='95',B='1',classification='WAIT_SETTLEMENT_REASSESSMENT'))
    add('non-monotone',convert(previous('non-monotone'),sell=(0,0),buy=(0,3)),status='COMPLETE',B_feasibility={'0':'REJECTED','1':'CURRENTLY_FEASIBLE','2':'CURRENTLY_FEASIBLE','3':'REJECTED'})
    r=convert(previous('legal-grid'));r['max_grid_combinations']='8'
    add('grid-over-limit',r,status='REFUSED_SEARCH_LIMIT',candidate_count=0)
    add('full-over-limit',convert(previous('full-over-limit')),status='REFUSED_SEARCH_LIMIT',candidate_count=0)
    add('existing-B-order',convert(previous('existing-order-full-unsupported'),'ADDITIONAL_BATCH',sell=(0,0),buy=(1,1)),status='COMPLETE',all_buys='NOT_IMPLEMENTED',reason='EXTERNAL_EXISTING_B_BUY_CONTINUATION_NOT_IMPLEMENTED',available='878')
    r=previous('legal-grid');r['decision_input']['account']['pending_orders']=[dict(id='synthetic-A-lock',code='A',side='SELL',remaining_shares='2')]
    add('sell-locked-A',convert(r,sell=(99,100),buy=(0,0)),status='COMPLETE',probe=dict(A='1',B='0',classification='REJECTED'),reason='SELLABLE_SHARES_RESERVED_OR_UNAVAILABLE:A')
    for name in ('future-A-wins','future-B-wins','future-both-fall'):
        add(name,convert(previous(name)),status='COMPLETE',same_research_as='first-manual-grid')
    return out
