"""Independent corporate-action accrual/cash ledger, never a trading policy.

Daily events are applied to prior-close holdings before explicitly supplied fills.
Scheduled cash credits occur at day end; receivables cannot fund earlier buys.
"""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal, localcontext, ROUND_FLOOR
import re
from graph_core.core import number, fingerprint
from .core import fees

VERSION = 'rotation-action-ledger/0.1'
TYPES = ('CASH_DIVIDEND', 'STOCK_DIVIDEND', 'CAPITAL_REDUCTION')


def days(start, end):
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    if a >= b: raise ValueError('Explicit start-close to later end-close window required')
    return [(a + timedelta(days=i)).isoformat() for i in range((b-a).days+1)]


def qualify(data):
    """Declared evidence is not authenticated by a self-consistent fingerprint."""
    if data.get('schema') != 'rotation-action-input/0.1' or data.get('mode') != 'RAW':
        raise ValueError('New RAW event ledger contract required; Adjusted would double count')
    ds = days(data['start'], data['end']); reasons = []
    sources = data['sources']; assets = data['assets']; events = data['events']
    if len({e['id'] for e in events}) != len(events): raise ValueError('Duplicate event identity')
    if not assets: raise ValueError('Explicit assets required')
    for s in sources.values():
        if not re.fullmatch('[0-9a-f]{64}', s.get('sha256','')) or not s.get('url') or not s.get('captured_at'):
            raise ValueError('Every source needs original URL/hash/capture time')
    for e in events:
        if e['id'] != fingerprint({k:v for k,v in e.items() if k != 'id'}):
            raise ValueError('Event fingerprint mismatch')
        if e['code'] not in assets or e['basis_id'] != assets[e['code']]['basis_id']:
            raise ValueError('Event source/basis mismatch')
        if e['type'] not in TYPES:
            reasons.append('UNSUPPORTED_EVENT:'+e['id']); continue
        if not e.get('source_ids') or any(s not in sources for s in e['source_ids']):
            raise ValueError('Unbound event sources')
        if date.fromisoformat(e['ex_date']).isoformat()!=e['ex_date']:raise ValueError('Canonical event date required')
        if not data['start'] < e['ex_date'] <= data['end']: continue
        required = ('ex_date',) + {'CASH_DIVIDEND':('gross_per_share','net_per_share','pay_date'),
                    'STOCK_DIVIDEND':('shares_per_share','delivery_date','tradable_date'),
                    'CAPITAL_REDUCTION':('remaining_share_ratio','gross_cash_per_old_share','net_cash_per_old_share','pay_date','tradable_date')}[e['type']]
        for key in required:
            if e.get(key) is None: reasons.append('MISSING_EVENT_FIELD:'+e['id']+':'+key)
            elif not e.get('field_sources',{}).get(key): reasons.append('UNSOURCED_EVENT_FIELD:'+e['id']+':'+key)
            else:
                for proof in e['field_sources'][key]:
                    if proof.get('source_id') not in e['source_ids'] or not proof.get('locator'):
                        raise ValueError('Field proof must bind a retained event source and locator')
            if key.endswith('date') and e.get(key) is not None and date.fromisoformat(e[key]).isoformat()!=e[key]:raise ValueError('Canonical event date required')
        if e['type'] == 'CASH_DIVIDEND' and e.get('net_per_share') is not None and e.get('gross_per_share') is not None and not 0 <= number(e['net_per_share']) <= number(e['gross_per_share']):
            raise ValueError('Net dividend must be sourced within gross amount')
        if e['type'] == 'STOCK_DIVIDEND' and e.get('shares_per_share') is not None:
            if number(e['shares_per_share']) < 0: raise ValueError('Negative stock entitlement')
            if e.get('delivery_date') and e.get('tradable_date') and (e['delivery_date'] > e['tradable_date'] or e['delivery_date'] < e['ex_date']): raise ValueError('Invalid delivery/tradability dates')
        if e['type'] == 'CAPITAL_REDUCTION' and e.get('remaining_share_ratio') is not None:
            if not 0 < number(e['remaining_share_ratio']) < 1: raise ValueError('Reduction ratio must preserve a positive smaller share count')
            if e.get('tradable_date') and e['tradable_date'] < e['ex_date']: raise ValueError('Tradability before conversion')
            if e.get('net_cash_per_old_share') is not None and e.get('gross_cash_per_old_share') is not None and not 0 <= number(e['net_cash_per_old_share']) <= number(e['gross_cash_per_old_share']):
                raise ValueError('Invalid net capital return')
        if e.get('pay_date') is not None and e['pay_date'] < e['ex_date']: raise ValueError('Payment before entitlement')
    calendar = data['calendar']
    if [d['date'] for d in calendar] != ds: raise ValueError('Every calendar date required; never fill missing sessions')
    if any(type(d['trading']) is not bool for d in calendar): raise ValueError('Explicit market calendar flags required')
    if data['qualification'].get('calendar') != 'VERIFIED_COMPLETE': reasons.append('CALENDAR_NOT_VERIFIED_COMPLETE')
    if data['qualification'].get('opening_claims') != 'VERIFIED': reasons.append('OPENING_ENTITLEMENTS_UNKNOWN')
    for code, asset in assets.items():
        if not asset['source_id'] or not asset['basis_id']: raise ValueError('Original quote source/basis required')
        if not asset.get('quote_source_ids') or any(s not in sources for s in asset['quote_source_ids']):raise ValueError('Unbound quote archive evidence')
        coverage = data['coverage'].get(code, {})
        if (coverage.get('status') != 'VERIFIED_COMPLETE' or coverage.get('start','9999') > data['start'] or coverage.get('end','0000') < data['end'] or
            not set(TYPES).issubset(coverage.get('types',[])) or not coverage.get('other_actions_checked') or
            not coverage.get('source_ids') or any(s not in sources for s in coverage.get('source_ids',[]))):
            reasons.append('ACTION_COVERAGE_INCOMPLETE:'+code)
        relevant = {e['id'] for e in events if e['code']==code and data['start'] < e['ex_date'] <= data['end']}
        if coverage.get('status') == 'VERIFIED_COMPLETE' and set(coverage.get('event_ids',[])) != relevant:
            reasons.append('COVERAGE_EVENT_LIST_MISMATCH:'+code)
    if data['qualification'].get('net_distributions') != 'VERIFIED': reasons.append('NET_DISTRIBUTIONS_TAX_FEES_UNKNOWN')
    if data.get('buying_power','SETTLED_CASH_ONLY')!='SETTLED_CASH_ONLY':raise ValueError('Broker credit/netting not supported without a separate sourced contract')
    cfg=data['terminal_costs']
    if any(number(cfg[k])<0 for k in ('fee_rate','minimum_fee','sell_tax','slippage_bps')) or number(cfg['slippage_bps'])>=10000:
        raise ValueError('Invalid explicit terminal cost model')
    # A dated issuer schedule does not establish investor-specific tax or cash receipt.
    return sorted(set(reasons))


