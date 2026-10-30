"""Bounded, read-only primary-source capture. No trading or source overwrite."""
import hashlib, json, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw'
RAW.mkdir(exist_ok=True)
JOBS = [
    ('exright-2025', 'https://www.twse.com.tw/rwd/zh/exRight/TWT49U?startDate=20250101&endDate=20251231&response=json'),
    ('exright-2026-to-cutoff', 'https://www.twse.com.tw/rwd/zh/exRight/TWT49U?startDate=20260101&endDate=20260724&response=json'),
    ('stock-2884-202606', 'https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date=20260601&stockNo=2884'),
    ('stock-2884-202607', 'https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date=20260701&stockNo=2884'),
] + [(f'market-{m:02d}', f'https://www.twse.com.tw/exchangeReport/FMTQIK?response=json&date=2026{m:02d}01') for m in range(1,8)]

def capture(job):
    name, url = job
    dest = RAW / (name + '.json')
    if dest.exists():
        raise RuntimeError('Refuse overwrite existing capture: ' + name)
    record = {'name':name,'url':url,'observed_at':datetime.now(timezone.utc).isoformat(),'attempts':[]}
    for attempt in range(2):
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                body = response.read()
                parsed = json.loads(body)
                assert parsed.get('stat') == 'OK', parsed.get('stat')
                assert parsed.get('fields') and isinstance(parsed.get('data'),list)
                record['attempts'].append({'number':attempt+1,'http':response.status,'result':'OK'})
            dest.write_bytes(body)
            record.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),rows=len(parsed['data']),status='CAPTURED',historical_publication_time='NOT_AUTHENTICATED')
            return record
        except Exception as exc:
            record['attempts'].append({'number':attempt+1,'error':str(exc)})
    record['status']='FAILED_AFTER_TWO_ATTEMPTS'
    return record

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(capture,JOBS))
    (ROOT/'source-capture.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    for record in records:
        print(record['name'],record['status'],record.get('rows'))
