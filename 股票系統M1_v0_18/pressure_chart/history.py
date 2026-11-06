"""Explicit free official monthly intake; create-only files, no database or repair.
A blocked host stops that host's requests. Retained responses are verified and
reused. No invented sessions or company actions. TLS/proxy settings stay intact.
"""
import argparse
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from contracts import validate_candles, fingerprint
from source_audit import parse_twse_month, planned_dates, apply_evidenced_closures
from product_candidate.build import publish_immutable

VERSION='official-history-intake/0.1'
STOCKS={'1101':'TWSE','2884':'TWSE','6488':'TPEX','8069':'TPEX'}


def months(start,end):
    a=date.fromisoformat(start).replace(day=1);last=date.fromisoformat(end).replace(day=1)
    if a>last:raise ValueError('Start after end')
    while a<=last:
        yield a.strftime('%Y-%m')
        a=date(a.year+1,1,1) if a.month==12 else date(a.year,a.month+1,1)


def url_for(code,month):
    if code not in STOCKS or not re.fullmatch(r'\d{4}-\d{2}',month):raise ValueError('Explicit supported identity required')
    year,mon=map(int,month.split('-'));date(year,mon,1)
    if STOCKS[code]=='TWSE':return 'https://www.twse.com.tw/exchangeReport/STOCK_DAY?'+urllib.parse.urlencode(dict(response='json',date=month.replace('-','')+'01',stockNo=code))
    return 'https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock?'+urllib.parse.urlencode(dict(date=month.replace('-','/')+'/01',code=code,response='json'))


def parse_month(payload,code,month):
    year,mon=map(int,month.split('-'))
    if STOCKS[code]=='TWSE':
        # Keep explicit zero-turnover/no-price rows as evidence, never zero-price
        # candles. Mixed missing OHLC or positive turnover still fail closed.
        filtered=dict(payload);filtered['data']=[]
        fields=payload.get('fields',[])
        for row in payload.get('data',[]):
            r=dict(zip(fields,row));prices=[r.get(k) for k in ('開盤價','最高價','最低價','收盤價')]
            if all(str(x).strip()=='--' for x in prices) and str(r.get('成交股數')).replace(',','')=='0' and str(r.get('成交筆數')).replace(',','')=='0':continue
            filtered['data'].append(row)
        return parse_twse_month(filtered,code=code,year=year,month=mon)
    if payload.get('code')!=code or payload.get('date')!=month.replace('-','')+'01' or str(payload.get('stat')).lower()!='ok':
        raise ValueError('TPEX identity/month/status mismatch')
    tables=payload.get('tables',[])
    if len(tables)!=1:raise ValueError('Exactly one authenticated monthly table required')
    t=tables[0]
    if not re.search(r'(?<!\d)'+re.escape(code)+r'(?!\d)',t.get('subtitle','')) or f'{year-1911}年{mon:02d}月' not in t.get('subtitle',''):
        raise ValueError('TPEX subtitle mismatch')
    unit=payload.get('flagField');field='成交張數' if unit=='張數' else '成交仟股' if unit=='仟股' else None
    if field is None or t.get('fields')!=['日 期',field,'成交仟元','開盤','最高','最低','收盤','漲跌','筆數']:
        raise ValueError('Unsupported TPEX explicit volume unit/fields')
    rows=[]
    for raw in t.get('data',[]):
        if len(raw)!=9:raise ValueError('TPEX row width')
        y,m,d=map(int,raw[0].split('/'));day=date(y+1911,m,d)
        if (day.year,day.month)!=(year,mon):raise ValueError('Row outside requested month')
        vol=Decimal(raw[1].replace(',',''))
        if not vol.is_finite() or vol<0 or vol*1000!=(vol*1000).to_integral_value():raise ValueError('Reported volume cannot map exactly to shares')
        if all(str(x).strip()=='--' for x in raw[3:7]) and vol==0 and str(raw[8]).replace(',','')=='0':continue
        rows.append(dict(date=day.isoformat(),volume_shares_scaled=format(vol*1000,'f'),
            **{k:raw[i].replace(',','') for i,k in enumerate(('open','high','low','close'),3)}))
    if not rows:raise ValueError('Empty month is not certified no-trade history')
    validate_candles(rows);return rows


