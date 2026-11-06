"""One local synthetic rehearsal, source->isolated restore->source-free verify.
No real private source copy, network, engine call or external deployment.
"""
import argparse,json,subprocess,sys
from pathlib import Path
from graph_core.port1_20261102.fixture import make
from rotation_research.private_portability import private,write_private


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',required=True);a=p.parse_args();work=private(a.work)
    if work.exists():raise FileExistsError('New synthetic rehearsal directory required')
    work.mkdir(mode=0o700,parents=True);source=make(work/'synthetic-source');manifest=work/'synthetic-inventory-private.json';dest=work/'isolated-restored'
    actions=[['inspect','--root',str(source),'--manifest',str(manifest)],['restore','--root',str(source),'--manifest',str(manifest),'--destination',str(dest)],['verify','--root',str(dest),'--manifest',str(manifest)]]
    results=[]
    for i,args in enumerate(actions):
        run=subprocess.run([sys.executable,'-m','rotation_research.private_portability',*args],capture_output=True,text=True)
        (work/('step-'+str(i)+'-private.log')).write_text(run.stdout+run.stderr)
        if run.returncode:raise RuntimeError('Synthetic CLI rehearsal failed at step '+str(i))
        results.append(json.loads(run.stdout))
    report=dict(status='PASS_SYNTHETIC_ISOLATED_RESTORE',source_class='SYNTHETIC_ENGINEERING_FIXTURE_NOT_PROVIDER_SAMPLE',
        steps=[dict(action=x[0],exit_code=0) for x in actions],files=results[0]['counts']['files'],du2_artifacts=results[0]['counts']['du2_logical_artifacts'],
        full_original_bytes_match=results[1]['full_original_bytes_match'],source_preserved=results[1]['original_source_preserved'],
        restored_hardlink_groups_match=results[2]['verification']['hardlink_groups_match'],source_reads_required_for_verify=results[2]['verification']['source_reads_required'],
        core_runs=0,source_requests=0,real_fm3_copied=False,external_backup=False,restart_restore='NOT_TESTED')
    write_private(work/'summary.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
