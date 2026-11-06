"""Fingerprint-bound old artifacts plus explicit JSON edits; no old producer."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).parent
REPO=ROOT.resolve().parents[2]


def materialize(spec):
    items=[]
    for item in spec['items']:
        source=item['source'];raw=(REPO/source['path']).read_bytes()
        assert len(raw)==source['bytes'] and hashlib.sha256(raw).hexdigest()==source['sha256']
        saved=json.loads(raw);edit=item['edit']
        if edit is not None:
            target=saved
            for key in edit['path'][:-1]:target=target[key]
            key=edit['path'][-1]
            if edit['op']=='remove':del target[key]
            elif edit['op']=='replace':
                assert key in target;target[key]=edit['value']
            elif edit['op']=='add':
                assert key not in target;target[key]=edit['value']
            else:raise ValueError(edit['op'])
        items.append(dict(label=item['label'],saved_result=saved))
    return dict(schema='capital-lifecycle-comparison-input/0.1',synthetic=True,items=items)


def load(name):return materialize(json.loads((ROOT/'cases'/name/'input.json').read_text()))
