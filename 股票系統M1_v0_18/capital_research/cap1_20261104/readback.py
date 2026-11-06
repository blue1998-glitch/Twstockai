"""Pinned GitHub raw-byte readback, finite one GET/file, receipts non-self-referential."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import quote
import json, subprocess, sys, argparse
from .build import ROOT, CAP, sha, write

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args]).decode().strip()

def verify(commit,output_dir,stem):
    assert git('rev-parse',commit)==commit and len(commit)==40
    # core.quotePath defaults to quoting Chinese names. Resolve using NUL mode.
    paths=subprocess.check_output(['git','-C',str(ROOT),'diff-tree','--no-commit-id','--name-only','-r','-z','--no-renames',commit]).decode().strip('\0').split('\0')
    assert paths and all(p and not p.startswith('/') for p in paths)
    before=git('ls-remote','origin','refs/heads/dev/m1-v018-chart-annotations').split()[0]
    def one(path):
        expected=subprocess.check_output(['git','-C',str(ROOT),'show',commit+':'+path])
        url='https://raw.githubusercontent.com/blue1998-glitch/Twstockai/'+commit+'/'+quote(path,safe='/')
        row=dict(path=path,url=url,expected_bytes=len(expected),expected_sha256=sha(expected))
        try:
            with build_opener(NoRedirect).open(Request(url,headers={'User-Agent':'Twstockai-fixed-commit-readback'}),timeout=45) as response:
                actual=response.read();status=response.status
            row.update(http_status=status,bytes=len(actual),sha256=sha(actual),exact_bytes=(status==200 and actual==expected))
        except Exception as e:
            row.update(exact_bytes=False,error=type(e).__name__+':'+str(e))
        return row
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(one,paths))
    after=git('ls-remote','origin','refs/heads/dev/m1-v018-chart-annotations').split()[0]
    report=dict(schema='cap1-fixed-github-readback/0.1',fixed_commit=commit,
        observed_at=datetime.now(timezone.utc).isoformat(),remote_before=before,remote_after=after,
        status='PASS' if all(r['exact_bytes'] for r in rows) else 'FAIL',
        files_read=len(rows),exact_files=sum(r['exact_bytes'] for r in rows),
        requests_per_file=1,retries=0,redirects_followed=False,files=rows)
    write(Path(output_dir)/(stem+'.json'),report)
    lines=['# M-CAP1 固定GitHub原bytes讀回','',
        '固定提交：`'+commit+'`','',
        '狀態：'+report['status']+'；'+str(report['exact_files'])+'/'+str(len(rows))+'檔HTTP200、長度、SHA256及原bytes逐檔完全相同。',
        '每檔一次GET、無轉址／重試；收據另存，不納入自身固定工程清單。',
        '遠端開始／結束：`'+before+'`／`'+after+'`。',
        '完整逐檔結果見同名JSON。','',
        '只含CAP1程式／純合成資料／PNG／文件與根最新節；未傳真實行情／FM3圖／帳戶憑證。']
    write(Path(output_dir)/(stem+'.md'),('\n'.join(lines)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False))
    if report['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('commit');ap.add_argument('--output-dir',default=str(CAP));ap.add_argument('--stem',default='GITHUB_READBACK');args=ap.parse_args()
    verify(args.commit,args.output_dir,args.stem)
