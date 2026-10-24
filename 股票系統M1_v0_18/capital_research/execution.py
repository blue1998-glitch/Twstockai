"""Synthetic order adapter. The existing action_ledger owns all accounting.

Reservations and order states live here; no second share/cash posting engine.
Every observation replays explicit accepted fills through the unchanged ledger.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
from graph_core.core import fingerprint
from rotation_research.action_ledger import replay, qualify
from .core import decide, costs, quantity, timestamp, nonnegative, validate_costs, number

VERSION = 'capital-execution/0.1'


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
    result = decide(data)['decision']
    selected = next((p for p in result['layer3']['alternatives'] if p['id'] == job['plan_id']), None)
    if selected is not None and selected['status']=='NOT_IMPLEMENTED':
        return _refusal('SELECTED_PLAN_NOT_IMPLEMENTED')
    if selected is None or not selected['feasible']:
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
    if ledger_input['start'] != data['data_cutoff'][:10] or a['as_of'] != data['data_cutoff']:
        raise ValueError('Opening ledger/cutoff mismatch')
    expected = dict(cash=a['settled_cash'], shares={c:x['shares'] for c,x in a['holdings'].items()},
                    cash_claims=a['cash_claims'], share_claims=a['share_claims'])
    if ledger_input['opening'] != expected or set(ledger_input['assets']) != set(data['assets']):
        raise ValueError('Unequal opening holdings/cash/rights')
    if any(s['kind'] != 'ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET' for s in ledger_input['sources'].values()):
        raise ValueError('Synthetic adapter cannot publish a real-data replay')
    for c, asset in ledger_input['assets'].items():
        if asset['source_id'] != data['assets'][c]['source_id'] or asset['basis_id'] != data['assets'][c]['basis_id']:
            raise ValueError('Ledger source/basis mismatch')
    reasons = qualify(ledger_input)
    if reasons:
        return _refusal('EXISTING_ACTION_LEDGER_REFUSED:' + '|'.join(reasons))
    cfg = data['cost_model']; validate_costs(cfg)
    for k in ('fee_rate', 'minimum_fee', 'sell_tax', 'slippage_bps'):
        if ledger_input['terminal_costs'][k] != cfg[k]:
            raise ValueError('Decision/execution/terminal cost model mismatch')
    state = replay(ledger_input)
    if not state['daily'] or state['daily'][0]['net_accrual_equity'] is None:
        return _refusal('OPENING_LEDGER_UNAVAILABLE')
    if number(state['daily'][0]['net_accrual_equity']) != number(result['initial_capital']):
        raise ValueError('Opening valuation/capital mismatch')
    for c in data['assets']:
        mark = [m for m in data['assets'][c]['marks'] if m['occurred_at'] == data['data_cutoff'] and timestamp(m['available_at']) <= timestamp(data['decision_at'])]
        if len(mark) != 1 or number(ledger_input['assets'][c]['quotes'][ledger_input['start']]) != number(mark[0]['price']):
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
    order_state = {o['id']:dict(remaining=o['shares'], status='WAITING', reserved_cash='0') for o in orders}
    decisions = []
    fills = []
    calendar = {d['date']:d['trading'] for d in ledger_input['calendar']}
    tape = job['tape']
    times = [timestamp(x['at']) for x in tape]
    if times != sorted(set(times)):
        raise ValueError('Execution observations must be unique, chronological and explicit')
    for obs in tape:
        when = timestamp(obs['at']); day = obs['at'][:10]
        if day <= ledger_input['start'] or day > ledger_input['end'] or not calendar[day] or timestamp(obs['available_at']) > when:
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
        # The tape supplies an explicit research settlement date, not inferred T+2.
        if obs['settlement_date'] not in calendar or obs['settlement_date'] < day:
            raise ValueError('Explicit in-window settlement date required')
        # Current intraday balance = prior day end, with today's accepted fills.
        current = replay(dict(ledger_input, fills=deepcopy(fills)))
        prior = [x for x in current['daily'] if x['date'] < day][-1]
        cash = number(prior['available_cash_strict']) - nonnegative(a['reserved_cash'])
        sellable = {c:number(prior['shares'][c]) for c in data['assets']}
        for f in [f for f in fills if f['date']==day]:
            if f['side']=='BUY': cash -= number(f['shares'])*number(f['price'])+number(f['fee'])+number(f['tax'])
            else: sellable[f['code']] -= number(f['shares'])
        # Release expired orders and reserve all active buys jointly, in explicit order.
        reserved = Decimal(0)
        for o in orders:
            st = order_state[o['id']]
            if not number(st['remaining']): continue
            if when >= timestamp(o['expires_at']):
                st.update(status='EXPIRED_UNFILLED', reserved_cash='0'); continue
            if when < timestamp(o['submitted_at']): continue
            if o['side'] == 'BUY':
                need = costs(quantity(st['remaining']), o['limit_price'], cfg, 'BUY')['cash']
                if need > cash - reserved:
                    st.update(status='WAITING_SETTLED_CASH', reserved_cash='0')
                else:
                    st.update(status='OPEN', reserved_cash=str(need)); reserved += need
            else:
                st.update(status='OPEN', reserved_cash='0')
        for o in orders:
            st = order_state[o['id']]
            if o['code'] != obs['code'] or st['status'] not in ('OPEN', 'PARTIAL'):
                continue
            if timestamp(o['submitted_at']) > when:
                continue
            if day <= o['decision_at'][:10]:
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
            f = dict(id=o['id']+'-fill-'+str(len(fills)), code=o['code'], side=o['side'], shares=str(n),
                     price=str(effective_price), fee=str(x['fee']), tax=str(x['tax']), date=day,
                     decision_date=o['decision_at'][:10], settlement_date=obs['settlement_date'], source_ids=[obs['source_id']])
            fills.append(f)
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
                                  reserved_cash_total=str(reserved), remaining=st['remaining']))
    final_time = timestamp(job['observed_until'])
    if times and final_time < times[-1]:
        raise ValueError('Execution watermark before tape')
    for o in orders:
        st=order_state[o['id']]
        if number(st['remaining']) and final_time >= timestamp(o['expires_at']):
            st.update(status='EXPIRED_UNFILLED', reserved_cash='0')
    final = replay(dict(ledger_input, fills=deepcopy(fills)))
    # Return qualification is inherited as synthetic; never rename it to real performance.
    out = dict(schema=VERSION, status='SYNTHETIC_EXECUTION_REPLAY', decision_id=result['decision_id'],
               common_account_id=result['common_account_id'], ledger_version=final['schema'],
               execution_model_version=data['execution_model']['version'], observed_until=job['observed_until'],
               orders=orders, order_states=order_state, execution_events=decisions, fills=fills, ledger=final,
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
        identities.append(fingerprint(dict(ledger=li, decision_input=j['decision_input'])))
    if len(set(identities)) != 1:
        raise ValueError('Alternatives must share exact opening capital AND rights, source/model/scenarios')
    return dict(schema='capital-comparison/0.1', synthetic=True, common_input_id=identities[0],
                results={k:simulate(j) for k,j in jobs.items()}, ranking=None,
                total_net_return_comparison_qualified=False, policy_authorized=False)
