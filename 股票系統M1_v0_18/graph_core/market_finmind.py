"""FM3: rate-limited individual Free histories into the existing Journal/core.

All raw inputs, results and previews stay outside every Git working tree.
No paid bulk API, token, recognition rule or new database is introduced.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Context, localcontext, ROUND_HALF_EVEN
import json
import inspect
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from graph_core.market_daily import ROOT, Journal, encode, digest, classify, quote_map, candle, URLS
from graph_core.finmind_run import external_path, _parse, ENDPOINT
from graph_core.finmind_adapter import history_payload, IntakeError
from graph_core.core import analyze, VERSION as CORE_VERSION
from graph_core.market_preview import source_segment_ma
from product_candidate.build import publish_immutable
from product_candidate.macd import macd

VERSION = 'finmind-market-history/0.1'


class Pause(RuntimeError):
    pass


def capture_key(parameters):
    return digest(encode(dict(endpoint=ENDPOINT, parameters=parameters)))


class FreeSource:
    """Immutable per-request reservations: crash/denial never causes a re-fetch.

    240/hour is a conservative local budget below documented 300/hour without
    token. It cannot account for unrelated clients sharing the provider's IP.
    """
    def __init__(self, root, limit=240, clock=time.time, transport=urlopen, delay=1):
        self.root = external_path(root)
        if not 1 <= limit <= 240: raise ValueError('Conservative unauthenticated limit is 1..240')
        self.limit, self.clock, self.transport, self.delay = limit, clock, transport, delay
        self.receipts = Journal(self.root/'source-receipts')
        self.slots = Journal(self.root/'source-slots')
        self.new_requests = 0

    def obtain(self, parameters):
        if parameters.get('dataset') not in ('TaiwanStockPrice','TaiwanStockTradingDate') or set(parameters)-{'dataset','data_id','start_date','end_date'}:
            raise ValueError('Only documented anonymous Free individual histories/calendar allowed')
        if parameters['dataset']=='TaiwanStockPrice' and not parameters.get('data_id'):
            raise ValueError('Paid whole-market route refused')
        key = capture_key(parameters)
        try:
            receipt = self.receipts.read(key)['value']
            if receipt['parameters'] != parameters: raise ValueError('Source receipt binding conflict')
            if receipt['status'] != 'RECEIVED': raise Pause(receipt['status'])
            raw = (self.root/'source-raw'/receipt['sha256']).read_bytes()
            if digest(raw) != receipt['sha256']: raise ValueError('Raw source fingerprint mismatch')
            return _parse(raw), receipt
        except FileNotFoundError:
            if self.receipts.path(key).exists(): raise Pause('SOURCE_DEPENDENCY_MISSING_NO_REPAIR')
        if self.slots.path(key).exists(): raise Pause('ACQUISITION_UNKNOWN_NO_AUTOMATIC_RETRY')
        now = self.clock()
        used = [json.loads(p.read_text())['value'] for p in self.slots.root.glob('*.json')]
        if sum(s['epoch'] > now-3600 for s in used) >= self.limit:
            raise Pause('LOCAL_FREE_HOURLY_BUDGET_EXHAUSTED')
        self.slots.save(key, dict(epoch=now, parameters=parameters, endpoint=ENDPOINT))
        self.new_requests += 1
        receipt = dict(parameters=parameters, endpoint=ENDPOINT,
                       requested_at=datetime.fromtimestamp(now, timezone.utc).isoformat(), attempts=1)
        try:
            with self.transport(ENDPOINT+'?'+urlencode(parameters), timeout=60) as r:
                raw = r.read(16000001); receipt['http_status'] = r.status
            if len(raw) > 16000000: raise ValueError('RESPONSE_SIZE_LIMIT')
            publish_immutable(self.root/'source-raw'/digest(raw), raw)
            response = _parse(raw)
            receipt.update(sha256=digest(raw), bytes=len(raw),
                           completed_at=datetime.now(timezone.utc).isoformat(), api_status=response.get('status'),
                           status='RECEIVED' if response.get('status') == 200 else 'PROVIDER_API_REFUSED')
            self.receipts.save(key, receipt)
            if receipt['status'] != 'RECEIVED': raise Pause('PROVIDER_API_REFUSED')
            return response, receipt
        except (HTTPError, URLError, TimeoutError) as e:
            receipt.update(status='PROVIDER_OR_NETWORK_REFUSED', http_status=getattr(e, 'code', None),
                           error_type=type(e).__name__)
            self.receipts.save(key, receipt)
            raise Pause('PROVIDER_OR_NETWORK_REFUSED_NO_RETRY') from None
        finally:
            if self.delay: time.sleep(self.delay)

    def adopt(self, raw, receipt):
        """Explicit already-captured pilot, including its quota reservation."""
        params = receipt['parameters']; key = capture_key(params)
        if (receipt.get('http_status') != 200 or digest(raw) != receipt['sha256'] or
                receipt['url'] != ENDPOINT+'?'+urlencode(params)):
            raise ValueError('Pilot capture binding mismatch')
        self.slots.save(key, dict(epoch=datetime.fromisoformat(receipt['requested_at']).timestamp(),
                                 parameters=params, endpoint=ENDPOINT))
        publish_immutable(self.root/'source-raw'/digest(raw), raw)
        self.receipts.save(key, dict(parameters=params, endpoint=ENDPOINT, attempts=1,
            http_status=200, requested_at=receipt['requested_at'], completed_at=receipt['completed_at'],
            sha256=digest(raw), bytes=len(raw), status='RECEIVED', api_status=_parse(raw).get('status')))


def reference(root, capture_id):
    root = external_path(root)
    receipts = json.loads((root/'captures'/(capture_id+'.json')).read_text())
    if digest(encode(receipts)) != capture_id or {r['name'] for r in receipts} != set(URLS):
        raise ValueError('Official reference capture binding mismatch')
    raw = {}
    for r in receipts:
        if r['status'] != 'RECEIVED' or r['url'] != URLS[r['name']]: raise ValueError('Official source missing')
        b = (root/'raw'/r['sha256']).read_bytes()
        if digest(b) != r['sha256']: raise ValueError('Official raw source mismatch')
        raw[r['name']] = b
    stocks, markets, dates = [], {}, []
    for market, lower in [('TWSE', 'twse'), ('TPEX', 'tpex')]:
        as_of, _ = quote_map(json.loads(raw[lower+'-daily.json']), market); dates.append(as_of)
        markets[market] = classify(json.loads(raw[lower+'-universe.json']), raw[market+'-classification.html'], market, as_of)
        for m in markets[market]['members']:
            stocks.append(dict(m, identity=market+':'+m['code'], as_of=as_of))
    if len(set(dates)) != 1: raise ValueError('No common official reference day')
    value = dict(as_of=dates[0], stocks=stocks, markets=markets, capture_id=capture_id,
                 source_receipts=receipts, summary=dict(expected=len(stocks),
                 expected_by_market={m: len(v['members']) for m,v in markets.items()}))
    key = 'fm3-reference-'+digest(encode(value)); Journal(root/'runs').save(key, value)
    return key


def observed_calendar(source, start, as_of):
    response, receipt = source.obtain(dict(dataset='TaiwanStockTradingDate'))
    dates = [r['date'] for r in response['data']]
    from datetime import date
    for d in dates: date.fromisoformat(d)
    if dates != sorted(set(dates)): raise ValueError('Calendar order/duplicates invalid')
    dates = [d for d in dates if start <= d <= as_of]
    if not dates or dates[-1] != as_of: raise ValueError('Calendar does not cover exact official date')
    return dates, receipt


def retained_warnings(code, start, end):
    """Reuse known source-role breaks, without inferring complete actions."""
    path = ROOT/'graph_core_chart/mg3_20261101/source-input-spec.json'
    spec = json.loads(path.read_text())
    out = []
    for w in spec.get('basis_warnings', {}).get(code, []):
        day = w.get('date', w.get('effective_date'))
        if day and start <= day <= end:
            out.append(dict(date=day, source_id='retained-mg3-spec:'+digest(path.read_bytes()),
                            kind='NON_COMPARABLE_MARKER_EVENT_TYPE_UNKNOWN'))
    return out


def official_check(root, ref, member, payload):
    """Exact same-day native bulk prices/shares; no comparison across bases."""
    lower = 'twse' if member['market']=='TWSE' else 'tpex'
    rec = next(r for r in ref['source_receipts'] if r['name']==lower+'-daily.json')
    raw = (root/'raw'/rec['sha256']).read_bytes()
    if digest(raw) != rec['sha256']: raise ValueError('Official comparison source changed')
    _, rows = quote_map(json.loads(raw), member['market'])
    if member['code'] not in rows: return dict(status='OFFICIAL_ANCHOR_MISSING', matched=False)
    bar, reason = candle(rows[member['code']], member['market'])
    if reason: return dict(status=reason, matched=False)
    actual = payload['bars'][-1]
    from decimal import Decimal
    fields = {k: Decimal(actual[k]) == Decimal(bar[k]) for k in
              ['open','high','low','close','volume_shares_scaled']}
    return dict(status='MATCH' if all(fields.values()) else 'SOURCE_PRICE_OR_NATIVE_VOLUME_MISMATCH',
                matched=all(fields.values()), fields=fields)


def analyze_stock(root, ref, member, source, start, calendar, calendar_receipt):
    end = ref['as_of']; start = max(start, member['listed_at'])
    params = dict(dataset='TaiwanStockPrice', data_id=member['code'], start_date=start, end_date=end)
    response, receipt = source.obtain(params)
    job = dict(schema_version='finmind-history-request/0.1', member=member,
               start_date=start, end_date=end, as_of=end, retrieved_at=receipt['completed_at'],
               expected_dates=[d for d in calendar if start<=d<=end],
               basis_warnings=retained_warnings(member['code'], start, end))
    payload = history_payload(response, job)
    cross = official_check(root, ref, member, payload)
    if not cross['matched']: return dict(status='SOURCE_COMPARISON_REFUSED', comparison=cross), None
    # Daily corporate-action markers are evidence of a reset, not event-type certification.
    lower = 'twse' if member['market']=='TWSE' else 'tpex'
    rec = next(r for r in ref['source_receipts'] if r['name']==lower+'-daily.json')
    _, official = quote_map(json.loads((root/'raw'/rec['sha256']).read_bytes()), member['market'])
    change = official[member['code']].get('Change','')
    if 'X' in change or any(x in change for x in ['除權','除息','不比價']):
        payload['basis_break_dates'] = sorted(set(payload['basis_break_dates']+[end]))
    with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999)):
        result = analyze(payload, as_of=end)
        resets = [i for i,b in enumerate(payload['bars']) if b['date'] in result['data_gaps']['basis_resets']]
        indicators = dict(macd=macd([b['close'] for b in payload['bars']],resets=resets),
            moving_averages=source_segment_ma(payload['bars'],resets),
            role='FINMIND_SEGMENTED_EXISTING_FORMULAS_NOT_RETAINED_PARENT',
            version='fm3-segment-indicators/0.1',reset_dates=result['data_gaps']['basis_resets'])
    stored = dict(input=payload,result=result,indicators=indicators,
        acquisition=receipt,calendar_acquisition=calendar_receipt,request=job,official_comparison=cross)
    hk='history-'+digest(encode(dict(bars=payload['bars'],basis_break_dates=payload['basis_break_dates'])))
    rk='fm3-result-'+digest(encode(stored))
    Journal(root/'histories').save(hk,dict(bars=payload['bars'],basis_break_dates=payload['basis_break_dates']))
    Journal(root/'results').save(rk,stored)
    complete = len(payload['bars'])>1 and indicators['macd'][-1]['histogram'] is not None
    return dict(status='ANALYZED_FINMIND_HISTORY' if complete else 'INSUFFICIENT_HISTORY',
        history_records=len(payload['bars']),history_key=hk,result_key=rk,
        missing_expected_dates=len(result['data_gaps']['missing_expected_dates']),comparison=cross,
        history_source_provenance=dict(role='FINMIND_FREE_INDIVIDUAL_HISTORY_NOT_OFFICIAL_MONTHLY_OR_NATIVE_BULK',
            source_ledger_sha256=receipt['sha256'],exact_native_share_precision='API_REPORTED_INTEGER_SHARES_NOT_INDEPENDENT_ALL_DAYS_CERTIFIED',
            historical_available_at='UNKNOWN',corporate_action_comparability='UNKNOWN_NO_CROSS_BASIS_CERTIFICATION',
            retained_source_gaps=dict(calendar_status='FINMIND_OBSERVED_SESSIONS_NOT_OFFICIAL_COMPLETE_CALENDAR_CERTIFICATION',
                actions_coverage='UNKNOWN',historical_publication_timing='UNKNOWN'))), stored


def _run(root, reference_run, start, *, limit=240, codes=None):
    root=external_path(root); source=FreeSource(root,limit=limit)
    ref=Journal(root/'runs').read(reference_run)['value']
    signature=dict(version=VERSION,source_glue=digest(Path(__file__).read_bytes()),
        adapter=digest((ROOT/'graph_core/finmind_adapter.py').read_bytes()),
        engine=digest((ROOT/'graph_core/core.py').read_bytes()),
        indicator_glue=digest(inspect.getsource(source_segment_ma).encode()),macd_glue=digest(inspect.getsource(macd).encode()),
        reference=reference_run,start=start)
    batch='fm3-'+digest(encode(signature));checkpoints=Journal(root/'checkpoints')
    calendar, cr=observed_calendar(source,start,ref['as_of'])
    members=ref['stocks'] if codes is None else [s for s in ref['stocks'] if s['code'] in codes]
    if codes is not None and {s['code'] for s in members}!=set(codes): raise ValueError('Requested code absent from official ordinary reference')
    outcomes=[];calls=0;pause=None
    for m in members:
        row=dict(m,status='HISTORY_NOT_YET_REQUESTED',history_records=0,history_key=None,result_key=None,
            historical_available_at='UNKNOWN',classification_quality='NOT_VALIDATED',primary_pressure_id=None,
            data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,
            policy_authorized=False,live_execution_authorized=False)
        key=batch+'-'+m['identity'].replace(':','-')
        try:
            if checkpoints.path(key).exists():
                saved=checkpoints.read(key)['value']
                if saved['signature']!=signature or saved['stock']['identity']!=row['identity']:raise ValueError('Checkpoint binding mismatch')
                row=saved['stock']
                if row.get('result_key'):
                    result=Journal(root/'results').read(row['result_key'])['value'];h=Journal(root/'histories').read(row['history_key'])['value']
                    if h['bars']!=result['input']['bars'] or result['input']['context']['code']!=row['code']:raise ValueError('Checkpoint dependency conflict')
                    if row['result_key']!='fm3-result-'+digest(encode(result)):
                        raise ValueError('Saved full result fingerprint changed')
                    if result['input']['context']['exchange']!=row['market']:
                        raise ValueError('Saved result market mismatch')
                    rr=source.receipts.read(capture_key(result['acquisition']['parameters']))['value']
                    if rr!=result['acquisition'] or rr['parameters']['data_id']!=row['code']:
                        raise ValueError('Saved acquisition changed')
                    if digest((root/'source-raw'/rr['sha256']).read_bytes())!=rr['sha256']:raise ValueError('Checkpoint raw source changed')
                outcomes.append(row);continue
            if pause:row.update(status='RATE_OR_PROVIDER_DEFERRED',reason=pause)
            else:
                try:
                    update,stored=analyze_stock(root,ref,m,source,start,calendar,cr);row.update(update)
                    if stored:calls+=1
                except Pause as e:pause=str(e);row.update(status='RATE_OR_PROVIDER_DEFERRED',reason=pause)
                except IntakeError as e:row.update(status='HISTORY_UNAVAILABLE' if str(e)=='HISTORY_UNAVAILABLE' else 'MISSING_ANCHOR_QUOTE' if str(e)=='MISSING_ANCHOR_QUOTE' else 'DATA_QUALITY_REFUSED',reason=str(e))
                except Exception as e:row.update(status='STOCK_SOURCE_OR_CORE_FAILURE',reason=type(e).__name__)
            if row['status']!='RATE_OR_PROVIDER_DEFERRED':checkpoints.save(key,dict(signature=signature,stock=row))
        except Exception as e:row.update(status='CHECKPOINT_DEPENDENCY_REFUSED',reason=type(e).__name__)
        outcomes.append(row)
    counts=dict(Counter(s['status'] for s in outcomes))
    summary=dict(status='PARTIAL',as_of=ref['as_of'],expected=ref['summary']['expected'],processed=len(outcomes),
        expected_by_market=ref['summary']['expected_by_market'],terminal_counts=counts,
        current_reference_observation='CURRENT_OFFICIAL_SNAPSHOT_NOT_HISTORICAL_UNIVERSE_CERTIFICATION',
        analyzed_history=counts.get('ANALYZED_FINMIND_HISTORY',0),charts=sum(bool(s.get('result_key')) for s in outcomes),
        current_run_core_calls=calls,current_run_api_requests=source.new_requests,pause_reason=pause,
        free_hourly_budget=limit,documented_unauthenticated_limit=300,requested_start=start,
        data_qualified=False,policy_authorized=False,primary_pressure_id=None,
        fixed_android_url='NOT_DEPLOYED',storage_persistence='UNKNOWN')
    # Each progressively expanded snapshot is immutable; never overwrite earlier runs.
    rid=batch+'-'+digest(encode(dict(outcomes=outcomes,core_calls=calls,api_requests=source.new_requests)))[:16]
    Journal(root/'runs').save(rid,dict(version=VERSION,as_of=ref['as_of'],sources=signature,
        reference_current_run=reference_run,stocks=outcomes,summary=summary,observed_sessions=calendar))
    return dict(id=rid,summary=summary,new_core_calls=calls)


def run(root, reference_run, start, *, limit=240, codes=None):
    root=external_path(root);root.mkdir(mode=0o700,parents=True,exist_ok=True)
    lock=root/'fm3-writer.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        os.write(fd,str(os.getpid()).encode())
        return _run(root,reference_run,start,limit=limit,codes=codes)
    finally:
        os.close(fd);lock.unlink()


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--reference-run',required=True)
    p.add_argument('--start',required=True);p.add_argument('--limit',type=int,default=240);p.add_argument('--codes',nargs='*')
    a=p.parse_args();print(json.dumps(run(a.root,a.reference_run,a.start,limit=a.limit,codes=a.codes),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
