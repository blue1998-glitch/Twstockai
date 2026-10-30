"""Workflow integration, ambiguous commit recovery, and input protection."""
from copy import deepcopy
import json,os,sqlite3,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from analysis_workflow import execute_workflow,WorkflowError,SCHEMA
from analysis_store import AnalysisStore
from analysis_jobs import run_analysis_job
from contracts import DataError,fingerprint
from test_analysis_store import fixture

class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.q,cls.r,cls.e=fixture()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.db=Path(self.temp.name)/'workflow.sqlite3'
        self.request=dict(schema_version=SCHEMA,operation='RUN',job=deepcopy(self.q),evidence=deepcopy(self.e),reason='workflow test')
    def run_request(self,req=None):return execute_workflow(req or self.request,self.db,create_if_missing=True)
    def test_run_read_and_lookup_preserve_real_engine_payload_and_input(self):
        req=deepcopy(self.request);req['include_bundle']=True;before=deepcopy(req)
        run=self.run_request(req);self.assertEqual(req,before)
        self.assertEqual(run['saved_bundle']['result'],self.r);self.assertEqual(run['commit_status'],'COMMITTED')
        read=execute_workflow(dict(schema_version=SCHEMA,operation='READ',record_id=run['record_id']),self.db)
        self.assertNotIn('saved_bundle',read);self.assertEqual(read['snapshot']['structure'],self.r['components']['structure']['snapshots'][-1])
        self.assertEqual(read['evidence_coverage'],'UNVERIFIED');self.assertEqual(read['action_qualification'],'NOT_EVALUATED')
        lookup=execute_workflow(dict(schema_version=SCHEMA,operation='LOOKUP',job=self.q,evidence=self.e),self.db)
        self.assertEqual(lookup['status'],'FOUND');self.assertEqual(lookup['matches'][0]['record_id'],run['record_id'])
    def test_repeat_run_does_not_duplicate_saved_records(self):
        first=self.run_request();stats=AnalysisStore(self.db).stats();second=self.run_request()
        self.assertEqual(second['store_status'],'EXISTING');self.assertEqual(first['record_id'],second['record_id']);self.assertEqual(stats,AnalysisStore(self.db).stats())
    def test_invalid_price_fails_before_database_initialization(self):
        req=deepcopy(self.request);req['job']['candles'][0]['close']='NaN'
        with self.assertRaises(WorkflowError) as cm:self.run_request(req)
        self.assertEqual((cm.exception.stage,cm.exception.commit_status),('CALCULATE','NOT_SAVED'));self.assertFalse(self.db.exists())
    def test_wrong_evidence_rejected_before_calculation(self):
        req=deepcopy(self.request);req['evidence']['code']='2884'
        with patch('analysis_workflow.run_analysis_job') as engine:
            with self.assertRaises(WorkflowError):self.run_request(req)
            engine.assert_not_called()
        self.assertFalse(self.db.exists())
    def test_absent_requested_date_rejected_before_saving(self):
        req=deepcopy(self.request);req['as_of']='2026-01-01'
        with self.assertRaises(WorkflowError) as cm:self.run_request(req)
        self.assertEqual(cm.exception.stage,'VALIDATE');self.assertFalse(self.db.exists())
    def test_calculation_exception_leaves_no_database(self):
        with patch('analysis_workflow.run_analysis_job',side_effect=RuntimeError('injected calculation failure')):
            with self.assertRaises(WorkflowError) as cm:self.run_request()
        self.assertEqual(cm.exception.stage,'CALCULATE');self.assertFalse(self.db.exists())
    def test_bad_existing_database_never_recreated(self):
        self.db.write_bytes(b'existing non-database file')
        with self.assertRaises(WorkflowError) as cm:self.run_request()
        self.assertEqual(cm.exception.stage,'PREPARE_STORE');self.assertEqual(self.db.read_bytes(),b'existing non-database file')
    def test_save_failure_rolls_back_all_content_and_can_be_looked_up(self):
        store=AnalysisStore.create(self.db)
        with sqlite3.connect(self.db) as db:db.execute("CREATE TRIGGER inject_failure BEFORE INSERT ON objects WHEN NEW.kind='result' BEGIN SELECT RAISE(ABORT,'write failure'); END")
        with self.assertRaises(WorkflowError) as cm:self.run_request()
        self.assertEqual((cm.exception.stage,cm.exception.commit_status),('SAVE','UNKNOWN'))
        self.assertEqual(store.stats()['objects'],0)
        lookup=execute_workflow(dict(schema_version=SCHEMA,operation='LOOKUP',job=self.q,evidence=self.e),self.db)
        self.assertEqual(lookup['status'],'NOT_FOUND')
    def test_lost_save_ack_is_found_without_recalculation_or_duplication(self):
        original=AnalysisStore.save
        def lost_ack(store,*a,**kw):original(store,*a,**kw);raise RuntimeError('ack lost after commit')
        with patch.object(AnalysisStore,'save',lost_ack):
            with self.assertRaises(WorkflowError) as cm:self.run_request()
        err=cm.exception.as_dict();self.assertEqual(err['commit_status'],'UNKNOWN');self.assertEqual(err['recovery_operation'],'LOOKUP')
        with patch('analysis_workflow.run_analysis_job',side_effect=AssertionError('LOOKUP must not calculate')):
            found=execute_workflow(dict(schema_version=SCHEMA,operation='LOOKUP',job=self.q,evidence=self.e),self.db)
        self.assertEqual(found['status'],'FOUND');repeat=self.run_request();self.assertEqual(repeat['store_status'],'EXISTING')
        self.assertEqual(repeat['record_id'],found['matches'][0]['record_id']);self.assertEqual(AnalysisStore(self.db).stats()['records'],1)
    def test_failed_readback_reports_committed_record_and_is_recoverable(self):
        with patch.object(AnalysisStore,'load',side_effect=DataError('INJECTED_READ','record','readback unavailable')):
            with self.assertRaises(WorkflowError) as cm:self.run_request()
        err=cm.exception.as_dict();self.assertEqual(err['commit_status'],'COMMITTED');self.assertEqual(err['recovery_operation'],'READ')
        read=execute_workflow(dict(schema_version=SCHEMA,operation='READ',record_id=err['record_id']),self.db)
        self.assertEqual(read['result_fingerprint'],fingerprint(self.r))
    def test_read_absent_date_never_substitutes_or_adds_records(self):
        rec=self.run_request();before=AnalysisStore(self.db).stats()
        with self.assertRaises(WorkflowError):execute_workflow(dict(schema_version=SCHEMA,operation='READ',record_id=rec['record_id'],as_of='2026-01-01'),self.db)
        self.assertEqual(before,AnalysisStore(self.db).stats())
    def test_empty_input_remains_explicit_without_invented_snapshot(self):
        req=deepcopy(self.request);req['job']['candles']=[];req['job']['expected_dates']=[]
        out=self.run_request(req);self.assertEqual(out['computation_status'],'EMPTY_INPUT');self.assertIsNone(out['snapshot']);self.assertEqual(out['bars'],0)
    def test_multiple_rule_versions_lookup_does_not_choose_latest(self):
        q=deepcopy(self.q);q['candles']=[];q['expected_dates']=[];r=run_analysis_job(q);store=AnalysisStore.create(self.db)
        store.save(q,r,self.e,reason='empty rule metadata fixture')
        second=deepcopy(r);second['components']['structure']['rule_version']='empty-version-fixture-2';second['component_versions']['structure']='empty-version-fixture-2'
        second['analysis_id']=fingerprint(dict(request=fingerprint(q),versions=second['component_versions'],parameters={k:v['parameters_fingerprint'] for k,v in second['components'].items()},adapter=second['adapter_version']))
        store.save(q,second,self.e,reason='second empty metadata fixture, not new strategy')
        out=execute_workflow(dict(schema_version=SCHEMA,operation='LOOKUP',job=q,evidence=self.e),self.db)
        self.assertEqual(out['status'],'MULTIPLE_VERSION_MATCHES');self.assertEqual(len(out['matches']),2)
    def test_typo_fields_and_nonboolean_options_rejected(self):
        for extra in [dict(asof='2026-01-01'),dict(include_bundle=1)]:
            req=deepcopy(self.request);req.update(extra)
            with self.assertRaises(WorkflowError):self.run_request(req)
        self.assertFalse(self.db.exists())
    def test_cli_output_collision_guards_input_hardlink_and_recovery_sidecar(self):
        source=Path(self.temp.name)/'request.json';source.write_text(json.dumps(self.request));alias=Path(self.temp.name)/'alias.json';os.link(source,alias)
        for out in [alias,self.db,Path(str(self.db)+'-journal')]:
            p=subprocess.run([sys.executable,str(ROOT/'src/workflow_cli.py'),'--input',str(source),'--db',str(self.db),'--create','--output',str(out)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0);self.assertEqual(json.loads(p.stdout)['code'],'WORKFLOW_OUTPUT_COLLISION')
        self.assertEqual(json.loads(source.read_text()),self.request);self.assertFalse(self.db.exists())
    def test_core_runs_with_all_storage_and_workflow_imports_blocked(self):
        source=Path(self.temp.name)/'core.json';source.write_text(json.dumps(self.q))
        script="""import sys,json,importlib.abc
sys.path.insert(0,sys.argv[1])
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname.split('.')[0] in {'sqlite3','analysis_store','analysis_workflow','store_cli','workflow_cli','store_contracts'}:raise AssertionError('Core imported storage or workflow')
sys.meta_path.insert(0,Guard())
from analysis_jobs import run_analysis_job
result=run_analysis_job(json.load(open(sys.argv[2])))
print(result['status'])
"""
        p=subprocess.run([sys.executable,'-c',script,str(ROOT/'src'),str(source)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(p.stdout.strip(),'COMPLETED')

if __name__=='__main__':unittest.main()
