"""Pure weekly/monthly OHLC and close SMA. No UI, storage or strategy rules."""
from calendar import monthrange
from datetime import date,timedelta
from decimal import Decimal,Context,localcontext,ROUND_HALF_EVEN
from contracts import DataError,fingerprint,iso_date,quality,validate_candles,validate_events
from structure import D,project_prices,volume_precision

VERSION='period-sma-0.1-research'
AGGREGATION_VERSION='period-bars-0.1'
PERIODS={'weekly':(4,13,26,52),'monthly':(3,6,12,24)}


def _calendar_view(context,as_of):
    if context is None:return None
    if not isinstance(context,dict) or set(context)!={'coverage_start','coverage_end','expected_dates'}:
        raise DataError('PERIOD_CALENDAR','calendar','Explicit coverage bounds and expected_dates required')
    start=iso_date(context['coverage_start'],'calendar.coverage_start');end=iso_date(context['coverage_end'],'calendar.coverage_end')
    dates=context['expected_dates']
    if start>end or not isinstance(dates,list):raise DataError('PERIOD_CALENDAR','calendar','Ordered coverage and date list required')
    previous=None
    for dt in dates:
        iso_date(dt,'calendar.expected_dates')
        if not start<=dt<=end or previous is not None and dt<=previous:
            raise DataError('PERIOD_CALENDAR','calendar.expected_dates','Unique ascending dates inside coverage required')
        previous=dt
    if start>as_of:return None
    return dict(coverage_start=start,coverage_end=min(end,as_of),expected_dates=[d for d in dates if d<=as_of])


def _bounds(dt,timeframe):
    if timeframe=='weekly':
        start=dt-timedelta(days=dt.weekday())
        try:end=start+timedelta(days=6)
        except OverflowError:raise DataError('PERIOD_DATE_RANGE','date','Weekly boundary exceeds supported date range') from None
        year,week,_=dt.isocalendar();label=f'{year:04d}-W{week:02d}'
    else:
        start=dt.replace(day=1);end=dt.replace(day=monthrange(dt.year,dt.month)[1]);label=f'{dt.year:04d}-{dt.month:02d}'
    return start,end,label


def _exact_sum(values):
    if not values:return None
    precision=max(50,max(v.adjusted()+1 for v in values)-min(v.as_tuple().exponent for v in values)+len(str(len(values)))+2)
    with localcontext(Context(prec=precision,rounding=ROUND_HALF_EVEN)):
        return sum(values,Decimal(0))


def _mean(values):
    total=_exact_sum(values)
    with localcontext(Context(prec=28,rounding=ROUND_HALF_EVEN)):
        return str(total/Decimal(len(values)))


