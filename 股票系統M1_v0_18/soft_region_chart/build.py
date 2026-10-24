"""Build a borderless style revision, preserving the exact0.4 analytical payload."""
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
from technical_chart.build import pack, unpack
from candle_region_chart.build import render as render_parent, selection
from product_candidate.build import publish_immutable

VERSION = 'candle-region-chart-view/0.4.1'
NAME = 'M1_v0_19_soft_regions_v041.html'
PARENT = ROOT / 'candle_region_chart/generated/M1_v0_19_candle_regions_v04.html'
PARENT_SHA256 = '8642986a70a1c315046327b4ec97452eae19ba78fbe619a713ce2965de42d44f'


def build():
    raw = PARENT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARENT_SHA256:
        raise ValueError('Immutable0.4 fingerprint mismatch')
    parent = unpack(json.loads(re.search(r'id="payload">(.*?)</script>', raw.decode(), re.S).group(1)))
    value = deepcopy(parent)
    value['view_version'] = VERSION
    value.pop('artifact_id')
    value['artifact_id'] = fingerprint(value)
    if unpack(pack(value)) != value:
        raise ValueError('Lossless transport mismatch')
    assert {k: v for k, v in parent.items() if k not in ('view_version', 'artifact_id')} == {
        k: v for k, v in value.items() if k not in ('view_version', 'artifact_id')}
    html = render_parent(value)
    old_js = (ROOT / 'candle_region_chart/regions_viewer.js').read_text()
    new_js = (Path(__file__).parent / 'regions_viewer.js').read_text()
    if html.count(old_js) != 1:
        raise ValueError('Parent region extension must occur exactly once')
    html = html.replace(old_js, new_js)
    html = html.replace('M1 K線範圍價量區域主圖 0.4', 'M1 K線淡底色主圖 0.4.1')
    html = html.replace('M1 K線範圍區域主圖 0.4', 'M1 K線淡底色主圖 0.4.1')
    cases = []
    for s in [*value['numbers']['series'], *value['history_series']]:
        for i in sorted({0, 33, 60, len(s['frames']) // 2, len(s['frames']) - 1}):
            f = s['frames'][i]
            cases.append(dict(series=s['key'], as_of=f['as_of'], frame_id=f['frame_id'],
                              fingerprint=fingerprint(selection(value, s['key'], f['as_of']))))
    report = dict(status='PASS', view_version=VERSION, frozen_parent_sha256=PARENT_SHA256,
                  html_sha256=hashlib.sha256(html.encode()).hexdigest(),
                  html_bytes=len(html.encode()), parent_payload_equal_except=['view_version', 'artifact_id'],
                  source_data_and_extents_unchanged=True, physical_android='NOT_TESTED_NEW_BUILD')
    return {NAME: html.encode(), 'selection-oracle.json': json.dumps(dict(cases=cases), indent=2).encode(),
            'build-verification.json': json.dumps(report, ensure_ascii=False, indent=2).encode()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', required=True)
    out = Path(p.parse_args().output_dir).resolve()
    if 'output' not in out.parts:
        raise ValueError('Use a new output leaf')
    for name, raw in build().items():
        print(name, publish_immutable(out / name, raw), len(raw), hashlib.sha256(raw).hexdigest(), flush=True)


if __name__ == '__main__':
    main()
