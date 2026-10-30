"""Bind one fully checked synthetic cash action to the existing execution.

No order generation, quantity search, strategy, financial formulas or IO.
This is RUN: the complete original action receipt is revalidated before use.
"""
from copy import deepcopy
from decimal import Context, InvalidOperation, DivisionByZero, Overflow, ROUND_HALF_EVEN, localcontext

from .cash_action import evaluate as evaluate_action
from .cash_action import INPUT_V2 as ACTION_INPUT_V2, SCHEMA_V2 as ACTION_SCHEMA_V2
from .core import fingerprint, quantity, timestamp
from .execution import simulate
from .continuity import make_checkpoint
from .close_clock import close_record

INPUT='capital-cash-action-execution-input/0.1'
SCHEMA='capital-cash-action-execution/0.1'
INPUT_V2='capital-cash-action-execution-input/0.2'
SCHEMA_V2='capital-cash-action-execution/0.2'
FLAGS=('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized')
ORDER_FIELDS={'id','code','side','shares','limit_price','decision_at','submitted_at','expires_at'}


def execute(request):
    """Run only explicitly supplied orders/tape on the original synthetic book."""
    with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999,
            capitals=1,clamp=0,flags=[],traps=[InvalidOperation,DivisionByZero,Overflow])):
        return _execute(request)


def _job(action_input, checked, spec):
    if not isinstance(spec,dict) or set(spec)!={'id','origin_ledger','ledger_close_proof','orders','tape','observed_until'}:
        raise ValueError('EXACT_EXTERNAL_EXECUTION_SPEC_REQUIRED')
    if (not isinstance(spec['id'],str) or not spec['id'] or not isinstance(spec['orders'],list)
            or not isinstance(spec['tape'],list) or not isinstance(spec['observed_until'],str)):
        raise ValueError('EXPLICIT_ORDERS_TAPE_AND_WATERMARK_REQUIRED')
    ledger=spec['origin_ledger'];source=action_input['account_source']
    if not isinstance(ledger,dict) or not ledger.get('sources') or any(
            s.get('kind')!='ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET' for s in ledger['sources'].values()):
        raise ValueError('EXPLICIT_SYNTHETIC_LEDGER_REQUIRED')
    if not isinstance(ledger.get('calendar'),list) or not ledger['calendar']:
        raise ValueError('EXPLICIT_LEDGER_CALENDAR_REQUIRED')
    cp=source.get('checkpoint') if source['kind']=='CHECKPOINT' else None
    if cp is not None:
        if ledger!=cp['origin_ledger_input']:raise ValueError('ORIGINAL_LEDGER_BINDING_REQUIRED')
        if spec['ledger_close_proof']!=cp['execution_result']['ledger_close_proof']:
            raise ValueError('ORIGINAL_CLOSE_PROOF_REQUIRED')
    data=deepcopy(checked['source_integrity_metadata']['derived_decision_input'])
    if cp is None:
        a=data['account']
        opening=dict(cash=a['settled_cash'],shares={c:r['shares'] for c,r in a['holdings'].items()},
            cash_claims=a['cash_claims'],share_claims=a['share_claims'])
        if ledger['opening']!=opening:raise ValueError('EXACT_DECLARED_OPENING_REQUIRED')
    if timestamp(spec['observed_until'])<timestamp(data['decision_at']):
        raise ValueError('OBSERVATION_WATERMARK_BEFORE_CHECKED_DECISION')
    close_record(ledger,spec['ledger_close_proof'],spec['observed_until'])
    for obs in spec['tape']:
        if timestamp(obs['at'])>timestamp(spec['observed_until']) or timestamp(obs['at'])<timestamp(data['decision_at']):
            raise ValueError('OBSERVATION_OUTSIDE_EXPLICIT_WATERMARK')
    intent=checked['research']['intent'];action=intent['external_action']
    selling=checked['research']['schema']==ACTION_SCHEMA_V2
    if action['kind']=='HOLD' and spec['orders']:
        raise ValueError('HOLD_CANNOT_CREATE_ORDERS')
    count=0
    for order in spec['orders']:
        if not isinstance(order,dict) or set(order)!=ORDER_FIELDS:
            raise ValueError('EXACT_EXPLICIT_ORDER_REQUIRED')
        if order['side']!=('SELL' if selling else 'BUY') or order['code']!=action['code']:
            raise ValueError('ORDER_OUTSIDE_CHECKED_ACTION_SCOPE')
        n=int(quantity(order['shares']))
        if n<=0:raise ValueError('POSITIVE_EXPLICIT_ORDER_REQUIRED')
        count+=n
    if count>int(quantity(action['sell_shares'] if selling else action['additional_shares'])):
        raise ValueError('AGGREGATE_ORDER_EXCEEDS_CHECKED_ACTION')
    job=dict(schema='capital-execution-input/0.1',decision_input=data,plan_id=intent['evaluated_plan_id'],
        ledger_input=deepcopy(ledger),ledger_close_proof=deepcopy(spec['ledger_close_proof']),orders=deepcopy(spec['orders']),
        tape=deepcopy(spec['tape']),observed_until=spec['observed_until'])
    if cp is not None:
        prior=cp['execution_result'];latest=prior['latest_decision_id']
        job['continuation']=dict(previous_decision=dict(decision=deepcopy(prior['decision_records'][latest])),
            checkpoint=deepcopy(cp),cancelled_order_ids=[])
    return job


