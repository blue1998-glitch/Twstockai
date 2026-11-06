"""Freeze the saved settled resume checkpoint and explicit next-action cases."""
import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent.parent
REPO=PROJECT.parent


def load(p):return json.loads(p.read_text())
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:
        json.dump(value,f,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
        f.write('\n')
def info(p):
    b=p.read_bytes()
    return dict(path=str(p.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    from capital_research.core import fingerprint
    settled_path=PROJECT/'capital_research/standing_orders_20261028/controls/expired-to-Jan8/actual.json'
    active_path=PROJECT/'capital_research/standing_orders_20261028/controls/partial-fill-to-Jan8/actual.json'
    previous_path=PROJECT/'capital_research/cash_two_rounds_20261028/cases/independent-B20/input.json'
    sources=[settled_path,active_path,previous_path,
        PROJECT/'capital_research/standing_orders_20261028/CHANGE_MANIFEST.json',
        PROJECT/'capital_research/standing_orders_20261028/tests-final.log',
        PROJECT/'capital_research/standing_orders_20261028/after-final/test-evidence/context-and-purity.json',
        PROJECT/'capital_research/standing_orders_20261028/after-final/summary.json']
    protected=sources+[PROJECT/'capital_research'/n for n in (
        'cash_action.py','cash_action_execution.py','core.py','execution.py','execution_continuation.py','continuity.py',
        'quantity_candidates.py','eligibility.py','fact_lineage.py','close_clock.py','reassessment_history.py','order_review.py','transition_risk.py')]
    protected += [PROJECT/'rotation_research/action_ledger.py',PROJECT/'rotation_research/core.py']
    saved=load(settled_path);cp=saved['checkpoint'];state=cp['state'];ex=cp['execution_result']
    assert saved['status']=='CONTINUED_ORIGINAL_ORDERS' and not state['unfilled_orders'] and state['row']['purchase_payable']=='0'
    assert cp['state_id']==fingerprint(state) and ex['result_id']==fingerprint({k:v for k,v in ex.items() if k!='result_id'})
    old=load(previous_path);spec=deepcopy(old['execution_spec'])
    assert spec['origin_ledger']==cp['origin_ledger_input'] and spec['ledger_close_proof']==ex['ledger_close_proof']
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        protected=[info(p) for p in protected],original_resume_mode='READ_SAVED_ONLY',original_resume_run_calls=0,
        old_two_round_producer_calls=0,new_quotes=0,new_calendar_rows=0))
    save(ROOT/'original-binding.json',dict(saved_resume=info(settled_path),checkpoint_id=cp['checkpoint_id'],state_id=cp['state_id'],
        origin_id=cp['integrity']['origin_ledger_input_id'],latest=ex['latest_decision_id'],origin_capital=state['origin_initial_capital'],
        row=state['row'],reserve=state['general_reserved_cash'],order_states=state['order_states'],tokens=state['reviewed_evidence_tokens']))
    positive=deepcopy(old['action_input']);positive['account_source']=dict(kind='CHECKPOINT',checkpoint=deepcopy(cp),
        expected_checkpoint_id=cp['checkpoint_id'],expected_latest_decision_id=ex['latest_decision_id'])
    cases=[]
    def add(name,r,e,orders=None):
        save(ROOT/'cases'/name/'action-input.json',r)
        external=deepcopy(spec)
        if orders is not None:external['orders']=orders
        else:external['orders'][0]['shares']=r['action']['additional_shares']
        save(ROOT/'cases'/name/'execution-spec.json',external)
        save(ROOT/'cases'/name/'expected.json',e);cases.append(name)
    hold=deepcopy(positive);hold['action']=dict(id='post-resume-HOLD',kind='HOLD',code=None,additional_shares='0',trigger_ids=[],batch_context=None)
    add('hold',hold,dict(checked_status='CURRENTLY_FEASIBLE',run_status='REPLAYED_EXPLICIT_ACTION',simulate_calls=1,
        new_fill_shares='0',new_fill_count=0,final_cash='938.860',final_B='7',final_C='4',final_nav='1178.860'),orders=[])
    add('independent-B20',positive,dict(checked_status='CURRENTLY_FEASIBLE',run_status='REPLAYED_EXPLICIT_ACTION',simulate_calls=1,
        new_fill_shares='20',new_fill_count=1,final_cash='537.460',final_B='27',final_C='4',final_nav='1177.460',
        trade_day_cash='858.860',trade_day_payable='401.400',trade_day_available='457.460'))
    old_trigger=deepcopy(positive);old_trigger['action']['trigger_ids']=['B-event']
    add('old-trigger',old_trigger,dict(checked_status='REJECTED',run_status='STOPPED_ACTION_GATE',simulate_calls=0,reason='NO_NEW_INDEPENDENT_TRIGGER'))
    first=deepcopy(positive);first['action']['batch_context']['phase']='FIRST_ENTRY';first['action']['trigger_ids']=[]
    add('false-first-entry',first,dict(checked_status='REJECTED',run_status='STOPPED_ACTION_GATE',simulate_calls=0,reason='FIRST_ENTRY_CONTRADICTS_B_EPISODE_HISTORY'))
    reserve=deepcopy(positive);reserve['action']['additional_shares']='40'
    add('reserve-not-spendable',reserve,dict(checked_status='REJECTED',run_status='STOPPED_ACTION_GATE',simulate_calls=0,
        reason='JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS',required_cost='801.800',settled_cash='858.860',spendable='758.860',
        parameter_role='EXPLICIT_SYNTHETIC_BOUNDARY_ONLY_NOT_USER_QUANTITY'))
    wrong=deepcopy(positive);wrong['account_source']['expected_latest_decision_id']='sha256:not-the-resumed-latest'
    add('wrong-latest',wrong,dict(checked_status='INPUT_ERROR',run_status='STOPPED_ACTION_GATE',simulate_calls=0,reason='EXACT_LATEST_PREDECESSOR_REQUIRED'))
    active=deepcopy(positive);active_cp=load(active_path)['checkpoint']
    active['account_source'].update(checkpoint=active_cp,expected_checkpoint_id=active_cp['checkpoint_id'],expected_latest_decision_id=active_cp['execution_result']['latest_decision_id'])
    add('still-active',active,dict(checked_status='NOT_IMPLEMENTED',run_status='STOPPED_ACTION_GATE',simulate_calls=0,reason='ACTIVE_ORDER_CONTINUATION_NOT_IMPLEMENTED'))
    save(ROOT/'case-index.json',dict(cases=cases,mutually_exclusive=True,original_resume_run_calls=0,new_quotes=0,new_calendar_rows=0,
        expected_product_module_changes=0,market_samples=0,old_suites_run=0,entrypoints=['cash_action.evaluate','cash_action_execution.execute']))
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='frozen.json']))
    print('Frozen seven inputs and independent expected results; old resume/producer and numeric RUN calls 0')


if __name__=='__main__':main()
