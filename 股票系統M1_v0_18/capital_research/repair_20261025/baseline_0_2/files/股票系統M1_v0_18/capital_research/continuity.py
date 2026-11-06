"""Account checkpoints reconstructed by the unchanged corporate-action ledger.

This module verifies lineage; it never posts cash, rights or shares itself.
"""
from copy import deepcopy
from graph_core.core import fingerprint
from rotation_research.action_ledger import replay
from .core import timestamp, number, quantity

CHECKPOINT = 'capital-account-checkpoint/0.1'


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
    if execution['schema'] not in ('capital-execution/0.1','capital-execution/0.2') or execution['status']!='SYNTHETIC_EXECUTION_REPLAY':
        raise ValueError('Successful explicit synthetic execution result required')
    if execution['result_id']!=fingerprint({k:v for k,v in execution.items() if k!='result_id'}):
        raise ValueError('Execution fingerprint conflict')


def make_checkpoint(origin, execution, *, through_at):
    _check_result(execution)
    if through_at!=execution['observed_until']:
        raise ValueError('Checkpoint must bind the execution watermark; no retrospective order-state inference')
    if any(f['date']>through_at[:10] for f in execution['fills']):
        raise ValueError('Execution contains a future fill beyond its watermark')
    if execution.get('origin_ledger_input_id',fingerprint(origin))!=fingerprint(origin):
        raise ValueError('Origin ledger changed')
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
               origin_initial_capital=r['initial_equity'],external_flow='0')
    # Full-source and execution fingerprints are integrity metadata, not prefix decisions.
    result=dict(schema=CHECKPOINT,state=state,state_id=fingerprint(state),
        origin_ledger_input=deepcopy(origin),execution_result=deepcopy(execution),
        integrity=dict(origin_ledger_input_id=fingerprint(origin),execution_result_id=execution['result_id']))
    result['checkpoint_id']=fingerprint(dict(schema=CHECKPOINT,state_id=result['state_id']))
    return result


def validate_checkpoint(checkpoint):
    rebuilt=make_checkpoint(checkpoint['origin_ledger_input'],checkpoint['execution_result'],
                            through_at=checkpoint['state']['through_at'])
    if rebuilt!=checkpoint:
        raise ValueError('Checkpoint differs from original ledger/fills/order states')
    return checkpoint


def account_at_checkpoint(checkpoint, *, decision_at, cancelled_order_ids=(), reserved_cash='0'):
    validate_checkpoint(checkpoint)
    if timestamp(decision_at)<=timestamp(checkpoint['state']['through_at']):
        raise ValueError('New decision must follow the recorded daily close')
    row=checkpoint['state']['row']
    if number(row['purchase_payable']):
        raise ValueError('OPENING_PAYABLE_CONTINUATION_NOT_IMPLEMENTED')
    active={o['order']['id'] for o in checkpoint['state']['unfilled_orders']}
    if set(cancelled_order_ids)!=active:
        raise ValueError('EXISTING_ORDER_CONTINUATION_NOT_IMPLEMENTED: explicitly cancel all unfilled orders at review')
    if len(set(cancelled_order_ids))!=len(cancelled_order_ids):
        raise ValueError('Duplicate cancellation identity')
    return dict(as_of=checkpoint['state']['through_at'],available_at=decision_at,
        holdings={c:dict(shares=n,sellable=n) for c,n in row['shares'].items()},
        settled_cash=row['settled_cash'],reserved_cash=reserved_cash,
        cash_claims=deepcopy(row['cash_claims']),share_claims=deepcopy(row['share_receivables']),
        payables=[],pending_orders=[])


def bind_resume(previous, data, checkpoint, cancelled_order_ids):
    validate_checkpoint(checkpoint)
    result=checkpoint['execution_result'];old=previous['decision']
    ids=result.get('decision_ids',[result['decision_id']])
    if old['decision_id'] not in ids or result['common_account_id']!=old['common_account_id']:
        raise ValueError('Checkpoint does not descend from the supplied decision/account')
    expected=account_at_checkpoint(checkpoint,decision_at=data['decision_at'],cancelled_order_ids=cancelled_order_ids,
                                   reserved_cash=old.get('reserved_cash','0'))
    if data['account']!=expected or data['data_cutoff']!=checkpoint['state']['through_at']:
        raise ValueError('Next account/cutoff resets or drops authoritative cash, rights, holdings or orders')
    return dict(checkpoint_id=checkpoint['checkpoint_id'],state_id=checkpoint['state_id'],
                origin_initial_capital=checkpoint['state']['origin_initial_capital'],external_flow='0',
                cancelled_order_ids=sorted(cancelled_order_ids),
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
