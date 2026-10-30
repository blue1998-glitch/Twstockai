"""Eight finite methods; no market accounting, old suite or strategy test."""
from copy import deepcopy
import hashlib
import json
import subprocess
import sys
import unittest
from graph_core.core import fingerprint
from rotation_research.market_case import source_binding,CaseError
from rotation_research.market_case_io import load_saved
from rotation_research.market_case_v2 import prepare_context_prefix
from .freeze import ROOT,PROJECT,REPO,load,save,info
from .build import check_frozen


class IIContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request=load(ROOT/'input.json');cls.saved=load_saved(REPO,load(ROOT/'source-spec.json'));cls.work=load(ROOT/'work-summary.json')
        cls.actual=load(ROOT/'final/actual/draft-II.json')['actual'];cls.expected=load(ROOT/'expected.json')

    def test_01_frozen_II_case_and_complete_diagnostics(self):
        check_frozen();rows=load(ROOT/'final/summary.json');self.assertEqual(len(rows),13);self.assertTrue(all(x['matched'] for x in rows))
        for row in rows:
            r=load(ROOT/'final/actual'/str(row['name']+'.json'))
            self.assertTrue(r['input_unchanged']);self.assertTrue(r['sources_unchanged']);self.assertTrue(r['summary_unchanged'])
            for k in ('qualify','ledger_replay','capital_simulate','quantity_replay','legacy_prepare'):self.assertEqual(r['calls'][k],0)
        self.assertEqual(self.actual['status'],self.expected['status']);self.assertEqual(self.actual['track_id'],'II')
        self.assertEqual(self.actual['main_opportunity_on'],'2026-04-09')
        # Initial rejection and pre-fix source are kept; oracle unchanged.
        before=load(ROOT/'actual/unsupported-6488.json');self.assertEqual(before['error'],'MAIN_TRACK_OPPORTUNITY_BINDING_REQUIRED');self.assertIsNone(before['actual'])
        source=next(x for x in load(ROOT/'source-versions-before-run.json')['files'] if x['path'].endswith('/market_case_v2.py'))
        raw=(ROOT/'diagnostics/market_case_v2-initial.py').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),source['sha256'])

    def test_02_case_timeline_references_and_no_automatic_action(self):
        for p in self.actual['prefixes']:
            self.assertEqual([f['id'] for f in p['facts']],self.expected['prefix_fact_ids'][p['as_of_case_date']])
            self.assertFalse(p['automatic_add']);self.assertFalse(p['automatic_exit']);self.assertFalse(p['automatic_order'])
            self.assertEqual(p['usable_historical_signal_ids'],[])
            if p['as_of_case_date']<'2026-04-22':
                text=json.dumps(p,ensure_ascii=False);self.assertNotIn('2026-04-22',text)
                self.assertNotIn('RECOVERY_NOT_RECLAIMED_AND_LOWER_THAN_IV',text)
        p=next(p for p in self.actual['prefixes'] if p['as_of_case_date']=='2026-04-15')
        refs={r['id']:r for r in p['references']}
        self.assertEqual((refs['A-important']['value'],refs['B-local']['value'],refs['B-original']['value']),('24.80','32.85','35.50'))
        self.assertIsNone(refs['B-local']['source_binding']);self.assertIsNone(refs['B-local']['raw_bar'])
        self.assertFalse(refs['A-important']['automatic_exit']);self.assertFalse(refs['B-local']['formal_primary_pressure'])

    def test_03_regular_and_odd_are_distinct_unexecuted_materials(self):
        early=self.actual['prefixes'][0];self.assertEqual(early['visible_entry_materials'],[]);self.assertIsNone(early['selected_entry_material'])
        for name,chosen,price in [('selected-regular','II-regular-open','25.35'),('selected-odd','II-odd-first','25.60')]:
            result=load(ROOT/'final/actual'/str(name+'.json'))['actual']
            self.assertIsNone(result['prefixes'][0]['selected_entry_material'])
            selected=result['prefixes'][1]['selected_entry_material'];self.assertEqual(selected['id'],chosen);self.assertEqual(selected['price'],price)
            self.assertFalse(selected['actual_fill']);self.assertFalse(selected['model_authorized']);self.assertIsNone(selected['capacity'])
        p=self.actual['prefixes'][1];materials={m['channel']:m for m in p['visible_entry_materials']}
        self.assertIsNotNone(materials['REGULAR_OPEN']['source_binding']);self.assertIsNone(materials['ODD_LOT_FIRST_PRINT']['source_binding'])
        self.assertNotIn('25.50',json.dumps(p,ensure_ascii=False))

    def test_04_counterexamples_are_refusals_not_orders(self):
        cases=load(ROOT/'cases.json')
        for case in cases:
            if 'error' not in case['expected']:continue
            r=load(ROOT/'final/actual'/str(case['name']+'.json'))
            self.assertEqual(r['error'],case['expected']['error']);self.assertIsNone(r['actual'])
            self.assertEqual(r['calls']['ledger_replay'],0)
        request=deepcopy(self.request);request['facts'][3]['reference_ids']=['V']
        with self.assertRaisesRegex(CaseError,'FUTURE_CASE_REFERENCE'):
            prepare_context_prefix(request,self.saved,self.work,as_of='2026-04-17')
        save(ROOT/'test-evidence/future-reference.json',dict(spec=load(ROOT/'test-spec.json')['future_reference'],input=request,error='FUTURE_CASE_REFERENCE'))

    def test_05_future_tail_and_unbounded_prose_never_enter_old_prefix(self):
        spec=load(ROOT/'prefix-spec.json');rows=[]
        for day in spec['prefixes_to_compare']:
            baseline=prepare_context_prefix(self.request,self.saved,self.work,as_of=day)
            for control in spec['future_controls']:
                saved=deepcopy(self.saved);request=deepcopy(self.request)
                next(r for r in saved['quotes']['assets']['2884']['bars'] if r['date']==spec['future_price_date'])['close']=control['B_future']
                next(f for f in request['facts'] if f['id']=='V')['statement']=control['V_statement']
                request['source_binding']=source_binding(saved);before=fingerprint(saved)
                actual=prepare_context_prefix(request,saved,self.work,as_of=day)
                self.assertEqual(actual['prefix'],baseline['prefix']);self.assertNotEqual(actual['source_integrity_metadata'],baseline['source_integrity_metadata'])
                self.assertEqual(before,fingerprint(saved));rows.append(dict(as_of=day,control=control,actual=actual,same_prefix=True))
        request=deepcopy(self.request);request['entry_materials'][0]['price']='NOT_A_PRICE'
        before=prepare_context_prefix(self.request,self.saved,self.work,as_of='2026-04-09')
        actual=prepare_context_prefix(request,self.saved,self.work,as_of='2026-04-09')
        self.assertEqual(actual['prefix'],before['prefix'])
        save(ROOT/'test-evidence/future-prefixes.json',dict(spec=spec,controls=rows,bad_future_material_spec=load(ROOT/'test-spec.json')['future_bad_material'],bad_future_material_actual=actual))

    def test_06_unknown_parameters_and_source_restrictions_preserved(self):
        self.assertTrue(all(v is None for v in self.actual['research_parameters'].values()))
        self.assertIn('N',self.actual['missing_research_parameters']);self.assertIsNone(self.actual['selected_entry_material_id'])
        self.assertTrue(all(v=='UNAPPROVED' for v in self.actual['research_controls'].values()))
        self.assertFalse(self.actual['work_originals_read_by_codex']);self.assertEqual(len(self.actual['source_parent_chain']),8)
        self.assertEqual(self.actual['source_coverage'],self.saved['catalog']['coverage'])
        self.assertTrue(all(c['status']=='INCOMPLETE' for c in self.actual['source_coverage'].values()))
        for k in ['data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized','strategy_validated']:self.assertFalse(self.actual[k])
        for k in ['primary_pressure_id','total_net_return','scenario_net_return','actual_realized_investor_return','ranking','fills']:self.assertIsNone(self.actual[k])
        self.assertEqual(self.actual['numeric_replay'],'NOT_PERFORMED');self.assertEqual(self.actual['account_reconstruction'],'NOT_PERFORMED')
        check_frozen()

    def test_07_fresh_pure_context_and_caller_preserved(self):
        done=subprocess.run([sys.executable,'-B','-m','rotation_research.market_case_v2_20261028.guard'],cwd=PROJECT,
            text=True,capture_output=True,check=True)
        self.assertEqual(done.stderr,'');r=json.loads(done.stdout);save(ROOT/'test-evidence/fresh-pure.json',r)
        self.assertEqual(r['status'],self.expected['status']);self.assertEqual(r['calls'],dict(context=1,qualify=0,replay=0))
        self.assertEqual(r['forbidden_effects'],[]);self.assertTrue(r['caller_unchanged']);self.assertTrue(r['default_unchanged'])

    def test_08_new_save_readback_and_old_version_unchanged(self):
        record=load(ROOT/'final/saved/II-context-draft.json')
        self.assertEqual(record['value']['request'],self.request);self.assertEqual(record['value']['work_summary'],self.work)
        self.assertEqual(record['value']['result'],self.actual)
        self.assertEqual(load(ROOT/'saved/II-context-draft.json')['value'],record['value'])
        bad=deepcopy(load(ROOT/'source-spec.json'));bad['files']['quotes']['sha256']='0'*64
        with self.assertRaisesRegex(CaseError,'SAVED_SOURCE_BYTES_MISMATCH'):load_saved(REPO,bad)
        check_frozen();save(ROOT/'test-evidence/preservation.json',dict(old_files_unchanged=len(load(ROOT/'intake.json')['original_files']),
            new_record_request_and_result_match=True,old_record_not_migrated=True,source_sha_mismatch='REJECTED'))


if __name__=='__main__':unittest.main()
