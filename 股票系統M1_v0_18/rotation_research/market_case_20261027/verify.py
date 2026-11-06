"""Publication fingerprints only, no old producer, numeric or new test run."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]


def main():
    value=json.loads((ROOT/'CHANGE_MANIFEST.json').read_text())
    for item in value['files']:
        p=REPO/item['path'];raw=p.read_bytes()
        assert not p.is_symlink() and len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],item['path']
    print(json.dumps(dict(matched=len(value['files']),manifest_self_excluded=True,numeric_calls=0)))


if __name__=='__main__':main()
