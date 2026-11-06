"""Explicit synthetic day-end availability; never invent a real exchange close."""
from copy import deepcopy
from .core import timestamp


def close_record(origin, proof, as_of):
    if not proof or proof.get('schema')!='synthetic-ledger-close-clock/0.1':
        raise ValueError('EXPLICIT_LEDGER_CLOSE_PROOF_REQUIRED')
    if proof.get('qualification')!='DECLARED_SYNTHETIC_DAY_END_NOT_REAL_MARKET_OR_BROKER_PROOF':
        raise ValueError('Synthetic close-clock qualification required')
    day=as_of[:10]
    if day not in {r['date'] for r in origin['calendar']} or day not in proof['closes']:
        raise ValueError('Missing explicit ledger daily close')
    row=proof['closes'][day]
    if row['as_of']!=as_of or timestamp(row['available_at'])<timestamp(row['as_of']):
        raise ValueError('DAILY_CLOSE_WATERMARK_REQUIRED: cannot relabel an end-of-day ledger as intraday')
    if not row['source_ids'] or any(s not in origin['sources'] or origin['sources'][s]['kind']!='ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET' for s in row['source_ids']):
        raise ValueError('Close proof must bind explicit synthetic ledger sources')
    return deepcopy(row)
