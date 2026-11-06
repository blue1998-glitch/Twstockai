"""Causal context from saved daily evidence; no UI, network, scoring or trading.

All interpretive links are independently versioned candidates. Unknown lifecycle,
pattern and ownership claims remain distinct from measurable observations.
"""
from copy import deepcopy
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from contracts import fingerprint

VERSION = 'product-context-candidate/0.1'


def D(value):
    number = Decimal(str(value).replace(',', ''))
    if not number.is_finite():
        raise ValueError('Finite evidence required')
    return number


def relation(a, b):
    if a is None or b is None:
        return 'UNKNOWN'
    return 'HIGHER' if D(a) > D(b) else 'LOWER' if D(a) < D(b) else 'EQUAL'


def mean(values):
    if not values or any(value is None for value in values):
        return None
    with localcontext() as ctx:
        ctx.prec = 50
        return str(sum(map(D, values)) / len(values))


def _activity(rows):
    volume = [row.get('volume_shares_scaled') for row in rows]
    ranges = [str((D(row['high']) - D(row['low'])) / D(row['close'])) for row in rows]
    output = {}
    for window in (5, 20):
        output['volume_mean_' + str(window)] = mean(volume[-window:]) if len(volume) >= window else None
        output['relative_range_mean_' + str(window)] = mean(ranges[-window:]) if len(ranges) >= window else None
    previous = mean(volume[-21:-1]) if len(volume) >= 21 else None
    output['volume_vs_previous20'] = (None if previous is None or D(previous) == 0 or volume[-1] is None
                                      else str(D(volume[-1]) / D(previous)))
    output['volume_5_vs_20'] = relation(output['volume_mean_5'], output['volume_mean_20'])
    output['range_5_vs_20'] = relation(output['relative_range_mean_5'], output['relative_range_mean_20'])
    output['ownership_claim'] = 'UNKNOWN_NO_HOLDER_OR_BROKER_DATA'
    return output


def activity(rows):
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        return _activity(rows)


def background_evidence(period, daily):
    """Use exact already-aligned period output; no nearest-date substitution."""
    if period is None:
        return dict(status='NOT_SAVED_AT_THIS_AS_OF', weekly=None, monthly=None, conflicts=[])
    if period.get('alignment_status') != 'ALIGNED_INPUTS':
        return dict(status='CONFLICT', weekly=None, monthly=None, conflicts=['SAVED_INPUT_ALIGNMENT_CONFLICT'])
    result = dict(status='EXACT_SAVED_BACKGROUND', weekly=[], monthly=[], conflicts=[],
                  analysis_id=period['analysis_id'], record_fingerprint=period['record_fingerprint'])
    for tf in ('weekly', 'monthly'):
        block = period['snapshot'][tf]
        # Preserve both period bases as separate observations.
        for basis in ('elapsed', 'candidate'):
            for length in block['periods']:
                curve = block[basis]['curves'][str(length)]
                direction = relation(curve[-1], curve[-2]) if len(curve) >= 2 else 'UNKNOWN'
                result[tf].append(dict(period=length, basis=basis, direction=direction,
                                       latest=deepcopy(block[basis]['latest'][str(length)])))
                if basis == 'elapsed' and daily == 'HIGHER' and direction == 'LOWER':
                    result['conflicts'].append(tf + ':' + str(length) + ':DAILY_UP_VS_PERIOD_DOWN')
                if basis == 'elapsed' and daily == 'LOWER' and direction == 'HIGHER':
                    result['conflicts'].append(tf + ':' + str(length) + ':DAILY_DOWN_VS_PERIOD_UP')
    return result


