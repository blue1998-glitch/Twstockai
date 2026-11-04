"""Bounded new synthetic replay, using only original decision/ledger/metrics."""
from pathlib import Path
from copy import deepcopy
import json, hashlib, shutil, subprocess, time, resource, sys
from .scenario import CAP,ROOT,OLD,declaration,seed,inputs,checked_request,original_case
from . import basket
from .compare import compare
from ..cash_action import evaluate
from ..cash_action_execution import execute
from ..core import fingerprint
from rotation_research.store import Journal

DELIVERY=ROOT/'deliveries/m1-cap1-full-cash-20261104'
MIN_FREE=512*1024**2;BUDGET=24*1024**2

def read(p):return json.loads(p.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,obj):
    body=obj if isinstance(obj,bytes) else (json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    if shutil.disk_usage(ROOT).free-len(body)<MIN_FREE:raise ValueError('CAPACITY_RESERVE_REFUSED')
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        if p.read_bytes()!=body:raise ValueError('IMMUTABLE_OUTPUT_CONFLICT:'+str(p))
    else:
        with p.open('xb') as f:f.write(body)
    return body


def preservation():
    prefix=['股票系統M1_v0_18/capital_research/cap1_20261104','deliveries/m1-cap1-20261104']
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only','-z','791b3875757702a4950dbd5ef66d181509876e24','--',*prefix]).decode().strip('\0').split('\0')
    paths += [str(p.relative_to(ROOT)) for folder in (CAP.parent,ROOT/'股票系統M1_v0_18/rotation_research') for p in folder.glob('*.py')]
    rows=[]
    for rel in sorted(paths):
        b=(ROOT/rel).read_bytes();old=subprocess.check_output(['git','show','791b3875757702a4950dbd5ef66d181509876e24:'+rel])
        if b!=old:raise ValueError('OLD_SOURCE_OR_PRODUCT_CHANGED:'+rel)
        rows.append(dict(path=rel,bytes=len(b),sha256=sha(b)))
    return dict(baseline='791b3875757702a4950dbd5ef66d181509876e24',files=rows)


def original_refusal():
    original=original_case();i=deepcopy(original['saved_result']['action_request']['action_input'])
    i['action']=dict(id='probe-original-C4',kind='EXIT_SELLABLE_HOLDING',code='C',sell_shares='4',reason='SYNTHETIC_REFUSAL_PROBE_NOT_ORDER')
    probe=evaluate(i)
    full=dict(schema=basket.INPUT,synthetic=True,id='old-full-probe',seed_action_input=deepcopy(original['saved_result']['action_request']['action_input']),sales={'B':'7','C':'2'})
    full['seed_action_input']['action'].update(kind='EXIT_SELLABLE_HOLDING',sell_shares='7')
    checked=basket.evaluate(full)
    return dict(schema='cap1-old-account-refusal/0.1',original_input_id=fingerprint(original),
        original_checkpoint_id=i['account_source']['expected_checkpoint_id'],original_C_rights=i['account_source']['checkpoint']['state']['row']['share_receivables'],
        original_cash_claims=i['account_source']['checkpoint']['state']['row']['cash_claims'],
        C4_probe_input=i,C4_probe_result=probe,basket_probe_input=full,basket_probe_result=checked,
        full_cash_metrics=None,original_execution_calls=0)


def build(label):
    start=time.monotonic();free=shutil.disk_usage(ROOT).free
    if free < MIN_FREE+BUDGET:raise ValueError('CAPACITY_BUDGET_REFUSED')
    write(CAP/'preserved-source-manifest.json',preservation())
    declared=declaration();write(CAP/'declaration.json',declared) # includes independent oracle, BEFORE replay
    write(CAP/'original-account-refusal.json',original_refusal())
    seed_request,seed_result=seed(declared);journal=Journal(CAP/'artifacts/journal')
    journal.save('new-settled-opening',dict(request=seed_request,result=seed_result))
    pairs=inputs(declared,seed_result);cases={}
    for name,(i,spec) in pairs.items():
        if name=='cash':
            request=dict(schema=basket.INPUT,synthetic=True,id='full-account-exit',seed_action_input=i,sales={'B':'7','C':'4'})
            checked=basket.evaluate(request);receipt=basket.execute(request,checked,spec)
            if receipt['status']!='REPLAYED_EXPLICIT_FULL_EXIT':raise ValueError(str(receipt['reasons']))
            case=dict(evaluation_at=declared['evaluation_at'],receipt=receipt)
        else:
            request=checked_request(i,spec);receipt=execute(request)
            if receipt['run']['status']!='REPLAYED_EXPLICIT_ACTION':raise ValueError(str(receipt['run']['reasons']))
            case=dict(schema='capital-action-account-metrics-input/0.1',synthetic=True,evaluation_at=declared['evaluation_at'],
                saved_result=dict(schema='capital-saved-action-source/0.1',action_request=request,action_result=receipt,continuation=None))
        journal.save('new-'+name,case);cases[name]=journal.read('new-'+name)['value']
    result=compare(cases)
    if result['status']!='COMPARABLE_SYNTHETIC_ACCOUNTS':raise ValueError(str(result['reasons']))
    for name,b in result['branches'].items():
        m=b['metrics'];oracle=declared['oracle']
        if (m['initial_capital']!=oracle['initial_equity'] or m['terminal_accrual_equity']!=oracle['equity_end'][name]
            or m['costs']['recorded_fill_fee_tax']!=oracle['fees'][name]
            or b['ledger']['daily'][-1]['settled_cash']!=oracle['cash_end'][name]):raise ValueError('FINANCIAL_ORACLE_MISMATCH:'+name+':'+str(m))
    if result['branches']['cash']['liquidation']['status']!='VERIFIED_ALL_CASH_SYNTHETIC':raise ValueError('FULL_ACCOUNT_NOT_SETTLED')
    write(CAP/'artifacts/comparison.json',result)
    report=dict(schema='cap1-cash-build/0.1',status='PASS',synthetic=True,new_path_count=4,seed_execution_calls=1,
        action_execution_calls=4,market_samples=0,seconds=round(time.monotonic()-start,3),max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        free_before=free,free_after=shutil.disk_usage(ROOT).free,old_preserved=preservation()==read(CAP/'preserved-source-manifest.json'))
    write(CAP/('build-'+label+'.json'),report);print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':build(sys.argv[1])
