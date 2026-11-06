"""Pure knowledge receipts, separate from accepted trading decisions/accounts."""
from copy import deepcopy
from graph_core.core import fingerprint
from .fact_lineage import source_snapshot

RECEIPT = 'capital-fact-receipt/0.1'
ATTEMPT = 'capital-reassessment-attempt/0.2'


def request_content_id(review):
    """Bind the entire submitted JSON, independently of receipt time/outcome."""
    if not isinstance(review.get('id'),str) or not review['id']:
        raise ValueError('REASSESSMENT_REQUEST_ID_REQUIRED')
    return fingerprint(review)


def check_request_retry(review, prior):
    """A known ID is idempotent only for exactly the same canonical content."""
    content_id=request_content_id(review)
    if prior.get('schema')!=ATTEMPT or 'request_content_id' not in prior:
        raise ValueError('REASSESSMENT_REQUEST_IDENTITY_NOT_IMPLEMENTED: no inferred historical request')
    if content_id!=prior['request_content_id']:
        raise ValueError('REASSESSMENT_ID_CONTENT_CONFLICT: same review ID has different submitted content')


def validate_request_binding(attempt):
    request=attempt['request']
    if request_content_id(request)!=attempt['request_content_id']:
        raise ValueError('Reassessment request fingerprint conflict')
    if (any(request[k]!=attempt[k] for k in ('id','order_id','plan_id','checkpoint_id','cancelled_order_ids'))
            or request['decision_id']!=attempt['decision']['decision_id']):
        raise ValueError('Reassessment request/result binding conflict')
    if source_snapshot(request['decision_input'])!=attempt['fact_source']:
        raise ValueError('Reassessment request/source binding conflict')


def declaration_sources(execution, *, decision_ids=None, attempt_limit=None):
    ids = execution['decision_ids'] if decision_ids is None else decision_ids
    result = [execution['fact_sources'][key] for key in ids]
    attempts = execution['reassessment_attempts']
    if attempt_limit is not None:
        attempts = attempts[:attempt_limit]
    for attempt in attempts:
        if attempt['outcome'] == 'REJECTED':
            result.append(dict(schema=RECEIPT, received_at=attempt['observed_at'],
                               source=deepcopy(attempt['fact_source'])))
    return result


def reviewed_tokens(execution):
    records = list(execution['decision_records'].values())
    records += [a['decision'] for a in execution['reassessment_attempts']]
    return sorted(set().union(*(set(d['reviewed_evidence_tokens']) for d in records)))


def make_attempt(review, decision, source, observed_at, outcome):
    value = dict(schema=ATTEMPT, id=review['id'], order_id=review['order_id'],
        observed_at=observed_at, outcome=outcome, decision=deepcopy(decision),
        fact_source=deepcopy(source), plan_id=review['plan_id'],
        checkpoint_id=review['checkpoint_id'],
        cancelled_order_ids=deepcopy(review['cancelled_order_ids']),
        request=deepcopy(review),request_content_id=request_content_id(review))
    value['attempt_id'] = fingerprint(value)
    return value
