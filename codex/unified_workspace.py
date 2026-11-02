"""Cooperative single-writer entry check. No source repairs or environment changes.
Environment ID must come from this thread's CURRENT environment_status tool.
A supplied string alone is not platform identity/authentication verification.
"""
import argparse,contextlib,fcntl,json,os,subprocess,sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'股票系統M1_v0_18'))
from rotation_research.private_portability import validate_report,quiet_source,private

POLICY=REPO/'docs/engineering-governance/unify1_20261102/policy.json'

def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()


def check(policy,environment_id,*,git_state=None):
    """Read-only metadata reuse of an existing full audit; never rehash data."""
    issues=[];result=dict(schema='unified-workspace-check/0.1',data_sha_repeated=False,environment_id=environment_id,issues=issues)
    if environment_id!=policy['environment_id']:
        issues.append('WRONG_CLOUD_DO_NOT_WRITE');result['status']='BLOCKED';return result
    try:
        if git_state is None:
            origin=git('remote','get-url','origin')
            if origin not in ('https://github.com/'+policy['repository'],'https://github.com/'+policy['repository']+'.git','git@github.com:'+policy['repository']+'.git'):issues.append('WRONG_ORIGIN_DO_NOT_WRITE')
            git_state=dict(root=git('rev-parse','--show-toplevel'),branch=git('branch','--show-current'),head=git('rev-parse','HEAD'),remote=git('ls-remote','origin','refs/heads/'+policy['branch']).split()[0])
            if Path(git('rev-parse','--path-format=absolute','--git-path','index.lock')).exists():issues.append('GIT_INDEX_OPERATION_BUSY')
            if subprocess.run(['git','-C',str(REPO),'merge-base','--is-ancestor',policy['minimum_ancestor'],git_state['head']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:issues.append('REQUIRED_ANCESTOR_MISSING')
        result['git']=git_state
        if git_state['root']!=policy['repository_root'] or git_state['branch']!=policy['branch']:issues.append('WRONG_REPOSITORY_OR_BRANCH')
        if git_state['head']!=git_state['remote']:issues.append('REFS_DIFFER_READ_LATEST_HANDOFF_BEFORE_WRITE')
        root=private(policy['fm3_root']);manifest=private(policy['private_manifest'])
        if not root.is_dir():issues.append('FM3_UNAVAILABLE_HERE_NOT_PROOF_OF_GLOBAL_LOSS')
        elif not manifest.is_file():issues.append('PRIVATE_AUDIT_UNAVAILABLE_DO_NOT_SUBSTITUTE_GITHUB_SUMMARY')
        else:
            report=json.loads(manifest.read_bytes());validate_report(report)
            if report['manifest_id']!=policy['private_manifest_id'] or report['observed_root']!=str(root):raise ValueError('PRIVATE_RECEIPT_BINDING_CHANGED')
            with quiet_source(root):
                paths={str(p.relative_to(root)):p for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
                if set(paths)!={f['path'] for f in report['files']}:raise ValueError('FM3_FILE_SET_CHANGED_REQUIRE_NEW_AUDIT')
                for entry in report['files']:
                    p=paths[entry['path']];s=p.stat()
                    if any(a.is_symlink() for a in (p,*p.parents)) or (s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev)!=(entry['bytes'],entry['mtime_ns'],entry['source_inode'],entry['source_device']):raise ValueError('FM3_METADATA_OR_FILESYSTEM_CHANGED_REQUIRE_REVIEW')
                # Verify access, not just same folder name or stat existence.
                with (root/'fm3-continuation.json').open('rb') as f:f.read(1)
            result['fm3']=dict(readable=True,unchanged_metadata_paths=len(paths),audit_manifest_id=report['manifest_id'],method='Reuse M-PORT1 full SHA audit plus unchanged path/size/mtime/inode/device; no new full SHA pass')
        lock=private(policy['engineering_lock'])
        if not lock.is_file():issues.append('ENGINEERING_LOCK_NOT_PROVISIONED')
        else:
            with lock.open('rb') as f:
                try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:issues.append('ENGINEERING_WRITER_BUSY_DO_NOT_START_SECOND_WRITER')
    except Exception as e:issues.append(type(e).__name__+':'+str(e) if isinstance(e,(ValueError,BlockingIOError)) else type(e).__name__)
    result['status']='READY_FOR_AUTHORIZED_TASK' if not issues else 'BLOCKED';return result


@contextlib.contextmanager
def engineering_lease(path):
    """Existing Git-external lock; cooperating child task holds this entire time."""
    lock=private(path)
    with lock.open('rb') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--environment-id',required=True);p.add_argument('--run',nargs=argparse.REMAINDER,help='Only the already-authorized local task argv; no shell or background daemon')
    args=p.parse_args();policy=json.loads(POLICY.read_bytes());result=check(policy,args.environment_id)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    if result['status']!='READY_FOR_AUTHORIZED_TASK':raise SystemExit(2)
    if args.run:
        command=args.run
        if command[0]=='--':command=command[1:]
        if not command:p.error('--run requires an authorized command')
        with engineering_lease(policy['engineering_lock']):
            # Close race between precheck and lease. Other entry points must obey same lock.
            if git('rev-parse','HEAD')!=git('ls-remote','origin','refs/heads/'+policy['branch']).split()[0]:raise RuntimeError('REMOTE_CHANGED_BEFORE_AUTHORIZED_TASK')
            raise SystemExit(subprocess.run(command,cwd=REPO,close_fds=True).returncode)

if __name__=='__main__':main()
