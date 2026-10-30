"""Offline real-source period replay with Fraction-based arithmetic checks."""
from copy import deepcopy
from datetime import date,timedelta
from decimal import Decimal,Context,localcontext,ROUND_HALF_EVEN
from fractions import Fraction
from itertools import groupby
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile

ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'period_analysis';OUT=HERE/'output';REQ=HERE/'requests'
sys.path.insert(0,str(ROOT/'src'))
from contracts import fingerprint
from period_jobs import run_period_job
from period_ma import analyze_period_ma
from structure import project_prices
from source_audit import planned_dates,apply_evidenced_closures


def decimal_fraction(value):return Fraction(str(value).replace(',',''))


def reference_check(snapshot,candles,events):
    dt=snapshot['as_of'];prefix=[c for c in candles if c['date']<=dt]
    with localcontext(Context(prec=28,rounding=ROUND_HALF_EVEN)):
        prices=project_prices(prefix,[e for e in events if e['effective_date']<=dt],dt,snapshot['price_mode'])
    checked_bars=0;checked_points=0
    for scale in ['weekly','monthly']:
        key=(lambda c:date.fromisoformat(c['date']).isocalendar()[:2]) if scale=='weekly' else (lambda c:c['date'][:7])
        groups=[list(g) for _,g in groupby(prices,key)]
        observed=[b for b in snapshot[scale]['bars'] if b['daily_records']]
        assert len(groups)==len(observed)
        for g,b in zip(groups,observed):
            assert b['daily_records']==len(g) and (b['first_price_date'],b['last_price_date'])==(g[0]['date'],g[-1]['date'])
            expected=[g[0]['open'],max(decimal_fraction(c['high']) for c in g),min(decimal_fraction(c['low']) for c in g),g[-1]['close']]
            assert [decimal_fraction(b[k]) for k in ['open','high','low','close']]==[decimal_fraction(v) for v in expected]
            known=[decimal_fraction(c['volume_shares_scaled']) for c in g if c.get('volume_shares_scaled') is not None]
            assert b['volume_shares'] is None if len(known)!=len(g) else decimal_fraction(b['volume_shares'])==sum(known,Fraction())
            checked_bars+=1
        for view in ['elapsed','candidate']:
            series=snapshot[scale][view];totals=[Fraction()];count=0
            for i,b in enumerate(snapshot[scale]['bars']):
                allowed=b['ma_eligible'] and (view=='candidate' or b['calendar_state']=='ELAPSED_CALENDAR_PERIOD')
                if not b['skip_supplied_no_trading_period'] and not b['ma_eligible']:totals=[Fraction()];count=0
                elif allowed:totals.append(totals[-1]+decimal_fraction(b['close']));count+=1
                for p in snapshot[scale]['periods']:
                    actual=series['curves'][str(p)][i]
                    if not allowed or count<p:assert actual is None
                    else:
                        exact=(totals[-1]-totals[-p-1])/p
                        with localcontext(Context(prec=28,rounding=ROUND_HALF_EVEN)):
                            expected=Decimal(exact.numerator)/Decimal(exact.denominator)
                        assert Decimal(actual)==expected
                    checked_points+=1
    return checked_bars,checked_points


def core(q,as_of,candles=None,events=None,calendar=None):
    return analyze_period_ma(q['candles'] if candles is None else candles,q['corporate_actions']['records'] if events is None else events,
                             code=q['code'],exchange=q['exchange'],mode=q['price_mode'],as_of=as_of,source_id=q['source']['id'],volume_unit=q['source']['volume_unit'],calendar=q.get('calendar') if calendar is None else calendar)


def make_job(code,mode):
    native=code in ['1101','2884'];path=ROOT/('data_audit' if native else 'data')/f'{code}_analysis_job.json';old=json.loads(path.read_text())
    start='2026-01-01' if native else '2025-08-01';end=old['candles'][-1]['date'];exchange=old['exchange']
    cal_files=['TWSE_2026_計畫開休市.json'] if native else ['TPEX_2025_計畫開休市.json','TPEX_2026_計畫開休市.json']
    schedules=[json.loads((ROOT/'data_audit'/p).read_text()) for p in cal_files]
    closures=json.loads((ROOT/'data_audit/臨時休市證據.json').read_text())
    expected=apply_evidenced_closures(planned_dates(schedules,start,end),closures,exchange=exchange)['dates']
    source=deepcopy(old['source']);source['period_calendar_provenance']=dict(files=cal_files+['臨時休市證據.json'],coverage='PLANNED_PLUS_EXPLICIT_CASES_ONLY; NOT_EXHAUSTIVE',
               fingerprints={p:hashlib.sha256((ROOT/'data_audit'/p).read_bytes()).hexdigest() for p in cal_files+['臨時休市證據.json']})
    return dict(schema_version='stock-period-analysis/1.0',code=code,exchange=exchange,timeframe='daily',price_mode=mode,source=source,
                candles=old['candles'],corporate_actions=old['corporate_actions'],as_of=end,
                calendar=dict(coverage_start=start,coverage_end=end,expected_dates=expected))


