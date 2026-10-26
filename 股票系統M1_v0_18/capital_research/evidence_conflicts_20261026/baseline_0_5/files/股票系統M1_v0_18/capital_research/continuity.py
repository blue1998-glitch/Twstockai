"""Account checkpoints reconstructed by the unchanged corporate-action ledger.

This module verifies lineage; it never posts cash, rights or shares itself.
"""
from copy import deepcopy
from graph_core.core import fingerprint
from rotation_research.action_ledger import replay
from .core import timestamp, number, quantity
from .close_clock import close_record
from .fact_lineage import history_at

CHECKPOINT = 'capital-account-checkpoint/0.4'


def ledger_prefix(origin, fills, day):
    if not origin['start'] < day <= origin['end']:
        raise ValueError('Checkpoint requires a later explicit daily close within origin window')
    x=deepcopy(origin);x['end']=day
    x['calendar']=[r for r in x['calendar'] if r['date']<=day]
    for asset in x['assets'].values():
        asset['quotes']={d:p for d,p in asset['quotes'].items() if d<=day}
    x['events']=[e for e in x['events'] if e['ex_date']<=day]
    x['fills']=[deepcopy(f) for f in fills if f['date']<=day]
    for c,coverage in x['coverage'].items():
        coverage['event_ids']=[e['id'] for e in x['events'] if e['code']==c and x['start']<e['ex_date']<=day]
    return x


def row_at(origin, fills, day):
    r=replay(ledger_prefix(origin,fills,day))
    if not r['daily'] or r['daily'][-1]['net_accrual_equity'] is None:
        raise ValueError('Authoritative ledger has no qualified mark at checkpoint')
    return r['daily'][-1],r


def _check_result(execution):
    if execution['schema']!='capital-execution/0.5' or execution['status']!='SYNTHETIC_EXECUTION_REPLAY':
        raise ValueError('LIFECYCLE_PROOF_REQUIRED: historical results remain readable, not implicitly upgraded')
    if execution['result_id']!=fingerprint({k:v for k,v in execution.items() if k!='result_id'}):
        raise ValueError('Execution fingerprint conflict')
    ids=execution['decision_ids'];records=execution['decision_records']
    if not ids or len(ids)!=len(set(ids)) or set(ids)!=set(records):
        raise ValueError('Exact ordered decision history required')
    sources=execution['fact_sources']
    if set(sources)!=set(ids):raise ValueError('Complete fact declaration history required')
    for index,key in enumerate(ids):
        d=records[key]
        if d['schema']!='capital-decision/0.5' or d['decision_id']!=key or fingerprint({k:v for k,v in d.items() if k!='decision_id'})!=key:
            raise ValueError('Decision history fingerprint conflict')
        if any(sources[key][k]!=d[k] for k in ('decision_at','data_cutoff')):
            raise ValueError('Fact declaration decision/cutoff conflict')
        expected=history_at([sources[k] for k in ids[:index+1]],d['decision_at'])
        if expected!=d['fact_history']:raise ValueError('Fact history differs from original declarations')
    times=[timestamp(records[key]['decision_at']) for key in ids]
    if times!=sorted(set(times)):raise ValueError('Decision history must be chronological')
    if execution['decision_id'] not in records or records[execution['decision_id']]['common_account_id']!=execution['common_account_id']:
        raise ValueError('Execution starting decision/account identity conflict')
    latest=records[ids[-1]]
    if execution['latest_decision_id']!=ids[-1] or execution['latest_common_account_id']!=latest['common_account_id']:
        raise ValueError('Latest predecessor identity conflict')
    tokens=set().union(*(set(d['reviewed_evidence_tokens']) for d in records.values()))
    if set(execution['reviewed_evidence_tokens'])!=tokens or not tokens<=set(latest['reviewed_evidence_tokens']):
        raise ValueError('Reviewed evidence history was dropped')
    orders={o['id']:o for o in execution['order_history']}
    if len(orders)!=len(execution['order_history']) or set(orders)!=set(execution['order_states']):
        raise ValueError('Order history/state identity conflict')
    fills={f['id']:f for f in execution['fills']};mapping=execution['fill_order_ids']
    if len(fills)!=len(execution['fills']) or set(fills)!=set(mapping):raise ValueError('Exact fill/order linkage required')
    for key,f in fills.items():
        o=orders.get(mapping[key])
        if o is None or any(o[k]!=f[k] for k in ('code','side')):raise ValueError('Fill belongs to another order')
    for key,o in orders.items():
        st=execution['order_states'][key]
        # Counts are exact integers; a caller's Decimal context must not round them.
        filled=sum(int(quantity(f['shares'])) for k,f in fills.items() if mapping[k]==key)
        if int(quantity(o['shares']))!=filled+int(quantity(st['remaining'])):raise ValueError('Filled/remaining quantity does not reconcile')
        if st['status'].startswith(('CANCELLED','EXPIRED')) and number(st['reserved_cash']):raise ValueError('Closed order retained a reservation')


