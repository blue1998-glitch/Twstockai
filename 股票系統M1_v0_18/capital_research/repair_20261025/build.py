"""Create-only repair evidence. Does not run old producers or mutate old files."""
from copy import deepcopy
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import json
import subprocess
import sys
from capital_research.core import decide,resume_decision,VERSION as DECISION_VERSION
from capital_research.execution import simulate,VERSION as EXECUTION_VERSION
from capital_research.continuity import make_checkpoint,CHECKPOINT
from capital_research.trend import VERSION as TREND_VERSION
from capital_research.trend_fixtures import path_fixture
from capital_research.trend_replay import run_fixture
from .fixtures import execution_job,prefix,advance,reassessed_job,continuation_job
from .reproduce import capture


def write_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    body=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    with path.open('xb') as f:f.write(body)


def build(output):
    out=Path(output)
    if any(x in out.parts for x in ('review_20261025','validation_20261024','baseline_0_2')):
        raise ValueError('Frozen evidence cannot be a repair output destination')
    out.mkdir(parents=True,exist_ok=False)
    capture(out/'after')
    j,old,new=reassessed_job(extend=True);first=simulate(j)
    second=continuation_job(j,first,new);last=simulate(second)
    assert first['fills']==last['fills'][:len(first['fills'])] and last['ledger']['initial_equity']=='2000'
    write_new(out/'reassessment-and-next-round.json',dict(first_input=j,old_decision=old,new_decision=new,
        first_execution=first,next_input=second,next_execution=last))
    j=prefix(execution_job());r=simulate(j);cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
    fresh,ids=advance(j['decision_input'],cp);reviewed=resume_decision(decide(j['decision_input']),fresh,checkpoint=cp,cancelled_order_ids=ids)
    second=continuation_job(j,r,decide(j['decision_input']),plan='B-full',fresh=fresh,ids=ids)
    write_new(out/'old-facts-current-review.json',dict(first_input=j,first_execution=r,checkpoint=cp,
        current_input=fresh,current_decision=reviewed,next_input=second,next_execution=simulate(second),
        evidence_bytes_equal=j['decision_input']['assets']['B']['evidence']==fresh['assets']['B']['evidence']))
    negative=path_fixture('exit_repair_reentry');positive=deepcopy(negative)
    for row in (positive['frames'][3],positive['trend_input']['records'][3]):row['new_capital_evidence_qualified']=True
    competitions={}
    for label,fixture in [('not-qualified',negative),('qualified',positive)]:
        result=run_fixture(fixture);competitions[label]=result
        write_new(out/'trend-reentry'/f'{label}-fixture.json',fixture)
        write_new(out/'trend-reentry'/f'{label}-competition.json',result)
    a=competitions['not-qualified']['policy_results']['structure_hold']['rounds'][3]
    b=competitions['qualified']['policy_results']['structure_hold']['rounds'][3]
    assert not a['selected_policy_proposal']['feasible'] and not a['new_fill_ids']
    assert b['selected_policy_proposal']['feasible'] and b['new_fill_ids']
    assert competitions['not-qualified']['common_market_path_id']==competitions['qualified']['common_market_path_id']
    # This is a read of an old saved result, not a regeneration of its old policy.
    old_dir=Path('capital_research/validation_20261024')
    command=[sys.executable,'-m','capital_research.cli','READ','--store',str(old_dir/'cli-records'),'--id','execution-v1']
    read=subprocess.run(command,capture_output=True)
    with (out/'old-READ.log').open('xb') as f:f.write(read.stdout)
    read_evidence=dict(command=command,exit_code=read.returncode,
        exact_saved_stdout=read.stdout==(old_dir/'cli-READ.log').read_bytes(),stderr=read.stderr.decode(),numeric_recomputation=False)
    write_new(out/'old-READ-verification.json',read_evidence)
    assert read.returncode==0 and read_evidence['exact_saved_stdout']
    old_path=Path('capital_research/review_20261025/artifacts/paths/exit_repair_reentry/competition.json')
    old_result=json.loads(old_path.read_text())['policy_results']['structure_hold']['rounds'][3]
    write_new(out/'original-saved-reentry-reference.json',dict(role='PREVIOUSLY_SAVED_V02_NOT_RERUN',
        path=str(old_path),sha256=hashlib.sha256(old_path.read_bytes()).hexdigest(),
        pointer='policy_results.structure_hold.rounds[3]',record=old_result))
    after={f.stem:json.loads(f.read_text()) for f in (out/'after').glob('*.json')}
    assert all(x['error'] is None for x in after.values())
    aa=after['latest-predecessor']['value']['actual']
    assert aa['latest']['error'] is None and aa['stale']['error']
    partial=after['partial-cancel-chain']['value']['actual'];row=partial['next_execution']['ledger']['daily'][-1]
    summary=dict(synthetic=True,generated_at=datetime.now(timezone.utc).isoformat(),
        before_cases=7,after_cases=7,reproduced_defects=5,
        partial_cancel_and_expiry='SUPPORTED_ALREADY_IN_V02; ADDITIONAL_DIRECTED_EVIDENCE_NOT_A_NEW_ACCOUNTING_IMPLEMENTATION',
        entry_gate=dict(negative_feasible=a['selected_policy_proposal']['feasible'],negative_new_fill_ids=a['new_fill_ids'],
            positive_feasible=b['selected_policy_proposal']['feasible'],positive_new_fill_ids=b['new_fill_ids']),
        latest_predecessor=dict(latest_accepted=aa['latest']['error'] is None,old_predecessor_error=aa['stale']['error']),
        partial_account=dict(root_capital=partial['next_execution']['ledger']['initial_equity'],terminal_settled_cash=row['settled_cash'],
            terminal_shares=row['shares'],terminal_equity=row['net_accrual_equity'],general_reserved_cash='100',
            expected_fill_fee_tax='9',expected_effective_price_slippage='1.28',external_flows='0'),
        trend_variants=2,market_paths_in_trend_probe=1,synthetic_policy_sequences=10,rounds_per_sequence=5,
        independent_market_samples=0,ranking=None,R2_F='NOT_IMPLEMENTED',
        qualifications=dict(data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,policy_authorized=False,live_execution_authorized=False))
    write_new(out/'summary.json',summary)
    sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('capital_research').glob('*.py')}
    sources.update({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('capital_research/repair_20261025').glob('*.py')})
    write_new(out/'source-versions.json',dict(decision=DECISION_VERSION,execution=EXECUTION_VERSION,
        checkpoint=CHECKPOINT,trend=TREND_VERSION,sources=sources,
        original_action_ledger_sha256=hashlib.sha256(Path('rotation_research/action_ledger.py').read_bytes()).hexdigest(),
        git_base='6be4333d490bcccfe952c7606dffb802b76cdd5c',uncommitted=True))
    return dict(status='NEW_REPAIR_ARTIFACTS_SAVED',before_cases=7,after_cases=7,old_READ_exact=True,market_validation=False)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    print(json.dumps(build(a.output),ensure_ascii=False,sort_keys=True))
