"""Fingerprint-bound fixture IO; the production adapter receives plain JSON."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def load(path):
    return json.loads(path.read_text())


def fingerprint(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return 'sha256:' + hashlib.sha256(raw.encode()).hexdigest()


def _source(spec):
    raw = (REPO / spec['path']).read_bytes()
    if len(raw) != spec['bytes'] or hashlib.sha256(raw).hexdigest() != spec['sha256']:
        raise ValueError('SAVED_SOURCE_CHANGED: ' + spec['path'])
    value = json.loads(raw)
    for key in spec['pointer']:
        value = value[key]
    return value


def materialize(spec):
    request = deepcopy(spec['request'])
    request['saved_result'] = _source(spec['saved_source'])
    request['checkpoint'] = _source(spec['checkpoint_source'])
    for edit in spec['edits']:
        node = request
        for key in edit['path'][:-1]:
            node = node[key]
        if edit.get('delete'):
            del node[edit['path'][-1]]
        else:
            node[edit['path'][-1]] = deepcopy(edit['value'])
    saved, cp = request['saved_result'], request['checkpoint']
    execution = cp['execution_result']
    request['predecessor'] = dict(document_id=fingerprint(saved), execution_result_id=execution['result_id'],
        checkpoint_id=cp['checkpoint_id'], latest_decision_id=execution['latest_decision_id'],
        latest_common_account_id=execution['latest_common_account_id'],
        reviewed_evidence_tokens=deepcopy(execution['reviewed_evidence_tokens']))
    request['predecessor'].update(deepcopy(spec['predecessor_overrides']))
    return request
