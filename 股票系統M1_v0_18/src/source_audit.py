"""Strict official-source parsers and planned-calendar comparisons.

Planned holidays are evidence, not certification of ad-hoc market closures,
individual suspensions, listing history, or source revisions.
"""
from datetime import date,timedelta
import html
import re
from contracts import DataError, iso_date, number, validate_candles

HOLIDAYS=('開國紀念','除夕','春節','和平紀念','兒童節','掃墓','勞動節','端午節','教師節','中秋節','國慶日','光復','行憲紀念')


def _year(title,expected):
    m=re.search(r'(\d+)\s*年',title)
    actual=int(m[1]) if m else None
    if actual is not None and actual<1911:actual+=1911
    if actual!=expected:raise DataError('SOURCE_YEAR_MISMATCH','title','Requested and returned years differ')


def parse_twse_month(payload,*,code,year,month):
    if not isinstance(payload,dict) or str(payload.get('stat')).lower()!='ok':
        raise DataError('SOURCE_STATUS','stat','Official response is not OK')
    title=payload.get('title','');_year(title,year)
    if not re.search(r'(?<!\d)'+re.escape(code)+r'(?!\d)',title):
        raise DataError('SOURCE_IDENTITY_MISMATCH','title','Requested stock code not present')
    if payload.get('date')!=f'{year}{month:02d}01':raise DataError('SOURCE_PERIOD_MISMATCH','date','Requested month differs')
    fields=payload.get('fields',[])
    required=['日期','成交股數','開盤價','最高價','最低價','收盤價']
    if len(set(fields))!=len(fields) or not all(k in fields for k in required):
        raise DataError('SOURCE_FIELDS','fields','Required fields and explicit share unit required')
    rows=[]
    for i,row in enumerate(payload.get('data',[])):
        if len(row)!=len(fields):raise DataError('SOURCE_ROW_WIDTH',f'data[{i}]','Incomplete row')
        r=dict(zip(fields,row));parts=str(r['日期']).split('/')
        if len(parts)!=3:raise DataError('SOURCE_DATE','日期','ROC date required')
        try:dt=date(int(parts[0])+1911,int(parts[1]),int(parts[2]))
        except ValueError:raise DataError('SOURCE_DATE','日期','Invalid source date') from None
        if dt.year!=year or dt.month!=month:raise DataError('SOURCE_PERIOD_MISMATCH','日期','Row outside requested month')
        volume=number(r['成交股數'],'成交股數')
        if volume!=volume.to_integral_value():raise DataError('SOURCE_VOLUME','成交股數','Reported share count must be integral')
        candle=dict(date=dt.isoformat(),volume_shares_scaled=str(volume))
        for target,source in [('open','開盤價'),('high','最高價'),('low','最低價'),('close','收盤價')]:
            candle[target]=str(number(r[source],source))
        rows.append(candle)
    if not rows:raise DataError('SOURCE_EMPTY_MONTH','data','Empty month is not presumed a valid no-trade month')
    validate_candles(rows)
    return rows


def parse_twse_holidays(payload,year):
    _year(payload.get('title',''),year)
    if str(payload.get('stat')).lower()!='ok':raise DataError('SOURCE_STATUS','stat','Holiday response not OK')
    closed=set();opened=set()
    for row in payload['data']:
        dt=iso_date(row[0],'holiday.date');name=row[1]
        if date.fromisoformat(dt).year!=year:raise DataError('SOURCE_YEAR_MISMATCH','data','Mixed holiday years')
        if '開始交易' in name or '最後交易' in name:opened.add(dt)
        elif '無交易' in name or any(word in name for word in HOLIDAYS):closed.add(dt)
        else:raise DataError('UNKNOWN_HOLIDAY_ROW','名稱',name)
    return dict(year=year,exchange='TWSE',closed_dates=sorted(closed),open_markers=sorted(opened),
                coverage='PLANNED_SCHEDULE_ONLY',ad_hoc_closures='UNVERIFIED')


