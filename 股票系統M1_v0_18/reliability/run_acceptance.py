"""Explicit fault injection on private temporary copies of the supplement DB.

Never target a user database. Faults are deliberately uncommitted invalid
objects. The only recovery is the pre-existing independent store CLI.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'reliability')]
from analysis_store import AnalysisStore
from contracts import fingerprint
from sqlite_probe import files, probe


def run(args, expected=0):
    p = subprocess.run([sys.executable, *map(str, args)], capture_output=True,
                       text=True, timeout=120,
                       env={**os.environ, 'PYTHONPATH': str(ROOT / 'src')})
    if p.returncode != expected:
        raise AssertionError(dict(args=list(map(str, args)), exit=p.returncode,
                                  stdout=p.stdout[-2000:], stderr=p.stderr[-2000:]))
    return p


def full_state(path):
    store = AnalysisStore(path)
    return dict(stats=store.stats(), records={
        m['record_id']: fingerprint(store.load(m['record_id']))
        for m in store.list_records()})


def main():
    source = ROOT / 'cross_view/output/補齊日線.sqlite3'
    source_before = files(source)
    assert all(not source_before[s].get('exists', True) for s in ('-journal', '-wal', '-shm')), 'Stop writers and preserve sidecars before copying'
    baseline = full_state(source)
    rounds = []
    for iteration in range(3):
        with tempfile.TemporaryDirectory(prefix='m1-incident-') as temp:
            work = Path(temp)
            db = work / 'isolated.sqlite3'
            shutil.copy2(source, db)
            # Existing saved results, not numeric regeneration. Each save and
            # readback occurs in its own process, matching content identity.
            clean = []
            for record_id in baseline['records']:
                code = """import sys,json
from analysis_store import AnalysisStore
s=AnalysisStore(sys.argv[1]);r=s.load(sys.argv[2]);receipt=s.save(r['request'],r['result'],r['evidence'],reason=r['reason']);print(json.dumps(receipt))
"""
                receipt = json.loads(run(['-c', code, db, record_id]).stdout)
                assert receipt['status'] == 'EXISTING'
                assert full_state(db) == baseline
                clean.append(dict(record_id=record_id, status=receipt['status']))
            fault = """import sqlite3,sys,os
c=sqlite3.connect(sys.argv[1]);c.execute('PRAGMA cache_size=8');c.execute('BEGIN IMMEDIATE');c.execute('INSERT INTO objects VALUES(?,?,?,?)',('fault','request','fault','x'*2000000));os._exit(17)
"""
            run(['-c', fault, db], expected=17)
            incident = probe(db)
            assert incident['observation']['sqlite_errorcode'] == 776, incident
            assert incident['observed_files_unchanged']
            assert incident['after']['-journal']['bytes'] > 512
            hot = files(db)
            config = work / 'sources.json'
            config.write_text(json.dumps(dict(schema_version='cross-timeframe-sources/1.0',
                daily_stores={'isolated': str(db)},
                period_stores={'unchanged': str(ROOT / 'period_workflow/output/背景流程結果庫')},
                as_of_dates=['2026-09-30'])))
            output = work / 'existing-output.html'
            output.write_text('PRESERVE_PREVIOUS_OUTPUT')
            read = run([ROOT / 'src/cross_view_cli.py', '--config', config,
                        '--html', '--output', output], expected=2)
            error = json.loads(read.stderr)
            assert error['database_access'] == 'READ_ONLY_NO_RECOVERY'
            assert error['code'] == 'STORE_DATABASE', error
            assert files(db) == hot, 'Viewer modified incident files'
            assert output.read_text() == 'PRESERVE_PREVIOUS_OUTPUT'
            recovery = json.loads(run([ROOT / 'src/store_cli.py', 'recover', '--db', db]).stdout)
            assert recovery['status'] == 'VERIFIED_READABLE'
            after = full_state(db)
            assert after == baseline
            assert not Path(str(db) + '-journal').exists()
            clean_probe = probe(db)
            assert clean_probe['observation']['status'] == 'READABLE'
            assert clean_probe['observed_files_unchanged']
            rounds.append(dict(iteration=iteration + 1, clean_saves=clean,
                injected_writer_exit=17, incident=incident, viewer_failure=error,
                viewer_preserved_database_and_journal=True, previous_output_preserved=True,
                recovery=recovery, recovered_full_content=after,
                recovery_preserved_all_committed_results=True,
                uncommitted_object_absent=(after['stats']['objects'] == 9)))
    assert files(source) == source_before, 'Published source changed'
    report = dict(status='PASS', method='Three isolated temporary copies; deliberate uncommitted process termination',
        rounds=rounds, clean_fresh_process_saves=9, fault_recovery_rounds=3,
        baseline=baseline, published_source_unchanged=True,
        original_incident_root_cause='NOT_ESTABLISHED',
        original_incident_limit='Matching symptoms demonstrate a possible mechanism, not the cause of the historical loss after reported commits',
        engines_or_storage_implementation_changed=False,
        classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED')
    out = ROOT / 'reliability/output/SQLite故障重現驗收.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({k:v for k,v in report.items() if k != 'rounds'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
