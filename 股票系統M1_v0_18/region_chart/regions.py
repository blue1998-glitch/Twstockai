"""Offline binding of reviewed time regions; unknown price/volume rules stay null."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from contracts import fingerprint

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'g1': 'docs/visual-discussion/20261018_g1_region_review/user_review.json',
    'g1_facts': 'docs/visual-discussion/20261018_g1_region_review/g1_region_review_facts.json',
    'g2': 'docs/visual-discussion/20261018_g2_endpoints/user_review.json',
    'g2_verification': 'docs/visual-discussion/20261018_g2_endpoints/endpoint_source_verification.json',
}
VERSION = 'manual-region-layer/0.1'


def load_reviews():
    raw = {k: (ROOT.parent / p).read_bytes() for k, p in FILES.items()}
    return {k: json.loads(v) for k, v in raw.items()}, {
        k: dict(path=FILES[k], sha256=hashlib.sha256(v).hexdigest()) for k, v in raw.items()}


def bind(reviews, digests, series, frame):
    g1, g2, facts, verification = (reviews[k] for k in ('g1', 'g2', 'g1_facts', 'g2_verification'))
    for case in (g1, g2):
        b = case['source_binding']
        if (series['code'], series['price_mode'], series['source']['id'], frame['frame_id'],
            frame['chart_base'], frame['as_of']) != (case['code'], case['price_mode'], b['source_id'],
            b['frame_id'], b['chart_base'], case['analysis_as_of']):
            return None
    rows = series['bases'][frame['chart_base']]['bars'][:frame['index'] + 1]
    for key in ('source_id', 'frame_id', 'chart_base'):
        if facts[key] != g1['source_binding'][key]:
            raise ValueError('G1 evidence binding mismatch')
    export_sha = g1['source_binding']['original_export_sha256']
    if export_sha != g2['source_binding']['source_export_sha256'] or any(
            v['source_export_sha256'] != export_sha for v in (facts, verification)):
        raise ValueError('Original export fingerprint mismatch')
    if len(rows) != verification['source_bar_count'] or fingerprint(rows) != frame['data_fingerprint']:
        raise ValueError('Reviewed source prefix changed or incomplete')
    dates = [r['date'] for r in rows]
    if dates != sorted(set(dates)):
        raise ValueError('Source dates must be real, unique and ordered')
    by_date = {r['date']: r for r in rows}
    for date, expected in facts['exact_source_bars'].items():
        if by_date.get(date) != expected:
            raise ValueError('G1/C/volume evidence source mismatch: ' + date)
    region = g2['region']
    if region['start'] != by_date.get(region['exact_start_date']) or region['end'] != by_date.get(region['exact_end_date']):
        raise ValueError('G2 exact endpoint OHLCV mismatch')
    if verification['endpoints'] != {region['exact_start_date']: region['start'], region['exact_end_date']: region['end']}:
        raise ValueError('G2 endpoint report does not bind the reviewed interval')
    if len(verification['endpoint_field_checks']) != 10 or any(
            not c['equal'] or c['source_value'] != by_date[c['date']][c['field']] or
            c['user_reported'] != c['source_value'] for c in verification['endpoint_field_checks']):
        raise ValueError('G2 ten-field verification mismatch')
    for date, row in verification['endpoints'].items():
        if by_date.get(date) != row:
            raise ValueError('G2 endpoint verification source mismatch')
    for case in (g1, g2):
        r = case['representative']
        if by_date[r['source_date']]['high'] != r['raw_high']:
            raise ValueError('Original representative point changed')
    if g1['older_region']['exact_start_date'] is not None or any(
            g1['older_region'][k] is not None for k in ('price_bounds', 'total_volume', 'bar_membership')):
        raise ValueError('G1 unknown boundaries/volume cannot be invented')
    if any(region[k] is not None for k in ('price_bounds', 'total_volume', 'volume_measure_rule', 'automatic_region_split')):
        raise ValueError('G2 undefined price/volume/automatic rules must stay unknown')
    if any(g1['newer_region'][k] is not None for k in ('exact_start_date', 'end_date', 'bar_membership', 'actual_remaining_trapped_shares')):
        raise ValueError('C-right extent/ownership must stay unknown')
    month_indices = [i for i, r in enumerate(rows) if r['date'].startswith(g1['older_region']['start_month'])]
    if not month_indices:
        raise ValueError('G1 approximate month unavailable')
    cdate = g1['older_region']['end_reference']['date']
    cindex = dates.index(cdate)
    if by_date[cdate]['low'] != g1['older_region']['end_reference']['source_low']:
        raise ValueError('C source low mismatch')
    a, b = dates.index(region['exact_start_date']), dates.index(region['exact_end_date'])
    if not a <= dates.index(g2['representative']['source_date']) <= b:
        raise ValueError('G2 representative outside selected endpoints')
    # Padding below is ONLY a reading window. It never becomes formal membership,
    # a new region boundary, a flatness threshold or a volume aggregation rule.
    def navigation(first, last, cursor):
        return dict(start=max(0, first - 20), end=min(len(rows) - 1, last + 20), cursor=cursor,
                    qualification='DISPLAY_PADDING_ONLY_NOT_REGION_BOUNDARIES')
    items = [dict(id='G1', title='G1 約2023年9月→C',
        exact_start_date=None, approximate_start_month=g1['older_region']['start_month'],
        end_reference=deepcopy(g1['older_region']['end_reference']), price_bounds=None,
        total_volume=None, bar_membership=None, representative=deepcopy(g1['representative']),
        display=dict(month_first_index=month_indices[0], month_last_index=month_indices[-1],
                     c_index=cindex, qualification='MONTH_EDGE_IS_ONLY_AN_UNCERTAIN_DISPLAY_ANCHOR'),
        navigation=navigation(month_indices[0], cindex, dates.index(g1['representative']['source_date']))),
        dict(id='G2', title='G2 2023-01-16～2023-08-16',
        exact_start_date=region['exact_start_date'], exact_end_date=region['exact_end_date'],
        price_bounds=None, total_volume=None, volume_measure_rule=None,
        representative=deepcopy(g2['representative']), endpoints=dict(start=deepcopy(region['start']), end=deepcopy(region['end'])),
        display=dict(start_index=a, end_index=b, endpoint_inclusion='INCLUSIVE_DISPLAY_ONLY_NOT_A_VOLUME_MEASURE'),
        navigation=navigation(a, b, dates.index(g2['representative']['source_date']))),
        dict(id='C_RIGHT', title='C後新平緩帶｜終點未定',
        exact_start_date=None, end_date=None, bar_membership=None,
        user_characterization=g1['newer_region']['user_characterization'],
        qualification='USER_QUALITATIVE_JUDGMENT_NOT_VERIFIED_OWNERSHIP_OR_ALL_LATER_BARS_CLASSIFICATION',
        display=dict(c_index=cindex, draw='OPEN_DIRECTION_RAIL_ONLY_NO_ASSERTED_END_OR_PRICE_BOUNDS'),
        navigation=navigation(cindex, min(cindex + 40, len(rows) - 1), cindex))]
    return dict(schema_version=VERSION, code=series['code'], price_mode=series['price_mode'],
        analysis_as_of=frame['as_of'], source_id=series['source']['id'], frame_id=frame['frame_id'],
        chart_base=frame['chart_base'], data_prefix_fingerprint=frame['data_fingerprint'],
        review_sources=deepcopy(digests), original_reviews=dict(g1=deepcopy(g1), g2=deepcopy(g2)),
        g1_source_facts=deepcopy(facts), g2_endpoint_verification=deepcopy(verification),
        regions=items, c_source=deepcopy(by_date[cdate]),
        volume_evidence=[dict(bar=deepcopy(by_date[d]), qualification='RETAINED_SOURCE_REFERENCE_NOT_FORMAL_MAX_OR_REGION_VOLUME_RULE')
                         for d in ('2023-10-18', '2023-11-30')],
        integration_status='EXACT_MANUAL_TIME_REGIONS_ONLY_NOT_AUTOMATIC_STRATEGY',
        qualification='LATER_MANUAL_REVIEW_NOT_ASOF_AUTOMATIC_SIGNALS',
        classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED',
        product_usefulness='NOT_ESTABLISHED', remaining_ownership=None)
