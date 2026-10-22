"""Explicit create-only official-source capture; no retry, proxy/TLS bypass or engines.

Only supported host www.twse.com.tw; prohibited historical ex-right endpoint is
not requested. Failed responses remain evidence, never a valid empty dataset.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import re
import urllib.request
from urllib.parse import urlsplit

HERE=Path(__file__).resolve().parent
OUT=HERE/'source_qualification_20261022'


def capture(name,url):
    if not re.fullmatch('[A-Za-z0-9_-]+',name):raise ValueError('Invalid capture identity')
    if urlsplit(url).scheme!='https' or urlsplit(url).netloc!='www.twse.com.tw' or any(x in url.upper() for x in ('TWT49U','TWT48U')):
        raise ValueError('Unsupported/prohibited request; no historical ex-right retry')
    raw=OUT/'raw';raw.mkdir(exist_ok=True,parents=True)
    body=raw/(name+'.response');meta=raw/(name+'.meta.json')
    if meta.exists():
        existing=json.loads(meta.read_text())
        if existing['url']!=url:raise ValueError('Existing identity conflict')
        if existing['status']=='CAPTURED' and hashlib.sha256(body.read_bytes()).hexdigest()!=existing['sha256']:raise ValueError('Existing capture tampered')
        return existing  # Including errors: explicit no retry.
    result=dict(name=name,url=url,attempted_at=datetime.now(timezone.utc).isoformat())
    try:
        with urllib.request.urlopen(url,timeout=20) as r:
            b=r.read(10_000_001);result.update(http=r.status,final_url=r.url,content_type=r.headers.get('Content-Type'))
        if len(b)>10_000_000:raise ValueError('Response size limit')
        with body.open('xb') as f:f.write(b)
        result.update(status='CAPTURED',bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    except Exception as e:result.update(status='FAILED',error=type(e).__name__+': '+str(e))
    with meta.open('x') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


def main():
    # Actual market sessions complement, but do not rewrite, planned calendars.
    for year in (2025,2026):
        for month in range(7 if year==2025 else 1,13 if year==2025 else 11):
            key=f'{year}{month:02d}';r=capture('market-'+key,f'https://www.twse.com.tw/exchangeReport/FMTQIK?response=json&date={key}01')
            print(json.dumps(dict(name=r['name'],status=r['status'],error=r.get('error')),ensure_ascii=False),flush=True)
            if r['status']!='CAPTURED':return  # Diagnose, never spray failed hosts.
            x=json.loads((OUT/'raw'/f'market-{key}.response').read_text())
            if x.get('stat')!='OK' or x.get('date')!=key+'01':raise ValueError('Market response not validated; stop before further captures')


if __name__=='__main__':main()
