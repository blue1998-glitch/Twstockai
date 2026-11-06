"""Single-account, repeated rotation accounting experiment, not stitched returns.

Every tenth saved session review the two trailing five-session returns. Full
switch, move halfway toward winner, and cash-if-neither-positive compete.
These arbitrary experimental controls DO NOT implement the user's visual strategy.
"""
from decimal import Decimal as D
from .core import validate, dec, fees, evidence

def replay_loop(data, start, end, policy):
    dates=validate(data);lo=dates.index(start);hi=dates.index(end)
    if hi<=lo or policy not in ('hold','full_review10','half_review10','cash_review10'):
        raise ValueError('Invalid loop interval/policy')
    if data['execution']['settlement_lag'] != 0:
        raise ValueError('Loop v0.1 requires explicit same-day buying-power assumption')
    codes=list(data['assets']);a=codes[0];cfg=data['execution'];lot=cfg['lot']
    for c in codes:
        evidence(data['assets'][c],start,data['proxy_window'])
        if any(b.get('missing') for b in data['assets'][c]['bars'][lo:hi+1]):
            raise ValueError('Missing loop quote; no fill')
    q={c:0 for c in codes};q[a]=data['initial_shares'];cash=dec(data['initial_cash'])
    initial=cash+q[a]*dec(data['assets'][a]['bars'][lo]['close'])
    target={a:D(1),codes[1]:D(0)};ledger=[];decisions=[];curve=[];cost=D(0);slippage=D(0)
    for i in range(lo+1,hi+1):
        is_review=(i-lo-1)%10==0
        if is_review and policy!='hold':
            prior=i-1;returns={c:dec(data['assets'][c]['bars'][prior]['close'])/dec(data['assets'][c]['bars'][prior-5]['close'])-1 for c in codes}
            # Stable code order resolves equal experimental returns, no future tie break.
            winner=max(codes,key=lambda c:returns[c]);desired={c:D(int(c==winner)) for c in codes}
            if policy=='cash_review10' and max(returns.values())<=0:desired={c:D(0) for c in codes}
            if policy=='half_review10':target={c:(target[c]+desired[c])/2 for c in codes}
            else:target=desired
            decisions.append({'known_at_close':dates[prior],'first_execution':dates[i],
                              'trailing_returns':{c:str(r) for c,r in returns.items()},
                              'target_weights':{c:str(w) for c,w in target.items()},
                              'rule':'UNVALIDATED_RET5_REVIEW10','action_eligible':False})
        if policy!='hold' and is_review:
            prices={c:dec(data['assets'][c]['bars'][i]['open']) for c in codes}
            equity=cash+sum(q[c]*prices[c] for c in codes)
            desired={c:int(equity*target[c]/prices[c])//lot*lot for c in codes}
            # Sell before buy in one account. Capacity uses previous observed volume.
            for side in ('SELL','BUY'):
                for c in codes:
                    cap=int(dec(data['assets'][c]['bars'][i-1]['volume'])*dec(cfg['participation']))//lot*lot
                    n=min(max(0,q[c]-desired[c] if side=='SELL' else desired[c]-q[c]),cap)
                    price=prices[c]*(1+(1 if side=='BUY' else -1)*dec(cfg['slippage_bps'])/10000)
                    if side=='BUY':
                        n=min(n,int(cash/price)//lot*lot)
                        while n>0 and n*price+sum(fees(n*price,cfg))>cash:n-=lot
                    if n<=0:continue
                    fee,tax=fees(n*price,cfg,side=='SELL')
                    flow=n*price-fee-tax if side=='SELL' else -(n*price+fee)
                    q[c]+=n*(-1 if side=='SELL' else 1);cash+=flow;cost+=fee+tax;slippage+=n*abs(price-prices[c])
                    ledger.append({'date':dates[i],'decision_cutoff':dates[i-1],'side':side,'code':c,'shares':n,
                                   'raw_open':str(prices[c]),'effective_price':str(price),
                                   'fee':str(fee),'tax':str(tax),'cash_flow':str(flow)})
        mark=cash;exit_cost=D(0)
        for c in codes:
            value=q[c]*dec(data['assets'][c]['bars'][i]['close']);mark+=value
            effective=value*(1-dec(cfg['slippage_bps'])/10000);fee,tax=fees(effective,cfg,True)
            exit_cost+=value-effective+fee+tax
        curve.append({'date':dates[i],'cash':str(cash),'shares':dict(q),'mark_equity':str(mark),
                      'net_liquidation_equity':str(mark-exit_cost),'exit_cost':str(exit_cost)})
    peak=initial;dd=D(0)
    for p in curve:
        v=dec(p['net_liquidation_equity']);peak=max(peak,v);dd=min(dd,v/peak-1)
    return {'schema':'rotation-loop/0.1','policy':policy,'source_commit':data.get('source_commit','SYNTHETIC'),
            'status':'CONDITIONAL_PRICE_ONLY_NOT_VALIDATED_CAPITAL_FLYWHEEL',
            'initial_equity':str(initial),'external_flow':'0','cost_fee_tax':str(cost),
            'slippage':str(slippage),'net_price_return':str(dec(curve[-1]['net_liquidation_equity'])/initial-1),
            'max_drawdown':str(dd),'decisions':decisions,'ledger':ledger,'curve':curve,
            'policy_authorized':False,'eligibility':data['eligibility']}
