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


def _full_transfer(data,incumbent,destination):
    if incumbent == destination or incumbent not in data['assets'] or destination not in data['assets']:
        raise ValueError('Distinct existing assets required')
    if quantity(data['account']['holdings'][incumbent]['sellable']) != quantity(data['account']['holdings'][incumbent]['shares']):
        raise ValueError('Full transfer unavailable: some incumbent shares not sellable')
    if data['execution_model']['buying_power'] != 'SETTLED_CASH_ONLY' or data['account']['pending_orders']:
        raise ValueError('Full-deploy builder requires strict cash and no pre-existing orders')
    d=deepcopy(data);d['plans']=[]
    base=decide(d)['decision']
    mark=[m for m in d['assets'][destination]['marks'] if m['occurred_at']==d['data_cutoff'] and timestamp(m['available_at'])<=timestamp(d['decision_at'])][0]
    # NAV is an intentionally loose search bound; feasibility excludes rights from cash.
    upper=int(number(base['initial_capital'])/number(mark['price']))
    targets={c:v['shares'] for c,v in d['account']['holdings'].items()}
    targets[incumbent]='0'
    original=int(targets[destination]);upper=max(original,upper)
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
