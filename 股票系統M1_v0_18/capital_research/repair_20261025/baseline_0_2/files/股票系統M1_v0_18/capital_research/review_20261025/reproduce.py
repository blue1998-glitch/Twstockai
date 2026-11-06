"""Independent Work hypotheses: capture observed behavior before any repair."""
from copy import deepcopy
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
from capital_research.core import decide, resume_decision
from capital_research.execution import simulate, compare_jobs
from capital_research.fixtures import fixture, job


def risk_job():
    d=fixture()
    for a in d['assets'].values():a['group']='shared'
    d['risk_limits']['group_value']={'shared':'1100'}
    d['plans'].append(dict(id='E-transition',family='E',route='R1',targets=dict(A='0',B='40',C='0'),
                           edge_budget='1000',trigger_ids=[],conditions=['COMMON_TRANSITION_RISK']))
    j=job('E-transition',d);j['tape'][0]['market_state']='LIMIT_DOWN_NO_SELL'
    return j


def cases():
    j=risk_job();r=simulate(j)
    yield 'transition-risk',dict(input=j,expected='No B buy if A remains; joint shared exposure must not increase from 1000 to about 1800 beyond 1100',
        actual=r,observed_group_exposure_at_Jan6=str(sum(float(r['ledger']['daily'][1]['shares'][c])*float(j['ledger_input']['assets'][c]['quotes']['2026-01-06']) for c in ('A','B','C'))))
    j=job();j['tape'][2]['evidence_status']='INVALIDATED'
    r=simulate(j)
    yield 'settlement-reassessment',dict(input=j,expected='Conditional B-full buy requires a new bound decision after settlement; invalidated evidence must cancel even inside limit',actual=r)
    a=job();b=deepcopy(a);b['tape'][2]['market_state']='LIMIT_UP_NO_BUY'
    try:r=compare_jobs(dict(open=a,blocked=b));error=None
    except ValueError as e:r=None;error=str(e)
    yield 'common-market',dict(input=dict(open=a,blocked=b),expected='Reject same-market comparison with different tape state',actual=r,error=error)
    d=fixture();old=decide(d);new=fixture();new['decision_at']='2026-01-05T16:00:00+08:00';new['account']['settled_cash']='9000'
    try:r=resume_decision(old,new);error=None
    except ValueError as e:r=None;error=str(e)
    yield 'continuity-and-static-scope',dict(input=dict(previous=old,next_input=new),
        expected='Token carry must not certify a reset account as continuous; static target Pareto must not imply policy dominance',
        actual=r,error=error,baseline_comparison_label=old['decision']['layer3']['comparison'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    versions={n:hashlib.sha256(Path('capital_research',n).read_bytes()).hexdigest() for n in ('core.py','execution.py','fixtures.py')}
    baseline=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    for name,value in cases():
        value.update(synthetic=True,baseline=baseline,source_sha256=versions)
        with (out/(name+'.json')).open('x') as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2)
        print(name, 'captured')


if __name__=='__main__':main()
