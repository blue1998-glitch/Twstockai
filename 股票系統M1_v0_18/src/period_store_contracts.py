"""Period persistence boundary. Validates identity/shape, never calculates prices or MA."""
import json
from decimal import Decimal, InvalidOperation
from contracts import DataError, fingerprint, iso_date, validate_candles, validate_events

STORE_SCHEMA = 'period-file-store/1.0'
RECORD_SCHEMA = 'stored-period-result/1.0'
VERSIONS = ('period-sma-0.1-research', 'period-bars-0.1', 'period-job-0.1')
PARAMETERS_FP = 'sha256:4652c5aec12de2e0ba8878cc3352a9c1101916cba46a88203ca0281b2810b058'
PERIODS = {'weekly': [4, 13, 26, 52], 'monthly': [3, 6, 12, 24]}
IDENTITY = ('schema_version', 'rule_version', 'aggregation_version', 'code', 'exchange',
            'price_mode', 'as_of', 'source_id', 'volume_unit', 'data_fingerprint',
            'effective_events_fingerprint', 'calendar_fingerprint', 'parameters_fingerprint')
REASONS = {'VALUE_AVAILABLE', 'INSUFFICIENT_CONTIGUOUS_PERIODS', 'OPEN_PERIOD_EXCLUDED',
           'SUPPLIED_NO_TRADING_PERIOD', 'NO_PRICE_RECORDS', 'LEFT_EDGE_UNCERTAIN', 'CALENDAR_MISMATCH'}


def require(ok, path, detail='Malformed or inconsistent saved period bundle'):
    if not ok: raise DataError('PERIOD_STORE_CONTRACT', path, detail)


def canonical(value):
    def walk(v):
        if isinstance(v, dict):
            require(all(isinstance(k, str) for k in v), 'json.keys')
            for x in v.values(): walk(x)
        elif isinstance(v, list):
            for x in v: walk(x)
        else: require(v is None or isinstance(v, (str, int, float, bool)), 'json.type')
    try:
        walk(value)
        s = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        s.encode('utf-8')
        return s
    except (ValueError, TypeError, UnicodeError) as e:
        raise DataError('PERIOD_STORE_JSON', 'json', str(e)) from None


def pairs(items):
    obj = {}
    for k, v in items:
        require(k not in obj, 'json.' + k, 'Duplicate JSON key')
        obj[k] = v
    return obj


def decimal_string(v, path, nullable=True):
    if v is None and nullable: return
    require(isinstance(v, str), path)
    try: require(Decimal(v).is_finite(), path)
    except InvalidOperation: require(False, path)


def _calendar(c, as_of):
    if c is None: return None
    require(isinstance(c, dict) and set(c) == {'coverage_start','coverage_end','expected_dates'}, 'calendar')
    lo = iso_date(c['coverage_start'], 'calendar.start'); hi = iso_date(c['coverage_end'], 'calendar.end')
    dates = c['expected_dates']
    require(lo <= hi and isinstance(dates, list), 'calendar')
    for d in dates: iso_date(d, 'calendar.date')
    require(dates == sorted(set(dates)) and all(lo <= d <= hi for d in dates), 'calendar.dates')
    if lo > as_of: return None
    return dict(coverage_start=lo, coverage_end=min(hi, as_of), expected_dates=[d for d in dates if d <= as_of])


def validate_bundle(q, r):
    canonical(q); canonical(r)
    try: return _validate(q, r)
    except (KeyError, TypeError, IndexError, AttributeError) as e:
        raise DataError('PERIOD_STORE_FIELDS', 'bundle', type(e).__name__) from None


