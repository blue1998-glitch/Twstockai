"""Exact source-bound structural counterexamples, never account-engine outputs."""
from copy import deepcopy
import hashlib
from capital_research.lifecycle import _fp
from .prepare import PROJECT,load


def resign(e,cp):
    e['result_id']=_fp({k:v for k,v in e.items() if k!='result_id'})
    cp['execution_result']=deepcopy(e);cp['state']['row']=deepcopy(e['ledger']['daily'][-1])
    cp['state']['reviewed_evidence_tokens']=deepcopy(e['reviewed_evidence_tokens'])
    cp['state_id']=_fp(cp['state']);cp['checkpoint_id']=_fp(dict(schema=cp['schema'],state_id=cp['state_id']))
    cp['integrity']['execution_result_id']=e['result_id']


def resolve(spec):
    path=PROJECT/spec['source']['path'];raw=path.read_bytes()
    assert len(raw)==spec['source']['bytes'] and hashlib.sha256(raw).hexdigest()==spec['source']['sha256']
    saved=load(path);recipe=spec['recipe'];at=spec['evaluation_at']
    if recipe=='INTENT_ONLY':saved=dict(schema='capital-research-choice/0.1',synthetic=True)
    elif recipe=='EARLY_EVALUATION':at='2026-01-12T15:59:59+08:00'
    elif recipe!='NONE':
        r=saved['replay'];frame=r['rounds'][-1];e=frame['execution'];cp=frame['checkpoint'];rows=e['ledger']['daily']
        if recipe=='MISSING_NAV':rows[4]['net_accrual_equity']=None
        elif recipe=='MISSING_MARK':rows[4]['marks']['A']['value']=None
        elif recipe=='MISSING_DAY':rows.pop(4)
        elif recipe=='NONPOSITIVE':rows[4]['net_accrual_equity']='0'
        elif recipe=='CHANGED_PREFIX':rows[1]['net_accrual_equity']='2225'
        elif recipe=='CHANGED_CAPITAL':cp['state']['origin_initial_capital']='2231'
        elif recipe=='MISSING_TOKEN':e['reviewed_evidence_tokens'].pop()
        elif recipe=='EXTERNAL_FLOW':cp['state']['external_flow']='1'
        elif recipe=='UNKNOWN_CLAIMS':rows[4]['cash_claims']=None
        elif recipe=='MISMATCHED_MARK':rows[4]['marks']['A']['value']='999'
        elif recipe=='STALE_TRADING_MARK':
            rows[4]['marks']['A'].update(source_date=rows[3]['date'],carried_nontrading_mark=True)
        elif recipe=='REAL_SOURCE':
            for f in r['rounds']:
                f['checkpoint']['origin_ledger_input']['sources']['fixture']['kind']='OFFICIAL_ARCHIVE'
        else:raise ValueError('UNKNOWN_EXPLICIT_FIXTURE_RECIPE:'+recipe)
        resign(e,cp);r['last_execution']=deepcopy(e);r['historical_checkpoint']=deepcopy(cp)
    return dict(schema='capital-account-metrics-input/0.1',synthetic=True,evaluation_at=at,saved_result=saved)
