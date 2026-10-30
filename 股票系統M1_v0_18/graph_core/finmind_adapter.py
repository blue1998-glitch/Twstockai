"""Pure, restricted FinMind daily intake. No HTTP, files, UI or trading logic.

Every returned payload/result can reconstruct quotes: keep it local, never Git.
Only public_summary() is suitable for a non-quote acceptance report.
"""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json

from .core import analyze, VERSION as CORE_VERSION

VERSION = 'finmind-graph-adapter/0.1'
TAIPEI = timezone(timedelta(hours=8))


class IntakeError(ValueError):
    """Stable diagnostic code, deliberately without any quote values."""


def _day(value):
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise IntakeError('INVALID_DATE') from None


def _timestamp(value):
    try:
        result = datetime.fromisoformat(value)
        if result.tzinfo is None:
            raise ValueError
        return result
    except (TypeError, ValueError):
        raise IntakeError('UNKNOWN_SOURCE_TIME') from None


def _number(value, *, volume=False):
    # Binary floats have already lost the original JSON decimal lexeme.
    if type(value) not in (int, str, Decimal):
        raise IntakeError('INVALID_VOLUME' if volume else 'MISSING_PRICE')
    try:
        number = Decimal(value)
        if not number.is_finite():
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        raise IntakeError('INVALID_VOLUME' if volume else 'ZERO_OR_INVALID_OHLC') from None
    if volume:
        if number < 0 or number != number.to_integral_value():
            raise IntakeError('INVALID_VOLUME')
    elif number <= 0:
        raise IntakeError('ZERO_OR_INVALID_OHLC')
    return format(number, 'f')


def _validate(response, request):
    if request.get('schema_version') != 'finmind-graph-request/0.1':
        raise IntakeError('UNSUPPORTED_SCHEMA')
    if (request.get('dataset'), request.get('code'), request.get('exchange')) != (
            'TaiwanStockPrice', '2884', 'TWSE'):
        raise IntakeError('UNSUPPORTED_SCOPE')
    if request.get('volume_unit') != 'SHARES_REPORTED':
        raise IntakeError('VOLUME_UNIT')
    if request.get('historical_available_at') != 'UNKNOWN':
        raise IntakeError('HISTORICAL_AVAILABILITY_NOT_PROVEN')
    for key in ('source_id', 'price_basis_id', 'calendar_source_id'):
        if not isinstance(request.get(key), str) or not request[key].strip():
            raise IntakeError('SOURCE_BINDING_REQUIRED')
    if request.get('calendar_completeness') != 'UNKNOWN':
        raise IntakeError('CALENDAR_COMPLETENESS_NOT_PROVEN')
    start, end, anchor = map(_day, (request['start_date'], request['end_date'], request['as_of']))
    if not date(2026, 3, 1) <= start <= end <= date(2026, 7, 22):
        raise IntakeError('UNSUPPORTED_SCOPE')
    if not start <= anchor <= end:
        raise IntakeError('EXACT_AS_OF_REQUIRED')
    retrieved = _timestamp(request.get('retrieved_at'))
    expected = request.get('expected_dates')
    if not isinstance(expected, list) or not expected:
        raise IntakeError('CALENDAR_REQUIRED')
    expected_days = [_day(d) for d in expected]
    if (expected_days != sorted(set(expected_days)) or
            any(not start <= d <= end for d in expected_days)):
        raise IntakeError('INVALID_CALENDAR')
    if response.get('status') != 200 or not isinstance(response.get('data'), list):
        raise IntakeError('SOURCE_API_REFUSED')
    rows = response['data']
    dates = []
    bars = []
    for row in rows:
        day = _day(row.get('date'))
        if day in dates:
            raise IntakeError('DUPLICATE_DATE')
        if dates and day < dates[-1]:
            raise IntakeError('UNORDERED_DATE')
        dates.append(day)
        if not start <= day <= end:
            raise IntakeError('DATE_OUTSIDE_REQUEST')
        if day >= retrieved.astimezone(TAIPEI).date() or row.get('complete', True) is not True:
            raise IntakeError('INCOMPLETE_DAY')
        if row.get('stock_id') != request['code']:
            raise IntakeError('STOCK_MISMATCH')
        if row.get('price_basis_id', request['price_basis_id']) != request['price_basis_id']:
            raise IntakeError('BASIS_MISMATCH')
        if row.get('source_id', request['source_id']) != request['source_id']:
            raise IntakeError('SOURCE_MISMATCH')
        values = {out: _number(row.get(field)) for out, field in
                  (('open', 'open'), ('high', 'max'), ('low', 'min'), ('close', 'close'))}
        o, h, l, c = (Decimal(values[k]) for k in ('open', 'high', 'low', 'close'))
        if not l <= min(o, c) <= max(o, c) <= h:
            raise IntakeError('ZERO_OR_INVALID_OHLC')
        volume = _number(row.get('Trading_Volume'), volume=True)
        if day <= anchor:
            bars.append(dict(date=day.isoformat(), **values, volume_shares_scaled=volume,
                             complete=True, available_at=None))
    if not bars or bars[-1]['date'] != anchor.isoformat():
        raise IntakeError('EXACT_AS_OF_REQUIRED')
    supplied = {r['date'] for r in bars}
    prefix_expected = [d for d in expected if d <= anchor.isoformat()]
    if any(d not in supplied for d in prefix_expected):
        raise IntakeError('MISSING_EXPECTED_DATES')
    if any(d not in expected for d in supplied):
        raise IntakeError('UNEXPECTED_SESSION')
    warnings = request.get('basis_warnings')
    if not isinstance(warnings, list):
        raise IntakeError('BASIS_WARNINGS_REQUIRED')
    resets = []
    for warning in warnings:
        day = _day(warning.get('date'))
        if (not start <= day <= end or
                warning.get('kind') != 'NON_COMPARABLE_MARKER_EVENT_TYPE_UNKNOWN' or
                not isinstance(warning.get('source_id'), str) or not warning['source_id']):
            raise IntakeError('INVALID_BASIS_WARNING')
        if day <= anchor:
            resets.append(day.isoformat())
    # The known in-scope official warning must not be dropped by a caller.
    if start <= date(2026, 7, 1) <= anchor and '2026-07-01' not in resets:
        raise IntakeError('KNOWN_BASIS_WARNING_REQUIRED')
    payload = dict(schema_version='graph-recognition-input/0.1',
                   context=dict(code=request['code'], exchange=request['exchange'],
                                source_id=request['source_id'], price_basis_id=request['price_basis_id'],
                                price_mode='RAW_CANDIDATE', volume_unit='SHARES_REPORTED',
                                source_kind='FINMIND_TAIWAN_STOCK_PRICE_RETROSPECTIVE',
                                corporate_action_comparability='UNKNOWN_NO_CROSS_BASIS_CERTIFICATION',
                                historical_publication_timing='UNKNOWN'),
                   bars=bars, expected_dates=prefix_expected, basis_break_dates=sorted(set(resets)))
    return payload


