"""Verify shipped data against immutable parent and the exact original review."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from hurdle_chart.build import ROOT, attach, selection
from pressure_chart.verify_artifact import verify as verify_sources
from product_candidate.build import publish_immutable
from technical_chart.build import unpack
from contracts import fingerprint


def decode(path):
    match = re.search(r'id="payload">(.*?)</script>', Path(path).read_text(), re.S)
    if not match:
        raise ValueError('Embedded payload missing')
    return unpack(json.loads(match.group(1)))


def verify(html, history, oracle):
    report = verify_sources(html, history)
    actual = decode(html)
    parent = decode(ROOT / 'pressure_chart/generated/M1_v0_19_pressure_chart.html')
    if actual != attach(parent):
        raise ValueError('Shipped chart is not exactly the additive manual layer over immutable parent')
    layer = [v for rows in actual['manual_hurdle_layers'].values() for v in rows if v]
    if len(layer) != 1:
        raise ValueError('Manual annotation leaked into other frames')
    cases = json.loads(Path(oracle).read_text())['cases']
    for row in cases:
        if fingerprint(selection(actual, row['series'], row['as_of'])) != row['fingerprint']:
            raise ValueError('Selection oracle differs from shipped data')
    report.update(parent_artifact_id=parent['artifact_id'], full_parent_payload_preserved=True,
                  exact_manual_matches=1, selection_oracle_cases=len(cases),
                  manual_source_fingerprints=layer[0]['source_fingerprints'],
                  original_review_sha256=hashlib.sha256((ROOT.parent / 'docs/visual-discussion/20261018_1101_selected_hurdles.json').read_bytes()).hexdigest(),
                  other_frames_manual_annotation='NULL_NO_HISTORICAL_BACKFILL')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', required=True)
    parser.add_argument('--history', required=True)
    parser.add_argument('--oracle', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    report = verify(args.html, args.history, args.oracle)
    print(publish_immutable(args.report, json.dumps(report, ensure_ascii=False, indent=2).encode()))
    print(json.dumps(report, ensure_ascii=False, indent=2))
