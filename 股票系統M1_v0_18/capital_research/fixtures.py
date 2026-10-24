"""Explicitly imaginary prices, evidence, credit terms and calendars."""
from copy import deepcopy
from rotation_research.action_fixtures import fixture as ledger_fixture

CUTOFF='2026-01-05T14:00:00+08:00'
DECISION='2026-01-05T15:00:00+08:00'


def binding(code):
    return dict(source_id='fixture', basis_id='RAW:fixture:'+code, adjustment_version='RAW:synthetic/1')


def fixture():
    assets={}
    for c,p,ref,g in [('A','10','15','original'),('B','20','30','new'),('C','25','35','new')]:
        b=binding(c)
        e=dict(id=c+'-event',feature='price_volume',stance='support',value='EXPLICIT_SYNTHETIC_BREAKOUT',
               occurred_at=CUTOFF,available_at=CUTOFF,formation_id=c+'-formation',volume_bar_id=c+'-bar',
               event_id=c+'-event',**b)
        assets[c]=dict(**b,group=g,marks=[dict(price=p,occurred_at=CUTOFF,available_at=CUTOFF,
                       reference_role='VALUATION_MARK',**b)],evidence=[e],
            entry_context=dict(**b,available_at=CUTOFF,position='SYNTHETIC_POSITION',
                formal_reference=dict(**b,price=ref,occurred_at=CUTOFF,available_at=CUTOFF,reference_role='FORMAL_RESISTANCE',
                                      qualification='SYNTHETIC_NOT_MARKET_AUTHORITY'),
                invalidation_risk='SCENARIO_LOSS_NOT_STOP_FILL',liquidity_shares='500'))
    targets=lambda a,b,c:dict(A=str(a),B=str(b),C=str(c))
    def plan(key,family,t,trigger=None,route='R1'):
        return dict(id=key,family=family,route=route,targets=t,trigger_ids=trigger or [],
                    edge_budget='1000',conditions=['SYNTHETIC_EVENT_OR_RISK_BUDGET_REVIEW'])
    return dict(schema='capital-decision-input/0.1',synthetic=True,decision_at=DECISION,data_cutoff=CUTOFF,
        policy_version='R1-explicit-event-risk-budget/0.1',policy_available_at=CUTOFF,parameter_source='SYNTHETIC_MECHANISM_FIXTURE_NOT_USER_RULE',
        assets=assets,account=dict(as_of=CUTOFF,available_at=CUTOFF,
            holdings={c:dict(shares=n,sellable=n) for c,n in [('A','100'),('B','0'),('C','0')]},
            settled_cash='1000',reserved_cash='0',cash_claims=[],share_claims=[],payables=[],pending_orders=[]),
        cost_model=dict(version='synthetic-costs/0.1',available_at=CUTOFF,fee_rate='0.001',minimum_fee='1',sell_tax='0.003',slippage_bps='10'),
        execution_model=dict(version='synthetic-next-day-orders/0.1',available_at=CUTOFF,
                             buying_power='SETTLED_CASH_ONLY',broker_credit=None),
        risk_limits=dict(version='synthetic-risk/0.1',available_at=CUTOFF,
            single_name_value={c:'3000' for c in assets},group_value={'original':'3000','new':'3000'},
            account_stress_loss='3000',max_trade_shares={c:'500' for c in assets}),
        scenario_set=dict(version='synthetic-common-scenarios/0.1',available_at=CUTOFF,
            assumption='COMMON_IMAGINARY_STRESSES_KNOWN_AS_ASSUMPTIONS_AT_DECISION_NOT_FORECASTS',
            scenarios=[dict(id='A_wins',prices=dict(A='15',B='18',C='22')),
                       dict(id='B_accelerates',prices=dict(A='11',B='32',C='26')),
                       dict(id='both_fall',prices=dict(A='7',B='12',C='16'))]),
        no_trade_buffer='5',full_transfer_edge_budget='1000',consumed_evidence_tokens=[],
        plans=[plan('B-full','B',targets(0,99,0)),plan('C-event','C',targets(50,20,0),['B-event']),
               plan('D-cash','D',targets(0,0,0)),plan('E-joint','E',targets(50,10,10)),
               plan('F-min-regret','F',None,route='R2')],
        source_integrity_metadata=dict(full_source_fingerprint='SYNTHETIC_SOURCE_BASELINE',
                                       historical_availability='NOT_MARKET_DATA'))


def ledger(data=None):
    data=data or fixture();x=ledger_fixture()
    x['opening']=dict(cash=data['account']['settled_cash'],
        shares={c:v['shares'] for c,v in data['account']['holdings'].items()},
        cash_claims=deepcopy(data['account']['cash_claims']),share_claims=deepcopy(data['account']['share_claims']))
    x['assets']['C']=deepcopy(x['assets']['B']);x['assets']['C']['basis_id']='RAW:fixture:C'
    x['coverage']['C']=deepcopy(x['coverage']['B'])
    for c in x['assets']:
        p=data['assets'][c]['marks'][0]['price']
        x['assets'][c]['quotes']={d:p for d in x['assets'][c]['quotes']}
    x['terminal_costs']={k:data['cost_model'][k] for k in ('fee_rate','minimum_fee','sell_tax','slippage_bps')}
    return x


def observation(code,when,price=None,capacity='500',state='OPEN',settlement=None):
    return dict(at=when,available_at=when,code=code,price=price or {'A':'10','B':'20','C':'25'}[code],
        capacity_shares=capacity,market_state=state,settlement_date=settlement or when[:10],
        version='synthetic-tape/0.1',qualification='EXPLICIT_SYNTHETIC_OBSERVATION',
        source_id='fixture',basis_id='RAW:fixture:'+code)


def order(key,side,code,n,limit):
    return dict(id=key,code=code,side=side,shares=str(n),limit_price=limit,decision_at=DECISION,
                submitted_at='2026-01-06T08:00:00+08:00',expires_at='2026-01-12T16:00:00+08:00')


def job(plan_id='B-full',data=None):
    data=deepcopy(data or fixture());p=next((p for p in data['plans'] if p['id']==plan_id),None)
    targets={c:v['shares'] for c,v in data['account']['holdings'].items()} if plan_id=='A-zero' else p['targets']
    orders=[]
    for c,t in targets.items():
        delta=int(t)-int(data['account']['holdings'][c]['shares'])
        if delta:orders.append(order(c+('-buy' if delta>0 else '-sell'),'BUY' if delta>0 else 'SELL',c,abs(delta),'100' if delta>0 else '0.01'))
    # A narrow bounded buy price, enough to include the declared slippage.
    for o in orders:
        if o['side']=='BUY':o['limit_price']={'B':'20.03','C':'25.04','A':'10.02'}[o['code']]
    return dict(schema='capital-execution-input/0.1',decision_input=data,plan_id=plan_id,
        ledger_input=ledger(data),orders=orders,observed_until='2026-01-12T16:00:00+08:00',
        tape=[observation('A','2026-01-06T09:00:00+08:00',settlement='2026-01-08'),
              observation('B','2026-01-06T09:01:00+08:00',settlement='2026-01-08'),
              observation('B','2026-01-09T09:00:00+08:00',settlement='2026-01-12'),
              observation('C','2026-01-09T09:01:00+08:00',settlement='2026-01-12')])
