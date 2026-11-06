"""Read-only artifact/preservation audit. Does not import or run the checker."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).parent
ROOT=HERE.parents[2]


def load(path):
    return json.loads(path.read_text())


def matches(row):
    payload=(ROOT/row['path']).read_bytes()
    return len(payload)==row['bytes'] and hashlib.sha256(payload).hexdigest()==row['sha256']


def verify(*, with_manifest=True):
    intake=load(HERE/'intake.json')
    sources=load(HERE/'source-versions-before-execution.json')['sources']
    summary=load(HERE/'summary.json')
    run=load(HERE/'test-run.json')
    protected=load(HERE/'preservation-before.json')['files']
    checks=dict(input_and_oracle_unchanged=all(matches(x) for x in intake['input_expected_files']),
                source_versions_unchanged=all(matches(x) for x in sources),
                protected_old_files_unchanged=all(matches(x) for x in protected),
                cases_saved_before_implementation=intake['checker_exists'] is False,
                no_old_tracked_diff=subprocess.run(['git','diff','--quiet','HEAD'],cwd=ROOT).returncode==0,
                index_empty=subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode==0,
                exact_original_tracked_index=True,all_saved_oracles_matched=True,
                diagnostic_flags_remain_false=True,artifact_hashes_match=True,checker_imports_only_stdlib=True)
    current=[]
    for entry in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).decode().split('\0'):
        if entry:
            meta,path=entry.split('\t',1);mode,blob,stage=meta.split()
            current.append(dict(path=path,mode=mode,blob=blob,stage=stage))
    checks['exact_original_tracked_index']=current==load(HERE/'tracked-index-before.json')
    allowed={'copy','datetime','decimal','hashlib','json','re'}
    tree=ast.parse((HERE.parent/'opening_evidence.py').read_text())
    imports={n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
    imports.update(a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names)
    checks['checker_imports_only_stdlib']=imports<=allowed
    for row in summary['cases']:
        directory=HERE/'cases'/row['case']
        expected,actual=load(directory/'expected.json'),load(directory/'actual.json')
        field=actual['fields'][expected['field']]
        checks['all_saved_oracles_matched'] &= (row['matched'] and actual['status']==expected['status'] and
            field['classification']==expected['classification'] and field['declared_value']==expected['preserved_value'] and
            (not expected['required_gap'] or expected['required_gap'] in field['gaps']) and
            (not expected['required_unsupported'] or dict(field=expected['field'],reason=expected['required_unsupported']) in actual['unsupported_capabilities']))
        for kind in ('input','expected','actual'):
            content=(directory/(kind+'.json')).read_bytes()
            checks['artifact_hashes_match'] &= row[kind]==dict(bytes=len(content),sha256=hashlib.sha256(content).hexdigest())
        checks['diagnostic_flags_remain_false'] &= all(actual[k] is False for k in
            ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized',
             'live_execution_authorized','authenticity_verified','opening_entitlements_verified','ledger_called'))
        checks['diagnostic_flags_remain_false'] &= actual['legacy_qualification_updates']=={} and actual['cash_or_share_postings']==[] and actual['primary_pressure_id'] is None
    log=(HERE/'tests-final.log').read_text()
    names=[line.split(' ',1)[0] for line in log.splitlines() if line.startswith('test_')]
    checks['saved_test_log_consistent']=run['exit_code']==0 and len(names)==len(set(names))==21 and 'Ran 21 tests' in log and log.rstrip().endswith('OK')
    manifest_count=None
    if with_manifest:
        manifest=load(HERE/'CHANGE_MANIFEST.json');manifest_count=len(manifest['files'])
        actual_paths={str(p.relative_to(ROOT)) for p in HERE.rglob('*') if p.is_file() and p.name!='CHANGE_MANIFEST.json'}
        actual_paths.update(str(p.relative_to(ROOT)) for p in (HERE.parent/'opening_evidence.py',ROOT/'M1_OPENING_ENTITLEMENTS_EVIDENCE_20261026_HANDOFF.md'))
        checks['manifest_hashes_match']=all(matches(x) for x in manifest['files'])
        checks['manifest_exact_paths']={x['path'] for x in manifest['files']}==actual_paths
    if not all(checks.values()):
        raise AssertionError(json.dumps(checks,ensure_ascii=False,indent=2))
    return dict(schema='opening-evidence-readonly-audit/0.1',checks=checks,all_passed=True,
        manifest_checked=with_manifest,manifest_entries=manifest_count,
        saved_test_methods=21,tests_executed_by_this_audit=0,producer_calls=0,
        note='File/JSON/log consistency only; no original-source authentication, strategy validation or fresh PASS count')


if __name__=='__main__':
    print(json.dumps(verify(),ensure_ascii=False,indent=2))
