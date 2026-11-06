"""Reproduce this limited-scope audit offline from captured official responses."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'data_audit';RAW=HERE/'raw'
sys.path.insert(0,str(ROOT/'src'))
from contracts import DataError,fingerprint
from source_audit import parse_tpex_holidays,parse_twse_holidays,parse_twse_month,planned_dates,compare_dates,apply_evidenced_closures
from analysis_jobs import run_analysis_job


def main():
    schedules=[];audits=[]
    for year in [2025,2026]:
        s=parse_tpex_holidays(json.loads((RAW/f'tpex_holiday_{year}.json').read_text()),year);schedules.append(s)
        (HERE/f'TPEX_{year}_計畫開休市.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
    twse=parse_twse_holidays(json.loads((RAW/'twse_holiday_2026_date.json').read_text()),2026)
    (HERE/'TWSE_2026_計畫開休市.json').write_text(json.dumps(twse,ensure_ascii=False,indent=2))
    evidence=json.loads((HERE/'臨時休市證據.json').read_text())
    for code in ['8069','6488']:
        candles=json.loads((ROOT/'data'/f'{code}_candles.json').read_text())
        planned=planned_dates(schedules,'2025-08-01','2026-09-30')
        revised=apply_evidenced_closures(planned,evidence,exchange='TPEX')
        audits.append(dict(code=code,exchange='TPEX',window=['2025-08-01','2026-09-30'],
                           before_exception=compare_dates(candles,planned),after_evidenced_exceptions=compare_dates(candles,revised['dates']),
                           note='Only exchange-specific reviewed closure cases applied; no exhaustive calendar or individual-suspension certification'))
    for code in ['1101','2884']:
        candles=[];sources=[]
        for month in range(1,10):
            name=f'{code}_2026{month:02d}.json'
            candles+=parse_twse_month(json.loads((RAW/name).read_text()),code=code,year=2026,month=month)
            sources.append(json.loads((RAW/(name+'.meta.json')).read_text()))
        planned=planned_dates([twse],'2026-01-01','2026-09-30')
        revised=apply_evidenced_closures(planned,evidence,exchange='TWSE')
        job=dict(schema_version='stock-analysis/1.0',code=code,exchange='TWSE',price_mode='RAW_CANDIDATE',timeframe='daily',
                 source=dict(id=fingerprint(candles),code=code,exchange='TWSE',volume_unit='SHARES_REPORTED',
                             volume_normalization='NATIVE_SHARE_COUNT_NO_SCALING',upstream='Official TWSE monthly STOCK_DAY responses',
                             source_records=sources,calendar_evidence_scope=revised['coverage']),
                 candles=candles,corporate_actions=dict(records=[],coverage_status='UNVERIFIED'),expected_dates=revised['dates'])
        (HERE/f'{code}_candles.json').write_text(json.dumps(candles,ensure_ascii=False,indent=2))
        (HERE/f'{code}_analysis_job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2))
        result=run_analysis_job(job)
        (HERE/'output'/f'{code}_RAW_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        audits.append(dict(code=code,exchange='TWSE',window=['2026-01-01','2026-09-30'],before_exception=compare_dates(candles,planned),
                           after_evidenced_exceptions=compare_dates(candles,revised['dates']),aligned_snapshots=len(result['aligned_snapshots']),
                           volume_unit='SHARES_REPORTED',corporate_action_coverage='UNVERIFIED',
                           ma260=result['components']['daily_ma']['snapshots'][-1]['curves']['260'][-1],
                           purpose='Engineering input/pipeline validation only; unknown corporate actions limit classification use'))
    rejected=[]
    try:parse_twse_holidays(json.loads((RAW/'twse_holiday_2025_rwd.json').read_text()),2025)
    except DataError as e:rejected.append(dict(file='twse_holiday_2025_rwd.json',error=e.as_dict()))
    report=dict(audits=audits,rejected_semantic_sources=rejected,calendar_certification='NOT_EXHAUSTIVE',
                classification_quality='NOT_VALIDATED',independent_performance_test='NOT_CLAIMED',
                existing_review_queue='Existing two-stock 326 targets preserved; new cases not added before corporate-action verification')
    (HERE/'output/資料日期與新樣本驗收.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    for a in audits:print(a['code'],a['after_evidenced_exceptions']['status'],a['after_evidenced_exceptions']['observed'],flush=True)


if __name__=='__main__':main()
