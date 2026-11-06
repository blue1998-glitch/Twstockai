from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,urllib.request,urllib.error,urllib.parse,subprocess

ROOT=Path('/workspace/Twstockai')
OUT=ROOT/'股票系統M1_v0_18/rotation_research/subsidiary_proposal_20261023'
def now():return datetime.now(timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args):return None
index=ROOT/'股票系統M1_v0_18/rotation_research/final_distribution_review_20261023/raw/tcc-meeting-index.response'
b=index.read_bytes();assert len(b)==495054 and sha(b)=='d995a10409cebd07942fad51aceb26de1db726936715af36376f4aa68d2f5098'
t=b.decode();target=t.index('議事錄1151013.pdf');section=t[max(0,target-5500):target+1800]
items=[('tcc-egm-minutes-20261013','台泥115年第一次股東臨時會議事錄1151013.pdf',1463099,'861283c21d87e0511c43485874592102dc8d4a73099271a5d23edcbf5dc44b7b'),('tcc-egm-voting-20261013','台泥115年第1次股東臨時會行使投票方式及投票表決結果.pdf',135295,'af2524a2a9ef722266fd82dceb95fbc5c4a0222793a0f965bbc27266aec48154')]
OUT.mkdir(exist_ok=True);(OUT/'raw').mkdir(exist_ok=True)
results=[]
for sid,name,size,digest in items:
    p=OUT/'raw'/f'{sid}.response'
    if p.exists():raise RuntimeError('Already acquired: no repeat')
    hrefs=[h for h in re.findall(r'href="([^"]+)"',section) if h.endswith('/'+name)]
    assert len(hrefs)==1
    href=hrefs[0];url=urllib.parse.quote(href,safe=':/%')
    m=dict(source_id=sid,index_path=str(index.relative_to(ROOT)),index_sha256=sha(b),original_href=href,url=url,method='GET',requested_at=now(),retries=0,redirects_followed=False)
    try:
        with urllib.request.build_opener(NoRedirect).open(urllib.request.Request(url,headers={'User-Agent':'Twstockai-source-research/0.10'}),timeout=60) as r:
            body=r.read();m.update(http=r.status,final_url=r.url,headers=dict(r.headers.items()),status='CAPTURED')
    except urllib.error.HTTPError as e:
        body=e.read();m.update(http=e.code,final_url=e.url,headers=dict(e.headers.items()),status='REFUSED_STOPPED',error=str(e))
    except Exception as e:
        body=b'';m.update(http=None,status='FAILED_STOPPED',error=repr(e))
    m.update(completed_at=now(),captured_at=now(),bytes=len(body),sha256=sha(body),expected_work_bytes=size,expected_work_sha256=digest,byte_identity_with_work_report=len(body)==size and sha(body)==digest)
    p.write_bytes(body);dump(p.with_suffix('.meta.json'),m);results.append(m)
    print(sid,m['status'],m['http'],len(body),sha(body),flush=True)
dump(OUT/'acquisition.json',dict(index_reused=True,index_bytes=len(b),index_sha256=sha(b),requests=results,forbidden_endpoints_requested=0,old_esun_pdf_requests=0))
