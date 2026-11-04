from pathlib import Path
import json,hashlib,shutil,math
from rotation_research import artifact_codec as c
BASE=Path('/workspace/twstockai-local-data')
ROOT=BASE/'fm3_20261101/runtime'
WORK=BASE/'graph_lazy1_20261104'
REPO=Path(__file__).resolve().parents[3]
PROJECT=REPO/'股票系統M1_v0_18'
RESERVE=536870912
LIMIT=16*1024**2
sha=c.sha
encode=c.encoded
read_json=lambda p:json.loads(Path(p).read_bytes())
def budget(n=0):
    initial=read_json(WORK/'baseline-private.json')['free_bytes'];free=shutil.disk_usage(WORK).free
    if free-math.ceil(n/4096)*4096-65536<RESERVE or initial-free+math.ceil(n/4096)*4096+65536>LIMIT:raise OSError('LAZY1_CAPACITY_BUDGET_STOP')
    return free
def write(p,b):
    p=Path(p)
    if not p.resolve().is_relative_to(WORK) or any(a.is_symlink() for a in (p,*p.parents)):raise ValueError('NEW_LAZY_ROOT_ONLY')
    budget(len(b) if not p.exists() else 0);c.immutable(p,b)
def heads():return {n:sha((ROOT/n).read_bytes()) for n in ['fm3-continuation.json','current-increment-run.json']}
