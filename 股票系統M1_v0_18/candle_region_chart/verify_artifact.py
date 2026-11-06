"""Verify the actual region HTML, frozen parent, cases and source data."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from candle_region_chart.build import attach, load_parent, selection
from pressure_chart.verify_artifact import verify as verify_sources
from technical_chart.build import unpack
from product_candidate.build import publish_immutable
from contracts import fingerprint


def verify(html, history, oracle):
    report = verify_sources(html, history)
    raw = Path(html).read_bytes()
    actual = unpack(json.loads(re.search(r'id="payload">(.*?)</script>', raw.decode(), re.S).group(1)))
    parent = load_parent()
    if actual != attach(parent):
        raise ValueError('Region artifact changed original data or reviewed cases')
    cases = json.loads(Path(oracle).read_text())['cases']
    for row in cases:
        if fingerprint(selection(actual, row['series'], row['as_of'])) != row['fingerprint']:
            raise ValueError('Shipped selection oracle mismatch')
    display = next(v for rows in actual['candle_region_extents'].values() for v in rows if v)
    layer = next(v for rows in actual['region_layers'].values() for v in rows if v)
    report.update(source_html_sha256=hashlib.sha256(raw).hexdigest(), frozen_0_3_payload_preserved=True,
                  exact_region_case_frames=sum(v is not None for rows in actual['region_layers'].values() for v in rows),
                  display_extents=display, selection_oracles=len(cases), g2_endpoint_fields_verified=10,
                  g1_exact_start=None, region_price_bounds=None, region_volume_rule=None,
                  review_sources=layer['review_sources'], physical_android='NOT_TESTED_NEW_BUILD')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('html', 'history', 'oracle', 'report'):
        p.add_argument('--' + name, required=True)
    a = p.parse_args()
    report = verify(a.html, a.history, a.oracle)
    print(publish_immutable(a.report, json.dumps(report,ensure_ascii=False,indent=2).encode()))
    print(json.dumps(report,ensure_ascii=False,indent=2))