def _aggregate(rows,as_of,timeframe,calendar):
    if not rows:return []
    cutoff=date.fromisoformat(as_of);first=rows[0]['date']
    domain_start=min(first,calendar['coverage_start']) if calendar else first
    cursor=_bounds(date.fromisoformat(domain_start),timeframe)[0]
    grouped={}
    for row in rows:grouped.setdefault(_bounds(date.fromisoformat(row['date']),timeframe)[0],[]).append(row)
    result=[]
    while cursor<=cutoff:
        start,end,label=_bounds(cursor,timeframe);a=start.isoformat();b=end.isoformat();through=min(b,as_of);part=grouped.get(start,[])
        actual={r['date'] for r in part};missing=[];unexpected=[];cal_status='UNVERIFIED';covered=False;expected=[]
        if calendar:
            lo=max(a,calendar['coverage_start']);hi=min(through,calendar['coverage_end'])
            if lo<=hi:
                expected=[d for d in calendar['expected_dates'] if lo<=d<=hi]
                missing=sorted(set(expected)-actual);unexpected=sorted({d for d in actual if lo<=d<=hi}-set(expected))
                covered=calendar['coverage_start']<=a and calendar['coverage_end']>=through
                cal_status='DIFFERS_FROM_SUPPLIED_CALENDAR' if missing or unexpected else 'MATCHES_SUPPLIED_CALENDAR_TO_AS_OF' if covered else 'PARTIAL_SUPPLIED_CALENDAR_SCOPE'
        elapsed=b<=as_of
        known_closed=not part and elapsed and covered and not expected and not missing and not unexpected
        start_covered=bool(calendar and calendar['coverage_start']<=a and calendar['coverage_end']>=min(first,through))
        left_uncertain=first>a and not start_covered and (not part or part[0]['date']==first)
        edge='LEFT_EDGE_UNCERTAIN' if left_uncertain else 'START_ALIGNED' if first==a else 'CALENDAR_COVERS_START' if first>a and start_covered else 'IN_RANGE'
        known=[D(r['volume_shares_scaled']) for r in part if r.get('volume_shares_scaled') is not None]
        known_sum=_exact_sum(known);missing_volume=len(part)-len(known)
        volume=None if not part or missing_volume else str(known_sum)
        issue='SUPPLIED_NO_TRADING_PERIOD' if known_closed else 'NO_PRICE_RECORDS' if not part else 'LEFT_EDGE_UNCERTAIN' if left_uncertain else 'CALENDAR_MISMATCH' if missing or unexpected else None
        result.append(dict(period=label,period_start=a,period_end=b,observed_through=through,
                           calendar_state='ELAPSED_CALENDAR_PERIOD' if elapsed else 'OPEN_CALENDAR_PERIOD',
                           first_price_date=part[0]['date'] if part else None,last_price_date=part[-1]['date'] if part else None,daily_records=len(part),
                           open=part[0]['open'] if part else None,high=str(max(D(r['high']) for r in part)) if part else None,
                           low=str(min(D(r['low']) for r in part)) if part else None,close=part[-1]['close'] if part else None,
                           volume_shares=volume,known_volume_sum_shares=str(known_sum) if known_sum is not None else None,
                           missing_volume_bars=missing_volume,volume_context='UNAVAILABLE' if not known else 'PARTIAL' if missing_volume else 'AVAILABLE_SOURCE_PRECISION',
                           calendar_status=cal_status,calendar_scope_covers_period_to_as_of=covered,missing_dates=missing,unexpected_dates=unexpected,
                           range_start_status=edge,ma_eligible=issue is None,ma_block_reason=issue,skip_supplied_no_trading_period=known_closed))
        if end>=cutoff:break
        cursor=end+timedelta(days=1)
    return result


def _ma_view(bars,periods,include_open):
    curves={str(p):[] for p in periods};states={str(p):[] for p in periods};windows={str(p):[] for p in periods};history=[]
    for b in bars:
        reason=b['ma_block_reason']
        if b['skip_supplied_no_trading_period']:
            pass  # Explicit supplied-calendar closure: no synthetic close.
        elif reason:
            history=[]  # Do not silently span missing prices or uncertain starts.
        elif not include_open and b['calendar_state']=='OPEN_CALENDAR_PERIOD':
            reason='OPEN_PERIOD_EXCLUDED'
        else:
            history.append(b)
        for p in periods:
            k=str(p);used=history[-p:]
            status=reason or ('VALUE_AVAILABLE' if len(used)==p else 'INSUFFICIENT_CONTIGUOUS_PERIODS')
            curves[k].append(_mean([D(x['close']) for x in used]) if status=='VALUE_AVAILABLE' else None)
            states[k].append(status);windows[k].append([x['period'] for x in used] if not reason else [])
    candidates=[i for i,b in enumerate(bars) if include_open or b['calendar_state']=='ELAPSED_CALENDAR_PERIOD' and not b['skip_supplied_no_trading_period']]
    index=candidates[-1] if candidates else None
    latest={}
    for p in periods:
        k=str(p);value=curves[k][index] if index is not None else None;b=bars[index] if index is not None else None
        latest[k]=dict(value=value,available=value is not None,period=b['period'] if b else None,
                       calendar_state=b['calendar_state'] if b else None,last_price_date=b['last_price_date'] if b else None,
                       reason=states[k][index] if index is not None else 'NO_ELAPSED_PERIODS' if not include_open else 'EMPTY_INPUT',
                       window_periods=windows[k][index] if index is not None else [])
    return dict(basis='INCLUDING_OPEN_PERIOD_CANDIDATE' if include_open else 'ELAPSED_CALENDAR_PERIODS_ONLY',curves=curves,point_status=states,latest=latest)


