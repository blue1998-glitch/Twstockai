"""Opt-in, pure evidence replay for explicitly selected attempt references.

No UI, database, quote provider, automatic level selection or trade instruction.
Observations are supplied prefixes, never paths reconstructed from daily OHLC.
"""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json

VERSION = 'attempt-evidence-candidate/0.1'
INPUT_SCHEMA = 'attempt-evidence-input/0.1'
TAIPEI = timezone(timedelta(hours=8))


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name}: nonempty string required')
    return value


def _number(value, name, *, volume=False):
    if volume and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f'{name}: exact decimal string or integer required')
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError(f'{name}: invalid decimal') from None
    if not result.is_finite() or (result < 0 if volume else result <= 0):
        raise ValueError(f'{name}: finite valid value required')
    if volume and result != result.to_integral_value():
        raise ValueError(f'{name}: integer share count required')
    return result


def _day(value):
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError('ISO date required') from None
    if parsed.isoformat() != value:
        raise ValueError('Canonical ISO date required')
    return parsed


def _time(value):
    try:
        result = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError('Timezone-aware observed/known timestamp required') from None
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError('Timezone-aware timestamp required')
    return result


def _relation(value, reference):
    return 'ABOVE' if value > reference else 'BELOW' if value < reference else 'AT_LEVEL'


def _fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(',', ':')).encode()).hexdigest()


def _bar(row, basis_id, *, historical):
    if row.get('price_basis_id') != basis_id:
        raise ValueError('Mixed or missing price basis; explicit rebasing is required')
    day = _day(row['date'])
    stamp = _time(row['known_at' if historical else 'observed_at'])
    if stamp.astimezone(TAIPEI).date() < day:
        raise ValueError('Observation cannot precede its trading date')
    if not historical and stamp.astimezone(TAIPEI).date() != day:
        raise ValueError('Replay observation must belong to its Taipei date')
    final = True if historical else row.get('is_close')
    if type(final) is not bool:
        raise ValueError('Explicit is_close boolean required; clock time is not confirmation')
    values = {key: _number(row[key], key) for key in ('open', 'high', 'low')}
    values['last'] = _number(row['close' if historical else 'last'], 'last')
    if not (values['low'] <= min(values['open'], values['last']) <=
            max(values['open'], values['last']) <= values['high']):
        raise ValueError('Inconsistent supplied OHLC')
    return dict(values, date=day, time=stamp, is_close=final,
                volume=_number(row.get('volume_shares'), 'volume_shares', volume=True))