def make_checkpoint(origin, execution, *, through_at):
    _check_result(execution)
    if through_at!=execution['observed_until']:
        raise ValueError('Checkpoint must bind the execution watermark; no retrospective order-state inference')
    if any(f['date']>through_at[:10] for f in execution['fills']):
        raise ValueError('Execution contains a future fill beyond its watermark')
    if execution.get('origin_ledger_input_id',fingerprint(origin))!=fingerprint(origin):
        raise ValueError('Origin ledger changed')
    close=close_record(origin,execution['ledger_close_proof'],through_at)
    unavailable=execution['opening_unavailable_shares']
    if set(unavailable)!=set(origin['assets']) or any(quantity(unavailable[c])>quantity(origin['opening']['shares'][c]) for c in unavailable):
        raise ValueError('Opening sellability proof conflict')
    row,r=row_at(origin,execution['fills'],through_at[:10])
    orders=execution.get('order_history',execution['orders'])
    active=[]
    for order in orders:
        state=execution['order_states'][order['id']]
        if number(state['remaining']) and state['status'] not in ('EXPIRED_UNFILLED','CANCELLED_EVIDENCE','CANCELLED_REASSESSMENT','CANCELLED_AT_REVIEW'):
            active.append(dict(order=deepcopy(order),state=deepcopy(state)))
    state=dict(through_at=through_at,ledger_version=r['schema'],row=deepcopy(row),
               accepted_fills=deepcopy(execution['fills']),unfilled_orders=active,
               order_states=deepcopy(execution['order_states']),
               origin_initial_capital=r['initial_equity'],external_flow='0',
               ledger_close=close,opening_unavailable_shares=deepcopy(unavailable),
               general_reserved_cash=execution['decision_records'][execution['latest_decision_id']]['reserved_cash'],
               latest_decision_id=execution['latest_decision_id'],latest_common_account_id=execution['latest_common_account_id'],
               reviewed_evidence_tokens=deepcopy(execution['reviewed_evidence_tokens']),
               fact_history=history_at([execution['fact_sources'][k] for k in execution['decision_ids']],through_at))
    # Full-source and execution fingerprints are integrity metadata, not prefix decisions.
    result=dict(schema=CHECKPOINT,state=state,state_id=fingerprint(state),
        origin_ledger_input=deepcopy(origin),execution_result=deepcopy(execution),
        integrity=dict(origin_ledger_input_id=fingerprint(origin),execution_result_id=execution['result_id'],
                       ledger_close_proof_id=fingerprint(execution['ledger_close_proof'])))
    result['checkpoint_id']=fingerprint(dict(schema=CHECKPOINT,state_id=result['state_id']))
    return result


def validate_checkpoint(checkpoint):
    if checkpoint['schema']!=CHECKPOINT:raise ValueError('Versioned lifecycle checkpoint required; no historical migration')
    rebuilt=make_checkpoint(checkpoint['origin_ledger_input'],checkpoint['execution_result'],
                            through_at=checkpoint['state']['through_at'])
    if rebuilt!=checkpoint:
        raise ValueError('Checkpoint differs from original ledger/fills/order states')
    return checkpoint