def retained():
    result={}
    for code in ('1101','2884'):
        for mon in range(1,10):
            p=ROOT/'data_audit/raw'/f'{code}_2026{mon:02d}.json';b=p.read_bytes();meta=json.loads(p.with_name(p.name+'.meta.json').read_text())
            if hashlib.sha256(b).hexdigest()!=meta['sha256']:raise ValueError('Retained TWSE SHA mismatch')
            result[(code,f'2026-{mon:02d}')]=(b,dict(url=meta['url'],fetched_at_utc=meta['fetched_at_utc'],sha256=meta['sha256'],origin=str(p.relative_to(ROOT))))
    archive=ROOT/'upstream/M0_7_長期日線與還原候選_v0_2.zip'
    with zipfile.ZipFile(archive) as z:
        for n in z.namelist():
            match=re.search(r'(6488|8069)_(\d{4}-\d{2})_meta.json$',n)
            if not match:continue
            code,month=match.groups();b=z.read(n.replace('_meta.json','.json'));meta=json.loads(z.read(n))
            if hashlib.sha256(b).hexdigest()!=meta['sha256']:raise ValueError('Retained TPEX SHA mismatch')
            result[(code,month)]=(b,dict(url=meta['url'],fetched_at_utc=meta['requested_at'],sha256=meta['sha256'],origin=str(archive.relative_to(ROOT))+'!'+n.replace('_meta.json','.json')))
    return result


