"""Freeze sell-specific contracts, original sources and manual oracles before code."""
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
    from capital_research.cash_action import evaluate
    prior=PROJECT/'capital_research/settled_resume_action_20261029'
    base=load(prior/'actual/independent-B20/execution-input.json')
    cp=base['action_input']['account_source']['checkpoint']
    tape_source=PROJECT/'capital_research/cash_execution_20261028/cases/partial-7-active-13/input.json'
    full20_source=PROJECT/'capital_research/cash_execution_20261028/actual/opening-B20/result.json'
    protected=[prior/'actual/independent-B20/execution-input.json',prior/'actual/independent-B20/result.json',tape_source,full20_source,
        PROJECT/'capital_research/standing_orders_20261028/controls/partial-fill-to-Jan8/actual.json',
        PROJECT/'capital_research/standing_orders_20261028/before/payable-only/checkpoint.json',
        *[PROJECT/'capital_research'/n for n in ('core.py','continuity.py','execution.py','execution_continuation.py','quantity_candidates.py',
         'fact_lineage.py','eligibility.py','reassessment_history.py','close_clock.py','transition_risk.py')],PROJECT/'rotation_research/action_ledger.py']
    originals=[]
    for name in ('cash_action.py','cash_action_execution.py'):
        p=PROJECT/'capital_research'/name;q=ROOT/'baseline'/name;q.parent.mkdir(parents=True,exist_ok=True)
        with q.open('x') as f:f.write(p.read_text())
        originals.append(dict(current=info(p),archived=info(q)))
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        changing_sources=originals,protected=[info(p) for p in protected],original_results_mode='READ_ONLY',new_quotes=0,new_calendar_rows=0))
    template=deepcopy(base['action_input']['decision_template'])
    template['assets']['B']['evidence']=[e for e in template['assets']['B']['evidence'] if e['id']!='B-step2']
    action_input=dict(schema='capital-cash-action-input/0.2',synthetic=True,decision_template=template,
        account_source=deepcopy(base['action_input']['account_source']),policy=deepcopy(base['action_input']['policy']),
        action=dict(id='sell-B-explicit',kind='REDUCE_HOLDING',code='B',sell_shares='3',reason='EXPLICIT_SYNTHETIC_REDUCTION_NOT_USER_RULE'))
    spec=deepcopy(base['execution_spec']);spec['id']='explicit-synthetic-sell'
    spec['orders'][0].update(id='sell-B-explicit',side='SELL',shares='3',limit_price='19.98')
    cases=[]
    def add(name,r,e,s=None,edit=None):
        save(ROOT/'cases'/name/'action-input.json',r);save(ROOT/'cases'/name/'execution-spec.json',s if s is not None else spec)
        save(ROOT/'cases'/name/'expected.json',e)
        if edit:save(ROOT/'cases'/name/'execution-edit.json',edit)
        cases.append(name)
    def ok(**kw):return dict(checked_status='CURRENTLY_FEASIBLE',run_status='REPLAYED_EXPLICIT_ACTION',simulate_calls=1,**kw)
    def blocked(reason,status='INPUT_ERROR'):return dict(checked_status=status,run_status='STOPPED_ACTION_GATE',simulate_calls=0,reason=reason)
    add('reduce-B3',action_input,ok(final_cash='996.800',final_B='4',final_C='4',new_shares='3',new_fills=1,sale_receivable='57.940',fees='1',tax='1'))
    exit=deepcopy(action_input);exit['action'].update(kind='EXIT_SELLABLE_HOLDING',sell_shares='7',reason='EXPLICIT_SYNTHETIC_EXIT_SPECIFIED_STOCK_NOT_ACCOUNT')
    exit_spec=deepcopy(spec);exit_spec['orders'][0]['shares']='7'
    add('exit-B7',exit,ok(final_cash='1076.720',final_B='0',final_C='4',new_shares='7',new_fills=1,sale_receivable='137.860',fees='1',tax='1'),exit_spec)
    split=deepcopy(exit_spec);a=deepcopy(split['orders'][0]);a.update(id='sell-B-3',shares='3');b=deepcopy(a);b.update(id='sell-B-4',shares='4');split['orders']=[a,b]
    add('split-exit',exit,ok(final_cash='1074.720',final_B='0',final_C='4',new_shares='7',new_fills=2,sale_receivable='135.860',fees='2',tax='2'),split)
    full20=load(full20_source)['run']['checkpoint'];partial=deepcopy(exit)
    partial['account_source'].update(checkpoint=full20,expected_checkpoint_id=full20['checkpoint_id'],expected_latest_decision_id=full20['execution_result']['latest_decision_id'])
    partial['action']['sell_shares']='20';ps=deepcopy(exit_spec);ps['orders'][0]['shares']='20';ps['tape']=deepcopy(load(tape_source)['execution_spec']['tape']);ps['observed_until']='2026-01-09T16:00:00+08:00'
    add('partial-exit-B20',partial,ok(final_cash='598.600',final_B='13',final_C='2',new_shares='7',new_fills=1,sale_receivable='137.860',fees='1',tax='1',remaining='13',order_status='PARTIAL',cash_receivable='217.860'),ps)
    for name,state,cap in [('limit-down','LIMIT_DOWN_NO_SELL','500'),('capacity-zero','OPEN','0')]:
        s=deepcopy(exit_spec);s['tape'][-1].update(market_state=state,capacity_shares=cap)
        add(name,exit,ok(final_cash='938.860',final_B='7',final_C='4',new_shares='0',new_fills=0,sale_receivable='0',fees='0',tax='0',remaining='7',order_status='EXPIRED_UNFILLED'),s)
    empty=deepcopy(exit_spec);empty['orders']=[]
    add('empty-orders',exit,ok(final_cash='938.860',final_B='7',final_C='4',new_shares='0',new_fills=0,sale_receivable='0',fees='0',tax='0'),empty)
    x=deepcopy(action_input);x['action']['sell_shares']='8';add('oversell',x,blocked('SELL_QUANTITY_EXCEEDS_AVAILABLE_SHARES'))
    x=deepcopy(exit);x['action']['sell_shares']='6';add('exit-quantity-mismatch',x,blocked('EXIT_MUST_MATCH_CURRENT_SELLABLE_SHARES'))
    x=deepcopy(action_input);x['action']['sell_shares']='7';add('reduction-would-exit',x,blocked('REDUCTION_MUST_LEAVE_SPECIFIED_HOLDING'))
    x=deepcopy(action_input);x['action']['sell_shares']='3.5';add('fractional',x,blocked('Explicit whole share quantity required'))
    x=deepcopy(exit);x['account_source']['expected_latest_decision_id']='wrong';add('wrong-latest',x,blocked('EXACT_LATEST_PREDECESSOR_REQUIRED'))
    x=deepcopy(exit);active=load(PROJECT/'capital_research/standing_orders_20261028/controls/partial-fill-to-Jan8/actual.json')['checkpoint']
    x['account_source'].update(checkpoint=active,expected_checkpoint_id=active['checkpoint_id'],expected_latest_decision_id=active['execution_result']['latest_decision_id'])
    add('active-checkpoint',x,blocked('ACTIVE_ORDER_CONTINUATION_NOT_IMPLEMENTED','NOT_IMPLEMENTED'))
    x=deepcopy(exit);unsettled=load(PROJECT/'capital_research/standing_orders_20261028/before/payable-only/checkpoint.json')
    x['account_source'].update(checkpoint=unsettled,expected_checkpoint_id=unsettled['checkpoint_id'],expected_latest_decision_id=unsettled['execution_result']['latest_decision_id'])
    x['decision_template']['data_cutoff']=unsettled['state']['through_at']
    for c,a in x['decision_template']['assets'].items():
        a['marks'][0].update(occurred_at=unsettled['state']['through_at'],available_at=unsettled['state']['through_at'],price=unsettled['state']['row']['marks'][c]['value'])
        a['capital_eligibility']['data_cutoff']=unsettled['state']['through_at']
    add('unsettled-checkpoint',x,blocked('OPENING_PAYABLE_CONTINUATION_NOT_IMPLEMENTED','NOT_IMPLEMENTED'))
    x=deepcopy(exit);x['decision_template']['assets']['B']['basis_id']='RAW:other';add('basis-mismatch',x,blocked('CHECKPOINT_ASSET_SOURCE_BASIS_CHANGED'))
    x=deepcopy(exit);x['account_source']['checkpoint']['origin_ledger_input']['sources']['fixture']['kind']='REAL_RAW_RELABELED';add('real-relabel',x,blocked('EXPLICIT_SYNTHETIC_SELL_CHECKPOINT_REQUIRED'))
    x=deepcopy(exit);x['account_source']=dict(kind='DECLARED_SYNTHETIC_OPENING',account={},consumed_evidence_tokens=[]);add('new-opening',x,blocked('CHECKPOINT_REQUIRED_FOR_SELL'))
    s=deepcopy(exit_spec);s['orders'][0]['side']='BUY';add('buy-injection',exit,dict(checked_status='CURRENTLY_FEASIBLE',run_status='INPUT_ERROR',simulate_calls=0,run_reason='ORDER_OUTSIDE_CHECKED_ACTION_SCOPE'),s)
    s=deepcopy(split);s['orders'][1]['shares']='5';add('oversplit',exit,dict(checked_status='CURRENTLY_FEASIBLE',run_status='INPUT_ERROR',simulate_calls=0,run_reason='AGGREGATE_ORDER_EXCEEDS_CHECKED_ACTION'),s)
    add('tampered-checked',exit,dict(checked_status='CURRENTLY_FEASIBLE',run_status='INPUT_ERROR',simulate_calls=0,run_reason='BOUND_ACTION_RESULT_MISMATCH'),exit_spec,dict(kind='TAMPER_CHECKED_REHASH'))
    add('cross-version',exit,dict(checked_status='CURRENTLY_FEASIBLE',run_status='INPUT_ERROR',simulate_calls=0,run_reason='SUPPORTED_FULL_CHECKED_ACTION_REQUIRED_NO_MIGRATION'),exit_spec,dict(kind='EXECUTE_AS_V01'))
    x=deepcopy(base['action_input']);x['action'].update(kind='EXIT_SELLABLE_HOLDING',additional_shares='7',trigger_ids=[],batch_context=None)
    add('v01-sell-refused',x,blocked('ONLY_EXPLICIT_HOLD_OR_SETTLED_CASH_BUY_SUPPORTED'),exit_spec)
    x=deepcopy(action_input);x['policy']['edge_budget']='0';add('existing-no-trade-band',x,blocked('NO_TRADE_BAND','REJECTED'))
    save(ROOT/'case-index.json',dict(cases=cases,all_synthetic=True,market_samples=0,old_suite_runs=0,new_quotes=0,new_calendar_rows=0))
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='frozen.json']))
    save(ROOT/'before/input.json',exit);save(ROOT/'before/expected.json',dict(new_version_not_accepted_by_original_api=True))
    save(ROOT/'before/actual.json',evaluate(exit))
    print('Frozen',len(cases),'sell scenarios and manual expectations; one old unsupported-version result retained')


if __name__=='__main__':main()
