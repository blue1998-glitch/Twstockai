"""Bounded synthetic A/B/cash quantity intents; no IO, orders or optimizer."""
from copy import deepcopy
from decimal import Context, InvalidOperation, DivisionByZero, Overflow, ROUND_HALF_EVEN, localcontext

from . import allocation
from . import quantity_domain
from .core import decide, resume_decision, quantity, nonnegative, timestamp, fingerprint, evidence_tokens

SCHEMA='capital-quantity-candidates/0.1'
INPUT='capital-quantity-candidates-input/0.1'
INPUT_V2='capital-quantity-candidates-input/0.2'
SCHEMA_V2='capital-quantity-candidates/0.2'
INPUT_V3='capital-quantity-candidates-input/0.3'
SCHEMA_V3='capital-quantity-candidates/0.3'
INPUT_V4='capital-quantity-candidates-input/0.4'
SCHEMA_V4='capital-quantity-candidates/0.4'
MAX_GRID_COMBINATIONS=1024
IMPLEMENTATION_REVISION='0.2.1-deterministic-decimal-context'
REQUIRED={'schema','synthetic','decision_input','incumbent','destination','bounds',
          'max_grid_combinations','trigger_ids','continuation','policy'}


def _validate_batch_context(request):
    context=request['batch_context'];data=request['decision_input'];b=request['destination']
    required={'version','parameter_source','available_at','phase','origin','code','source_id','basis_id','adjustment_version','account_id'}
    if not isinstance(context,dict) or set(context)!=required:
        raise ValueError('Explicit batch context with exact account/asset binding required')
    if (not context['version'] or not context['parameter_source'] or
            timestamp(context['available_at'])>timestamp(data['decision_at'])):
        raise ValueError('Batch context missing provenance or not yet available')
    if context['code']!=b or any(context[k]!=data['assets'][b][k] for k in ('source_id','basis_id','adjustment_version')):
        raise ValueError('Batch context source/basis/asset mismatch')
    if context['account_id']!=fingerprint(data['account']):
        raise ValueError('Batch context account mismatch')
    if context['phase'] not in ('FIRST_ENTRY','ADDITIONAL_BATCH','UNKNOWN'):
        raise ValueError('Explicit supported batch phase required')
    expected='CHECKPOINT_EPISODE' if request['continuation'] is not None else 'DECLARED_SYNTHETIC_OPENING'
    if context['origin']!=expected:
        raise ValueError('Batch context origin does not match supplied continuity')


def _first_entry_reasons(request, known):
    """No ledger reconstruction here: reuse the already-validated checkpoint."""
    data=request['decision_input'];b=request['destination'];a=data['account']
    if request['batch_context']['phase']=='UNKNOWN':
        return ['BATCH_PHASE_UNKNOWN']
    if request['batch_context']['phase']!='FIRST_ENTRY':
        return []
    participated=bool(quantity(a['holdings'][b]['shares']) or
        any(x['code']==b and quantity(x['shares']) for x in a['share_claims']))
    continuation=request['continuation']
    if continuation is not None:
        cp=continuation['checkpoint'];origin=cp['origin_ledger_input']['opening']
        participated |= bool(quantity(origin['shares'][b]) or
            any(x['code']==b and quantity(x['shares']) for x in origin['share_claims']))
        participated |= any(f['code']==b and f['side']=='BUY' and quantity(f['shares']) for f in cp['state']['accepted_fills'])
        execution=cp['execution_result']
        participated |= any(o['code']==b and o['side']=='BUY' for o in execution.get('order_history',execution['orders']))
    if participated:
        return ['FIRST_ENTRY_CONTRADICTS_B_EPISODE_HISTORY']
    if continuation is None:
        tokens=set().union(*(evidence_tokens(e) for e in known.values())) if known else set()
        if tokens & set(data['consumed_evidence_tokens']):
            return ['FIRST_ENTRY_HISTORY_NOT_ESTABLISHED']
    return []


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
    # Direct callers receive the same numerical environment as the standard
    # replay path, without inheriting ambient traps, rounding or exponent limits.
    with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999,
            capitals=1,clamp=0,flags=[],traps=[InvalidOperation,DivisionByZero,Overflow])):
        return _generate(request)


