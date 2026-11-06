"""Bound completed synthetic retry output to the existing quantity generator."""
from copy import deepcopy
from decimal import localcontext

from .conditional_retry import predecessor
from .continuity import validate_checkpoint, account_at_checkpoint
from .core import fingerprint, quantity, number, timestamp
from .quantity_candidates import generate
from .quantity_replay import _quantity_request

INPUT = 'capital-quantity-after-retry-input/0.1'
SCHEMA = 'capital-quantity-after-retry/0.1'
FLAGS = ('data_qualified', 'execution_model_qualified', 'historical_signal_eligible',
         'policy_authorized', 'live_execution_authorized')


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def generate_after_retry(request):
    with localcontext() as ctx:
        ctx.prec = 50
        return _generate(request)


def _generate(request):
    out = dict(schema=SCHEMA, synthetic=True, status='PENDING', reasons=[], binding=None,
        account=None, quantity_request=None, generation=None, ranking=None, selected_id=None,
        order_generation='NOT_PERFORMED', execution='NOT_PERFORMED', primary_pressure_id=None,
        **{k: False for k in FLAGS})
    stage = 'INPUT'

    def wrap():
        return dict(adapter=out, source_integrity_metadata=dict(full_input_id=fingerprint(request)))

    try:
        _require(set(request) == {'schema', 'synthetic', 'saved_result', 'checkpoint', 'predecessor',
            'decision_template', 'quantity_template'} and request['schema'] == INPUT and
            request['synthetic'] is True, 'EXPLICIT_SYNTHETIC_AFTER_RETRY_INPUT_REQUIRED')
        saved = request['saved_result']
        r = saved['review']
        _require(r['schema'] == 'capital-conditional-quantity-review/0.3' and r['synthetic'] is True and
            r['status'] in ('REPLAYED_ACCEPTED_REVIEW', 'REPLAYED_REJECTED_REVIEW', 'REPLAYED_RETRY_NOT_ACTIVATED') and
            all(r[k] is False for k in FLAGS) and r['primary_pressure_id'] is None,
            'COMPLETED_REVIEW_0_3_REQUIRED')
        cp = request['checkpoint']
        _require(set(cp) == {'schema', 'state', 'state_id', 'origin_ledger_input', 'execution_result',
            'integrity', 'checkpoint_id'} and cp['schema'] == 'capital-account-checkpoint/0.8',
            'FULL_CHECKPOINT_0_8_REQUIRED')
        _require(request['predecessor'] == predecessor(saved), 'EXACT_SAVED_PREDECESSOR_REQUIRED')
        stage = 'SAVED_RESULT_BINDING'
        e, job = r['execution'], r['execution_job']
        _require(cp['execution_result'] == e and cp['origin_ledger_input'] == job['ledger_input'] and
            {k: cp[k] for k in ('schema', 'checkpoint_id', 'state_id', 'state')} == r['checkpoint'],
            'SAVED_RESULT_CHECKPOINT_CONFLICT')
        _require(job['orders'] == e['orders'] and job['observed_until'] == e['observed_until'] and
            job['ledger_close_proof'] == e['ledger_close_proof'], 'SAVED_JOB_BINDING_CONFLICT')
        _require(all(any(a['request'] == v for v in job['reassessments']) for a in e['reassessment_attempts']),
            'SAVED_REVIEW_REQUEST_HISTORY_MISSING')
        origin, state = cp['origin_ledger_input'], cp['state']
        _require(all(s['kind'] == 'ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET' for s in origin['sources'].values()),
            'EXPLICIT_ENGINEERED_SOURCE_REQUIRED')
        # These are refusals, not qualification of an unvalidated account. No
        # candidates are generated for even a declared unsupported balance.
        if state['unfilled_orders']:
            out.update(status='STOPPED_NOT_IMPLEMENTED', reasons=['ACTIVE_ORDERS_NOT_SUPPORTED'])
            return wrap()
        if number(state['row']['purchase_payable']):
            out.update(status='STOPPED_NOT_IMPLEMENTED', reasons=['OPENING_PAYABLE_NOT_SUPPORTED'])
            return wrap()
        template, qtemplate = request['decision_template'], request['quantity_template']
        a, b = qtemplate['incumbent'], qtemplate['destination']
        order = r['original_approval']['order']
        _require(order['side'] == 'BUY' and order['code'] == b and a != b and a in state['row']['shares'],
            'ORIGINAL_DESTINATION_AND_DISTINCT_INCUMBENT_REQUIRED')
        if not quantity(state['row']['shares'][a]):
            out.update(status='STOPPED_NOT_IMPLEMENTED', reasons=['POSITIVE_INCUMBENT_REQUIRED'])
            return wrap()
        stage = 'AUTHORITATIVE_CHECKPOINT'
        validate_checkpoint(cp)
        approval = r['original_approval']
        original = e['decision_records'][approval['original_decision_id']]
        raw_plan = approval['original_plan']
        original_plan = next((p for p in original['layer3']['alternatives'] if p['id'] == raw_plan['id']), None)
        _require(original_plan is not None and original_plan['feasible'] and original_plan['family'] == 'C' and
            e['decision_id'] == original['decision_id'] and job['plan_id'] == raw_plan['id'] and
            any(p == raw_plan for p in job['decision_input']['plans']) and
            all(original_plan[k] == raw_plan[k] for k in ('id', 'family', 'route', 'targets', 'trigger_ids', 'conditions')) and
            any(order == o for o in e['order_history']) and original['decision_at'] == order['decision_at'],
            'ORIGINAL_APPROVAL_BINDING_CONFLICT')
        opening = next(p for p in original['layer3']['alternatives'] if p['id'] == 'A-zero')['targets']
        original_incumbents = [c for c in opening if quantity(original_plan['targets'][c]) < quantity(opening[c])]
        if len(original_incumbents) != 1:
            out.update(status='STOPPED_NOT_IMPLEMENTED', reasons=['ORIGINAL_INCUMBENT_ROLE_NOT_SAVED'])
            return wrap()
        _require(a == original_incumbents[0], 'INCUMBENT_DIFFERS_FROM_ORIGINAL_ROLE')
        _require(qtemplate['batch_context']['phase'] == 'ADDITIONAL_BATCH', 'ADDITIONAL_BATCH_REQUIRED')
        _require(template['data_cutoff'] == state['through_at'], 'CUTOFF_MUST_MATCH_SAVED_CHECKPOINT')
        original_assets = job['decision_input']['assets']
        _require(set(template['assets']) == set(original_assets) and
            all(template['assets'][c][k] == original_assets[c][k] for c in original_assets
                for k in ('source_id', 'basis_id', 'adjustment_version')) and
            template['cost_model'] == job['decision_input']['cost_model'], 'SOURCE_BASIS_OR_COST_CHANGED')
        for c, asset in template['assets'].items():
            marks = [m for m in asset['marks'] if m['occurred_at'] == template['data_cutoff'] and
                timestamp(m['available_at']) <= timestamp(template['decision_at'])]
            _require(len(marks) == 1 and number(marks[0]['price']) ==
                number(origin['assets'][c]['quotes'][template['data_cutoff'][:10]]),
                'CUTOFF_MARK_DIFFERS_FROM_ORIGINAL_LEDGER')
        account = account_at_checkpoint(cp, decision_at=template['decision_at'], cancelled_order_ids=[])
        previous = dict(decision=deepcopy(e['decision_records'][e['latest_decision_id']]))
        continuation = dict(previous_decision=previous, checkpoint=deepcopy(cp), cancelled_order_ids=[])
        q = _quantity_request(dict(decision_template=template, quantity_template=qtemplate), account, continuation)
        q['decision_input']['consumed_evidence_tokens'] = sorted(
            set(q['decision_input']['consumed_evidence_tokens']) | set(state['reviewed_evidence_tokens']))
        out.update(account=account, quantity_request=q, binding=dict(
            source_document_id=fingerprint(saved), execution_result_id=e['result_id'],
            checkpoint_id=cp['checkpoint_id'], state_id=cp['state_id'],
            latest_decision_id=e['latest_decision_id'], latest_common_account_id=e['latest_common_account_id'],
            origin_ledger_input_id=e['origin_ledger_input_id'], origin_initial_capital=state['origin_initial_capital'],
            current_net_accrual_equity=state['row']['net_accrual_equity'],
            reviewed_evidence_tokens=deepcopy(state['reviewed_evidence_tokens']),
            received_attempt_ids=[v['attempt_id'] for v in e['reassessment_attempts']]))
        stage = 'EXISTING_QUANTITY_GATE'
        generation = generate(q)
        out['generation'] = generation
        research = generation['research']
        out.update(status='GENERATED' if research['status'] == 'COMPLETE' else 'STOPPED_QUANTITY_GATE',
            reasons=deepcopy(research['reasons']))
        return wrap()
    except (ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        unsupported = ('OPENING_PAYABLE_CONTINUATION_NOT_IMPLEMENTED', 'SELLABLE_LIMIT_CONTINUATION_NOT_IMPLEMENTED',
            'EXISTING_ORDER_CONTINUATION_NOT_IMPLEMENTED', 'ACTIVE_ORDER_GAP_CONTINUATION_NOT_IMPLEMENTED')
        out.update(status='STOPPED_NOT_IMPLEMENTED' if str(exc).startswith(unsupported) else 'STOPPED_INPUT_ERROR',
            reasons=[str(exc)], failed_stage=stage, error_type=type(exc).__name__)
        return wrap()
