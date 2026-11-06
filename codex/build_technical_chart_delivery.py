"""Create three ordinary ZIPs of the hydrated project, then extract/hash all members.
Run from repository root after building and recording acceptance. No engine calls.
"""
from pathlib import Path
import hashlib
import io
import json
import tempfile
import zipfile
import zlib

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'股票系統M1_v0_18'
OUT=ROOT/'deliveries/m1-v019-technical-chart-20261017'
BASE='3dcfcf6534fe645781898eaa603e88a2b3bd3e9d'

def sha(b):return hashlib.sha256(b).hexdigest()
def write_new(path,b):
    if path.is_symlink():raise ValueError('Symlink output')
    if path.exists():
        if path.read_bytes()!=b:raise ValueError('Different existing delivery: '+str(path))
    else:path.write_bytes(b)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    files={}
    for p in PROJECT.rglob('*'):
        rel=p.relative_to(PROJECT)
        if any(x in rel.parts for x in ('__pycache__','tmp')):continue
        if rel.parts[:2]==('technical_chart','output'):continue
        if p.is_symlink():raise ValueError('Unexpected project symlink '+str(p))
        if p.is_file():files[str(p.relative_to(ROOT))]=p
    for pattern in ('AGENTS.md','CONTINUE_IN_WORK_MODE.md','PROJECT_VISION.md','M1_*.md','M1_*.json','docs/visual-discussion/*','codex/build_technical_chart_delivery.py'):
        for p in ROOT.glob(pattern):
            if p.is_file():files[str(p.relative_to(ROOT))]=p
    # Previous delivered candidate HTML/JSON stay available without regeneration.
    for folder,names in [('m1-v019-context-20261017',['M1_v0_19_candidate.html','candidate.json']),('m1-v019-attempt-view-20261017',['M1_v0_19_attempt_candidate.html','attempt-candidate.json','attempt-selection-oracle.json'])]:
        for name in names:
            p=ROOT/'deliveries'/folder/name
            files['股票系統M1_v0_18/product_candidate/generated/'+name]=p
    manifest={};rank=[]
    for name,p in sorted(files.items()):
        b=p.read_bytes();manifest[name]=dict(bytes=len(b),sha256=sha(b));rank.append((len(zlib.compress(b,9)),name,p))
    manifest_bytes=json.dumps(dict(version='technical-chart-view/0.1',base_commit=BASE,files=manifest),ensure_ascii=False,indent=2).encode()
    write_new(OUT/'PROJECT_FILE_MANIFEST.json',manifest_bytes)
    bins=[[],[],[]];sizes=[0,0,0]
    for size,name,p in sorted(rank,reverse=True):
        i=min(range(3),key=lambda j:sizes[j]);bins[i].append((name,p));sizes[i]+=size
    archives=[]
    with tempfile.TemporaryDirectory(prefix='m1-chart-pack-',dir='/workspace') as tmp:
        tmp=Path(tmp)
        for i,items in enumerate(bins,1):
            dest=tmp/f'M1_v019_chart_full_{i:02d}.zip'
            with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
                for name,p in sorted(items):z.writestr(name,p.read_bytes())
                if i==1:
                    z.writestr('PROJECT_FILE_MANIFEST.json',manifest_bytes)
                    z.writestr('OFFLINE_PROJECT_README.txt',(OUT/'OFFLINE_PROJECT_README.txt').read_bytes())
            content=dest.read_bytes()
            if len(content)>=32*1024*1024:raise ValueError('Package exceeds 32MiB')
            write_new(OUT/dest.name,content);archives.append(dict(file=dest.name,bytes=len(content),mib=round(len(content)/1048576,3),sha256=sha(content)))
        extracted=tmp/'extracted';extracted.mkdir();members=[]
        for row in archives:
            with zipfile.ZipFile(OUT/row['file']) as z:
                if z.testzip() is not None:raise ValueError('CRC mismatch')
                for info in z.infolist():
                    name=info.filename
                    if name in members or Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('Unsafe/duplicate member')
                    members.append(name)
                z.extractall(extracted)
        for name,meta in manifest.items():
            b=(extracted/name).read_bytes()
            if len(b)!=meta['bytes'] or sha(b)!=meta['sha256']:raise ValueError('Extract mismatch: '+name)
        # Verify the small, standalone page ZIP independently as well.
        page_bytes=(PROJECT/'technical_chart/generated/M1_v0_19_technical_chart.html').read_bytes()
        buff=io.BytesIO()
        with zipfile.ZipFile(buff,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            z.writestr('M1_v0_19_technical_chart.html',page_bytes)
            z.writestr('README.txt',(OUT/'OFFLINE_PROJECT_README.txt').read_bytes())
        write_new(OUT/'M1_v019_chart_page.zip',buff.getvalue())
        with zipfile.ZipFile(OUT/'M1_v019_chart_page.zip') as z:
            if z.read('M1_v0_19_technical_chart.html')!=page_bytes:raise ValueError('Standalone mismatch')
        write_new(OUT/'M1_v0_19_technical_chart.html',page_bytes)
    report=dict(status='PASS',archives=archives,project_and_handoff_files=len(manifest),unique_members=len(members),duplicates=0,all_extracted_bytes_match=True,standalone_html_sha256=sha(page_bytes),original_engine_or_database_recomputed=False)
    write_new(OUT/'PACKAGE_VERIFICATION.json',json.dumps(report,ensure_ascii=False,indent=2).encode())
    sums=''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ('SHA256SUMS.txt','GITHUB_DOWNLOAD_VERIFICATION.json'))
    write_new(OUT/'SHA256SUMS.txt',sums.encode())
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
