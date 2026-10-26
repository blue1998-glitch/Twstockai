"""Pure knowledge receipts, separate from accepted trading decisions/accounts."""
from copy import deepcopy
from graph_core.core import fingerprint

RECEIPT = 'capital-fact-receipt/0.1'
ATTEMPT = 'capital-reassessment-attempt/0.1'


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
        cancelled_order_ids=deepcopy(review['cancelled_order_ids']))
    value['attempt_id'] = fingerprint(value)
    return value
