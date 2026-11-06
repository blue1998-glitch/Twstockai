"""Bind a later human review to one exact source/frame/basis, offline only.

No automatic selection, region boundaries, scoring or volume rules are inferred.
The original review JSON is retained unchanged, including its historical status.
"""
from copy import deepcopy
from decimal import Decimal
import hashlib

VERSION = 'manual-hurdle-display/0.1'


def bind(case, case_bytes, series, frame):
    identity = (series['code'], series['price_mode'], series['source']['id'],
                frame['as_of'], frame['frame_id'], frame['chart_base'])
    expected = tuple(case[k] for k in ('code', 'price_mode', 'source_id',
                                      'analysis_as_of', 'frame_id', 'chart_base'))
    if identity != expected:
        return None
    if case['schema_version'] != 'manual-left-hurdles-review/0.1':
        raise ValueError('Unsupported manual review')
    if frame['price_mode'] != case['price_mode'] or frame['code'] != case['code']:
        raise ValueError('Frame identity conflicts with source')
    if case['reviewed_at'][:10] <= case['analysis_as_of']:
        raise ValueError('This adapter requires a later retrospective review')
    rows = series['bases'][frame['chart_base']]['bars'][:frame['index'] + 1]
    by_date = {r['date']: r for r in rows}
    refs = []
    if [r['id'] for r in case['references']] != ['G1', 'G2', 'G3']:
        raise ValueError('Preserve explicit user hurdle order')
    for order, ref in enumerate(case['references'], 1):
        if ref['order'] != order:
            raise ValueError('User order mismatch')
        dates = ref['matching_source_dates']
        if not dates or dates != sorted(set(dates)):
            raise ValueError('Missing or duplicate source dates')
        if ref['source_bars'] != [by_date.get(d) for d in dates]:
            raise ValueError('Manual reference source OHLCV mismatch')
        if any(d > frame['as_of'] or Decimal(by_date[d]['high']) != Decimal(ref['raw_high']) for d in dates):
            raise ValueError('Reference high or date mismatch')
        if ref['source_date'] is None:
            all_dates = [r['date'] for r in rows if Decimal(r['high']) == Decimal(ref['raw_high'])]
            if dates != all_dates or ref['source_bar'] is not None:
                raise ValueError('Price-only review must retain all matching source dates')
        elif dates != [ref['source_date']] or ref['source_bar'] != by_date[ref['source_date']]:
            raise ValueError('Explicit date mismatch')
        if ref['display_anchor_source_date'] not in dates:
            raise ValueError('Display anchor must reference a supplied match')
        if any(ref[k] is not None for k in ('region_start', 'region_end', 'region_price_bounds',
                                           'region_total_volume', 'volume_expansion_rule', 'automatic_selection_rule')):
            raise ValueError('Undefined core rules must stay unknown')
        close, high = Decimal(frame['close']), Decimal(ref['raw_high'])
        relation = 'ABOVE' if close > high else 'BELOW' if close < high else 'AT'
        if relation != ref['current_raw_close_relation']:
            raise ValueError('Review close relation conflicts with retained frame')
        refs.append(dict(reference=deepcopy(ref), current_close_relation=relation,
                         source_indices=[next(i for i, r in enumerate(rows) if r['date'] == d) for d in dates]))
    return dict(schema_version=VERSION, review=deepcopy(case), references=refs,
                integration_status='EXACT_MANUAL_CASE_DISPLAY_ONLY',
                source_fingerprints=dict(source_id=case['source_id'], frame_id=case['frame_id'],
                    chart_base=case['chart_base'], data_prefix=frame['data_fingerprint'],
                    review_file_sha256=hashlib.sha256(case_bytes).hexdigest(),
                    original_phone_export_sha256=case['export_sha256']),
                review_qualification=case['annotations_are'], comparison_basis=case['comparison_basis'],
                classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED')
