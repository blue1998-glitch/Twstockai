"""Freeze exact new synthetic requests before implementing the coordinator."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
SEED=ROOT.parent/'quantity_replay_20261026/cases/prefix-only/input.json'


def load(p):return json.loads(p.read_text())


def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def info(p):
    raw=p.read_bytes();return dict(path=str(p.relative_to(PROJECT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def main():
    seed=load(SEED)
    for name in ('complete','incomplete','stopped'):
        replay=deepcopy(seed);f=replay['rounds'][0]
        replay['run_policy']['parameter_source']='EXPLICIT_EVALUATED_REPLAY_MILESTONE_FIXTURE_20261027'
        f['decision_template']['parameter_source']='EVALUATED_REPLAY_20261027_'+name
        if name!='stopped':
            f['selection']=dict(mode='HOLD',sell_A=None,additional_B=None,reason='EXPLICIT_SYNTHETIC_HOLD_FOR_PIPELINE_VALIDATION')
            f['orders']=[];f['tape']=[]
            f['observed_until']='2026-01-'+('12' if name=='complete' else '08')+'T16:00:00+08:00'
        else:f['decision_template']['assets']['B']['capital_eligibility']['status']='NOT_QUALIFIED'
        request=dict(schema='capital-evaluated-replay-input/0.1',synthetic=True,replay_input=replay,
            evaluation_at='2026-01-12T16:00:00+08:00')
        expected=dict(workflow_status='COMPLETED_EVALUATED' if name=='complete' else 'COMPLETED_EVALUATION_REFUSED',
            evaluation_status='EVALUATED' if name=='complete' else 'REFUSED',
            replay_status='STOPPED_CANDIDATE_GATE' if name=='stopped' else 'COMPLETED_PROVIDED_ROUNDS',
            reason=None if name=='complete' else ('INCOMPLETE_SAVED_RESULT' if name=='stopped' else 'LEDGER_RETURN_REFUSED'),
            replay_calls=1,evaluation_calls=1,execution_calls=0 if name=='stopped' else 1,
            terminal_accrual_equity='2230' if name=='complete' else None,
            accrual_growth='0' if name=='complete' else None,original_capital='2230',general_reserve='100')
        save(ROOT/'cases'/name/'input.json',request);save(ROOT/'cases'/name/'expected.json',expected)
    save(ROOT/'fault-specification.json',dict(stages=['request','replay','evaluation','result'],
        fault='PERSIST_THEN_LOSE_ACKNOWLEDGEMENT_IN_TEMP_COPY',expected_run='STOPPED_STORAGE',
        expected_storage='UNKNOWN',read_final='READ_ONLY',read_prefix='INCOMPLETE_SAVED_PREFIX',no_automatic_retry=True))
    save(ROOT/'read-counterexamples.json',[
        dict(name='missing-evaluation',mutation='REMOVE_TEMP_EVALUATION_FILE',expected='UNREADABLE'),
        dict(name='missing-result',mutation='REMOVE_TEMP_RESULT_FILE',expected='INCOMPLETE_SAVED_PREFIX'),
        dict(name='swapped-evaluation',mutation='COPY_DIFFERENT_OPERATION_EVALUATION_VALUE',expected='UNREADABLE'),
        dict(name='changed-summary',mutation='CHANGE_GROWTH_AND_RESIGN_RESULT_ONLY',expected='UNREADABLE'),
        dict(name='changed-replay',mutation='CHANGE_SAVED_REPLAY_STATUS_WITHOUT_REBINDING',expected='UNREADABLE'),
        dict(name='changed-time',mutation='CHANGE_EVALUATION_RECORD_TIME_AND_RESIGN',expected='UNREADABLE')])
    originals=[info(SEED)]+[info(ROOT.parent/n) for n in ('quantity_replay.py','account_metrics.py','account_metrics_read.py',
        'research_operation.py','lifecycle.py','core.py','execution.py','continuity.py')]+[info(PROJECT/'rotation_research'/n) for n in ('store.py','action_ledger.py')]
    save(ROOT/'intake.json',dict(baseline='11c914ad5235682822b2c22e07e00d092ab3b6de',originals=originals,
        ordering='CONTRACT_EXACT_INPUT_EXPECTED_AND_VERSIONS_BEFORE_IMPLEMENTATION',new_synthetic_RUN_cases=3,
        reused_old_fixture_as_seed=True,old_actuals_recomputed=False,new_prices_added=False))


if __name__=='__main__':main()
