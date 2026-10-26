"""Bounded synthetic A/B/cash quantity intents; no IO, orders or optimizer."""
from copy import deepcopy
from decimal import localcontext

from . import allocation
from .core import decide, resume_decision, quantity, nonnegative, timestamp, fingerprint, evidence_tokens

SCHEMA='capital-quantity-candidates/0.1'
INPUT='capital-quantity-candidates-input/0.1'
MAX_GRID_COMBINATIONS=1024
REQUIRED={'schema','synthetic','decision_input','incumbent','destination','bounds',
          'max_grid_combinations','trigger_ids','continuation','policy'}


def _evaluate(data, plans, continuation):
    d=deepcopy(data);d['plans']=deepcopy(plans)
    if continuation is None:
        return decide(d)['decision']
    return resume_decision(continuation['previous_decision'],d,
        checkpoint=continuation['checkpoint'],cancelled_order_ids=continuation['cancelled_order_ids'])['decision']


def _classification(evaluation):
    return {'FEASIBLE':'CURRENTLY_FEASIBLE','CONDITIONAL':'WAIT_SETTLEMENT_REASSESSMENT',
            'REJECTED':'REJECTED','NOT_IMPLEMENTED':'NOT_IMPLEMENTED'}[evaluation['status']]


def generate(request):
    """Complete the explicit bounded domain; keep alternatives mutually exclusive."""
    with localcontext() as ctx:
        ctx.prec=50
        return _generate(request)


