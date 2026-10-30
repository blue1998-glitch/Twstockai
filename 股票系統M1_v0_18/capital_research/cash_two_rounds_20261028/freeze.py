"""Reuse first saved result; freeze six mutually exclusive second-round inputs."""
import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent.parent
REPO=PROJECT.parent
OLD=ROOT.parent/'cash_execution_20261028'


def load(p):return json.loads(p.read_text())
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False);f.write('\n')
def info(p):
    b=p.read_bytes();return dict(path=str(p.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    from capital_research.core import fingerprint
    from capital_research.cash_action import evaluate
    first_input=OLD/'cases/opening-B20/input.json';first_actual=OLD/'actual/opening-B20/result.json';tape_input=OLD/'cases/exited-A-buy-B20/input.json'
    original=load(first_input);first=load(first_actual);cp=first['run']['checkpoint'];execution=cp['execution_result']
    assert first['run']['status']=='REPLAYED_EXPLICIT_ACTION'
    assert not cp['state']['unfilled_orders'] and cp['state']['row']['purchase_payable']=='0'
    assert execution['result_id']==fingerprint({k:v for k,v in execution.items() if k!='result_id'})
    assert cp['state_id']==fingerprint(cp['state'])
    protected=[first_input,first_actual,tape_input,OLD/'source-versions.json',OLD/'CHANGE_MANIFEST.json',
        *[PROJECT/'capital_research'/name for name in ('cash_action.py','cash_action_execution.py','core.py','execution.py','continuity.py',
           'quantity_candidates.py','eligibility.py','fact_lineage.py','close_clock.py','reassessment_history.py','transition_risk.py')],
        PROJECT/'rotation_research/action_ledger.py']
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        protected=[info(p) for p in protected],first_round=dict(input=info(first_input),actual=info(first_actual),mode='READ_SAVED_ONLY',execution_calls_this_round=0),
        market_tape_source=info(tape_input),new_quotes=0,new_calendar_rows=0,first_checkpoint_id=cp['checkpoint_id'],
        original_window=[cp['origin_ledger_input']['start'],cp['origin_ledger_input']['end']]))
    save(ROOT/'first-round-binding.json',dict(original_input=info(first_input),original_actual=info(first_actual),
        original_checked_action_id=original['expected_checked_action_id'],execution_result_id=execution['result_id'],
        checkpoint_id=cp['checkpoint_id'],state_id=cp['state_id'],latest=execution['latest_decision_id'],
        origin_ledger_input_id=cp['integrity']['origin_ledger_input_id'],origin_initial_capital=cp['state']['origin_initial_capital'],
        through_at=cp['state']['through_at'],row=cp['state']['row'],reserved_cash=cp['state']['general_reserved_cash'],
        reviewed_evidence_tokens=cp['state']['reviewed_evidence_tokens'],first_execution_this_round=False))
    data=deepcopy(original['action_input']['decision_template']);data['data_cutoff']=cp['state']['through_at'];data['decision_at']='2026-01-08T17:00:00+08:00'
    for code,asset in data['assets'].items():
        asset['marks']=[dict(asset['marks'][0],price=cp['state']['row']['marks'][code]['value'],occurred_at=data['data_cutoff'],available_at=data['data_cutoff'])]
        asset['capital_eligibility'].update(assessed_at=data['decision_at'],available_at=data['decision_at'],data_cutoff=data['data_cutoff'])
    event=deepcopy(data['assets']['B']['evidence'][0]);event.update(id='B-step2',formation_id='B-step2-formation',volume_bar_id='B-step2-bar',event_id='B-step2-event',
        occurred_at=data['data_cutoff'],available_at=data['data_cutoff'])
    event['validity'].update(valid_from=data['data_cutoff'],available_at=data['data_cutoff'])
    data['assets']['B']['evidence'].append(event)
    action=deepcopy(original['action_input']['action']);action.update(id='second-explicit-B20',additional_shares='20',trigger_ids=['B-step2'])
    action['batch_context'].update(phase='ADDITIONAL_BATCH',available_at=data['decision_at'])
    policy=deepcopy(original['action_input']['policy']);policy['available_at']=data['decision_at']
    second=dict(schema='capital-cash-action-input/0.1',synthetic=True,decision_template=data,
        account_source=dict(kind='CHECKPOINT',checkpoint=deepcopy(cp),expected_checkpoint_id=cp['checkpoint_id'],expected_latest_decision_id=execution['latest_decision_id']),
        action=action,policy=policy)
    saved_tape=load(tape_input)['execution_spec'];spec=deepcopy(saved_tape)
    spec.update(id='second-round-same-account',origin_ledger=deepcopy(cp['origin_ledger_input']),ledger_close_proof=deepcopy(execution['ledger_close_proof']))
    spec['orders'][0]['id']='second-B-buy'
    cases=[]
    def add(name,action_input,expected):
        # Save exact input and independent oracle before producing a new receipt.
        save(ROOT/'cases'/name/'action-input.json',action_input);save(ROOT/'cases'/name/'expected.json',expected)
        checked=evaluate(action_input);save(ROOT/'cases'/name/'checked-action.json',checked)
        external=deepcopy(spec);external['orders'][0]['shares']=action_input['action']['additional_shares']
        request=dict(schema='capital-cash-action-execution-input/0.1',synthetic=True,action_input=action_input,
            checked_action=checked,expected_checked_action_id=fingerprint(checked),execution_spec=external)
        save(ROOT/'cases'/name/'input.json',request);cases.append(name)
    add('independent-B20',second,dict(checked_status='CURRENTLY_FEASIBLE',run_status='REPLAYED_EXPLICIT_ACTION',simulate_calls=1,
        original_capital='1180',current_nav_before_second='1178.600',incoming_cash='598.600',reserve='100',
        trade_day_settled_cash='598.600',trade_day_payable='401.400',trade_day_available='197.200',
        final_cash='277.200',final_B='40',final_C='4',final_nav='1177.200',new_fill_shares='20',new_fill_count=1,
        reviewed_tokens=12,reviewed_old_tokens=9,post_settlement_payable='0'))
    old=deepcopy(second);old['action']['trigger_ids']=['B-event']
    add('reused-first-trigger',old,dict(checked_status='REJECTED',run_status='STOPPED_ACTION_GATE',simulate_calls=0,reason='NO_NEW_INDEPENDENT_TRIGGER'))
    first=deepcopy(second);first['action']['batch_context']['phase']='FIRST_ENTRY';first['action']['trigger_ids']=[]
    add('false-first-entry',first,dict(checked_status='REJECTED',run_status='STOPPED_ACTION_GATE',simulate_calls=0,reason='FIRST_ENTRY_CONTRADICTS_B_EPISODE_HISTORY',core_snapshot_feasible=True))
    reserved=deepcopy(second);reserved['action']['additional_shares']='25'
    add('reserve-not-reused',reserved,dict(checked_status='REJECTED',run_status='STOPPED_ACTION_GATE',simulate_calls=0,
        reason='JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS',required_cost='501.5',spendable_after_reserve='498.6'))
    receivable=deepcopy(second);receivable['action']['additional_shares']='30'
    add('receivable-not-spendable',receivable,dict(checked_status='REJECTED',run_status='STOPPED_ACTION_GATE',simulate_calls=0,
        reason='JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS',required_cost='601.6',settled_cash='598.6',unsettled_cash_claim='80'))
    wrong=deepcopy(second);wrong['account_source']['expected_latest_decision_id']='sha256:not-the-first-round-latest'
    add('wrong-first-predecessor',wrong,dict(checked_status='INPUT_ERROR',run_status='STOPPED_ACTION_GATE',simulate_calls=0,reason='EXACT_LATEST_PREDECESSOR_REQUIRED'))
    save(ROOT/'case-index.json',dict(cases=cases,mutually_exclusive_second_rounds=True,first_round_mode='SAVED_READ_ONLY',
        original_ledger_window_unchanged=True,existing_entrypoints=['cash_action.evaluate','cash_action_execution.execute'],
        no_new_production_code_expected=True,market_samples=0,old_suite_runs=0,new_quotes=0,new_calendar_rows=0))
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='frozen.json']))
    print('Frozen six new second-round requests and oracles; first round READ only; simulate calls 0')


if __name__=='__main__':main()
