"""Inputs and oracles are fixed before any decision, checkpoint or replay call."""
from copy import deepcopy
from pathlib import Path
from capital_research.core import decide, resume_decision
from capital_research.execution import simulate
from capital_research.continuity import make_checkpoint
from capital_research.repair_20261025.fixtures import advance, prefix
from capital_research.rejected_reassessment_20261026.fixtures import specification as old_spec

ROOT = Path(__file__).resolve().parents[1]
CASES = tuple(scope+'-'+mode for scope in ('same-job','cross-round')
              for mode in ('collision','identical','unique-control'))


def specification(name):
    if name not in CASES: raise ValueError(name)
    scope='cross-round' if name.startswith('cross-round') else 'same-job'
    mode=name[len(scope)+1:]
    j=old_spec('value-only-rejection')['first_input']
    initial=deepcopy(j['tape'][:2]);j['tape']=[]
    for day in ('06','07','08','09'):
        for old in initial:
            o=deepcopy(old);o.update(at=old['at'].replace('01-06','01-'+day),
                available_at=old['available_at'].replace('01-06','01-'+day),
                capacity_shares='100' if day=='09' else '0',
                settlement_date='2026-01-12')
            j['tape'].append(o)
    j['observed_until']='2026-01-12T16:00:00+08:00'
    return dict(schema='capital-review-identity-spec/0.1',synthetic=True,name=name,
        scope=scope,mode=mode,first_input=j,
        first_close='2026-01-06T16:00:00+08:00',
        first_review_id='inflight-review',
        inherited_close='2026-01-07T16:00:00+08:00',
        second_close='2026-01-08T16:00:00+08:00',
        second_expiry='2026-01-10T16:00:00+08:00',
        expected=dict(status='ERROR' if mode=='collision' else 'OK',
            error='REASSESSMENT_ID_CONTENT_CONFLICT' if mode=='collision' else None,
            B_fill_shares=None if mode=='collision' else '20' if mode=='identical' else '0',
            origin_initial_capital='2180',general_reserve='100',
            no_duplicate_attempt=True,no_new_authorization_from_retry=True))


def candidate(previous,data,cp,order_id,key,record,tag):
    fresh,ids=advance(data,cp)
    fact=fresh['assets']['B']['evidence'][0]
    fact['value']='EXPLICIT_REJECTED_REWRITE_NOT_A_SOURCE_CORRECTION'
    if tag=='second':fact['validity']['valid_until']='2026-01-10T16:00:00+08:00'
    record(tag+'-decision-input',fresh)
    result=resume_decision(previous,fresh,checkpoint=cp,cancelled_order_ids=ids)
    record(tag+'-decision-actual',result)
    return dict(id=key,order_id=order_id,decision_input=fresh,
        decision_id=result['decision']['decision_id'],plan_id='E-partial',
        checkpoint_id=cp['checkpoint_id'],cancelled_order_ids=ids)


def materialize(spec,record=lambda tag,x:None):
    j=deepcopy(spec['first_input']);initial=decide(j['decision_input'])
    first=prefix(j,spec['first_close']);record('first-prefix-input',first)
    e0=simulate(first);record('first-prefix-actual',e0)
    cp0=make_checkpoint(j['ledger_input'],e0,through_at=first['observed_until'])
    record('first-checkpoint',cp0)
    review1=candidate(initial,j['decision_input'],cp0,'B-buy',spec['first_review_id'],record,'first')
    j['reassessments']=[review1]
    if spec['scope']=='cross-round':
        first_round=prefix(j,spec['inherited_close']);record('first-round-input',first_round)
        e1=simulate(first_round);record('first-round-actual',e1)
        cp1=make_checkpoint(j['ledger_input'],e1,through_at=first_round['observed_until'])
        record('inherited-checkpoint',cp1)
        fresh,ids=advance(spec['first_input']['decision_input'],cp1)
        record('next-decision-input',fresh)
        next_decision=resume_decision(initial,fresh,checkpoint=cp1,cancelled_order_ids=ids)
        record('next-decision-actual',next_decision)
        j=deepcopy(spec['first_input']);j['decision_input']=fresh
        j['continuation']=dict(previous_decision=initial,checkpoint=cp1,cancelled_order_ids=ids)
        j['orders'][0].update(id='next-B-buy',decision_at=fresh['decision_at'],
                             submitted_at='2026-01-08T08:00:00+08:00')
        j['tape']=[o for o in j['tape'] if o['at'][:10]>spec['inherited_close'][:10]]
        previous=next_decision
    else:
        previous=initial
    prior_job=prefix(j,spec['second_close']);record('second-prefix-input',prior_job)
    prior=simulate(prior_job);record('second-prefix-actual',prior)
    cp2=make_checkpoint(j['ledger_input'],prior,through_at=prior_job['observed_until'])
    record('second-checkpoint',cp2)
    if spec['mode']=='identical':review2=deepcopy(review1)
    else:
        key=spec['first_review_id'] if spec['mode']=='collision' else 'new-restrictive-review'
        review2=candidate(previous,j['decision_input'],cp2,j['orders'][0]['id'],key,record,'second')
    if spec['scope']=='same-job':j['reassessments']=[review1,review2]
    else:j['reassessments']=[review2]
    record('input',j)
    try:
        actual=simulate(j)
        result=dict(status='OK',execution=actual,error=None)
    except ValueError as exc:
        result=dict(status='ERROR',execution=None,error=str(exc))
    record('actual',result)
    return dict(result=result,prefix=prior,job=j,checkpoint=cp2,previous=previous)


def observed(r):
    a=r['result'];e=a['execution']
    return dict(status=a['status'],error=a['error'],
        B_fill_shares=None if e is None else str(sum(int(f['shares']) for f in e['fills'] if f['code']=='B' and f['side']=='BUY')),
        attempts=None if e is None else len(e['reassessment_attempts']),
        latest_decision_id=None if e is None else e['latest_decision_id'],
        order_states=None if e is None else e['order_states'])
