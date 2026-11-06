"""Package only this new synthetic research plus exact unchanged dependencies."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def package(destination):
    project=Path(__file__).resolve().parents[1];root=project.parent
    dependencies=['graph_core/__init__.py','graph_core/core.py','manual_basis/__init__.py','manual_basis/core.py',
        'rotation_research/__init__.py','rotation_research/core.py','rotation_research/action_ledger.py',
        'rotation_research/action_fixtures.py','rotation_research/store.py']
    paths=[project/x for x in dependencies]+[p for p in (project/'capital_research').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths.append(root/'M1_CAPITAL_RESEARCH_PHASE1_HANDOFF.md')
    manifest=[]
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(paths):
            if p.is_symlink():raise ValueError('Refuse symlink')
            relative=p.relative_to(root).as_posix();body=p.read_bytes()
            z.writestr(relative,body);manifest.append(dict(path=relative,bytes=len(body),sha256=hashlib.sha256(body).hexdigest()))
        z.writestr('MANIFEST.json',json.dumps(dict(synthetic_only=True,dependencies='Exact unchanged repository source copies; no alternate ledger',
            limitation='Real-source gate probe is saved evidence; rerunning that gate needs the full repository catalog chain.',files=manifest),ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    body=destination.read_bytes()
    return dict(path=str(destination),bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),members=len(manifest)+1)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    print(json.dumps(package(a.output),ensure_ascii=False,sort_keys=True))


if __name__=='__main__':main()
