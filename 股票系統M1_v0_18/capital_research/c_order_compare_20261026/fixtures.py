"""Load fingerprint-bound saved originals; no numerical producer or mutation."""
import hashlib
import json
from pathlib import Path

from capital_research.lifecycle_compare import INPUT

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def load(path):
    return json.loads(path.read_text())


def load_request(name):
    spec = load(ROOT / 'cases' / name / 'input.json')
    items = []
    for item in spec['items']:
        source = item['source']
        path = REPO / source['path']
        raw = path.read_bytes()
        if (len(raw) != source['bytes'] or
                hashlib.sha256(raw).hexdigest() != source['sha256']):
            raise ValueError('SAVED_ORIGINAL_CHANGED: ' + source['path'])
        items.append(dict(label=item['label'], saved_result=json.loads(raw)))
    return dict(schema=INPUT, synthetic=True, items=items)
