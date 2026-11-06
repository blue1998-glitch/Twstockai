"""Nine hypothetical future paths, a common prefix, and five competing intents.

All prices/calendars/event semantics are designed fixtures, never market data.
"""
from copy import deepcopy
from datetime import date,timedelta
from decimal import Decimal,localcontext
from .fixtures import fixture,ledger,binding
from .trend import FEATURES

POLICIES=('original_baseline','structure_hold','flexible_participation','adaptive_exit','account_reallocation')
PATHS={
    'staircase_up':(['10','13','16','19','23','28'],['STRENGTHENING']*6),
    'direct_acceleration':(['10','18','29','42','56','72'],['STRENGTHENING']*6),
    'deep_drawdown_then_resume':(['10','14','8','11','17','25'],['STRENGTHENING','STRENGTHENING','WEAKENING','STRENGTHENING','STRENGTHENING','STRENGTHENING']),
    'surge_then_collapse':(['10','17','29','18','8','4'],['STRENGTHENING','STRENGTHENING','STRENGTHENING','WEAKENING','WEAKENING','WEAKENING']),
    'sideways_opportunity_cost':(['10','10.2','9.9','10.1','10','10.1'],['STRENGTHENING','CONSOLIDATING','CONSOLIDATING','CONSOLIDATING','CONSOLIDATING','CONSOLIDATING']),
    'limits_unfilled':(['10','14','16','9','7','12'],['STRENGTHENING','STRENGTHENING','CONSOLIDATING','WEAKENING','WEAKENING','STRENGTHENING']),
    'source_basis_change':(['10','13','15','16','19','21'],['STRENGTHENING']*6),
    'industry_reversal':(['10','14','18','12','8','6'],['STRENGTHENING','STRENGTHENING','STRENGTHENING','WEAKENING','WEAKENING','WEAKENING']),
    'exit_repair_reentry':(['10','13','8','11','16','24'],['STRENGTHENING','STRENGTHENING','WEAKENING','STRENGTHENING','STRENGTHENING','STRENGTHENING'])}


