"""Finite synthetic replay using existing cash-action/execution/metrics/Journal.

No market IO, no new accounting formula. Outputs only into a new CAP1 folder.
Run as a module from the repository root with the original v0_18 on PYTHONPATH.
"""
from copy import deepcopy
from pathlib import Path
import hashlib, json, shutil, zipfile, argparse, time
from ..cash_action import evaluate
from ..cash_action_execution import execute
from ..core import fingerprint
from ..action_account_metrics import evaluate_saved
from rotation_research.store import Journal
from .compare import compare
from .render import render

ROOT = Path(__file__).resolve().parents[3]
CAP = Path(__file__).resolve().parent
DELIVERY = ROOT/'deliveries/m1-cap1-20261104'
OLD = CAP.parent/'action_metrics_20261029'
MIN_FREE = 512*1024**2
BUDGET = 24*1024**2


def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_bytes())
def write(p, b):
    if not isinstance(b, bytes): b=(json.dumps(b,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    if shutil.disk_usage(ROOT).free-len(b) < MIN_FREE: raise ValueError('CAPACITY_RESERVE_REFUSED')
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        if p.read_bytes()!=b: raise ValueError('IMMUTABLE_OUTPUT_CONFLICT:'+str(p))
    else:
        with p.open('xb') as f:f.write(b)
    return b


def source_manifest():
    paths=[OLD/'cases'/n/'input.json' for n in ('v01-hold','reduce-B3','exit-B7')]
    paths += [OLD/'final-corrected'/n/'actual.json' for n in ('v01-hold','reduce-B3','exit-B7')]
    paths += [CAP.parent/(n+'.py') for n in ('cash_action','cash_action_execution','account_metrics','action_account_metrics','saved_action_source','core','execution','continuity','lifecycle')]
    paths += [ROOT/'股票系統M1_v0_18/rotation_research'/n for n in ('store.py','action_ledger.py')]
    return dict(schema='cap1-frozen-source-manifest/0.1', baseline_commit='c7b2c2c5782bba74711645c84d15f6f07b5c5c4f',
        recipe='Reuse reduce-B3 account/template/policy/tape for all actions; new HOLD 0.1 with empty orders. Reduce/exit unchanged. No invented observations or quotes.',
        oracles={'hold_equity':'1178.860','reduce_equity':'1176.800','exit_B_equity':'1176.720',
                 'fees':['1','3','3'],'end_cash':['938.860','996.800','1076.720'],
                 'C_retained_all_branches':'4','initial_capital':'1180','dates':8},
        files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in paths])


def prepare_inputs():
    reduce=read(OLD/'cases/reduce-B3/input.json')
    exit_b=read(OLD/'cases/exit-B7/input.json')
    hold=deepcopy(reduce);saved=hold['saved_result'];r=saved['action_request']
    old=read(OLD/'cases/v01-hold/input.json')['saved_result']['action_request']
    r['schema']=old['schema'];r['action_input']['schema']=old['action_input']['schema']
    r['action_input']['action']=deepcopy(old['action_input']['action'])
    r['execution_spec']['orders']=[]
    checked=evaluate(r['action_input'])
    if checked['research']['status']!='CURRENTLY_FEASIBLE':raise ValueError(str(checked['research']))
    r['checked_action']=checked;r['expected_checked_action_id']=fingerprint(checked)
    # This new source has a different information set from the old HOLD; replay.
    saved['action_result']=None
    return dict(hold=hold,reduce=reduce,exit_b=exit_b)


def build():
    before=shutil.disk_usage(ROOT).free;t=time.monotonic()
    if before < MIN_FREE+BUDGET:raise ValueError('CAPACITY_BUDGET_REFUSED')
    # Persist input-source identities and independent old oracles BEFORE execution.
    freeze=source_manifest();write(CAP/'source-manifest.json',freeze)
    cases=prepare_inputs(); journal=Journal(CAP/'artifacts/journal')
    evidence=[]
    for name,case in cases.items():
        r=case['saved_result']['action_request'];old=case['saved_result']['action_result']
        actual=execute(r)
        if actual['run']['status']!='REPLAYED_EXPLICIT_ACTION':raise ValueError(str(actual['run']))
        if old is not None and actual!=old:raise ValueError('SAVED_REPLAY_CHANGED:'+name)
        case['saved_result']['action_result']=actual
        m=evaluate_saved(case)
        if m['status']!='EVALUATED':raise ValueError(str(m['reasons']))
        original_name={'hold':'v01-hold','reduce':'reduce-B3','exit_b':'exit-B7'}[name]
        old_m=read(OLD/'final-corrected'/original_name/'actual.json')
        for key in ('statistics','initial_capital','terminal_accrual_equity','costs'):
            if m[key]!=old_m[key]:raise ValueError('ORIGINAL_FINANCIAL_ORACLE_CHANGED:'+name+':'+key)
        record=journal.save('cap1-'+name,case)
        if journal.read('cap1-'+name)!=record:raise ValueError('JOURNAL_READBACK_CONFLICT')
        evidence.append(dict(branch=name,old_replay_exact=old is not None,
            new_same_information_hold=old is None,metrics_match_old_financial_fields=True,
            input_id=fingerprint(case),execution_id=actual['run']['execution']['result_id']))
    out=compare(cases)
    if out['status']!='COMPARABLE_SYNTHETIC_ACCOUNTS':raise ValueError(str(out['reasons']))
    write(CAP/'artifacts/comparison.json',out)
    from .package import package
    packaged=package()
    receipts=dict(schema='cap1-build-verification/0.1',engine_calls=3,metrics_reads=3,
        source_checks=evidence,synthetic=True,market_samples=0,
        full_cash_exit='NOT_IMPLEMENTED_MISSING_ALL_ASSET_EXECUTION_AND_RIGHTS_EVIDENCE',
        raw_source_manifest_unchanged=freeze==source_manifest(),html_bytes=packaged['files'][0]['bytes'],
        zip_bytes=packaged['files'][1]['bytes'],minimum_free_bytes=MIN_FREE)
    write(CAP/'replay-verification.json',receipts)
    print(json.dumps(dict(html_bytes=packaged['files'][0]['bytes'],zip_bytes=packaged['files'][1]['bytes'],
        elapsed_seconds=round(time.monotonic()-t,3),free_before=before,
        free_after=shutil.disk_usage(ROOT).free,branches=list(out['branches'])),ensure_ascii=False))

if __name__=='__main__':build()
