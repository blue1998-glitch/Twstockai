from pathlib import Path
import json,hashlib,shutil,math
from rotation_research import artifact_codec as c
BASE=Path('/workspace/twstockai-local-data')
ROOT=BASE/'fm3_20261101/runtime'
WORK=BASE/'storage1_20261104'
CAPTURE=BASE/'day2_compact_20261104/capture'
REPO=Path(__file__).resolve().parents[3]
RESERVE=536870912
LIMIT=32*1024**2
IMMUTABLE=c.immutable
sha=c.sha
encode=c.encoded
def budget(amount=0):
    initial=json.loads((WORK/'baseline-private.json').read_bytes())['free_bytes'];free=shutil.disk_usage(WORK).free
    allocated=math.ceil(amount/4096)*4096+4096
    if free-allocated<RESERVE or initial-free+allocated>LIMIT:raise OSError('STORAGE1_CAPACITY_PRESERVE_ORIGINALS')
    return free
def write(path,body):
    p=Path(path)
    if not p.resolve().is_relative_to(WORK.resolve()) or any(a.is_symlink() for a in (p,*p.parents)):raise ValueError('NEW_PRIVATE_STORAGE1_ROOT_ONLY')
    budget(len(body) if not p.exists() else 0);IMMUTABLE(p,body)
def read_json(p):return json.loads(Path(p).read_bytes())
def protected_heads():
    values={}
    for name in ['fm3-continuation.json','current-increment-run.json']:
        p=ROOT/name;values[name]=sha(p.read_bytes())
    return values