def evaluate(payload):
    """Return deterministic evidence frames without mutating input or writing files.

    See ATTEMPT_EVIDENCE.md for scope, explicit-reference input and unknowns.
    The price condition is one component, NOT overall trading qualification.
    """
    if payload.get('schema_version') != INPUT_SCHEMA:
        raise ValueError('Unsupported input schema')
    context = deepcopy(payload['context'])
    for key in ('series_id', 'source_id', 'price_basis_id'):
        _text(context.get(key), key)
    if context.get('volume_unit') != 'SHARES_REPORTED':
        raise ValueError('SHARES_REPORTED required; no implicit lot/share conversion')
    if context.get('price_mode') not in ('RAW_CANDIDATE', 'ADJUSTED_CANDIDATE'):
        raise ValueError('Explicit supported price mode required')
    if context['price_mode'] == 'ADJUSTED_CANDIDATE':
        _day(context.get('adjustment_anchor'))
    basis = context['price_basis_id']
    history = [_bar(row, basis, historical=True) for row in payload['history']]
    observations = [_bar(row, basis, historical=False) for row in payload['observations']]
    if not history or not observations:
        raise ValueError('Nonempty history and observation prefix required')
    if any(a['date'] >= b['date'] for a, b in zip(history, history[1:])):
        raise ValueError('Historical dates must be strictly increasing and unique')
    first = observations[0]
    if (context['price_mode'] == 'ADJUSTED_CANDIDATE' and
            _day(context['adjustment_anchor']) > first['date']):
        raise ValueError('Adjusted anchor cannot come from the future')
    if any(h['date'] >= first['date'] or h['time'] > first['time'] for h in history):
        raise ValueError('History must be already known before this observation episode')
    references = payload['references']
    reference_set = _text(references.get('id'), 'reference set id')
    known = _time(references['known_at'])
    if known > first['time']:
        raise ValueError('References were not known at first observation')
    near, left = references['near_high'], references['left_zone']
    near_price = _number(near['price'], 'near_high.price')
    left_low = _number(left['low'], 'left_zone.low')
    left_high = _number(left['high'], 'left_zone.high')
    if not near_price < left_low <= left_high:
        raise ValueError('This candidate requires near high < left low <= left high')
    by_date = {h['date'].isoformat(): h for h in history}
    if near.get('bar_date') not in by_date:
        raise ValueError('Near-high source bar must be supplied')
    source_high = by_date[near['bar_date']]
    if source_high['high'] != near_price or source_high['time'] > known:
        raise ValueError('Near-high reference must match its already-known bar high')
    zone_dates = left.get('bar_dates')
    if not isinstance(zone_dates, list) or not zone_dates or len(set(zone_dates)) != len(zone_dates):
        raise ValueError('Explicit unique left-zone source dates required')
    if any(day not in by_date for day in zone_dates):
        raise ValueError('Missing left-zone source bar; do not use a partial maximum')
    zone = [by_date[day] for day in zone_dates]
    if any(h['time'] > known or h['high'] < left_low or h['low'] > left_high for h in zone):
        raise ValueError('Left-zone bars must be known and intersect the selected price area')
    benchmark = None if any(h['volume'] is None for h in zone) else max(h['volume'] for h in zone)
    previous = None
    for current in observations:
        if previous:
            if current['time'] <= previous['time'] or current['date'] < previous['date']:
                raise ValueError('Observation prefix must be strictly time ordered')
            if current['date'] == previous['date']:
                if previous['is_close']:
                    raise ValueError('Closed daily observation cannot be updated in this replay')
                if (current['open'] != previous['open'] or current['high'] < previous['high'] or
                        current['low'] > previous['low']):
                    raise ValueError('Intraday OHLC must extend the same observed day')
                if (current['volume'] is not None and previous['volume'] is not None and
                        current['volume'] < previous['volume']):
                    raise ValueError('Cumulative share count decreased; revise as a new input version')
            elif not previous['is_close']:
                raise ValueError('Missing final daily observation before next day')
        previous = current

    levels = [('NEAR_HIGH', near_price), ('LEFT_ZONE_UPPER', left_high)]
    previous_close = history[-1]['last']
    close_relation = {name: _relation(previous_close, price) for name, price in levels}
    last_non_equal = {name: next((_relation(h['last'], price) for h in reversed(history)
                                 if h['last'] != price), 'AT_LEVEL') for name, price in levels}
    active_close = {name: last_non_equal[name] == 'ABOVE' for name, _ in levels}
    history_fingerprint = _fingerprint(dict(context=context, references=references,
                                            history=payload['history'], version=VERSION))
    zone_end = max(h['date'] for h in zone)
    price_previously_passed = any(h['high'] > left_high for h in history if h['date'] > zone_end)
    volume_days, lead_ids, events, frames = set(), [], [], []

    def event(kind, reference_id, row, index, **evidence):
        stamp = payload['observations'][index]['observed_at']
        identity = dict(frame_id=current_frame_id, kind=kind,
                        reference_id=reference_id, evidence=evidence)
        event_id = _fingerprint(identity)
        item = dict(id=event_id, kind=kind, reference_id=reference_id,
                    bar_date=row['date'].isoformat(), occurred_at=None,
                    first_observed_at=stamp,
                    confirmed_at=stamp if row['is_close'] else None,
                    observation_index=index, evidence=evidence)
        events.append(item)
        return event_id

    for index, row in enumerate(observations):
        previous_frame_id = frames[-1]['frame_id'] if frames else None
        current_frame_id = _fingerprint(dict(history_fingerprint=history_fingerprint,
                                            previous_frame_id=previous_frame_id,
                                            observation=payload['observations'][index]))
        added = []
        conditions = []
        for name, price in levels:
            relation = _relation(row['last'], price)
            if row['is_close']:
                if relation == 'ABOVE':
                    kind = 'CLOSE_STILL_ABOVE' if active_close[name] else 'CLOSE_CROSSED_ABOVE'
                    active_close[name] = True
                elif relation == 'BELOW':
                    kind = 'CLOSE_RETURNED_BELOW' if active_close[name] else 'CLOSE_BELOW_LEVEL'
                    active_close[name] = False
                else:
                    kind = 'CLOSE_AT_LEVEL'
                close_relation[name] = relation
                added.append(event(kind, name, row, index, price=format(row['last'], 'f'),
                                   reference_price=format(price, 'f')))
            elif relation != 'AT_LEVEL' and relation != last_non_equal[name]:
                kind = ('INTRADAY_CROSSED_ABOVE' if relation == 'ABOVE' else
                        'INTRADAY_RETURNED_BELOW' if last_non_equal[name] == 'ABOVE' else
                        'INTRADAY_BELOW_LEVEL')
                added.append(event(kind, name, row, index, price=format(row['last'], 'f'),
                                   reference_price=format(price, 'f')))
            if relation != 'AT_LEVEL':
                last_non_equal[name] = relation
            conditions.append(dict(reference_id=name, price=format(price, 'f'), relation=relation,
                                   price_attempt_condition='MET' if relation == 'ABOVE' else
                                   'AT_BOUNDARY' if relation == 'AT_LEVEL' else 'NOT_MET',
                                   latest_completed_close_relation=close_relation[name]))
        volume = row['volume']
        comparison = ('UNKNOWN' if volume is None or benchmark is None else
                      'HIGHER' if volume > benchmark else 'LOWER' if volume < benchmark else 'EQUAL')
        if comparison == 'HIGHER' and row['date'] not in volume_days:
            volume_days.add(row['date'])
            kind = ('VOLUME_EXCESS_PRICE_ALREADY_PASSED' if price_previously_passed else
                    'VOLUME_LEAD_OBSERVED' if row['high'] <= left_high else 'VOLUME_EXCESS_ORDER_UNKNOWN')
            volume_id = event(kind, 'LEFT_ZONE_VOLUME_MAX', row, index,
                              volume_shares=format(volume, 'f'),
                              benchmark_shares=format(benchmark, 'f'),
                              observed_high=format(row['high'], 'f'),
                              left_zone_upper=format(left_high, 'f'))
            added.append(volume_id)
            if kind == 'VOLUME_LEAD_OBSERVED':
                lead_ids.append(volume_id)
        price_previously_passed = price_previously_passed or row['high'] > left_high
        frames.append(dict(frame_id=current_frame_id, previous_frame_id=previous_frame_id,
                           source_observation=deepcopy(payload['observations'][index]),
                           observed_at=payload['observations'][index]['observed_at'],
                           bar_date=row['date'].isoformat(), is_close=row['is_close'],
                           current_price=format(row['last'], 'f'), attempt_levels=conditions,
                           volume_relation=comparison,
                           volume_shares=None if volume is None else format(volume, 'f'),
                           left_zone_max_volume_shares=None if benchmark is None else format(benchmark, 'f'),
                           volume_lead_evidence_ids=list(lead_ids), event_ids=added,
                           action_qualification='NOT_EVALUATED',
                           trend_strength='NOT_CLASSIFIED', probability_estimate=None))
    return dict(schema_version=VERSION, context=context, reference_set=deepcopy(references),
                source_history=deepcopy(payload['history']),
                history_fingerprint=history_fingerprint,
                reference_selection='EXPLICIT_CALLER_SELECTION_NOT_AUTO_RECOGNIZED',
                left_zone_max_volume_shares=None if benchmark is None else format(benchmark, 'f'),
                left_zone_volume_source_dates=list(zone_dates),
                evidence_scope='SUPPLIED_HISTORY_AND_OBSERVATION_PREFIX_ONLY',
                limitations=['REAL_MARKET_HISTORY_COVERAGE_NOT_AUTHENTICATED',
                             'CORPORATE_ACTION_AND_COMMON_BASIS_DECLARED_BY_CALLER_NOT_VERIFIED',
                             'NO_HOLDER_DATA_OR_CALIBRATED_SUCCESS_PROBABILITY',
                             'DAILY_OHLC_DOES_NOT_ESTABLISH_INTRADAY_ORDER',
                             'NO_AUTOMATIC_DEFENSE_RAISE_EXIT_OR_TREND_CLASSIFICATION'],
                classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED',
                frames=frames, events=events)


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Explicit-reference candidate evidence; no storage writes')
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(json.loads(args.input.read_text(encoding='utf-8'))),
                     ensure_ascii=False, indent=2))
