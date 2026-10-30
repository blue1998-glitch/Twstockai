"""Explicit offline IO for phase-1 synthetic artifacts. Existing files immutable."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import argparse
from graph_core.core import fingerprint
from rotation_research.store import Journal
from .core import decide, resume_decision
from .execution import simulate, compare_jobs
from .allocation import full_transfer
from .fixtures import fixture, job


def write_new(path,value):
    body=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=body:raise ValueError('Existing artifact preserved; choose a new output: '+str(path))
        return
    with path.open('xb') as f:f.write(body)


def _frozen_v01_reference(output):
    out=Path(output);data=fixture();decision=decide(data)
    write_new(out/'input.json',data);write_new(out/'execution-input.json',job())
    store=Journal(out/'records')
    store.save('decision-v1',decision)
    later=fixture();later['decision_at']='2026-01-05T16:00:00+08:00'
    store.save('decision-v2',resume_decision(decision,later))
    comparison=compare_jobs({p:job(p,data) for p in ('A-zero','B-full','C-event','D-cash','E-joint')})
    write_new(out/'common-capital-comparison.json',comparison)
    completed=simulate(job());store.save('execution-v1',completed)
    write_new(out/'accounting-evidence.json',dict(synthetic=True,initial='2000',
        final_accrual_equity=completed['ledger']['daily'][-1]['net_accrual_equity'],
        fills_fee_tax=completed['ledger']['fees_and_tax_on_fills'],slippage='2.98',external_flow='0',
        conservation='2000 = 1991.020 + 6 + 2.98',
        terminal_estimated_exit_cost=completed['ledger']['terminal_estimated_exit_cost'],
        terminal_exit_is_estimate_not_fill=True,daily=completed['ledger']['daily'],fills=completed['fills']))
    variants={}
    for name,pa,pb in [('A_surge','100','1'),('B_surge','1','100'),('both_fall','1','1')]:
        d=fixture()
        for c,p in [('A',pa),('B',pb)]:
            row=deepcopy(d['assets'][c]['marks'][0]);row.update(price=p,occurred_at='2026-01-06T14:00:00+08:00',available_at='2026-01-06T14:00:00+08:00')
            d['assets'][c]['marks'].append(row)
        d['source_integrity_metadata']['full_source_fingerprint']=name
        r=decide(d);assert r['decision']==decision['decision']
        variants[name]=dict(decision_id=r['decision']['decision_id'],source_integrity_metadata=r['source_integrity_metadata'],
                            decision_bytes_projection_identical=True,input=d)
    write_new(out/'future-isolation.json',dict(synthetic=True,comparison_scope='ENTIRE_DECISION_OBJECT_EXCLUDES_SOURCE_INTEGRITY_METADATA',variants=variants))
    cases={}
    for name,modify,expected in [
        ('sold_A_B_limit_up',lambda j:[x.update(market_state='LIMIT_UP_NO_BUY') for x in j['tape'] if x['code']=='B'],'A sold, B shares 0, no completed switch'),
        ('A_limit_down',lambda j:j['tape'][0].update(market_state='LIMIT_DOWN_NO_SELL'),'no sell, no funded full buy'),
        ('capacity_20',lambda j:j['tape'][2].update(capacity_shares='20'),'B fills 20, remaining 79 expires'),
        ('slow_reentry',lambda j:j['tape'][2].update(price='32'),'price exceeds limit, remains cash')]:
        j=job();modify(j);result=simulate(j)
        cases[name]=dict(expected=expected,actual=result,input=j)
    for path,pa,pb in [('false_breakout_A_up','15','12'),('B_accelerates','11','32'),('both_fall','7','12'),('continued_rise','15','32')]:
        values={}
        for p in ('A-zero','B-full','C-event','D-cash','E-joint'):
            j=job(p);j['ledger_input']['assets']['A']['quotes']['2026-01-12']=pa;j['ledger_input']['assets']['B']['quotes']['2026-01-12']=pb
            r=simulate(j)
            values[p]=dict(accrual_equity=r['ledger']['daily'][-1]['net_accrual_equity'],
                           terminal_net_equity_after_estimated_exit=r['ledger']['end_net_equity'],
                           fills=r['fills'],input=j)
        cases[path]=dict(expected='Directional mechanism counterexample; no market performance claim',actual=values)
    write_new(out/'synthetic-cases.json',dict(synthetic=True,cases=cases,ranked_market_performance=False))
    write_new(out/'R1-full-proposal.json',full_transfer(data,incumbent='A',destination='B'))
    d=fixture();d['execution_model'].update(buying_power='BROKER_CREDIT_RESEARCH',broker_credit=dict(
        qualification='EXPLICIT_SYNTHETIC_TERMS',available_at=d['data_cutoff'],source_id='synthetic-broker',version='credit/1',limit='1000'))
    write_new(out/'broker-credit-distinction.json',dict(decision=decide(d),execution=simulate(job('B-full',d)),
        interpretation='Credit is separately qualified as an imaginary assumption. Existing ledger refuses credit replay.'))
    for key in ('decision-v1','decision-v2','execution-v1'):
        assert store.read(key)['id']==key
    return dict(status='SYNTHETIC_ARTIFACTS_SAVED_AND_READ',decision_id=decision['decision']['decision_id'],
                tests_rerun=False,market_producer_rerun=False,total_net_return_comparison_qualified=False)


def build(output):
    raise ValueError('Frozen phase-1/0.1 producer: use fixed ea380cf for historical reproduction, or capital_research.review_20261025.build for new 0.2 evidence; no old artifact overwrite')


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    print(json.dumps(build(a.output),ensure_ascii=False,sort_keys=True))


if __name__=='__main__':main()
