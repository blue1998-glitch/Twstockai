"""Explicit IO for new review evidence; never writes the frozen 20261024 tree."""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
from graph_core.core import fingerprint
from capital_research.core import decide
from capital_research.execution import simulate
from capital_research.trend_fixtures import path_fixture,PATHS
from capital_research.trend_replay import run_fixture
from .reproduce import cases
from .fixtures import reauthorized_job,continued_job


def write_new(path,value):
    path=Path(path);body=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=body:raise ValueError('Existing review evidence differs; choose a new output: '+str(path))
        return
    with path.open('xb') as f:f.write(body)


def build(output):
    out=Path(output)
    if 'validation_20261024' in out.parts:raise ValueError('Frozen evidence tree cannot be a new output destination')
    sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('capital_research').glob('*.py')}
    for name,value in cases():
        write_new(out/'after'/f'{name}.json',dict(synthetic=True,current_source_sha256=sources,**value))
    j,cp,new=reauthorized_job();result=simulate(j)
    assert any(f['code']=='B' and f['decision_date']=='2026-01-08' for f in result['fills'])
    write_new(out/'valid-reassessment.json',dict(input=j,checkpoint=cp,new_decision=new,execution=result))
    first,prior,second=continued_job();continued=simulate(second)
    assert continued['ledger']['initial_equity']=='2000' and len(continued['new_fill_ids'])==1
    write_new(out/'continuous-account.json',dict(first_input=first,first_execution=prior,next_input=second,next_execution=continued))
    summary={};prefix_ids=set()
    for name in PATHS:
        f=path_fixture(name);r=run_fixture(f)
        assert all(v['status']=='COMPLETED_SYNTHETIC_SEQUENCE' for v in r['policy_results'].values())
        prefix_ids.update(v['first_decision_id'] for v in r['policy_results'].values())
        write_new(out/'paths'/name/'fixture.json',f);write_new(out/'paths'/name/'competition.json',r)
        summary[name]={p:dict(status=v['status'],metrics={k:x for k,x in v['metrics'].items() if k!='curve'},
            observed_risk_breach_count=v['observed_risk_breach_count'],qualification=v['qualification']) for p,v in r['policy_results'].items()}
    assert len(prefix_ids)==1
    write_new(out/'summary.json',dict(synthetic=True,path_count=9,policies_per_path=5,independent_market_samples=0,
        common_initial_decision_id=next(iter(prefix_ids)),results=summary,ranking=None,
        qualifications=dict(data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,
                            policy_authorized=False,live_execution_authorized=False),R2_F='NOT_IMPLEMENTED',
        risk_matching='SHARED_HARD_CAPS; MATCHED_REALIZED_EXPOSURE_CONTROLS_NOT_IMPLEMENTED',
        old_46_tests_not_rerun_as_a_suite=True,old_window_producer_runs=0))
    write_new(out/'source-versions.json',dict(capital_decision='0.2',capital_execution='0.2',trend='0.1',
        original_action_ledger='0.1_UNCHANGED',sources=sources,git_commit='UNCOMMITTED_LOCAL_REVIEW_BASE_6be4333d'))
    return dict(status='NEW_REVIEW_EVIDENCE_SAVED',paths=9,policy_sequences=45,
                initial_decision_ids=len(prefix_ids),market_validation=False,old_evidence_overwritten=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    print(json.dumps(build(a.output),ensure_ascii=False,sort_keys=True))


if __name__=='__main__':main()
