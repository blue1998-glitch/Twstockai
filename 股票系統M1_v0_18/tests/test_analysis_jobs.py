import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import analysis_jobs as api
from contracts import DataError,SCHEMA_VERSION,fingerprint
from jobs import run_job
from moving_averages import analyze_daily_ma


def sample_job(n=6):
    from datetime import date,timedelta
    candles=[dict(date=(date(2026,1,1)+timedelta(days=i)).isoformat(),open='100',high='102',low='99',close=str(100+i/10),volume_shares_scaled='1000') for i in range(n)]
    return dict(schema_version=api.REQUEST_SCHEMA,code='FIXTURE',exchange='TPEX',price_mode='RAW_CANDIDATE',timeframe='daily',
                source=dict(id='TEST_FIXTURE',code='FIXTURE',exchange='TPEX',volume_unit='SHARES_SCALED_FROM_LOTS'),
                candles=candles,corporate_actions=dict(records=[],coverage_status='UNVERIFIED'))


class AnalysisJobTests(unittest.TestCase):
    def test_both_components_equal_standalone_calls_and_do_not_mutate_input(self):
        j=sample_job();before=copy.deepcopy(j);r=api.run_analysis_job(j)
        legacy=copy.deepcopy(j);legacy['schema_version']=SCHEMA_VERSION
        self.assertEqual(r['components']['structure'],run_job(legacy))
        self.assertEqual(r['components']['daily_ma'],analyze_daily_ma(j['candles'],[],code=j['code'],mode=j['price_mode']))
        self.assertEqual(j,before);r['shared_input']['source']['id']='changed'
        self.assertEqual(j['source']['id'],'TEST_FIXTURE')

    def test_version_and_source_validation_reject_before_second_engine(self):
        for field,value in [('schema_version',SCHEMA_VERSION),('price_mode','AUTO')]:
            j=sample_job();j[field]=value
            with self.assertRaises(DataError):api.run_analysis_job(j)
        for field,value in [('code','OTHER'),('exchange','TWSE'),('volume_unit','LOTS'),('id',3)]:
            j=sample_job();j['source'][field]=value
            with patch.object(api,'analyze_daily_ma') as ma:
                with self.assertRaises(DataError):api.run_analysis_job(j)
                ma.assert_not_called()

    def test_malformed_calendar_never_escapes_as_untyped_error(self):
        for dates in ['weekday-only',{},[{}],[['2026-01-01']],['2026-01-01']*2,['2026-02-30']]:
            j=sample_job();j['expected_dates']=dates
            with self.assertRaises(DataError):api.run_analysis_job(j)

    def test_supplied_calendar_is_shared_context_not_source_certification(self):
        j=sample_job();j['expected_dates']=[c['date'] for c in j['candles']]
        r=api.run_analysis_job(j)
        self.assertEqual(r['shared_input']['data_quality']['calendar_status'],'MATCHES_SUPPLIED_CALENDAR')
        self.assertEqual(r['components']['daily_ma']['data_quality']['calendar_status'],'UNVERIFIED')
        j['expected_dates'].append('2026-01-09');r=api.run_analysis_job(j)
        self.assertEqual(r['shared_input']['data_quality']['missing_dates'],['2026-01-09'])
        self.assertEqual(len(r['aligned_snapshots']),6)
        previous=r['aligned_snapshots'][0]['snapshot_id']
        j['expected_dates'].append('2025-12-31')
        self.assertNotEqual(previous,api.run_analysis_job(j)['aligned_snapshots'][0]['snapshot_id'])

    def test_empty_input_is_empty_not_completed(self):
        r=api.run_analysis_job(sample_job(0));self.assertEqual(r['status'],'EMPTY_INPUT')
        self.assertEqual(r['aligned_snapshots'],[])
        self.assertEqual(r['components']['daily_ma']['snapshots'],[])

    def test_deterministic_ids_and_no_future_change_to_earlier_joint_snapshots(self):
        j=sample_job();r=api.run_analysis_job(j);self.assertEqual(r,api.run_analysis_job(j))
        future=copy.deepcopy(j);future['candles'][-1]['close']='101'
        changed=api.run_analysis_job(future)
        self.assertNotEqual(r['analysis_id'],changed['analysis_id'])
        self.assertEqual(r['aligned_snapshots'][:-1],changed['aligned_snapshots'][:-1])
        earlier=copy.deepcopy(j);earlier['candles']=earlier['candles'][:5]
        self.assertEqual(r['aligned_snapshots'][:5],api.run_analysis_job(earlier)['aligned_snapshots'])

    def test_component_mismatch_is_rejected(self):
        j=sample_job();base=analyze_daily_ma(j['candles'],[],code=j['code'],mode=j['price_mode'])
        for field,value in [('code','OTHER'),('price_mode','ADJUSTED_CANDIDATE'),('data_fingerprint','bad')]:
            broken=copy.deepcopy(base);broken[field]=value
            with patch.object(api,'analyze_daily_ma',return_value=broken):
                with self.assertRaises(DataError) as e:api.run_analysis_job(j)
                self.assertEqual(e.exception.code,'COMPONENT_ALIGNMENT')
        for field,value in [('as_of','2020-01-01'),('events_fingerprint','bad')]:
            broken=copy.deepcopy(base);broken['snapshots'][0][field]=value
            with patch.object(api,'analyze_daily_ma',return_value=broken):
                with self.assertRaises(DataError):api.run_analysis_job(j)

    def test_nonfinite_extra_value_is_a_data_error(self):
        j=sample_job();j['extension']=float('nan')
        with self.assertRaises(DataError) as e:api.run_analysis_job(j)
        self.assertEqual(e.exception.code,'NON_JSON_VALUE')

    def test_cli_success_and_typed_invalid_input(self):
        with tempfile.TemporaryDirectory() as d:
            inp=Path(d)/'request.json';out=Path(d)/'result.json'
            inp.write_text(json.dumps(sample_job()))
            cmd=[sys.executable,str(ROOT/'src/analysis_jobs.py'),'--input',str(inp),'--output',str(out)]
            r=subprocess.run(cmd,capture_output=True);self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads(out.read_text())['status'],'COMPLETED')
            inp.write_text('broken');r=subprocess.run(cmd,capture_output=True)
            self.assertEqual(r.returncode,2);error=json.loads(out.read_text())
            self.assertEqual(error['status'],'DATA_ERROR');self.assertNotIn('components',error)
            self.assertFalse(list(Path(d).glob('*.tmp')))

    def test_cli_protects_input_and_reports_output_write_failure(self):
        with tempfile.TemporaryDirectory() as d:
            inp=Path(d)/'request.json';inp.write_text(json.dumps(sample_job()));original=inp.read_bytes()
            cmd=[sys.executable,str(ROOT/'src/analysis_jobs.py'),'--input',str(inp),'--output']
            same=subprocess.run(cmd+[str(inp)],capture_output=True)
            self.assertEqual(same.returncode,3);self.assertEqual(inp.read_bytes(),original)
            self.assertEqual(json.loads(same.stderr)['code'],'INPUT_OUTPUT_COLLISION')
            failed=subprocess.run(cmd+[d],capture_output=True)
            self.assertEqual(failed.returncode,3);self.assertEqual(json.loads(failed.stderr)['code'],'OUTPUT_FILE_ERROR')
            self.assertFalse(list(Path(d).glob('*.tmp')))

    def test_real_generated_jobs_preserve_all_baseline_outputs(self):
        for code in ['8069','6488']:
            j=json.loads((ROOT/'data'/f'{code}_analysis_job.json').read_text())
            self.assertEqual(j['candles'],json.loads((ROOT/'data'/f'{code}_candles.json').read_text()))
            self.assertEqual(j['corporate_actions']['records'],json.loads((ROOT/'data'/f'{code}_events.json').read_text()))
            for mode in ['RAW_CANDIDATE','ADJUSTED_CANDIDATE']:
                r=json.loads((ROOT/'output'/f'{code}_{mode}_ANALYSIS.json').read_text())
                structure=json.loads((ROOT/'output'/f'{code}_{mode}.json').read_text())
                self.assertEqual({k:r['components']['structure'][k] for k in structure},structure)
                self.assertEqual(r['components']['daily_ma'],json.loads((ROOT/'output'/f'{code}_{mode}_MA.json').read_text()))
                self.assertEqual(len(r['aligned_snapshots']),283)
                for joint,s,m in zip(r['aligned_snapshots'],r['components']['structure']['snapshots'],r['components']['daily_ma']['snapshots']):
                    self.assertEqual(joint['input_quality_fingerprint'],fingerprint(s['data_quality']))
                    self.assertEqual(joint['structure_snapshot_id'],s['snapshot_id'])
                    self.assertEqual(joint['daily_ma_snapshot_id'],m['snapshot_id'])
                self.assertEqual(r['action_qualification'],'NOT_EVALUATED')
                self.assertEqual(r['shared_input']['data_fingerprint'],fingerprint(j['candles']))


if __name__=='__main__':unittest.main()
