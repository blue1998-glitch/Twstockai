"""Pure saved-result intent selection; no decision, accounting or execution import."""
from copy import deepcopy
from .lifecycle import FLAGS, _fp, _integer, _time, _snapshot, _signed
from .quantity_choice_rules import select_candidate

INPUT = 'capital-research-choice-input/0.1'
SCHEMA = 'capital-research-choice/0.1'
ELIGIBLE = {'CURRENTLY_FEASIBLE': 'FEASIBLE', 'WAIT_SETTLEMENT_REASSESSMENT': 'CONDITIONAL'}


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def bind_saved_source(saved):
    """Validate saved structural links, never rerun a numerical producer."""
    a = saved['adapter']; g = a['generation']; r = g['research'] if g is not None else None
    _require(a['schema'] == 'capital-quantity-after-retry/0.1' and a['synthetic'] is True and
        a['status'] == 'GENERATED' and r is not None and r['schema'] == 'capital-quantity-candidates/0.2' and
        r['status'] == 'COMPLETE' and r['enumeration_complete'] is True, 'COMPLETE_SAVED_GENERATION_REQUIRED')
    for row in (a, r):
        _require(all(row[k] is False for k in FLAGS) and row['primary_pressure_id'] is None and
            row['ranking'] is None and row['selected_id'] is None and
            row['order_generation'] == row['execution'] == 'NOT_PERFORMED', 'RESEARCH_ONLY_SOURCE_REQUIRED')
    q = a['quantity_request']; cp = q['continuation']['checkpoint']; e = cp['execution_result']; s = cp['state']
    _require(q['schema'] == 'capital-quantity-candidates-input/0.2' and q['synthetic'] is True and
        g['source_integrity_metadata']['full_request_id'] == _fp(q), 'SAVED_QUANTITY_REQUEST_CONFLICT')
    _snapshot(e, cp, '/adapter/quantity_request/continuation/checkpoint')
    _require(_fp(cp['origin_ledger_input']) == e['origin_ledger_input_id'], 'SAVED_ORIGIN_FINGERPRINT_CONFLICT')
    data = q['decision_input']; baseline = r['baseline']; account = a['account']; binding = a['binding']
    _signed(baseline, 'decision_id')
    _require(account == data['account'] and _fp(account) == r['common_account_id'] == baseline['common_account_id'],
        'SAVED_ACCOUNT_BINDING_CONFLICT')
    _require(data['data_cutoff'] == s['through_at'] and baseline['data_cutoff'] == data['data_cutoff'] and
        baseline['decision_at'] == data['decision_at'] and _time(data['decision_at']) >= _time(s['ledger_close']['available_at']),
        'SAVED_CUTOFF_BINDING_CONFLICT')
    previous = q['continuation']['previous_decision']['decision']
    _require(previous == e['decision_records'][e['latest_decision_id']] and
        baseline['continuity']['checkpoint_id'] == cp['checkpoint_id'] and
        baseline['continuity']['state_id'] == cp['state_id'] and
        baseline['continuity']['latest_predecessor_id'] == e['latest_decision_id'], 'SAVED_LATEST_BINDING_CONFLICT')
    _require(binding['checkpoint_id'] == cp['checkpoint_id'] and binding['state_id'] == cp['state_id'] and
        binding['execution_result_id'] == e['result_id'] and binding['origin_ledger_input_id'] == e['origin_ledger_input_id'] and
        binding['latest_decision_id'] == e['latest_decision_id'] and
        binding['latest_common_account_id'] == e['latest_common_account_id'] and
        binding['reviewed_evidence_tokens'] == s['reviewed_evidence_tokens'] and
        binding['received_attempt_ids'] == [v['attempt_id'] for v in e['reassessment_attempts']], 'SAVED_ADAPTER_BINDING_CONFLICT')
    _require(set(s['reviewed_evidence_tokens']) <= set(data['consumed_evidence_tokens']) and
        set(s['reviewed_evidence_tokens']) <= set(baseline['reviewed_evidence_tokens']), 'SAVED_TOKEN_HISTORY_CONFLICT')
    return dict(source_document_id=_fp(saved), generation_document_id=_fp(g), quantity_request_id=_fp(q),
        source_input_id=saved['source_integrity_metadata']['full_input_id'], account_id=_fp(account),
        checkpoint_id=cp['checkpoint_id'], state_id=cp['state_id'], execution_result_id=e['result_id'],
        origin_ledger_input_id=e['origin_ledger_input_id'], latest_decision_id=e['latest_decision_id'],
        latest_common_account_id=e['latest_common_account_id'], data_cutoff=data['data_cutoff'], decision_at=data['decision_at'],
        historical_reviewed_tokens=deepcopy(s['reviewed_evidence_tokens']),
        decision_reviewed_tokens=deepcopy(baseline['reviewed_evidence_tokens']),
        received_attempt_ids=[v['attempt_id'] for v in e['reassessment_attempts']],
        versions=dict(adapter=a['schema'], generation=r['schema'], checkpoint=cp['schema'], decision=baseline['schema']))


