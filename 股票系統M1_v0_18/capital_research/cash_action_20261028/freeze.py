"""Freeze finite hypothetical inputs/oracles before implementing the adapter."""
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
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def info(p):
    b=p.read_bytes();return dict(path=str(p.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    from capital_research.execution import simulate
    from capital_research.continuity import make_checkpoint
    seed=PROJECT/'capital_research/repair_ab_20261025/after/A-own-evidence/input.json'
    old=load(seed)
    protected=[seed,*[PROJECT/'capital_research'/n for n in
        ('core.py','continuity.py','execution.py','quantity_candidates.py','eligibility.py','fact_lineage.py',
         'reassessment_history.py','close_clock.py','order_review.py')],
        PROJECT/'rotation_research/action_ledger.py',
        PROJECT/'rotation_research/market_case_v2_20261028/CHANGE_MANIFEST.json']
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        task='EXPLICIT_SYNTHETIC_CASH_ACTION_DECISION_ONLY',protected=[info(p) for p in protected],
        old_market_context_unchanged=True,market_replay=False,source_originals_fetched=False))
    jobs={}
    for name,exit_a,through,capacity in [('holding',False,'2026-01-08T16:00:00+08:00','100'),
            ('exit-unsettled',True,'2026-01-08T16:00:00+08:00','100'),
            ('exit-settled',True,'2026-01-12T16:00:00+08:00','100'),
            ('partial-active',True,'2026-01-08T16:00:00+08:00','20')]:
        j=deepcopy(old);d=j['decision_input'];a=d['account'];a['holdings']['C']=dict(shares='2',sellable='2')
        a['share_claims'][0].update(code='C',shares='2')
        targets={c:v['shares'] for c,v in a['holdings'].items()};targets['A']='0'
        d['plans']=[dict(id='exit-A-only',family='E',route='R1',targets=targets,trigger_ids=[],
            edge_budget='1000',conditions=['EXPLICIT_SYNTHETIC_EXIT_A_NOT_ALL_ASSETS'])] if exit_a else []
        j['plan_id']='exit-A-only' if exit_a else 'A-zero';j['observed_until']=through
        origin=j['ledger_input'];origin['opening']=dict(cash=a['settled_cash'],
            shares={c:v['shares'] for c,v in a['holdings'].items()},cash_claims=deepcopy(a['cash_claims']),share_claims=deepcopy(a['share_claims']))
        j['orders']=[dict(id='exit-A',code='A',side='SELL',shares='100',limit_price='9.98',
            decision_at=d['decision_at'],submitted_at='2026-01-06T08:00:00+08:00',expires_at='2026-01-12T16:00:00+08:00')] if exit_a else []
        j['tape']=[dict(at='2026-01-06T09:00:00+08:00',available_at='2026-01-06T09:00:00+08:00',
            code='A',price='10',capacity_shares=capacity,market_state='OPEN',settlement_date='2026-01-12',
            version='synthetic-tape/0.1',qualification='EXPLICIT_SYNTHETIC_OBSERVATION',source_id='fixture',basis_id='RAW:fixture:A')] if exit_a else []
        jobs[name]=j;save(ROOT/'preconditions'/name/'input.json',j)
    save(ROOT/'preconditions/expected.json',dict(origin_initial_capital='2180',general_reserved_cash='100',
        exit_fill_shares='100',exit_fill_price='9.990',exit_fee='1',exit_tax='2.997',exit_net_receivable='995.003',
        unsettled_cash='1000',settled_cash='2075.003',holding_A='100',exit_A='0',
        C_before_delivery='2',C_after_delivery='4',cash_claim_amount='80',C_share_claim_amount='2',
        partial_fill_shares='20',partial_remaining='80',
        explanation='100*9.99-1-2.997=995.003; 1000+995.003+80=2075.003. C shares/rights worth 100; original capital 2180, not a new opening.'))
    checkpoints={}
    for name,j in jobs.items():
        result=simulate(j)
        if result['status']!='SYNTHETIC_EXECUTION_REPLAY':raise ValueError(result)
        cp=make_checkpoint(j['ledger_input'],result,through_at=j['observed_until'])
        checkpoints[name]=cp;save(ROOT/'preconditions'/name/'execution.json',result);save(ROOT/'preconditions'/name/'checkpoint.json',cp)

    def template(cp=None):
        d=deepcopy(jobs['holding']['decision_input'])
        for k in ('account','plans','consumed_evidence_tokens'):d.pop(k)
        if cp:
            d['data_cutoff']=cp['state']['through_at'];d['decision_at']=cp['state']['through_at'][:10]+'T17:00:00+08:00'
            for c,a in d['assets'].items():
                a['marks']=[dict(a['marks'][0],price=cp['state']['row']['marks'][c]['value'],
                    occurred_at=d['data_cutoff'],available_at=d['data_cutoff'])]
                a['capital_eligibility'].update(assessed_at=d['decision_at'],available_at=d['decision_at'],data_cutoff=d['data_cutoff'])
        return d

    def request(cp=None,code='B',phase='FIRST_ENTRY',n='20'):
        d=template(cp);asset=d['assets'][code]
        if cp:
            source=dict(kind='CHECKPOINT',checkpoint=deepcopy(cp),expected_checkpoint_id=cp['checkpoint_id'],
                expected_latest_decision_id=cp['execution_result']['latest_decision_id'])
        else:
            a=deepcopy(jobs['holding']['decision_input']['account'])
            a['holdings']['A']=dict(shares='0',sellable='0')
            source=dict(kind='DECLARED_SYNTHETIC_OPENING',account=a,consumed_evidence_tokens=[])
        return dict(schema='capital-cash-action-input/0.1',synthetic=True,decision_template=d,account_source=source,
            action=dict(id='explicit-cash-intent',kind='BUY_FROM_SETTLED_CASH',code=code,additional_shares=n,
                trigger_ids=[],batch_context=dict(version='synthetic-batch-context/0.1',parameter_source='EXPLICIT_TEST_ONLY_NOT_USER_RULE',
                    available_at=d['decision_at'],phase=phase,code=code,**{k:asset[k] for k in ('source_id','basis_id','adjustment_version')})),
            policy=dict(version='cash-action-fixture-policy/0.1',parameter_source='EXPLICIT_SYNTHETIC_EDGE_NOT_FORECAST',
                available_at=d['decision_at'],edge_budget='1000'))

    cases=[]
    def add(name,r,status,reason=None):
        expected=dict(status=status,reason=reason,no_orders=True,no_fills=True,all_authorizations_false=True)
        save(ROOT/'cases'/name/'input.json',r);save(ROOT/'cases'/name/'expected.json',expected);cases.append(name)
    add('opening-cash-first-B',request(),'CURRENTLY_FEASIBLE')
    hold=request();hold['action']=dict(id='explicit-hold',kind='HOLD',code=None,additional_shares='0',trigger_ids=[],batch_context=None)
    add('opening-hold-zero-A',hold,'CURRENTLY_FEASIBLE')
    add('original-cash-no-sale-A',request(checkpoints['holding']),'CURRENTLY_FEASIBLE')
    add('exit-unsettled-first-B-small',request(checkpoints['exit-unsettled']),'CURRENTLY_FEASIBLE')
    add('exit-settled-first-B',request(checkpoints['exit-settled']),'CURRENTLY_FEASIBLE')
    add('receivable-not-buying-power',request(checkpoints['exit-unsettled'],n='60'),'REJECTED','JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS')
    add('settled-larger-B',request(checkpoints['exit-settled'],n='60'),'CURRENTLY_FEASIBLE')
    add('reserve-not-spendable',request(checkpoints['holding'],n='45'),'REJECTED','JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS')
    add('fees-paid-from-original-cash',request(n='50'),'REJECTED','JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS')
    r=request(checkpoints['exit-settled'],code='A',phase='ADDITIONAL_BATCH');r['action']['trigger_ids']=['A-event']
    add('reentry-old-trigger',r,'REJECTED','NO_NEW_INDEPENDENT_TRIGGER')
    fresh=deepcopy(r);e=deepcopy(fresh['decision_template']['assets']['A']['evidence'][0]);e.update(id='A-independent',event_id='A-independent',formation_id='A-new-formation',volume_bar_id='A-new-bar',occurred_at=fresh['decision_template']['data_cutoff'],available_at=fresh['decision_template']['data_cutoff'])
    fresh['decision_template']['assets']['A']['evidence'].append(e);fresh['action']['trigger_ids']=['A-independent']
    add('reentry-independent-A',fresh,'CURRENTLY_FEASIBLE')
    r=deepcopy(fresh);r['decision_template']['assets']['A']['evidence'][-1]['volume_bar_id']='A-bar'
    add('reentry-shared-bar',r,'REJECTED','NO_NEW_INDEPENDENT_TRIGGER')
    r=deepcopy(fresh);r['action']['trigger_ids']=['B-event']
    add('cross-stock-trigger',r,'REJECTED','BATCH_TRIGGER_NOT_OWNED_BY_DESTINATION')
    r=request(checkpoints['exit-settled'],code='A');add('false-first-after-exit',r,'REJECTED','FIRST_ENTRY_CONTRADICTS_B_EPISODE_HISTORY')
    r=request(checkpoints['holding']);r['action']['batch_context']['phase']='UNKNOWN';add('unknown-phase',r,'REJECTED','BATCH_PHASE_UNKNOWN')
    r=request();r['decision_template']['assets']['B']['capital_eligibility']['status']='UNKNOWN';add('unknown-capital-review',r,'REJECTED','NEW_CAPITAL_NOT_QUALIFIED:B')
    r=request();r['decision_template']['assets']['B']['evidence'][0]['validity']['invalidation']=dict(evidence_id='B-revoked',occurred_at=r['decision_template']['data_cutoff'],available_at=r['decision_template']['data_cutoff'],source_ids=['fixture'])
    add('revoked-evidence',r,'REJECTED','NEW_CAPITAL_NOT_QUALIFIED:B')
    r=request();r['decision_template']['risk_limits']['group_value']['new']='100';add('joint-risk',r,'REJECTED','RISK_LIMIT_EXCEEDED')
    r=request();r['decision_template']['risk_limits']['max_trade_shares']['B']='10';add('liquidity',r,'REJECTED','LIQUIDITY_REQUIRES_SMALLER_OR_PARTIAL_ORDER:B')
    r=request(checkpoints['exit-settled']);r['account_source']['expected_latest_decision_id']='wrong';add('wrong-latest',r,'INPUT_ERROR','EXACT_LATEST_PREDECESSOR_REQUIRED')
    r=request(checkpoints['exit-settled']);r['account_source']['expected_checkpoint_id']='wrong';add('wrong-checkpoint',r,'INPUT_ERROR','EXACT_CHECKPOINT_REQUIRED')
    r=request();r['decision_template']['account']={};add('account-override',r,'INPUT_ERROR','DERIVED_ACCOUNT_PLANS_TOKENS_CANNOT_BE_OVERRIDDEN')
    r=request();r['decision_template']['consumed_evidence_tokens']=[];add('token-override',r,'INPUT_ERROR','DERIVED_ACCOUNT_PLANS_TOKENS_CANNOT_BE_OVERRIDDEN')
    add('active-partial-order',request(checkpoints['partial-active']),'NOT_IMPLEMENTED','ACTIVE_ORDER_CONTINUATION_NOT_IMPLEMENTED')
    r=request();r['account_source']['account']['payables']=[dict(id='unknown-payable',amount='50')];add('opening-payable',r,'NOT_IMPLEMENTED','OPENING_PAYABLE_CONTINUATION_NOT_IMPLEMENTED')
    r=request(checkpoints['holding']);r['action']['batch_context']['basis_id']='wrong';add('batch-basis-mismatch',r,'INPUT_ERROR','Batch context source/basis/asset mismatch')
    r=request(checkpoints['holding']);r['decision_template']['assets']['B']['adjustment_version']='other';add('checkpoint-source-mismatch',r,'INPUT_ERROR','CHECKPOINT_ASSET_SOURCE_BASIS_CHANGED')
    r=request();r['synthetic']=False;add('real-source-refused',r,'INPUT_ERROR','EXPLICIT_SYNTHETIC_CASH_ACTION_REQUIRED')
    r=request();r['action']['family']='E';add('family-override',r,'INPUT_ERROR','EXACT_EXPLICIT_ACTION_REQUIRED')
    r=request();r['policy']['available_at']='2026-01-06T17:00:00+08:00';add('future-policy',r,'INPUT_ERROR','ACTION_POLICY_NOT_YET_AVAILABLE')
    r=request();r['decision_template']['assets']['B']['evidence'][0]['validity']['invalidation']=dict(evidence_id='future-revocation',occurred_at='2026-01-06T14:00:00+08:00',available_at='2026-01-06T14:00:00+08:00',source_ids=['fixture']);add('future-revocation-prefix',r,'CURRENTLY_FEASIBLE')
    save(ROOT/'case-index.json',dict(cases=cases,fixture_checkpoint_builds=len(jobs),market_samples=0,
        contract=info(ROOT/'CONTRACT.md'),inputs_and_oracles_frozen_before_adapter=True))
    files=[p for p in ROOT.rglob('*') if p.is_file() and p.name!='frozen.json']
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(files)]))
    print('Frozen',len(cases),'finite cases; four synthetic preconditions, no market replay')


if __name__=='__main__':main()