def analyze_period_ma(candles,events=(),*,code,exchange,mode,as_of,source_id,volume_unit,calendar=None):
    validate_candles(candles);validate_events(events);iso_date(as_of,'as_of');volume_precision(volume_unit)
    if not isinstance(code,str) or not code.strip() or not isinstance(source_id,str) or not source_id.strip():
        raise DataError('PERIOD_SOURCE','code/source_id','Explicit stock and source identity strings required')
    if exchange not in ('TWSE','TPEX'):raise DataError('PERIOD_SCOPE','exchange','Explicit TWSE or TPEX exchange required')
    if mode not in ('RAW_CANDIDATE','ADJUSTED_CANDIDATE'):raise DataError('INVALID_PRICE_MODE','mode','Explicit candidate mode required')
    cal=_calendar_view(calendar,as_of);prefix=[c for c in candles if c['date']<=as_of];effective=[e for e in events if e['effective_date']<=as_of]
    params=dict(periods={k:list(v) for k,v in PERIODS.items()},week='ISO_MONDAY_THROUGH_SUNDAY',month='GREGORIAN_CALENDAR_MONTH',
                as_of_semantics='END_OF_DATE; DAILY_RECORDS_ASSUMED_CLOSED',method='SIMPLE_ARITHMETIC_MEAN_OF_PERIOD_CLOSES',
                arithmetic='EXACT_ACCUMULATION_THEN_28_SIGNIFICANT_DIGITS_HALF_EVEN',full_window_required=True,
                uncertain_left_edge='EXCLUDE_AND_BREAK_WINDOW',unknown_empty_period='BREAK_WINDOW_WITHOUT_FORWARD_FILL',
                supplied_calendar_zero_trading_period='SKIP_WITHOUT_SYNTHETIC_PRICE',raw_policy='KEEP_RAW_PRICE_SERIES',
                candidate_and_elapsed_views='SEPARATE; ELAPSED_IS_NOT_CALENDAR_CERTIFICATION')
    # Freeze the established price-projection precision, independent of the
    # caller's Decimal context; no event after as_of is applied.
    with localcontext(Context(prec=28,rounding=ROUND_HALF_EVEN)):
        rows=project_prices(prefix,effective,as_of,mode)
    outputs={}
    for timeframe,periods in PERIODS.items():
        bars=_aggregate(rows,as_of,timeframe,cal)
        outputs[timeframe]=dict(periods=list(periods),bars=bars,elapsed=_ma_view(bars,periods,False),candidate=_ma_view(bars,periods,True))
    ident=dict(schema_version='period-ma/1.0',rule_version=VERSION,aggregation_version=AGGREGATION_VERSION,code=code,exchange=exchange,price_mode=mode,
               as_of=as_of,source_id=source_id,volume_unit=volume_unit,data_fingerprint=fingerprint(prefix),
               effective_events_fingerprint=fingerprint(effective),calendar_fingerprint=fingerprint(cal),parameters_fingerprint=fingerprint(params))
    input_quality=quality(prefix)
    if cal:
        actual={r['date'] for r in prefix};inside={d for d in actual if cal['coverage_start']<=d<=cal['coverage_end']}
        missing=sorted(set(cal['expected_dates'])-actual);unexpected=sorted(inside-set(cal['expected_dates']))
        partial=bool(prefix and prefix[0]['date']<cal['coverage_start']) or cal['coverage_end']<as_of
        input_quality.update(calendar_status='DIFFERS_FROM_SUPPLIED_CALENDAR' if missing or unexpected else 'PARTIAL_SUPPLIED_CALENDAR_SCOPE' if partial else 'MATCHES_SUPPLIED_CALENDAR',missing_dates=missing,unexpected_dates=unexpected)
    return dict(**ident,snapshot_id=fingerprint(ident),status='COMPLETED' if prefix else 'EMPTY_INPUT',parameters=params,
                adjustment_anchor=as_of,daily_records=len(prefix),last_price_date=prefix[-1]['date'] if prefix else None,
                calendar_context=cal,calendar_authentication='SUPPLIED_UNVERIFIED' if cal else 'UNVERIFIED',
                data_quality=input_quality,**outputs,
                classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED',
                limitations=['Elapsed calendar periods are not proof of complete or authenticated market data',
                             'Uncertain leading periods and unknown missing periods break full windows',
                             'Effective-date cash adjustment candidates; historical publication timing and full action coverage unverified',
                             'No weekly/monthly structural classification or trading qualification is provided'])
