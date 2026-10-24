"""Separate create-only capture of official planned calendars; not exhaustive."""
import argparse,json,time,hashlib
from pathlib import Path
from pressure_chart.history import ROOT,fetch
from source_audit import parse_twse_holidays,parse_tpex_holidays
from product_candidate.build import publish_immutable


def capture(out,first,last):
    out=Path(out)
    if out.exists():raise ValueError('Use a fresh calendar output directory')
    out.mkdir(parents=True);report=[];blocked=set()
    for exchange in ('TWSE','TPEX'):
        for year in range(first,last+1):
            url=f'https://www.twse.com.tw/rwd/zh/holidaySchedule/holidaySchedule?response=json&date={year}0101' if exchange=='TWSE' else f'https://www.tpex.org.tw/www/zh-tw/bulletin/tradingDate?date={year}&response=json'
            if exchange in blocked:continue
            b,meta=fetch(url)
            if b is None:report.append(dict(exchange=exchange,year=year,**meta));blocked.add(exchange);continue
            stem=f'{exchange}_{year}';publish_immutable(out/(stem+'.raw.json'),b)
            publish_immutable(out/(stem+'.meta.json'),json.dumps(meta,ensure_ascii=False,indent=2).encode())
            try:
                parsed=(parse_twse_holidays if exchange=='TWSE' else parse_tpex_holidays)(json.loads(b),year)
                publish_immutable(out/(stem+'.calendar.json'),json.dumps(parsed,ensure_ascii=False,indent=2).encode())
                report.append(dict(exchange=exchange,year=year,status='PARSED_PLANNED_CALENDAR_NOT_EXHAUSTIVE',**meta))
            except (ValueError,KeyError,TypeError) as e:report.append(dict(exchange=exchange,year=year,status='REJECTED',error=repr(e),**meta))
            time.sleep(3)
    publish_immutable(out/'calendar-report.json',json.dumps(report,ensure_ascii=False,indent=2).encode());return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);p.add_argument('--first-year',type=int,required=True);p.add_argument('--last-year',type=int,required=True);a=p.parse_args();print(json.dumps(capture(a.output_dir,a.first_year,a.last_year),ensure_ascii=False,indent=2))
