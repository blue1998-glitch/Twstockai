"""Mechanical R1 all-deploy proposal, never a best-ratio/return optimizer."""
from copy import deepcopy
from decimal import localcontext
from .core import decide, quantity, number, timestamp


def full_transfer(data, *, incumbent, destination):
    """Largest whole-share destination position passing the same feasibility gate.

    Existing non-incumbent holdings/rights stay common. Capacity and risk can
    leave cash. Settlement remains conditional. No assumption of sell success.
    Caller-supplied event budgets/edge are research parameters, not user rules.
    """
    with localcontext() as ctx:
        ctx.prec=50
        return _full_transfer(data,incumbent,destination)


def _full_space(data,incumbent,destination,*,baseline=None):
    """Shared conservative preconditions and loose bound; no endpoint approval."""
    if incumbent == destination or incumbent not in data['assets'] or destination not in data['assets']:
        raise ValueError('Distinct existing assets required')
    if quantity(data['account']['holdings'][incumbent]['sellable']) != quantity(data['account']['holdings'][incumbent]['shares']):
        raise ValueError('Full transfer unavailable: some incumbent shares not sellable')
    if data['execution_model']['buying_power'] != 'SETTLED_CASH_ONLY' or data['account']['pending_orders']:
        raise ValueError('Full-deploy builder requires strict cash and no pre-existing orders')
    d=deepcopy(data);d['plans']=[]
    base=decide(d)['decision'] if baseline is None else baseline
    mark=[m for m in d['assets'][destination]['marks'] if m['occurred_at']==d['data_cutoff'] and timestamp(m['available_at'])<=timestamp(d['decision_at'])][0]
    # NAV is an intentionally loose search bound; feasibility excludes rights from cash.
    upper=int(number(base['initial_capital'])/number(mark['price']))
    targets={c:v['shares'] for c,v in d['account']['holdings'].items()}
    targets[incumbent]='0'
    original=int(targets[destination]);upper=max(original,upper)
    return d,upper,original,targets


def _full_transfer(data,incumbent,destination):
    d,upper,original,targets=_full_space(data,incumbent,destination)
    if upper-original > 20000:
        raise ValueError('Finite phase-1 proposal enumeration limit exceeded; solver not implemented')
    def probe(n):
        targets[destination]=str(n)
        d['plans']=[dict(id='R1-full-proposal',family='B',route='R1',targets=deepcopy(targets),trigger_ids=[],
                        edge_budget=data['full_transfer_edge_budget'],conditions=['RECHECK_AFTER_SALE_SETTLES'])]
        return decide(d)['decision']['layer3']['alternatives'][1]
    # Shared scenarios may contain hedges, so feasibility need not be monotone.
    # Bounded descending enumeration avoids assuming it is a convex optimizer.
    for n in range(upper,original-1,-1):
        proposal=probe(n)
        if proposal['feasible']:return proposal
    return proposal


MAX_UNIT_PROBES=20000


def _unit_full_search(data,incumbent,destination,*,baseline,units,max_probes,probe):
    """Inside generate's fixed Decimal context; probe is its COMPLETE gate.

    Enumerate legal *increments*, not rounded legacy targets. A higher unknown
    point prevents claiming that a lower feasible quantity is the maximum.
    """
    receipt=dict(status='NOT_ATTEMPTED',reasons=[],probe_count=0,probe_trace=[],
        configured_max_probes=max_probes,implementation_max_probes=MAX_UNIT_PROBES,
        legal_candidate_count=None,selected_target=None,
        scope='MECHANICAL_FULL_TRANSFER_ENDPOINT_NOT_STRATEGY_OR_RECOMMENDATION')
    try:
        _,upper,original,targets=_full_space(data,incumbent,destination,baseline=baseline)
    except ValueError as exc:
        if str(exc)=='Full-deploy builder requires strict cash and no pre-existing orders':
            receipt.update(status='NOT_IMPLEMENTED',reasons=['EXISTING_ORDER_FULL_PROPOSAL_NOT_IMPLEMENTED'])
        elif str(exc)=='Full transfer unavailable: some incumbent shares not sellable':
            receipt.update(status='REJECTED_PRECONDITION',reasons=['FULL_TRANSFER_INCUMBENT_NOT_FULLY_SELLABLE'])
        else:raise
        return None,receipt
    sold=int(quantity(data['account']['holdings'][incumbent]['shares']))
    receipt.update(original_B=str(original),upper_total_B=str(upper),sell_A=str(sold),unit_B=str(units[destination]))
    if sold%units[incumbent]:
        receipt.update(status='REJECTED_DOMAIN',reasons=['SELL_QUANTITY_OUTSIDE_DECLARED_UNIT:'+incumbent])
        return None,receipt
    count=(upper-original)//units[destination]+1
    receipt['legal_candidate_count']=count
    if count>max_probes or count>MAX_UNIT_PROBES or max_probes>MAX_UNIT_PROBES:
        receipt.update(status='REFUSED_SEARCH_LIMIT',reasons=['FULL_UNIT_SEARCH_ENUMERATION_LIMIT_EXCEEDED'])
        return None,receipt
    for k in range(count-1,-1,-1):
        targets[destination]=str(original+k*units[destination])
        candidate=probe(deepcopy(targets))
        receipt['probe_trace'].append(dict(targets=deepcopy(targets),additional_B=candidate['additional_B'],
            classification=candidate['classification'],feasible_for_research=candidate['feasible_for_research'],
            reasons=deepcopy(candidate['reasons']),core_decision_id=candidate['core_decision_id']))
        receipt['probe_count']+=1
        if candidate['classification']=='NOT_IMPLEMENTED':
            receipt.update(status='NOT_IMPLEMENTED',reasons=['HIGHER_FULL_TARGET_NOT_IMPLEMENTED_MAXIMUM_UNKNOWN'])
            return None,receipt
        if candidate['feasible_for_research']:
            receipt.update(status='FOUND' if k else 'FOUND_ZERO_ADDITION',selected_target=deepcopy(targets))
            return candidate,receipt
    receipt.update(status='NO_FEASIBLE_TARGET',reasons=['NO_FULL_TARGET_PASSES_COMPLETE_GATE'])
    return None,receipt
