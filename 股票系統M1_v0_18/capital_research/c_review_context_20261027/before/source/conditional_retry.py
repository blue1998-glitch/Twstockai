"""One bounded retry of a saved rejected C review, using the original book."""
from copy import deepcopy
from decimal import localcontext

from .conditional_quantity_review import reassess_conditional, INPUT_C, SCHEMA_C
from .core import fingerprint, quantity, timestamp, nonnegative, resume_decision
from .continuity import make_checkpoint, account_at_checkpoint
from .execution import simulate
from .eligibility import expired_entry_reasons
from .fact_lineage import history_at, source_snapshot, asset_issues
from .reassessment_history import declaration_sources

INPUT = 'capital-conditional-retry-input/0.1'
SCHEMA = 'capital-conditional-quantity-review/0.3'


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _compact(cp):
    return {k: deepcopy(cp[k]) for k in ('schema', 'checkpoint_id', 'state_id', 'state')}


def predecessor(saved):
    """Declared binding only; retry_rejected still verifies the original RUN."""
    r = saved['review']
    e = r['execution']
    return dict(document_id=fingerprint(saved), execution_result_id=e['result_id'],
        checkpoint_id=r['checkpoint']['checkpoint_id'], latest_decision_id=e['latest_decision_id'],
        latest_common_account_id=e['latest_common_account_id'],
        reviewed_evidence_tokens=deepcopy(e['reviewed_evidence_tokens']))


def retry_rejected(request):
    with localcontext() as ctx:
        ctx.prec = 50
        return _retry(request)


