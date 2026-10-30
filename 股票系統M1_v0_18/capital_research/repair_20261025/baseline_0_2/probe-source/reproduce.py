"""Capture probes with inputs/expectations/versions before modifying numerical code."""
from copy import deepcopy
from pathlib import Path
from decimal import Decimal, localcontext
import argparse
import hashlib
import json
from capital_research.core import decide, resume_decision, VERSION as DECISION_VERSION
from capital_research.execution import simulate, VERSION as EXECUTION_VERSION
from capital_research.continuity import make_checkpoint, account_at_checkpoint
from .fixtures import data_fixture, execution_job, prefix, advance, reassessed_job, continuation_job, partial_first


EXPECTED={
    'entry-gate':'NOT_QUALIFIED must exclude the increasing target and prevent the buy',
    'sellable-chain':'Unreleased sellable=0 must be preserved, or continuation explicitly refused',
    'intraday-close':'09:00 watermark cannot expose the 995 end-of-day settlement or authorize 09:01 use',
    'latest-predecessor':'Latest reassessed decision must resume; an older predecessor must refuse',
    'expired-evidence':'An expired supporting fact cannot qualify fresh capital despite a new decision ID',
    'partial-cancel-chain':'Partial fills, claims, pending rights and general reserve must survive explicit cancellation and continuation',
    'partial-expiry-chain':'Expiry releases only order reservations; preserves remaining quantity, rights and original capital'}


def attempt(call):
    try:return dict(value=call(),error=None)
    except (ValueError,KeyError) as e:return dict(value=None,error=type(e).__name__+': '+str(e))


def probe(name):
    if name in ('entry-gate','expired-evidence'):
        d=data_fixture()
        if name=='entry-gate':
            d['assets']['B']['capital_eligibility']['status']='NOT_QUALIFIED'
            plan='C-event'
        else:
            # The expiry is a declared hypothetical source fact, not a fixed-age rule.
            d['assets']['B']['evidence'][0]['validity']['valid_until']='2026-01-05T13:59:00+08:00'
            d['assets']['B']['evidence'][0]['validity']['valid_from']='2026-01-02T14:00:00+08:00'
            plan='C-event'
        j=execution_job(plan,d);r=simulate(j)
        return dict(input=j,actual=dict(decision=decide(d),execution=r))
    if name=='sellable-chain':
        d=data_fixture();d['account']['holdings']['A']['sellable']='0';j=prefix(execution_job('A-zero',d));r=simulate(j)
        cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        a=attempt(lambda:advance(d,cp));out=dict(input=j,first_execution=r,checkpoint=cp,advance=a)
        if a['value']:
            fresh,ids=a['value'];out['next_decision']=attempt(lambda:resume_decision(decide(d),fresh,checkpoint=cp,cancelled_order_ids=ids))
        return dict(input=j,actual=out)
    if name=='intraday-close':
        j=prefix(execution_job(),through='2026-01-08T09:00:00+08:00');r=attempt(lambda:simulate(j));out=dict(execution=r)
        if r['value']:
            cp=attempt(lambda:make_checkpoint(j['ledger_input'],r['value'],through_at=j['observed_until']));out['checkpoint']=cp
            if cp['value']:out['next_input']=attempt(lambda:advance(j['decision_input'],cp['value'],at='2026-01-08T09:01:00+08:00'))
        return dict(input=j,actual=out)
    if name=='latest-predecessor':
        j,old,new=reassessed_job();r=simulate(j);cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        fresh,ids=advance(j['reassessments'][0]['decision_input'],cp)
        return dict(input=j,actual=dict(execution=r,checkpoint=cp,next_input=fresh,cancelled_order_ids=ids,
            latest=attempt(lambda:resume_decision(new,fresh,checkpoint=cp,cancelled_order_ids=ids)),
            stale=attempt(lambda:resume_decision(old,fresh,checkpoint=cp,cancelled_order_ids=ids))))
    j=partial_first(expire=name=='partial-expiry-chain');r=simulate(j)
    second=continuation_job(j,r,decide(j['decision_input']));out=simulate(second)
    return dict(input=dict(first=j,next=second),actual=dict(first_execution=r,next_execution=out))


def capture(output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('capital_research').glob('*.py')}
    for name,expected in EXPECTED.items():
        with localcontext() as ctx:
            ctx.prec=50
            result=attempt(lambda:probe(name))
        record=dict(synthetic=True,case=name,expected=expected,versions=dict(decision=DECISION_VERSION,execution=EXECUTION_VERSION),
                    source_sha256=sources,**result)
        with (out/(name+'.json')).open('x') as f:json.dump(record,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
        print(name,'CAPTURED',result['error'] or '')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();capture(a.output)
