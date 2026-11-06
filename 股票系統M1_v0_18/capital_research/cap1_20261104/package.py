"""Package saved engine outputs only; no accounting/replay imports or calls."""
import io, zipfile, shutil, json, time, resource
from .build import CAP, ROOT, DELIVERY, MIN_FREE, BUDGET, read, write, sha, source_manifest
from .render import render
HTML_NAME='Twstockai_CAP1_synthetic_demo_v01.html'
ZIP_NAME='Twstockai_CAP1_synthetic_demo_v01.zip'


def package(label=None):
    start=time.monotonic();free=shutil.disk_usage(ROOT).free
    if free < MIN_FREE+BUDGET:raise ValueError('CAPACITY_BUDGET_REFUSED')
    freeze=read(CAP/'source-manifest.json')
    if freeze!=source_manifest():raise ValueError('ORIGINAL_SOURCE_CHANGED')
    out=read(CAP/'artifacts/comparison.json');html=render(out,freeze).encode()
    write(DELIVERY/HTML_NAME,html)
    z=io.BytesIO()
    with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as f:
        for n,b in [(HTML_NAME,html),('README.txt','合成帳戶示範。解壓後以瀏覽器開啟HTML，無需登入或連線。非真實收益，不提供交易建議。全帳退出持現金尚無足夠資料。'.encode())]:
            info=zipfile.ZipInfo(n,(2026,11,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;f.writestr(info,b)
    write(DELIVERY/ZIP_NAME,z.getvalue())
    paths=[DELIVERY/HTML_NAME,DELIVERY/ZIP_NAME]
    report=dict(schema='cap1-presentation-package/0.1',financial_engine_calls=0,
        comparison_sha256=sha((CAP/'artifacts/comparison.json').read_bytes()),
        files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in paths],
        seconds=round(time.monotonic()-start,3),max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        free_before=free,free_after=shutil.disk_usage(ROOT).free,minimum_free_bytes=MIN_FREE)
    if label is not None:write(CAP/('presentation-verification-'+label+'.json'),report)
    print(json.dumps(report,ensure_ascii=False));return report

if __name__=='__main__':
    import sys
    package(sys.argv[1] if len(sys.argv)>1 else None)