def main():
    OUT.mkdir(parents=True,exist_ok=True);REQ.mkdir(exist_ok=True)
    historical=[ROOT/'workflow/output/分析流程_v0_10.sqlite3',ROOT/'persistence/output/研究資料_v0_9.sqlite3',ROOT/'volume_revision/output/單位修正並存_v0_12.sqlite3']
    before={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in historical}
    cases=[];audit=[];processes=[]
    with tempfile.TemporaryDirectory(prefix='period-acceptance-') as tmp:
        for code,mode in [('8069','RAW_CANDIDATE'),('8069','ADJUSTED_CANDIDATE'),('6488','RAW_CANDIDATE'),('6488','ADJUSTED_CANDIDATE'),('1101','RAW_CANDIDATE'),('2884','RAW_CANDIDATE')]:
            q=make_job(code,mode);name=code+'_'+mode;source_fp=fingerprint(q);bars=points=0;dates=[c['date'] for c in q['candles']]
            for dt in dates:
                snap=core(q,dt);prefix=[c for c in q['candles'] if c['date']<=dt]
                assert snap==core(q,dt,candles=prefix)
                b,p=reference_check(snap,q['candles'],q['corporate_actions']['records']);bars+=b;points+=p
                audit.append(dict(code=code,mode=mode,as_of=dt,snapshot_id=snap['snapshot_id'],content_fingerprint=fingerprint(snap)))
            last=core(q,dates[-1]);mid=dates[len(dates)//2]
            altered=deepcopy(q['candles']);altered[-1]['close']=altered[-1]['open']
            future=list(q['corporate_actions']['records'])+[dict(effective_date=(date.fromisoformat(dates[-1])+timedelta(days=365)).isoformat(),factor='0.9')]
            changed_calendar=deepcopy(q['calendar']);changed_calendar['expected_dates']=[d for d in changed_calendar['expected_dates'] if d!=dates[-1]]
            assert core(q,mid)==core(q,mid,candles=altered,events=future,calendar=changed_calendar)
            assert fingerprint(q)==source_fp
            inp=REQ/(name+'.json');inp.write_text(json.dumps(q,ensure_ascii=False,indent=2));output=OUT/(name+'_PERIOD.json')
            p=subprocess.run([sys.executable,str(ROOT/'src/period_jobs.py'),'--input',str(inp),'--output',str(output)],capture_output=True,text=True,timeout=30)
            assert p.returncode==0,p.stdout+p.stderr;receipt=json.loads(p.stdout);processes.append(receipt['process_id'])
            saved=json.loads(output.read_text());assert saved==run_period_job(q) and saved['snapshot']==last
            assert last['monthly']['elapsed']['latest']['24']['value'] is None
            cases.append(dict(code=code,mode=mode,daily_snapshots=len(dates),aggregate_bars_checked=bars,curve_points_checked=points,
                              all_prefix_snapshots_equal=True,future_changes_do_not_change_earlier_snapshot=True,cli_readback_equal=True,
                              volume_unit=q['source']['volume_unit'],corporate_action_coverage=q['corporate_actions']['coverage_status'],
                              calendar_authentication=last['calendar_authentication'],latest={s:{v:last[s][v]['latest'] for v in ['elapsed','candidate']} for s in ['weekly','monthly']},
                              output=str(output.relative_to(ROOT)),request_fingerprint=source_fp,result_fingerprint=fingerprint(saved)))
            print(name,len(dates),'prefix snapshots PASS',flush=True)
    for rel,digest in before.items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest
    report=dict(schema_version='period-acceptance/1.0',status='PASS',cases=cases,total_daily_snapshots=len(audit),
                aggregate_bars_checked=sum(c['aggregate_bars_checked'] for c in cases),curve_points_checked=sum(c['curve_points_checked'] for c in cases),
                worker_processes=processes,historical_databases_byte_unchanged=True,historical_sha256=before,
                reference='Independent date grouping, OHLC extrema and Fraction arithmetic; uses unchanged established daily price projector',
                main_analysis_contract_modified=False,main_storage_integration='NOT_IMPLEMENTED',ui_integration='NOT_IMPLEMENTED',
                classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED')
    (OUT/'週月核心真實重播驗收.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    (OUT/'逐日重播核對指紋.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in audit))
    print(json.dumps(dict(status='PASS',cases=len(cases),daily_snapshots=len(audit),aggregate_bars=report['aggregate_bars_checked'],curve_points=report['curve_points_checked']),ensure_ascii=False))


if __name__=='__main__':main()
