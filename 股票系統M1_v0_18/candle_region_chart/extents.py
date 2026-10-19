"""Exact source-derived display envelopes, never formal pressure/volume rules."""
from decimal import Decimal, InvalidOperation
from contracts import fingerprint

VERSION = 'candle-region-display-extent/0.1'


def decimal(value):
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError('Invalid source display number') from error
    if not result.is_finite():
        raise ValueError('Nonfinite source display number')
    return result


def envelope(bars, first, last, *, uncertain_start_month=None):
    if not 0 <= first <= last < len(bars):
        raise ValueError('Display indices outside source prefix')
    rows = bars[first:last + 1]
    for row in rows:
        if row['low'] is None or row['high'] is None:
            raise ValueError('Missing source wick; no invented price envelope')
        if decimal(row['low']) > decimal(row['high']):
            raise ValueError('Reversed source wick')
    low = min(rows, key=lambda r: decimal(r['low']))['low']
    high = max(rows, key=lambda r: decimal(r['high']))['high']
    known = [r for r in rows if r['volume_shares_scaled'] is not None]
    if any(decimal(r['volume_shares_scaled']) < 0 for r in known):
        raise ValueError('Negative source volume')
    known_max = max(known, key=lambda r: decimal(r['volume_shares_scaled']))['volume_shares_scaled'] if known else None
    missing = [r['date'] for r in rows if r['volume_shares_scaled'] is None]
    maximum = None if missing else known_max
    return dict(schema_version=VERSION,
        qualification='SELECTED_SOURCE_CANDLE_ENVELOPE_DISPLAY_ONLY_NOT_FORMAL_PRESSURE_BOUNDS',
        first_index=first, last_index=last, first_source_date=rows[0]['date'], last_source_date=rows[-1]['date'],
        included_source_bars=len(rows), selected_source_rows_fingerprint=fingerprint(rows),
        uncertain_start_month=uncertain_start_month,
        left_edge='OPEN_UNCERTAIN_MONTH_ANCHOR' if uncertain_start_month else 'EXACT_INCLUDED_SOURCE_DAY',
        formal_price_bounds=None, formal_volume_measure=None, formal_bar_membership=None,
        price=dict(low=low, high=high,
            low_dates=[r['date'] for r in rows if decimal(r['low']) == decimal(low)],
            high_dates=[r['date'] for r in rows if decimal(r['high']) == decimal(high)],
            basis='FULL_SELECTED_SOURCE_WICKS_NOT_VISIBLE_SUBWINDOW', axis_effect='NONE'),
        volume=dict(max_volume_shares_scaled=maximum, known_max_volume_shares_scaled=known_max,
            known_max_dates=[r['date'] for r in known if decimal(r['volume_shares_scaled']) == decimal(known_max)],
            known_records=len(known), missing_dates=missing,
            true_zero_dates=[r['date'] for r in known if decimal(r['volume_shares_scaled']) == 0],
            completeness='MISSING_NO_ENVELOPE' if missing else 'COMPLETE_SOURCE_ROWS',
            qualification='DISPLAY_HIGHEST_SOURCE_COLUMN_NOT_REGION_TOTAL_OR_STRATEGY_MAXIMUM'))


def prepare(series, frame, layer):
    if layer is None:
        return None
    if (layer['code'], layer['price_mode'], layer['source_id'], layer['frame_id'], layer['chart_base'], layer['analysis_as_of']) != (
            series['code'], series['price_mode'], series['source']['id'], frame['frame_id'], frame['chart_base'], frame['as_of']):
        raise ValueError('Display extent binding mismatch')
    bars = series['bases'][frame['chart_base']]['bars'][:frame['index'] + 1]
    if fingerprint(bars) != layer['data_prefix_fingerprint']:
        raise ValueError('Display source prefix fingerprint mismatch')
    g1, g2 = (next(r for r in layer['regions'] if r['id'] == key) for key in ('G1', 'G2'))
    if g1['exact_start_date'] is not None or any(r['price_bounds'] is not None for r in (g1, g2)):
        raise ValueError('Formal unknowns must not become display geometry')
    a, b = g2['display']['start_index'], g2['display']['end_index']
    if bars[a]['date'] != g2['exact_start_date'] or bars[b]['date'] != g2['exact_end_date']:
        raise ValueError('Display dates differ from exact reviewed G2 endpoints')
    return dict(schema_version='manual-candle-region-display-layer/0.1',
        source_id=layer['source_id'], frame_id=layer['frame_id'], chart_base=layer['chart_base'],
        analysis_as_of=layer['analysis_as_of'], review_sources=layer['review_sources'],
        extents=dict(G1=envelope(bars,g1['display']['month_first_index'],g1['display']['c_index'],
                                 uncertain_start_month=g1['approximate_start_month']),
                     G2=envelope(bars,a,b)),
        c_right_extent=None, c_right_qualification='OPEN_REFERENCE_ONLY_NO_CLOSED_REGION',
        formal_price_bounds=None, total_volume=None,
        classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED')
