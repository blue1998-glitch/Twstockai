"""Independent region main chart over the immutable0.2 numerical payload."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from contracts import fingerprint
from product_candidate.build import publish_immutable
from technical_chart.build import pack, unpack
from hurdle_chart.build import selection as hurdle_selection
from region_chart.regions import bind, load_reviews

VERSION = 'manual-region-chart-view/0.3'
NAME = 'M1_v0_19_manual_regions_v03.html'
PARENT = ROOT / 'hurdle_chart/generated/labels_v02/M1_v0_19_three_hurdles_labels_v02.html'
PARENT_SHA256 = 'fe0d27111f9a03b23ea587cb195a5b5b3987b4862e7af6ee20684be1b69fbce6'


def load_parent():
    raw = PARENT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARENT_SHA256:
        raise ValueError('Immutable0.2 chart fingerprint mismatch')
    return unpack(json.loads(re.search(r'id="payload">(.*?)</script>', raw.decode(), re.S).group(1)))


def attach(parent, reviews=None, digests=None):
    if reviews is None:
        reviews, digests = load_reviews()
    value = deepcopy(parent)
    layers = {s['key']: [bind(reviews, digests, s, f) for f in s['frames']]
              for s in [*parent['numbers']['series'], *parent['history_series']]}
    if sum(v is not None for rows in layers.values() for v in rows) != 1:
        raise ValueError('Expected one exact manual region case')
    value.update(schema_version='manual-region-chart-bundle/0.1', view_version=VERSION,
                 region_layers=layers, region_parent_artifact_id=parent['artifact_id'],
                 physical_android='NOT_TESTED_NEW_BUILD')
    value.pop('artifact_id')
    value['artifact_id'] = fingerprint(value)
    return value


def selection(payload, key, as_of):
    value = hurdle_selection(payload, key, as_of)
    s = next(s for s in [*payload['numbers']['series'], *payload['history_series']] if s['key'] == key)
    f = next(f for f in s['frames'] if f['as_of'] == as_of)
    value.update(schema_version='manual-region-chart-selection/0.1',
                 manual_regions=deepcopy(payload['region_layers'][key][f['index']]))
    return value


def render(payload):
    here = Path(__file__).parent
    raw = json.dumps(pack(payload), ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    for char, escape in [('&', '\\u0026'), ('<', '\\u003c'), ('>', '\\u003e'), ('\u2028', '\\u2028'), ('\u2029', '\\u2029')]:
        raw = raw.replace(char, escape)
    style = ''.join((ROOT / n).read_text() for n in ['pressure_chart/viewer.css', 'hurdle_chart/viewer.css', 'region_chart/viewer.css'])
    script = (here / 'viewer.js').read_text().replace('// @@MANUAL_EXTENSION@@', (ROOT / 'hurdle_chart/manual_viewer.js').read_text()).replace('// @@REGION_EXTENSION@@', (here / 'regions_viewer.js').read_text())
    return (here / 'template.html').read_text().replace('@@DATA@@', raw).replace('@@STYLE@@', style).replace('@@SCRIPT@@', script)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', required=True)
    a = p.parse_args()
    out = Path(a.output_dir).resolve()
    if 'output' not in out.parts or out == ROOT:
        raise ValueError('Use a separate output leaf')
    payload = attach(load_parent())
    if unpack(pack(payload)) != payload:
        raise ValueError('Lossless transport mismatch')
    cases = []
    for s in [*payload['numbers']['series'], *payload['history_series']]:
        for i in sorted({0, 33, 60, len(s['frames']) // 2, len(s['frames']) - 1}):
            f = s['frames'][i]
            cases.append(dict(series=s['key'], as_of=f['as_of'], frame_id=f['frame_id'],
                              fingerprint=fingerprint(selection(payload, s['key'], f['as_of']))))
    layer = next(v for rows in payload['region_layers'].values() for v in rows if v)
    files = {NAME: render(payload).encode(),
             'selection-oracle.json': json.dumps(dict(cases=cases),ensure_ascii=False,indent=2).encode(),
             'region-layer.json': json.dumps(layer,ensure_ascii=False,indent=2).encode(),
             'manual-layer.json': (ROOT / 'hurdle_chart/generated/labels_v02/manual-layer.json').read_bytes(),
             'window-oracle.json': (ROOT / 'hurdle_chart/generated/labels_v02/window-oracle.json').read_bytes()}
    for name, content in files.items():
        q = out / name
        if q.is_symlink() or q.exists() and q.read_bytes() != content:
            raise ValueError('Existing different artifact: ' + str(q))
    for name, content in files.items():
        print(name, publish_immutable(out / name, content), len(content), hashlib.sha256(content).hexdigest(),flush=True)


if __name__ == '__main__':
    main()
