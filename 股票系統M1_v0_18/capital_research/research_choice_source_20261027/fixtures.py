"""Literal saved-source references and READ-only structural variants, no engines."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PROJECT = ROOT.parents[1]
OLD = ROOT.parent / 'research_choice_20261027'


def load(path):
    return json.loads(path.read_text())


def fp(value):
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return 'sha256:' + hashlib.sha256(body).hexdigest()


def reference(path):
    body = path.read_bytes()
    return dict(path=str(path.relative_to(REPO)), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())


def original(ref):
    raw = (REPO / ref['path']).read_bytes()
    if len(raw) != ref['bytes'] or hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise ValueError('SAVED_SOURCE_CHANGED')
    return json.loads(raw)


def materialize(spec):
    choice = original(spec['choice_source'])
    if 'value' in choice:
        choice = choice['value']
    source = original(spec['explicit_source'])
    for value, edits in [(choice, spec['choice_edits']), (source, spec['source_edits'])]:
        for edit in edits:
            row = value
            for key in edit['path'][:-1]:
                row = row[key]
            row[edit['path'][-1]] = deepcopy(edit['value'])
    if spec['duplicate_candidate']:
        members = source['adapter']['generation']['research']['candidates']
        key = choice['choice']['selected']['id']
        members.append(deepcopy(next(v for v in members if v['id'] == key)))
    if spec['refresh_source_content_ids']:
        choice['choice']['source_binding'].update(source_document_id=fp(source),
            generation_document_id=fp(source['adapter']['generation']))
    if spec['resign_record']:
        c = choice['choice']
        c['record_id'] = fp({k:v for k,v in c.items() if k != 'record_id'})
    if spec['bare_generation']:
        source = source['adapter']['generation']
    return dict(choice_value=choice, explicit_source=source)
