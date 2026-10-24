"""A small, immutable style revision over the verified0.4.1 ZIP."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from contracts import fingerprint
from technical_chart.build import pack, unpack
from product_candidate.build import publish_immutable

VERSION = 'candle-region-chart-view/0.4.3'
NAME = 'M1_v0_19_soft_regions_v043.html'
PARENT_SHA256 = 'd6b9a16ad2e4c28b169ae3cbaf937da5e15006207d598fa82dabc523c0a07b1b'
PARENT = ROOT.parent / 'deliveries/m1-v019-soft-regions-v041-20261019/M1_v019_soft_regions_v041.zip'


def build():
    if hashlib.sha256(PARENT.read_bytes()).hexdigest() != PARENT_SHA256:
        raise ValueError('Frozen0.4.1 ZIP fingerprint mismatch')
    with zipfile.ZipFile(PARENT) as z:
        source = z.read('M1_v0_19_soft_regions_v041.html').decode()
    match = re.search(r'id="payload">(.*?)</script>', source, re.S)
    parent = unpack(json.loads(match.group(1)))
    value = deepcopy(parent)
    value['view_version'] = VERSION
    value.pop('artifact_id')
    value['artifact_id'] = fingerprint(value)
    unchanged = lambda v: {k: x for k, x in v.items() if k not in ('view_version', 'artifact_id')}
    if unchanged(parent) != unchanged(value) or unpack(pack(value)) != value:
        raise ValueError('Payload or precision changed')
    raw = json.dumps(pack(value), ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    for char, escape in [('&', '\\u0026'), ('<', '\\u003c'), ('>', '\\u003e'), ('\u2028', '\\u2028'), ('\u2029', '\\u2029')]:
        raw = raw.replace(char, escape)
    html = source[:match.start(1)] + raw + source[match.end(1):]
    html = html.replace('M1 K線淡底色主圖 0.4.1', 'M1 K線淡底色主圖 0.4.3')
    end = html.rfind('</script>')
    html = html[:end] + '\n' + (Path(__file__).parent / 'fill_patch.js').read_text() + '\n' + html[end:]
    result = dict(status='PASS', view_version=VERSION, parent_zip_sha256=PARENT_SHA256,
                  html_bytes=len(html.encode()), html_sha256=hashlib.sha256(html.encode()).hexdigest(),
                  payload_equal_except=['view_version', 'artifact_id'], lossless_transport=True,
                  default_opacity='0.18', local_display_choices=['0.12', '0.18', '0.26'],
                  physical_android='NOT_TESTED_NEW_BUILD')
    return {NAME: html.encode(), 'build-verification.json': json.dumps(result, ensure_ascii=False, indent=2).encode()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', required=True)
    out = Path(p.parse_args().output_dir).resolve()
    if 'output' not in out.parts:
        raise ValueError('Use a new output leaf')
    for name, content in build().items():
        print(name, publish_immutable(out / name, content), len(content), hashlib.sha256(content).hexdigest(), flush=True)


if __name__ == '__main__':
    main()
