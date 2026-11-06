"""Archive this display delta and frozen local inputs; never downloads or evaluates."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import zipfile

HERE=Path(__file__).parent
APP=HERE.parent
REPO=APP.parent
NAME='M1_P03_readability_v02_20261024.zip'
sha=lambda b:hashlib.sha256(b).hexdigest()


def put(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def package(artifact, evidence, delivery):
    delivery.mkdir(parents=True,exist_ok=True)
    report=json.loads((evidence/'browser-release/browser-report.json').read_text())
    assert report['status']=='PASS'
    shutil.copytree(artifact,delivery/'artifacts',dirs_exist_ok=True)
    images=delivery/'images';images.mkdir(exist_ok=True)
    for src in [* (evidence/'browser-release').glob('*.png'),*(evidence/'panels').glob('*.png')]:
        shutil.copy2(src,images/src.name)
    with tempfile.TemporaryDirectory(prefix='p03-display-package-') as temp:
        work=Path(temp)/'tree';work.mkdir()
        for folder in ['artifacts','images']:
            shutil.copytree(delivery/folder,work/folder)
        shutil.copytree(evidence,work/'evidence')
        shutil.copy2(REPO/'M1_P03_READABILITY_HANDOFF.md',work/'WORK_HANDOFF.md')
        shutil.copy2(HERE/'READABILITY.md',work/'CONTRACT.md')
        project=work/'project';target=project/'股票系統M1_v0_18'
        for rel in ['__init__.py','build_readable.py','readability.js','test_readability.cjs','capture_readability.cjs','package_readability.py','READABILITY.md']:
            dest=target/'structure_state_chart'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/rel,dest)
        dest=target/'tests/test_structure_state_readability.py';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(APP/'tests/test_structure_state_readability.py',dest)
        frozen=REPO/'deliveries/m1-p03-structure-state-20261024/artifacts'
        shutil.copytree(frozen,project/'deliveries/m1-p03-structure-state-20261024/artifacts')
        (work/'REPRODUCE.md').write_text('''# 顯示0.2獨立可重現包

不是整份歷史專案，不要覆寫原checkout。一般讀者直接看GitHub新images，不要求終端、手機搬檔或架伺服器。artifacts是新自含HTML與原bytes JSON；project含本輪完整新增顯示工程及庫內固定0.1輸入，沒有數值producer或新行情。原核心完整來源保持在固定702e9144 GitHub。

工程師在全新解壓目錄：

```bash
cd project/股票系統M1_v0_18
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_structure_state_readability.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m structure_state_chart.build_readable --output-dir structure_state_chart/output/REPRODUCED
```

應與artifacts七輸出完整bytes相同。上述新解壓同6不加總12；不需要網路、DB、核心producer或重跑歷史65／94。瀏覽器測試另需既有Chromium與Playwright，開臨時loopback HTTP而非file://或部署；沒有Android通過宣稱。完整限制與下一輪Work唯讀指令見WORK_HANDOFF。
''')
        members=sorted(p for p in work.rglob('*') if p.is_file())
        manifest=[dict(path=str(p.relative_to(work)),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in members]
        put(work/'MANIFEST.json',dict(schema='p03-display-package/0.2',members=manifest,manifest_excludes_self=True,timestamp_not_observation_time=True))
        archive=delivery/NAME
        if archive.exists():
            raise ValueError('Preserve existing package; use separate delivery directory')
        with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in sorted([*members,work/'MANIFEST.json']):
                i=zipfile.ZipInfo(str(p.relative_to(work)),date_time=(2026,10,24,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16
                z.writestr(i,p.read_bytes(),compresslevel=9)
    with tempfile.TemporaryDirectory(prefix='p03-display-extract-') as temp:
        fresh=Path(temp)
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            names=z.namelist();assert len(names)==len(set(names))
            assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names)
            m=json.loads(z.read('MANIFEST.json'))['members'];assert set(names)=={x['path'] for x in m}|{'MANIFEST.json'}
            for row in m:
                b=z.read(row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
            z.extractall(fresh)
        before={n:sha((fresh/n).read_bytes()) for n in names}
        cwd=fresh/'project/股票系統M1_v0_18';env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');runs=[]
        for label,cmd in [('display-tests',['python3','-m','unittest','discover','-s','tests','-p','test_structure_state_readability.py','-v']),('display-rebuild',['python3','-m','structure_state_chart.build_readable','--output-dir','structure_state_chart/output/REPRODUCED'])]:
            run=subprocess.run(cmd,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (delivery/(label+'-extracted.log')).write_bytes(run.stdout)
            runs.append(dict(label=label,command=cmd,returncode=run.returncode))
            assert run.returncode==0,run.stdout.decode()[-3000:]
        rebuilt=cwd/'structure_state_chart/output/REPRODUCED';equal=[]
        for p in (fresh/'artifacts').iterdir():
            assert p.read_bytes()==(rebuilt/p.name).read_bytes(),p.name
            equal.append(p.name)
        assert before=={n:sha((fresh/n).read_bytes()) for n in names}
    result=dict(status='PASS',scope='DISPLAY_ONLY_NOT_NUMERIC_PRODUCER_MARKET_ACCURACY_OR_ANDROID',filename=NAME,
                bytes=archive.stat().st_size,sha256=sha(archive.read_bytes()),members=len(names),manifest_entries=len(m),
                crc_safe_unique_names=True,all_member_sha_lengths_verified=True,new_extraction_runs=runs,
                rebuilt_full_bytes_equal=equal,archive_members_unchanged=True,
                unique_directed_python_tests=6,new_extraction_same_6_not_added=True,real_chromium_display_checks=report['checks'],
                old_65_python_94_browser_not_rerun=True,new_numeric_producer=False,new_source_011=False,physical_android='NOT_TESTED_NEW_BUILD')
    put(delivery/'package-verification.json',result)
    (delivery/'SHA256SUMS').write_text(result['sha256']+'  '+NAME+'\n')
    put(delivery/'artifact-manifest.json',dict(files=[dict(path=str(p.relative_to(delivery)),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted([*(delivery/'artifacts').iterdir(),*images.iterdir()])]))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artifact',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--delivery',type=Path,required=True)
    a=p.parse_args();package(a.artifact,a.evidence,a.delivery)
