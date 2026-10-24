"""Daily close SMA, independently calculated; no strategy/qualification rules.

Each snapshot's entire curve uses that snapshot's price anchor. Earlier
snapshots are retained, never replaced by end-of-period adjusted curves.
"""
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from contracts import DataError, fingerprint, quality, validate_candles, validate_events
from structure import D, project_prices

VERSION = 'daily-sma-0.1'
PERIODS = (5, 20, 60, 130, 260)


def curves(rows):
    """Return full-window arithmetic means, counting supplied price records."""
    closes=[D(row['close']) for row in rows]
    result={}
    # Keep rolling additions/subtractions exact, including values whose price
    # adjustment factor has many decimals. Round only the final mean.
    precision=max(50,max((c.adjusted()+1 for c in closes),default=1)
                  -min((c.as_tuple().exponent for c in closes),default=0)
                  +len(str(len(closes)))+2)
    with localcontext() as accumulator:
        accumulator.prec=precision
        for period in PERIODS:
            total=Decimal(0);values=[]
            for i,close in enumerate(closes):
                total+=close
                if i>=period:total-=closes[i-period]
                if i+1<period:values.append(None)
                else:
                    with localcontext() as output:
                        output.prec=28;output.rounding=ROUND_HALF_EVEN
                        values.append(str(total/Decimal(period)))
            result[str(period)]=values
    return result


def analyze_daily_ma(candles, events=(), *, code, mode):
    validate_candles(candles);validate_events(events)
    if mode not in ('RAW_CANDIDATE','ADJUSTED_CANDIDATE'):
        raise DataError('INVALID_PRICE_MODE','mode','Explicit candidate price mode required')
    params=dict(method='SIMPLE_ARITHMETIC_MEAN',field='CLOSE',periods=list(PERIODS),
                window_unit='SUPPLIED_DAILY_PRICE_RECORDS',full_window_required=True,
                raw_corporate_action_policy='KEEP_RAW_PRICE_SERIES',
                arithmetic='EXACT_ACCUMULATION_THEN_28_SIGNIFICANT_DIGITS_HALF_EVEN')
    param_fp=fingerprint(params);snapshots=[]
    for i,candle in enumerate(candles):
        as_of=candle['date'];prefix=candles[:i+1]
        effective=[e for e in events if e['effective_date']<=as_of]
        data_fp=fingerprint(prefix);events_fp=fingerprint(effective)
        values=curves(project_prices(prefix,effective,as_of,mode))
        ident=dict(code=code,price_mode=mode,as_of=as_of,rule_version=VERSION,
                   data_fingerprint=data_fp,events_fingerprint=events_fp,parameters_fingerprint=param_fp)
        snapshots.append(dict(**ident,snapshot_id=fingerprint(ident),bars=i+1,curves=values,
                              available={str(p):i+1>=p for p in PERIODS}))
    return dict(schema_version='daily-sma/1.0',rule_version=VERSION,code=code,price_mode=mode,
                parameters=params,parameters_fingerprint=param_fp,data_fingerprint=fingerprint(candles),
                events_fingerprint=fingerprint(events),data_quality=quality(candles),snapshots=snapshots,
                action_qualification='NOT_EVALUATED',classification_quality='NOT_EVALUATED',
                limitation='Price-record averages; official calendar and complete corporate actions remain unverified')