def _generate(request):
    if set(request)!=REQUIRED or request['schema']!=INPUT or request['synthetic'] is not True:
        raise ValueError('Explicit synthetic quantity contract required; no family/route override')
    data=request['decision_input'];a,b=request['incumbent'],request['destination']
    if a==b or a not in data['assets'] or b not in data['assets']:
        raise ValueError('Distinct existing incumbent/destination required')
    if data.get('synthetic') is not True:
        raise ValueError('Real-source qualification remains refused')
    q={code:str(int(quantity(row['shares']))) for code,row in data['account']['holdings'].items()}
    incumbent=int(quantity(q[a]));original_b=int(quantity(q[b]))
    if incumbent<=0:
        raise ValueError('Positive incumbent holding required for this bounded workflow')
    bounds=request['bounds'];policy=request['policy']
    if set(bounds)!={'retained_A','additional_B'} or set(policy)!={'version','parameter_source','available_at','edge_budget'}:
        raise ValueError('Explicit bounded quantity policy required')
    endpoints=[]
    for key in ('retained_A','additional_B'):
        row=bounds[key]
        if set(row)!={'minimum','maximum'}:
            raise ValueError('Only inclusive whole-share endpoints, no implicit sampling step')
        low,high=(int(quantity(row[k])) for k in ('minimum','maximum'))
        if low>high:
            raise ValueError('Inverted quantity range')
        endpoints.append((low,high))
    (amin,amax),(bmin,bmax)=endpoints
    if not 1<=amin<=amax<=incumbent:
        raise ValueError('Partial grid must retain between one and all incumbent shares')
    if not policy['version'] or not policy['parameter_source'] or timestamp(policy['available_at'])>timestamp(data['decision_at']):
        raise ValueError('Quantity policy unavailable or missing provenance')
    nonnegative(policy['edge_budget'])
    triggers=request['trigger_ids']
    if not isinstance(triggers,list) or any(not isinstance(x,str) for x in triggers):
        raise ValueError('Explicit trigger ID list required')
    continuation=request['continuation']
    if continuation is not None and set(continuation)!={'previous_decision','checkpoint','cancelled_order_ids'}:
        raise ValueError('Exact existing continuation contract required')
    configured_limit=int(quantity(request['max_grid_combinations']))
    points=(amax-amin+1)*(bmax-bmin+1)
    result=dict(schema=SCHEMA,synthetic=True,status='COMPLETE',incumbent=a,destination=b,
        generator_policy=deepcopy(policy),bounds=deepcopy(bounds),grid_points=points,
        configured_grid_limit=configured_limit,implementation_grid_limit=MAX_GRID_COMBINATIONS,
        legacy_full_builder_limit=20000,enumeration_complete=False,baseline=None,candidates=[],
        groups={k:[] for k in ('CURRENTLY_FEASIBLE','WAIT_SETTLEMENT_REASSESSMENT','REJECTED','NOT_IMPLEMENTED')},
        selected_id=None,ranking=None,order_generation='NOT_PERFORMED',execution='NOT_PERFORMED',
        candidate_scope='MUTUALLY_EXCLUSIVE_ALTERNATIVES_FROM_ONE_ACCOUNT_NOT_SIMULTANEOUS_ORDERS',
        reasons=[],data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,
        policy_authorized=False,live_execution_authorized=False,primary_pressure_id=None)
    def wrap():
        return dict(research=result,source_integrity_metadata=dict(full_request_id=fingerprint(request),
            original=deepcopy(data['source_integrity_metadata'])))
    if configured_limit<1 or configured_limit>MAX_GRID_COMBINATIONS or points>configured_limit or points>MAX_GRID_COMBINATIONS:
        result.update(status='REFUSED_SEARCH_LIMIT',reasons=['EXPLICIT_GRID_ENUMERATION_LIMIT_EXCEEDED'])
        return wrap()
    if data['execution_model']['buying_power']!='SETTLED_CASH_ONLY':
        result.update(status='NOT_IMPLEMENTED',reasons=['CREDIT_QUANTITY_WORKFLOW_NOT_IMPLEMENTED'])
        return wrap()
    baseline=_evaluate(data,[],continuation)
    result['baseline']=baseline
    result['common_account_id']=baseline['common_account_id']
    result['initial_capital']=baseline['initial_capital']
    # The existing builder proposes a snapshot endpoint. Revalidate every endpoint
    # through the current history/checkpoint; do not reuse its B-family approval.
    prepared=deepcopy(data);prepared['plans']=[];prepared['full_transfer_edge_budget']=policy['edge_budget']
    full_error=None
    try:
        full=allocation.full_transfer(prepared,incumbent=a,destination=b)
    except ValueError as exc:
        message=str(exc)
        if message=='Finite phase-1 proposal enumeration limit exceeded; solver not implemented':
            result.update(status='REFUSED_SEARCH_LIMIT',reasons=['LEGACY_FULL_TRANSFER_ENUMERATION_LIMIT_EXCEEDED'])
            return wrap()
        if message=='Full-deploy builder requires strict cash and no pre-existing orders':
            full_error=('NOT_IMPLEMENTED','EXISTING_ORDER_FULL_PROPOSAL_NOT_IMPLEMENTED')
        elif message=='Full transfer unavailable: some incumbent shares not sellable':
            full_error=('REJECTED','FULL_TRANSFER_INCUMBENT_NOT_FULLY_SELLABLE')
        else:
            raise
    by_target={}
    # Ownership and dependence are point-in-time facts. Raw future rows cannot
    # lend a foreign ID to B. A same-bar label is not a fresh trigger independent
    # of the different fact already used by the current B capital review.
    known={e['id']:e for feature in baseline['layer1'][b]['features'].values()
           for stance in feature.values() for e in stance if 'id' in e}
    owned=set(known)
    review=baseline['layer2'][b]['capital_eligibility']['review']
    review_ids=set(review['evidence_ids']) if review else set()
    def add(targets,kind):
        targets={code:str(int(quantity(value))) for code,value in targets.items()}
        key=fingerprint(targets)
        if key in by_target:
            by_target[key]['kinds'].append(kind)
            return
        buying=quantity(targets[b])>quantity(q[b])
        same=targets==q
        plan=dict(id='A-zero' if same else 'quantity:'+key,family='A' if same else 'C' if buying else 'E',route='R1',
            targets=deepcopy(targets),trigger_ids=deepcopy(triggers) if buying else [],
            edge_budget='0' if same else policy['edge_budget'],
            conditions=['CURRENT_RESEARCH_INTENT_ONLY','REASSESS_AFTER_SETTLEMENT','NEW_INDEPENDENT_TRIGGER_FOR_NEXT_BUY_BATCH'])
        evaluated=baseline if same else _evaluate(data,[plan],continuation)
        evaluation=deepcopy(next(x for x in evaluated['layer3']['alternatives'] if x['id']==plan['id']))
        gate=[]
        if buying and any(t not in owned for t in triggers):
            gate.append('BATCH_TRIGGER_NOT_OWNED_BY_DESTINATION')
        if buying and any(evidence_tokens(known[t]) & evidence_tokens(known[old])
                          for t in triggers if t in known for old in review_ids
                          if old in known and old!=t):
            gate.append('NO_NEW_INDEPENDENT_TRIGGER')
        classification='REJECTED' if gate else _classification(evaluation)
        candidate=dict(id=plan['id'],kinds=[kind],plan=plan,core_decision_id=evaluated['decision_id'],
            core_schema=evaluated['schema'],core_evaluation=evaluation,batch_gate_reasons=gate,
            reasons=sorted(set(evaluation['reasons']+gate)),classification=classification,
            feasible_for_research=not gate and evaluation['feasible'],
            additional_B=str(quantity(targets[b])-quantity(q[b])))
        if candidate['feasible_for_research'] and evaluation['common_account_id']!=baseline['common_account_id']:
            raise ValueError('Candidate account changed during enumeration')
        by_target[key]=candidate
        result['candidates'].append(candidate)
    add(q,'HOLD')
    for retained in range(amin,amax+1):
        for added in range(bmin,bmax+1):
            targets=deepcopy(q);targets[a]=str(retained);targets[b]=str(original_b+added)
            kind='PARTIAL_TRANSFER' if added else 'REDUCE_A_KEEP_CASH' if retained<incumbent else 'GRID_HOLD'
            add(targets,kind)
    cash=deepcopy(q);cash[a]='0';add(cash,'EXIT_A_KEEP_CASH')
    if full_error:
        classification,reason=full_error
        result['candidates'].append(dict(id='quantity:full-unavailable',kinds=['FULL_TRANSFER'],plan=None,
            classification=classification,reasons=[reason],feasible_for_research=False,additional_B=None,
            core_evaluation=None,batch_gate_reasons=[]))
    else:
        add(full['targets'],'FULL_TRANSFER')
    for candidate in result['candidates']:
        result['groups'][candidate['classification']].append(candidate['id'])
    result['enumeration_complete']=True
    result['evaluated_unique_targets']=len(by_target)
    result['full_proposal_source']='allocation.full_transfer -> current 0.8 recheck; every additional buy uses family C'
    return wrap()
