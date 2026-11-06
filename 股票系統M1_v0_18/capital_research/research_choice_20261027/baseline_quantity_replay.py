"""Gated, explicit-choice synthetic replay using existing quantity/ledger engines."""
from copy import deepcopy
from decimal import localcontext

from .core import fingerprint, quantity, timestamp
from .quantity_candidates import generate, INPUT_V2, REQUIRED
from .continuity import make_checkpoint, account_at_checkpoint
from .execution import simulate

INPUT='capital-quantity-replay-input/0.1'
SCHEMA='capital-quantity-replay/0.1'
MAX_ROUNDS=8
FRAME_FIELDS={'id','decision_template','quantity_template','selection','orders','tape','observed_until','cancelled_order_ids'}


def _quantity_request(frame,account,continuation):
    template=frame['decision_template']
    if 'account' in template or 'plans' in template:
        raise ValueError('TEMPLATE_ACCOUNT_OR_PLANS_FORBIDDEN')
    if {'orders','reassessments','continuation','ledger_input','plan_id','selected_candidate','tape'} & set(template):
        raise ValueError('TEMPLATE_EXECUTION_FIELDS_FORBIDDEN')
    data=deepcopy(template);data['account']=deepcopy(account);data['plans']=[]
    q=deepcopy(frame['quantity_template'])
    expected=(REQUIRED|{'batch_context'})-{'decision_input','continuation'}
    if set(q)!=expected or q['schema']!=INPUT_V2 or q['synthetic'] is not True:
        raise ValueError('EXPLICIT_V02_QUANTITY_TEMPLATE_REQUIRED')
    if not isinstance(q['batch_context'],dict) or {'account_id','origin'} & set(q['batch_context']):
        raise ValueError('BATCH_ACCOUNT_AND_ORIGIN_ARE_DERIVED_NOT_OVERRIDDEN')
    q['batch_context'].update(account_id=fingerprint(account),
        origin='CHECKPOINT_EPISODE' if continuation else 'DECLARED_SYNTHETIC_OPENING')
    q.update(decision_input=data,continuation=continuation)
    return q


def _select(candidates,selection):
    if set(selection)!={'mode','sell_A','additional_B','reason'} or not selection['reason']:
        raise ValueError('EXPLICIT_SELECTION_AND_REASON_REQUIRED_NO_DEFAULT')
    mode=selection['mode']
    if mode=='GRID':
        sold=int(quantity(selection['sell_A']));added=int(quantity(selection['additional_B']))
        matches=[c for c in candidates if c['plan'] is not None and int(c['sold_A'])==sold and int(c['additional_B'])==added]
    elif mode in ('HOLD','EXIT_A_KEEP_CASH','FULL_TRANSFER'):
        if selection['sell_A'] is not None or selection['additional_B'] is not None:
            raise ValueError('ENDPOINT_SELECTION_MUST_NOT_HIDE_QUANTITY_OVERRIDE')
        matches=[c for c in candidates if mode in c['kinds']]
    else:
        raise ValueError('SELECTION_MODE_NOT_SUPPORTED')
    if len(matches)!=1:
        raise ValueError('SELECTION_MUST_MATCH_ONE_CURRENT_CANDIDATE')
    return matches[0]


def _numeric_prefix(generation,selected,orders,execution,checkpoint):
    # Keep original raw records separately; never modify their signed identities.
    return dict(generation=deepcopy(generation['research']),selected_id=selected['id'],
        classification=selected['classification'],orders=deepcopy(orders),
        fills=deepcopy(execution['fills']),new_fill_ids=deepcopy(execution['new_fill_ids']),
        execution_events=deepcopy(execution['execution_events']),order_states=deepcopy(execution['order_states']),
        risk_observations=deepcopy(execution['risk_observations']),ledger=deepcopy(execution['ledger']),
        checkpoint_state=deepcopy(checkpoint['state']))


def replay_sequence(request):
    """No selection/ordering policy: callers explicitly supply each intent/order."""
    with localcontext() as ctx:
        ctx.prec=50
        return _replay_sequence(request)


