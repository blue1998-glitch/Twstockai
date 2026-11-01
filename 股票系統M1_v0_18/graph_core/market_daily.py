"""Official bulk daily intake, immutable history and isolated graph-core batches.

Raw data/results must stay outside Git. No strategy or source authentication.
"""
import argparse
from collections import Counter
from datetime import date,datetime,timezone
from decimal import Decimal,Context,localcontext,ROUND_HALF_EVEN
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import resource
import sys
import time
from urllib.request import urlopen
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from graph_core.core import analyze,fingerprint
from product_candidate.build import publish_immutable
from rotation_research.store import Journal
from contracts import validate_candles

VERSION='official-market-daily/0.4'
URLS={
 'twse-universe.json':'https://openapi.twse.com.tw/v1/opendata/t187ap03_L',
 'tpex-universe.json':'https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O',
 'twse-daily.json':'https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL',
 'tpex-daily.json':'https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes',
 'TWSE-classification.html':'https://isin.twse.com.tw/isin/C_public.jsp?strMode=2',
 'TPEX-classification.html':'https://isin.twse.com.tw/isin/C_public.jsp?strMode=4'}


def digest(raw):return hashlib.sha256(raw).hexdigest()
def encode(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def outside(path):
    p=Path(path).resolve()
    if p.is_relative_to(ROOT.parent.resolve()):raise ValueError('Real market IO inside Git refused')
    return p


def day(raw):
    s=str(raw).strip().replace('/','').replace('-','')
    if len(s)==7:s=str(int(s[:3])+1911)+s[3:]
    if len(s)!=8:raise ValueError('Unrecognized official date')
    return date.fromisoformat(s[:4]+'-'+s[4:6]+'-'+s[6:]).isoformat()


class Table(HTMLParser):
    def __init__(self):super().__init__();self.rows=[];self.row=[];self.cell=None
    def handle_starttag(self,t,a):
        if t=='tr':self.row=[]
        if t in ('td','th'):self.cell=''
    def handle_data(self,d):
        if self.cell is not None:self.cell+=d
    def handle_endtag(self,t):
        if t in ('td','th') and self.cell is not None:self.row.append(self.cell.strip());self.cell=None
        if t=='tr' and self.row:self.rows.append(self.row)


def classify(companies,html,market,as_of):
    text=html.decode('cp950',errors='replace');p=Table();p.feed(text)
    if 'CFICode' not in text:raise ValueError('No official CFI header')
    observed=re.search(r'最近更新日期:(\d{4}/\d{2}/\d{2})',text)
    if not observed:raise ValueError('No classification observation date')
    key='公司代號' if market=='TWSE' else 'SecuritiesCompanyCode'
    name='公司簡稱' if market=='TWSE' else 'CompanyAbbreviation'
    registry={}
    for c in companies:
        code=c[key].strip()
        if code in registry:raise ValueError('Duplicate company registry identity')
        registry[code]=c
    seen=set();receipts=[];members=[]
    for r in p.rows:
        if len(r)!=7 or r[5]=='CFICode':continue
        code=r[0].split()[0]
        if code in seen:raise ValueError('Duplicate security classification')
        seen.add(code);cfi=r[5];state='EXCLUDED_NON_ORDINARY'
        if r[3] not in (('上市','上市臺灣創新板') if market=='TWSE' else ('上櫃',)):state='CLASSIFICATION_MARKET_MISMATCH'
        elif cfi.startswith('ES'):
            state='ORDINARY' if code in registry else 'ORDINARY_MISSING_COMPANY_METADATA'
            if day(r[2])>as_of:state='NOT_YET_LISTED_AT_SOURCE_DATE'
            elif state.startswith('ORDINARY'):
                members.append(dict(code=code,name=registry[code][name].strip() if code in registry else r[0],market=market,
                    isin=r[1],cfi=cfi,listed_at=day(r[2]),registry_present=code in registry))
        elif not cfi:state='CLASSIFICATION_UNKNOWN'
        receipts.append(dict(code=code,cfi=cfi,status=state,market_label=r[3]))
    for code in sorted(registry.keys()-seen):receipts.append(dict(code=code,cfi=None,status='COMPANY_WITHOUT_SECURITY_CLASSIFICATION'))
    return dict(market=market,observed_at=day(observed[1]),historical_membership_at_as_of='UNKNOWN',members=members,receipts=receipts,
                classification_counts=dict(Counter(r['status'] for r in receipts)),company_records=len(companies))


def quote_map(rows,market):
    code_key='Code' if market=='TWSE' else 'SecuritiesCompanyCode'
    dates={day(r['Date']) for r in rows}
    if len(dates)!=1:raise ValueError('Bulk source mixed/empty dates')
    indexed={}
    for r in rows:
        code=r[code_key].strip()
        if code in indexed:raise ValueError('Duplicate daily quote identity')
        indexed[code]=r
    return next(iter(dates)),indexed


def candle(r,market):
    fields=('OpeningPrice','HighestPrice','LowestPrice','ClosingPrice','TradeVolume') if market=='TWSE' else ('Open','High','Low','Close','TradingShares')
    vals=[str(r[k]).strip().replace(',','') for k in fields]
    volume=Decimal(vals[-1])
    if not volume.is_finite() or volume<0 or volume!=volume.to_integral_value():raise ValueError('Invalid native reported share volume')
    if volume==0:return None,'NO_TRADE_REPORTED_ZERO_VOLUME'
    if any(v in ('','--','---','----','－') for v in vals[:4]):return None,'NO_VALID_CLOSE_SUSPENSION_NOT_AUTHENTICATED'
    bar=dict(date=day(r['Date']),open=vals[0],high=vals[1],low=vals[2],close=vals[3],volume_shares_scaled=vals[4])
    validate_candles([bar])
    return bar,None


def capture(destination):
    out=outside(destination);receipt=[]
    for name,url in URLS.items():
        try:
            with urlopen(url,timeout=35) as response:raw=response.read()
            sha=digest(raw);publish_immutable(out/'raw'/sha,raw)
            receipt.append(dict(name=name,url=url,sha256=sha,bytes=len(raw),fetched_at=datetime.now(timezone.utc).isoformat(),status='RECEIVED'))
        except Exception as e:
            receipt.append(dict(name=name,url=url,status='SOURCE_FAILURE',error=type(e).__name__+': '+str(e)))
        time.sleep(1)  # six bounded official requests, no retries/parameter probing
    key=digest(encode(receipt));publish_immutable(out/'captures'/(key+'.json'),encode(receipt))
    return key


def import_saved(source,destination):
    source=outside(source);out=outside(destination);receipt=[]
    for name,url in URLS.items():
        p=source/name
        if not p.exists():receipt.append(dict(name=name,url=url,status='SOURCE_FAILURE',error='LOCAL_ORIGINAL_MISSING'));continue
        raw=p.read_bytes();sha=digest(raw);publish_immutable(out/'raw'/sha,raw)
        receipt.append(dict(name=name,url=url,sha256=sha,bytes=len(raw),status='RECEIVED',fetched_at='SEE_ORIGINAL_ACQUISITION_RECEIPT'))
    key=digest(encode(receipt));publish_immutable(out/'captures'/(key+'.json'),encode(receipt));return key


def process(root,capture_id,*,parent_run=None,correction_of=None,correction_reason=None,now=None):
    root=outside(root);started=time.monotonic();journal=Journal(root/'runs')
    if not re.fullmatch('[a-f0-9]{64}',capture_id):raise ValueError('Invalid capture identity')
    receipt=json.loads((root/'captures'/(capture_id+'.json')).read_text())
    if digest(encode(receipt))!=capture_id:raise ValueError('Capture receipt fingerprint changed')
    if len(receipt)!=len(URLS) or {r['name'] for r in receipt}!=set(URLS):raise ValueError('Complete unique source receipt required')
    # A local missing/corrupt original is not an identical-source re-run. Preserve
    # the old journal, refuse this RUN, and never repair from a cached result.
    for record in receipt:
        if record['url']!=URLS[record['name']]:raise ValueError('Unexpected source URL')
        if record['status']=='RECEIVED':
            if not re.fullmatch('[a-f0-9]{64}',record['sha256']):raise ValueError('Invalid raw source fingerprint')
            path=root/'raw'/record['sha256']
            if not path.is_file() or digest(path.read_bytes())!=record['sha256']:
                raise ValueError('Stored source fingerprint mismatch; old results preserved')
    signature={r['name']:r.get('sha256',r['status']) for r in receipt}
    producer_sha=digest(Path(__file__).read_bytes());engine_sha=digest((ROOT/'graph_core/core.py').read_bytes())
    parent=journal.read(parent_run)['value'] if parent_run else None
    if parent and (parent['version']!=VERSION or parent.get('producer_sha256')!=producer_sha or parent.get('engine_sha256')!=engine_sha):
        raise ValueError('Cross-producer continuation NOT_IMPLEMENTED; old records remain READ-only')
    if parent and parent['sources']==signature:return dict(id=parent_run,reused=True,summary=parent['summary'],new_core_calls=0)
    def read(name):
        record=next(r for r in receipt if r['name']==name)
        if record['status']!='RECEIVED':raise ValueError(record.get('error','SOURCE_FAILURE'))
        raw=(root/'raw'/record['sha256']).read_bytes()
        if digest(raw)!=record['sha256']:raise ValueError('Raw source fingerprint changed')
        return raw
    markets={};maps={};failures={};dates=[]
    for market,lower in [('TWSE','twse'),('TPEX','tpex')]:
        try:dt,maps[market]=quote_map(json.loads(read(lower+'-daily.json')),market);dates.append(dt)
        except Exception as e:failures[market]=str(e)
    if not dates:raise ValueError('No dated official batch available')
    if len(set(dates))!=1:raise ValueError('Markets have different data dates; no common session')
    as_of=dates[0];today=(now or datetime.now(ZoneInfo('Asia/Taipei'))).date().isoformat()
    if as_of>=today:raise ValueError('Completion publication not proven; accept prior closed date only')
    if date.fromisoformat(as_of).weekday()>=5:raise ValueError('Weekend date requires explicit official session evidence')
    if parent and as_of<parent['as_of']:raise ValueError('Do not append older source to current history')
    if parent and as_of==parent['as_of'] and (correction_of!=parent_run or not correction_reason):raise ValueError('Same-date source revision requires explicit correction_of and reason')
    for market,lower in [('TWSE','twse'),('TPEX','tpex')]:
        try:markets[market]=classify(json.loads(read(lower+'-universe.json')),read(market+'-classification.html'),market,as_of)
        except Exception as e:failures[market+'-UNIVERSE']=str(e)
    members=[m for v in markets.values() for m in v['members']]
    identities=[m['market']+':'+m['code'] for m in members]
    if len(identities)!=len(set(identities)):raise ValueError('Duplicate universe member')
    run_id='fm1-'+digest(encode(dict(version=VERSION,producer_sha256=producer_sha,engine_sha256=engine_sha,sources=signature,parent=parent_run,correction_of=correction_of,reason=correction_reason)))
    try:
        saved=journal.read(run_id)['value'];return dict(id=run_id,reused=True,summary=saved['summary'],new_core_calls=0)
    except FileNotFoundError:pass
    histories=Journal(root/'histories');results=Journal(root/'results');outcomes=[];calls=0
    previous={s['identity']:s for s in parent['stocks']} if parent else {}
    expected=sorted(set((parent['observed_sessions'] if parent else [])+[as_of]))
    for member in members:
        identity=member['market']+':'+member['code'];old=previous.get(identity);bars=[];breaks=[]
        row=dict(member,identity=identity,as_of=as_of,status=None,history_key=None,result_key=None,
                 historical_available_at='UNKNOWN',corporate_action_coverage='UNVERIFIED',primary_pressure_id=None,classification_quality='NOT_VALIDATED',
                 data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,policy_authorized=False,live_execution_authorized=False)
        if old and old.get('history_key'):
            h=histories.read(old['history_key'])['value'];bars=h['bars'];breaks=h['basis_break_dates']
            row['history_key']=old['history_key']
        stage='DATA_QUALITY_FAILURE'
        try:
            if member['market'] in failures:row['status']='SOURCE_FAILURE';row['reason']=failures[member['market']]
            elif member['code'] not in maps[member['market']]:row['status']='MISSING_QUOTE';row['reason']='Registry ordinary stock absent; not assumed no trade or delisted'
            else:
                raw=maps[member['market']][member['code']];bar,reason=candle(raw,member['market'])
                if reason:row['status']=reason;row['reason']=reason
                else:
                    existing=next((b for b in bars if b['date']==as_of),None)
                    if existing and existing!=bar and correction_of!=parent_run:raise ValueError('Historical same-day price conflict')
                    bars=[b for b in bars if b['date']!=as_of]+[bar]
                    if parent and as_of>parent['as_of'] and (date.fromisoformat(as_of)-date.fromisoformat(parent['as_of'])).days>1:
                        breaks=sorted(set(breaks+[as_of]));row['continuity_qualification']='UNOBSERVED_CALENDAR_INTERVAL_RESET_NOT_CORPORATE_ACTION_CERTIFICATION'
                    change=raw.get('Change','')
                    if 'X' in change or any(w in change for w in ('除權','除息','不比價')):breaks=sorted(set(breaks+[as_of]))
                    if old and old['status'] not in ('ANALYZED_RESEARCH','INSUFFICIENT_HISTORY'):breaks=sorted(set(breaks+[as_of]))
                    payload=dict(schema_version='graph-recognition-input/0.1',context=dict(code=member['code'],exchange=member['market'],
                        source_id=fingerprint(dict(feed=VERSION,identity=identity,bars=bars)),price_basis_id=identity+'-RAW-UNVERIFIED',
                        price_mode='RAW_CANDIDATE',volume_unit='SHARES_REPORTED',source_kind='OFFICIAL_BULK_DAILY_NATIVE_SHARES',
                        corporate_action_comparability='UNVERIFIED',historical_publication_timing='UNKNOWN'),bars=bars,basis_break_dates=breaks,expected_dates=expected)
                    calls+=1;stage='CORE_FAILURE'
                    with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999)):
                        result=analyze(payload,as_of=as_of)
                    stage='STORAGE_FAILURE'
                    hk='history-'+fingerprint(dict(bars=bars,basis_break_dates=breaks)).split(':')[1]
                    histories.save(hk,dict(bars=bars,basis_break_dates=breaks));rk='result-'+result['result_id'].split(':')[1];results.save(rk,dict(input=payload,result=result))
                    row.update(history_key=hk,result_key=rk,history_records=len(bars),status='INSUFFICIENT_HISTORY' if len(bars)==1 else 'ANALYZED_RESEARCH',
                               classification_quality='NOT_VALIDATED',source_volume_field='TradeVolume' if member['market']=='TWSE' else 'TradingShares',volume_unit='NATIVE_REPORTED_SHARES',
                               source_date=as_of,missing_expected_dates=result['data_gaps']['missing_expected_dates'])
        except Exception as e:row['status']=stage;row['reason']=type(e).__name__+': '+str(e)
        outcomes.append(row)
    removed=[dict(identity=k,status='ABSENT_FROM_CURRENT_REGISTRY_NOT_PROOF_OF_DELISTING',prior=v) for k,v in previous.items() if k not in identities]
    transitions=[dict(identity=r['identity'],old_name=previous[r['identity']]['name'],new_name=r['name'],status='NAME_CHANGE_OBSERVED_NOT_IDENTITY_REISSUE_AUTHENTICATION') for r in outcomes if r['identity'] in previous and r['name']!=previous[r['identity']]['name']]
    prior_isins={r['isin']:r for r in previous.values() if r.get('isin')}
    market_changes=[dict(isin=r['isin'],old_identity=prior_isins[r['isin']]['identity'],new_identity=r['identity'],
        status='MARKET_CHANGE_OBSERVED_EFFECTIVE_DATE_AND_PRICE_CONTINUITY_UNKNOWN_HISTORY_NOT_MERGED') for r in outcomes
        if r.get('isin') in prior_isins and prior_isins[r['isin']]['market']!=r['market']]
    summary=dict(as_of=as_of,expected_by_market={m:len(markets[m]['members']) if m in markets else None for m in ('TWSE','TPEX')},
        expected=len(members),terminal_counts=dict(Counter(s['status'] for s in outcomes)),actual_core_calls=calls,
        processed=len(outcomes),all_known_members_have_terminal=len(outcomes)==len(members),both_market_universes_read=len(markets)==2,
        both_market_quotes_read=len(maps)==2,universe_historical_qualification='UNKNOWN_CURRENT_SNAPSHOT_NOT_HISTORICAL_MEMBERSHIP',
        source_failures=failures,wall_seconds=time.monotonic()-started,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scheduling='NOT_ENABLED_NO_VERIFIED_PERSISTENT_PRIVATE_RUNTIME',fixed_android_url='NOT_DEPLOYED',status='PARTIAL')
    journal.save(run_id,dict(version=VERSION,producer_sha256=producer_sha,engine_sha256=engine_sha,as_of=as_of,sources=signature,capture_id=capture_id,parent_run=parent_run,
        correction_of=correction_of,correction_reason=correction_reason,observed_sessions=expected,markets=markets,
        stocks=outcomes,removed_registry_entries=removed,name_changes=transitions,market_changes=market_changes,summary=summary))
    return dict(id=run_id,reused=False,summary=summary,new_core_calls=calls)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--capture');p.add_argument('--fetch',action='store_true');p.add_argument('--import-saved');p.add_argument('--parent-run');p.add_argument('--correction-of');p.add_argument('--correction-reason');a=p.parse_args()
    cap=capture(a.root) if a.fetch else import_saved(a.import_saved,a.root) if a.import_saved else a.capture
    if not cap:raise ValueError('Explicit fetch/capture/import required')
    print(json.dumps(process(a.root,cap,parent_run=a.parent_run,correction_of=a.correction_of,correction_reason=a.correction_reason),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