def _validate(q, r):
    required = {'schema_version','code','exchange','timeframe','price_mode','source','candles','corporate_actions','as_of'}
    require(required <= set(q) <= required | {'calendar'}, 'request.fields')
    require(q['schema_version'] == 'stock-period-analysis/1.0', 'request.schema_version')
    require(r['schema_version'] == 'period-analysis-result/1.0', 'result.schema_version')
    require(set(r) == {'schema_version','adapter_version','request_fingerprint','analysis_id','status',
                       'corporate_action_coverage','source','snapshot','classification_quality','action_qualification'}, 'result.fields')
    require(q['exchange'] in ('TWSE','TPEX') and q['timeframe'] == 'daily' and
            q['price_mode'] in ('RAW_CANDIDATE','ADJUSTED_CANDIDATE'), 'request.scope')
    require(isinstance(q['code'], str) and bool(q['code'].strip()), 'request.code')
    iso_date(q['as_of'], 'as_of')
    source = q['source']; actions = q['corporate_actions']; s = r['snapshot']
    require(source['code'] == q['code'] and source['exchange'] == q['exchange'], 'source.identity')
    require(isinstance(source['id'], str) and bool(source['id'].strip()) and
            source['volume_unit'] in ('SHARES_REPORTED','SHARES_SCALED_FROM_LOTS'), 'source')
    require(set(actions) == {'records','coverage_status'} and
            actions['coverage_status'] in ('UNVERIFIED','CASH_ONLY_VERIFIED_SAMPLE'), 'actions')
    validate_candles(q['candles']); validate_events(actions['records'])
    require((s['rule_version'], s['aggregation_version'], r['adapter_version']) == VERSIONS,
            'versions', 'Unsupported producer version; explicit reader upgrade required')
    require(s['schema_version'] == 'period-ma/1.0', 'snapshot.schema_version')
    require(r['request_fingerprint'] == fingerprint(q) and r['source'] == source and
            r['corporate_action_coverage'] == actions['coverage_status'], 'request.link')
    prefix = [c for c in q['candles'] if c['date'] <= q['as_of']]
    effective = [e for e in actions['records'] if e['effective_date'] <= q['as_of']]
    cal = _calendar(q.get('calendar'), q['as_of'])
    expected = dict(code=q['code'], exchange=q['exchange'], price_mode=q['price_mode'], as_of=q['as_of'],
                    source_id=source['id'], volume_unit=source['volume_unit'], data_fingerprint=fingerprint(prefix),
                    effective_events_fingerprint=fingerprint(effective), calendar_fingerprint=fingerprint(cal),
                    parameters_fingerprint=fingerprint(s['parameters']))
    for k, v in expected.items(): require(s[k] == v, 'snapshot.' + k)
    require(s['snapshot_id'] == fingerprint({k: s[k] for k in IDENTITY}), 'snapshot_id')
    require(r['analysis_id'] == fingerprint(dict(request=fingerprint(q), rule_version=s['rule_version'],
                                                adapter=r['adapter_version'], snapshot=s['snapshot_id'])), 'analysis_id')
    require(s['calendar_context'] == cal and s['calendar_authentication'] == ('SUPPLIED_UNVERIFIED' if cal else 'UNVERIFIED'), 'calendar.link')
    require(s['adjustment_anchor'] == q['as_of'] and type(s['daily_records']) is int and s['daily_records'] == len(prefix) and
            s['last_price_date'] == (prefix[-1]['date'] if prefix else None), 'snapshot.scope')
    require(r['status'] == s['status'] == ('COMPLETED' if prefix else 'EMPTY_INPUT'), 'status')
    for x in (r, s):
        require(x['classification_quality'] == 'NOT_VALIDATED' and x['action_qualification'] == 'NOT_EVALUATED', 'qualification')
    require(isinstance(s['data_quality'], dict) and isinstance(s['limitations'], list) and
            all(isinstance(x, str) for x in s['limitations']), 'snapshot.metadata')
    require(s['parameters']['periods'] == PERIODS and s['parameters_fingerprint'] == PARAMETERS_FP, 'parameters',
            'Producer version has a fixed parameter contract; explicit reader upgrade required')
    for tf, periods in PERIODS.items():
        block = s[tf]; bars = block['bars']; n = len(bars)
        require(set(block) == {'periods','bars','elapsed','candidate'} and block['periods'] == periods and isinstance(bars, list), tf)
        require(bool(bars) == bool(prefix), tf + '.bars')
        previous = None
        for b in bars:
            for k in ('period_start','period_end','observed_through'): iso_date(b[k], tf + '.' + k)
            require(b['period_start'] <= b['observed_through'] <= b['period_end'] and
                    b['observed_through'] == min(b['period_end'], q['as_of']) and
                    (previous is None or previous < b['period_start']), tf + '.order')
            previous = b['period_end']
            require(isinstance(b['period'], str) and type(b['daily_records']) is int and b['daily_records'] >= 0, tf + '.bar')
            require(b['calendar_state'] == ('ELAPSED_CALENDAR_PERIOD' if b['period_end'] <= q['as_of'] else 'OPEN_CALENDAR_PERIOD'), tf + '.calendar_state')
            for k in ('open','high','low','close','volume_shares','known_volume_sum_shares'): decimal_string(b[k], tf + '.' + k)
            require((b['close'] is None) == (b['daily_records'] == 0), tf + '.close')
            for k in ('first_price_date','last_price_date'):
                if b[k] is not None:
                    iso_date(b[k], k); require(b['period_start'] <= b[k] <= b['observed_through'], k)
            require(type(b['ma_eligible']) is bool and type(b['skip_supplied_no_trading_period']) is bool and
                    b['ma_block_reason'] in REASONS - {'VALUE_AVAILABLE','INSUFFICIENT_CONTIGUOUS_PERIODS','OPEN_PERIOD_EXCLUDED'} | {None} and
                    b['ma_eligible'] == (b['ma_block_reason'] is None), tf + '.eligibility')
            require(b['volume_context'] in ('UNAVAILABLE','PARTIAL','AVAILABLE_SOURCE_PRECISION') and
                    b['calendar_status'] in ('UNVERIFIED','DIFFERS_FROM_SUPPLIED_CALENDAR','MATCHES_SUPPLIED_CALENDAR_TO_AS_OF','PARTIAL_SUPPLIED_CALENDAR_SCOPE'), tf + '.metadata')
        for view in ('elapsed','candidate'):
            v = block[view]; keys = {str(p) for p in periods}
            require(set(v) == {'basis','curves','point_status','latest'} and
                    v['basis'] == ('ELAPSED_CALENDAR_PERIODS_ONLY' if view == 'elapsed' else 'INCLUDING_OPEN_PERIOD_CANDIDATE'), tf + '.view')
            require(set(v['curves']) == set(v['point_status']) == set(v['latest']) == keys, tf + '.curves')
            ix = [i for i,b in enumerate(bars) if view == 'candidate' or
                  b['calendar_state'] == 'ELAPSED_CALENDAR_PERIOD' and not b['skip_supplied_no_trading_period']]
            for p in keys:
                curve = v['curves'][p]; states = v['point_status'][p]; latest = v['latest'][p]
                require(isinstance(curve, list) and isinstance(states, list) and len(curve) == len(states) == n, tf + '.alignment')
                for value, state in zip(curve, states):
                    decimal_string(value, tf + '.curve')
                    require(state in REASONS and (value is not None) == (state == 'VALUE_AVAILABLE'), tf + '.point_status')
                index = ix[-1] if ix else None; b = bars[index] if index is not None else None
                require(type(latest['available']) is bool and latest['available'] == (latest['value'] is not None), tf + '.latest.available')
                for k in ('period','calendar_state','last_price_date'):
                    require(latest[k] == (b[k] if b else None), tf + '.latest.' + k)
                require(latest['value'] == (curve[index] if index is not None else None) and
                        latest['reason'] == (states[index] if index is not None else 'NO_ELAPSED_PERIODS' if view == 'elapsed' else 'EMPTY_INPUT'), tf + '.latest')
                require(isinstance(latest['window_periods'], list) and len(latest['window_periods']) <= int(p) and
                        all(x in {b['period'] for b in bars} for x in latest['window_periods']), tf + '.window')
    return dict(code=q['code'], exchange=q['exchange'], price_mode=q['price_mode'], as_of=q['as_of'],
                rule_version=s['rule_version'], aggregation_version=s['aggregation_version'], adapter_version=r['adapter_version'],
                parameters_fingerprint=s['parameters_fingerprint'], source_id=source['id'], volume_unit=source['volume_unit'],
                last_price_date=s['last_price_date'], calendar_authentication=s['calendar_authentication'],
                calendar_context=cal, source=source, request_fingerprint=r['request_fingerprint'],
                result_fingerprint=fingerprint(r), snapshot_id=s['snapshot_id'])
