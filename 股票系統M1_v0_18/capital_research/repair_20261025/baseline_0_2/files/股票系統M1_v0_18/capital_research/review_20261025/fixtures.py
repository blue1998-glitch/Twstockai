"""New synthetic review fixtures; prior 20261024 evidence remains immutable."""
from copy import deepcopy
from capital_research.fixtures import fixture, job, order
from capital_research.core import decide,resume_decision
from capital_research.continuity import make_checkpoint,account_at_checkpoint
from capital_research.execution import simulate


def first_segment(data=None):
    j=job(data=data);j['observed_until']='2026-01-08T16:00:00+08:00'
    j['tape']=[o for o in j['tape'] if o['at'][:10]<='2026-01-08']
    r=simulate(j);cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
    return j,r,cp


def next_input(previous_input,cp,*,decision_at='2026-01-08T17:00:00+08:00'):
    d=deepcopy(previous_input);d['decision_at']=decision_at;d['data_cutoff']=cp['state']['through_at']
    cancelled=[o['order']['id'] for o in cp['state']['unfilled_orders']]
    d['account']=account_at_checkpoint(cp,decision_at=decision_at,cancelled_order_ids=cancelled,
                                     reserved_cash=previous_input['account']['reserved_cash'])
    for c,a in d['assets'].items():
        m=deepcopy(a['marks'][0]);m.update(price=cp['state']['row']['marks'][c]['value'],occurred_at=d['data_cutoff'],available_at=d['data_cutoff'])
        a['marks'].append(m)
    return d,cancelled


def reauthorized_job():
    first,r,cp=first_segment();fresh,cancelled=next_input(first['decision_input'],cp)
    previous=decide(first['decision_input']);new=resume_decision(previous,fresh,checkpoint=cp,cancelled_order_ids=cancelled)
    j=job()
    j['reassessments']=[dict(id='after-sale-settled',order_id='B-buy',decision_input=fresh,
        decision_id=new['decision']['decision_id'],plan_id='B-full',checkpoint_id=cp['checkpoint_id'],cancelled_order_ids=cancelled)]
    return j,cp,new


def continued_job(data=None):
    first,r,cp=first_segment(data);fresh,cancelled=next_input(first['decision_input'],cp)
    second=job('B-full',fresh);second['ledger_input']=deepcopy(first['ledger_input'])
    second['orders']=[o for o in second['orders'] if o['side']=='BUY']
    for o in second['orders']:
        o.update(id='round2-'+o['id'],decision_at=fresh['decision_at'],submitted_at='2026-01-09T08:00:00+08:00')
    second['tape']=[o for o in first['tape'] if o['at'][:10]>'2026-01-08']
    # first_segment intentionally contains only the prefix; the later observations
    # come from the same original full synthetic tape, never from inferred bars.
    second['tape']=[o for o in job()['tape'] if o['at'][:10]>'2026-01-08']
    second['continuation']=dict(previous_decision=decide(first['decision_input']),checkpoint=cp,cancelled_order_ids=cancelled)
    return first,r,second
