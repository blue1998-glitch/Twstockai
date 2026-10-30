"""Small synthetic policy competition through original-ledger account chains.

Targets are supplied research intents, not newly approved strategy formulas.
Each review explicitly cancels old outstanding orders; unsupported unsettled
opening payables refuse a new round instead of being converted to free capital.
"""
from copy import deepcopy
from datetime import date
from decimal import Decimal,localcontext
from graph_core.core import fingerprint
from .core import decide,resume_decision,costs,quantity,number
from .continuity import make_checkpoint,account_at_checkpoint
from .execution import simulate
from .trend import evaluate,competing_targets
from .trend_fixtures import POLICIES


def _input(fixture,frame,account,targets,trend_record):
    d=deepcopy(fixture['base_input']);d['decision_at']=frame['decision_at'];d['data_cutoff']=frame['data_cutoff'];d['account']=deepcopy(account)
    for c,a in d['assets'].items():
        mark=deepcopy(a['marks'][0]);mark.update(price=fixture['origin']['assets'][c]['quotes'][frame['data_cutoff'][:10]],
            occurred_at=frame['data_cutoff'],available_at=frame['data_cutoff']);a['marks']=[mark]
    # The decision identity must bind the *current* trend evidence even when
    # two reviews happen to propose the same target. Never reuse only the seed.
    d['parameter_source']='SYNTHETIC_TREND_REVIEW:'+trend_record['record_id']
    a=d['assets']['A'];a['evidence']=[]
    mapping=dict(box='box',dense_volume_peaks='price_volume',point_line_steps='key_position',
                 momentum_repair='momentum',dynamic_balance='momentum',cross_scale='cross_scale')
    compatible=all(frame['binding'][k]==a[k] for k in ('source_id','basis_id','adjustment_version'))
    for feature,rows in frame['evidence'].items():
        for e in rows:
            a['evidence'].append(dict(id=e['id'],feature=mapping[feature],stance=e['stance'] if compatible else 'unknown',
                value=dict(trend_record_id=trend_record['record_id'],original_evidence_id=e['id'],
                    qualification='DECLARED_SYNTHETIC_FACT' if compatible else 'SOURCE_BASIS_CHANGED_NO_CROSS_BASIS_VALUE_COMPARISON'),
                occurred_at=e['occurred_at'],available_at=e['available_at'],formation_id='review-'+frame['data_cutoff'],
                event_id=e['id'],volume_bar_id=frame['data_cutoff'] if feature=='dense_volume_peaks' else None,
                source_id=a['source_id'],basis_id=a['basis_id'],adjustment_version=a['adjustment_version']))
            if compatible and 'validity' in e:a['evidence'][-1]['validity']=deepcopy(e['validity'])
    a['capital_eligibility']=dict(schema='capital-entry-review/0.1',code='A',
        status='QUALIFIED_SYNTHETIC_RESEARCH' if trend_record['additional_capital_qualification']=='CONDITIONAL_RESEARCH_ONLY' else 'NOT_QUALIFIED',
        data_cutoff=frame['data_cutoff'],assessed_at=frame['decision_at'],available_at=frame['decision_at'],
        evidence_ids=deepcopy(trend_record['evidence_ids']),source_ids=[a['source_id']],
        source_id=a['source_id'],basis_id=a['basis_id'],adjustment_version=a['adjustment_version'])
    for code,r in frame.get('capital_reviews',{}).items():
        if code=='A':raise ValueError('A capital review must bind the current trend qualification')
        d['assets'][code]['capital_eligibility']=deepcopy(r)
    d['plans']=[dict(id=p,family='E',route='R1',targets=deepcopy(targets[p]),trigger_ids=[],edge_budget='1000',
                    conditions=['EXPLICIT_SYNTHETIC_REVIEW_INTENT_NOT_APPROVED_RULE']) for p in POLICIES]
    return d


def _orders(data,policy,round_number,next_day):
    target=next(p['targets'] for p in data['plans'] if p['id']==policy);orders=[]
    for c,n in target.items():
        change=quantity(n)-quantity(data['account']['holdings'][c]['shares'])
        if not change:continue
        price=number(data['assets'][c]['marks'][0]['price'])
        # Explicit fixture limit band, calculated at the decision, never at a future open.
        limit=price*(Decimal('1.20') if change>0 else Decimal('0.80'))
        orders.append(dict(id=f'{policy}-r{round_number}-{c}',code=c,side='BUY' if change>0 else 'SELL',shares=str(abs(change)),
            limit_price=str(limit),decision_at=data['decision_at'],submitted_at=next_day+'T08:00:00+08:00',
            expires_at=data['data_cutoff'][:10]+'T23:59:59+08:00'))
    return orders


