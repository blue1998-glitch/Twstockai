"""Deterministic research candidates. No UI, network, score or trading signal.
All numbers used in decisions are Decimal. Parameters are NOT validated strategy rules.
"""
from copy import deepcopy
from dataclasses import dataclass, asdict
from datetime import date
from decimal import Decimal
from contracts import SCHEMA_VERSION, DataError, fingerprint, validate_candles, validate_events, quality, validate_output

VERSION = 'structure-0.3-research'
VOLUME_PRECISION = {
    'SHARES_SCALED_FROM_LOTS': 'Source lots scaled to shares; display precision retained',
    'SHARES_REPORTED': 'Source reports shares directly; display precision retained; no lot scaling',
}


def volume_precision(unit):
    if not isinstance(unit, str) or unit not in VOLUME_PRECISION:
        raise DataError('UNSUPPORTED_UNIT', 'volume_unit', 'Explicit reported shares or source lots scaled to shares required')
    return VOLUME_PRECISION[unit]


def D(x):
    n = Decimal(str(x).replace(',', ''))
    if not n.is_finite():
        raise ValueError('Non-finite number')
    return n


@dataclass(frozen=True)
class Config:
    window: int = 20
    minor_multiple: str = '1.5'
    major_multiple: str = '3'
    minor_bars: int = 2
    major_bars: int = 3
    zone_half_width: str = '0.35'
    breach_bars: int = 2

    def validate(self):
        if any(not isinstance(x,int) or isinstance(x,bool) for x in (self.window,self.minor_bars,self.major_bars,self.breach_bars)):
            raise ValueError('Window and duration parameters must be integers')
        if self.window < 2 or min(self.minor_bars, self.major_bars, self.breach_bars) < 1:
            raise ValueError('Invalid window or confirmation duration')
        if min(D(self.minor_multiple), D(self.major_multiple), D(self.zone_half_width)) <= 0:
            raise ValueError('Invalid relative width')


def validate(candles):
    validate_candles(candles)


def serialize(x):
    if isinstance(x, Decimal):
        return str(x)
    if isinstance(x, dict):
        return {k: serialize(v) for k, v in x.items()}
    if isinstance(x, list):
        return [serialize(v) for v in x]
    return x


def project_prices(candles, events, as_of, mode):
    """Effective-date reconstruction, not certified historical publication timing."""
    if mode not in ('RAW_CANDIDATE', 'ADJUSTED_CANDIDATE'):
        raise ValueError('Explicit candidate price mode required')
    validate_events(events)
    result = []
    seen = set()
    for e in events:
        if e['effective_date'] in seen or D(e['factor']) <= 0:
            raise ValueError('Invalid or duplicate adjustment events')
        seen.add(e['effective_date'])
    for c in candles:
        if c['date'] > as_of:
            break
        row = dict(c)
        f = Decimal(1)
        if mode == 'ADJUSTED_CANDIDATE':
            for e in events:
                if c['date'] < e['effective_date'] <= as_of:
                    f *= D(e['factor'])
        for k in ('open', 'high', 'low', 'close'):
            row[k] = str(D(c[k]) * f)
        row['adjustment_factor'] = str(f)
        result.append(row)
    return result


def update_zone(z, candle, i, cfg):
    """Only call after zone creation. Contact counts distinct episodes, not days."""
    if z['state'] != 'ACTIVE_CANDIDATE' or i <= z['created_index']:
        return []
    dt, close, high, low = candle['date'], D(candle['close']), D(candle['high']), D(candle['low'])
    overlap = high >= z['low'] and low <= z['high']
    events = []
    if overlap and not z['was_touching']:
        z['touch_episodes'] += 1
        events.append(dict(type='ZONE_CONTACT', date=dt, zone_id=z['id'], touch_episodes=z['touch_episodes']))
    z['was_touching'] = overlap
    location = 'ABOVE' if close > z['high'] else 'BELOW' if close < z['low'] else 'INSIDE'
    if location != z['last_close_location']:
        events.append(dict(type='ZONE_CLOSE_LOCATION', date=dt, zone_id=z['id'], previous=z['last_close_location'], location=location))
    z['last_close_location'] = location
    outside = (z['role'] == 'SUPPORT_CANDIDATE' and location == 'BELOW') or (z['role'] == 'RESISTANCE_CANDIDATE' and location == 'ABOVE')
    z['outside_streak'] = z['outside_streak'] + 1 if outside else 0
    if z['outside_streak'] >= cfg.breach_bars:
        z['state'] = 'BREACHED_CANDIDATE'
        z['invalidated_at'] = dt
        events.append(dict(type='ZONE_BREACHED_CANDIDATE', date=dt, zone_id=z['id'],
                           evidence=dict(consecutive_closes=z['outside_streak'], close=close, low=z['low'], high=z['high'])))
    return events