def replay(data):
    reasons = qualify(data)
    base = dict(schema=VERSION, input_id=fingerprint(data), start=data['start'], end=data['end'],
                policy_authorized=False, historical_signal_eligible=False, research_only=True,
                source_qualification=deepcopy(data['qualification']), refusal_reasons=reasons,
                daily=[], journal=[], total_net_return=None, scenario_net_return=None,
                actual_realized_investor_return=None,
                primary_pressure_id=None, flywheel_validation='NOT_VALIDATED')
    if reasons: return dict(base, status='REFUSED_INCOMPLETE_EVENT_ACCOUNTING')
    with localcontext() as ctx:
        ctx.prec = 50
        return _replay(data, base)


def _replay(data, result):
    ds=days(data['start'],data['end']); calendar={d['date']:d['trading'] for d in data['calendar']}
    q={c:number(data['opening']['shares'].get(c,'0')) for c in data['assets']};cash=number(data['opening']['cash'])
    if set(data['opening']['shares'])-set(q) or cash<0 or any(v<0 or v!=v.to_integral_value() for v in q.values()): raise ValueError('No unknown/negative/fractional opening holdings')
    claims=deepcopy(data['opening'].get('cash_claims',[]));pending=deepcopy(data['opening'].get('share_claims',[]))
    for x in claims:
        x['amount']=number(x['amount']);x.setdefault('kind','OPENING_RECEIVABLE')
        if x['amount']<0 or x['pay_date']<=data['start'] or not x.get('source_ids') or any(s not in data['sources'] for s in x['source_ids']):raise ValueError('Invalid/unsourced opening cash claim')
    for x in pending:
        x['shares']=number(x['shares'])
        if x['code'] not in q or x['shares']<0 or x['shares']!=x['shares'].to_integral_value() or x['tradable_date']<=data['start'] or not x.get('source_ids') or any(s not in data['sources'] for s in x['source_ids']):raise ValueError('Invalid/unsourced opening share claim')
    if len({x['id'] for x in claims+pending})!=len(claims+pending):raise ValueError('Duplicate opening claim')
    payable=[];journal=[];last_quotes={};fractional=False;quote_gaps=[]
    costs=Decimal(0);fills=data.get('fills',[])
    if len({f['id'] for f in fills})!=len(fills):raise ValueError('Duplicate fill')
    for f in fills:
        if (f['code'] not in q or f['side'] not in ('BUY','SELL') or f['date'] not in ds[1:] or not calendar[f['date']] or f['settlement_date']<f['date'] or
            not f.get('source_ids') or any(s not in data['sources'] for s in f['source_ids'])):raise ValueError('Invalid/unsourced explicit fill')
        if f.get('decision_date',f['date'])>=f['date']:raise ValueError('Research fill decision must precede execution day')
    def post(day, entry_type, **values):journal.append(dict(date=day,type=entry_type,**{k:str(v) if isinstance(v,Decimal) else v for k,v in values.items()}))
    def valuation(day):
        equity=cash+sum((c['amount'] for c in claims),Decimal(0))-sum((x['amount'] for x in payable),Decimal(0));prices={};unpriced=[]
        for code,asset in data['assets'].items():
            quote=asset['quotes'].get(day)
            if quote is not None:
                if number(quote)<=0:raise ValueError('Invalid RAW mark')
                last_quotes[code]=(day,number(quote))
            elif calendar[day] and (q[code] or any(x['code']==code for x in pending)):
                unpriced.append(code);continue
            if code not in last_quotes:
                if q[code] or any(x['code']==code for x in pending):unpriced.append(code)
                continue
            when,p=last_quotes[code];prices[code]=dict(value=str(p),source_date=when,carried_nontrading_mark=when!=day,
                                                    source_id=asset['source_id'],basis_id=asset['basis_id'],quote_source_ids=asset['quote_source_ids'])
            amount=q[code]+sum((x['shares'] for x in pending if x['code']==code),Decimal(0))
            equity+=amount*p
        return (None if unpriced else equity),prices,unpriced
    def daily(day,equity,prices):
        amount=lambda xs:sum((x['amount'] for x in xs),Decimal(0))
        return dict(date=day,settled_cash=str(cash),available_cash_strict=str(cash-amount(payable)),shares={c:str(v) for c,v in q.items()},
            cash_receivable=str(amount(claims)),purchase_payable=str(amount(payable)),
            cash_claims=[{**x,'amount':str(x['amount'])} for x in claims],
            share_receivables=[{**x,'shares':str(x['shares'])} for x in pending],
            net_accrual_equity=None if equity is None else str(equity),marks=prices)
    initial,prices,missing=valuation(ds[0])
    if initial is None or initial<=0:raise ValueError('Opening NAV cannot be established')
    result['daily'].append(daily(ds[0],initial,prices))
    for day in ds[1:]:
        # Entitlement is based on prior-close ownership, before ex-day open fills.
        prior_q=dict(q)
        prior_pending={x['code'] for x in pending if x['shares']}
        for e in [e for e in data['events'] if e['ex_date']==day]:
            code=e['code'];owned=prior_q[code]
            if code in prior_pending:
                raise ValueError('Overlapping uncredited rights require separately sourced entitlement treatment')
            if e['type']=='CASH_DIVIDEND':
                amount=owned*number(e['net_per_share']);claims.append(dict(id=e['id'],kind='DIVIDEND',amount=amount,pay_date=e['pay_date']))
                post(day,'DIVIDEND_RECEIVABLE',event_id=e['id'],code=code,entitled_shares=owned,gross=owned*number(e['gross_per_share']),net=amount)
            else:
                ratio=number(e['shares_per_share'] if e['type']=='STOCK_DIVIDEND' else e['remaining_share_ratio'])
                units=owned*ratio
                if e['type']=='CAPITAL_REDUCTION':
                    q[code]-=owned;last_quotes.pop(code,None)
                    amount=owned*number(e['net_cash_per_old_share']);claims.append(dict(id=e['id'],kind='CAPITAL_RETURN',amount=amount,pay_date=e['pay_date']))
                    post(day,'CAPITAL_REDUCTION',event_id=e['id'],code=code,old_shares=owned,new_shares=units,net_cash_receivable=amount)
                else:post(day,'STOCK_RECEIVABLE',event_id=e['id'],code=code,entitled_shares=owned,new_shares=units)
                whole=units.to_integral_value(rounding=ROUND_FLOOR);fraction=units-whole
                if units:
                    pending.append(dict(id=e['id'],code=code,shares=units,delivery_date=e.get('delivery_date'),tradable_date=e['tradable_date']))
                if fraction:
                    # No silent rounding or invented cash-in-lieu rate.
                    fractional=True;post(day,'UNRESOLVED_FRACTIONAL_SHARE',event_id=e['id'],code=code,shares=fraction)
        for x in pending[:]:
            if x.get('delivery_date')==day:
                post(day,'SHARES_DELIVERED_NOT_YET_ASSUMED_TRADABLE',event_id=x['id'],code=x['code'],shares=x['shares'])
            if x['tradable_date']==day:
                credited=x['shares'].to_integral_value(rounding=ROUND_FLOOR)
                q[x['code']]+=credited;pending.remove(x);post(day,'SHARES_TRADABLE',event_id=x['id'],code=x['code'],shares=credited)
                if x['shares']!=credited:
                    pending.append(dict(x,shares=x['shares']-credited,tradable_date=None,fractional_status='UNRESOLVED_NOT_CASH_OR_TRADABLE'))
        for f in [f for f in fills if f['date']==day]:
            n=number(f['shares']);price=number(f['price']);fee=number(f['fee']);tax=number(f['tax']);gross=n*price
            if n<=0 or n!=n.to_integral_value() or price<=0 or min(fee,tax)<0:raise ValueError('Invalid fill quantities/costs')
            code=f['code'];costs+=fee+tax
            if f['side']=='SELL':
                if n>q[code]:raise ValueError('Selling unavailable or uncredited shares')
                amount=gross-fee-tax
                if amount<0:raise ValueError('Negative sale proceeds')
                q[code]-=n;claims.append(dict(id=f['id'],kind='SALE',amount=amount,pay_date=f['settlement_date']))
            else:
                amount=gross+fee+tax;available=cash-sum((x['amount'] for x in payable),Decimal(0))
                if amount>available:raise ValueError('Insufficient explicitly available buying power; dividend receivable not cash')
                q[code]+=n;payable.append(dict(id=f['id'],amount=amount,pay_date=f['settlement_date']))
            post(day,'FILL',fill=deepcopy(f))
        # Credits are end-of-day; no invented intraday payment time.
        for x in claims[:]:
            if x['pay_date']==day:cash+=x['amount'];claims.remove(x);post(day,'CASH_RECEIVED',claim_id=x['id'],kind=x['kind'],amount=x['amount'])
        for x in payable[:]:
            if x['pay_date']==day:cash-=x['amount'];payable.remove(x);post(day,'PURCHASE_SETTLED',fill_id=x['id'],amount=x['amount'])
        if cash<0:raise ValueError('Negative settled cash')
        equity,prices,missing=valuation(day)
        if missing:quote_gaps.append(dict(date=day,codes=missing))
        result['daily'].append(daily(day,equity,prices))
    result['journal']=journal;result['quote_gaps']=quote_gaps;result['initial_equity']=str(initial)
    if fractional:result['refusal_reasons'].append('FRACTIONAL_SHARE_DISPOSITION_UNVERIFIED')
    if quote_gaps:result['refusal_reasons'].append('MISSING_HELD_ASSET_MARK_NO_SYNTHETIC_PRICE')
    if pending:result['refusal_reasons'].append('TERMINAL_SHARES_NOT_YET_TRADABLE')
    if result['refusal_reasons']:return dict(result,status='PARTIAL_LEDGER_RETURN_REFUSED')
    terminal=number(result['daily'][-1]['net_accrual_equity']);exit_cost=Decimal(0)
    for code,shares in q.items():
        if not shares:continue
        # At a non-trading endpoint this is a dated valuation mark, never a fabricated bar.
        value=shares*last_quotes[code][1];cfg=data['terminal_costs']
        effective=value*(1-number(cfg['slippage_bps'])/10000);fee,tax=fees(effective,cfg,True);exit_cost+=value-effective+fee+tax
    end=terminal-exit_cost;result.update(status='QUALIFIED_ACCOUNTING_SCENARIO_NOT_STRATEGY_VALIDATION',end_net_equity=str(end),
        terminal_estimated_exit_cost=str(exit_cost),fees_and_tax_on_fills=str(costs),scenario_net_return=str(end/initial-1))
    official=all(s.get('kind') in ('OFFICIAL_ARCHIVE','BROKER_RECORD') for s in data['sources'].values())
    modeled=official and data['qualification'].get('execution_costs') in ('VERIFIED_EXPLICIT_MODEL','VERIFIED_ACTUAL')
    if modeled:
        result['total_net_return']=result['scenario_net_return']
        result['return_qualification']='SOURCE_QUALIFIED_TOTAL_NET_RETURN_UNDER_DECLARED_COSTS_NOT_STRATEGY_VALIDATION'
    else:result['return_qualification']='ENGINEERED_OR_UNVERIFIED_SCENARIO_NOT_SOURCE_QUALIFIED_TOTAL_RETURN'
    # Hypothetical terminal liquidation and scheduled claims are not actual broker profit.
    if official and data['qualification'].get('execution_costs')=='VERIFIED_ACTUAL' and data['qualification'].get('investor_cashflows')=='VERIFIED_ACTUAL' and not any(q.values()) and not claims and not payable:
        result['actual_realized_investor_return']=result['scenario_net_return']
    return result


def compare(accounts):
    """Compare explicit fill paths only; never select or regenerate a strategy."""
    if not accounts:raise ValueError('Explicit nonempty competing accounts required')
    results={k:replay(v) for k,v in accounts.items()}
    starts={(r['start'],r['end'],number(r['initial_equity'])) for r in results.values() if r['scenario_net_return'] is not None}
    if len(starts)>1:raise ValueError('Unequal period or initial capital cannot be compared')
    eligible=all(r['total_net_return'] is not None for r in results.values())
    with localcontext() as ctx:
        ctx.prec=50
        differences={a:{b:str(number(x['end_net_equity'])-number(y['end_net_equity'])) for b,y in results.items()} for a,x in results.items()} if eligible else None
    return dict(schema='rotation-action-comparison/0.1',results=results,
                total_net_return_comparison_qualified=eligible,ranking=None,
                pairwise_end_net_equity_difference=differences,
                policy_authorized=False,historical_signal_eligible=False)
