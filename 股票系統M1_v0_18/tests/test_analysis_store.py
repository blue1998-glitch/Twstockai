"""Real engine output persisted, fault-injected transactions and CLI processes."""
from copy import deepcopy
import json,os,sqlite3,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from analysis_jobs import run_analysis_job
from analysis_store import AnalysisStore
from contracts import DataError,fingerprint


def fixture():
    q=json.loads((ROOT/'data_audit/1101_analysis_job.json').read_text());q['candles']=q['candles'][:24]
    q['expected_dates']=[c['date'] for c in q['candles']]
    e=dict(schema_version='analysis-evidence/1.0',code=q['code'],coverage_status='UNVERIFIED',records=[dict(status='UNVERIFIED',reason='Storage fixture; no event promotion')])
    return q,run_analysis_job(q),e

class StoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.q,cls.r,cls.e=fixture()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'research.sqlite3';self.store=AnalysisStore.create(self.path)
    def save(self,q=None,r=None,e=None):return self.store.save(q or self.q,r or self.r,e or self.e,reason='test import')
    def test_close_reopen_preserves_unknown_quality_and_whole_payloads(self):
        receipt=self.save();out=AnalysisStore(self.path).load(receipt['record_id'])
        self.assertEqual((out['request'],out['result'],out['evidence']),(self.q,self.r,self.e))
        self.assertEqual(out['evidence']['coverage_status'],'UNVERIFIED');self.assertEqual(out['result']['action_qualification'],'NOT_EVALUATED')
    def test_repeat_import_does_not_duplicate_or_change_first_receipt(self):
        first=self.save();before=self.store.stats();created=self.store.load(first['record_id'])['created_at_utc']
        second=self.save();self.assertEqual(second['status'],'EXISTING');self.assertEqual(self.store.stats(),before)
        self.assertEqual(created,self.store.load(second['record_id'])['created_at_utc'])
    def test_source_revision_produces_new_run_and_keeps_old_snapshot(self):
        first=self.save();q=deepcopy(self.q);q['source']['revision']='controlled-metadata-test'
        r=run_analysis_job(q);second=self.save(q,r)
        self.assertNotEqual(first['analysis_id'],second['analysis_id']);self.assertEqual(self.store.stats()['analyses'],2)
        self.assertEqual(self.store.load(first['record_id'])['result'],self.r)
    def test_new_evidence_preserves_old_record_without_repeating_computation(self):
        first=self.save();e=deepcopy(self.e);e['records'].append(dict(status='UNVERIFIED',revision='context-only'))
        second=self.save(e=e);stats=self.store.stats()
        self.assertEqual(first['analysis_id'],second['analysis_id']);self.assertNotEqual(first['record_id'],second['record_id'])
        self.assertEqual((stats['analyses'],stats['records'],stats['snapshots']),(1,2,24))
        self.assertEqual(self.store.load(first['record_id'])['evidence'],self.e)
    def test_changed_rule_metadata_is_separate_even_with_empty_input(self):
        # Explicit empty-input producer-version fixture, not a new real algorithm.
        q=deepcopy(self.q);q['candles']=[];q['expected_dates']=[];r=run_analysis_job(q);first=self.save(q,r)
        other=deepcopy(r);other['components']['structure']['rule_version']='empty-fixture-version-2'
        other['component_versions']['structure']='empty-fixture-version-2'
        other['analysis_id']=fingerprint(dict(request=fingerprint(q),versions=other['component_versions'],parameters={k:v['parameters_fingerprint'] for k,v in other['components'].items()},adapter=other['adapter_version']))
        second=self.save(q,other);self.assertNotEqual(first['analysis_id'],second['analysis_id'])
        self.assertEqual(self.store.load(first['record_id'])['rules']['component_versions'],r['component_versions'])
    def test_different_result_at_same_run_id_is_conflict(self):
        first=self.save();r=deepcopy(self.r);r['limitations'].append('Different returned content')
        with self.assertRaisesRegex(DataError,'STORE_RESULT_CONFLICT'):self.save(r=r)
        self.assertEqual(self.store.load(first['record_id'])['result'],self.r)
    def test_injected_failure_rolls_back_all_objects_and_indexes(self):
        before=self.store.stats()
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER inject_failure BEFORE INSERT ON objects WHEN NEW.kind='result' BEGIN SELECT RAISE(ABORT,'injected write failure'); END")
        with self.assertRaisesRegex(DataError,'STORE_DATABASE'):self.save()
        self.assertEqual(self.store.stats(),before);self.assertEqual(self.store.list_records(),[])
    def test_terminated_writer_recovers_without_partial_data_or_lost_history(self):
        rec=self.save();before=self.store.stats()
        # Force cache spill so the interrupted transaction leaves a hot journal.
        script="import sqlite3,sys,os;db=sqlite3.connect(sys.argv[1]);db.execute('PRAGMA cache_size=8');db.execute('BEGIN IMMEDIATE');db.execute('INSERT INTO objects VALUES(?,?,?,?)',('fault','request','fault','x'*2000000));os._exit(17)"
        child=subprocess.run([sys.executable,'-c',script,str(self.path)],capture_output=True,text=True,timeout=15)
        self.assertEqual(child.returncode,17)
        # A new independent recovery process must finish before read-only load.
        cmd=[sys.executable,str(ROOT/'src/store_cli.py'),'recover','--db',str(self.path)]
        recovery=subprocess.run(cmd,capture_output=True,text=True,timeout=15)
        self.assertEqual(recovery.returncode,0,recovery.stdout+recovery.stderr)
        self.assertEqual(json.loads(recovery.stdout)['status'],'VERIFIED_READABLE')
        self.assertEqual(AnalysisStore(self.path).stats(),before)
        self.assertEqual(AnalysisStore(self.path).load(rec['record_id'])['result'],self.r)
    def test_direct_updates_are_blocked_by_history_trigger(self):
        self.save()
        with sqlite3.connect(self.path) as db:
            with self.assertRaises(sqlite3.IntegrityError):db.execute("UPDATE records SET reason='overwrite'")
    def test_modified_stored_json_fingerprint_detected(self):
        rec=self.save()
        with sqlite3.connect(self.path) as db:
            db.execute('DROP TRIGGER immutable_objects_update')
            db.execute("UPDATE objects SET payload='{}' WHERE kind='result'")
        with self.assertRaisesRegex(DataError,'STORE_INTEGRITY'):self.store.load(rec['record_id'])
    def test_missing_snapshot_index_detected(self):
        rec=self.save()
        with sqlite3.connect(self.path) as db:
            db.execute('DROP TRIGGER immutable_snapshots_delete');db.execute('DELETE FROM snapshots WHERE as_of=(SELECT min(as_of) FROM snapshots)')
        with self.assertRaisesRegex(DataError,'STORE_INTEGRITY'):self.store.load(rec['record_id'])
    def test_wrong_request_or_evidence_identity_rejected_without_writes(self):
        q=deepcopy(self.q);q['source']['revision']='not computed'
        with self.assertRaises(DataError):self.save(q=q)
        e=deepcopy(self.e);e['code']='2884'
        with self.assertRaises(DataError):self.save(e=e)
        self.assertEqual(self.store.stats()['objects'],0)
    def test_nonfinite_json_is_rejected_before_database_writes(self):
        e=deepcopy(self.e);e['bad']=float('nan')
        with self.assertRaisesRegex(DataError,'STORE_JSON'):self.save(e=e)
        self.assertEqual(self.store.stats()['objects'],0)
    def test_initialization_never_replaces_existing_file(self):
        before=self.path.read_bytes()
        with self.assertRaisesRegex(DataError,'STORE_EXISTS'):AnalysisStore.create(self.path)
        self.assertEqual(before,self.path.read_bytes())
    def test_read_missing_or_bad_database_does_not_initialize_it(self):
        missing=Path(self.temp.name)/'missing.db'
        with self.assertRaises(DataError):AnalysisStore(missing).stats()
        self.assertFalse(missing.exists())
        bad=Path(self.temp.name)/'bad.db';bad.write_bytes(b'not a sqlite file')
        with self.assertRaises(DataError):AnalysisStore(bad).stats()
        self.assertEqual(bad.read_bytes(),b'not a sqlite file')
    def test_unknown_schema_version_is_rejected(self):
        with sqlite3.connect(self.path) as db:db.execute('PRAGMA user_version=999')
        with self.assertRaisesRegex(DataError,'STORE_VERSION'):self.store.stats()
    def test_exact_snapshot_and_parameterized_stock_filter(self):
        rec=self.save();dt=self.q['candles'][20]['date'];out=self.store.snapshot(rec['record_id'],dt)
        self.assertEqual(out['structure'],self.r['components']['structure']['snapshots'][20])
        self.assertEqual(self.store.list_records("1101' OR 1=1 --"),[])
        with self.assertRaisesRegex(DataError,'STORE_NOT_FOUND'):self.store.snapshot(rec['record_id'],'2026-01-01')
    def test_cli_output_cannot_overwrite_database_or_hardlinked_input(self):
        before=self.path.read_bytes()
        r=subprocess.run([sys.executable,str(ROOT/'src/store_cli.py'),'stats','--db',str(self.path),'--output',str(self.path)],capture_output=True,text=True)
        self.assertEqual(r.returncode,2);self.assertEqual(before,self.path.read_bytes())
        inputs={}
        for name,obj in [('request',self.q),('result',self.r),('evidence',self.e)]:
            path=Path(self.temp.name)/(name+'.json');path.write_text(json.dumps(obj));inputs[name]=path
        alias=Path(self.temp.name)/'request-hardlink.json';os.link(inputs['request'],alias)
        r=subprocess.run([sys.executable,str(ROOT/'src/store_cli.py'),'save','--db',str(self.path),'--request',str(inputs['request']),'--result',str(inputs['result']),'--evidence',str(inputs['evidence']),'--reason','collision test','--output',str(alias)],capture_output=True,text=True)
        self.assertEqual(r.returncode,2);self.assertEqual(json.loads(inputs['request'].read_text()),self.q)
        self.assertEqual(self.store.stats()['records'],0)
    def test_two_independent_processes_deduplicate_same_import(self):
        paths=[]
        for name,obj in [('request',self.q),('result',self.r),('evidence',self.e)]:
            p=Path(self.temp.name)/(name+'.json');p.write_text(json.dumps(obj));paths.append(p)
        cmd=[sys.executable,str(ROOT/'src/store_cli.py'),'save','--db',str(self.path),'--request',str(paths[0]),'--result',str(paths[1]),'--evidence',str(paths[2]),'--reason','separate process test']
        ps=[subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
        outs=[]
        for p in ps:
            out,err=p.communicate(timeout=15);self.assertEqual(p.returncode,0,err+out);outs.append(json.loads(out))
        self.assertEqual({r['status'] for r in outs},{'CREATED','EXISTING'});self.assertNotEqual(outs[0]['process_id'],outs[1]['process_id'])
        self.assertEqual(self.store.stats()['records'],1)

if __name__=='__main__':unittest.main()
