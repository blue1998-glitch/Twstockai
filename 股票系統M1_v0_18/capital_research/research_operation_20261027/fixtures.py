"""Explicit synthetic operation fixtures; no generator is called here."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from capital_research.quantity_after_retry_20261027.fixtures import materialize as generation_input

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
REPO = PROJECT.parent
OLD = ROOT.parent / 'quantity_after_retry_20261027'


def load(path):
    return json.loads(path.read_text())


def fp(value):
    return 'sha256:' + hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,
        separators=(',',':'),allow_nan=False).encode()).hexdigest()


def reference(path):
    b=path.read_bytes()
    return dict(path=str(path.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def materialize(spec):
    row=spec['generation_spec'];raw=(REPO/row['path']).read_bytes()
    if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
        raise ValueError('GENERATION_INPUT_SPEC_CHANGED')
    return dict(schema='capital-research-operation-input/0.1',synthetic=True,
        generation_input=generation_input(json.loads(raw)),selection=deepcopy(spec['selection']),
        recorded_at=spec['recorded_at'])
