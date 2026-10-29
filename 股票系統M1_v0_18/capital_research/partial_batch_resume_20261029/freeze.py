"""Freeze a new exogenous capacity model, never edit the old full-fill result."""
import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent.parent
REPO=PROJECT.parent


def load(p):return json.loads(p.read_text())
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:
        json.dump(x,f,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False);f.write('\n')
def info(p):
    b=p.read_bytes();return dict(path=str(p.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    from capital_research.core import fingerprint
    prior=PROJECT/'capital_research/settled_resume_action_20261029'
    result_path=prior/'actual/independent-B20/result.json'
    request_path=prior/'actual/independent-B20/execution-input.json'
    tape_path=PROJECT/'capital_research/cash_execution_20261028/cases/partial-7-active-13/input.json'
    protected=[result_path,request_path,tape_path,prior/'CHANGE_MANIFEST.json',prior/'tests-final.log',
        PROJECT/'capital_research/standing_orders_20261028/after-final/test-evidence/context-and-purity.json',
        *[PROJECT/'capital_research'/n for n in ('cash_action.py','cash_action_execution.py','execution.py','execution_continuation.py',
        'continuity.py','core.py','fact_lineage.py','eligibility.py','close_clock.py','reassessment_history.py','transition_risk.py','quantity_candidates.py')],
        PROJECT/'rotation_research/action_ledger.py']
    original=load(result_path)['run'];root=deepcopy(original['execution_job'])
    tape=load(tape_path)['execution_spec']['tape']
    assert len(root['tape'])==len(tape)
    assert [{k:v for k,v in o.items() if k!='capacity_shares'} for o in root['tape']]==[{k:v for k,v in o.items() if k!='capacity_shares'} for o in tape]
    assert root['ledger_close_proof']['closes']['2026-01-10']['as_of']=='2026-01-10T16:00:00+08:00'
    root['tape']=deepcopy(tape)
    prefix=deepcopy(root);prefix['observed_until']='2026-01-09T16:00:00+08:00'
    external=deepcopy(load(request_path));external['execution_spec'].update(tape=deepcopy(tape),observed_until=prefix['observed_until'])
    coverage=[]
    for row in root['ledger_input']['calendar']:
        if row['trading'] and root['decision_input']['data_cutoff'][:10]<row['date']<=root['observed_until'][:10]:
            coverage.append(dict(date=row['date'],source_ids=['fixture'],qualification='EXPLICIT_SYNTHETIC_COMPLETE_EXECUTION_OPPORTUNITIES',
                observation_ids=[fingerprint(o) for o in tape if o['at'][:10]==row['date']],no_other_execution_opportunities=True))
    path=dict(schema='capital-synthetic-order-path/0.1',version='frozen-synthetic-path/0.1',
        qualification='EXPLICIT_SYNTHETIC_COMPLETE_PATH_NOT_MARKET_PROOF',source_ids=['fixture'],
        origin_ledger_input_id=fingerprint(root['ledger_input']),start_at=root['decision_input']['data_cutoff'],
        through_at=root['observed_until'],observations=deepcopy(tape),session_coverage=coverage)
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        protected=[info(p) for p in protected],original_saved_resume_runs=0,old_producer_runs=0,
        original_result_mode='READ_ONLY_FULL_FILL_REMAINS_IMMUTABLE',new_quotes=0,new_calendar_rows=0))
    save(ROOT/'root-input.json',root);save(ROOT/'prefix-input.json',prefix);save(ROOT/'prefix-action-input.json',external);save(ROOT/'path.json',path)
    save(ROOT/'expected.json',dict(prefix_cash='858.860',prefix_payable='141.140',prefix_available='717.720',prefix_B='14',prefix_C='2',
        remaining='13',reserved='261.65039',general_reserve='100',origin_capital='1180',tokens=12,
        final_cash='797.720',final_B='14',final_C='4',final_payable='0',final_nav='1177.720',final_status='EXPIRED_UNFILLED',
        tail_fills=0,new_decisions=0,original_expired_remaining='13',full_execution_equal=True,every_observation_equal=True,every_daily_row_equal=True))
    save(ROOT/'negative-specifications.json',dict(
        wrong_latest='EXACT_LATEST_PREDECESSOR_REQUIRED',
        dropped_parent='Opening ledger/cutoff mismatch',
        different_capacity_path='PREFIX_EXECUTION_MISMATCH',
        duplicate_fill='Execution fingerprint conflict',
        missing_empty_session='COMPLETE_SESSION_COVERAGE_REQUIRED'))
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='frozen.json']))
    print('Frozen root/prefix/action/path and independent expectations; numeric RUNs0')


if __name__=='__main__':main()
