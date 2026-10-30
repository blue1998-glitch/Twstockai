"""Only hypothetical repair inputs; no historical market producer."""
from copy import deepcopy
from datetime import timedelta,date
from capital_research.fixtures import fixture, job, observation
from capital_research.core import decide, resume_decision, timestamp
from capital_research.execution import simulate
from capital_research.continuity import make_checkpoint, account_at_checkpoint


def validity(at):
    return dict(schema='capital-fact-validity/0.1', available_at=at,
                valid_from=at, valid_until=None, invalidation=None,
                source_ids=['fixture'], qualification='EXPLICIT_SYNTHETIC_ONGOING_REQUIRES_REVIEW')


def review(asset, code, cutoff, at, qualified=True):
    return dict(schema='capital-entry-review/0.1', code=code,
                status='QUALIFIED_SYNTHETIC_RESEARCH' if qualified else 'NOT_QUALIFIED',
                data_cutoff=cutoff, assessed_at=at, available_at=at,
                evidence_ids=[e['id'] for e in asset['evidence']], source_ids=['fixture'],
                source_id=asset['source_id'], basis_id=asset['basis_id'],
                adjustment_version=asset['adjustment_version'])


def data_fixture():
    d=fixture()
    for c,a in d['assets'].items():
        for e in a['evidence']:e['validity']=validity(e['available_at'])
        a['entry_context']['validity']=validity(d['data_cutoff'])
        a['entry_context']['formal_reference']['validity']=validity(d['data_cutoff'])
        a['capital_eligibility']=review(a,c,d['data_cutoff'],d['decision_at'])
    return d


def close_proof(origin, initial_cutoff):
    return dict(schema='synthetic-ledger-close-clock/0.1',
        qualification='DECLARED_SYNTHETIC_DAY_END_NOT_REAL_MARKET_OR_BROKER_PROOF',
        closes={r['date']:dict(as_of=initial_cutoff if r['date']==origin['start'] else r['date']+'T16:00:00+08:00',
            available_at=initial_cutoff if r['date']==origin['start'] else r['date']+'T16:00:00+08:00',
            source_ids=['fixture']) for r in origin['calendar']})


def execution_job(plan='B-full', data=None):
    j=job(plan,data or data_fixture())
    j['ledger_close_proof']=close_proof(j['ledger_input'],j['decision_input']['data_cutoff'])
    return j


def prefix(j, through='2026-01-08T16:00:00+08:00'):
    j=deepcopy(j);j['observed_until']=through
    j['tape']=[o for o in j['tape'] if timestamp(o['at'])<=timestamp(through)]
    return j


def advance(previous, cp, *, at=None, qualified=True):
    d=deepcopy(previous);cutoff=cp['state']['through_at']
    at=at or (timestamp(cutoff)+timedelta(hours=1)).isoformat()
    ids=[x['order']['id'] for x in cp['state']['unfilled_orders']]
    d.update(decision_at=at,data_cutoff=cutoff)
    d['account']=account_at_checkpoint(cp,decision_at=at,cancelled_order_ids=ids,
                                      reserved_cash=previous['account']['reserved_cash'])
    for c,a in d['assets'].items():
        mark=deepcopy(a['marks'][0]);mark.update(price=cp['state']['row']['marks'][c]['value'],
            occurred_at=cutoff,available_at=cp['state'].get('ledger_close',{}).get('available_at',cutoff));a['marks']=[mark]
        a['capital_eligibility']=review(a,c,cutoff,at,qualified)
    return d,ids


def reassessed_job(*, extend=False):
    j=execution_job()
    if extend:
        origin=j['ledger_input'];old_end=date.fromisoformat(origin['end']);origin['end']='2026-01-16'
        for i in range(1,(date(2026,1,16)-old_end).days+1):
            day=old_end+timedelta(days=i);origin['calendar'].append(dict(date=day.isoformat(),trading=day.weekday()<5))
            for c,a in origin['assets'].items():a['quotes'][day.isoformat()]={'A':'10','B':'20','C':'25'}[c]
        for coverage in origin['coverage'].values():coverage['end']=origin['end']
        j['ledger_close_proof']=close_proof(origin,j['decision_input']['data_cutoff'])
    first=prefix(j);prior=simulate(first)
    cp=make_checkpoint(j['ledger_input'],prior,through_at=first['observed_until'])
    fresh,ids=advance(j['decision_input'],cp)
    # New but genuinely independent fact: later resume must carry this token too.
    e=deepcopy(fresh['assets']['B']['evidence'][0])
    e.update(id='B-reviewed-repair',formation_id='B-new-formation',volume_bar_id='B-new-bar',
             event_id='B-reviewed-repair',occurred_at=fresh['data_cutoff'],available_at=fresh['data_cutoff'])
    e['validity']=validity(fresh['data_cutoff']);fresh['assets']['B']['evidence'].append(e)
    fresh['assets']['B']['capital_eligibility']=review(fresh['assets']['B'],'B',fresh['data_cutoff'],fresh['decision_at'])
    original=decide(j['decision_input'])
    new=resume_decision(original,fresh,checkpoint=cp,cancelled_order_ids=ids)
    j['reassessments']=[dict(id='repair-settled-review',order_id='B-buy',decision_input=fresh,
        decision_id=new['decision']['decision_id'],plan_id='B-full',checkpoint_id=cp['checkpoint_id'],cancelled_order_ids=ids)]
    return j,original,new


def continuation_job(first_job, prior, previous_decision, *, plan='D-cash', fresh=None, ids=None):
    cp=make_checkpoint(first_job['ledger_input'],prior,through_at=prior['observed_until'])
    if fresh is None:fresh,ids=advance(first_job['decision_input'],cp)
    j=execution_job(plan,fresh);j['ledger_input']=deepcopy(first_job['ledger_input'])
    j['ledger_close_proof']=deepcopy(first_job['ledger_close_proof'])
    day=(timestamp(fresh['data_cutoff'])+timedelta(days=1)).date().isoformat()
    endpoint=first_job['ledger_input']['end'];j['observed_until']=endpoint+'T16:00:00+08:00'
    for o in j['orders']:
        o.update(id='next-'+o['id'],decision_at=fresh['decision_at'],submitted_at=day+'T08:00:00+08:00',expires_at=j['observed_until'])
    j['tape']=[observation(c,day+f'T09:0{i}:00+08:00',settlement=endpoint) for i,c in enumerate(('A','B','C'))]
    j['continuation']=dict(previous_decision=previous_decision,checkpoint=cp,cancelled_order_ids=ids)
    return j


def partial_first(*, expire=False):
    d=data_fixture();d['account']['reserved_cash']='100'
    d['account']['cash_claims']=[dict(id='opening-cash',amount='80',pay_date='2026-01-12',source_ids=['fixture'])]
    d['account']['share_claims']=[dict(id='opening-shares',code='A',shares='10',delivery_date='2026-01-09',tradable_date='2026-01-12',source_ids=['fixture'])]
    d['plans'].append(dict(id='E-partial',family='E',route='R1',targets=dict(A='50',B='20',C='0'),
        edge_budget='1000',trigger_ids=[],conditions=['EXPLICIT_PARTIAL_REPAIR_CASE']))
    j=prefix(execution_job('E-partial',d));j['tape'][0]['capacity_shares']='20';j['tape'][1]['capacity_shares']='7'
    if expire:
        for o in j['orders']:o['expires_at']=j['observed_until']
    return j
