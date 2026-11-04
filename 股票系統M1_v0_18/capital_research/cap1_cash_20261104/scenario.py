"""Explicit NEW synthetic opening. Never a repair/relabel of the old account."""
from copy import deepcopy
from pathlib import Path
import json
from ..cash_action import evaluate
from ..cash_action_execution import execute
from ..core import fingerprint

CAP=Path(__file__).resolve().parent
ROOT=CAP.parents[2]
OLD=CAP.parent/'cap1_20261104'

def original_case():return json.loads((OLD/'artifacts/journal/cap1-reduce.json').read_bytes())['value']

def template_at(template,cutoff,decision):
    t=deepcopy(template);t.update(data_cutoff=cutoff,decision_at=decision)
    for code,a in t['assets'].items():
        a['marks']=[dict(a['marks'][0],occurred_at=cutoff,available_at=cutoff)]
        a['capital_eligibility'].update(data_cutoff=cutoff,assessed_at=decision,available_at=decision)
    return t


def declaration():
    old=original_case()['saved_result']['action_request'];origin=deepcopy(old['execution_spec']['origin_ledger'])
    # NEW declared account: all opening shares are already tradable, no receivables.
    # These explicit synthetic conditions do not cancel any old C entitlement.
    origin['opening']=dict(cash='1000',shares={'A':'0','B':'7','C':'4'},cash_claims=[],share_claims=[])
    origin['fills']=[]
    proof=deepcopy(old['execution_spec']['ledger_close_proof'])
    seed_time='2026-01-05T15:00:00+08:00';decision='2026-01-06T17:00:00+08:00'
    t=template_at(old['action_input']['decision_template'],'2026-01-05T14:00:00+08:00',seed_time)
    account=dict(as_of=t['data_cutoff'],available_at=seed_time,
        holdings={c:dict(shares=n,sellable=n) for c,n in origin['opening']['shares'].items()},
        settled_cash='1000',reserved_cash='100',cash_claims=[],share_claims=[],pending_orders=[],payables=[])
    policy=deepcopy(old['action_input']['policy']);policy['available_at']=seed_time
    hold=dict(id='cap1-settled-opening',kind='HOLD',code=None,additional_shares='0',trigger_ids=[],batch_context=None)
    seed_input=dict(schema='capital-cash-action-input/0.1',synthetic=True,decision_template=t,
        account_source=dict(kind='DECLARED_SYNTHETIC_OPENING',account=account,consumed_evidence_tokens=[]),action=hold,policy=policy)
    seed_spec=dict(id='cap1-settled-opening',origin_ledger=origin,ledger_close_proof=proof,orders=[],tape=[],observed_until='2026-01-06T16:00:00+08:00')
    shared_template=template_at(t,'2026-01-06T16:00:00+08:00',decision)
    policy=deepcopy(policy);policy['available_at']=decision
    tape=[]
    for code,minute,price in [('B','00','20'),('C','01','25')]:
        at='2026-01-07T09:'+minute+':00+08:00'
        tape.append(dict(at=at,available_at=at,basis_id='RAW:fixture:'+code,capacity_shares='500',code=code,
            market_state='OPEN',price=price,qualification='EXPLICIT_SYNTHETIC_OBSERVATION',settlement_date='2026-01-09',source_id='fixture',version='synthetic-tape/0.1'))
    orders={}
    for key,sales in [('hold',{}),('reduce',{'B':'3'}),('partial',{'B':'7'}),('cash',{'B':'7','C':'4'})]:
        orders[key]=[dict(id='cap1-'+key+'-'+c,code=c,side='SELL',shares=n,limit_price={'B':'19.98','C':'24.975'}[c],
            decision_at=decision,submitted_at='2026-01-06T17:01:00+08:00',expires_at='2026-01-07T16:00:00+08:00') for c,n in sales.items()]
    return dict(schema='cap1-fully-settled-synthetic-declaration/0.1',synthetic=True,
        qualification='NEW_ACCOUNT_NOT_OLD_C_RIGHTS_RELEASE_NOT_MARKET_OR_BROKER_PROOF',
        original_source_commit='692594ee1567ac7f795da972a10ae6d89691f5e8',
        seed_input=seed_input,seed_execution_spec=seed_spec,decision_template=shared_template,policy=policy,
        tape=tape,orders=orders,observed_until='2026-01-12T16:00:00+08:00',evaluation_at='2026-01-12T16:00:00+08:00',
        source_precision='EXPLICIT_SYNTHETIC_DECIMAL_STRINGS_AND_WHOLE_SHARES',
        oracle=dict(initial_equity='1240',cash_end={'hold':'1000','reduce':'1057.940','partial':'1137.860','cash':'1235.760'},
            equity_end={'hold':'1240','reduce':'1237.940','partial':'1237.860','cash':'1235.760'},fees={'hold':'0','reduce':'2','partial':'2','cash':'4'},
            full_cash_not_before='2026-01-09',general_reserve='100',period=['2026-01-05','2026-01-12']))


def checked_request(action_input,spec):
    checked=evaluate(action_input)
    if checked['research']['status']!='CURRENTLY_FEASIBLE':raise ValueError(str(checked['research']))
    return dict(schema='capital-cash-action-execution-input/'+action_input['schema'].rsplit('/',1)[1],synthetic=True,
        action_input=action_input,checked_action=checked,expected_checked_action_id=fingerprint(checked),execution_spec=spec)


def seed(declared):
    request=checked_request(declared['seed_input'],declared['seed_execution_spec'])
    receipt=execute(request)
    if receipt['run']['status']!='REPLAYED_EXPLICIT_ACTION':raise ValueError(str(receipt['run']))
    return request,receipt


def inputs(declared,parent):
    cp=parent['run']['checkpoint'];account_source=dict(kind='CHECKPOINT',checkpoint=deepcopy(cp),
        expected_checkpoint_id=cp['checkpoint_id'],expected_latest_decision_id=cp['state']['latest_decision_id'])
    cases={}
    for name in ('hold','reduce','partial','cash'):
        i=dict(schema='capital-cash-action-input/0.1' if name=='hold' else 'capital-cash-action-input/0.2',synthetic=True,
            decision_template=deepcopy(declared['decision_template']),account_source=deepcopy(account_source),policy=deepcopy(declared['policy']))
        if name=='hold':i['action']=dict(id='new-hold',kind='HOLD',code=None,additional_shares='0',trigger_ids=[],batch_context=None)
        else:i['action']=dict(id='new-'+name,kind='REDUCE_HOLDING' if name=='reduce' else 'EXIT_SELLABLE_HOLDING',code='B',sell_shares='3' if name=='reduce' else '7',reason='EXPLICIT_SYNTHETIC_NOT_STRATEGY')
        spec=dict(id='new-'+name,origin_ledger=deepcopy(declared['seed_execution_spec']['origin_ledger']),
            ledger_close_proof=deepcopy(declared['seed_execution_spec']['ledger_close_proof']),orders=deepcopy(declared['orders'][name]),
            tape=deepcopy(declared['tape']),observed_until=declared['observed_until'])
        cases[name]=(i,spec)
    return cases