def _replay_sequence(request):
    required={'schema','synthetic','initial_account','origin_ledger','ledger_close_proof','run_policy','rounds'}
    if set(request)!=required or request['schema']!=INPUT or request['synthetic'] is not True:
        raise ValueError('EXPLICIT_SYNTHETIC_QUANTITY_REPLAY_REQUIRED')
    frames=request['rounds'];policy=request['run_policy']
    if not isinstance(frames,list) or not frames:
        raise ValueError('EXPLICIT_NONEMPTY_ROUND_LIST_REQUIRED')
    if set(policy)!={'version','parameter_source','available_at','max_rounds'} or not policy['version'] or not policy['parameter_source']:
        raise ValueError('EXPLICIT_RUN_RESOURCE_PROVENANCE_REQUIRED')
    if timestamp(policy['available_at'])>timestamp(frames[0]['decision_template']['decision_at']):
        raise ValueError('RUN_POLICY_NOT_YET_AVAILABLE')
    limit=int(quantity(policy['max_rounds']))
    result=dict(schema=SCHEMA,synthetic=True,status='COMPLETED_PROVIDED_ROUNDS',run_policy=deepcopy(policy),
        implementation_round_limit=MAX_ROUNDS,rounds=[],execution_calls=0,stopped_at=None,reasons=[],
        last_execution=None,historical_checkpoint=None,execution_watermark=None,
        checkpoint_resume_api='NOT_IMPLEMENTED_REPLAY_COMPLETE_EXPLICIT_INPUT_ONLY',
        ranking=None,selected_strategy=None,strategy_validated=False,
        data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,
        policy_authorized=False,live_execution_authorized=False,primary_pressure_id=None)
    def wrap():
        return dict(replay=result,source_integrity_metadata=dict(full_input_id=fingerprint(request),
            original_ledger_input_id=fingerprint(request['origin_ledger']),close_proof_id=fingerprint(request['ledger_close_proof'])))
    if limit<1 or limit>MAX_ROUNDS or len(frames)>limit:
        result.update(status='REFUSED_ROUND_LIMIT',reasons=['EXPLICIT_ROUND_RESOURCE_LIMIT_EXCEEDED'])
        return wrap()
    current=None;checkpoint=None;seen=set()
    for index,frame in enumerate(frames):
        record=dict(index=index,id=frame.get('id'),status='PENDING',quantity_request=None,generation=None,selected_candidate=None,
                    execution_job=None,execution=None,checkpoint=None,numeric_prefix=None,
                    cancellations_requested=deepcopy(frame.get('cancelled_order_ids')),cancellations_applied=False,reasons=[])
        result['rounds'].append(record)
        stage='ROUND_INPUT'
        try:
            if set(frame)!=FRAME_FIELDS:
                raise ValueError('ROUND_FIELDS_NOT_SUPPORTED')
            if not isinstance(frame['id'],str) or not frame['id'] or frame['id'] in seen:
                raise ValueError('UNIQUE_EXPLICIT_ROUND_ID_REQUIRED')
            seen.add(frame['id'])
            if not isinstance(frame['orders'],list) or not isinstance(frame['tape'],list) or not isinstance(frame['cancelled_order_ids'],list):
                raise ValueError('EXPLICIT_ORDERS_TAPE_AND_CANCELLATION_LISTS_REQUIRED')
            template=frame['decision_template']
            if 'account' in template or 'plans' in template:
                raise ValueError('TEMPLATE_ACCOUNT_OR_PLANS_FORBIDDEN')
            if timestamp(frame['observed_until'])<timestamp(template['decision_at']):
                raise ValueError('OBSERVATION_WATERMARK_MUST_FOLLOW_REVIEW')
            continuation=None
            stage='AUTHORITATIVE_ACCOUNT'
            if current is None:
                if frame['cancelled_order_ids']:
                    raise ValueError('INITIAL_ACCOUNT_CANNOT_CANCEL_EXTERNAL_HISTORY')
                account=deepcopy(request['initial_account'])
                if account['as_of']!=template['data_cutoff']:
                    raise ValueError('INITIAL_ACCOUNT_CUTOFF_MISMATCH')
            else:
                if template['data_cutoff']!=checkpoint['state']['through_at']:
                    raise ValueError('REVIEW_CUTOFF_MUST_MATCH_PREVIOUS_WATERMARK')
                account=account_at_checkpoint(checkpoint,decision_at=template['decision_at'],
                    cancelled_order_ids=frame['cancelled_order_ids'])
                previous=dict(decision=deepcopy(current['decision_records'][current['latest_decision_id']]))
                continuation=dict(previous_decision=previous,checkpoint=deepcopy(checkpoint),
                    cancelled_order_ids=deepcopy(frame['cancelled_order_ids']))
            stage='QUANTITY_GATE'
            quantity_request=_quantity_request(frame,account,continuation)
            record['quantity_request']=deepcopy(quantity_request)
            generation=generate(quantity_request);record['generation']=generation
            if generation['research']['status']!='COMPLETE':
                status='STOPPED_NOT_IMPLEMENTED' if generation['research']['status']=='NOT_IMPLEMENTED' else 'STOPPED_CANDIDATE_GATE'
                record.update(status=status,reasons=deepcopy(generation['research']['reasons']))
                result.update(status=status,stopped_at=frame['id'],reasons=record['reasons']);break
            selected=_select(generation['research']['candidates'],frame['selection'])
            record['selected_candidate']=deepcopy(selected)
            if selected['classification'] not in ('CURRENTLY_FEASIBLE','WAIT_SETTLEMENT_REASSESSMENT') or not selected['feasible_for_research']:
                status='STOPPED_NOT_IMPLEMENTED' if selected['classification']=='NOT_IMPLEMENTED' else 'STOPPED_CANDIDATE_GATE'
                record.update(status=status,reasons=deepcopy(selected['reasons']))
                result.update(status=status,stopped_at=frame['id'],reasons=record['reasons']);break
            stage='EXPLICIT_EXECUTION'
            data=deepcopy(quantity_request['decision_input'])
            data['plans']=[] if selected['id']=='A-zero' else [deepcopy(selected['plan'])]
            job=dict(schema='capital-execution-input/0.1',decision_input=data,plan_id=selected['id'],
                ledger_input=deepcopy(request['origin_ledger']),ledger_close_proof=deepcopy(request['ledger_close_proof']),
                orders=deepcopy(frame['orders']),tape=deepcopy(frame['tape']),observed_until=frame['observed_until'])
            if continuation is not None:job['continuation']=continuation
            record['execution_job']=deepcopy(job);result['execution_calls']+=1
            execution=simulate(job);record['execution']=execution
            if execution['status']!='SYNTHETIC_EXECUTION_REPLAY':
                reasons=deepcopy(execution['refusal_reasons'])
                status='STOPPED_NOT_IMPLEMENTED' if any('NOT_IMPLEMENTED' in r or 'NOT_SUPPORTED' in r for r in reasons) else 'STOPPED_EXECUTION_REFUSAL'
                record.update(status=status,reasons=reasons);result.update(status=status,stopped_at=frame['id'],reasons=reasons);break
            if execution['decision_id']!=selected['core_decision_id']:
                raise ValueError('EXECUTION_DECISION_DIFFERS_FROM_GATED_QUANTITY_DECISION')
            record['cancellations_applied']=bool(frame['cancelled_order_ids'])
            current=execution;result['last_execution']=execution;result['execution_watermark']=execution['observed_until']
            stage='CHECKPOINT'
            checkpoint=make_checkpoint(request['origin_ledger'],execution,through_at=frame['observed_until'])
            record.update(status='REPLAYED_EXPLICIT_INTENT',checkpoint=checkpoint,
                cancellations_applied=bool(frame['cancelled_order_ids']),
                numeric_prefix=_numeric_prefix(generation,selected,frame['orders'],execution,checkpoint))
            result['historical_checkpoint']=checkpoint
        except (ValueError,TypeError,KeyError,StopIteration) as exc:
            reason=str(exc)
            capability_codes={'OPENING_PAYABLE_CONTINUATION_NOT_IMPLEMENTED','EXISTING_ORDER_CONTINUATION_NOT_IMPLEMENTED',
                              'ACTIVE_ORDER_GAP_CONTINUATION_NOT_IMPLEMENTED','SELLABLE_LIMIT_CONTINUATION_NOT_IMPLEMENTED'}
            status='STOPPED_NOT_IMPLEMENTED' if reason.split(':',1)[0] in capability_codes else 'STOPPED_INPUT_ERROR'
            record.update(status=status,reasons=[reason],error_type=type(exc).__name__,failed_stage=stage)
            result.update(status=status,stopped_at=frame.get('id'),reasons=[reason]);break
    return wrap()
