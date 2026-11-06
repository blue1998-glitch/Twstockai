"""Fixed standalone contracts, executable separation and export failures."""
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import json,os,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from contracts import DataError
from period_jobs import run_period_job,_write
from test_period_ma import weekdays


def job():
    return dict(schema_version='stock-period-analysis/1.0',code='FIXTURE',exchange='TWSE',timeframe='daily',price_mode='RAW_CANDIDATE',
                source=dict(id='synthetic-contract-fixture',code='FIXTURE',exchange='TWSE',volume_unit='SHARES_REPORTED'),
                candles=weekdays('2026-01-05','2026-05-29'),corporate_actions=dict(records=[],coverage_status='UNVERIFIED'),as_of='2026-05-31')


class PeriodJobTests(unittest.TestCase):
    def test_fixed_job_is_deterministic_and_does_not_mutate_input(self):
        q=job();before=deepcopy(q);r=run_period_job(q)
        self.assertEqual(q,before);self.assertEqual(r,run_period_job(q));self.assertEqual(r['schema_version'],'period-analysis-result/1.0')
        self.assertEqual(r['corporate_action_coverage'],'UNVERIFIED');self.assertEqual(r['snapshot']['classification_quality'],'NOT_VALIDATED')

    def test_unknown_fields_scope_source_and_coverage_fail_as_data_errors(self):
        for key,value in [('asof','2026-05-31'),('schema_version','stock-analysis/1.0'),('timeframe','weekly'),('exchange','UNKNOWN'),('source',{}),('corporate_actions',{'records':[]})]:
            q=job();q[key]=value
            with self.assertRaises(DataError):run_period_job(q)
        for field,value in [('code','OTHER'),('volume_unit','LOTS'),('id',None)]:
            q=job();q['source'][field]=value
            with self.assertRaises(DataError):run_period_job(q)

    def test_full_request_identity_can_change_while_earlier_snapshot_remains_same(self):
        q=job();q['as_of']='2026-03-01';a=run_period_job(q);q['candles'][-1]['close']=q['candles'][-1]['open'];b=run_period_job(q)
        self.assertNotEqual(a['request_fingerprint'],b['request_fingerprint']);self.assertNotEqual(a['analysis_id'],b['analysis_id']);self.assertEqual(a['snapshot'],b['snapshot'])

    def test_cli_and_adapter_work_with_ui_sql_and_old_job_modules_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'request.json';path.write_text(json.dumps(job()))
            script="""import sys,json,importlib.abc
sys.path.insert(0,sys.argv[1])
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname.split('.')[0] in {'sqlite3','streamlit','fastapi','analysis_store','store_contracts','analysis_workflow','analysis_jobs','jobs'}:raise AssertionError('Forbidden dependency '+fullname)
sys.meta_path.insert(0,Guard())
from period_jobs import run_period_job
assert run_period_job(json.load(open(sys.argv[2])))['snapshot']['weekly']['elapsed']['latest']['4']['available']
"""
            p=subprocess.run([sys.executable,'-c',script,str(ROOT/'src'),str(path)],capture_output=True,text=True,timeout=15)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)

    def test_cli_success_duplicate_keys_and_invalid_json_are_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            inp=Path(d)/'in.json';out=Path(d)/'out.json';inp.write_text(json.dumps(job()))
            cmd=[sys.executable,str(ROOT/'src/period_jobs.py'),'--input',str(inp),'--output',str(out)]
            r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads(out.read_text()),run_period_job(job()))
            for content in ['broken','{"schema_version":1,"schema_version":2}']:
                inp.write_text(content);r=subprocess.run(cmd,capture_output=True,text=True)
                self.assertEqual(r.returncode,2);self.assertEqual(json.loads(out.read_text())['status'],'DATA_ERROR')

    def test_cli_does_not_overwrite_input_or_alias_and_reports_output_failure(self):
        with tempfile.TemporaryDirectory() as d:
            inp=Path(d)/'in.json';inp.write_text(json.dumps(job()));before=inp.read_bytes()
            hard=Path(d)/'hard.json';os.link(inp,hard);sym=Path(d)/'sym.json';sym.symlink_to(inp)
            cmd=[sys.executable,str(ROOT/'src/period_jobs.py'),'--input',str(inp),'--output']
            for out in [inp,hard,sym,Path(d)/'missing'/'out.json']:
                r=subprocess.run(cmd+[str(out)],capture_output=True,text=True);self.assertEqual(r.returncode,3,r.stdout+r.stderr)
            self.assertEqual(inp.read_bytes(),before)

    def test_atomic_write_failure_preserves_prior_result_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'out.json';out.write_text('previous')
            with patch('period_jobs.os.replace',side_effect=OSError('injected export failure')):
                with self.assertRaises(OSError):_write(out,run_period_job(job()))
            self.assertEqual(out.read_text(),'previous');self.assertEqual(list(Path(d).glob('.period-*')),[])


if __name__=='__main__':unittest.main()