def _generate(request):
    v4=request.get('schema')==INPUT_V4
    v3=v4 or request.get('schema')==INPUT_V3
    v2=v3 or request.get('schema')==INPUT_V2
    required=(REQUIRED|{'batch_context'} if v2 else REQUIRED)|({'quantity_domain'} if v3 else set())|({'full_search'} if v4 else set())
    if set(request)!=required or request['schema'] not in (INPUT,INPUT_V2,INPUT_V3,INPUT_V4) or request['synthetic'] is not True:
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
    a_key='sell_A' if v2 else 'retained_A'
    if set(bounds)!={a_key,'additional_B'} or set(policy)!={'version','parameter_source','available_at','edge_budget'}:
        raise ValueError('Explicit bounded quantity policy required')
    endpoints=[]
    for key in (a_key,'additional_B'):
        row=bounds[key]
        if set(row)!={'minimum','maximum'}:
            raise ValueError('Only inclusive whole-share endpoints, no implicit sampling step')
        low,high=(int(quantity(row[k])) for k in ('minimum','maximum'))
        if low>high:
            raise ValueError('Inverted quantity range')
        endpoints.append((low,high))
    (amin,amax),(bmin,bmax)=endpoints
    if v2:
        if not 0<=amin<=amax<=incumbent:
            raise ValueError('Explicit A sale range must be within physical incumbent shares')
        amin,amax=incumbent-amax,incumbent-amin
    elif not 1<=amin<=amax<=incumbent:
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
    if v2:_validate_batch_context(request)
    units=quantity_domain.validate(request) if v3 else None
    if v4:
        search=request['full_search']
        if (not isinstance(search,dict) or set(search)!={'schema','version','parameter_source','available_at','max_probes'}
                or search['schema']!='capital-full-unit-search/0.1'
                or any(not isinstance(search[k],str) or not search[k] for k in ('version','parameter_source','available_at'))):
            raise ValueError('EXPLICIT_FULL_SEARCH_PROVENANCE_REQUIRED')
        if timestamp(search['available_at'])>timestamp(data['decision_at']):
            raise ValueError('FULL_SEARCH_POLICY_NOT_YET_AVAILABLE')
        value=search['max_probes']
        if not isinstance(value,str) or not value.isascii() or not value.isdigit() or int(value)<=0:
            raise ValueError('EXPLICIT_POSITIVE_FULL_SEARCH_LIMIT_REQUIRED')
        max_probes=int(value)
    configured_limit=int(quantity(request['max_grid_combinations']))
    points=(amax-amin+1)*(bmax-bmin+1)
    raw_points=points
    if v3:
        sale_axis,sales=quantity_domain.axis(incumbent-amax,incumbent-amin,units[a])
        buy_axis,buys=quantity_domain.axis(bmin,bmax,units[b])
        points=sale_axis['count']*buy_axis['count']
    result=dict(schema=SCHEMA_V4 if v4 else SCHEMA_V3 if v3 else SCHEMA_V2 if v2 else SCHEMA,synthetic=True,status='COMPLETE',incumbent=a,destination=b,
        generator_policy=deepcopy(policy),bounds=deepcopy(bounds),grid_points=points,
        configured_grid_limit=configured_limit,implementation_grid_limit=MAX_GRID_COMBINATIONS,
        legacy_full_builder_limit=20000,enumeration_complete=False,baseline=None,candidates=[],
        groups={k:[] for k in ('CURRENTLY_FEASIBLE','WAIT_SETTLEMENT_REASSESSMENT','REJECTED','NOT_IMPLEMENTED')},
        selected_id=None,ranking=None,order_generation='NOT_PERFORMED',execution='NOT_PERFORMED',
        candidate_scope='MUTUALLY_EXCLUSIVE_ALTERNATIVES_FROM_ONE_ACCOUNT_NOT_SIMULTANEOUS_ORDERS',
        reasons=[],data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,
        policy_authorized=False,live_execution_authorized=False,primary_pressure_id=None)
    if v2:
        result.update(batch_context=deepcopy(request['batch_context']),batch_phase_reasons=[],
            policy_governs=['bounds','max_grid_combinations','edge_budget'],
            account_liquidation_claimed=False,
            original_pending_B_orders=deepcopy([o for o in data['account']['pending_orders'] if o['code']==b]))
    if v3:
        strict,_=quantity_domain.axis(max(1,incumbent-amax),min(incumbent-1,incumbent-amin),units[a])
        result.update(quantity_domain=deepcopy(request['quantity_domain']),quantity_domain_id=fingerprint(request['quantity_domain']),
            domain_axes=dict(sell_A=sale_axis,additional_B=buy_axis),raw_integer_grid_points=raw_points,
            quantity_domain_diagnostics=dict(grid_empty=points==0,has_strict_partial_A_sale=bool(strict['count'])),
            domain_reasons=(['NO_LEGAL_GRID_QUANTITIES_IN_EXPLICIT_BOUNDS'] if points==0 else [])+
                (['NO_LEGAL_STRICT_PARTIAL_A_SALE_IN_BOUNDS'] if not strict['count'] else []),
            full_proposal_status='NOT_ATTEMPTED',enumeration_scope='EXPLICIT_LEGAL_GRID_NOT_UNIT_AWARE_FULL_SOLVER')
    if v4:
        result.update(full_search_policy=deepcopy(search),full_search_receipt=None,
            enumeration_scope='EXPLICIT_LEGAL_GRID_AND_BOUNDED_COMPLETE_GATE_FULL_SEARCH')
        result['policy_governs'].append('full_search.max_probes')
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
        full=None if v4 else allocation.full_transfer(prepared,incumbent=a,destination=b)
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
    first_entry=v2 and request['batch_context']['phase']=='FIRST_ENTRY'
    phase_reasons=_first_entry_reasons(request,known) if v2 else []
    pending_b_buy=v2 and any(o['code']==b and o['side']=='BUY' for o in data['account']['pending_orders'])
    if v2:result['batch_phase_reasons']=phase_reasons
    def build(targets,kind,*,in_grid=False):
        targets={code:str(int(quantity(value))) for code,value in targets.items()}
        key=fingerprint(targets)
        buying=quantity(targets[b])>quantity(q[b])
        same=targets==q
        plan=dict(id='A-zero' if same else 'quantity:'+key,family='A' if same else 'C' if buying and not first_entry else 'E',route='R1',
            targets=deepcopy(targets),trigger_ids=deepcopy(triggers) if buying and not first_entry else [],
            edge_budget='0' if same else policy['edge_budget'],
            conditions=['CURRENT_RESEARCH_INTENT_ONLY','REASSESS_AFTER_SETTLEMENT','NEW_INDEPENDENT_TRIGGER_FOR_NEXT_BUY_BATCH'])
        evaluated=baseline if same else _evaluate(data,[plan],continuation)
        evaluation=deepcopy(next(x for x in evaluated['layer3']['alternatives'] if x['id']==plan['id']))
        gate=[]
        if buying and not first_entry and any(t not in owned for t in triggers):
            gate.append('BATCH_TRIGGER_NOT_OWNED_BY_DESTINATION')
        if buying and not first_entry and any(evidence_tokens(known[t]) & evidence_tokens(known[old])
                          for t in triggers if t in known for old in review_ids
                          if old in known and old!=t):
            gate.append('NO_NEW_INDEPENDENT_TRIGGER')
        if buying:gate.extend(phase_reasons)
        if buying and pending_b_buy:gate.append('EXTERNAL_EXISTING_B_BUY_CONTINUATION_NOT_IMPLEMENTED')
        unit_reasons=quantity_domain.reasons(targets,q,a,b,units) if v3 else []
        gate.extend(unit_reasons)
        classification='NOT_IMPLEMENTED' if buying and pending_b_buy else 'REJECTED' if gate else _classification(evaluation)
        candidate=dict(id=plan['id'],kinds=[kind],plan=plan,core_decision_id=evaluated['decision_id'],
            core_schema=evaluated['schema'],core_evaluation=evaluation,batch_gate_reasons=gate,
            reasons=sorted(set(evaluation['reasons']+gate)),classification=classification,
            feasible_for_research=not gate and evaluation['feasible'],
            additional_B=str(quantity(targets[b])-quantity(q[b])))
        if v3:candidate.update(unit_gate_reasons=unit_reasons,in_explicit_grid=in_grid)
        if candidate['feasible_for_research'] and evaluation['common_account_id']!=baseline['common_account_id']:
            raise ValueError('Candidate account changed during enumeration')
        return candidate
    def add(targets,kind,*,in_grid=False,prepared_candidate=None):
        targets={code:str(int(quantity(value))) for code,value in targets.items()}
        key=fingerprint(targets)
        if key in by_target:
            by_target[key]['kinds'].append(kind)
            if v3:by_target[key]['in_explicit_grid'] |= in_grid
            return by_target[key]
        candidate=prepared_candidate if prepared_candidate is not None else build(targets,kind,in_grid=in_grid)
        by_target[key]=candidate
        result['candidates'].append(candidate)
        return candidate
    if v4:
        full_candidate,receipt=allocation._unit_full_search(prepared,a,b,baseline=baseline,units=units,
            max_probes=max_probes,probe=lambda targets:build(targets,'FULL_TRANSFER'))
        result.update(full_search_receipt=receipt,full_proposal_status=receipt['status'])
        if receipt['status']=='REFUSED_SEARCH_LIMIT':
            result.update(status='REFUSED_SEARCH_LIMIT',reasons=deepcopy(receipt['reasons']))
            return wrap()
    add(q,'HOLD')
    retained_values=((incumbent-n for n in sales) if points else ()) if v3 else range(amax,amin-1,-1) if v2 else range(amin,amax+1)
    for retained in retained_values:
        for added in (buys if v3 else range(bmin,bmax+1)):
            targets=deepcopy(q);targets[a]=str(retained);targets[b]=str(original_b+added)
            kind='PARTIAL_TRANSFER' if added else 'REDUCE_A_KEEP_CASH' if retained<incumbent else 'GRID_HOLD'
            add(targets,kind,in_grid=True)
    cash=deepcopy(q);cash[a]='0';add(cash,'EXIT_A_KEEP_CASH')
    if v4:
        if full_candidate is not None:
            add(full_candidate['plan']['targets'],'FULL_TRANSFER',prepared_candidate=full_candidate)
        else:
            classification='NOT_IMPLEMENTED' if receipt['status']=='NOT_IMPLEMENTED' else 'REJECTED'
            result['candidates'].append(dict(id='quantity:full-unit-unavailable',kinds=['FULL_TRANSFER'],plan=None,
                classification=classification,reasons=deepcopy(receipt['reasons']),feasible_for_research=False,
                additional_B=None,core_evaluation=None,batch_gate_reasons=[],unit_gate_reasons=[],in_explicit_grid=False))
    elif full_error:
        if v3:result['full_proposal_status']='LEGACY_FULL_ENDPOINT_UNAVAILABLE'
        classification,reason=full_error
        result['candidates'].append(dict(id='quantity:full-unavailable',kinds=['FULL_TRANSFER'],plan=None,
            classification=classification,reasons=[reason],feasible_for_research=False,additional_B=None,
            core_evaluation=None,batch_gate_reasons=[]))
        if v3:result['candidates'][-1].update(unit_gate_reasons=[],in_explicit_grid=False)
    elif v3 and quantity_domain.reasons(full['targets'],q,a,b,units):
        unit_reasons=quantity_domain.reasons(full['targets'],q,a,b,units)
        result['full_proposal_status']='NOT_IMPLEMENTED_IN_DECLARED_DOMAIN'
        result['candidates'].append(dict(id='quantity:full-unit-unavailable',kinds=['FULL_TRANSFER'],plan=None,
            classification='NOT_IMPLEMENTED',reasons=['UNIT_AWARE_FULL_TRANSFER_NOT_IMPLEMENTED']+unit_reasons,
            feasible_for_research=False,additional_B=None,core_evaluation=None,batch_gate_reasons=[],unit_gate_reasons=unit_reasons,
            in_explicit_grid=False,legacy_full_endpoint=deepcopy(full)))
    else:
        if v3:result['full_proposal_status']='LEGACY_ENDPOINT_IN_DECLARED_DOMAIN'
        add(full['targets'],'FULL_TRANSFER')
    for candidate in result['candidates']:
        if v2:
            candidate['sold_A']=str(incumbent-int(candidate['plan']['targets'][a])) if candidate['plan'] else None
            candidate['generation_reasons']=list(candidate['kinds'])
            candidate['generation_policy_version']=policy['version']
        result['groups'][candidate['classification']].append(candidate['id'])
    result['enumeration_complete']=True
    result['evaluated_unique_targets']=len(by_target)
    result['full_proposal_source']=('allocation.full_transfer -> current 0.8 recheck; first-entry gate or independent additional-batch gate'
        if v2 else 'allocation.full_transfer -> current 0.8 recheck; every additional buy uses family C')
    if v4:result['full_proposal_source']='allocation shared bound -> descending legal deltas -> same complete build/core/resume/batch/unit gate'
    return wrap()
