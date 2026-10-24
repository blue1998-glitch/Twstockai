"""Create-only reproducible research bundle, including small retained public sources."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
DELIVERY = REPO/'deliveries/m1-volume-peak-research-20261024'


def package(destination):
    paths = list((APP/'volume_peak_research').rglob('*'))
    helpers = ['graph_core/__init__.py','graph_core/core.py','reaction_facts/__init__.py',
               'reaction_facts/core.py','pressure_chart/__init__.py','pressure_chart/facts.py',
               'src/contracts.py','src/source_audit.py','structure_state_chart/examples/band-volume-selection.json',
               'pressure_chart/data/history-20261018/coverage-audit.json']
    paths.extend(APP/p for p in helpers)
    request = json.loads((APP/'volume_peak_research/examples/request.json').read_bytes())
    for month in request['months']:
        for suffix in ['.json','_meta.json']:
            paths.append(APP/'pressure_chart/data/history-20261018/raw'/(request['code']+'_'+month+suffix))
    paths.extend(p for p in (DELIVERY/'artifacts').iterdir() if p.is_file())
    paths.extend([DELIVERY/'README.md', REPO/'M1_VOLUME_PEAK_RESEARCH_HANDOFF.md'])
    files = {}
    for path in paths:
        if path.is_file() and '__pycache__' not in path.parts:
            name = str(path.relative_to(REPO))
            files[name] = path.read_bytes()
    manifest = {name: dict(bytes=len(body),sha256=hashlib.sha256(body).hexdigest()) for name,body in sorted(files.items())}
    files['MANIFEST.json'] = (json.dumps(dict(schema_version='research-offline-bundle/0.1',files=manifest),ensure_ascii=False,indent=2)+'\n').encode()
    with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,body in sorted(files.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,body)
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        names=archive.namelist();assert len(names)==len(set(names))
        for name in names:
            assert not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts
            assert archive.read(name)==files[name]
    body=Path(destination).read_bytes()
    return dict(bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),members=len(files),
                manifest_members=len(manifest),crc_all_members=True,all_member_bytes_match=True,
                only_public_sources=True,old_zip_or_images_read=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(package(args.out),indent=2))