def portfolio_metrics(result,market,labels):
    root=number(result['ledger']['initial_equity'])
    curve=[];peak=root;drawdown=Decimal(0);underwater_since=None;max_duration=0;cash_weights=[];participation=[]
    for row in result['ledger']['daily']:
        if row['net_accrual_equity'] is None or row['share_receivables']:
            return dict(status='REFUSED_UNPRICED_OR_UNTRADABLE_RIGHTS',geometric_growth=None)
        nav=number(row['net_accrual_equity']);exit_cost=Decimal(0)
        for c,n in row['shares'].items():
            if not number(n):continue
            value=number(n)*number(row['marks'][c]['value']);proceeds=costs(number(n),row['marks'][c]['value'],market['base_input']['cost_model'],'SELL')['cash']
            exit_cost+=value-proceeds
        net=nav-exit_cost
        if net<=0:return dict(status='REFUSED_NONPOSITIVE_EQUITY',geometric_growth=None)
        if peak is None or net>=peak:
            peak=net
            if underwater_since is not None:
                max_duration=max(max_duration,(date.fromisoformat(row['date'])-underwater_since).days);underwater_since=None
        else:
            if underwater_since is None:underwater_since=date.fromisoformat(row['date'])
            max_duration=max(max_duration,(date.fromisoformat(row['date'])-underwater_since).days)
        drawdown=min(drawdown,net/peak-1)
        cash_weights.append(number(row['available_cash_strict'])/nav)
        named=labels['named_asset'];participation.append(number(row['shares'][named])*number(row['marks'][named]['value'])/nav)
        curve.append(dict(date=row['date'],net_liquidation_estimate=str(net),accrual_equity=str(nav),estimated_exit_cost=str(exit_cost)))
    terminal=number(curve[-1]['net_liquidation_estimate'])
    quotes={(t['at'][:10],t['code']):number(t['price']) for t in market['common_tape']}
    slippage=sum((quantity(f['shares'])*abs(number(f['price'])-quotes[(f['date'],f['code'])]) for f in result['fills']),Decimal(0))
    return dict(status='SYNTHETIC_WHOLE_ACCOUNT_NOT_MARKET_VALIDATION',initial_capital=str(root),
        terminal_net_liquidation_estimate=str(terminal),geometric_growth=str(terminal/root-1),
        maximum_drawdown=str(drawdown),maximum_drawdown_duration_calendar_days=max_duration,
        recovery_censored=underwater_since is not None,fill_fee_tax=result['ledger']['fees_and_tax_on_fills'],
        effective_price_slippage=str(slippage),nominal_cash_price_return='0',
        mean_settled_available_cash_weight=str(sum(cash_weights)/len(cash_weights)),
        mean_equity_weight_in_ex_post_named_asset=str(sum(participation)/len(participation)),
        winner_participation_label_role='EVALUATION_ONLY_NOT_A_POLICY_INPUT',
        portfolio_peak_to_terminal_drawdown=str(terminal/max(number(x['net_liquidation_estimate']) for x in curve)-1),
        actual_terminal_pending_cash_claims=deepcopy(result['ledger']['daily'][-1]['cash_claims']),
        actual_terminal_purchase_payable=result['ledger']['daily'][-1]['purchase_payable'],
        matched_realized_exposure_control='NOT_IMPLEMENTED_SHARED_CAPS_ARE_NOT_EQUAL_REALIZED_EXPOSURE',
        perfect_hindsight_exit_benchmark=None,curve=curve)


def run_fixture(fixture):
    with localcontext() as ctx:
        ctx.prec=50
        return _run(fixture)


