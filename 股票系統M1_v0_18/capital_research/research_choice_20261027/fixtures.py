"""Only reference-bound saved JSON IO; no decision or market engine."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def load(path):
    return json.loads(path.read_text())


def fp(value):
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return 'sha256:' + hashlib.sha256(text.encode()).hexdigest()


def declared_binding(saved):
    a = saved['adapter']; q = a['quantity_request']; cp = q['continuation']['checkpoint']
    e = cp['execution_result']; s = cp['state']; g = a['generation']; r = g['research']; d = r['baseline'] or {}
    return dict(source_document_id=fp(saved), generation_document_id=fp(g), quantity_request_id=fp(q),
        source_input_id=saved['source_integrity_metadata']['full_input_id'], account_id=fp(a['account']),
        checkpoint_id=cp['checkpoint_id'], state_id=cp['state_id'], execution_result_id=e['result_id'],
        origin_ledger_input_id=e['origin_ledger_input_id'], latest_decision_id=e['latest_decision_id'],
        latest_common_account_id=e['latest_common_account_id'], data_cutoff=q['decision_input']['data_cutoff'],
        decision_at=q['decision_input']['decision_at'], historical_reviewed_tokens=deepcopy(s['reviewed_evidence_tokens']),
        decision_reviewed_tokens=deepcopy(d.get('reviewed_evidence_tokens', [])),
        received_attempt_ids=[x['attempt_id'] for x in e['reassessment_attempts']],
        versions=dict(adapter=a['schema'], generation=r['schema'], checkpoint=cp['schema'], decision=d.get('schema')))


def materialize(spec):
    source = spec['source']; raw = (REPO / source['path']).read_bytes()
    if len(raw) != source['bytes'] or hashlib.sha256(raw).hexdigest() != source['sha256']:
        raise ValueError('SAVED_SOURCE_CHANGED')
    saved = json.loads(raw)
    for edit in spec['edits']:
        row = saved
        for key in edit['path'][:-1]:
            row = row[key]
        row[edit['path'][-1]] = deepcopy(edit['value'])
    binding = declared_binding(saved)
    binding.update(deepcopy(spec['binding_overrides']))
    return dict(schema='capital-research-choice-input/0.1', synthetic=True, saved_result=saved,
        source_binding=binding, selection=deepcopy(spec['selection']), recorded_at=spec['recorded_at'])