def analyze_response(response, request):
    """Validate the supplied response and run unchanged core on exact prefix.

    Full-response integrity is separate from the numerical analysis identity.
    Future malformed source rows refuse intake; valid future mutations cannot
    alter the prior core result. No historical availability is inferred.
    """
    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN)):
        payload = _validate(response, request)
        result = analyze(payload, as_of=request['as_of'])
        raw_identity = json.dumps(response, sort_keys=True, separators=(',', ':'), default=str)
        return dict(schema_version=VERSION, graph_input=payload, analysis=result,
                    provenance=dict(source_id=request['source_id'], retrieved_at=request['retrieved_at'],
                                    historical_available_at='UNKNOWN',
                                    response_identity=hashlib.sha256(raw_identity.encode()).hexdigest(),
                                    response_records=len(response['data'])),
                    limitations=['HISTORICAL_AVAILABLE_AT_UNKNOWN', 'CALENDAR_COMPLETENESS_UNKNOWN',
                                 'CORPORATE_ACTIONS_UNKNOWN', 'CROSS_BASIS_CONTINUITY_NOT_QUALIFIED',
                                 'GRAPH_RECOGNITION_NOT_VALIDATED', 'REDISTRIBUTION_NOT_AUTHORIZED'])


def public_summary(result):
    """Allowlist: no OHLCV, references, IDs/hashes derived from source bars."""
    analysis = result['analysis']
    return dict(schema_version='finmind-graph-public-summary/0.1', adapter_version=VERSION,
                core_version=CORE_VERSION, code=analysis['context']['code'], as_of=analysis['as_of'],
                status='RESEARCH_COMPUTED_NOT_QUALIFIED',
                source_records=analysis['source_records'],
                basis_break_dates=deepcopy(analysis['data_gaps']['basis_resets']),
                historical_available_at='UNKNOWN', calendar_completeness='UNKNOWN',
                corporate_action_type='UNKNOWN', continuous_structure_qualified=False,
                classification_quality=analysis['classification_quality'],
                qualified_interpretation=analysis['qualified_interpretation'],
                primary_pressure_id=analysis['comparison']['primary_pressure_id'],
                data_qualified=False, execution_model_qualified=False,
                historical_signal_eligible=False, policy_authorized=False,
                live_execution_authorized=False, limitations=deepcopy(result['limitations']))


def assess_integer_lot_display(*, official_unit, displayed_value):
    """An integer lot display cannot authenticate a precise share count.

    No multiplication, rounding rule, inferred interval or price validation.
    """
    if official_unit != '成交張數':
        raise IntakeError('UNSUPPORTED_OFFICIAL_VOLUME_DISPLAY')
    if not isinstance(displayed_value, str) or not displayed_value.replace(',', '').isdigit():
        raise IntakeError('INVALID_OFFICIAL_VOLUME_DISPLAY')
    return dict(official_volume_precision='INTEGER_LOTS_DISPLAY',
                finmind_volume_unit='SHARES_REPORTED', exact_shares_verified=False,
                exact_shares_status='UNKNOWN', precise_share_comparison='REFUSED_PRECISION_INSUFFICIENT')
