"""Headless, offline comparison of reviewed cash-event research replays.

The caller supplies reviewed event provenance. This module checks identities and
arithmetic; it does not authenticate sources or certify period completeness.
Existing engines and historical outputs are never modified.
"""
from copy import deepcopy
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
import re,unicodedata
from contracts import DataError,fingerprint,number,iso_date,validate_candles,validate_events
from analysis_jobs import run_analysis_job
from structure import project_prices

SCHEMA='stock-event-replay/1.0'


def parse_contract_notice(text,*,code):
    """Parse captured PDF text without treating contract dates as stock dates."""
    s=re.sub(r'\s+','',unicodedata.normalize('NFKC',text))
    if '臺灣期貨交易所' not in s or f'公司股票代號:{code}' not in s:
        raise DataError('CONTRACT_NOTICE_IDENTITY','code','Issuer code or official heading differs')
    amt=re.search(r'每股配發([0-9.]+)元',s)
    effective=re.search(r'調整生效日:(\d+)年(\d+)月(\d+)日',s)
    published=re.search(r'發文日期:中華民國(\d+)年(\d+)月(\d+)日',s)
    doc=re.search(r'台期交字第(\d+)號',s)
    if not all([amt,effective,published,doc]):raise DataError('CONTRACT_NOTICE_FIELDS','text','Expected cash, contract date, publication date and number')
    def roc(m):return iso_date(f'{int(m[1])+1911:04d}-{int(m[2]):02d}-{int(m[3]):02d}','notice.date')
    return dict(code=code,cash_per_share=str(number(amt[1],'cash')),contract_adjustment_date=roc(effective),
                date_kind='DERIVATIVE_CONTRACT_ADJUSTMENT_DATE',document_date=roc(published),document_number=doc[1],
                stock_ex_trading_date=None,stock_reference_price=None,
                interpretation='Corroborating cash/contract evidence only; not a stock reference-price table')


def validate_reviewed_events(job,events):
    if not isinstance(job,dict) or job.get('schema_version')!='stock-analysis/1.0' or not isinstance(job.get('code'),str) or 'candles' not in job:
        raise DataError('REPLAY_JOB','job','Versioned daily base job required')
    validate_candles(job['candles']);validate_events(events)
    if not events:raise DataError('NO_REVIEWED_EVENTS','events','A comparison requires an actual reviewed event')
    dates=[c['date'] for c in job['candles']]
    for e in events:
        if e.get('code')!=job['code']:raise DataError('REPLAY_IDENTITY','events.code','Event stock differs')
        if not re.fullmatch('[0-9a-f]{64}',e.get('source_sha256','')):
            raise DataError('REPLAY_PROVENANCE','source_sha256','Reviewed source content fingerprint required')
        if e.get('formula')!='(previous_close-cash_dividend)/previous_close':
            raise DataError('UNSUPPORTED_EVENT_FORMULA','formula','Cash-only research formula required')
        dt=e['effective_date']
        if dt not in dates or dates.index(dt)==0:raise DataError('REPLAY_BASIS','effective_date','Observed event bar and previous bar required')
        prev=number(job['candles'][dates.index(dt)-1]['close'],'previous candle close')
        cash=number(e.get('cash_dividend'),'cash_dividend')
        if cash<=0 or prev<=cash or prev!=number(e.get('previous_close'),'previous_close'):
            raise DataError('REPLAY_BASIS','previous_close','Invalid cash or mismatched observed price basis')
        with localcontext() as ctx:
            ctx.prec=28;ctx.rounding=ROUND_HALF_EVEN;factor=(prev-cash)/prev
        if number(e['factor'],'factor')!=factor:
            raise DataError('REPLAY_FACTOR','factor','Factor differs from reviewed cash formula')


def make_replay_jobs(job,events):
    """No source/status upgrade; one ablation and two event-aware scenarios."""
    validate_reviewed_events(job,events)
    cases={}
    for name,mode,records in [('RAW_WITHOUT_EVENTS','RAW_CANDIDATE',[]),('RAW_WITH_EVENTS','RAW_CANDIDATE',events),
                              ('ADJUSTED_WITH_EVENTS','ADJUSTED_CANDIDATE',events)]:
        q=deepcopy(job);q['price_mode']=mode
        q['corporate_actions']=dict(records=deepcopy(records),coverage_status='CASH_ONLY_VERIFIED_SAMPLE' if records else 'UNVERIFIED')
        cases[name]=q
    return cases


