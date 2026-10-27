"""Order-bound review of a gated synthetic conditional quantity buy; no IO."""
from copy import deepcopy
from decimal import Context, InvalidOperation, DivisionByZero, Overflow, ROUND_HALF_EVEN, localcontext

from .core import fingerprint, quantity, nonnegative, timestamp, resume_decision
from .quantity_replay import replay_sequence
from .continuity import make_checkpoint, account_at_checkpoint
from .execution import simulate

INPUT='capital-conditional-quantity-review-input/0.1'
SCHEMA='capital-conditional-quantity-review/0.1'
INPUT_C='capital-conditional-quantity-review-input/0.2'
SCHEMA_C='capital-conditional-quantity-review/0.2'
IMPLEMENTATION_REVISION='0.2.1-deterministic-decimal-context'


def reassess_conditional(request):
    """One explicit review, same local order, unchanged limits and original book."""
    # Include account/checkpoint work after the protected original replay returns.
    with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999,
            capitals=1,clamp=0,flags=[],traps=[InvalidOperation,DivisionByZero,Overflow])):
        return _reassess_conditional(request)


def _reassess_conditional(request):
    c_review=request.get('schema')==INPUT_C
    out=dict(schema=SCHEMA_C if c_review else SCHEMA,synthetic=True,status='PENDING',reasons=[],
        prefix_execution=None,prefix_checkpoint=None,original_approval=None,
        review_request=None,review_decision=None,execution_job=None,execution=None,checkpoint=None,
        original_replay_status=None,numeric_result=None,ranking=None,
        data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,
        policy_authorized=False,live_execution_authorized=False,primary_pressure_id=None)
    def wrap():
        return dict(review=out,source_integrity_metadata=dict(full_input_id=fingerprint(request)))
    def stop(status,reason):
        out.update(status=status,reasons=[reason]);return wrap()
    stage='INPUT'
    try:
        if set(request)!={'schema','synthetic','replay_input','review'} or request['schema'] not in (INPUT,INPUT_C) or request['synthetic'] is not True:
            raise ValueError('EXPLICIT_SYNTHETIC_CONDITIONAL_REVIEW_REQUIRED')
        intent=request['review']
        if set(intent)!={'id','order_id','decision_template','policy'} or not isinstance(intent['id'],str) or not intent['id']:
            raise ValueError('EXACT_ORDER_BOUND_REVIEW_REQUIRED')
        template=intent['decision_template'];policy=intent['policy']
        if {'account','plans'} & set(template):
            raise ValueError('TEMPLATE_ACCOUNT_OR_PLANS_FORBIDDEN')
        if set(policy)!={'version','parameter_source','available_at','edge_budget'} or not policy['version'] or not policy['parameter_source']:
            raise ValueError('EXPLICIT_CURRENT_REVIEW_POLICY_REQUIRED')
        if timestamp(policy['available_at'])>timestamp(template['decision_at']):
            raise ValueError('REVIEW_POLICY_NOT_YET_AVAILABLE')
        nonnegative(policy['edge_budget'])
        original=request['replay_input'];frames=original['rounds'];last=frames[-1]
        if set(template)!=set(last['decision_template']):
            raise ValueError('REVIEW_TEMPLATE_FIELDS_MUST_MATCH_ORIGINAL_CONTRACT')
        cutoff=template['data_cutoff'];when=template['decision_at']
        if not (timestamp(last['decision_template']['decision_at'])<timestamp(cutoff)<timestamp(when)<=timestamp(last['observed_until'])):
            raise ValueError('EXPLICIT_REVIEW_WITHIN_LAST_ROUND_REQUIRED')
        stage='ORIGINAL_QUANTITY_GATE'
        prefix_input=deepcopy(original);prefix_input['rounds'][-1]['observed_until']=cutoff
        prefix_input['rounds'][-1]['tape']=[o for o in prefix_input['rounds'][-1]['tape'] if timestamp(o['at'])<=timestamp(cutoff)]
        prefix=replay_sequence(prefix_input)['replay'];out['original_replay_status']=prefix['status']
        if prefix['status']!='COMPLETED_PROVIDED_ROUNDS':
            out.update(status='STOPPED_ORIGINAL_GATE',reasons=deepcopy(prefix['reasons']))
            return wrap()
        record=prefix['rounds'][-1];execution=record['execution'];cp=record['checkpoint']
        out.update(prefix_execution=execution,prefix_checkpoint=dict(schema=cp['schema'],checkpoint_id=cp['checkpoint_id'],
            state_id=cp['state_id'],state=deepcopy(cp['state'])))
        stage='ORDER_SCOPE'
        order=next((o for o in execution['orders'] if o['id']==intent['order_id']),None)
        destination=last['quantity_template']['destination']
        if order is None or order['side']!='BUY' or order['code']!=destination:
            raise ValueError('OWN_LAST_ROUND_CONDITIONAL_ORDER_REQUIRED')
        st=execution['order_states'][order['id']]
        if st['status'].startswith(('CANCELLED','EXPIRED')) or not quantity(st['remaining']):
            raise ValueError('ORIGINAL_ORDER_CLOSED_NO_REACTIVATION')
        if not st['requires_reassessment']:
            return stop('STOPPED_NOT_IMPLEMENTED','ONLY_WAITING_CONDITIONAL_ORDER_REVIEW_SUPPORTED')
        active=[x['order']['id'] for x in cp['state']['unfilled_orders']]
        if active!=[order['id']]:
            return stop('STOPPED_NOT_IMPLEMENTED','SINGLE_OWN_CONDITIONAL_BUY_ONLY')
        approved=record['selected_candidate'];plan=approved['plan']
        if plan is None or plan['family'] not in (('C',) if c_review else ('B','E')) or plan['route']!='R1':
            return stop('STOPPED_NOT_IMPLEMENTED','ORIGINAL_FAMILY_CONTINUATION_NOT_IMPLEMENTED')
        remaining=quantity(st['remaining'])
        if not 0<remaining<=quantity(order['shares'])<=quantity(approved['additional_B']):
            raise ValueError('ORIGINAL_APPROVED_QUANTITY_SCOPE_CONFLICT')
        applicable=[o for o in last['tape'] if o['code']==destination and timestamp(when)<=timestamp(o['at'])<=timestamp(last['observed_until'])]
        if not applicable:
            raise ValueError('EXPLICIT_POST_REVIEW_OBSERVATION_REQUIRED')
        activation=min(applicable,key=lambda o:timestamp(o['at']))
        if timestamp(activation['at'])>=timestamp(order['expires_at']):
            raise ValueError('ORIGINAL_ORDER_EXPIRES_BEFORE_REVIEW_ACTIVATION')
        stage='AUTHORITATIVE_REVIEW'
        account=account_at_checkpoint(cp,decision_at=when,cancelled_order_ids=active)
        data=deepcopy(template);data['account']=account
        old=record['execution_job']['decision_input']
        if (set(data['assets'])!=set(old['assets']) or
            any(data['assets'][c][k]!=old['assets'][c][k] for c in old['assets'] for k in ('source_id','basis_id','adjustment_version')) or
            data['cost_model']!=old['cost_model']):
            raise ValueError('REVIEW_SOURCE_BASIS_OR_COST_CHANGED')
        bound_plan=deepcopy(plan)
        bound_plan['targets']={c:row['shares'] for c,row in account['holdings'].items()}
        bound_plan['targets'][destination]=str(quantity(account['holdings'][destination]['shares'])+remaining)
        bound_plan['edge_budget']=policy['edge_budget'];data['plans']=[bound_plan]
        previous=dict(decision=deepcopy(execution['decision_records'][execution['latest_decision_id']]))
        decision=resume_decision(previous,data,checkpoint=cp,cancelled_order_ids=active,
            same_order_id=order['id'] if c_review else None)['decision']
        review=dict(id=intent['id'],order_id=order['id'],decision_input=data,decision_id=decision['decision_id'],
            plan_id=bound_plan['id'],checkpoint_id=cp['checkpoint_id'],cancelled_order_ids=active)
        if c_review:review['same_order_review']=dict(schema='capital-same-order-review/0.1',order_id=order['id'])
        out.update(original_approval=dict(candidate_id=approved['id'],classification=approved['classification'],
            original_decision_id=approved['core_decision_id'],original_plan=deepcopy(plan),
            order=deepcopy(order),remaining=str(remaining),origin_ledger_input_id=execution['origin_ledger_input_id'],
            latest_predecessor_id=execution['latest_decision_id'],review_policy=deepcopy(policy)),
            review_request=review,review_decision=decision)
        stage='NATIVE_REVIEW_EXECUTION'
        job=deepcopy(record['execution_job']);job['observed_until']=last['observed_until'];job['reassessments']=[review]
        job['tape']=deepcopy(last['tape'])
        out['execution_job']=job
        actual=simulate(job);out['execution']=actual
        if actual['status']!='SYNTHETIC_EXECUTION_REPLAY':
            out.update(status='STOPPED_EXECUTION_REFUSAL',reasons=deepcopy(actual['refusal_reasons']));return wrap()
        attempt=next((a for a in actual['reassessment_attempts'] if a['id']==intent['id']),None)
        if attempt is None:
            raise ValueError('NATIVE_REVIEW_NOT_RECORDED_NO_AUTHORIZATION_CLAIM')
        final=make_checkpoint(original['origin_ledger'],actual,through_at=last['observed_until'])
        out['checkpoint']=dict(schema=final['schema'],checkpoint_id=final['checkpoint_id'],state_id=final['state_id'],state=final['state'])
        out['status']='REPLAYED_ACCEPTED_REVIEW' if attempt['outcome']=='ACCEPTED' else 'REPLAYED_REJECTED_REVIEW'
        evaluation=next(p for p in decision['layer3']['alternatives'] if p['id']==bound_plan['id'])
        out['reasons']=deepcopy(evaluation['reasons'])
        out['numeric_result']=dict(decision=decision,order=deepcopy(order),fills=actual['fills'],
            order_states=actual['order_states'],events=actual['execution_events'],ledger=actual['ledger'],checkpoint_state=final['state'])
        return wrap()
    except (ValueError,KeyError,TypeError,IndexError,StopIteration) as exc:
        unsupported={'OPENING_PAYABLE_CONTINUATION_NOT_IMPLEMENTED','SELLABLE_LIMIT_CONTINUATION_NOT_IMPLEMENTED',
            'EXISTING_ORDER_CONTINUATION_NOT_IMPLEMENTED','ACTIVE_ORDER_GAP_CONTINUATION_NOT_IMPLEMENTED'}
        status='STOPPED_NOT_IMPLEMENTED' if str(exc).split(':',1)[0] in unsupported else 'STOPPED_INPUT_ERROR'
        out.update(status=status,reasons=[str(exc)],failed_stage=stage,error_type=type(exc).__name__)
        return wrap()
