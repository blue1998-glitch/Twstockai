"""Reproducible delta package; reuse only locally frozen public inputs."""
import argparse,hashlib,json,os,shutil,subprocess,tempfile,zipfile
from pathlib import Path,PurePosixPath

HERE=Path(__file__).parent;APP=HERE.parent;REPO=APP.parent
NAME='M1_explicit_band_volume_v03_20261024.zip'
sha=lambda body:hashlib.sha256(body).hexdigest()
def put(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def package(artifact,evidence,delivery):
    delivery.mkdir(parents=True,exist_ok=True)
    browser=json.loads((evidence/'browser-final/browser-report.json').read_bytes());assert browser['status']=='PASS'
    shutil.copytree(artifact,delivery/'artifacts',dirs_exist_ok=True)
    images=delivery/'images';images.mkdir(exist_ok=True)
    for f in (evidence/'browser-final').glob('*.png'):shutil.copy2(f,images/f.name)
    with tempfile.TemporaryDirectory(prefix='explicit-volume-package-') as temp:
        work=Path(temp)/'tree';work.mkdir()
        for folder in ['artifacts','images']:shutil.copytree(delivery/folder,work/folder)
        shutil.copytree(evidence,work/'evidence')
        shutil.copy2(REPO/'M1_EXPLICIT_BAND_VOLUME_HANDOFF.md',work/'WORK_HANDOFF.md')
        shutil.copy2(HERE/'BAND_VOLUME.md',work/'CONTRACT.md')
        project=work/'project';app=project/'股票系統M1_v0_18'
        paths=['graph_core/__init__.py','graph_core/core.py','reaction_facts/__init__.py','reaction_facts/core.py','reaction_facts/source.py','reaction_facts/band_volume.py',
               'pressure_chart/__init__.py','pressure_chart/facts.py','candle_region_chart/__init__.py','candle_region_chart/extents.py','src/contracts.py',
               'structure_state/__init__.py','structure_state/core.py','structure_state_chart/__init__.py','structure_state_chart/build_volume.py','structure_state_chart/band_volume.js',
               'structure_state_chart/test_band_volume.cjs','structure_state_chart/package_band_volume.py','structure_state_chart/BAND_VOLUME.md','structure_state_chart/examples/band-volume-selection.json',
               'tests/test_explicit_band_volume.py','cross_scale_chart/generated/comparison-data.json']
        for p in paths:
            dest=app/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(APP/p,dest)
        shutil.copytree(REPO/'deliveries/m1-p03-readability-20261024/artifacts',project/'deliveries/m1-p03-readability-20261024/artifacts')
        (work/'REPRODUCE.md').write_text('''# 明示研究帶最大量：獨立重現包

不是全歷史專案，不要覆寫原checkout。正常查看直接用GitHub新PNG，不需手機搬檔、終端或架站。artifacts為新自含HTML／JSON及完整原精度；project含本輪完整新增工程、所需不變舊helper及已存公開0.2父輸入、原comparison-data，沒有新來源下載或graph_core／P0-3／指標重算。

工程師在新目錄解壓後：

```bash
cd project/股票系統M1_v0_18
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_explicit_band_volume.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m structure_state_chart.build_volume --output-dir structure_state_chart/output/REPRODUCED --selection structure_state_chart/examples/band-volume-selection.json
```

應與artifacts九輸出完整bytes相同。新解壓同26不加總52；相關6舊回歸只在完整repo實跑，不在此包跑無關全套。純prepare／evaluate也可無網頁呼叫。瀏覽器另需既有Chromium及Playwright，臨時loopback HTTP並非部署；Android未測，file://不重試。日期／來源資格／密集量峰未定及下一輪Work完整指令見WORK_HANDOFF。
''')
        files=sorted(p for p in work.rglob('*') if p.is_file());members=[dict(path=str(p.relative_to(work)),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in files]
        put(work/'MANIFEST.json',dict(schema='explicit-band-volume-package/0.1',members=members,manifest_excludes_self=True,timestamp_not_observation_time=True))
        archive=delivery/NAME
        with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for f in sorted([*files,work/'MANIFEST.json']):
                i=zipfile.ZipInfo(str(f.relative_to(work)),date_time=(2026,10,24,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,f.read_bytes(),compresslevel=9)
    with tempfile.TemporaryDirectory(prefix='explicit-volume-extract-') as temp:
        fresh=Path(temp)
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            names=z.namelist();assert len(names)==len(set(names));assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names)
            m=json.loads(z.read('MANIFEST.json'))['members'];assert set(names)=={x['path'] for x in m}|{'MANIFEST.json'}
            for row in m:
                b=z.read(row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
            z.extractall(fresh)
        before={n:sha((fresh/n).read_bytes()) for n in names}
        cwd=fresh/'project/股票系統M1_v0_18';runs=[]
        for label,cmd in [('band-volume-tests',['python3','-m','unittest','discover','-s','tests','-p','test_explicit_band_volume.py','-v']),('volume-chart-rebuild',['python3','-m','structure_state_chart.build_volume','--output-dir','structure_state_chart/output/REPRODUCED','--selection','structure_state_chart/examples/band-volume-selection.json'])]:
            run=subprocess.run(cmd,cwd=cwd,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (delivery/(label+'-extracted.log')).write_bytes(run.stdout);runs.append(dict(label=label,command=cmd,returncode=run.returncode));assert run.returncode==0,run.stdout.decode()[-3000:]
        equal=[]
        for f in (fresh/'artifacts').iterdir():
            assert f.read_bytes()==(cwd/'structure_state_chart/output/REPRODUCED'/f.name).read_bytes(),f.name;equal.append(f.name)
        assert before=={n:sha((fresh/n).read_bytes()) for n in names}
    result=dict(status='PASS',scope='EXPLICIT_SAVED_RESEARCH_BAND_VOLUME_WIRING_NOT_AUTOMATIC_BANDS_OR_STRATEGY',filename=NAME,bytes=archive.stat().st_size,sha256=sha(archive.read_bytes()),members=len(names),manifest_entries=len(m),crc_unique_safe_paths=True,all_member_lengths_sha_verified=True,new_extraction_runs=runs,rebuilt_full_bytes_equal=equal,archive_members_unchanged=True,unique_python_tests=dict(new=26,related_regression=6,total=32),extracted_same_26_not_added=True,real_chromium_checks=browser['checks'],previous_tests_not_rerun=True,new_source_011=False,graph_p03_indicators_recomputed=False,physical_android='NOT_TESTED_NEW_BUILD')
    put(delivery/'package-verification.json',result);(delivery/'SHA256SUMS').write_text(result['sha256']+'  '+NAME+'\n')
    put(delivery/'artifact-manifest.json',dict(files=[dict(path=str(f.relative_to(delivery)),bytes=f.stat().st_size,sha256=sha(f.read_bytes())) for f in sorted([*(delivery/'artifacts').iterdir(),*images.iterdir()])]))
    print(json.dumps(result,ensure_ascii=False,indent=2));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artifact',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--delivery',type=Path,required=True)
    a=p.parse_args();package(a.artifact,a.evidence,a.delivery)