def _run_prefix(candles, cfg, *, raw_boundaries=(), volume_unit=None):
    # Internal numeric fixtures may omit provenance; never guess lots vs shares.
    precision = volume_precision(volume_unit) if volume_unit is not None else 'Volume origin unspecified; share values retained without rescaling'
    cfg.validate()
    validate(candles)
    if not candles:
        return dict(pivots=[], zones=[], events=[], pending=[], warmup=True,zero_volatility=False,current_pivots_available=False)
    profiles = [('minor', D(cfg.minor_multiple), cfg.minor_bars), ('major', D(cfg.major_multiple), cfg.major_bars)]
    states = {name: dict(direction=None, pending={}) for name, _, _ in profiles}
    pivots, zones, ledger, tr, volumes = [], [], [], [], []
    start = 0
    previous_close = None
    candidate_sequence = 0

    def emit(kind, dt, **kw):
        ledger.append(deepcopy(dict(type=kind, date=dt, **kw)))

    def candidate(kind, idx, observed_i, atr, profile):
        nonlocal candidate_sequence
        candidate_sequence += 1
        c = candles[idx]
        return dict(id=f"{profile}:{kind}:{c['date']}:{candles[observed_i]['date']}:{candidate_sequence}", kind=kind, profile=profile,
                    occurred_at=c['date'], occurred_index=idx, first_observed_at=candles[observed_i]['date'],
                    price=D(c['high' if kind == 'HIGH' else 'low']), volatility_basis=atr,
                    basis_observed_at=candles[observed_i]['date'], status='PENDING',
                    invalidation='More extreme price before rule confirmation replaces this candidate')

    def replace(st, kind, i, atr, profile):
        old = st['pending'].get(kind)
        new = candidate(kind, i, i, atr, profile)
        if old:
            emit('CANDIDATE_REPLACED', candles[i]['date'], profile=profile, candidate_id=old['id'], replaced_by=new['id'],
                 previous_candidate=old)
        st['pending'][kind] = new
        emit('CANDIDATE_OBSERVED', candles[i]['date'], profile=profile, candidate=new)

    for i, c in enumerate(candles):
        dt = c['date']
        if dt in raw_boundaries:
            for z in zones:
                if z['state'] == 'ACTIVE_CANDIDATE':
                    z.update(state='INACTIVE_CORPORATE_ACTION', invalidated_at=dt)
            for name, st in states.items():
                for pending in st['pending'].values():
                    emit('CANDIDATE_CANCELLED_CORPORATE_ACTION', dt, profile=name, candidate_id=pending['id'])
                st.update(direction=None, pending={})
            start, tr, volumes, previous_close = i, [], [], None
            emit('RAW_CORPORATE_ACTION_BOUNDARY', dt, reason='Reset scale-sensitive candidates and zones; warm up again')
        h, l, close = D(c['high']), D(c['low']), D(c['close'])
        tr.append(max(h-l, abs(h-previous_close), abs(l-previous_close)) if previous_close is not None else h-l)
        previous_close = close
        volume = D(c['volume_shares_scaled']) if c.get('volume_shares_scaled') is not None else None
        volumes.append(volume)
        for z in zones:
            ledger.extend(deepcopy(update_zone(z, c, i, cfg)))
        if len(tr) < cfg.window:
            continue
        atr = sum(tr[-cfg.window:]) / Decimal(cfg.window)
        if atr <= 0:
            continue
        for profile, multiple, min_bars in profiles:
            st = states[profile]
            kinds = [st['direction']] if st['direction'] else ['HIGH', 'LOW']
            for kind in kinds:
                old = st['pending'].get(kind)
                price = h if kind == 'HIGH' else l
                if old is None or (price > old['price'] if kind == 'HIGH' else price < old['price']):
                    replace(st, kind, i, atr, profile)
            eligible = []
            for kind in kinds:
                p = st['pending'][kind]
                bars = i - p['occurred_index']
                reversal = p['price']-close if kind == 'HIGH' else close-p['price']
                if bars >= min_bars and reversal >= multiple*p['volatility_basis']:
                    eligible.append((kind, p, reversal, bars))
            if len(eligible) > 1:
                emit('AMBIGUOUS_BOTH_DIRECTIONS', dt, profile=profile,
                     candidate_ids=[x[1]['id'] for x in eligible])
                continue
            if not eligible:
                continue
            kind, p, reversal, bars = eligible[0]
            # Volume is supporting context only; no high-volume necessity is invented.
            prior_vol = volumes[-cfg.window-1:-1]
            vr = None
            if len(prior_vol) == cfg.window and volume is not None and all(v is not None for v in prior_vol):
                avg = sum(prior_vol) / Decimal(cfg.window)
                vr = volume / avg if avg > 0 else None
            previous_same = [x for x in pivots if x['profile'] == profile and x['kind'] == kind]
            relation = 'FIRST' if not previous_same else ('HIGHER' if p['price'] > previous_same[-1]['price'] else 'LOWER' if p['price'] < previous_same[-1]['price'] else 'EQUAL')
            pivot = deepcopy(p)
            pivot.update(status='RULE_CONFIRMED_CANDIDATE', confirmed_at=dt, confirmed_index=i,
                         evidence=dict(reversal=reversal, required_reversal=multiple*p['volatility_basis'],
                                       bars_after_extreme=bars, required_bars=min_bars, volume_ratio_20=vr,
                                       volume_precision=precision,
                                       relation_to_previous_same_kind=relation),
                         classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED')
            pivots.append(pivot)
            emit('PIVOT_RULE_CONFIRMED_CANDIDATE', dt, profile=profile, pivot=pivot)
            for rejected in st['pending'].values():
                if rejected['id'] != p['id']:
                    emit('BOOTSTRAP_OTHER_CANDIDATE_CANCELLED', dt, profile=profile, candidate_id=rejected['id'])
            half = D(cfg.zone_half_width)*p['volatility_basis']
            zone = dict(id='zone:'+p['id'], profile=profile, pivot_id=p['id'],
                        role='RESISTANCE_CANDIDATE' if kind == 'HIGH' else 'SUPPORT_CANDIDATE',
                        low=p['price']-half, high=p['price']+half, center=p['price'],
                        created_at=dt, created_index=i, state='ACTIVE_CANDIDATE', touch_episodes=0,
                        was_touching=False, last_close_location='NOT_OBSERVED', outside_streak=0,
                        invalidated_at=None, formation_basis='Rule-confirmed candidate pivot and volatility width',
                        invalidation_rule=f'{cfg.breach_bars} consecutive closes beyond the outer boundary')
            zones.append(zone)
            emit('ZONE_CREATED_CANDIDATE', dt, zone=zone)
            opposite = 'LOW' if kind == 'HIGH' else 'HIGH'
            # Do not assume the intraday order on the pivot's own day.
            available = list(range(max(p['occurred_index']+1, start), i+1))
            idx = min(available, key=lambda j:D(candles[j]['low'])) if opposite == 'LOW' else max(available, key=lambda j:D(candles[j]['high']))
            seed = candidate(opposite, idx, i, atr, profile)
            st.update(direction=opposite, pending={opposite:seed})
            emit('CANDIDATE_OBSERVED', dt, profile=profile, candidate=seed)
    return dict(pivots=pivots, zones=zones, events=ledger,
                pending=[deepcopy(p) for st in states.values() for p in st['pending'].values()],
                warmup=len(tr)<cfg.window, zero_volatility=len(tr)>=cfg.window and sum(tr[-cfg.window:])==0,
                current_pivots_available=any(p['confirmed_index']>=start for p in pivots))


def analyze(candles, events=(), *, code, mode, cfg=Config(), source_id, expected_dates=None, volume_unit=None):
    volume_precision(volume_unit)  # Public output requires explicit origin, even for empty input.
    validate(candles)
    validate_events(events)
    cfg.validate()
    if mode not in ('RAW_CANDIDATE','ADJUSTED_CANDIDATE'):raise DataError('INVALID_PRICE_MODE','mode','Explicit candidate mode required')
    if not code or not source_id:
        raise ValueError('Code and source identity required')
    snapshots, ledger = [], []
    parameters_fingerprint=fingerprint(asdict(cfg))
    full_quality=quality(candles,expected_dates=expected_dates)
    boundaries = {e['effective_date'] for e in events} if mode == 'RAW_CANDIDATE' else set()
    for i, c in enumerate(candles):
        prefix = project_prices(candles[:i+1], events, c['date'], mode)
        current = _run_prefix(prefix, cfg, raw_boundaries=boundaries, volume_unit=volume_unit)
        day_events = [e for e in current['events'] if e['date'] == c['date']]
        prefix_data_fingerprint=fingerprint(candles[:i+1])
        prefix_event_fingerprint=fingerprint([e for e in events if e['effective_date']<=c['date']])
        snapshot_id=fingerprint(dict(code=code,mode=mode,as_of=c['date'],rule_version=VERSION,
                                     parameters=parameters_fingerprint,data=prefix_data_fingerprint,events=prefix_event_fingerprint,
                                     volume_unit=volume_unit))
        for seq, e in enumerate(day_events):
            ledger.append(dict(event_id=f"{snapshot_id}:{seq}",snapshot_id=snapshot_id, code=code,
                               price_mode=mode, adjustment_anchor=c['date'], rule_version=VERSION, **e))
        snapshots.append(dict(as_of=c['date'], code=code, price_mode=mode, adjustment_anchor=c['date'],
                              source_id=source_id, volume_unit=volume_unit, rule_version=VERSION, parameters=asdict(cfg),schema_version=SCHEMA_VERSION,
                              snapshot_id=snapshot_id,data_fingerprint=prefix_data_fingerprint, parameters_fingerprint=parameters_fingerprint,
                              effective_events_fingerprint=prefix_event_fingerprint,
                              data_quality=quality(candles[:i+1],expected_dates=[dt for dt in expected_dates if dt<=c['date']] if expected_dates is not None else None),
                              event_status='WARMUP' if current['warmup'] else 'ZERO_VOLATILITY' if current['zero_volatility'] else 'EVENTS_PRESENT' if day_events else 'NO_NEW_EVENTS',
                              structure_status='RESEARCH_CANDIDATES_AVAILABLE' if not current['warmup'] and current.get('current_pivots_available') else 'UNKNOWN',
                              evidence_sufficiency='WARMUP' if current['warmup'] else 'ZERO_VOLATILITY' if current['zero_volatility'] else 'RULE_EVIDENCE_ONLY_CLASSIFICATION_UNVALIDATED',
                              action_qualification='NOT_EVALUATED',
                              pivots=current['pivots'], zones=current['zones'], pending=current['pending'],
                              daily_events=day_events))
    result=serialize(dict(code=code, price_mode=mode, volume_unit=volume_unit, rule_version=VERSION, snapshots=snapshots, event_ledger=ledger,
                          schema_version=SCHEMA_VERSION,parameters_fingerprint=parameters_fingerprint,
                          data_fingerprint=fingerprint(candles),events_fingerprint=fingerprint(events),data_quality=full_quality,
                          limitations=['Research parameters, no validated classification quality or trading edge',
                                       'Effective-date adjustment reconstruction; historical announcement timing not certified',
                                       'No official consolidation, breakout, retest or trade qualification rule activated']))
    validate_output(result)
    return result
