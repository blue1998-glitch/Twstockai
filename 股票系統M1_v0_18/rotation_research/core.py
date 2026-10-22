"""Pure causal decisions and cash/share replay; standard library only.

All policies are competing experiments, never approved investment rules.
No UI, database, network, or imports from historical numeric engines.
"""
from decimal import Decimal as D, ROUND_CEILING
import copy

VERSION = 'rotation-research/0.1'
PLANS = ('hold', 'full', 'staged25', 'staged50', 'cash', 'delay5')

def dec(v):
    x = D(str(v))
    if not x.is_finite():
        raise ValueError('Non-finite value')
    return x

def validate(data):
    if data['schema'] != 'rotation-input/0.1' or data['mode'] != 'RAW':
        raise ValueError('Unsupported schema/basis: never silently fall back')
    if len(data['assets']) != 2:
        raise ValueError('Explicit two assets required')
    dates = None
    for code, asset in data['assets'].items():
        if asset['volume_unit'] != 'SHARES_REPORTED' or not asset['source_id'] or not asset['basis_id']:
            raise ValueError('Missing source/basis/volume binding')
        bars = asset['bars']; ds = [b['date'] for b in bars]
        if ds != sorted(set(ds)) or not bars:
            raise ValueError('Unsorted/duplicate/empty dates')
        if dates is not None and dates != ds:
            raise ValueError('Unmatched calendars: no intersection fill')
        dates = ds
        for b in bars:
            if b.get('missing'):
                if not all(b[k] is None for k in ('open','high','low','close')):
                    raise ValueError('Missing quote must remain null')
                continue
            o,h,l,c = [dec(b[k]) for k in ('open','high','low','close')]
            if not (0 < l <= min(o,c) <= max(o,c) <= h) or int(b['volume']) <= 0:
                raise ValueError('Invalid/missing OHLCV')
    cfg=data['execution']
    for k in ('fee_rate','minimum_fee','sell_tax','slippage_bps','participation'):
        if dec(cfg[k]) < 0:
            raise ValueError('Negative execution parameter')
    if dec(cfg['participation']) > 1 or dec(cfg['slippage_bps']) >= 10000:
        raise ValueError('Invalid execution limits')
    if type(cfg['lot']) is not int or cfg['lot'] < 1 or cfg['settlement_lag'] not in (0,2):
        raise ValueError('Invalid lot/settlement assumption')
    if data['eligibility']['company_actions'] != 'VERIFIED_COMPLETE' and data.get('strict',True):
        raise ValueError('Company actions incomplete: strict total-return replay refused')
    if data.get('strict',True) and (data['eligibility']['calendar'] != 'VERIFIED_COMPLETE' or
                                   data['eligibility']['historical_availability'] != 'VERIFIED'):
        raise ValueError('Historical calendar/availability unverified')
    # This producer has no action-adjustment ledger yet; fail even if a caller claims completeness.
    if data.get('corporate_actions'):
        raise ValueError('Corporate-action ledger not supported in v0.1')
    return dates

def evidence(asset, cutoff, window=20):
    """Never reads a bar after cutoff. Rolling extrema are experimental proxies."""
    bs=[b for b in asset['bars'] if b['date'] <= cutoff]
    if not bs or bs[-1]['date'] != cutoff or len(bs) < window+1:
        raise ValueError('Exact cutoff/warmup missing')
    if any(b.get('missing') for b in bs[-max(window+1,6):]):
        raise ValueError('Missing quote in evidence window')
    cur, prev=bs[-1],bs[-2]; history=bs[-window-1:-1]
    key=max(dec(b['high']) for b in history)
    floor=min(dec(b['low']) for b in history)
    return {'as_of':cutoff,'source_id':asset['source_id'],'basis_id':asset['basis_id'],
            'price_fact': {'close':cur['close'],'experimental_prior_high':str(key),
                           'experimental_prior_low':str(floor),'close_above_proxy':dec(cur['close']) > key,
                           'close_below_proxy':dec(cur['close']) < floor,
                           'body':str(dec(cur['close'])-dec(cur['open'])),
                           'gap_from_previous_close':str(dec(cur['open'])-dec(prev['close'])),
                           'return_5_sessions':str(dec(cur['close'])/dec(bs[-6]['close'])-1)},
            'volume_fact': {'current':cur['volume'],'previous':prev['volume'],
                            'above_previous':int(cur['volume']) > int(prev['volume']),
                            'prior_window_max':max(int(b['volume']) for b in history)},
            'proxy_window':window,'proxy_status':'UNVALIDATED_NOT_FORMAL_KEY_LEVEL',
            'structure_state':'UNKNOWN_NO_APPROVED_REFERENCE_BINDING',
            'volume_economic_role':'UNKNOWN','scenario_confidence':None,
            'action_eligible':False,'remaining_upside':None,'waiting_value':'NOT_ESTABLISHED'}

