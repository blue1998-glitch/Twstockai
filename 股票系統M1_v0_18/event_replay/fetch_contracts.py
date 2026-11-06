"""Read-only public TAIFEX form query, matching observed form fields."""
from pathlib import Path
import urllib.request,urllib.parse,datetime,json,hashlib,concurrent.futures
HERE=Path(__file__).resolve().parent

def fetch(code):
    url='https://www.taifex.com.tw/cht/4/contractAdj';fields=dict(stock_id=code,sId='',sDt='0')
    meta=dict(url=url,method='POST',form_fields=fields,fetched_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    name=f'taifex_contract_{code}.html'
    try:
        req=urllib.request.Request(url,data=urllib.parse.urlencode(fields).encode(),headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=20) as r:b=r.read();meta.update(status=r.status,final_url=r.url,content_type=r.headers.get('Content-Type'))
        (HERE/'raw'/name).write_bytes(b);meta.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    except Exception as e:meta.update(error=type(e).__name__,detail=str(e))
    (HERE/'raw'/(name+'.meta.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    return dict(name=name,**meta)

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:
        for m in p.map(fetch,['1101','2884']):print(json.dumps(m,ensure_ascii=False),flush=True)
