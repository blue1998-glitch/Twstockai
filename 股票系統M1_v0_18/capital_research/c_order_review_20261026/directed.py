"""Directed gateway and next-batch evidence; no old producer or new prices."""
from copy import deepcopy
import json
from pathlib import Path
from capital_research.core import resume_decision
from capital_research.continuity import make_checkpoint,account_at_checkpoint
from capital_research.execution import simulate

ROOT=Path(__file__).parent


def gateway_inputs(actual):
    r=actual['review'];origin=r['execution_job']['ledger_input']
    cp=make_checkpoint(origin,r['prefix_execution'],through_at=r['prefix_execution']['observed_until'])
    return dict(previous=dict(decision=r['prefix_execution']['decision_records'][r['prefix_execution']['latest_decision_id']]),
        decision_input=deepcopy(r['review_request']['decision_input']),checkpoint=cp,cancelled_order_ids=['r1-B'],same_order_id='r1-B')


def edit_gateway(base,spec):
    x=deepcopy(base);edit=spec['edit'];target=edit.get('target','decision_input')
    if target=='order_id':x['same_order_id']=edit['value'];return x
    d=x[target]
    for key in edit['path'][:-1]:d=d[key]
    d[edit['path'][-1]]=edit['value'];return x


def resume(x):
    return resume_decision(x['previous'],x['decision_input'],checkpoint=x['checkpoint'],
        cancelled_order_ids=x['cancelled_order_ids'],same_order_id=x.get('same_order_id'))


def materialize_next(actual,record=lambda name,value:None):
    r=actual['review'];spec=json.loads((ROOT/'new-batch-specification.json').read_text())
    job=deepcopy(r['execution_job']);job['observed_until']=spec['end_at']
    record('settle-input',job);e=simulate(job);record('settle-actual',e)
    cp=make_checkpoint(job['ledger_input'],e,through_at=spec['end_at']);record('checkpoint',cp)
    data=deepcopy(r['review_request']['decision_input']);data.update(data_cutoff=spec['end_at'],decision_at=spec['next_decision_at'])
    data['account']=account_at_checkpoint(cp,decision_at=data['decision_at'],cancelled_order_ids=[])
    for code,a in data['assets'].items():
        m=deepcopy(a['marks'][0]);m.update(occurred_at=data['data_cutoff'],available_at=data['data_cutoff'],price=job['ledger_input']['assets'][code]['quotes'][data['data_cutoff'][:10]])
        a['marks']=[m];a['capital_eligibility'].update(data_cutoff=data['data_cutoff'],assessed_at=data['decision_at'],available_at=data['decision_at'])
    p=data['plans'][0];p['id']='next-C-batch';p['targets']={c:v['shares'] for c,v in data['account']['holdings'].items()};p['targets']['B']=str(int(p['targets']['B'])+int(spec['next_buy']))
    previous=dict(decision=e['decision_records'][e['latest_decision_id']])
    old=dict(previous=previous,decision_input=data,checkpoint=cp,cancelled_order_ids=[])
    record('old-trigger-input',old);old_result=resume(old);record('old-trigger-actual',old_result)
    fresh=deepcopy(old);a=fresh['decision_input']['assets']['B'];fact=deepcopy(a['evidence'][0]);fact.update(spec['new_trigger'])
    fact['validity'].update(valid_from=spec['end_at'],available_at=spec['end_at'],invalidation=None)
    a['evidence'].append(fact);a['capital_eligibility']['evidence_ids'].append(fact['id'])
    fresh['decision_input']['plans'][0]['trigger_ids']=[fact['id']]
    record('new-trigger-input',fresh);new_result=resume(fresh);record('new-trigger-actual',new_result)
    return dict(old=old_result,new=new_result,settled_execution=e,checkpoint=cp)