def path_fixture(name):
    if name not in PATHS:raise ValueError('Explicit synthetic path required')
    prices,states=PATHS[name]
    start=date(2026,1,5);sessions=[];day=start
    while len(sessions)<18:
        if day.weekday()<5:sessions.append(day.isoformat())
        day+=timedelta(days=1)
    reviews=[sessions[i] for i in (0,3,6,9,12,15)]
    data=fixture()
    for a in data['assets'].values():a['group']='shared'
    data['risk_limits']['group_value']={'shared':'3000'}
    origin=ledger(data);origin['end']=sessions[-1]
    dates=[(start+timedelta(days=i)).isoformat() for i in range((date.fromisoformat(sessions[-1])-start).days+1)]
    origin['calendar']=[dict(date=d,trading=d in sessions) for d in dates]
    points={'A':prices,'B':['20','21','23','26','29','33'],'C':['25','26','28','31','35','40']}
    if name=='industry_reversal':points.update(B=['20','23','27','17','11','7'],C=['25','29','34','21','14','9'])
    with localcontext() as ctx:
        ctx.prec=50
        for c,ps in points.items():
            quotes={}
            for i,d in enumerate(sessions):
                if i%3==0 and i<=15:
                    quotes[d]=ps[i//3]
                    continue
                k=min(i//3,4);fraction=Decimal(min(i,15)-3*k)/3
                quotes[d]=str(Decimal(ps[k])+(Decimal(ps[k+1])-Decimal(ps[k]))*fraction)
            origin['assets'][c]['quotes']=quotes
            origin['coverage'][c]['end']=origin['end']
    tape=[]
    for i,d in enumerate(sessions[1:16],1):
        settlement=sessions[i+2]
        for minute,c in enumerate(('A','B','C')):
            state='OPEN'
            if name=='limits_unfilled' and 10<=i<=12:
                state='LIMIT_DOWN_NO_SELL' if c=='A' else 'LIMIT_UP_NO_BUY'
            tape.append(dict(at=d+f'T09:0{minute}:00+08:00',available_at=d+f'T09:0{minute}:00+08:00',
                code=c,price=origin['assets'][c]['quotes'][d],capacity_shares='500',market_state=state,
                settlement_date=settlement,source_id='fixture',basis_id='RAW:fixture:'+c,
                version='synthetic-tape/0.1',qualification='EXPLICIT_SYNTHETIC_OBSERVATION'))
    b=binding('A');b['code']='A'
    ref=dict(id='original-major',price='15',available_at='2026-01-05T14:00:00+08:00',binding=deepcopy(b),role='EXPLICIT_SYNTHETIC_MAJOR_REFERENCE')
    frames=[]
    for i,(d,p,state) in enumerate(zip(reviews,prices,states)):
        cutoff=d+('T14:00:00+08:00' if i==0 else 'T16:00:00+08:00');decision=d+('T15:00:00+08:00' if i==0 else 'T17:00:00+08:00')
        rb=deepcopy(b)
        if name=='source_basis_change' and i>=2:rb.update(basis_id='ADJUSTED:unvalidated-new-basis',adjustment_version='UNKNOWN_NEW_VERSION')
        evidence={}
        for f in FEATURES:
            stance='refutation' if state=='WEAKENING' and f in ('box','dynamic_balance') else 'support'
            evidence[f]=[dict(id=f+'-'+d,source_id='fixture',binding=deepcopy(rb),stance=stance,
                             occurred_at=cutoff,available_at=cutoff)]
        price=Decimal(p);budget_shares=min(100,int(Decimal('2800')/price))
        participation=min(budget_shares,([100,77,43,61,35,82][i]))
        adaptive=budget_shares if state!='WEAKENING' else 0
        if i==0:participation=100
        pressure='UPPER_PRESSURE_REMAINS' if price<=15 else 'BROKEN_OLD_REFERENCE'
        alt_supported=(i>=2 and name=='sideways_opportunity_cost') or (i>=3 and name=='limits_unfilled')
        account=dict(A='0',B='35',C='0') if alt_supported else dict(A=str(budget_shares if state!='WEAKENING' else 0),B='0',C='0')
        frames.append(dict(decision_at=decision,data_cutoff=cutoff,available_at=cutoff,binding=rb,price=p,
            evidence=evidence,structure_state=state,invalidation_confirmed=state=='WEAKENING',hard_risk_breaches=[],
            pressure=dict(status=pressure,crossed_reference_ids=['original-major'] if price>15 else [],checked_scope=None),
            new_capital_evidence_qualified=False,
            extension_reasons=['EXPLICIT_POINT_IN_TIME_STRUCTURE_AND_ALTERNATIVES_REVIEW'],
            alternative_opportunities=[dict(code='A',role='INCUMBENT',evidence_id='box-'+d),
                dict(code='B',role='ALTERNATIVE_SUPPORTED' if alt_supported else 'ALTERNATIVE_UNDISTINGUISHED',evidence_id='alternative-'+d),
                dict(code='CASH',role='AVAILABLE_OPTION')],
            reached_original_target=price>=Decimal('12'),elapsed_sessions=i*3,
            baseline_exit_trigger=price>=Decimal('12'),structure_shares=str(budget_shares),
            participation_shares=str(participation),adaptive_shares=str(adaptive),account_targets=account))
    return dict(schema='trend-policy-fixture/0.1',synthetic=True,name=name,origin=origin,base_input=data,
        common_tape=tape,reviews=reviews,frames=frames,trend_input=dict(schema='trend-continuation-input/0.1',
            synthetic=True,binding=b,references=[ref],records=deepcopy(frames)),
        evaluation_labels=dict(named_asset='A',role='EX_POST_EVALUATION_ONLY_NEVER_AVAILABLE_TO_POLICY'),
        calendar_qualification='EXPLICIT_SYNTHETIC_WEEKDAY_CALENDAR_NOT_AUTHENTICATED_TAIWAN_CALENDAR',
        settlement_qualification='EXPLICIT_SECOND_FOLLOWING_SYNTHETIC_SESSION; CALENDAR_EXTENDS_BEYOND_EVALUATION_END')
