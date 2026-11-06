"""Independent intake audit with exact no-trade notes retained as evidence.
Do not silently remove missing source sessions or infer market/stock suspensions.
"""
import json,hashlib,re
from datetime import date
from pathlib import Path
from pressure_chart.history import ROOT
from pressure_chart.history_adapter import validate_intake
from source_audit import planned_dates,apply_evidenced_closures
from product_candidate.build import publish_immutable


def run(history,calendars):
    h=validate_intake(history);calendars=Path(calendars);results=[];notes=[]
    for exchange in ('TWSE','TPEX'):
        for year in range(2021,2027):
            if exchange!='TWSE':continue
            p=calendars/f'{exchange}_{year}.raw.json';v=json.loads(p.read_text())
            for r in v.get('data',[]):
                if len(r)>=3 and '市場無交易' in str(r[2]):
                    # The row can be the LAST TRADING DAY while the note names
                    # later non-trading days. Never turn that row date into a closure.
                    cited=re.findall(r'(\d+)月(\d+)日',r[2])
                    if not cited:raise ValueError('No explicit no-trade date in primary note')
                    for month,day in cited:
                        notes.append(dict(exchange=exchange,date=date(year,int(month),int(day)).isoformat(),source_row_date=r[0],name=r[1],primary_text=r[2],source=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    closures=json.loads((ROOT/'data_audit/臨時休市證據.json').read_text())
    for s in h['series']:
        schedules=[json.loads((calendars/f"{s['exchange']}_{year}.calendar.json").read_text()) for year in range(2021,2027)]
        expected=apply_evidenced_closures(planned_dates(schedules,h['target_start'],h['target_end']),closures,exchange=s['exchange'])['dates']
        explicit={r['date'] for r in notes if r['exchange']==s['exchange']}
        expected=set(expected)-explicit;actual={r['date'] for r in s['candles']};zero=[]
        for m in s['source_records']:
            for row in m['zero_turnover_no_price_source_rows']:
                y,mon,day=map(int,row[0].split('/'));zero.append(dict(date=f'{y+1911:04d}-{mon:02d}-{day:02d}',raw_row=row,month=m['month'],response_sha256=m['sha256']))
        zero_dates={r['date'] for r in zero}
        results.append(dict(code=s['code'],rows=len(actual),first=s['actual_start'],last=s['actual_end'],monthly_responses=len(s['source_records']),missing_months=s['missing_months'],
            missing_price_bars_vs_reviewed_planned_calendar=sorted(expected-actual),
            explicit_zero_turnover_no_price_rows=zero,
            missing_dates_still_require_primary_closure_or_suspension_evidence=sorted(expected-actual-zero_dates),
            unexpected_price_dates=sorted(actual-expected),
            volume_units=sorted({m['source_volume_field'] for m in s['source_records']}),
            actions='OLD_SAMPLES_ONLY_FULL_FIVE_YEAR_ACTIONS_UNVERIFIED',full_history_high='NOT_ESTABLISHED'))
    return dict(schema_version='official-history-audit/0.1',status='MONTH_RESPONSES_AND_OHLCV_VERIFIED_GAPS_DISCLOSED',source_calendar_explicit_no_equity_trading_notes=notes,series=results,
        calendar_completeness='PLANNED_PLUS_CITED_NOTES_AND_OLD_EXPLICIT_EXCEPTIONS_NOT_EXHAUSTIVE',
        corporate_action_obligation='Need complete ex-dividend/ex-right/split/reduction/other actions and publication-time evidence before common adjusted five-year comparisons',
        twse_prior_security_denied_exright_endpoint='NOT_RETRIED_PER_PROJECT_AGENTS',known_market_closure_inference_from_cross_stock_absence='NOT_PERFORMED')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--history',required=True);p.add_argument('--calendars',required=True);p.add_argument('--output',required=True);a=p.parse_args();r=run(a.history,Path(a.calendars).resolve());print(publish_immutable(a.output,json.dumps(r,ensure_ascii=False,indent=2).encode()));print(json.dumps(r,ensure_ascii=False,indent=2))