def _run(fixture):
    if fixture['synthetic'] is not True:raise ValueError('Only explicit synthetic policy fixtures supported')
    outputs={};common_origin=fingerprint(fixture['origin']);common_market=fingerprint(fixture['common_tape'])
    for policy in POLICIES:
        current=None;previous_decision=None;history=[];rounds=[];first_decision_id=None
        for i,frame in enumerate(fixture['frames'][:-1]):
            frame=deepcopy(frame);next_cutoff=fixture['frames'][i+1]['data_cutoff'];next_day=next(t['at'][:10] for t in fixture['common_tape'] if t['at'][:10]>frame['data_cutoff'][:10])
            continuation=None
            if current is None:
                account=deepcopy(fixture['base_input']['account']);account.update(as_of=frame['data_cutoff'],available_at=frame['data_cutoff'])
            else:
                cp=make_checkpoint(fixture['origin'],current,through_at=frame['data_cutoff'])
                cancellations=[o['order']['id'] for o in cp['state']['unfilled_orders']]
                try:account=account_at_checkpoint(cp,decision_at=frame['decision_at'],cancelled_order_ids=cancellations)
                except ValueError as e:
                    outputs[policy]=dict(status='NOT_IMPLEMENTED_AT_THIS_REVIEW',reason=str(e),rounds=rounds,last_execution=current)
                    break
                continuation=dict(previous_decision=previous_decision,checkpoint=cp,cancelled_order_ids=cancellations)
            q={c:x['shares'] for c,x in account['holdings'].items()}
            # Hard limits are evaluated from the actual current account, not winner labels.
            if number(q['A'])*number(frame['price'])>number(fixture['base_input']['risk_limits']['single_name_value']['A']):
                frame['hard_risk_breaches'].append('SINGLE_NAME_A')
            history.append(frame)
            trend_input=deepcopy(fixture['trend_input']);trend_input['records']=deepcopy(history)
            state=evaluate(trend_input,decision_at=frame['decision_at'])['records'][-1]
            targets=competing_targets(frame,state,q);data=_input(fixture,frame,account,targets,state)
            decision=resume_decision(previous_decision,data,checkpoint=cp,cancelled_order_ids=cancellations) if continuation else decide(data)
            if first_decision_id is None:first_decision_id=decision['decision']['decision_id']
            selected=next(p for p in decision['decision']['layer3']['alternatives'] if p['id']==policy)
            selected_id=policy if selected['feasible'] else 'A-zero'
            orders=_orders(data,policy,i,next_day) if selected['feasible'] else []
            for order in orders:order['expires_at']=next_cutoff[:10]+'T16:00:00+08:00'
            tape=[deepcopy(t) for t in fixture['common_tape'] if frame['data_cutoff'][:10]<t['at'][:10]<=next_cutoff[:10]]
            work=dict(schema='capital-execution-input/0.1',decision_input=data,plan_id=selected_id,ledger_input=fixture['origin'],
                      orders=orders,tape=tape,observed_until=next_cutoff,ledger_close_proof=fixture['ledger_close_proof'])
            if continuation:work['continuation']=continuation
            current=simulate(work)
            if current['status']!='SYNTHETIC_EXECUTION_REPLAY':
                outputs[policy]=dict(status='REFUSED_EXECUTION',refusal=current,rounds=rounds);break
            rounds.append(dict(review=i,point_in_time_trend=state,decision=decision,
                selected_policy_proposal=selected,execution_plan_id=selected_id,
                checkpoint_id=continuation['checkpoint']['checkpoint_id'] if continuation else None,
                cancelled_order_ids=continuation['cancelled_order_ids'] if continuation else [],
                new_fill_ids=current['new_fill_ids'],execution=current))
            previous_decision=decision
        else:
            outputs[policy]=dict(status='COMPLETED_SYNTHETIC_SEQUENCE',first_decision_id=first_decision_id,
                origin_ledger_input_id=common_origin,common_market_path_id=common_market,rounds=rounds,
                observed_risk_breach_count=sum(any(number(v)>0 for v in o['actual_violations'].values()) for rr in rounds for o in rr['execution']['risk_observations']),
                qualification='OBSERVATIONAL_ZERO_TRADE_CONTROL_NOT_RISK_QUALIFIED_RECOMMENDATION' if policy=='original_baseline' else 'SYNTHETIC_POLICY_INTENT_SUBJECT_TO_EXECUTION_RISK_GATES',
                metrics=portfolio_metrics(current,fixture,fixture['evaluation_labels']))
    return dict(schema='trend-policy-competition/0.2',synthetic=True,origin_ledger_input_id=common_origin,
        common_market_path_id=common_market,policy_results=outputs,ranking=None,
        evaluation_qualification='WHOLE_ACCOUNT_SYNTHETIC_COUNTEREXAMPLES_NOT_STRATEGY_OR_R1_R2_EVIDENCE',
        R2_F='NOT_IMPLEMENTED',data_qualified=False,execution_model_qualified=False,
        historical_signal_eligible=False,policy_authorized=False,live_execution_authorized=False)