def fetch(url):
    timestamp=datetime.now(timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(url,timeout=25) as response:
            b=response.read();return b,dict(url=url,fetched_at_utc=timestamp,http_status=response.status,final_url=response.url,sha256=hashlib.sha256(b).hexdigest())
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        return None,dict(url=url,fetched_at_utc=timestamp,error=repr(e),status='BLOCKED_OR_UNAVAILABLE')


def collect(out,start,end,network=False,cache=None,request_interval=3,calendar_dir=None):
    date.fromisoformat(start);date.fromisoformat(end)
    if end>=datetime.now(timezone(timedelta(hours=8))).date().isoformat():raise ValueError('Closed-day intake requires end before the current Taiwan date')
    out=Path(out)
    # Output is always a NEW leaf, so an interrupted capture can never overwrite.
    if out.exists():raise ValueError('Choose a fresh intake directory; reuse captures with --cache')
    out.mkdir(parents=True)
    existing=retained();reports=[];series=[];blocked_hosts={};calendar_evidence=[];last_request={}
    if cache:
        for p in Path(cache).glob('raw/*_meta.json'):
            m=json.loads(p.read_text());code,month=p.name.removesuffix('_meta.json').split('_');b=p.with_name(p.name.replace('_meta.json','.json')).read_bytes()
            if hashlib.sha256(b).hexdigest()!=m['sha256']:raise ValueError('Cache checksum mismatch')
            if urllib.parse.urlparse(m['url']).hostname!=urllib.parse.urlparse(url_for(code,month)).hostname:raise ValueError('Cache origin mismatch')
            # Content parser independently verifies stock, month and volume unit.
            parse_month(json.loads(b),code,month);existing[(code,month)]=(b,m)
    for code,exchange in STOCKS.items():
        wanted=list(months(start,end));rows=[];source_records=[];missing=[]
        # First request the newest missing month; a denied host is not hammered244 times.
        ordered=sorted(wanted,reverse=True)
        for month in ordered:
            url=url_for(code,month);host=urllib.parse.urlparse(url).hostname
            if (code,month) in existing:b,meta=existing[(code,month)];meta={**meta,'status':'VERIFIED_RETAINED_RESPONSE'}
            elif not network:missing.append(month);continue
            elif host in blocked_hosts:missing.append(month);continue
            else:
                delay=request_interval-(time.monotonic()-last_request.get(host,0))
                if delay>0:time.sleep(delay)
                b,meta=fetch(url);reports.append(dict(code=code,month=month,**meta))
                last_request[host]=time.monotonic()
                if b is None:blocked_hosts[host]=meta;missing.append(month);continue
                if urllib.parse.urlparse(meta['final_url']).hostname!=host:raise ValueError('Unexpected official redirect host')
            # Preserve even semantically rejected responses for diagnosis.
            publish_immutable(out/'raw'/f'{code}_{month}.json',b)
            publish_immutable(out/'raw'/f'{code}_{month}_meta.json',json.dumps(meta,ensure_ascii=False,indent=2).encode())
            try:parsed=parse_month(json.loads(b),code,month)
            except (ValueError,KeyError,TypeError) as error:
                missing.append(month);reports.append(dict(code=code,month=month,url=url,error=repr(error),status='SOURCE_SEMANTIC_REJECTION'));continue
            meta['source_volume_field']='成交股數' if exchange=='TWSE' else json.loads(b)['tables'][0]['fields'][1]
            payload=json.loads(b);fields=payload.get('fields') if exchange=='TWSE' else payload['tables'][0]['fields'];table=payload.get('data') if exchange=='TWSE' else payload['tables'][0]['data']
            price_slice=slice(3,7)
            meta['zero_turnover_no_price_source_rows']=[r for r in table if all(str(x).strip()=='--' for x in r[price_slice])]
            rows.extend(r for r in parsed if start<=r['date']<=end);source_records.append(dict(month=month,**meta))
        rows.sort(key=lambda r:r['date']);validate_candles(rows)
        if len({r['date'] for r in rows})!=len(rows):raise ValueError('Duplicate official date')
        schedules=[]
        for year in range(int(start[:4]),int(end[:4])+1):
            captured=Path(calendar_dir).resolve()/f'{exchange}_{year}.calendar.json' if calendar_dir else None
            p=captured if captured and captured.exists() else ROOT/'data_audit'/f'{exchange}_{year}_計畫開休市.json'
            if p.exists():
                if captured and p==captured:
                    raw=p.with_name(f'{exchange}_{year}.raw.json');meta=json.loads(p.with_name(f'{exchange}_{year}.meta.json').read_text())
                    if hashlib.sha256(raw.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('Calendar raw SHA mismatch')
                    from source_audit import parse_twse_holidays,parse_tpex_holidays
                    verified=(parse_twse_holidays if exchange=='TWSE' else parse_tpex_holidays)(json.loads(raw.read_bytes()),year)
                    if verified!=json.loads(p.read_text()):raise ValueError('Calendar parse mismatch')
                schedules.append(json.loads(p.read_text()));calendar_evidence.append(dict(file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        expected=[];closures=json.loads((ROOT/'data_audit/臨時休市證據.json').read_text())
        for s in schedules:
            first=max(start,f"{s['year']}-01-01");last=min(end,f"{s['year']}-12-31")
            expected.extend(apply_evidenced_closures(planned_dates([s],first,last),closures,exchange=exchange)['dates'])
        actual={r['date'] for r in rows}
        item=dict(code=code,exchange=exchange,price_mode='RAW_CANDIDATE',candles=rows,source_records=sorted(source_records,key=lambda m:m['month']),
            source_id=fingerprint(dict(code=code,exchange=exchange,candles=rows)),
            volume_unit='SHARES_REPORTED' if exchange=='TWSE' else 'NORMALIZED_SHARES_EXPLICIT_LOTS_OR_THOUSAND_SHARES',
            normalization='NATIVE_SHARE_COUNT' if exchange=='TWSE' else 'EXPLICIT_REPORTED_LOTS_OR_THOUSAND_SHARES_TIMES1000_PRESERVE_SOURCE_UNIT_PER_RESPONSE',
            actions_coverage='UNVERIFIED_NO_NEW_ACTION_AUTHENTICATION',corporate_actions=[],
            target_start=start,target_end=end,actual_start=rows[0]['date'] if rows else None,actual_end=rows[-1]['date'] if rows else None,
            missing_months=sorted(missing),known_calendar_missing_dates=sorted(set(expected)-actual),
            calendar_years_unverified=[y for y in range(int(start[:4]),int(end[:4])+1) if y not in {s['year'] for s in schedules}],
            calendar_status='PLANNED_PLUS_REVIEWED_EXCEPTIONS_ONLY_NOT_EXHAUSTIVE',historical_publication_timing='UNVERIFIED',
            listing_start='UNVERIFIED_NOT_INFERRED_FROM_NO_ROWS',status='PARTIAL_HISTORY' if missing else 'MONTH_RESPONSES_PRESENT_CALENDAR_ACTIONS_NOT_CERTIFIED')
        series.append(item)
        print(code,len(rows),'bars',len(missing),'missing monthly responses',flush=True)
    result=dict(schema_version='official-history-candidate/0.1',producer_version=VERSION,target_start=start,target_end=end,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),series=series,requests=reports,blocked_hosts=blocked_hosts,calendar_evidence=calendar_evidence,
        five_year_target='BLOCKED' if any(s['missing_months'] for s in series) else 'REQUIRES_CALENDAR_AND_ACTION_REVIEW',
        full_history_high='NOT_ESTABLISHED',physical_android='NOT_TESTED')
    publish_immutable(out/'history-candidate.json',json.dumps(result,ensure_ascii=False,indent=2).encode())
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);p.add_argument('--start',required=True);p.add_argument('--end',required=True);p.add_argument('--fetch',action='store_true');p.add_argument('--cache');p.add_argument('--calendars');a=p.parse_args()
    r=collect(a.output_dir,a.start,a.end,a.fetch,a.cache,calendar_dir=a.calendars)
    print(json.dumps(dict(status=r['five_year_target'],requests=r['requests'],series=[dict(code=s['code'],bars=len(s['candles']),start=s['actual_start'],end=s['actual_end'],missing_months=len(s['missing_months'])) for s in r['series']]),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
