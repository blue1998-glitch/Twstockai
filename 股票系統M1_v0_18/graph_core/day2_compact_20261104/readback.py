"""Finite fixed-SHA public GitHub byte readback; no provider/source retries."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.parse import quote
import argparse,hashlib,json,subprocess,shutil
REPO=Path(__file__).resolve().parents[3]
BRANCH='dev/m1-v018-chart-annotations'
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*a,**k):return None
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args]).decode().strip()
def sha(b):return hashlib.sha256(b).hexdigest()
def verify(commit,output,stem):
    if len(commit)!=40 or git('rev-parse',commit)!=commit:raise ValueError('FIXED_FULL_COMMIT_REQUIRED')
    paths=subprocess.check_output(['git','-C',str(REPO),'diff-tree','--no-commit-id','--name-only','-r','-z','--no-renames',commit]).decode().strip('\0').split('\0')
    if not paths or any(not p or p.startswith('/') for p in paths):raise ValueError('INVALID_CHANGE_SET')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    targets=[output/(stem+'.json'),output/(stem+'.md')]
    if any(p.exists() for p in targets):raise FileExistsError('RECEIPT_ALREADY_EXISTS_NO_REPEAT')
    if shutil.disk_usage(output).free<536870912+2*1024**2:raise OSError('RESERVE_REQUIRED')
    before=git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]
    def one(p):
        expected=subprocess.check_output(['git','-C',str(REPO),'show',commit+':'+p]);url='https://raw.githubusercontent.com/blue1998-glitch/Twstockai/'+commit+'/'+quote(p,safe='/')
        row=dict(path=p,url=url,expected_bytes=len(expected),expected_sha256=sha(expected))
        try:
            with build_opener(NoRedirect).open(Request(url,headers={'User-Agent':'Twstockai-DAY2-fixed-readback'}),timeout=45) as response:
                actual=response.read();status=response.status
            row.update(http_status=status,bytes=len(actual),sha256=sha(actual),exact_bytes=(status==200 and actual==expected))
        except Exception as e:row.update(exact_bytes=False,error=type(e).__name__+': '+str(e))
        return row
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(one,paths))
    after=git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]
    report=dict(schema='m-day2-fixed-readback/0.1',fixed_commit=commit,observed_at=datetime.now(timezone.utc).isoformat(),remote_before=before,remote_after=after,status='PASS' if all(r['exact_bytes'] for r in rows) else 'FAIL',files_read=len(rows),exact_files=sum(r['exact_bytes'] for r in rows),requests_per_file=1,retries=0,redirects_followed=False,files=rows)
    targets[0].write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    lines=['# M-DAY2-COMPACT 固定GitHub原bytes讀回','',f'固定提交：`{commit}`','',f"{report['status']}：{report['exact_files']}/{len(rows)} 檔HTTP200、長度、SHA256及完整bytes一致。",'','每檔一次GET、無重試／轉址；此收據另存，不自指。',f'遠端開始／結束：`{before}`／`{after}`。','', '只讀回此次程式、原碼差異快照、不可還原容量摘要／定向測試日志及根交接，未公開行情、原圖、完整分析、憑證或私人原件。','', '本輪仍BLOCKED_CAPACITY，正式新日套用0；讀回通過不等全市場更新成功。']
    targets[1].write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False))
    if report['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('commit');p.add_argument('--output-dir',required=True);p.add_argument('--stem',default='GITHUB_READBACK');a=p.parse_args();verify(a.commit,a.output_dir,a.stem)
