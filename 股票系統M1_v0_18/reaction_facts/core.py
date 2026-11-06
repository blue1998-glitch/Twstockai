"""Pure exact-string daily observations. No I/O, manual audit, or analysis calls."""
from copy import deepcopy
from datetime import date, datetime
from decimal import localcontext, ROUND_HALF_EVEN

from graph_core.core import number, ratio, fingerprint

VERSION = 'multi-reference-reaction-facts/0.1'
BINDING = ('code', 'source_id', 'price_basis_id', 'source_frame_id', 'source_prefix_fingerprint')
PRICES = ('open', 'high', 'low', 'close')
FIELDS = ('close', 'high', 'low')


def day(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError('Canonical date required')
    return value


def timestamp(value):
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError('Selection timestamp requires timezone')
    return parsed.isoformat()


def compare(value, reference, reason='MISSING_PRICE'):
    if value is None or reference is None:
        return dict(relation=None, delta=None, reason=reason)
    a, b = number(value), number(reference)
    # Exact subtraction even for very long strings or almost equal values.
    precision = max(a.adjusted(), b.adjusted(), 0) - min(a.as_tuple().exponent, b.as_tuple().exponent, 0) + 3
    with localcontext() as ctx:
        ctx.prec = precision
        delta = format(a - b, 'f')
    return dict(relation='ABOVE' if a > b else 'BELOW' if a < b else 'EQUAL', delta=delta, reason='AVAILABLE')


def _validate(payload, as_of):
    if payload.get('schema_version') != 'reaction-facts-input/0.1':
        raise ValueError('Unsupported fact input')
    day(as_of)
    c = payload['context']
    if any(not isinstance(c.get(k), str) or not c[k] for k in BINDING):
        raise ValueError('Explicit code/source/basis/frame/prefix binding required')
    if c.get('volume_unit') != 'SHARES_REPORTED':
        raise ValueError('Original reported shares required')
    bars, macd = payload['bars'], payload['macd']
    if len(bars) != len(macd):
        raise ValueError('Saved ordinal MACD axis differs')
    if fingerprint(bars) != c['source_prefix_fingerprint']:
        raise ValueError('Input source prefix differs')
    if any(a['date'] >= b['date'] for a, b in zip(bars, bars[1:])):
        raise ValueError('Unique increasing dates required; never sort/deduplicate silently')
    for row, indicator in zip(bars, macd):
        day(row['date'])
        if row.get('complete', True) is not True:
            raise ValueError('Incomplete daily bar refused')
        if row.get('price_basis_id', c['price_basis_id']) != c['price_basis_id']:
            raise ValueError('Mixed row basis refused; use explicit break dates')
        if day(row.get('known_on', row['date'])) < row['date']:
            raise ValueError('Bar cannot be known before its source day')
        for key in (*PRICES, 'volume_shares_scaled'):
            if key not in row:
                raise ValueError('Missing source key; explicit null required')
            if row[key] is not None and number(row[key]) < 0:
                raise ValueError('Negative price or volume')
            if key in PRICES and row[key] is not None and number(row[key]) == 0:
                raise ValueError('Zero source price')
        if row['high'] is not None and row['low'] is not None and number(row['high']) < number(row['low']):
            raise ValueError('Contradictory partial high/low')
        for key in ('open', 'close'):
            if row[key] is not None and ((row['low'] is not None and number(row[key]) < number(row['low'])) or
                                         (row['high'] is not None and number(row[key]) > number(row['high']))):
                raise ValueError('Contradictory partial OHLC')
        if all(row[k] is not None for k in PRICES):
            o, h, l, cl = (number(row[k]) for k in PRICES)
            if min(o, h, l, cl) <= 0 or not l <= min(o, cl) <= max(o, cl) <= h:
                raise ValueError('Contradictory OHLC')
        if indicator is not None:
            if indicator.get('date', row['date']) != row['date']:
                raise ValueError('Saved MACD date differs')
            for key in ('dif', 'dea', 'histogram'):
                if indicator.get(key) is not None:
                    number(indicator[key])
    for key in ('known_gap_dates', 'basis_break_dates'):
        for d in payload.get(key, []):
            day(d)
    selected = [i for i, row in enumerate(bars) if row['date'] <= as_of]
    if not selected or bars[selected[-1]]['date'] != as_of:
        raise ValueError('Exact saved as_of required')
    refs = payload['references']
    by_date = {row['date']: row for row in bars}
    if len({r['id'] for r in refs}) != len(refs):
        raise ValueError('Distinct reference IDs required even for the same price')
    for r in refs:
        if not isinstance(r['id'], str) or not r['id']:
            raise ValueError('Stable reference ID required')
        if any(r['binding'].get(k) != c[k] for k in BINDING):
            raise ValueError('Reference source/basis/frame/prefix/code mismatch')
        number(r['price'])
        day(r['occurred_at']); day(r['known_on'])
        if r['known_on'] < r['occurred_at']:
            raise ValueError('Reference cannot be known before occurrence')
        timestamp(r['selected_at'])
        if r['qualification'] not in ('EXPLICIT_RESEARCH_QUERY', 'CONFIRMED_RESEARCH_BOUND'):
            raise ValueError('Unsupported reference qualification')
        if r.get('historical_signal_eligible') is True:
            raise ValueError('This layer cannot authenticate historical selection/signals')
        if not r.get('origin_id') or not r.get('source_field'):
            raise ValueError('Reference evidence identity/field required')
        if r['qualification'] == 'EXPLICIT_RESEARCH_QUERY':
            if r.get('source_kind') != 'BAR_FIELD':
                raise ValueError('Reference source kind differs')
            source = by_date.get(r['occurred_at'])
            if source is None:
                if r['known_on'] <= as_of:
                    raise ValueError('Available reference source bar missing')
            elif (r['source_field'] not in PRICES or fingerprint(source) != r['origin_id'] or
                  source[r['source_field']] != r['price'] or
                  source.get('known_on', source['date']) != r['known_on']):
                raise ValueError('Reference does not match original bar field/availability')
        else:
            if r.get('source_kind') != 'RESEARCH_BOUND':
                raise ValueError('Reference source kind differs')
            evidence = payload.get('research_reference_evidence', {}).get(r['origin_id'])
            if (not evidence or r['source_field'] not in ('high', 'low') or
                evidence['confirmed_at'] != r['known_on'] or evidence['source_end'] != r['occurred_at'] or
                evidence['research_bounds'][r['source_field']] != r['price']):
                raise ValueError('Reference does not match confirmed research evidence')
    return bars[:selected[-1] + 1], macd[:selected[-1] + 1]


def evaluate(payload, *, as_of):
    """Observe an explicit prefix. Later selection is always research, never a signal."""
    rows, indicators = _validate(payload, as_of)
    refs = payload['references']; gaps = set(payload.get('known_gap_dates', []))
    breaks = set(payload.get('basis_break_dates', []))
    records = []; transitions = []; prior_positions = {}; latest_break = None
    for i, (row, macd) in enumerate(zip(rows, indicators)):
        d = row['date']; previous = rows[i - 1] if i else None
        crossed_gaps = sorted(g for g in gaps if previous and previous['date'] < g <= d)
        crossed_breaks = sorted(g for g in breaks if (previous['date'] if previous else '') < g <= d)
        if crossed_breaks:
            latest_break = crossed_breaks[-1]
        discontinuity = ('BASIS_INTERRUPTION' if crossed_breaks else
                         'KNOWN_UNVERIFIED_CALENDAR_GAP' if crossed_gaps else None)
        current_known = row.get('known_on', d) <= d
        previous_known = previous and previous.get('known_on', previous['date']) <= d
        adjacency_reason = ('NO_PREVIOUS_SAVED_RECORD' if not previous else discontinuity or
                            ('SOURCE_NOT_KNOWN_ON_RECORD_DATE' if not current_known or not previous_known else None))
        def adjacent(key, previous_key=None):
            return compare(row[key] if not adjacency_reason else None,
                           previous[previous_key or key] if previous else None,
                           adjacency_reason or 'MISSING_ADJACENT_PRICE')
        high, low = adjacent('high'), adjacent('low')
        sides = (high['relation'], low['relation'])
        range_direction = (None if None in sides else 'BOTH_ENDS_UP' if sides == ('ABOVE', 'ABOVE') else
                           'BOTH_ENDS_DOWN' if sides == ('BELOW', 'BELOW') else
                           'BOTH_EQUAL' if sides == ('EQUAL', 'EQUAL') else 'MIXED_OR_ONE_EQUAL')
        geometry = None
        if not adjacency_reason and all(r[k] is not None for r in (row, previous) for k in ('high', 'low')):
            h, l, ph, pl = (number(v) for v in (row['high'], row['low'], previous['high'], previous['low']))
            geometry = ('ENTIRELY_ABOVE' if l > ph else 'ENTIRELY_BELOW' if h < pl else
                        'TOUCHING' if l == ph or h == pl else 'OVERLAPPING')
        num = row['volume_shares_scaled']; denom = previous['volume_shares_scaled'] if previous else None
        volume_reason = adjacency_reason or ('MISSING_CURRENT_VOLUME' if num is None else
                                             'MISSING_PREVIOUS_VOLUME' if denom is None else
                                             'ZERO_DENOMINATOR' if number(denom) == 0 else 'AVAILABLE')
        with localcontext() as ctx:
            ctx.rounding = ROUND_HALF_EVEN
            volume_ratio = ratio(number(num), number(denom)) if volume_reason == 'AVAILABLE' else None
        volume = dict(current_shares=num, previous_shares=denom,
                      numerator_date=d, denominator_dates=[previous['date']] if previous else [],
                      baseline_includes_current=False, reason=volume_reason,
                      ratio=volume_ratio,
                      ratio_precision='50_SIGNIFICANT_DECIMAL_DIGITS_HALF_EVEN_ORIGINAL_NUMERATOR_DENOMINATOR_RETAINED',
                      qualification='PREVIOUS_SAVED_RECORD_DESCRIPTION_NOT_VOLUME_SIGNAL')
        macd_observation = dict(original=deepcopy(macd),
                                reason='MISSING_MACD' if macd is None else macd.get('reason', 'UNSPECIFIED_SAVED_REASON'),
                                field_observations={})
        for key in ('dif', 'dea', 'histogram'):
            v = macd.get(key) if macd and current_known else None
            pv = indicators[i - 1].get(key) if i and indicators[i - 1] else None
            macd_observation['field_observations'][key] = dict(
                value=v, reason='SOURCE_NOT_KNOWN_ON_RECORD_DATE' if not current_known else 'AVAILABLE' if v is not None else 'MISSING_SAVED_FIELD',
                sign=compare(v, '0', 'SOURCE_NOT_KNOWN_ON_RECORD_DATE' if not current_known else 'MISSING_SAVED_FIELD'),
                versus_previous=compare(v if not adjacency_reason else None, pv,
                                        adjacency_reason or 'MISSING_ADJACENT_MACD'))
        positions = {}
        for r in refs:
            reason = ('REFERENCE_NOT_YET_KNOWN' if d < r['known_on'] else
                      'REFERENCE_BEFORE_BASIS_INTERRUPTION' if latest_break and (r['known_on'] < latest_break or r['occurred_at'] < latest_break) else
                      'SOURCE_NOT_KNOWN_ON_RECORD_DATE' if not current_known else None)
            per_field = {}
            for key in FIELDS:
                fact = compare(row[key] if not reason else None, r['price'], reason or 'MISSING_PRICE')
                token = (r['id'], key); prior = prior_positions.get(token)
                if fact['relation'] is None:
                    change = dict(kind='NOT_AVAILABLE', previous_date=prior[0] if prior else None,
                                  from_relation=prior[1] if prior else None, to_relation=None, reason=fact['reason'])
                    prior_positions.pop(token, None)
                elif discontinuity or prior is None:
                    change = dict(kind='SEGMENT_START', previous_date=None, from_relation=None,
                                  to_relation=fact['relation'], reason=discontinuity or 'NO_CONTIGUOUS_PRIOR_POSITION')
                    prior_positions[token] = (d, fact['relation'])
                else:
                    a, b = prior[1], fact['relation']
                    change = dict(kind='UNCHANGED' if a == b else a + '_TO_' + b,
                                  previous_date=prior[0], from_relation=a, to_relation=b, reason='AVAILABLE')
                    prior_positions[token] = (d, b)
                fact['transition'] = change
                per_field[key] = fact
                if change['kind'] not in ('UNCHANGED', 'NOT_AVAILABLE') or (change['kind'] == 'NOT_AVAILABLE' and change['from_relation'] is not None):
                    transitions.append(dict(reference_id=r['id'], field=key, date=d, **deepcopy(change)))
            positions[r['id']] = dict(status='NOT_AVAILABLE' if reason else 'SOURCE_VALUE_COMPARISON_ONLY',
                                       reason=reason, historical_signal_eligible=False, fields=per_field)
        records.append(dict(date=d, original_bar=deepcopy(row),
                            original_value_known_on=row.get('known_on', d),
                            intraday_sequence='UNKNOWN_FROM_DAILY_OHLC',
                            body=compare(row['close'] if current_known else None, row['open'], 'SOURCE_NOT_KNOWN_OR_MISSING_PRICE'),
                            adjacent=dict(previous_record_date=previous['date'] if previous else None,
                                          reason=adjacency_reason, close=adjacent('close'), high=high, low=low,
                                          range_direction=range_direction, range_geometry=geometry,
                                          qualification='ADJACENT_SAVED_RAW_RECORDS_NOT_CONFIRMED_SWINGS_OR_AUTHENTICATED_GAP'),
                            continuity=dict(reason=discontinuity, known_gap_dates=crossed_gaps, basis_break_dates=crossed_breaks),
                            volume=volume, macd=macd_observation, references=positions))
    catalog = []
    for r in refs:
        item = deepcopy(r)
        if r['known_on'] > as_of:
            item['price'] = None  # Never publish a future source price as prefix-eligible.
        item.update(historical_signal_eligible=False,
                    selection_qualification='LATER_EXPLICIT_RESEARCH_OR_SELECTION_UNVERIFIED_NOT_HISTORICAL_SIGNAL',
                    value_availability_at_as_of='AVAILABLE' if r['known_on'] <= as_of else 'NOT_AVAILABLE')
        catalog.append(item)
    result = dict(schema_version=VERSION, as_of=as_of, context=deepcopy(payload['context']),
                  evaluated_prefix_fingerprint=fingerprint(rows), reference_catalog=catalog,
                  records=records, transitions=transitions,
                  limits=deepcopy(payload.get('limits', {})),
                  primary_pressure_id=None, whole_pressure_clearance=None, effective_breakout=None,
                  lifecycle='UNKNOWN', core_usefulness='NOT_ESTABLISHED', classification_quality='NOT_VALIDATED',
                  action_qualification='NOT_EVALUATED', physical_android='NOT_TESTED_NEW_BUILD',
                  historical_publication_timing='UNVERIFIED', intraday_sequence='UNKNOWN_FROM_DAILY_OHLC')
    result['result_id'] = fingerprint(result)
    return result
