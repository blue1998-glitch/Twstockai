"""Explicit synthetic choices/orders/tape. No engine or old producer calls."""
from copy import deepcopy
import json
from pathlib import Path

ROOT=Path(__file__).parents[1]


def load(path):return json.loads(path.read_text())


def observation(code,day,clock,capacity='0',state='OPEN',settlement=None):
    at=day+'T'+clock+'+08:00'
    return dict(at=at,available_at=at,code=code,price={'A':'10','B':'20','C':'25'}[code],capacity_shares=capacity,
        market_state=state,settlement_date=settlement or day,version='synthetic-tape/0.1',
        qualification='EXPLICIT_SYNTHETIC_OBSERVATION',source_id='fixture',basis_id='RAW:fixture:'+code)


def day_tape(day,a='0',b='0',a_state='OPEN',b_state='OPEN',settlement=None):
    return [observation('A',day,'09:00:00',a,a_state,settlement),
            observation('C',day,'09:00:30',settlement=settlement),
            observation('B',day,'09:01:00',b,b_state,settlement)]


def order(key,code,side,n,decision,day,expiry):
    return dict(id=key,code=code,side=side,shares=str(n),limit_price='9.98' if side=='SELL' else '20.03',
        decision_at=decision,submitted_at=day+'T08:00:00+08:00',expires_at=expiry)


def frame(base,key,cutoff,decision,phase,sell,buy,day,until,*,independent=False):
    data=deepcopy(base['decision_input']);data.pop('account');data.pop('plans')
    data.update(data_cutoff=cutoff,decision_at=decision)
    for a in data['assets'].values():
        mark=deepcopy(a['marks'][0]);mark.update(occurred_at=cutoff,available_at=cutoff);a['marks']=[mark]
        a['capital_eligibility'].update(data_cutoff=cutoff,assessed_at=decision,available_at=decision)
    triggers=[]
    if phase=='ADDITIONAL_BATCH':triggers=['B-event']
    if independent:
        a=data['assets']['B'];fact=deepcopy(a['evidence'][0]);fact.update(id='B-next-round',event_id='B-next-round',
            formation_id='B-next-formation',volume_bar_id='B-next-bar',occurred_at=cutoff,available_at=cutoff)
        fact['validity'].update(valid_from=cutoff,available_at=cutoff,invalidation=None)
        a['evidence'].append(fact);a['capital_eligibility']['evidence_ids'].append(fact['id']);triggers=[fact['id']]
    quantity=deepcopy(base);quantity.pop('decision_input');quantity.pop('continuation')
    quantity['trigger_ids']=triggers
    quantity['bounds']=dict(sell_A=dict(minimum=str(sell),maximum=str(sell)),additional_B=dict(minimum=str(buy),maximum=str(buy)))
    context=quantity['batch_context'];context.pop('account_id');context.pop('origin');context.update(phase=phase,available_at=decision)
    orders=[]
    if sell:orders.append(order(key+'-A','A','SELL',sell,decision,day,until))
    if buy:orders.append(order(key+'-B','B','BUY',buy,decision,day,until))
    return dict(id=key,decision_template=data,quantity_template=quantity,
        selection=dict(mode='GRID',sell_A=str(sell),additional_B=str(buy),reason='EXPLICIT_SYNTHETIC_INTENT_NOT_A_POLICY_OR_OPTIMAL_RATIO'),
        orders=orders,tape=[],observed_until=until,cancelled_order_ids=[])