def _retry(request):
    out = dict(schema=SCHEMA, synthetic=True, status='PENDING', reasons=[],
        prefix_execution=None, prefix_checkpoint=None, original_approval=None,
        review_request=None, review_decision=None, execution_job=None, execution=None,
        checkpoint=None, numeric_result=None, retry_binding=None, previous_result_id=None,
        ranking=None, data_qualified=False, execution_model_qualified=False,
        historical_signal_eligible=False, policy_authorized=False, live_execution_authorized=False,
        primary_pressure_id=None)
    stage = 'INPUT'

    def wrap():
        return dict(review=out, source_integrity_metadata=dict(full_input_id=fingerprint(request)))

    try:
        _require(set(request) == {'schema', 'synthetic', 'original_input', 'previous_result',
            'predecessor', 'review', 'observation'} and request['schema'] == INPUT and
            request['synthetic'] is True, 'EXPLICIT_SYNTHETIC_RETRY_REQUIRED')
        saved = request['previous_result']
        prior = saved['review']
        _require(prior['schema'] == SCHEMA_C and prior['status'] == 'REPLAYED_REJECTED_REVIEW'
            and request['original_input']['schema'] == INPUT_C, 'REJECTED_C_REVIEW_0_2_REQUIRED')
        intent = request['review']
        _require(set(intent) == {'id', 'order_id', 'decision_template', 'policy'} and
            isinstance(intent['id'], str) and intent['id'], 'EXACT_RETRY_REVIEW_REQUIRED')
        _require(intent['order_id'] == prior['review_request']['order_id'], 'SAME_REJECTED_ORDER_REQUIRED')
        old = prior['execution']
        state = old['order_states'][intent['order_id']]
        _require(not state['status'].startswith(('CANCELLED', 'EXPIRED')) and
            quantity(state['remaining']) > 0, 'ORIGINAL_ORDER_CLOSED_NO_REACTIVATION')
        _require(state['requires_reassessment'] is True, 'WAITING_REJECTED_ORDER_REQUIRED')
        _require(request['predecessor'] == predecessor(saved), 'EXACT_RETRY_PREDECESSOR_REQUIRED')
        stage = 'ORIGINAL_QUANTITY_AND_REVIEW_GATE'
        rebuilt = reassess_conditional(request['original_input'])
        _require(rebuilt == saved, 'SAVED_REJECTED_REVIEW_DIFFERS_FROM_ORIGINAL_GATE')
        job = deepcopy(prior['execution_job'])
        origin = job['ledger_input']
        cp = make_checkpoint(origin, old, through_at=old['observed_until'])
        _require(_compact(cp) == prior['checkpoint'], 'SAVED_RETRY_CHECKPOINT_CONFLICT')
        out.update(prefix_execution=deepcopy(old), prefix_checkpoint=_compact(cp),
            original_approval=deepcopy(prior['original_approval']),
            retry_binding=deepcopy(request['predecessor']), previous_result_id=fingerprint(saved))
        stage = 'RETRY_SCOPE'
        _require(intent['id'] not in {a['id'] for a in old['reassessment_attempts']},
            'RETRY_NEW_REVIEW_ID_REQUIRED')
        template = intent['decision_template']
        _require(set(template) == set(request['original_input']['review']['decision_template']) and
            not {'account', 'plans'} & set(template), 'EXACT_RETRY_TEMPLATE_REQUIRED')
        cutoff, when = template['data_cutoff'], template['decision_at']
        _require(cutoff == old['observed_until'], 'RETRY_MUST_USE_SAVED_WATERMARK')
        _require(all(timestamp(a['observed_at']) < timestamp(when) for a in old['reassessment_attempts']),
            'RETRY_MUST_FOLLOW_RECEIVED_ATTEMPTS')
        policy = intent['policy']
        _require(set(policy) == {'version', 'parameter_source', 'available_at', 'edge_budget'} and
            policy['version'] and policy['parameter_source'] and timestamp(policy['available_at']) <= timestamp(when),
            'EXPLICIT_CURRENT_RETRY_POLICY_REQUIRED')
        nonnegative(policy['edge_budget'])
        initial = job['decision_input']
        _require(set(template['assets']) == set(initial['assets']) and
            all(template['assets'][c][k] == initial['assets'][c][k] for c in initial['assets']
                for k in ('source_id', 'basis_id', 'adjustment_version')) and
            template['cost_model'] == initial['cost_model'], 'RETRY_SOURCE_BASIS_OR_COST_CHANGED')
        observation = request['observation']
        _require(set(observation) == {'observed_until', 'tape_extension'}, 'EXACT_RETRY_OBSERVATION_REQUIRED')
        end, tail = observation['observed_until'], observation['tape_extension']
        _require(timestamp(cutoff) < timestamp(when) < timestamp(end) and end[:10] <= origin['end'],
            'RETRY_OBSERVATION_OUTSIDE_ORIGINAL_WINDOW')
        times = [timestamp(row['at']) for row in tail]
        _require(times and times == sorted(set(times)) and
            all(timestamp(cutoff) < t <= timestamp(end) for t in times), 'RETRY_TAPE_MUST_EXTEND_SAVED_PREFIX')
        order = next(o for o in old['order_history'] if o['id'] == intent['order_id'])
        applicable = [row for row in tail if row['code'] == order['code'] and timestamp(row['at']) >= timestamp(when)]
        _require(applicable, 'EXPLICIT_POST_RETRY_OBSERVATION_REQUIRED')
        activation = applicable[0]['at']
        _require(timestamp(activation) < timestamp(order['expires_at']), 'ORIGINAL_ORDER_EXPIRES_BEFORE_RETRY')
        account = account_at_checkpoint(cp, decision_at=when, cancelled_order_ids=[order['id']])
        data = deepcopy(template)
        data['account'] = account
        plan = deepcopy(prior['original_approval']['original_plan'])
        plan['targets'] = {c: h['shares'] for c, h in account['holdings'].items()}
        plan['targets'][order['code']] = str(quantity(account['holdings'][order['code']]['shares']) + quantity(state['remaining']))
        plan['edge_budget'] = policy['edge_budget']
        data['plans'] = [plan]
        previous = dict(decision=deepcopy(old['decision_records'][old['latest_decision_id']]))
        decision = resume_decision(previous, data, checkpoint=cp,
            cancelled_order_ids=[order['id']], same_order_id=order['id'])['decision']
        review = dict(id=intent['id'], order_id=order['id'], decision_input=data,
            decision_id=decision['decision_id'], plan_id=plan['id'], checkpoint_id=cp['checkpoint_id'],
            cancelled_order_ids=[order['id']],
            same_order_review=dict(schema='capital-same-order-review/0.1', order_id=order['id']))
        out.update(review_request=review, review_decision=decision)
        evaluation = next(p for p in decision['layer3']['alternatives'] if p['id'] == plan['id'])
        if evaluation['feasible']:
            # The retry decision does not authorize filling through a restriction
            # that becomes effective before its later receipt/activation. Keep this
            # bounded adapter closed rather than expand the native timing model.
            history = history_at([*declaration_sources(old), source_snapshot(data)], activation)
            limits = expired_entry_reasons(data['assets'][order['code']], activation)
            limits += asset_issues(history, order['code'], data['assets'][order['code']], activation, accepted_order=True)
            if limits:
                out.update(status='STOPPED_NOT_IMPLEMENTED',
                    reasons=['RETRY_RESTRICTION_BEFORE_ACTIVATION_NOT_IMPLEMENTED'], activation_restrictions=limits)
                return wrap()
        stage = 'NATIVE_RETRY_EXECUTION'
        job['tape'] += deepcopy(tail)
        job['observed_until'] = end
        job['reassessments'].append(review)
        out['execution_job'] = job
        actual = simulate(job)
        out['execution'] = actual
        _require(actual['status'] == 'SYNTHETIC_EXECUTION_REPLAY', 'RETRY_EXECUTION_REFUSED')
        _require(actual['order_history'] == old['order_history'] and
            actual['fills'][:len(old['fills'])] == old['fills'] and
            actual['reassessment_attempts'][:len(old['reassessment_attempts'])] == old['reassessment_attempts'] and
            all(actual['decision_records'].get(k) == v for k, v in old['decision_records'].items()) and
            all(actual['fact_sources'].get(k) == v for k, v in old['fact_sources'].items()) and
            set(old['reviewed_evidence_tokens']) <= set(actual['reviewed_evidence_tokens']), 'RETRY_HISTORY_CHANGED')
        final = make_checkpoint(origin, actual, through_at=end)
        out['checkpoint'] = _compact(final)
        attempt = next((a for a in actual['reassessment_attempts'] if a['id'] == intent['id']), None)
        if attempt is None:
            _require(actual['order_states'][order['id']]['status'].startswith(('CANCELLED', 'EXPIRED')),
                'RETRY_NOT_RECORDED')
            out.update(status='REPLAYED_RETRY_NOT_ACTIVATED', reasons=['ORIGINAL_ORDER_CLOSED_BEFORE_RETRY_ACTIVATION'])
        else:
            out.update(status='REPLAYED_ACCEPTED_REVIEW' if attempt['outcome'] == 'ACCEPTED' else 'REPLAYED_REJECTED_REVIEW',
                reasons=deepcopy(evaluation['reasons']))
        out['numeric_result'] = dict(decision=decision, order=deepcopy(order), fills=actual['fills'],
            order_states=actual['order_states'], events=actual['execution_events'], ledger=actual['ledger'],
            checkpoint_state=final['state'])
        return wrap()
    except (ValueError, KeyError, TypeError, IndexError, StopIteration) as exc:
        unsupported = ('OPENING_PAYABLE_CONTINUATION_NOT_IMPLEMENTED', 'SELLABLE_LIMIT_CONTINUATION_NOT_IMPLEMENTED',
            'EXISTING_ORDER_CONTINUATION_NOT_IMPLEMENTED', 'ACTIVE_ORDER_GAP_CONTINUATION_NOT_IMPLEMENTED')
        out.update(status='STOPPED_NOT_IMPLEMENTED' if str(exc).startswith(unsupported) else 'STOPPED_INPUT_ERROR',
            reasons=[str(exc)], failed_stage=stage, error_type=type(exc).__name__)
        return wrap()
