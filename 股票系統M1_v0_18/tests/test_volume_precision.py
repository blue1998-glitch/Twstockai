"""Source-unit provenance is explicit; numeric decisions and old reads persist."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from contracts import DataError,fingerprint
from structure import analyze,Config,VOLUME_PRECISION,VERSION,_run_prefix
from analysis_jobs import run_analysis_job
from analysis_store import AnalysisStore
from analysis_workflow import execute_workflow
from store_contracts import validate_bundle
from test_structure import candles
from test_analysis_store import fixture


class VolumePrecisionTests(unittest.TestCase):
    def inputs(self):
        return candles([10,12,14,16,18,20,22,22,20,18,16,18,20,24,22,19,17])
    def analyze(self,unit,cs=None):
        return analyze(cs if cs is not None else self.inputs(),code='T',mode='RAW_CANDIDATE',source_id='fixture',volume_unit=unit,
                       cfg=Config(window=2,minor_multiple='1',major_multiple='2'))

    def test_native_and_scaled_evidence_follow_explicit_unit_without_rescaling(self):
        cs=self.inputs();before=deepcopy(cs);a=self.analyze('SHARES_REPORTED',cs);b=self.analyze('SHARES_SCALED_FROM_LOTS',cs)
        self.assertEqual(cs,before)
        for r,unit in [(a,'SHARES_REPORTED'),(b,'SHARES_SCALED_FROM_LOTS')]:
            self.assertEqual(r['volume_unit'],unit);self.assertEqual(r['rule_version'],VERSION)
            self.assertTrue(r['snapshots'][-1]['pivots'])
            self.assertTrue(all(s['volume_unit']==unit for s in r['snapshots']))
            self.assertTrue(all(p['evidence']['volume_precision']==VOLUME_PRECISION[unit] for p in r['snapshots'][-1]['pivots']))
        for x,y in zip(a['snapshots'][-1]['pivots'],b['snapshots'][-1]['pivots']):
            x=deepcopy(x);y=deepcopy(y);x['evidence'].pop('volume_precision');y['evidence'].pop('volume_precision');self.assertEqual(x,y)
        self.assertEqual(a['snapshots'][-1]['zones'],b['snapshots'][-1]['zones'])

    def test_unit_affects_snapshot_identity_even_without_pivots(self):
        a=self.analyze('SHARES_REPORTED',self.inputs()[:1]);b=self.analyze('SHARES_SCALED_FROM_LOTS',self.inputs()[:1])
        s=a['snapshots'][0]
        self.assertNotEqual(s['snapshot_id'],b['snapshots'][0]['snapshot_id'])
        self.assertEqual(s['snapshot_id'],fingerprint(dict(code='T',mode='RAW_CANDIDATE',as_of=s['as_of'],rule_version=VERSION,
                         parameters=s['parameters_fingerprint'],data=s['data_fingerprint'],events=s['effective_events_fingerprint'],volume_unit='SHARES_REPORTED')))
        self.assertEqual(a,self.analyze('SHARES_REPORTED',self.inputs()[:1]))

    def test_missing_or_unsupported_public_unit_is_typed_error_even_for_empty_input(self):
        for unit in [None,'','LOTS','AUTO',True,{},[]]:
            with self.assertRaisesRegex(DataError,'UNSUPPORTED_UNIT'):self.analyze(unit,[])
        with self.assertRaisesRegex(DataError,'UNSUPPORTED_UNIT'):
            analyze([],code='T',mode='RAW_CANDIDATE',source_id='fixture')

    def test_internal_numeric_fixture_does_not_guess_volume_origin(self):
        cfg=Config(window=2,minor_multiple='1',major_multiple='2')
        p=_run_prefix(self.inputs(),cfg)['pivots'][0]
        self.assertEqual(p['evidence']['volume_precision'],'Volume origin unspecified; share values retained without rescaling')

    def test_shared_job_boundary_passes_unit_and_rejects_invalid_before_ma(self):
        q,_,_=fixture()
        for unit in VOLUME_PRECISION:
            j=deepcopy(q);j['source']['volume_unit']=unit;r=run_analysis_job(j)
            self.assertEqual(r['components']['structure']['volume_unit'],unit)
        for unit in [None,'LOTS',True,[],{}]:
            j=deepcopy(q);j['source']['volume_unit']=unit
            with patch('analysis_jobs.analyze_daily_ma') as ma:
                with self.assertRaises(DataError):run_analysis_job(j)
                ma.assert_not_called()

    def test_null_and_zero_volume_context_are_preserved(self):
        cs=self.inputs();cs[0]['volume_shares_scaled']=None;cs[1]['volume_shares_scaled']='0'
        r=self.analyze('SHARES_REPORTED',cs)
        self.assertEqual(r['data_quality']['missing_volume_bars'],1)
        self.assertEqual(r['data_quality']['volume_context'],'PARTIAL')
        self.assertIsNone(cs[0]['volume_shares_scaled']);self.assertEqual(cs[1]['volume_shares_scaled'],'0')

    def test_new_unit_fields_must_match_source_at_storage_boundary(self):
        q,r,e=fixture();validate_bundle(q,r,e)
        for mutation in ['root','snapshot','missing']:
            other=deepcopy(r)
            if mutation=='root':other['components']['structure']['volume_unit']='SHARES_SCALED_FROM_LOTS'
            elif mutation=='snapshot':other['components']['structure']['snapshots'][0]['volume_unit']='SHARES_SCALED_FROM_LOTS'
            else:other['components']['structure'].pop('volume_unit')
            with self.assertRaisesRegex(DataError,'STORE_BUNDLE_MISMATCH'):validate_bundle(q,other,e)

    def test_legacy_real_record_is_read_without_engine_execution(self):
        db=ROOT/'workflow/output/分析流程_v0_10.sqlite3';store=AnalysisStore(db)
        row=store.list_records('1101')[0];before=db.read_bytes()
        with patch('analysis_workflow.run_analysis_job',side_effect=AssertionError('READ must not calculate')):
            reply=execute_workflow(dict(schema_version='analysis-workflow/1.0',operation='READ',record_id=row['record_id']),db)
        self.assertEqual(reply['component_versions']['structure'],'structure-0.2-research')
        self.assertNotIn('volume_unit',reply['snapshot']['structure']);self.assertEqual(before,db.read_bytes())

    def test_old_acceptance_runners_stop_before_touching_historical_outputs(self):
        for runner,db,proof in [('workflow/run_acceptance.py','workflow/output/分析流程_v0_10.sqlite3','workflow/output/單一分析保存流程驗收.json'),
                                ('persistence/run_acceptance.py','persistence/output/研究資料_v0_9.sqlite3','persistence/output/獨立保存與跨程序讀回驗收.json')]:
            paths=[ROOT/db,ROOT/proof];before=[p.read_bytes() for p in paths]
            r=subprocess.run([sys.executable,str(ROOT/runner)],capture_output=True,text=True,timeout=15)
            self.assertEqual(r.returncode,2,r.stdout+r.stderr);self.assertEqual(json.loads(r.stdout)['status'],'HISTORICAL_RUNNER_VERSION_MISMATCH')
            self.assertEqual(before,[p.read_bytes() for p in paths])


if __name__=='__main__':unittest.main()