def partial():
    base=load(ROOT/'quantity_candidates_v02_20261026/cases/first-manual-grid/input.json')
    old=load(ROOT/'repair_ab_20261025/after/A-own-evidence/input.json')
    account=deepcopy(base['decision_input']['account']);origin=deepcopy(old['ledger_input'])
    origin['opening']=dict(cash=account['settled_cash'],shares={c:v['shares'] for c,v in account['holdings'].items()},
        cash_claims=deepcopy(account['cash_claims']),share_claims=deepcopy(account['share_claims']))
    r1=frame(base,'r1','2026-01-05T14:00:00+08:00','2026-01-05T15:00:00+08:00','FIRST_ENTRY',50,20,'2026-01-06','2026-01-08T16:00:00+08:00')
    r1['tape']=day_tape('2026-01-06',a='20',b='7',settlement='2026-01-08')
    r2=frame(base,'r2','2026-01-08T16:00:00+08:00','2026-01-08T17:00:00+08:00','ADDITIONAL_BATCH',0,1,'2026-01-09','2026-01-12T16:00:00+08:00',independent=True)
    r2['tape']=day_tape('2026-01-09',b='1',settlement='2026-01-12')
    return dict(schema='capital-quantity-replay-input/0.1',synthetic=True,initial_account=account,origin_ledger=origin,
        ledger_close_proof=deepcopy(old['ledger_close_proof']),run_policy=dict(version='explicit-synthetic-round-budget/0.1',
            parameter_source='ENGINEERED_SYNTHETIC_REPLAY_NOT_STRATEGY',available_at='2026-01-05T14:00:00+08:00',max_rounds='8'),rounds=[r1,r2])


def waiting():
    r=partial();r['initial_account']['settled_cash']='100';r['origin_ledger']['opening']['cash']='100'
    first=r['rounds'][0];first['observed_until']='2026-01-09T16:00:00+08:00'
    for o in first['orders']:o['expires_at']='2026-01-12T16:00:00+08:00'
    first['tape']=day_tape('2026-01-06',a='50',b='20',settlement='2026-01-08')+day_tape('2026-01-09',b='20',settlement='2026-01-12')
    base=load(ROOT/'quantity_candidates_v02_20261026/cases/first-manual-grid/input.json')
    second=frame(base,'r2','2026-01-09T16:00:00+08:00','2026-01-09T17:00:00+08:00','ADDITIONAL_BATCH',0,1,'2026-01-12','2026-01-12T16:00:00+08:00',independent=True)
    second['cancelled_order_ids']=['r1-B'];second['tape']=day_tape('2026-01-12',b='1',settlement='2026-01-12')
    r['rounds'][1]=second
    return r


