"""One private finite continuation of an already-authorized FM3 cohort.

No cron, service, Git operation or trading. Waits for the conservative local
budget, then resumes the same original Journal checkpoints. Any provider denial
or source-code change stops it. Container lifetime/persistence is not guaranteed.
"""
import argparse
from datetime import datetime,timezone
import hashlib,json,os,time
from pathlib import Path
from graph_core.market_finmind import run,external_path,ROOT
from graph_core.market_preview import build
from graph_core.market_daily import encode


def continue_batch(root,reference_run,start,limit=240):
    root=external_path(root);lock=root/'fm3-continuation.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    files=[ROOT/p for p in ['graph_core/market_finmind.py','graph_core/finmind_adapter.py',
        'graph_core/core.py','graph_core/market_preview.py','product_candidate/macd.py',
        'graph_core_chart/viewer.js','graph_core/fm3_20261101/lazy_series.js','graph_core/fm1_20261101/search.js']]
    frozen={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    def state(value):
        value.update(observed_at=datetime.now(timezone.utc).isoformat(),pid=os.getpid())
        tmp=root/'fm3-continuation.pending';tmp.write_bytes(encode(value));os.chmod(tmp,0o600);os.replace(tmp,root/'fm3-continuation.json')
    try:
        os.write(fd,str(os.getpid()).encode())
        while True:
            if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha for p,sha in frozen.items()):
                state(dict(status='BLOCKED_SOURCE_CHANGED',no_auto_migration=True));return
            try:
                result=run(root,reference_run,start,limit=limit)
                preview=build(root,result['id'])
            except Exception as error:
                state(dict(status='STOPPED_SOURCE_OR_EXECUTION',error_type=type(error).__name__,automatic_retry=False));return
            if result['summary']['pause_reason']!='LOCAL_FREE_HOURLY_BUDGET_EXHAUSTED':
                state(dict(status='FINISHED_COHORT_WITH_EXPLICIT_QUALIFICATIONS' if not result['summary']['pause_reason'] else 'STOPPED_PROVIDER_OR_SOURCE',result=result,preview=preview));return
            used=[json.loads(p.read_text())['value']['epoch'] for p in (root/'source-slots').glob('*.json')]
            active=sorted(t for t in used if t>time.time()-3600)
            ready=max(active)+3601 if active else time.time()+1  # resume a whole conservative window, not one repeated tiny rebuild
            state(dict(status='WAITING_CONSERVATIVE_FREE_BUDGET',result=result,preview=preview,
                       next_budget_at=datetime.fromtimestamp(ready,timezone.utc).isoformat(),
                       provider_denial_observed=False,scheduled_service_installed=False,persistence='UNKNOWN'))
            while time.time()<ready:time.sleep(min(60,max(0,ready-time.time())))
    finally:
        os.close(fd);lock.unlink()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--reference-run',required=True)
    p.add_argument('--start',required=True);p.add_argument('--limit',type=int,default=240);a=p.parse_args()
    continue_batch(a.root,a.reference_run,a.start,a.limit)
