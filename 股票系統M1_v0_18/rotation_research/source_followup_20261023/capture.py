"""One attempt per exact new source URL. No redirects, retries or TLS changes."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,subprocess,urllib.request,urllib.error

OUT=Path('/workspace/m1-source-followup-retry-v07-20261023/captures');OUT.mkdir(exist_ok=True)
SOURCES={
 'taifex-esun-resumption-20251106':dict(url='https://www.taifex.com.tw/file/taifex/CHINESE/11/attach/%E7%8E%89%E5%B1%B1%E9%87%911106%E6%81%A2%E5%BE%A9%E4%BA%A4%E6%98%93%E5%85%AC%E5%91%8A.pdf',expected_bytes=81441,expected_sha256='9699a6d1349a1f4e14d78601af4874f724df5c24224dbe49906b1ce4ee712320',work_request_at='2026-10-23T07:44:09.947859+00:00',work_completed_at='2026-10-23T07:44:15.344058+00:00',kind='PDF'),
 'esun-issuer-closing-completed-20260902':dict(url='https://www.esunfhc.com/zh-tw/news-center/news-center/news/detail?id=D0565FF2DAE34916B079E1F26A048B1C&p=148DB1EBDC2B47629ED09DC9820A2155',expected_bytes=103632,expected_sha256='4696b71825fac29c1baaf21a475387240d6a53d463c2108704c7bbfc54fbf38c',work_request_at='2026-10-23T07:43:19.915765+00:00',work_completed_at='2026-10-23T07:43:30.109551+00:00',kind='HTML'),
 'tcc-2026-q2-consolidated-report':dict(url='https://media.taiwancement.com/web_tcc/comm/pdf/report/2026/TCC%20115%E5%B9%B4%E7%AC%AC%E4%BA%8C%E5%AD%A3%E5%90%88%E4%BD%B5%E8%B2%A1%E5%A0%B1.pdf',expected_bytes=3320224,expected_sha256='e8a8ca682a242180a908a68030dc80ee0321ddf92217586f59230b1d3e584d2d',work_request_at='2026-10-23T07:45:17.500234+00:00',work_completed_at='2026-10-23T07:45:26.457982+00:00',kind='PDF'),
}
def now():return datetime.now(timezone.utc).isoformat()
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
def capture(item):
 sid,lead=item
 if (OUT/(sid+'.meta.json')).exists():raise ValueError('Existing attempt; do not repeat or overwrite')
 m=dict(source_id=sid,url=lead['url'],method='GET',requested_at=now(),work_comparison_only=lead,retries=0,redirects_followed=False)
 try:
  req=urllib.request.Request(lead['url'],headers={'User-Agent':'M1-Source-Audit/0.7','Accept':'application/pdf,text/html'})
  try:response=urllib.request.build_opener(NoRedirect()).open(req,timeout=40)
  except urllib.error.HTTPError as e:response=e
  with response:
   body=response.read(20*1024*1024+1)
   if len(body)>20*1024*1024:raise ValueError('Response exceeds size cap')
   m.update(http=response.code,final_url=response.url,headers={k:response.headers.get(k) for k in ['Content-Type','Content-Length','Date','Last-Modified','Location']})
  (OUT/(sid+'.response')).write_bytes(body)
  m.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),completed_at=now(),status='CAPTURED' if m['http']==200 else 'HTTP_FAILURE')
  m['captured_at']=m['completed_at'];m['readback_at']=now();m['work_sha_match']=m['sha256']==lead['expected_sha256']
  if m['http']==200 and body.startswith(b'%PDF-'):
   p=subprocess.run(['pdftotext','-layout',str(OUT/(sid+'.response')),str(OUT/(sid+'.txt'))],capture_output=True,text=True)
   t=OUT/(sid+'.txt');e=dict(command='pdftotext -layout',returncode=p.returncode,stderr=p.stderr,pdf_sha256=m['sha256'],version=subprocess.run(['pdftotext','-v'],capture_output=True,text=True).stderr.splitlines()[0])
   if t.exists():e.update(text_sha256=hashlib.sha256(t.read_bytes()).hexdigest(),pages=t.read_text().count('\f'))
   (OUT/(sid+'.extraction.json')).write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
 except Exception as e:m.update(status='REQUEST_FAILED',error=type(e).__name__+': '+str(e),completed_at=now(),captured_at=None,readback_at=None)
 (OUT/(sid+'.meta.json')).write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 return sid,m
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=3) as pool:result=dict(pool.map(capture,SOURCES.items()))
 (OUT/'source-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))