def parse_tpex_holidays(payload,year):
    text=payload.get('data',{}).get('html','')
    clean=lambda s:html.unescape(re.sub(r'<[^>]*>',' ',s)).strip()
    _year(clean(text),year)
    closed=set();opened=set();last_name=None
    def dates(cell):
        return [date(year,int(m),int(d)).isoformat() for m,d in re.findall(r'(\d+)月\s*(\d+)日',cell)]
    for tr in re.findall(r'<tr\b[^>]*>(.*?)</tr>',text,re.S|re.I):
        cells=[clean(c) for c in re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>',tr,re.S|re.I)]
        if len(cells)<2 or cells[0]=='紀念節日名稱':continue
        if re.match(r'^\d+月\s*\d+日',cells[0]):
            name=last_name;cell=cells[0];note=' '.join(cells[1:])
        else:
            name=cells[0];last_name=name;cell=cells[1];note=' '.join(cells[2:])
        if name is None:raise DataError('HOLIDAY_ROWSPAN','html','Continuation without event name')
        # Bond-system closure dates are not equity-market closure dates.
        if any(k in name for k in ['國際債券','債券等殖','債券處所']):continue
        ds=dates(cell)
        if not ds:raise DataError('HOLIDAY_DATE_MISSING','html',name)
        if '開始交易' in name:opened.update(ds)
        elif '股票交易系統' in name and '最後交易' in name:
            opened.update(ds)
            if '無交易' in note:closed.update(dates(note))
        elif any(k in name for k in HOLIDAYS):closed.update(ds)
        else:raise DataError('UNKNOWN_HOLIDAY_ROW','html',name)
    if not closed:raise DataError('EMPTY_HOLIDAY_SCHEDULE','html','No holiday evidence parsed')
    return dict(year=year,exchange='TPEX',closed_dates=sorted(closed),open_markers=sorted(opened),
                coverage='PLANNED_SCHEDULE_ONLY',ad_hoc_closures='UNVERIFIED')


def planned_dates(schedules,start,end):
    first=date.fromisoformat(iso_date(start,'start'));last=date.fromisoformat(iso_date(end,'end'))
    if last<first:raise DataError('INVALID_RANGE','end','End before start')
    years={s['year'] for s in schedules}
    if not set(range(first.year,last.year+1))<=years:
        raise DataError('CALENDAR_YEAR_GAP','schedules','A requested year is not covered')
    closed={dt for s in schedules for dt in s['closed_dates']}
    result=[];dt=first
    while dt<=last:
        if dt.weekday()<5 and dt.isoformat() not in closed:result.append(dt.isoformat())
        dt+=timedelta(days=1)
    return result


def compare_dates(candles,expected):
    validate_candles(candles)
    actual={c['date'] for c in candles};expected=set(expected)
    missing=sorted(expected-actual);unexpected=sorted(actual-expected)
    return dict(status='MATCHES_PLANNED_SCHEDULE' if not missing and not unexpected else 'DIFFERENCES_REQUIRE_EVIDENCE',
                observed=len(candles),planned=len(expected),missing_dates=missing,unexpected_dates=unexpected,
                individual_suspensions='UNVERIFIED',ad_hoc_closures='UNVERIFIED',
                interpretation='Differences are evidence requests, not automatically missing-price defects')


def apply_evidenced_closures(expected,evidence,*,exchange):
    closed=set();used=[]
    for item in evidence:
        if item.get('exchange')!=exchange:continue
        if item.get('verification')!='OFFICIAL_PRIMARY_TEXT_RETRIEVED':
            raise DataError('UNVERIFIED_CLOSURE','evidence','Do not remove dates without reviewed primary evidence')
        dt=iso_date(item.get('date'),'evidence.date')
        if not item.get('source_url'):raise DataError('MISSING_EVIDENCE','source_url','Primary source URL required')
        closed.add(dt);used.append(item)
    return dict(dates=[dt for dt in expected if dt not in closed],used_evidence=used,
                coverage='PLANNED_PLUS_EXPLICIT_CASES_ONLY; NOT_EXHAUSTIVE')
