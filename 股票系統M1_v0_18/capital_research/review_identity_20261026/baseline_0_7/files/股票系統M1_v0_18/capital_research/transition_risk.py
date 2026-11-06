"""Joint as-observed exposure envelope, without assuming any sale succeeds."""
from copy import deepcopy
from decimal import Decimal
from .core import number, quantity, nonnegative, costs, _risk
from .continuity import row_at


def inspect_risk(data, origin, fills, day, marks, orders, states):
    row,_=row_at(origin,fills,day)
    q={c:quantity(n) for c,n in row['shares'].items()}
    policy=deepcopy(data);policy['account']['share_claims']=deepcopy(row['share_receivables'])
    prices={c:number(marks[c]['price']) for c in q}
    actual=_risk(q,prices,Decimal(0),policy)
    exposed={c:q[c]+sum((quantity(x['shares']) for x in row['share_receivables'] if x['code']==c),Decimal(0)) for c in q}
    pending={c:Decimal(0) for c in q};pending_cost={c:Decimal(0) for c in q}
    for o in orders:
        st=states[o['id']]
        if o['side']=='BUY' and st['status'] in ('OPEN','PARTIAL','WAITING_SETTLED_CASH'):
            n=quantity(st['remaining']);pending[o['code']]+=n*max(prices[o['code']],number(o['limit_price']))
            pending_cost[o['code']]+=costs(n,o['limit_price'],data['cost_model'],'BUY')['cash']
    values={c:exposed[c]*prices[c]+pending[c] for c in q}
    group={}
    for c,v in values.items():
        g=data['assets'][c]['group'];group[g]=group.get(g,Decimal(0))+v
    limits=data['risk_limits'];joint={('single:'+c):max(Decimal(0),v-nonnegative(limits['single_name_value'][c])) for c,v in values.items()}
    joint.update({('group:'+g):max(Decimal(0),v-nonnegative(limits['group_value'][g])) for g,v in group.items()})
    # Worst independent fill subset per common scenario: a potential hedge is not
    # credited until actually filled. Sell orders never reduce this envelope.
    worst=Decimal(0)
    for s in data['scenario_set']['scenarios']:
        loss=sum((exposed[c]*(prices[c]-number(s['prices'][c])) for c in q),Decimal(0))
        for o in orders:
            st=states[o['id']]
            if o['side']=='BUY' and st['status'] in ('OPEN','PARTIAL','WAITING_SETTLED_CASH'):
                n=quantity(st['remaining'])
                loss+=max(Decimal(0),costs(n,o['limit_price'],data['cost_model'],'BUY')['cash']-n*number(s['prices'][o['code']]))
        worst=max(worst,loss)
    joint['account_stress']=max(Decimal(0),worst-nonnegative(limits['account_stress_loss']))
    stale=[c for c in q if (exposed[c] or pending[c]) and marks[c]['at'][:10]!=day]
    return dict(actual_violations={k:str(v) for k,v in actual.items()},
        joint_possible_fill_violations={k:str(v) for k,v in joint.items()},
        joint_group_values={g:str(v) for g,v in group.items()},stale_exposure_marks=stale,
        marks=deepcopy(marks),rights=deepcopy(row['share_receivables']),
        qualification='DECLARED_SCENARIOS_AND_OBSERVED_MARKS_NOT_MAXIMUM_LOSS_GUARANTEE')