def fees(notional, cfg, sell=False):
    if notional <= 0: return D(0), D(0)
    commission=max(dec(cfg['minimum_fee']),notional*dec(cfg['fee_rate'])).to_integral_value(rounding=ROUND_CEILING)
    tax=(notional*dec(cfg['sell_tax'])).to_integral_value(rounding=ROUND_CEILING) if sell else D(0)
    return commission,tax

def replay(data, incumbent, candidate, cutoff, horizon, plan):
    dates=validate(data)
    if incumbent == candidate or {incumbent,candidate} != set(data['assets']) or plan not in PLANS:
        raise ValueError('Explicit pair/plan required')
    if type(horizon) is not int or horizon < 1:
        raise ValueError('Positive session horizon required')
    start=dates.index(cutoff)
    if start+horizon >= len(dates):
        raise ValueError('Insufficient forward observations; no shortened horizon')
    a,b=[data['assets'][c] for c in (incumbent,candidate)]
    if any(bar.get('missing') for asset in (a,b) for bar in asset['bars'][start:start+horizon+1]):
        raise ValueError('Missing quote in replay window; no forward fill')
    snapshots={c:evidence(data['assets'][c],cutoff,data['proxy_window']) for c in (incumbent,candidate)}
    cfg=data['execution']; lot=cfg['lot']; initial_shares=data['initial_shares']
    if type(initial_shares) is not int or initial_shares <= 0 or initial_shares % lot:
        raise ValueError('Initial holdings must match explicit lot')
    cash=dec(data['initial_cash']); q={incumbent:initial_shares,candidate:0}
    if cash < 0: raise ValueError('Negative cash')
    initial=cash+initial_shares*dec(a['bars'][start]['close'])
    fixed_key=dec(snapshots[candidate]['price_fact']['experimental_prior_high'])
    a_proxy=dec(snapshots[incumbent]['price_fact']['experimental_prior_high'])
    trades=[]; decisions=[]; pending=[]; blocks=[]; weak_days=0; weak_capital_days=D(0)
    nav=[]; allocation=[]; spent=D(0); slip_total=D(0)
    target=D(0); step=D('.25') if plan=='staged25' else D('.5')
    if plan=='full': target=D(1)
    if plan.startswith('staged'): target=step
    cash_only=plan=='cash'
    for i in range(start+1,start+horizon+1):
        day=dates[i]; prior=dates[i-1]
        for unlock,amount in pending[:]:
            if unlock <= i: cash+=amount;pending.remove((unlock,amount))
        # Decision uses ONLY previous completed close; order uses this open.
        if plan=='delay5' and i==start+6: target=D(1)
        if plan.startswith('staged') and i > start+1 and target < 1:
            cb=b['bars'][i-1]; pb=b['bars'][i-2]
            if dec(cb['close']) > fixed_key and dec(cb['close']) > dec(pb['close']) and int(cb['volume']) > int(pb['volume']):
                target=min(D(1),target+step)
        desired_left=0 if cash_only else int(D(initial_shares)*(1-target))//lot*lot
        sell_qty=max(0,q[incumbent]-desired_left)
        # Capacity is based on yesterday's observed volume, never today's final volume.
        cap_a=int(dec(a['bars'][i-1]['volume'])*dec(cfg['participation']))//lot*lot
        sell_qty=min(sell_qty,cap_a)
        if q[incumbent] > desired_left and sell_qty == 0: blocks.append({'date':day,'side':'SELL','reason':'PRIOR_VOLUME_LIMIT'})
        decisions.append({'known_at_close':prior,'execute_not_before':day,'target_fraction_B':str(target),
                          'frozen_B_proxy':str(fixed_key),'policy':plan,'qualification':False})
        if sell_qty:
            raw=dec(a['bars'][i]['open']); price=raw*(1-dec(cfg['slippage_bps'])/10000)
            gross=sell_qty*price; fee,tax=fees(gross,cfg,True); amount=gross-fee-tax
            if amount < 0: raise ValueError('Sale costs exceed proceeds')
            q[incumbent]-=sell_qty;spent+=fee+tax;slip_total+=sell_qty*(raw-price)
            if cfg['settlement_lag']: pending.append((i+cfg['settlement_lag'],amount))
            else: cash+=amount
            trades.append({'date':day,'decision_cutoff':prior,'code':incumbent,'side':'SELL','shares':sell_qty,
                           'raw_open':str(raw),'effective_price':str(price),'fee':str(fee),'tax':str(tax),'cash_flow':str(amount)})
        if not cash_only and target > 0:
            raw=dec(b['bars'][i]['open']);price=raw*(1+dec(cfg['slippage_bps'])/10000)
            qty=int(cash/(price*(1+dec(cfg['fee_rate']))))//lot*lot
            cap_b=int(dec(b['bars'][i-1]['volume'])*dec(cfg['participation']))//lot*lot
            qty=min(qty,cap_b)
            while qty > 0 and qty*price+sum(fees(qty*price,cfg)) > cash: qty-=lot
            if qty > 0:
                gross=qty*price;fee,tax=fees(gross,cfg);amount=gross+fee
                cash-=amount;q[candidate]+=qty;spent+=fee;slip_total+=qty*(price-raw)
                trades.append({'date':day,'decision_cutoff':prior,'code':candidate,'side':'BUY','shares':qty,
                               'raw_open':str(raw),'effective_price':str(price),'fee':str(fee),'tax':'0','cash_flow':str(-amount)})
        receivable=sum((amount for _,amount in pending),D(0))
        gross_nav=cash+receivable;liq_nav=gross_nav; exit_cost=D(0);intraday_low=gross_nav
        values={}
        for code in q:
            bar=data['assets'][code]['bars'][i];value=q[code]*dec(bar['close']);values[code]=value
            gross_nav+=value;intraday_low+=q[code]*dec(bar['low'])
            effective=value*(1-dec(cfg['slippage_bps'])/10000);fee,tax=fees(effective,cfg,True)
            exit_cost+=value-effective+fee+tax
        liq_nav=gross_nav-exit_cost
        # Weak occupation is an explicitly named frozen-proxy diagnostic, not formal weakness.
        if dec(a['bars'][i]['close']) <= a_proxy and q[incumbent]:
            weak_days+=1;weak_capital_days+=values[incumbent]
        nav.append({'date':day,'mark_equity':str(gross_nav),'net_liquidation_equity':str(liq_nav),
                    'low_mark_bound':str(intraday_low),'estimated_exit_cost':str(exit_cost)})
        allocation.append({'date':day,'shares':copy.deepcopy(q),'cash':str(cash),'receivable':str(receivable)})
    peak=initial;dd=D(0)
    for point in nav:
        v=dec(point['net_liquidation_equity']);peak=max(peak,v);dd=min(dd,v/peak-1)
    end=dec(nav[-1]['net_liquidation_equity']);profit=end-initial
    capital_days=initial*horizon
    metrics={'initial_equity':str(initial),'end_mark_equity':nav[-1]['mark_equity'],
             'end_net_liquidation_equity':str(end),'net_price_return':str(profit/initial),
             'profit_per_session':str(profit/horizon),'return_per_session_linear':str(profit/capital_days),
             'max_drawdown_close_net':str(dd),
             'worst_low_mark_vs_start':str(min(dec(n['low_mark_bound']) for n in nav)/initial-1),
             'actual_model_fees_tax':str(spent),'actual_model_slippage':str(slip_total),
             'estimated_terminal_exit_cost':nav[-1]['estimated_exit_cost'],
             'total_modeled_friction':str(spent+slip_total+dec(nav[-1]['estimated_exit_cost'])),
             'unadvanced_A_sessions':weak_days,'unadvanced_A_capital_days':str(weak_capital_days),
             'unadvanced_A_time_weight':str(weak_capital_days/capital_days),'orders':len(trades)}
    return {'schema':'rotation-result/0.1','producer':VERSION,'research_only':True,
            'policy_authorized':False,'historical_signal_eligible':False,
            'status':'CONDITIONAL_PRICE_ONLY_NOT_TOTAL_RETURN','cutoff':cutoff,'incumbent':incumbent,
            'candidate':candidate,'horizon':horizon,'plan':plan,'input_evidence':snapshots,
            'execution':copy.deepcopy(cfg),'metrics':metrics,'decisions':decisions,'trades':trades,
            'nav':nav,'allocation':allocation,'blocks':blocks,'eligibility':copy.deepcopy(data['eligibility'])}

def compare(data, incumbent, candidate, cutoff, horizon):
    results={p:replay(data,incumbent,candidate,cutoff,horizon,p) for p in PLANS}
    hold=dec(results['hold']['metrics']['end_net_liquidation_equity'])
    full=dec(results['full']['metrics']['end_net_liquidation_equity'])
    for r in results.values():
        end=dec(r['metrics']['end_net_liquidation_equity'])
        r['metrics']['net_value_vs_hold']=str(end-hold)
        r['metrics']['net_value_vs_immediate_full']=str(end-full)
    return results
