import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from contracts import DataError, fingerprint
from period_store import PeriodStore, StoreFailure
from period_workflow import execute_period_workflow, WorkflowError, SCHEMA
from period_workflow_cli import main


def fixture():
    q=json.loads((ROOT/'period_analysis/requests/1101_RAW_CANDIDATE.json').read_text())
    r=json.loads((ROOT/'period_analysis/output/1101_RAW_CANDIDATE_PERIOD.json').read_text())
    return q,r


class PeriodWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=self.base/'store';self.q,self.expected=fixture()
        self.request=dict(schema_version=SCHEMA,operation='RUN',job=self.q,reason='v0.15 真實結果流程驗收',include_bundle=True)
        self.aid=self.expected['analysis_id']

    def run_job(self,**kwargs):return execute_period_workflow(self.request,self.root,**kwargs)
    def read(self,aid=None):return execute_period_workflow(dict(schema_version=SCHEMA,operation='READ',analysis_id=aid or self.aid,include_bundle=True),self.root)
    def filters(self):return {k:self.q[k] for k in ('code','exchange','price_mode','as_of')}
    def lookup(self,filters=None):return execute_period_workflow(dict(schema_version=SCHEMA,operation='LOOKUP',filters=filters or self.filters()),self.root)
    def files(self):return {p.name:p.read_bytes() for p in self.root.iterdir()}
    def command(self,cmd=None):
        path=self.base/'command.json';path.write_text(json.dumps(cmd or self.request,ensure_ascii=False));return path
    def cli(self,path,out,create=False):
        args=[sys.executable,str(ROOT/'src/period_workflow_cli.py'),'--store',str(self.root),'--input',str(path),'--output',str(out)]
        if create:args.append('--create')
        return subprocess.run(args,capture_output=True,text=True,timeout=30)

    def test_run_calls_engine_once_and_returns_exact_saved_content(self):
        from period_jobs import run_period_job
        with patch('period_jobs.run_period_job',wraps=run_period_job) as engine:
            response=self.run_job(create_if_missing=True)
        self.assertEqual(engine.call_count,1);self.assertEqual(response['commit_status'],'COMMITTED')
        self.assertEqual(response['saved_bundle']['result'],self.expected)
        self.assertEqual(response['snapshot'],self.expected['snapshot'])
        self.assertEqual(response['saved_bundle'],PeriodStore(self.root).load(self.aid))

    def test_explicit_run_retry_deduplicates_and_preserves_request(self):
        before=copy.deepcopy(self.request);self.run_job(create_if_missing=True);saved=self.files()
        result=self.run_job()
        self.assertEqual(result['store_status'],'DUPLICATE');self.assertEqual(saved,self.files());self.assertEqual(before,self.request)

    def test_preflight_unknown_fields_and_wrong_types_do_not_call_engine(self):
        from period_jobs import run_period_job
        variants=[None,[],dict(self.request,extra=1),dict(self.request,operation=['RUN']),dict(self.request,include_bundle=1),dict(self.request,reason=' '),dict(self.request,reason='x'*2001),dict(self.request,schema_version='bad'),dict(self.request,job=[])]
        with patch('period_jobs.run_period_job',wraps=run_period_job) as engine:
            for command in variants:
                with self.subTest(command=repr(command)[:70]),self.assertRaises(WorkflowError) as e:execute_period_workflow(command,self.root,create_if_missing=True)
                self.assertEqual(e.exception.stage,'VALIDATE')
        self.assertEqual(engine.call_count,0);self.assertFalse(self.root.exists())

    def test_read_lookup_and_cli_import_no_numeric_modules_in_fresh_process(self):
        self.run_job(create_if_missing=True);before=self.files()
        payload=self.base/'read.json';payload.write_text(json.dumps(dict(schema_version=SCHEMA,operation='READ',analysis_id=self.aid,include_bundle=True)))
        code="""import sys,json,importlib.abc
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname in ('period_jobs','period_ma','structure','daily_ma','jobs','analysis_jobs','analysis_store','analysis_workflow'):raise RuntimeError('ENGINE IMPORT '+fullname)
sys.meta_path.insert(0,Block())
from period_workflow import execute_period_workflow
from period_workflow_cli import main
assert main(['--store',sys.argv[1],'--input',sys.argv[2],'--output',sys.argv[3]])==0
f=json.loads(sys.argv[4]);r=execute_period_workflow(dict(schema_version='period-workflow/1.0',operation='LOOKUP',filters=f),sys.argv[1]);assert r['status']=='FOUND'
"""
        p=subprocess.run([sys.executable,'-c',code,str(self.root),str(payload),str(self.base/'readout.json'),json.dumps(self.filters())],env={**os.environ,'PYTHONPATH':str(ROOT/'src')},capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(before,self.files())

    def test_lookup_exact_date_versions_and_request_fingerprint(self):
        self.run_job(create_if_missing=True)
        self.assertEqual(self.lookup()['status'],'FOUND')
        for key,value in [('as_of','2026-09-29'),('rule_version','nonexistent'),('request_fingerprint','sha256:'+'0'*64)]:
            f={**self.filters(),key:value};r=self.lookup(f);self.assertEqual(r['status'],'NOT_FOUND');self.assertEqual(r['matches'],[])
        f={**self.filters(),'request_fingerprint':fingerprint(self.q)};self.assertEqual(self.lookup(f)['matches'][0]['analysis_id'],self.aid)

    def test_lookup_multiple_requests_never_picks_one(self):
        self.run_job(create_if_missing=True);cmd=copy.deepcopy(self.request);cmd['job']['source']['note']='別份完整來源中繼資料；不代表新行情'
        other=execute_period_workflow(cmd,self.root);self.assertNotEqual(self.aid,other['analysis_id'])
        r=self.lookup();self.assertEqual(r['status'],'MULTIPLE_MATCHES');self.assertEqual(len(r['matches']),2);self.assertNotIn('snapshot',r)
        f={**self.filters(),'request_fingerprint':fingerprint(self.q)};self.assertEqual(len(self.lookup(f)['matches']),1)

    def test_missing_store_requires_explicit_create(self):
        with self.assertRaises(WorkflowError) as e:self.run_job()
        self.assertEqual(e.exception.stage,'PREPARE_STORE');self.assertEqual(e.exception.commit_status,'NOT_SAVED');self.assertFalse(self.root.exists())

    def test_read_lookup_never_create_even_when_create_flag_requested(self):
        commands=[dict(schema_version=SCHEMA,operation='READ',analysis_id=self.aid),dict(schema_version=SCHEMA,operation='LOOKUP',filters=self.filters())]
        for cmd in commands:
            for create in (False,True):
                with self.subTest(cmd=cmd['operation'],create=create),self.assertRaises(WorkflowError) as e:execute_period_workflow(cmd,self.root,create_if_missing=create)
                self.assertEqual(e.exception.commit_status,'NOT_APPLICABLE');self.assertFalse(self.root.exists())

    def test_conflicting_reason_preserves_old_record(self):
        self.run_job(create_if_missing=True);before=self.files();self.request['reason']='另一個理由不能改舊紀錄'
        with self.assertRaises(WorkflowError) as e:self.run_job()
        self.assertEqual(e.exception.code,'PERIOD_STORE_CONFLICT');self.assertEqual(e.exception.commit_status,'NOT_SAVED');self.assertEqual(e.exception.as_dict()['recovery_operation'],'READ');self.assertEqual(before,self.files())

    def test_bad_market_input_fails_before_store_creation(self):
        self.q['candles'][0]['high']='-1'
        with self.assertRaises(WorkflowError) as e:self.run_job(create_if_missing=True)
        self.assertEqual(e.exception.stage,'CALCULATE');self.assertEqual(e.exception.commit_status,'NOT_SAVED');self.assertFalse(self.root.exists())

    def test_invalid_engine_output_fails_before_store_creation(self):
        r=copy.deepcopy(self.expected);r['status']='WRONG'
        with patch('period_jobs.run_period_job',return_value=r),self.assertRaises(WorkflowError) as e:self.run_job(create_if_missing=True)
        self.assertEqual(e.exception.stage,'VALIDATE_RESULT');self.assertFalse(self.root.exists())

    def test_precommit_io_error_reports_not_saved(self):
        PeriodStore.create(self.root)
        with patch('period_store.os.link',side_effect=OSError('disk failure')),self.assertRaises(WorkflowError) as e:self.run_job()
        self.assertEqual(e.exception.commit_status,'NOT_SAVED');self.assertEqual(e.exception.identities['analysis_id'],self.aid);self.assertEqual(self.lookup()['status'],'NOT_FOUND')

    def test_postcommit_fsync_error_is_unknown_and_resolved_by_read(self):
        PeriodStore.create(self.root)
        with patch('period_store._sync_dir',side_effect=OSError('directory fsync failure')),self.assertRaises(WorkflowError) as e:self.run_job()
        self.assertEqual(e.exception.commit_status,'UNKNOWN');self.assertEqual(e.exception.as_dict()['recovery_operation'],'READ')
        self.assertEqual(self.read()['saved_bundle']['result'],self.expected);self.assertEqual(self.run_job()['store_status'],'DUPLICATE')

    def test_unexpected_error_after_save_does_not_claim_not_saved(self):
        PeriodStore.create(self.root);save=PeriodStore.save
        def saved_then_failed(store,*args,**kwargs):save(store,*args,**kwargs);raise RuntimeError('lost acknowledgment')
        with patch.object(PeriodStore,'save',new=saved_then_failed),self.assertRaises(WorkflowError) as e:self.run_job()
        self.assertEqual(e.exception.commit_status,'UNKNOWN');self.assertEqual(self.read()['snapshot'],self.expected['snapshot'])

    def test_readback_failure_remains_committed_without_memory_fallback(self):
        PeriodStore.create(self.root)
        with patch.object(PeriodStore,'load',side_effect=StoreFailure('TEST_READ','read blocked')),self.assertRaises(WorkflowError) as e:self.run_job()
        self.assertEqual(e.exception.stage,'READ_BACK');self.assertEqual(e.exception.commit_status,'COMMITTED')
        self.assertEqual(self.read()['saved_bundle']['result'],self.expected)

    def test_wrong_readback_content_is_rejected_after_commit(self):
        PeriodStore.create(self.root);load=PeriodStore.load
        def wrong(store,aid):
            r=load(store,aid);r['reason']='incorrect return';return r
        with patch.object(PeriodStore,'load',new=wrong),self.assertRaises(WorkflowError) as e:self.run_job()
        self.assertEqual(e.exception.commit_status,'COMMITTED');self.assertEqual(e.exception.stage,'READ_BACK')
        self.assertEqual(self.read()['saved_bundle']['reason'],self.request['reason'])

    def killed(self,after):
        PeriodStore.create(self.root);path=self.command()
        code="""import os,json,sys;from pathlib import Path;import period_store
from period_workflow import execute_period_workflow
if sys.argv[3]=='after':period_store._sync_dir=lambda *a:os._exit(82)
else:period_store.os.link=lambda *a:os._exit(81)
execute_period_workflow(json.loads(Path(sys.argv[1]).read_text()),sys.argv[2])
"""
        return subprocess.run([sys.executable,'-c',code,str(path),str(self.root),'after' if after else 'before'],env={**os.environ,'PYTHONPATH':str(ROOT/'src')},capture_output=True)

    def test_process_terminated_before_commit_has_no_phantom_and_retry_works(self):
        p=self.killed(False);self.assertEqual(p.returncode,81);before=self.files()
        self.assertEqual(self.lookup()['status'],'NOT_FOUND');self.assertEqual(before,self.files())
        self.assertEqual(len(PeriodStore(self.root).diagnostics()['pending_files']),1)
        self.assertEqual(self.run_job()['store_status'],'SAVED');self.assertEqual(len(PeriodStore(self.root).diagnostics()['pending_files']),1)

    def test_process_terminated_after_commit_read_and_retry_without_cleanup(self):
        p=self.killed(True);self.assertEqual(p.returncode,82);before=self.files()
        self.assertEqual(self.read()['saved_bundle']['result'],self.expected);self.assertEqual(before,self.files())
        self.assertEqual(self.run_job()['store_status'],'DUPLICATE');self.assertEqual(len(PeriodStore(self.root).diagnostics()['pending_files']),1)

    def test_concurrent_explicit_runs_commit_once(self):
        PeriodStore.create(self.root);path=self.command()
        args=[sys.executable,str(ROOT/'src/period_workflow_cli.py'),'--store',str(self.root),'--input',str(path),'--output']
        ps=[subprocess.Popen(args+[str(self.base/f'result{i}.json')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for i in range(4)]
        statuses=[]
        for p in ps:
            out,err=p.communicate(timeout=30);self.assertEqual(p.returncode,0,err);r=json.loads(out);statuses.append(r['store_status']);self.assertEqual(r['analysis_id'],self.aid)
        self.assertEqual(statuses.count('SAVED'),1);self.assertEqual(statuses.count('DUPLICATE'),3);self.assertEqual(len(PeriodStore(self.root).list()),1)

    def test_cli_end_to_end_file_contains_complete_saved_bundle(self):
        out=self.base/'result.json';p=self.cli(self.command(),out,True)
        self.assertEqual(p.returncode,0,p.stderr);receipt=json.loads(p.stdout);self.assertEqual(receipt['commit_status'],'COMMITTED');self.assertEqual(receipt['workflow_status'],'COMPLETED')
        saved=json.loads(out.read_text())['saved_bundle'];self.assertEqual(saved['result'],self.expected);self.assertEqual(saved,PeriodStore(self.root).load(self.aid))

    def test_output_failure_after_commit_can_be_read_by_another_worker(self):
        p=self.cli(self.command(),self.base/'absent/result.json',True)
        self.assertEqual(p.returncode,3);error=json.loads(p.stderr);self.assertEqual(error['stage'],'EXPORT');self.assertEqual(error['commit_status'],'COMMITTED');self.assertEqual(error['analysis_id'],self.aid)
        cmd=self.command(dict(schema_version=SCHEMA,operation='READ',analysis_id=error['analysis_id'],include_bundle=True));out=self.base/'read.json';p=self.cli(cmd,out)
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(out.read_text())['saved_bundle']['result'],self.expected)

    def test_atomic_export_failure_preserves_existing_output(self):
        cmd=self.command();out=self.base/'result.json';out.write_text('prior response')
        err=io.StringIO()
        with patch('period_store_cli.os.replace',side_effect=OSError('replace failed')),patch('sys.stderr',err):
            code=main(['--store',str(self.root),'--input',str(cmd),'--output',str(out),'--create'])
        self.assertEqual(code,3);self.assertEqual(out.read_text(),'prior response');self.assertEqual(json.loads(err.getvalue())['commit_status'],'COMMITTED');self.assertEqual(self.read()['saved_bundle']['result'],self.expected)

    def test_output_collisions_fail_before_engine_and_preserve_files(self):
        from period_jobs import run_period_job
        self.run_job(create_if_missing=True);before=self.files();cmd=self.command();hard=self.base/'hard.json';os.link(cmd,hard)
        symlink=self.base/'symlink.json';symlink.symlink_to(cmd)
        record=self.root/(self.aid[7:]+'.json');hard_record=self.base/'hard_record.json';os.link(record,hard_record)
        with patch('period_jobs.run_period_job',wraps=run_period_job) as engine:
            for out in (cmd,hard,symlink,record,hard_record,self.root/'new.json'):
                err=io.StringIO()
                with patch('sys.stderr',err):code=main(['--store',str(self.root),'--input',str(cmd),'--output',str(out)])
                self.assertEqual(code,3);self.assertEqual(json.loads(err.getvalue())['stage'],'FILE_PREFLIGHT')
        self.assertEqual(engine.call_count,0);self.assertEqual(before,self.files())

    def test_duplicate_json_keys_and_nonfinite_cli_values_fail_without_writes(self):
        cmd=self.base/'bad.json'
        for text in ('{"operation":"RUN","operation":"READ"}',json.dumps(dict(self.request,bad=float('nan')))):
            cmd.write_text(text);p=self.cli(cmd,self.base/'out.json',True);self.assertNotEqual(p.returncode,0);json.loads(p.stderr);self.assertFalse(self.root.exists());self.assertFalse((self.base/'out.json').exists())

    def test_read_corruption_fails_and_preserves_all_files(self):
        self.run_job(create_if_missing=True);p=self.root/(self.aid[7:]+'.json');p.write_text(p.read_text().replace('v0.15 真實結果流程驗收','tampered'))
        before=self.files()
        for f in (self.read,self.lookup):
            with self.assertRaises(WorkflowError) as e:f()
            self.assertEqual(e.exception.commit_status,'NOT_APPLICABLE')
        self.assertEqual(before,self.files())

    def test_empty_input_stays_empty_with_computation_status_disclosed(self):
        self.q['candles']=[];self.q['corporate_actions']['records']=[];self.q.pop('calendar',None)
        r=self.run_job(create_if_missing=True);self.assertEqual(r['computation_status'],'EMPTY_INPUT');self.assertEqual(r['snapshot']['last_price_date'],None)
        self.assertEqual(r['snapshot']['weekly']['bars'],[]);self.assertIsNone(r['snapshot']['monthly']['candidate']['latest']['24']['value'])

    def test_stdout_failure_preserves_committed_identity_and_written_output(self):
        cmd=self.command();out=self.base/'result.json';errors=[]
        def fake_print(value,**kw):
            if kw.get('file') is sys.stderr:errors.append(json.loads(value))
            else:raise BrokenPipeError('response pipe closed')
        with patch('period_workflow_cli.print',new=fake_print,create=True):code=main(['--store',str(self.root),'--input',str(cmd),'--output',str(out),'--create'])
        self.assertEqual(code,3);self.assertEqual(errors[0]['stage'],'STDOUT');self.assertEqual(errors[0]['commit_status'],'COMMITTED');self.assertEqual(errors[0]['analysis_id'],self.aid);self.assertTrue(out.exists())


if __name__=='__main__':unittest.main()
