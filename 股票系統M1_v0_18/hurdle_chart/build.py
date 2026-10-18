"""Build a NEW offline manual-three-hurdle chart; never overwrite old pages."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from contracts import fingerprint
from pressure_chart.build import make as pressure_make, selection as pressure_selection
from technical_chart.build import pack, unpack
from product_candidate.build import publish_immutable
from hurdle_chart.manual import bind, VERSION as LAYER_VERSION

VERSION = 'hurdle-chart-view/0.1'
NAME = 'M1_v0_19_three_hurdles.html'
CASE = ROOT.parent / 'docs/visual-discussion/20261018_1101_selected_hurdles.json'


def attach(original, case_path=CASE):
    payload = deepcopy(original)
    raw = Path(case_path).read_bytes()
    case = json.loads(raw)
    layers = {}
    matches = 0
    for s in [*payload['numbers']['series'], *payload['history_series']]:
        layers[s['key']] = [bind(case, raw, s, f) for f in s['frames']]
        matches += sum(v is not None for v in layers[s['key']])
    if matches != 1:
        raise ValueError(f'Expected one exact manual source/frame/basis, got {matches}')
    payload.update(schema_version='hurdle-chart-bundle/0.1', view_version=VERSION,
                   manual_layer_version=LAYER_VERSION, manual_hurdle_layers=layers,
                   parent_artifact_id=original['artifact_id'], physical_android='NOT_TESTED_NEW_BUILD')
    payload.pop('artifact_id')
    payload['artifact_id'] = fingerprint(payload)
    return payload


def make(history, case_path=CASE):
    return attach(pressure_make(history), case_path)


def selection(payload, key, as_of):
    value = pressure_selection(payload, key, as_of)
    s = next(s for s in [*payload['numbers']['series'], *payload['history_series']] if s['key'] == key)
    frame = next(f for f in s['frames'] if f['as_of'] == as_of)
    value.update(schema_version='hurdle-chart-selection/0.1', view_version=VERSION,
                 manual_hurdles=deepcopy(payload['manual_hurdle_layers'][key][frame['index']]))
    return value


def render(payload):
    here = Path(__file__).parent
    raw = json.dumps(pack(payload), ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    for char, escaped in [('&', '\\u0026'), ('<', '\\u003c'), ('>', '\\u003e'),
                          ('\u2028', '\\u2028'), ('\u2029', '\\u2029')]:
        raw = raw.replace(char, escaped)
    style = (ROOT / 'pressure_chart/viewer.css').read_text() + (here / 'viewer.css').read_text()
    script = (here / 'viewer.js').read_text().replace('// @@MANUAL_EXTENSION@@', (here / 'manual_viewer.js').read_text())
    return (here / 'template.html').read_text().replace('@@DATA@@', raw).replace('@@STYLE@@', style).replace('@@SCRIPT@@', script)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    out = Path(args.output_dir).resolve()
    if 'output' not in out.parts or out == ROOT:
        raise ValueError('Use a new dedicated output leaf')
    payload = make(args.history)
    if unpack(pack(payload)) != payload:
        raise ValueError('Lossless transport mismatch')
    cases = []
    for s in [*payload['numbers']['series'], *payload['history_series']]:
        for i in sorted({0, 33, 60, len(s['frames']) // 2, len(s['frames']) - 1}):
            f = s['frames'][i]
            cases.append(dict(series=s['key'], as_of=f['as_of'],
                              fingerprint=fingerprint(selection(payload, s['key'], f['as_of'])), frame_id=f['frame_id']))
    files = {NAME: render(payload).encode(),
             'selection-oracle.json': json.dumps(dict(cases=cases), ensure_ascii=False, indent=2).encode(),
             'window-oracle.json': (ROOT / 'pressure_chart/generated/window-oracle.json').read_bytes(),
             'manual-layer.json': json.dumps(next(v for rows in payload['manual_hurdle_layers'].values() for v in rows if v), ensure_ascii=False, indent=2).encode()}
    for name, content in files.items():
        path = out / name
        if path.is_symlink() or path.exists() and path.read_bytes() != content:
            raise ValueError('Existing different output: ' + str(path))
    for name, content in files.items():
        print(name, publish_immutable(out / name, content), len(content), hashlib.sha256(content).hexdigest(), flush=True)


if __name__ == '__main__':
    main()