def _frame_context(request, snapshot, ma, projected, indicator, *, previous=None, period=None, prior_indicator=None):
    as_of = snapshot['as_of']
    if previous and (previous['as_of'] >= as_of or previous['code'] != request['code'] or
                     previous['price_mode'] != request['price_mode'] or previous['source_id'] != request['source']['id']):
        raise ValueError('Previous frame must be an earlier observation of the same source and mode')
    if not projected or projected[-1]['date'] != as_of or ma['as_of'] != as_of:
        raise ValueError('Exact same-day evidence required')
    if snapshot['adjustment_anchor'] != as_of or snapshot['price_mode'] != request['price_mode']:
        raise ValueError('Price anchor/mode mismatch')
    if any(p['confirmed_at'] > as_of or p['occurred_at'] > p['confirmed_at'] for p in snapshot['pivots']):
        raise ValueError('Future or reversed pivot confirmation')
    effective = [e for e in request['corporate_actions']['records'] if e['effective_date'] <= as_of]
    boundary = (max((e['effective_date'] for e in effective), default=request['candles'][0]['date'])
                if request['price_mode'] == 'RAW_CANDIDATE' else request['candles'][0]['date'])
    pivots = [p for p in snapshot['pivots'] if p['confirmed_at'] >= boundary]
    primary = [p for p in pivots if p['profile'] == 'major']
    highs = [p for p in primary if p['kind'] == 'HIGH']
    lows = [p for p in primary if p['kind'] == 'LOW']
    high_relation = relation(highs[-1]['price'], highs[-2]['price']) if len(highs) >= 2 else 'UNKNOWN'
    low_relation = relation(lows[-1]['price'], lows[-2]['price']) if len(lows) >= 2 else 'UNKNOWN'
    structure_id = fingerprint(dict(producer=VERSION, code=request['code'], exchange=request['exchange'],
                                    mode=request['price_mode'], source=request['source']['id'], episode_start=boundary))
    legs = []
    for profile in ('major', 'minor'):
        points = sorted((p for p in pivots if p['profile'] == profile), key=lambda p: (p['occurred_at'], p['confirmed_at']))
        for a, b in zip(points, points[1:]):
            ambiguous = a['occurred_at'] == b['occurred_at'] or a['kind'] == b['kind']
            legs.append(dict(swing_id=fingerprint(dict(structure=structure_id, start=a['id'], end=b['id'])),
                             profile=profile, start_id=a['id'], end_id=b['id'],
                             start_date=a['occurred_at'], end_date=b['occurred_at'],
                             first_observed_at=max(a['first_observed_at'], b['first_observed_at']),
                             confirmed_at=max(a['confirmed_at'], b['confirmed_at']),
                             start_price=a['price'], end_price=b['price'],
                             price_change=None if ambiguous else str(D(b['price']) - D(a['price'])),
                             relation='AMBIGUOUS_NO_INTRADAY_ORDER' if ambiguous else relation(b['price'], a['price'])))
    close = projected[-1]['close']
    zones = []
    pivot_ids = {p['id'] for p in pivots}
    pivot_map = {p['id']: p for p in pivots}
    for z in snapshot['zones']:
        if z['pivot_id'] not in pivot_ids:
            continue
        location = 'ABOVE' if D(close) > D(z['high']) else 'BELOW' if D(close) < D(z['low']) else 'INSIDE'
        challenged = location == ('BELOW' if z['role'] == 'SUPPORT_CANDIDATE' else 'ABOVE')
        condition = ('INVALIDATED' if z['state'] == 'BREACHED_CANDIDATE' else
                     'STOPPED' if z['state'] != 'ACTIVE_CANDIDATE' else 'CHALLENGED' if challenged else 'NOT_BREACHED')
        zones.append({key: deepcopy(z[key]) for key in ('id', 'pivot_id', 'profile', 'role', 'low', 'high',
                     'created_at', 'invalidated_at', 'state', 'touch_episodes', 'outside_streak')} |
                     dict(structure_id=structure_id, current_location=location, condition=condition,
                          occurred_at=pivot_map[z['pivot_id']]['occurred_at'],
                          first_observed_at=pivot_map[z['pivot_id']]['first_observed_at'],
                          confirmed_at=pivot_map[z['pivot_id']]['confirmed_at'],
                          invalidation_rule=z['invalidation_rule'], formation_reason=z['formation_basis'],
                          evidence_as_of=as_of, relevance_basis=['SAVED_' + z['profile'].upper() + '_PIVOT',
                          'LINKED_TO_THIS_STRUCTURE_EPISODE', 'STATE_AND_CURRENT_CLOSE_REPORTED_SEPARATELY']))
    low_zone = next((z for z in zones if lows and z['pivot_id'] == lows[-1]['id']), None)
    support_condition = low_zone['condition'] if low_zone else 'UNKNOWN'
    up = high_relation == low_relation == 'HIGHER'
    down = high_relation == low_relation == 'LOWER'
    state = ('PRIMARY_LOW_REFERENCE_BREACHED' if support_condition == 'INVALIDATED' else
             'PRIMARY_LOW_REFERENCE_CHALLENGED' if support_condition == 'CHALLENGED' else
             'RISING_SWINGS_REFERENCE_INTACT' if up and support_condition == 'NOT_BREACHED' else
             'FALLING_SWING_RELATION' if down else 'MIXED_SWING_EVIDENCE' if primary else 'UNKNOWN')
    ma_evidence = []
    for length, curve in ma['curves'].items():
        ma_evidence.append(dict(period=int(length), value=curve[-1],
                                direction=relation(curve[-1], curve[-2]) if len(curve) > 1 else 'UNKNOWN',
                                close_relation=relation(close, curve[-1])))
    hist = indicator['histogram']
    same_anchor = previous and previous['effective_events_fingerprint'] == snapshot['effective_events_fingerprint']
    prior_hist = (prior_indicator['histogram'] if prior_indicator is not None else
                  previous['momentum']['histogram'] if same_anchor and previous['structure_id'] == structure_id else None)
    momentum = dict(indicator, histogram_change=relation(hist, prior_hist),
                    previous_histogram_same_anchor=prior_hist,
                    comparison_basis='SELECTED_AS_OF_PRICE_ANCHOR_NOT_PREVIOUS_FRAME_ANCHOR',
                    interpretation='OBJECTIVE_INDICATOR_CHANGE_NOT_STRUCTURE_OR_TRADE_APPROVAL')
    daily_direction = next((r['direction'] for r in ma_evidence if r['period'] == 20), 'UNKNOWN')
    background = background_evidence(period, daily_direction)
    supporting, opposing, missing = [], [], ['LIFECYCLE_OPERATIONAL_RULES_UNDEFINED',
        'THREE_FORMAL_PATTERN_RULES_UNDEFINED', 'HOLDER_AND_BROKER_DATA_UNAVAILABLE',
        'FULL_STOCK_LIFECYCLE_NOT_COVERED', 'INTRADAY_EVENTS_UNAVAILABLE']
    missing.extend(['OFFICIAL_CALENDAR_NOT_AUTHENTICATED', 'COMPLETE_ACTIONS_AND_PUBLICATION_TIMING_UNVERIFIED'])
    if len(projected) < 20:
        missing.append('ACTIVITY_FULL_WINDOW_NOT_READY')
    if any(row.get('volume_shares_scaled') is None for row in projected[-20:]):
        missing.append('VOLUME_GAPS_IN_LAST20')
    if up:
        supporting.append(dict(code='HIGHER_CONFIRMED_HIGHS_AND_LOWS', references=[p['id'] for p in (highs[-2:] + lows[-2:])]))
    if low_zone:
        (supporting if support_condition == 'NOT_BREACHED' else opposing).append(
            dict(code='PRIMARY_LOW_REFERENCE_' + support_condition, references=[low_zone['id']],
                 reason=low_zone['invalidation_rule']))
    else:
        missing.append('NO_CONFIRMED_MAJOR_LOW_REFERENCE_IN_CURRENT_EPISODE')
    if hist is None:
        missing.append('MACD_FULL_WINDOW_NOT_READY')
    elif D(hist) > 0 and momentum['histogram_change'] == 'LOWER':
        opposing.append(dict(code='POSITIVE_MACD_HISTOGRAM_DECREASING', references=['macd:' + as_of],
                             reason='Momentum observation does not itself invalidate the primary support'))
    for row in ma_evidence:
        if row['direction'] == 'LOWER':
            opposing.append(dict(code='FALLING_DAILY_MA', references=['daily_ma:' + str(row['period'])],
                                 reason='Moving-average risk is not cancelled by positive structure evidence'))
    for z in zones:
        if (z['profile'] == 'major' and z['role'] == 'RESISTANCE_CANDIDATE' and
                z['state'] == 'BREACHED_CANDIDATE' and z['current_location'] in ('BELOW', 'INSIDE')):
            opposing.append(dict(code='RETURNED_INTO_OR_BELOW_PREVIOUSLY_BREACHED_RESISTANCE', references=[z['id']],
                                 reason='Observable re-entry; formal false-breakout classification remains undefined; no automatic role swap'))
    if background['status'] != 'EXACT_SAVED_BACKGROUND':
        missing.append('NO_ALIGNED_SAVED_PERIOD_BACKGROUND_ON_EXACT_DATE')
    opposing.extend(dict(code='TIMEFRAME_CONFLICT', references=[s]) for s in background['conflicts'])
    changes = []
    if previous:
        if state != previous['structure']['candidate_state'] or structure_id != previous['structure_id']:
            changes.append(dict(kind='STRUCTURE_CONTEXT_CHANGED', previous=previous['structure']['candidate_state'],
                                current=state, reason='NEW_SAVED_PIVOT_ZONE_OR_RAW_ACTION_EVIDENCE',
                                source_snapshot=snapshot['snapshot_id']))
        old = {z['id']: z for z in previous['zones']}
        for z in zones:
            if z['id'] not in old or (z['state'], z['condition'], z['touch_episodes']) != (
                    old[z['id']]['state'], old[z['id']]['condition'], old[z['id']]['touch_episodes']):
                changes.append(dict(kind='ZONE_EVIDENCE_CHANGED', zone_id=z['id'], previous=None if z['id'] not in old else
                                    old[z['id']]['condition'], current=z['condition'], state=z['state'],
                                    reason='SAVED_STATE_CONTACT_OR_CURRENT_CLOSE_CHANGED'))
    result = dict(schema_version='product-context-candidate/0.1', producer_version=VERSION,
                  as_of=as_of, code=request['code'], exchange=request['exchange'], price_mode=request['price_mode'],
                  source_id=request['source']['id'], structure_id=structure_id,
                  previous_frame_id=previous['frame_id'] if previous else None,
                  previous_structure_id=previous['structure_id'] if previous else None,
                  structure_snapshot_id=snapshot['snapshot_id'], ma_snapshot_id=ma['snapshot_id'],
                  data_fingerprint=snapshot['data_fingerprint'], effective_events_fingerprint=snapshot['effective_events_fingerprint'],
                  close=close, data_start=projected[0]['date'], daily_records=len(projected),
                  structure=dict(candidate_state=state, high_relation=high_relation, low_relation=low_relation,
                    primary_low_condition=support_condition, primary_low_zone_id=low_zone['id'] if low_zone else None,
                    scope='LATEST_CONFIRMED_LOW_IS_A_REFERENCE_NOT_A_VALIDATED_IMPORTANCE_RANKING'),
                  legs=legs, zones=zones, pending=deepcopy(snapshot.get('pending', [])),
                  source_evidence_sufficiency=snapshot.get('evidence_sufficiency', 'UNKNOWN'),
                  moving_averages=ma_evidence, momentum=momentum,
                  activity=activity(projected), background=background,
                  lifecycle=dict(stage='UNKNOWN', reason='OPERATIONAL_STAGE_CONDITIONS_UNDEFINED'),
                  correction=dict(state='UNKNOWN', observations=dict(high_relation=high_relation,
                                  primary_low_condition=support_condition), reason='FORMAL_CORRECTION_CONDITIONS_UNDEFINED'),
                  pattern='UNKNOWN_FORMAL_RULES_UNDEFINED', intraday='INTRADAY_NOT_EVALUABLE',
                  supporting=supporting, opposing=opposing, missing=missing, changes=changes,
                  daily_events=deepcopy(snapshot['daily_events']), classification_quality='NOT_VALIDATED',
                  action_qualification='NOT_EVALUATED')
    changed_ids = {c['zone_id'] for c in changes if 'zone_id' in c}
    result['main_zone_ids'] = [z['id'] for z in zones if z['profile'] == 'major' and (
        z['state'] == 'ACTIVE_CANDIDATE' or z['id'] == result['structure']['primary_low_zone_id'] or z['id'] in changed_ids)]
    result['reference_group_rule'] = 'MAJOR_AND_ACTIVE_OR_PRIMARY_LOW_OR_CHANGED_TODAY_NOT_IMPORTANCE_RANK'
    result['frame_id'] = fingerprint(result)
    return result


def frame_context(*args, **kwargs):
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        return _frame_context(*args, **kwargs)