def compare_replay_results(job,events,results):
    """Independent behavioral checks; failure is an error, never an approval."""
    validate_reviewed_events(job,events)
    checks=[];boundaries=[]
    def check(name,condition,**detail):
        checks.append(dict(check=name,status='PASS' if condition else 'FAIL',**detail))
    candles=job['candles'];dates=[c['date'] for c in candles]
    base=results['RAW_WITHOUT_EVENTS']['components'];raw=results['RAW_WITH_EVENTS']['components'];adj=results['ADJUSTED_WITH_EVENTS']['components']
    check('same_input_stock_and_price_records',all(r['shared_input']['code']==job['code'] and r['shared_input']['data_fingerprint']==fingerprint(candles) for r in results.values()))
    check('all_snapshots_present',all(len(r['aligned_snapshots'])==len(candles) for r in results.values()),bars=len(candles))
    first=min(e['effective_date'] for e in events);n=sum(dt<first for dt in dates)
    check('raw_snapshots_before_first_event_identical',base['structure']['snapshots'][:n]==raw['structure']['snapshots'][:n],snapshots=n)
    check('raw_ma_values_unchanged_by_events',all(a['curves']==b['curves'] for a,b in zip(base['daily_ma']['snapshots'],raw['daily_ma']['snapshots'])),snapshots=len(candles))
    check('qualification_stays_disabled',all(r['action_qualification']=='NOT_EVALUATED' and all(s['action_qualification']=='NOT_EVALUATED' for s in r['components']['structure']['snapshots']) for r in results.values()))
    for e in events:
        i=dates.index(e['effective_date']);dt=dates[i];snap=raw['structure']['snapshots'][i];before=raw['structure']['snapshots'][i-1]
        daily=snap['daily_events'];pending={p['id'] for p in before['pending']}
        cancelled={x['candidate_id'] for x in daily if x['type']=='CANDIDATE_CANCELLED_CORPORATE_ACTION'}
        active={z['id'] for z in before['zones'] if z['state']=='ACTIVE_CANDIDATE'}
        after={z['id']:z for z in snap['zones']}
        check('one_raw_boundary_per_event',sum(x['type']=='RAW_CORPORATE_ACTION_BOUNDARY' for x in daily)==1,date=dt)
        check('previous_pending_candidates_cancelled',pending==cancelled,date=dt,checked_candidates=len(pending))
        check('previous_active_zones_deactivated',all(k in after and after[k]['state']=='INACTIVE_CORPORATE_ACTION' and after[k]['invalidated_at']==dt for k in active),date=dt,checked_zones=len(active))
        next_i=min([dates.index(x['effective_date']) for x in events if x['effective_date']>dt]+[len(dates)])
        warm=raw['structure']['snapshots'][i:min(i+19,next_i)]
        check('first_19_supplied_bars_warm_up_without_candidates',all(s['event_status']=='WARMUP' and not s['pending'] for s in warm),date=dt,checked_bars=len(warm))
        if i+19<next_i:
            check('20th_supplied_bar_exits_warmup',raw['structure']['snapshots'][i+19]['event_status']!='WARMUP',date=dt,bar_date=dates[i+19])
        check('adjusted_mode_does_not_reset_raw_boundaries',not any(x['type']=='RAW_CORPORATE_ACTION_BOUNDARY' for x in adj['structure']['snapshots'][i]['daily_events']),date=dt)
        view=project_prices(candles,events,dt,'ADJUSTED_CANDIDATE')
        check('projection_never_adjusts_volume',all(p.get('volume_shares_scaled')==c.get('volume_shares_scaled') for p,c in zip(view,candles)),date=dt,rows=len(view))
        check('event_day_ohlc_keeps_current_scale',all(number(view[-1][k],k)==number(candles[i][k],k) for k in ['open','high','low','close']),date=dt)
        with localcontext() as ctx:
            ctx.prec=28;ctx.rounding=ROUND_HALF_EVEN
            before_price=number(candles[i-1]['close'],'close')*number(e['factor'],'factor')
        check('previous_observation_uses_new_factor',number(view[-2]['close'],'projected close')==before_price,date=dt)

        # Independent 5-bar SMA oracle at the event anchor, using only effective
        # factors. Round projected prices to engine precision, then sum exactly.
        prices=[]
        for c in candles[max(0,i-4):i+1]:
            with localcontext() as ctx:
                ctx.prec=28;ctx.rounding=ROUND_HALF_EVEN;f=Decimal(1)
                for a in events:
                    if c['date']<a['effective_date']<=dt:f*=number(a['factor'],'factor')
                prices.append(number(c['close'],'close')*f)
        with localcontext() as ctx:
            ctx.prec=100;total=sum(prices,Decimal(0))
            ctx.prec=28;ctx.rounding=ROUND_HALF_EVEN;expected=str(total/5) if len(prices)==5 else None
        actual=adj['daily_ma']['snapshots'][i]['curves']['5'][-1]
        check('event_day_sma5_matches_independent_anchor_calculation',actual==expected,date=dt,expected=expected,actual=actual)
        boundaries.append(dict(date=dt,cancelled_candidates=len(pending),deactivated_active_zones=len(active),
                               warmup_bars_checked=len(warm),raw_sma5=raw['daily_ma']['snapshots'][i]['curves']['5'][-1],adjusted_sma5=actual))
    return dict(schema_version=SCHEMA,status='PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL',code=job['code'],checks=checks,
                boundaries=boundaries,classification_quality='NOT_VALIDATED',period_action_coverage='UNVERIFIED',
                trading_qualification='NOT_EVALUATED',scope='Event mechanics only; no accuracy, performance or historical publication certification')


def run_event_replay(job,events):
    jobs=make_replay_jobs(job,events)
    results={name:run_analysis_job(q) for name,q in jobs.items()}
    report=compare_replay_results(job,events,results)
    # Re-run each mode with prices truncated and future event records removed.
    # Compare stored snapshots, not run-level IDs that include the full request.
    for cut in sorted(e['effective_date'] for e in events):
        count=sum(c['date']<cut for c in job['candles'])
        for name in ['RAW_WITH_EVENTS','ADJUSTED_WITH_EVENTS']:
            prefix=deepcopy(jobs[name]);prefix['candles']=prefix['candles'][:count]
            prefix['corporate_actions']['records']=[e for e in events if e['effective_date']<cut]
            replay=run_analysis_job(prefix)
            ok=all(replay['components'][k]['snapshots']==results[name]['components'][k]['snapshots'][:count] for k in ['structure','daily_ma'])
            report['checks'].append(dict(check='truncated_prices_and_removed_future_events_preserve_stored_snapshots',scenario=name,before_event=cut,status='PASS' if ok else 'FAIL',snapshots=count))
    report['status']='PASS' if all(c['status']=='PASS' for c in report['checks']) else 'FAIL'
    return dict(schema_version=SCHEMA,request_fingerprint=fingerprint(dict(job=job,reviewed_events=events)),jobs=jobs,results=results,report=report)
