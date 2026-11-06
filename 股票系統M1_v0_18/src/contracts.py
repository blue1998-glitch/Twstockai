"""Strict input contracts and causal fingerprints. Standard library only."""
import hashlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation

SCHEMA_VERSION='stock-structure/1.0'


class DataError(ValueError):
    def __init__(self, code, path, detail):
        self.code,self.path,self.detail=code,path,detail
        super().__init__(f'{code} at {path}: {detail}')

    def as_dict(self):
        return dict(status='DATA_ERROR',code=self.code,path=self.path,detail=self.detail,
                    action_qualification='NOT_EVALUATED')


def fingerprint(value):
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return 'sha256:'+hashlib.sha256(raw).hexdigest()


def number(value,path):
    if value is None or isinstance(value,bool) or isinstance(value,str) and not value.strip():
        raise DataError('MISSING_OR_INVALID_NUMBER',path,'A finite numeric value is required')
    try:n=Decimal(str(value).replace(',',''))
    except (InvalidOperation,ValueError):raise DataError('INVALID_NUMBER',path,'Not a numeric value') from None
    if not n.is_finite():raise DataError('NONFINITE_NUMBER',path,'NaN and infinity are not valid market data')
    return n


def iso_date(value,path):
    if not isinstance(value,str):raise DataError('INVALID_DATE',path,'ISO date string required')
    try:dt=date.fromisoformat(value)
    except ValueError:raise DataError('INVALID_DATE',path,'Invalid calendar date') from None
    if dt.isoformat()!=value:raise DataError('INVALID_DATE',path,'Canonical YYYY-MM-DD required')
    return value


def validate_candles(candles):
    if not isinstance(candles,list):raise DataError('INVALID_CONTAINER','candles','List required')
    previous=None
    for i,c in enumerate(candles):
        path=f'candles[{i}]'
        if not isinstance(c,dict):raise DataError('INVALID_RECORD',path,'Object required')
        for key in ['date','open','high','low','close']:
            if key not in c:raise DataError('MISSING_FIELD',path+'.'+key,'Required price field missing')
            if c[key] is None:raise DataError('MISSING_VALUE',path+'.'+key,'Required price value is null')
        dt=iso_date(c['date'],path+'.date')
        if dt==previous:raise DataError('DUPLICATE_DATE',path+'.date','Duplicate trading record')
        if previous is not None and dt<previous:raise DataError('OUT_OF_ORDER_DATE',path+'.date','Records must be ascending')
        previous=dt
        o,h,l,close=[number(c[k],path+'.'+k) for k in ['open','high','low','close']]
        if not 0<l<=min(o,close)<=max(o,close)<=h:raise DataError('INCONSISTENT_OHLC',path,'High/low/open/close relationship invalid')
        if c.get('volume_shares_scaled') is not None and number(c['volume_shares_scaled'],path+'.volume_shares_scaled')<0:
            raise DataError('NEGATIVE_VOLUME',path+'.volume_shares_scaled','Volume cannot be negative')


def validate_events(events):
    if not isinstance(events,(list,tuple)):raise DataError('INVALID_CONTAINER','events','List or tuple required')
    seen=set()
    for i,e in enumerate(events):
        if not isinstance(e,dict):raise DataError('INVALID_EVENT',f'events[{i}]','Object required')
        for key in ['effective_date','factor']:
            if key not in e:raise DataError('MISSING_FIELD',f'events[{i}].{key}','Required event field missing')
        dt=iso_date(e['effective_date'],f'events[{i}].effective_date')
        if dt in seen:raise DataError('DUPLICATE_EVENT',f'events[{i}]','Same-day events require explicit aggregation upstream')
        seen.add(dt)
        if number(e['factor'],f'events[{i}].factor')<=0:raise DataError('INVALID_FACTOR',f'events[{i}].factor','Factor must be positive')


def quality(candles, *, expected_dates=None):
    validate_candles(candles)
    dates=[c['date'] for c in candles]
    volume_missing=sum(c.get('volume_shares_scaled') is None for c in candles)
    report=dict(status='EMPTY_INPUT' if not candles else 'PRICE_RECORDS_VALID',bars=len(candles),
                volume_context='UNAVAILABLE' if volume_missing==len(candles) else 'PARTIAL' if volume_missing else 'AVAILABLE_SOURCE_PRECISION',
                missing_volume_bars=volume_missing,calendar_status='UNVERIFIED',missing_dates=[],unexpected_dates=[])
    if expected_dates is not None:
        if not isinstance(expected_dates,list) or len(set(expected_dates))!=len(expected_dates):raise DataError('INVALID_CALENDAR','expected_dates','Unique list required')
        for dt in expected_dates:iso_date(dt,'expected_dates')
        expected=set(expected_dates);actual=set(dates)
        report.update(calendar_status='MATCHES_SUPPLIED_CALENDAR' if actual==expected else 'DIFFERS_FROM_SUPPLIED_CALENDAR',
                      missing_dates=sorted(expected-actual),unexpected_dates=sorted(actual-expected))
    return report


def validate_output(result):
    if not isinstance(result,dict):raise DataError('OUTPUT_CONTAINER','result','Object required')
    for key in ['schema_version','code','price_mode','rule_version','parameters_fingerprint','data_fingerprint','events_fingerprint','snapshots','event_ledger','data_quality']:
        if key not in result:raise DataError('MISSING_OUTPUT_FIELD',key,'Required output field missing')
    if result.get('schema_version')!=SCHEMA_VERSION:raise DataError('OUTPUT_SCHEMA','schema_version','Unsupported schema')
    if not isinstance(result['snapshots'],list) or not isinstance(result['event_ledger'],list):raise DataError('OUTPUT_CONTAINER','snapshots/event_ledger','Arrays required')
    if not result.get('parameters_fingerprint') or not result.get('data_fingerprint'):raise DataError('OUTPUT_PROVENANCE','result','Missing version fingerprints')
    last=None
    for s in result.get('snapshots',[]):
        if not isinstance(s,dict) or not all(k in s for k in ['as_of','schema_version','snapshot_id','data_fingerprint','parameters_fingerprint','data_quality','event_status','pivots','action_qualification']):
            raise DataError('MISSING_SNAPSHOT_FIELD','snapshots','Missing required snapshot fields')
        if s['schema_version']!=SCHEMA_VERSION:raise DataError('OUTPUT_SCHEMA','snapshots.schema_version','Unsupported snapshot schema')
        dt=iso_date(s.get('as_of'),'snapshots.as_of')
        if last is not None and dt<=last:raise DataError('OUTPUT_DATE_ORDER','snapshots','Non-ascending output')
        last=dt
        if s.get('action_qualification')!='NOT_EVALUATED':raise DataError('UNAUTHORIZED_QUALIFICATION','action_qualification','Trading rules not implemented')
        for p in s.get('pivots',[]):
            if not p['occurred_at']<=p['first_observed_at']<=p['confirmed_at']<=dt:
                raise DataError('FUTURE_PIVOT','pivots','Pivot chronology invalid')
    ids=[e['event_id'] for e in result.get('event_ledger',[])]
    if len(ids)!=len(set(ids)):raise DataError('DUPLICATE_OUTPUT_EVENT','event_ledger','Event IDs must be unique')
    return True
