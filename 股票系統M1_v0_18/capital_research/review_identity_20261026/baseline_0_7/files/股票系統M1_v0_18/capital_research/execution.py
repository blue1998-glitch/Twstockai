"""Synthetic order adapter. The existing action_ledger owns all accounting.

Reservations and order states live here; no second share/cash posting engine.
Every observation replays explicit accepted fills through the unchanged ledger.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
from graph_core.core import fingerprint
from rotation_research.action_ledger import replay, qualify
from .core import decide, resume_decision, costs, quantity, timestamp, nonnegative, validate_costs, number
from .continuity import row_at, ledger_prefix, make_checkpoint, validate_checkpoint
from .transition_risk import inspect_risk
from .close_clock import close_record
from .eligibility import expired_entry_reasons
from .fact_lineage import source_snapshot, history_at, asset_issues, first_issue_at
from .reassessment_history import declaration_sources, reviewed_tokens, make_attempt

VERSION = 'capital-execution/0.7'


def _refusal(reason):
    return dict(schema=VERSION, status='REFUSED', refusal_reasons=[reason], fills=[], ledger=None,
                data_qualified=False, execution_model_qualified=False, historical_signal_eligible=False,
                policy_authorized=False, live_execution_authorized=False)


def simulate(job):
    with localcontext() as ctx:
        ctx.prec = 50
        return _simulate(job)


def _simulate(job):
    if job['schema'] != 'capital-execution-input/0.1':
        raise ValueError('Explicit isolated execution contract required')
    data = job['decision_input']
    continuation=job.get('continuation')
    if continuation:
        result=resume_decision(continuation['previous_decision'],data,checkpoint=continuation['checkpoint'],
                               cancelled_order_ids=continuation['cancelled_order_ids'])['decision']
    else:
        result = decide(data)['decision']
    selected = next((p for p in result['layer3']['alternatives'] if p['id'] == job['plan_id']), None)
    if selected is not None and selected['status']=='NOT_IMPLEMENTED':
        return _refusal('SELECTED_PLAN_NOT_IMPLEMENTED')
    observation_only=bool(selected is not None and not selected['feasible'] and job['plan_id']=='A-zero' and not job['orders'])
    if selected is None or (not selected['feasible'] and not observation_only):
        return _refusal('SELECTED_PLAN_NOT_FEASIBLE')
    if data['execution_model']['buying_power'] != 'SETTLED_CASH_ONLY':
        return _refusal('BROKER_CREDIT_ACCOUNTING_NOT_IMPLEMENTED_NO_SYNTHETIC_LOAN_OR_CASH')
    a = data['account']
    if a['payables']:
        return _refusal('OPENING_PAYABLE_REPLAY_NOT_SUPPORTED_BY_EXISTING_LEDGER')
    if a['pending_orders']:
        return _refusal('OPENING_PENDING_ORDER_REPLAY_NOT_IMPLEMENTED_DECISION_RESERVATIONS_SUPPORTED')
    ledger_input = deepcopy(job['ledger_input'])
    if ledger_input['fills']:
        raise ValueError('Explicit empty new fill path required')
    if (not continuation and ledger_input['start'] != data['data_cutoff'][:10]) or a['as_of'] != data['data_cutoff']:
        raise ValueError('Opening ledger/cutoff mismatch')
    expected = dict(cash=a['settled_cash'], shares={c:x['shares'] for c,x in a['holdings'].items()},
                    cash_claims=a['cash_claims'], share_claims=a['share_claims'])
    if (not continuation and ledger_input['opening'] != expected) or set(ledger_input['assets']) != set(data['assets']):
        raise ValueError('Unequal opening holdings/cash/rights')
    if continuation and ledger_input!=continuation['checkpoint']['origin_ledger_input']:
        raise ValueError('Continuous account must reuse the exact original ledger input')
    if any(s['kind'] != 'ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET' for s in ledger_input['sources'].values()):
        raise ValueError('Synthetic adapter cannot publish a real-data replay')
    for c, asset in ledger_input['assets'].items():
        if asset['source_id'] != data['assets'][c]['source_id'] or asset['basis_id'] != data['assets'][c]['basis_id']:
            raise ValueError('Ledger source/basis mismatch')
    reasons = qualify(ledger_input)
    if reasons:
        return _refusal('EXISTING_ACTION_LEDGER_REFUSED:' + '|'.join(reasons))
    clock=job.get('ledger_close_proof')
    opening_close=close_record(ledger_input,clock,data['data_cutoff'])
    close_record(ledger_input,clock,job['observed_until'])
    if timestamp(opening_close['available_at'])>timestamp(data['decision_at']):
        raise ValueError('LEDGER_CLOSE_NOT_YET_AVAILABLE')
    if continuation and clock!=continuation['checkpoint']['execution_result']['ledger_close_proof']:
        raise ValueError('Continuous account must reuse the exact close-availability proof')
    cfg = data['cost_model']; validate_costs(cfg)
    for k in ('fee_rate', 'minimum_fee', 'sell_tax', 'slippage_bps'):
        if ledger_input['terminal_costs'][k] != cfg[k]:
            raise ValueError('Decision/execution/terminal cost model mismatch')
    initial_fills=deepcopy(continuation['checkpoint']['state']['accepted_fills']) if continuation else []
    state = replay(dict(ledger_input,fills=initial_fills))
    if not state['daily'] or state['daily'][0]['net_accrual_equity'] is None:
        return _refusal('OPENING_LEDGER_UNAVAILABLE')
    opening_row=next(x for x in state['daily'] if x['date']==data['data_cutoff'][:10])
    if number(opening_row['net_accrual_equity']) != number(result['initial_capital']):
        raise ValueError('Opening valuation/capital mismatch')
    for c in data['assets']:
        mark = [m for m in data['assets'][c]['marks'] if m['occurred_at'] == data['data_cutoff'] and timestamp(m['available_at']) <= timestamp(data['decision_at'])]
        if len(mark) != 1 or number(ledger_input['assets'][c]['quotes'][data['data_cutoff'][:10]]) != number(mark[0]['price']):
            raise ValueError('Ledger opening mark differs from decision mark')
    orders = deepcopy(job['orders'])
    if len({o['id'] for o in orders}) != len(orders):
        raise ValueError('Duplicate order identity')
    requested = {c:Decimal(0) for c in data['assets']}
    for o in orders:
        if o['code'] not in requested or o['side'] not in ('BUY', 'SELL'):
            raise ValueError('Unknown order asset/side')
        n = quantity(o['shares'])
        if n <= 0 or number(o['limit_price']) <= 0:
            raise ValueError('Positive order/limit required')
        t = timestamp(o['decision_at'])
        if t != timestamp(data['decision_at']) or timestamp(o['submitted_at']) < t or timestamp(o['expires_at']) <= timestamp(o['submitted_at']):
            raise ValueError('Order decision/submission/expiry chronology mismatch')
        requested[o['code']] += n * (1 if o['side'] == 'BUY' else -1)
    for c, n in requested.items():
        delta = quantity(selected['targets'][c]) - quantity(a['holdings'][c]['shares'])
        if (n and n * delta < 0) or abs(n) > abs(delta):
            raise ValueError('Order exceeds selected target change')
    # Both gross buy and sell orders for one asset would defeat the net check.
    if any(len({o['side'] for o in orders if o['code']==c}) > 1 for c in requested):
        raise ValueError('Opposite same-asset orders require a separate decision')
    inherited=continuation['checkpoint']['execution_result'] if continuation else None
    order_state=deepcopy(inherited['order_states']) if inherited else {}
    order_history=deepcopy(inherited.get('order_history',inherited['orders'])) if inherited else []
    if set(order_state)&{o['id'] for o in orders}:
        raise ValueError('New order identity collides with earlier account history')
    decisions = []
    if continuation:
        for key in continuation['cancelled_order_ids']:
            at=result['continuity']['cancellation_effective_at']
            order_state[key].update(status='CANCELLED_AT_REVIEW',reserved_cash='0',cancelled_at=at)
            decisions.append(dict(at=at,order_id=key,status='CANCELLED_AT_REVIEW',
                                  reason='EXPLICIT_REVIEW_BEFORE_NEXT_DECLARED_TRADING_DATE'))
    for o in orders:
        order_state[o['id']]=dict(remaining=o['shares'],status='WAITING',reserved_cash='0',
            requires_reassessment=bool(o['side']=='BUY' and selected['funding']!='SETTLED'),
            active_decision_at=o['decision_at'],active_decision_id=result['decision_id'])
    order_history+=deepcopy(orders)
    initial_fill_count=len(initial_fills)
    fills = deepcopy(initial_fills)
    risk_observations=[];reassessments=[]
    decision_ids=deepcopy(inherited['decision_ids']) if inherited else []
    decision_records=deepcopy(inherited['decision_records']) if inherited else {}
    decision_ids.append(result['decision_id']);decision_records[result['decision_id']]=deepcopy(result)
    fact_sources=deepcopy(inherited['fact_sources']) if inherited else {}
    fact_sources[result['decision_id']]=source_snapshot(data)
    reassessment_attempts=deepcopy(inherited['reassessment_attempts']) if inherited else []
    fill_order_ids=deepcopy(inherited['fill_order_ids']) if inherited else {}
    unavailable=deepcopy(inherited['opening_unavailable_shares']) if inherited else {
        c:str(quantity(x['shares'])-quantity(x['sellable'])) for c,x in a['holdings'].items()}
    origin_common=inherited['origin_common_account_id'] if inherited else result['common_account_id']
    latest_result=result

    def knowledge():
        return dict(decision_ids=decision_ids,decision_records=decision_records,
                    fact_sources=fact_sources,reassessment_attempts=reassessment_attempts)

    def lineage():
        latest=decision_records[decision_ids[-1]]
        return dict(decision_ids=deepcopy(decision_ids),decision_records=deepcopy(decision_records),
            latest_decision_id=latest['decision_id'],latest_common_account_id=latest['common_account_id'],
            origin_common_account_id=origin_common,opening_unavailable_shares=deepcopy(unavailable),
            reviewed_evidence_tokens=reviewed_tokens(knowledge()),
            fill_order_ids=deepcopy(fill_order_ids),ledger_close_proof=deepcopy(clock),
            fact_sources=deepcopy(fact_sources),reassessment_attempts=deepcopy(reassessment_attempts))
    marks={c:dict(price=next(m['price'] for m in x['marks'] if m['occurred_at']==data['data_cutoff'] and timestamp(m['available_at'])<=timestamp(data['decision_at'])),
                        at=data['data_cutoff'],source_id=x['source_id'],basis_id=x['basis_id']) for c,x in data['assets'].items()}
    risk_data=data

    def cancel_known_restrictions(at, reason):
        sources=declaration_sources(knowledge())
        known_history=history_at(sources,at)
        for o in orders:
            st=order_state[o['id']]
            if o['side']!='BUY' or not number(st['remaining']) or st['status'].startswith(('CANCELLED','EXPIRED')):
                continue
            invalid=expired_entry_reasons(risk_data['assets'][o['code']],at)
            invalid+=asset_issues(known_history,o['code'],risk_data['assets'][o['code']],at,accepted_order=True)
            if invalid:
                effective=first_issue_at(sources,o['code'],risk_data['assets'][o['code']],
                    after=st['active_decision_at'],through=at,accepted_order=True) or at
                if timestamp(effective)>=timestamp(o['expires_at']):
                    continue
                st.update(status='CANCELLED_EVIDENCE',reserved_cash='0')
                decisions.append(dict(at=effective,observed_at=at,order_id=o['id'],
                    status='CANCELLED_EVIDENCE',reason=reason,details=invalid))

    calendar = {d['date']:d['trading'] for d in ledger_input['calendar']}
    tape = job['tape']
    times = [timestamp(x['at']) for x in tape]
    if times != sorted(set(times)):
        raise ValueError('Execution observations must be unique, chronological and explicit')
    for obs in tape:
        when = timestamp(obs['at']); day = obs['at'][:10]
        if day <= data['data_cutoff'][:10] or day > ledger_input['end'] or not calendar[day] or timestamp(obs['available_at']) > when:
            raise ValueError('Unsupported observation day/availability')
        if obs['version'] != 'synthetic-tape/0.1' or obs['qualification'] != 'EXPLICIT_SYNTHETIC_OBSERVATION':
            raise ValueError('Synthetic executable tape qualification required')
        asset = ledger_input['assets'][obs['code']]
        if obs['source_id'] != asset['source_id'] or obs['basis_id'] != asset['basis_id']:
            raise ValueError('Execution observation source/basis mismatch')
        if obs['market_state'] not in ('OPEN', 'LIMIT_UP_NO_BUY', 'LIMIT_DOWN_NO_SELL', 'HALTED'):
            raise ValueError('Unknown execution state is not a fill')
        if number(obs['price']) <= 0:
            raise ValueError('Missing/invalid execution price; never fill from a stop')
        capacity = quantity(obs['capacity_shares'])
        marks[obs['code']]=dict(price=obs['price'],at=obs['at'],source_id=obs['source_id'],basis_id=obs['basis_id'])
        # The tape supplies an explicit research settlement date, not inferred T+2.
        if obs['settlement_date'] not in calendar or obs['settlement_date'] < day:
            raise ValueError('Explicit in-window settlement date required')
        # Current intraday balance = prior day end, with today's accepted fills.
        current = replay(dict(ledger_input, fills=deepcopy(fills)))
        prior = [x for x in current['daily'] if x['date'] < day][-1]
        prior_close=close_record(ledger_input,clock,clock['closes'][prior['date']]['as_of'])
        if timestamp(prior_close['available_at'])>when:
            raise ValueError('LEDGER_CLOSE_NOT_YET_AVAILABLE_FOR_EXECUTION')
        cash = number(prior['available_cash_strict']) - nonnegative(a['reserved_cash'])
        sellable = {c:number(prior['shares'][c]) for c in data['assets']}
        for f in [f for f in fills if f['date']==day]:
            if f['side']=='BUY': cash -= number(f['shares'])*number(f['price'])+number(f['fee'])+number(f['tax'])
            else: sellable[f['code']] -= number(f['shares'])
        # Observed cancellation facts apply even if a conditional order is unfunded.
        if obs.get('evidence_status') in ('INVALIDATED','BASIS_CHANGED'):
            for o in orders:
                st=order_state[o['id']]
                if o['side']=='BUY' and o['code']==obs['code'] and number(st['remaining']):
                    st.update(status='CANCELLED_EVIDENCE',reserved_cash='0')
                    decisions.append(dict(at=obs['at'],order_id=o['id'],status='CANCELLED_EVIDENCE',reason=obs['evidence_status']))
        cancel_known_restrictions(obs['at'],'DECLARED_VALIDITY_ENDED')
        # Funding is not a reauthorization. A new decision must bind the actual
        # prior-close account, original fill path and explicit order cancellations.
        for review in job.get('reassessments',[]):
            o=next((o for o in orders if o['id']==review['order_id']),None)
            if o is None:raise ValueError('Reassessment references an unknown order')
            st=order_state[o['id']]
            fresh=review['decision_input']
            if (o['code']!=obs['code'] or review['id'] in {x['id'] for x in reassessment_attempts}
                    or timestamp(fresh['decision_at'])>when):continue
            if st['status'] in ('CANCELLED_EVIDENCE','EXPIRED_UNFILLED') or not number(st['remaining']):continue
            if fresh['data_cutoff'][:10]>=day or any(f['date']>fresh['data_cutoff'][:10] for f in fills):
                raise ValueError('Reassessment requires a genuine prior daily close with no later fill hidden')
            provisional=dict(schema=VERSION,status='SYNTHETIC_EXECUTION_REPLAY',decision_id=result['decision_id'],
                common_account_id=result['common_account_id'],origin_ledger_input_id=fingerprint(ledger_input),
                observed_until=fresh['data_cutoff'],orders=deepcopy(orders),order_history=deepcopy(order_history),
                order_states=deepcopy(order_state),fills=deepcopy(fills),**lineage())
            provisional['result_id']=fingerprint(provisional)
            cp=make_checkpoint(ledger_input,provisional,through_at=fresh['data_cutoff'])
            if review['checkpoint_id']!=cp['checkpoint_id']:
                raise ValueError('Reassessment checkpoint does not match executed fills, rights and unfilled orders')
            fresh_result=resume_decision(dict(decision=latest_result),fresh,checkpoint=cp,
                cancelled_order_ids=review['cancelled_order_ids'])['decision']
            if fresh_result['decision_id']!=review['decision_id']:
                raise ValueError('Reassessment decision_id mismatch')
            fresh_plan=next((p for p in fresh_result['layer3']['alternatives'] if p['id']==review['plan_id']),None)
            if fresh_plan is None or not fresh_plan['feasible'] or fresh_plan.get('funding')!='SETTLED':
                reassessment_attempts.append(make_attempt(review,fresh_result,source_snapshot(fresh),obs['at'],'REJECTED'))
                invalid=expired_entry_reasons(fresh['assets'][o['code']],fresh['decision_at'])
                if invalid:st.update(status='CANCELLED_EVIDENCE',reserved_cash='0')
                decisions.append(dict(at=obs['at'],order_id=o['id'],status='CANCELLED_EVIDENCE' if invalid else 'WAITING_REASSESSMENT',
                                      reason='NEW_DECISION_EVIDENCE_EXPIRED_OR_INVALIDATED' if invalid else 'NEW_DECISION_NOT_FEASIBLE_AND_SETTLED',
                                      reassessment_attempt_id=reassessment_attempts[-1]['attempt_id']))
                cancel_known_restrictions(obs['at'],'REJECTED_REASSESSMENT_KNOWN_RESTRICTION')
                continue
            if any(fresh['assets'][c][k]!=data['assets'][c][k] for c in data['assets'] for k in ('source_id','basis_id','adjustment_version')):
                raise ValueError('Reassessment cannot silently change price basis')
            if any(fresh['cost_model'][k]!=cfg[k] for k in ('fee_rate','minimum_fee','sell_tax','slippage_bps')):
                raise ValueError('Cost-model change requires a separately bound research execution')
            if quantity(fresh_plan['targets'][o['code']])-quantity(fresh['account']['holdings'][o['code']]['shares'])<quantity(st['remaining']):
                raise ValueError('Reassessment target changed; cancel/reissue an explicit smaller order')
            for key in review['cancelled_order_ids']:
                order_state[key].update(status='CANCELLED_REASSESSMENT',reserved_cash='0')
            st.update(status='WAITING',requires_reassessment=False,active_decision_at=fresh['decision_at'],active_decision_id=fresh_result['decision_id'])
            risk_data=fresh;latest_result=fresh_result;decision_ids.append(fresh_result['decision_id'])
            decision_records[fresh_result['decision_id']]=deepcopy(fresh_result)
            fact_sources[fresh_result['decision_id']]=source_snapshot(fresh)
            reassessment_attempts.append(make_attempt(review,fresh_result,source_snapshot(fresh),obs['at'],'ACCEPTED'))
            reassessments.append(dict(id=review['id'],at=obs['at'],order_id=o['id'],checkpoint_id=cp['checkpoint_id'],
                decision_id=fresh_result['decision_id'],cancelled_order_ids=review['cancelled_order_ids']))
        # Release expired orders and reserve all active buys jointly, in explicit order.
        reserved = Decimal(0)
        for o in orders:
            st = order_state[o['id']]
            if not number(st['remaining']): continue
            if st['status'] in ('CANCELLED_EVIDENCE','CANCELLED_REASSESSMENT','CANCELLED_AT_REVIEW'):continue
            if when >= timestamp(o['expires_at']):
                st.update(status='EXPIRED_UNFILLED', reserved_cash='0'); continue
            if when < timestamp(o['submitted_at']): continue
            if st['requires_reassessment']:
                st.update(status='WAITING_REASSESSMENT',reserved_cash='0')
                decisions.append(dict(at=obs['at'],order_id=o['id'],status='WAITING_REASSESSMENT',reason='NEW_ACCOUNT_EVIDENCE_CUTOFF_AND_DECISION_ID_REQUIRED'))
                continue
            if o['side'] == 'BUY':
                need = costs(quantity(st['remaining']), o['limit_price'], cfg, 'BUY')['cash']
                if need > cash - reserved:
                    st.update(status='WAITING_SETTLED_CASH', reserved_cash='0')
                else:
                    st.update(status='OPEN', reserved_cash=str(need)); reserved += need
            else:
                st.update(status='OPEN', reserved_cash='0')
        risk_observations.append(dict(at=obs['at'],kind='OBSERVED_ACCOUNT_AND_LIVE_ORDERS',
            **inspect_risk(risk_data,ledger_input,fills,day,marks,order_history,order_state)))
        for o in orders:
            st = order_state[o['id']]
            if o['code'] != obs['code'] or st['status'] not in ('OPEN', 'PARTIAL'):
                continue
            if timestamp(o['submitted_at']) > when:
                continue
            if day <= st['active_decision_at'][:10]:
                raise ValueError('Existing ledger requires decision on a prior day')
            blocked = obs['market_state'] == 'HALTED' or (o['side']=='BUY' and obs['market_state']=='LIMIT_UP_NO_BUY') or (o['side']=='SELL' and obs['market_state']=='LIMIT_DOWN_NO_SELL')
            n = min(quantity(st['remaining']), capacity)
            if o['side']=='SELL': n = min(n, sellable[o['code']], quantity(a['holdings'][o['code']]['sellable']))
            x = costs(n, obs['price'], cfg, o['side'])
            effective_price = number(obs['price']) * (1 + (1 if o['side']=='BUY' else -1)*number(cfg['slippage_bps'])/10000)
            limit_ok = effective_price <= number(o['limit_price']) if o['side']=='BUY' else effective_price >= number(o['limit_price'])
            if blocked or not n or not limit_ok:
                decisions.append(dict(at=obs['at'], order_id=o['id'], status='UNFILLED', reason='MARKET_BLOCK' if blocked else 'CAPACITY_OR_LIMIT', remaining=st['remaining']))
                continue
            if o['side']=='BUY':
                other = reserved - number(st['reserved_cash'])
                if x['cash'] > cash - other:
                    raise ValueError('Internal joint reservation conflict')
                risk=inspect_risk(risk_data,ledger_input,fills,day,marks,order_history,order_state)
                risk_observations.append(dict(at=obs['at'],order_id=o['id'],**risk))
                if risk['stale_exposure_marks'] or any(number(v)>0 for v in risk['joint_possible_fill_violations'].values()):
                    reserved-=number(st['reserved_cash']);st.update(status='RISK_BLOCKED',reserved_cash='0')
                    decisions.append(dict(at=obs['at'],order_id=o['id'],status='UNFILLED',reason='ACTUAL_RIGHTS_AND_POSSIBLE_FILLS_EXCEED_RISK_OR_MARKS_STALE',remaining=st['remaining']))
                    continue
            f = dict(id=o['id']+'-fill-'+str(len(fills)), code=o['code'], side=o['side'], shares=str(n),
                     price=str(effective_price), fee=str(x['fee']), tax=str(x['tax']), date=day,
                     decision_date=st['active_decision_at'][:10], settlement_date=obs['settlement_date'], source_ids=[obs['source_id']])
            fills.append(f)
            fill_order_ids[f['id']]=o['id']
            if o['side']=='BUY':
                cash -= x['cash']; reserved -= number(st['reserved_cash'])
            else:
                sellable[o['code']] -= n
            capacity -= n
            st.update(remaining=str(quantity(st['remaining'])-n), status='FILLED' if quantity(st['remaining'])==n else 'PARTIAL', reserved_cash='0')
            if o['side']=='BUY' and number(st['remaining']):
                need = costs(quantity(st['remaining']), o['limit_price'], cfg, 'BUY')['cash']
                st['reserved_cash']=str(need); reserved += need
            # Authoritative accounting rejects any oversell, unsupported rights or overspend.
            current = replay(dict(ledger_input, fills=deepcopy(fills)))
            decisions.append(dict(at=obs['at'], order_id=o['id'], status=st['status'], fill_id=f['id'],
                                  decision_id=st['active_decision_id'],reserved_cash_total=str(reserved), remaining=st['remaining']))
    final_time = timestamp(job['observed_until'])
    if times and final_time < times[-1]:
        raise ValueError('Execution watermark before tape')
    final_sources=declaration_sources(knowledge())
    final_history=history_at(final_sources,job['observed_until'])
    for o in orders:
        st=order_state[o['id']]
        if o['side']=='BUY' and number(st['remaining']) and not st['status'].startswith(('CANCELLED','EXPIRED')):
            invalid=asset_issues(final_history,o['code'],risk_data['assets'][o['code']],job['observed_until'],accepted_order=True)
            if invalid:
                effective=first_issue_at(final_sources,o['code'],risk_data['assets'][o['code']],
                                         after=st['active_decision_at'],through=job['observed_until'],accepted_order=True)
                if effective is not None and timestamp(effective)<timestamp(o['expires_at']):
                    st.update(status='CANCELLED_EVIDENCE',reserved_cash='0')
                    decisions.append(dict(at=effective,observed_at=job['observed_until'],order_id=o['id'],status='CANCELLED_EVIDENCE',
                                          reason='KNOWN_FACT_HISTORY_AT_WATERMARK',details=invalid))
        if number(st['remaining']) and final_time >= timestamp(o['expires_at']) and not st['status'].startswith('CANCELLED'):
            st.update(status='EXPIRED_UNFILLED', reserved_cash='0')
            decisions.append(dict(at=o['expires_at'],order_id=o['id'],status='EXPIRED_UNFILLED',reason='EXPLICIT_ORDER_DEADLINE',remaining=st['remaining']))
    final = replay(ledger_prefix(ledger_input,fills,job['observed_until'][:10]))
    # Return qualification is inherited as synthetic; never rename it to real performance.
    out = dict(schema=VERSION, status='SYNTHETIC_EXECUTION_REPLAY', decision_id=result['decision_id'],
               common_account_id=result['common_account_id'], ledger_version=final['schema'],
               origin_ledger_input_id=fingerprint(ledger_input),opening_checkpoint_id=continuation['checkpoint']['checkpoint_id'] if continuation else None,
               execution_model_version=data['execution_model']['version'], observed_until=job['observed_until'],
               orders=orders,order_history=order_history, order_states=order_state, execution_events=decisions, fills=fills, ledger=final,
               new_fill_ids=[f['id'] for f in fills[initial_fill_count:]],**lineage(),
               observation_only=observation_only,selected_plan_feasible=selected['feasible'],
               risk_observations=risk_observations,reassessments=reassessments,
               data_qualified=False, execution_model_qualified=False, historical_signal_eligible=False,
               policy_authorized=False, live_execution_authorized=False)
    out['result_id']=fingerprint(out)
    return out


def compare_jobs(jobs):
    """Reject unequal rights, costs, universe, marks or periods before any replay."""
    if not jobs:
        raise ValueError('Nonempty competing jobs required')
    identities=[]
    for j in jobs.values():
        li=deepcopy(j['ledger_input']); li.pop('fills')
        identities.append(fingerprint(dict(ledger=li, decision_input=j['decision_input'],tape=j['tape'],observed_until=j['observed_until'],
            ledger_close_proof=j.get('ledger_close_proof'),
            predecessor_state=j.get('continuation',{}).get('checkpoint',{}).get('state_id'))))
    if len(set(identities)) != 1:
        raise ValueError('Alternatives must share exact capital/rights AND exogenous prices/capacity/states/availability/settlement path')
    return dict(schema='capital-comparison/0.7', synthetic=True, common_input_id=identities[0],
                results={k:simulate(j) for k,j in jobs.items()}, ranking=None,
                total_net_return_comparison_qualified=False, policy_authorized=False)
