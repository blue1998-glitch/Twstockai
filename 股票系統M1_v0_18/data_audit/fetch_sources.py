"""Capture official response bytes and provenance, including failed requests."""
import concurrent.futures,datetime,hashlib,json,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def fetch(item):
    name,url=item;target=ROOT/'raw'/name
    meta=dict(url=url,fetched_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json,text/html,*/*'})
        with urllib.request.urlopen(req,timeout=15) as r:
            data=r.read();meta.update(status=r.status,content_type=r.headers.get('Content-Type'),final_url=r.url)
        target.write_bytes(data);meta.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    except Exception as e:meta.update(error=type(e).__name__,detail=str(e))
    (ROOT/'raw'/(name+'.meta.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    return dict(name=name,**meta)

if __name__=='__main__':
    jobs=json.loads((ROOT/'fetch_requests.json').read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(fetch,jobs))
    (ROOT/'fetch_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    for r in results:print(json.dumps({k:r.get(k) for k in ['name','status','bytes','error']},ensure_ascii=False),flush=True)