def _execute(request):
    selling=isinstance(request,dict) and request.get('schema')==INPUT_V2
    out=dict(schema=SCHEMA_V2 if selling else SCHEMA,synthetic=True,status='PENDING',reasons=[],execution_calls=0,binding=None,
        execution_job=None,execution=None,checkpoint=None,numeric_result=None,
        order_generation='NOT_PERFORMED',ranking=None,selected_strategy=None,strategy_validated=False,
        **{k:False for k in FLAGS},primary_pressure_id=None)
    integrity=dict(full_request_id=fingerprint(request))
    def wrap():return dict(run=out,source_integrity_metadata=integrity)
    stage='BIND_FULL_ACTION'
    try:
        if (not isinstance(request,dict) or set(request)!={'schema','synthetic','action_input','checked_action','expected_checked_action_id','execution_spec'}
                or request['schema'] not in (INPUT,INPUT_V2) or request['synthetic'] is not True):
            raise ValueError('EXPLICIT_SYNTHETIC_CASH_EXECUTION_REQUIRED')
        checked=request['checked_action'];original=request['action_input']
        checked_id=fingerprint(checked)
        if checked_id!=request['expected_checked_action_id']:
            raise ValueError('FULL_CHECKED_ACTION_ID_MISMATCH')
        if checked['source_integrity_metadata']['full_request_id']!=fingerprint(original):
            raise ValueError('ACTION_INPUT_ID_MISMATCH')
        if checked['research']['schema']!=(ACTION_SCHEMA_V2 if selling else 'capital-cash-action/0.1'):
            raise ValueError('SUPPORTED_FULL_CHECKED_ACTION_REQUIRED_NO_MIGRATION')
        if selling and original['schema']!=ACTION_INPUT_V2:
            raise ValueError('EXECUTION_ACTION_VERSION_MISMATCH')
        fresh=evaluate_action(original)
        if fresh!=checked:
            raise ValueError('BOUND_ACTION_RESULT_MISMATCH')
        gate=checked['research'];intent=gate['intent']
        if gate['status']!='CURRENTLY_FEASIBLE' or not intent or not intent['feasible_for_research']:
            out.update(status='STOPPED_ACTION_GATE',reasons=['CHECKED_ACTION_NOT_CURRENTLY_FEASIBLE'],
                action_gate_reasons=deepcopy(gate['reasons']))
            return wrap()
        if (gate['research_recommendation']['candidate_ids']!=[intent['evaluated_plan_id']]
                or any(gate[k] is not False for k in FLAGS) or gate['primary_pressure_id'] is not None):
            raise ValueError('CHECKED_ACTION_QUALIFICATION_OR_CANDIDATE_CONFLICT')
        out['binding']=dict(checked_action_id=checked_id,action_input_id=fingerprint(original),
            decision_id=gate['core_decision']['decision_id'],common_account_id=gate['core_decision']['common_account_id'],
            evaluated_plan_id=intent['evaluated_plan_id'],account=deepcopy(gate['account_binding']))
        stage='EXTERNAL_EXECUTION_SPEC'
        job=_job(original,checked,request['execution_spec']);out['execution_job']=deepcopy(job)
        integrity.update(origin_ledger_input_id=fingerprint(job['ledger_input']),external_execution_spec_id=fingerprint(request['execution_spec']))
        stage='EXISTING_SYNTHETIC_EXECUTION'
        out['execution_calls']+=1
        execution=simulate(job);out['execution']=execution
        if execution['status']!='SYNTHETIC_EXECUTION_REPLAY':
            out.update(status='STOPPED_EXECUTION_REFUSAL',reasons=deepcopy(execution['refusal_reasons']))
            return wrap()
        d=gate['core_decision']
        if (execution['decision_id']!=d['decision_id'] or execution['decision_records'][d['decision_id']]!=d
                or execution['common_account_id']!=d['common_account_id']):
            raise ValueError('EXECUTION_DECISION_DIFFERS_FROM_FULL_CHECKED_ACTION')
        stage='ORIGINAL_BOOK_CHECKPOINT'
        cp=make_checkpoint(job['ledger_input'],execution,through_at=job['observed_until']);out['checkpoint']=cp
        out['numeric_result']=dict(decision=deepcopy(d),fills=deepcopy(execution['fills']),new_fill_ids=deepcopy(execution['new_fill_ids']),
            events=deepcopy(execution['execution_events']),order_states=deepcopy(execution['order_states']),
            risk_observations=deepcopy(execution['risk_observations']),ledger=deepcopy(execution['ledger']),checkpoint_state=deepcopy(cp['state']))
        out['status']='REPLAYED_EXPLICIT_ACTION'
        return wrap()
    except (ValueError,KeyError,TypeError,IndexError,StopIteration) as exc:
        reason=str(exc)
        unsupported=any(word in reason for word in ('NOT_IMPLEMENTED','NOT_SUPPORTED'))
        out.update(status='NOT_IMPLEMENTED' if unsupported else 'INPUT_ERROR',reasons=[reason],failed_stage=stage,error_type=type(exc).__name__)
        return wrap()