def account_at_checkpoint(checkpoint, *, decision_at, cancelled_order_ids=(), reserved_cash=None):
    validate_checkpoint(checkpoint)
    if timestamp(decision_at)<=timestamp(checkpoint['state']['through_at']):
        raise ValueError('New decision must follow the recorded daily close')
    if timestamp(decision_at)<timestamp(checkpoint['state']['ledger_close']['available_at']):
        raise ValueError('LEDGER_CLOSE_NOT_YET_AVAILABLE')
    if any(quantity(n) for n in checkpoint['state']['opening_unavailable_shares'].values()):
        raise ValueError('SELLABLE_LIMIT_CONTINUATION_NOT_IMPLEMENTED: no sourced release; cannot promote physical shares to sellable')
    authoritative_reserve=checkpoint['state']['general_reserved_cash']
    if reserved_cash is not None and reserved_cash!=authoritative_reserve:
        raise ValueError('General cash reserve cannot silently disappear or change')
    row=checkpoint['state']['row']
    if number(row['purchase_payable']):
        raise ValueError('OPENING_PAYABLE_CONTINUATION_NOT_IMPLEMENTED')
    active={o['order']['id'] for o in checkpoint['state']['unfilled_orders']}
    if set(cancelled_order_ids)!=active:
        raise ValueError('EXISTING_ORDER_CONTINUATION_NOT_IMPLEMENTED: explicitly cancel all unfilled orders at review')
    if len(set(cancelled_order_ids))!=len(cancelled_order_ids):
        raise ValueError('Duplicate cancellation identity')
    # This adapter has daily closes, not an uninterrupted intraday old-order
    # replay. A live order crossing another declared trading date may have filled
    # before review. Missing tape is not proof of no fills; fail closed using the
    # origin's explicit calendar, never an invented market-opening time or T+2.
    close_at=timestamp(checkpoint['state']['through_at'])
    review_day=timestamp(decision_at).astimezone(close_at.tzinfo).date().isoformat()
    if active and any(r['trading'] and close_at.date().isoformat()<r['date']<=review_day
                      for r in checkpoint['origin_ledger_input']['calendar']):
        raise ValueError('ACTIVE_ORDER_GAP_CONTINUATION_NOT_IMPLEMENTED: obtain a complete later ledger/order checkpoint before cancelling or reusing reservations')
    return dict(as_of=checkpoint['state']['through_at'],available_at=decision_at,
        holdings={c:dict(shares=n,sellable=n) for c,n in row['shares'].items()},
        settled_cash=row['settled_cash'],reserved_cash=authoritative_reserve,
        cash_claims=deepcopy(row['cash_claims']),share_claims=deepcopy(row['share_receivables']),
        payables=[],pending_orders=[])


def bind_resume(previous, data, checkpoint, cancelled_order_ids):
    validate_checkpoint(checkpoint)
    result=checkpoint['execution_result'];old=previous['decision']
    if (old['decision_id']!=result['latest_decision_id'] or result['latest_common_account_id']!=old['common_account_id']
            or old!=result['decision_records'][result['latest_decision_id']]):
        raise ValueError('LATEST_PREDECESSOR_REQUIRED: checkpoint must descend from the exact latest decision/account')
    expected=account_at_checkpoint(checkpoint,decision_at=data['decision_at'],cancelled_order_ids=cancelled_order_ids,
                                   reserved_cash=old.get('reserved_cash','0'))
    if data['account']!=expected or data['data_cutoff']!=checkpoint['state']['through_at']:
        raise ValueError('Next account/cutoff resets or drops authoritative cash, rights, holdings or orders')
    return dict(checkpoint_id=checkpoint['checkpoint_id'],state_id=checkpoint['state_id'],
                origin_initial_capital=checkpoint['state']['origin_initial_capital'],external_flow='0',
                latest_predecessor_id=old['decision_id'],
                cancelled_order_ids=sorted(cancelled_order_ids),
                cancellation_effective_at=data['decision_at'] if cancelled_order_ids else None,
                qualification='VERIFIED_SYNTHETIC_LEDGER_PREFIX_NOT_INVESTOR_AUTHORITY')


def describe_position_roles(row, roles):
    """Non-accounting labels must partition each physical holding exactly once."""
    if set(roles)!=set(row['shares']):raise ValueError('Every physical asset needs an explicit role partition')
    for c,parts in roles.items():
        if sum((quantity(n) for n in parts.values()),number('0'))!=quantity(row['shares'][c]):
            raise ValueError('Virtual purposes cannot duplicate or drop physical holdings')
    return dict(schema='capital-position-purpose/0.1',physical_shares=deepcopy(row['shares']),roles=deepcopy(roles),
                cash_claims_once=deepcopy(row['cash_claims']),share_claims_once=deepcopy(row['share_receivables']),
                separate_capital_or_entitlement_accounts=False)
