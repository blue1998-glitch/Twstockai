"""Only materialize new finite synthetic requests; never rerun old suites."""
import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent.parent
REPO=PROJECT.parent
OLD=ROOT.parent/'cash_action_20261028'


def load(p):return json.loads(p.read_text())
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False);f.write('\n')
def info(p):
    b=p.read_bytes();return dict(path=str(p.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    from capital_research.core import fingerprint
    from capital_research.cash_action import evaluate
    protected=[PROJECT/'capital_research'/n for n in ('cash_action.py','core.py','execution.py','continuity.py',
        'quantity_candidates.py','eligibility.py','fact_lineage.py','close_clock.py','reassessment_history.py','transition_risk.py')]
    protected += [PROJECT/'rotation_research/action_ledger.py',OLD/'CHANGE_MANIFEST.json',
        PROJECT/'rotation_research/market_case_v2_20261028/CHANGE_MANIFEST.json']
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        protected=[info(p) for p in protected],task='BIND_FULL_CHECKED_CASH_ACTION_TO_EXISTING_SYNTHETIC_EXECUTION',
        old_suites_rerun=0,market_replay=False,source_fetch=False))
    checked_cache={}
    def prior(name):
        if name not in checked_cache:
            i=load(OLD/'cases'/name/'input.json');a=load(OLD/'after-final/actual'/name/'result.json')
            checked_cache[name]=(i,a)
        return deepcopy(checked_cache[name])
    def obs(code,day,at,capacity='500',state='OPEN'):
        return dict(at=day+'T'+at+'+08:00',available_at=day+'T'+at+'+08:00',code=code,
            price={'A':'10','B':'20','C':'25'}[code],capacity_shares=capacity,market_state=state,
            settlement_date='2026-01-08' if day=='2026-01-06' else '2026-01-12',
            source_id='fixture',basis_id='RAW:fixture:'+code,version='synthetic-tape/0.1',qualification='EXPLICIT_SYNTHETIC_OBSERVATION')
    def material(name):
        i,a=prior(name);source=i['account_source']
        if source['kind']=='CHECKPOINT':
            ledger=deepcopy(source['checkpoint']['origin_ledger_input']);clock=deepcopy(source['checkpoint']['execution_result']['ledger_close_proof']);day='2026-01-09'
        else:
            seed=load(OLD/'preconditions/holding/input.json');ledger=seed['ledger_input'];clock=seed['ledger_close_proof'];day='2026-01-06'
            account=source['account'];ledger['opening']=dict(cash=account['settled_cash'],
                shares={c:v['shares'] for c,v in account['holdings'].items()},cash_claims=deepcopy(account['cash_claims']),share_claims=deepcopy(account['share_claims']))
        code=i['action']['code'] or 'B';others=[c for c in ('A','C','B') if c!=code]
        tape=[obs(c,day,'09:0'+str(k)+':00') for k,c in enumerate(others)]
        tape.append(obs(code,day,'09:02:00'))
        orders=[] if i['action']['kind']=='HOLD' else [dict(id='explicit-order',code=code,side='BUY',shares=i['action']['additional_shares'],
            limit_price='10.02' if code=='A' else '20.03',decision_at=i['decision_template']['decision_at'],
            submitted_at=day+'T08:00:00+08:00',expires_at='2026-01-12T12:00:00+08:00')]
        return dict(schema='capital-cash-action-execution-input/0.1',synthetic=True,action_input=i,checked_action=a,
            expected_checked_action_id=fingerprint(a),execution_spec=dict(id='explicit-synthetic-run',origin_ledger=ledger,
                ledger_close_proof=clock,orders=orders,tape=tape,observed_until='2026-01-12T16:00:00+08:00'))

    cases=[]
    def add(name,x,status='REPLAYED_EXPLICIT_ACTION',reason=None,**expected):
        save(ROOT/'cases'/name/'input.json',x)
        save(ROOT/'cases'/name/'expected.json',dict(status=status,reason=reason,**expected));cases.append(name)
    opening=material('opening-cash-first-B');opening['execution_spec']['observed_until']='2026-01-08T16:00:00+08:00'
    add('opening-B20',opening,new_shares='20',new_fill_count=1,final_cash='598.600',origin_capital='1180')
    held=material('original-cash-no-sale-A')
    add('keep-A-buy-B20',held,new_shares='20',new_fill_count=1,final_cash='678.600',origin_capital='2180',final_A='100')
    exited=material('exit-unsettled-first-B-small')
    add('exited-A-buy-B20',exited,new_shares='20',new_fill_count=1,final_cash='1673.600',origin_capital='2180',final_A='0')
    hold=deepcopy(exited);hold['action_input']['action']=dict(id='keep-original-cash',kind='HOLD',code=None,additional_shares='0',trigger_ids=[],batch_context=None)
    # This is a new explicit HOLD, not a rerun of a previous suite/result.
    hold['checked_action']=evaluate(hold['action_input']);hold['expected_checked_action_id']=fingerprint(hold['checked_action'])
    hold['execution_spec']['orders']=[];hold['execution_spec']['tape']=[]
    add('hold-receivables-to-settlement',hold,new_shares='0',new_fill_count=0,final_cash='2075.000',origin_capital='2180',final_A='0')
    partial=deepcopy(exited);partial['execution_spec']['tape'][-1]['capacity_shares']='7';partial['execution_spec']['observed_until']='2026-01-09T16:00:00+08:00'
    add('partial-7-active-13',partial,new_shares='7',new_fill_count=1,remaining='13',order_status='PARTIAL',reserved_cash='261.65039',final_cash='858.860',origin_capital='2180')
    expired=deepcopy(partial);expired['execution_spec']['observed_until']='2026-01-12T16:00:00+08:00'
    add('partial-7-expired-13',expired,new_shares='7',new_fill_count=1,remaining='13',order_status='EXPIRED_UNFILLED',reserved_cash='0',final_cash='1933.860',origin_capital='2180')
    cancelled=deepcopy(partial);cancelled['execution_spec']['tape'].append(obs('B','2026-01-09','13:00:00',capacity='13'));cancelled['execution_spec']['observed_until']='2026-01-12T16:00:00+08:00'
    cancelled['action_input']['decision_template']['assets']['B']['evidence'][0]['validity']['invalidation']=dict(
        evidence_id='B-known-at-noon',occurred_at='2026-01-09T12:00:00+08:00',available_at='2026-01-09T12:00:00+08:00',source_ids=['fixture'])
    cancelled['checked_action']=evaluate(cancelled['action_input']);cancelled['expected_checked_action_id']=fingerprint(cancelled['checked_action'])
    add('partial-7-cancelled-13',cancelled,new_shares='7',new_fill_count=1,remaining='13',order_status='CANCELLED_EVIDENCE',reserved_cash='0',final_cash='1933.860',origin_capital='2180')
    for name,field,value in [('limit-up-unfilled','market_state','LIMIT_UP_NO_BUY'),('zero-capacity-unfilled','capacity_shares','0')]:
        x=deepcopy(exited);x['execution_spec']['tape'][-1][field]=value
        add(name,x,new_shares='0',new_fill_count=0,remaining='20',order_status='EXPIRED_UNFILLED',reserved_cash='0',final_cash='2075.000',origin_capital='2180')
    empty=deepcopy(exited);empty['execution_spec']['orders']=[]
    add('no-implicit-order',empty,new_shares='0',new_fill_count=0,final_cash='2075.000',origin_capital='2180')
    fresh=deepcopy(exited);i=fresh['action_input'];i['action'].update(code='A',trigger_ids=['A-new-reentry'])
    b=i['action']['batch_context'];b.update(code='A',basis_id='RAW:fixture:A',phase='ADDITIONAL_BATCH')
    e=deepcopy(i['decision_template']['assets']['A']['evidence'][0]);e.update(id='A-new-reentry',event_id='A-new-reentry',formation_id='A-new-reentry-formation',volume_bar_id='A-new-reentry-bar',occurred_at=i['decision_template']['data_cutoff'],available_at=i['decision_template']['data_cutoff'])
    i['decision_template']['assets']['A']['evidence'].append(e)
    fresh['checked_action']=evaluate(i);fresh['expected_checked_action_id']=fingerprint(fresh['checked_action'])
    fresh['execution_spec']['orders'][0].update(code='A',limit_price='10.02')
    fresh['execution_spec']['tape']=[obs('C','2026-01-09','09:00:00'),obs('B','2026-01-09','09:01:00'),obs('A','2026-01-09','09:02:00')]
    add('new-independent-A-reentry',fresh,new_shares='20',new_fill_count=1,final_cash='1873.800',origin_capital='2180',final_A='20')
    rejected=deepcopy(fresh);rejected['action_input']['action']['batch_context']['phase']='FIRST_ENTRY';rejected['action_input']['action']['trigger_ids']=[]
    rejected['checked_action']=evaluate(rejected['action_input']);rejected['expected_checked_action_id']=fingerprint(rejected['checked_action'])
    add('outer-rejected-core-feasible',rejected,'STOPPED_ACTION_GATE','CHECKED_ACTION_NOT_CURRENTLY_FEASIBLE',execution_calls=0)
    forged=deepcopy(rejected);r=forged['checked_action']['research'];r['status']='CURRENTLY_FEASIBLE';r['intent']['feasible_for_research']=True;r['research_recommendation']['candidate_ids']=[r['intent']['evaluated_plan_id']]
    forged['expected_checked_action_id']=fingerprint(forged['checked_action'])
    add('forged-outer-approval',forged,'INPUT_ERROR','BOUND_ACTION_RESULT_MISMATCH',execution_calls=0)
    x=deepcopy(exited);x['expected_checked_action_id']='wrong';add('wrong-full-result-id',x,'INPUT_ERROR','FULL_CHECKED_ACTION_ID_MISMATCH',execution_calls=0)
    x=deepcopy(exited);x['action_input']['action']['additional_shares']='21';add('different-action-input',x,'INPUT_ERROR','ACTION_INPUT_ID_MISMATCH',execution_calls=0)
    x=deepcopy(exited);x['checked_action']['source_integrity_metadata']['derived_decision_input']['account']['reserved_cash']='0';x['expected_checked_action_id']=fingerprint(x['checked_action'])
    add('tampered-metadata-reserve',x,'INPUT_ERROR','BOUND_ACTION_RESULT_MISMATCH',execution_calls=0)
    x=deepcopy(exited);x['execution_spec']['origin_ledger']['opening']['cash']='9999';add('reset-original-capital',x,'INPUT_ERROR','ORIGINAL_LEDGER_BINDING_REQUIRED',execution_calls=0)
    x=deepcopy(exited);x['execution_spec']['ledger_close_proof']['closes']['2026-01-08']['available_at']='2026-01-08T18:00:00+08:00';add('changed-close-proof',x,'INPUT_ERROR','ORIGINAL_CLOSE_PROOF_REQUIRED',execution_calls=0)
    x=deepcopy(exited);x['execution_spec']['orders'][0]['shares']='11';o=deepcopy(x['execution_spec']['orders'][0]);o.update(id='split-second',shares='10');x['execution_spec']['orders'].append(o)
    add('split-order-total-exceeds-20',x,'INPUT_ERROR','AGGREGATE_ORDER_EXCEEDS_CHECKED_ACTION',execution_calls=0)
    x=deepcopy(exited);x['execution_spec']['orders'][0]['side']='SELL';add('sell-cannot-bypass-cash-intent',x,'INPUT_ERROR','ORDER_OUTSIDE_CHECKED_ACTION_SCOPE',execution_calls=0)
    x=deepcopy(hold);x['execution_spec']['orders']=deepcopy(exited['execution_spec']['orders']);add('hold-cannot-submit-buy',x,'INPUT_ERROR','HOLD_CANNOT_CREATE_ORDERS',execution_calls=0)
    x=deepcopy(opening);x['execution_spec']['origin_ledger']['sources']['fixture']['kind']='REAL_RAW_MARKET_SOURCE';add('real-ledger-relabel-refused',x,'INPUT_ERROR','EXPLICIT_SYNTHETIC_LEDGER_REQUIRED',execution_calls=0)
    x=deepcopy(opening);x['execution_spec']['origin_ledger'].pop('calendar');add('missing-calendar',x,'INPUT_ERROR','EXPLICIT_LEDGER_CALENDAR_REQUIRED',execution_calls=0)
    x=deepcopy(exited);x['execution_spec']['tape']=None;add('missing-tape',x,'INPUT_ERROR','EXPLICIT_ORDERS_TAPE_AND_WATERMARK_REQUIRED',execution_calls=0)
    x=deepcopy(exited);x['execution_spec']['continuation']={};add('continuation-override',x,'INPUT_ERROR','EXACT_EXTERNAL_EXECUTION_SPEC_REQUIRED',execution_calls=0)
    x=deepcopy(exited);x['execution_spec']['tape'][-1]['at']='2026-01-13T09:02:00+08:00';x['execution_spec']['tape'][-1]['available_at']=x['execution_spec']['tape'][-1]['at'];add('future-observation-outside-origin',x,'INPUT_ERROR','OBSERVATION_OUTSIDE_EXPLICIT_WATERMARK',execution_calls=0)
    prefix=deepcopy(opening);prefix['execution_spec']['origin_ledger']['assets']['B']['quotes']['2026-01-12']='200'
    add('future-quote-prefix-control',prefix,new_shares='20',new_fill_count=1,final_cash='598.600',origin_capital='1180',same_numeric_as='opening-B20')
    save(ROOT/'case-index.json',dict(cases=cases,finite_cases=len(cases),old_suite_methods_executed=0,market_samples=0,
        fresh_fixture_checks=['new HOLD','known future cancellation','independent A reentry','false-first counterexample'],
        original_checked_results_reused=['opening-cash-first-B','original-cash-no-sale-A','exit-unsettled-first-B-small'],
        all_inputs_and_oracles_before_new_adapter=True))
    save(ROOT/'test-spec.json',dict(manual_cash_math=dict(B20='20*20.02+ceil(max(1,400.4*.001))=401.4',
        B7='7*20.02+1=141.14',partial_remaining_reserve='13*(20.03*1.001)+1=261.65039',
        A20='20*10.01+1=201.2',old_sale='100*9.99-1-3=995',origin_capital='2180 retained; cash-only declared opening 1180'),
        first_checkpoint_original='2026-01-08T16:00:00+08:00',last_legal_origin_day='2026-01-12',
        extra_checks=['exact decision match','all accepted fills and original opening','all historical tokens','no engine on refusal',
            'new checkpoint to existing HOLD gate','active partial remains unsupported to resume','normal/hostile Context','no IO/network','future numeric prefix'] ))
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='frozen.json']))
    print('Frozen',len(cases),'new execution requests/oracles; no execution calls or old suite runs')


if __name__=='__main__':main()
