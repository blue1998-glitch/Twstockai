"""Read-only liquidation state, not an accounting or valuation engine."""
from decimal import Decimal
from ..lifecycle import TERMINAL

def cash_state(row):
    required=('shares','settled_cash','cash_receivable','purchase_payable','cash_claims','share_receivables','net_accrual_equity')
    if any(row.get(k) is None for k in required):return 'INSUFFICIENT_EVIDENCE'
    if not isinstance(row['shares'],dict) or not isinstance(row['cash_claims'],list) or not isinstance(row['share_receivables'],list):return 'INSUFFICIENT_EVIDENCE'
    try:
        amounts=[Decimal(row[k]) for k in ('settled_cash','cash_receivable','purchase_payable','net_accrual_equity')]
        shares=[Decimal(n) for n in row['shares'].values()]
        if not amounts or not shares or any(not x.is_finite() or x<0 for x in amounts+shares):return 'INSUFFICIENT_EVIDENCE'
        if any(n>0 for n in shares):return 'HOLDINGS_REMAIN'
        if amounts[1]!=0 or amounts[2]!=0 or row['cash_claims'] or row['share_receivables']:return 'AWAITING_SETTLEMENT_OR_RIGHTS'
        if amounts[0]!=amounts[3]:return 'ACCOUNT_VALUE_CONFLICT'
        return 'ALL_CASH_AT_SAVED_CLOSE'
    except (ValueError,TypeError,KeyError,ArithmeticError):return 'INSUFFICIENT_EVIDENCE'


def audit(execution):
    """Final label additionally requires all orders and all fills to be resolved.

Intermediate row statuses are holdings/rights facts, not a live order replay.
No intraday cash-availability claim is inferred from a daily close.
"""
    ledger=execution['ledger'];row=ledger['daily'][-1];reasons=[]
    status=cash_state(row)
    if status!='ALL_CASH_AT_SAVED_CLOSE':reasons.append(status)
    if any(st['status'] not in TERMINAL or st['reserved_cash']!='0' for st in execution['order_states'].values()):reasons.append('UNRESOLVED_ORDERS')
    for fill in execution['fills']:
        if fill['side']!='SELL':reasons.append('UNSUPPORTED_BUY_IN_FULL_EXIT_AUDIT');continue
        matches=[j for j in ledger['journal'] if j['type']=='CASH_RECEIVED' and j.get('kind')=='SALE' and j.get('claim_id')==fill['id']]
        if len(matches)!=1 or matches[0]['date']!=fill['settlement_date'] or fill['settlement_date']>row['date']:reasons.append('UNVERIFIED_SALE_SETTLEMENT:'+fill['id'])
    records=list(execution['decision_records'].values());reserve_unchanged=bool(records) and all(d['reserved_cash']==records[0]['reserved_cash'] for d in records)
    if not reserve_unchanged:reasons.append('GENERAL_RESERVE_CHANGED')
    q=ledger['source_qualification']
    if q['calendar']!='VERIFIED_COMPLETE' or q['opening_claims']!='VERIFIED' or q['net_distributions']!='VERIFIED':reasons.append('ACCOUNTING_SOURCE_GAP')
    return dict(status='VERIFIED_ALL_CASH_SYNTHETIC' if not reasons else 'NOT_FULLY_CASH',reasons=reasons,
        as_of=execution['observed_until'],settled_cash=row['settled_cash'],cash_receivable=row['cash_receivable'],
        purchase_payable=row['purchase_payable'],holdings=row['shares'],share_receivables=row['share_receivables'],
        general_reserve_unchanged=reserve_unchanged,scope='SAVED_CLOSE_NOT_REAL_BROKER_OR_FUTURE_GUARANTEE',
        daily_states=[dict(date=r['date'],status=cash_state(r)) for r in ledger['daily']])