def _qualified(candidate):
    classification = candidate['classification']
    if classification not in ELIGIBLE or candidate['feasible_for_research'] is not True:
        raise ValueError('CANDIDATE_NOT_QUALIFIED')
    core = candidate['core_evaluation']
    _require(core['feasible'] is True and core['status'] == ELIGIBLE[classification] and
        not core['reasons'] and not candidate['reasons'] and not candidate['batch_gate_reasons'],
        'SAVED_CANDIDATE_QUALIFICATION_CONFLICT')
    _require(core['id'] == candidate['id'] == candidate['plan']['id'] and
        core['targets'] == candidate['plan']['targets'], 'SAVED_CANDIDATE_PLAN_CONFLICT')
    _require(core['funding'] == ('SETTLED' if classification == 'CURRENTLY_FEASIBLE' else
        'WAIT_SALE_SETTLEMENT_AND_REEVALUATE'), 'SAVED_CANDIDATE_FUNDING_CONFLICT')
    return classification


def choose_saved(request):
    r = dict(schema=SCHEMA, synthetic=True, status='REFUSED', reasons=[], request_id=_fp(request),
        source_binding=None, requested_selection=deepcopy(request.get('selection')),
        recorded_at=request.get('recorded_at'), selected=None, rejected_candidate=None,
        purpose='EXPLICIT_RESEARCH_INTENT_ONLY', ranking=None, execution_authorized=False,
        order_generation='NOT_PERFORMED', execution='NOT_PERFORMED', primary_pressure_id=None,
        **{k: False for k in FLAGS})
    try:
        _require(set(request) == {'schema', 'synthetic', 'saved_result', 'source_binding', 'selection', 'recorded_at'} and
            request['schema'] == INPUT and request['synthetic'] is True, 'EXPLICIT_RESEARCH_CHOICE_REQUIRED')
        binding = bind_saved_source(request['saved_result'])
        _require(request['source_binding'] == binding, 'SOURCE_BINDING_MISMATCH')
        r['source_binding'] = binding
        _require(_time(request['recorded_at']) >= _time(binding['decision_at']), 'RECORD_TIME_PRECEDES_SOURCE_DECISION')
        research = request['saved_result']['adapter']['generation']['research']
        candidate = select_candidate(research['candidates'], request['selection'], _integer)
        reason = request['selection']['reason']
        _require(isinstance(reason, str) and bool(reason.strip()), 'EXPLICIT_TEXT_REASON_REQUIRED')
        r['rejected_candidate'] = deepcopy(candidate)
        classification = _qualified(candidate)
        _require(candidate['core_evaluation']['common_account_id'] == binding['account_id'], 'SELECTED_ACCOUNT_CONFLICT')
        r.update(status='RECORDED_CONDITIONAL_RESEARCH_INTENT' if classification == 'WAIT_SETTLEMENT_REASSESSMENT'
            else 'RECORDED_RESEARCH_INTENT', selected=deepcopy(candidate), rejected_candidate=None)
    except (ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        r['reasons'] = [str(exc)]
    r['record_id'] = _fp(r)
    return dict(choice=r)


def validate_record(saved):
    """READ only: validate the saved record, without choosing or fetching source."""
    _require(set(saved) == {'choice'}, 'CHOICE_RECORD_ENVELOPE_REQUIRED')
    r = saved['choice']
    _require(r['schema'] == SCHEMA and r['synthetic'] is True and
        r['purpose'] == 'EXPLICIT_RESEARCH_INTENT_ONLY', 'UNSUPPORTED_CHOICE_RECORD')
    _signed(r, 'record_id')
    _require(all(r[k] is False for k in FLAGS) and r['execution_authorized'] is False and
        r['primary_pressure_id'] is None and r['ranking'] is None and
        r['order_generation'] == r['execution'] == 'NOT_PERFORMED', 'RESEARCH_ONLY_RECORD_REQUIRED')
    if r['status'] == 'REFUSED':
        _require(r['selected'] is None and bool(r['reasons']), 'REFUSED_CHOICE_CONFLICT')
    else:
        classification = _qualified(r['selected'])
        expected = 'RECORDED_CONDITIONAL_RESEARCH_INTENT' if classification == 'WAIT_SETTLEMENT_REASSESSMENT' else 'RECORDED_RESEARCH_INTENT'
        _require(r['status'] == expected and r['source_binding'] is not None and not r['reasons'] and
            r['rejected_candidate'] is None, 'RECORDED_CHOICE_CONFLICT')
    return saved