def cases():
    out={}
    def add(name,data,**expected):out[name]=dict(input=data,expected=expected)
    add('partial-then-independent',partial(),status='COMPLETED_PROVIDED_ROUNDS',execution_calls=2,total_fills=3,
        first_shares=dict(A='80',B='7',C='2'),first_cash='1056.66',first_nav='2226.66',
        final_shares=dict(A='90',B='8',C='2'),final_cash='1115.64',final_nav='2225.64',origin_capital='2230')
    r=waiting();r['rounds']=r['rounds'][:1]
    add('settled-not-reapproved',r,status='COMPLETED_PROVIDED_ROUNDS',execution_calls=1,total_fills=1,
        final_shares=dict(A='50',B='0',C='2'),final_cash='596.5',waiting_order='r1-B')
    add('wait-then-new-review',waiting(),status='COMPLETED_PROVIDED_ROUNDS',execution_calls=2,total_fills=2,
        final_shares=dict(A='60',B='1',C='2'),final_cash='655.48',final_nav='1325.48',origin_capital='1330',cancelled_order='r1-B')
    r=partial();second=r['rounds'][1];second['decision_template']['assets']['B']['evidence']=second['decision_template']['assets']['B']['evidence'][:1]
    second['decision_template']['assets']['B']['capital_eligibility']['evidence_ids']=['B-event'];second['quantity_template']['trigger_ids']=['B-event']
    add('old-trigger-blocked',r,status='STOPPED_CANDIDATE_GATE',execution_calls=1,total_fills=2,reason='NO_NEW_INDEPENDENT_TRIGGER')
    r=partial();r['rounds'][1]['quantity_template']['batch_context']['phase']='FIRST_ENTRY';r['rounds'][1]['quantity_template']['trigger_ids']=[]
    add('false-first-blocked',r,status='STOPPED_CANDIDATE_GATE',execution_calls=1,total_fills=2,reason='FIRST_ENTRY_CONTRADICTS_B_EPISODE_HISTORY')
    r=partial();r['rounds'][1]['decision_template']['assets']['B']['evidence'][-1]['volume_bar_id']='B-bar'
    add('shared-bar-blocked',r,status='STOPPED_CANDIDATE_GATE',execution_calls=1,total_fills=2,reason='NO_NEW_INDEPENDENT_TRIGGER')
    r=partial();r['rounds']=r['rounds'][:1];r['rounds'][0]['tape'][-1]['market_state']='LIMIT_UP_NO_BUY'
    add('limit-up-unfilled',r,status='COMPLETED_PROVIDED_ROUNDS',execution_calls=1,total_fills=1,final_shares=dict(A='80',B='0',C='2'))
    r=partial();r['rounds']=r['rounds'][:1];first=r['rounds'][0]
    for a in first['decision_template']['assets'].values():a['group']='shared'
    first['decision_template']['risk_limits']['group_value']={'shared':'1300'}
    first['tape'][0]['market_state']='LIMIT_DOWN_NO_SELL';first['tape'][0]['capacity_shares']='50';first['tape'][-1]['capacity_shares']='20'
    add('unsold-A-joint-risk',r,status='COMPLETED_PROVIDED_ROUNDS',execution_calls=1,total_fills=0,
        final_shares=dict(A='100',B='0',C='2'),reason='ACTUAL_RIGHTS_AND_POSSIBLE_FILLS_EXCEED_RISK_OR_MARKS_STALE')
    r=partial();r['rounds'][0]['reassessments']=[]
    add('embedded-review-refused',r,status='STOPPED_INPUT_ERROR',execution_calls=0,reason='ROUND_FIELDS_NOT_SUPPORTED')
    r=partial();r['rounds'][0]['observed_until']='2026-01-07T16:00:00+08:00'
    base=load(ROOT/'quantity_candidates_v02_20261026/cases/first-manual-grid/input.json')
    second=frame(base,'r2','2026-01-07T16:00:00+08:00','2026-01-07T17:00:00+08:00','ADDITIONAL_BATCH',0,1,'2026-01-09','2026-01-12T16:00:00+08:00',independent=True)
    second['cancelled_order_ids']=['r1-A','r1-B'];second['tape']=day_tape('2026-01-09',b='1',settlement='2026-01-12');r['rounds'][1]=second
    add('opening-payable-unsupported',r,status='STOPPED_NOT_IMPLEMENTED',execution_calls=1,total_fills=2,reason='OPENING_PAYABLE_CONTINUATION_NOT_IMPLEMENTED',pending_payable='141.14')
    r=partial();r['ledger_close_proof']['closes']['2026-01-08']['available_at']='2026-01-08T16:30:00+08:00'
    second=frame(base,'r2','2026-01-08T16:00:00+08:00','2026-01-08T16:01:00+08:00','ADDITIONAL_BATCH',0,1,'2026-01-09','2026-01-12T16:00:00+08:00',independent=True)
    second['tape']=day_tape('2026-01-09',b='1',settlement='2026-01-12');r['rounds'][1]=second
    add('close-not-yet-known',r,status='STOPPED_INPUT_ERROR',execution_calls=1,total_fills=2,reason='LEDGER_CLOSE_NOT_YET_AVAILABLE')
    r=partial();r['rounds'][1]['decision_template']['account']=deepcopy(r['initial_account'])
    add('account-reset-refused',r,status='STOPPED_INPUT_ERROR',execution_calls=1,total_fills=2,reason='TEMPLATE_ACCOUNT_OR_PLANS_FORBIDDEN')
    r=partial();r['rounds']=r['rounds'][:1]
    add('prefix-only',r,status='COMPLETED_PROVIDED_ROUNDS',execution_calls=1,total_fills=2)
    for name,prices in [('future-A-wins',dict(A='100',B='1',C='25')),('future-B-wins',dict(A='1',B='100',C='25')),('future-both-fall',dict(A='1',B='1',C='25'))]:
        r=partial();r['rounds']=r['rounds'][:1]
        for c,p in prices.items():r['origin_ledger']['assets'][c]['quotes']['2026-01-12']=p
        add(name,r,status='COMPLETED_PROVIDED_ROUNDS',execution_calls=1,total_fills=2,same_numeric_prefix_as='prefix-only')
    r=partial();r['rounds'][0]['quantity_template']['batch_context']['phase']='UNKNOWN'
    add('outer-gate-before-execution',r,status='STOPPED_CANDIDATE_GATE',execution_calls=0,reason='BATCH_PHASE_UNKNOWN')
    return out
