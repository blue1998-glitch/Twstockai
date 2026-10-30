"""Eight unique methods for preparation; no numeric market-performance tests."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from graph_core.core import fingerprint
from rotation_research.market_case import prepare_case,prepare_decision_prefix,source_binding,CaseError
from rotation_research.market_case_io import load_saved
from .freeze import ROOT,REPO,PROJECT,load,save,info
from .build import check_frozen,inspect


class MarketCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved=load_saved(REPO,load(ROOT/'source-spec.json'));cls.draft=load(ROOT/'input.json')
        cls.explicit=load(ROOT/'controls/source-bound-input.json');cls.spec=load(ROOT/'additional-spec.json')

    def test_01_frozen_case_observations_and_real_draft(self):
        check_frozen();r=load(ROOT/'after-final/actual/draft/actual.json');a=r['actual'];e=load(ROOT/'expected.json')
        self.assertIsNone(r['error']);self.assertEqual(a['status'],e['draft_status']);self.assertIsNone(a['compiled_accounts'])
        self.assertIn('common.period',a['missing_inputs']);self.assertIn('common.account.cash',a['missing_inputs'])
        self.assertIn('common_entry',a['missing_inputs']);self.assertIsNone(self.draft['common']['account']['cash'])
        self.assertEqual([{k:p[k] for k in ('code','date','field','value')} for p in a['observations']],e['milestones'])
        self.assertEqual(a['b_first_strict_breakout'],dict(status='MATCHED_SAVED_COMPLETE_PREFIX',date='2026-06-22'))
        self.assertTrue(r['input_unchanged']);self.assertTrue(r['sources_unchanged']);self.assertEqual(r['calls']['source_qualify'],0)
        for p in a['observations']:self.assertIsNone(p['available_at'])

    def test_02_complete_common_conditions_and_future_reference_refuse(self):
        for name in load(ROOT/'cases/index.json')['rejected_cases']:
            with self.subTest(case=name):
                r=load(ROOT/'after-final/actual'/name/'actual.json');expected=load(ROOT/'cases'/name/'expected.json')
                self.assertIsNone(r['actual']);self.assertEqual(r['error'],expected['error'])
                self.assertEqual(r['calls']['source_qualify'],0);self.assertEqual(r['calls']['ledger_replay'],0)
                self.assertTrue(r['input_unchanged']);self.assertTrue(r['sources_unchanged'])

    def test_03_one_original_account_full_paths_and_existing_source_gate(self):
        r=load(ROOT/'after-final/actual/explicit-control/actual.json');a=r['actual'];expected=load(ROOT/'expected.json')
        self.assertIsNone(r['error']);self.assertEqual(a['status'],expected['explicit_status'])
        self.assertEqual(a['comparison_status'],'COMMON_CONDITIONS_BOUND_NOT_PERFORMANCE_COMPARISON')
        self.assertEqual(r['calls']['source_qualify'],3)
        for key in ['ledger_replay','capital_simulate','quantity_replay','legacy_compare','old_source_producer']:self.assertEqual(r['calls'][key],0)
        for p in self.explicit['paths']:
            prepared=a['compiled_accounts'][p['id']]
            self.assertEqual(prepared['opening'],dict(cash='10000',shares={'1101':'0','2884':'0'},cash_claims=[],share_claims=[]))
            self.assertEqual(prepared['fills'],p['fills']);self.assertEqual(prepared['fills'][0],self.explicit['common_entry'])
            self.assertEqual((prepared['start'],prepared['end']),('2026-04-07','2026-06-23'))
            self.assertNotEqual(prepared['qualification']['opening_claims'],'VERIFIED')
            refusal=a['source_admissions'][p['id']]
            self.assertTrue(set(expected['old_qualification_reasons_include'])<=set(refusal['refusal_reasons']))
            self.assertEqual(refusal['daily'],[]);self.assertEqual(refusal['journal'],[])
            self.assertIsNone(refusal['total_net_return'])
            # Full inherited events remain even beyond this model-control period.
            july=[e for e in prepared['events'] if e['ex_date']=='2026-07-01']
            self.assertEqual({e['code'] for e in july},{'1101','2884'})
            self.assertTrue(all(e['net_per_share'] is None for e in july))

    def test_04_current_prefix_never_reads_future_signal(self):
        original=prepare_decision_prefix(self.draft,self.saved,'A-return');records=[]
        for spec in self.spec['future_prefix_controls']:
            changed=deepcopy(self.saved)
            for code,key in [('1101','A_future'),('2884','B_future')]:
                row=next(x for x in changed['quotes']['assets'][code]['bars'] if x['date']=='2026-06-22');row['close']=spec[key]
            request=deepcopy(self.draft);request['source_binding']=source_binding(changed)
            before=fingerprint(changed);actual=prepare_decision_prefix(request,changed,'A-return')
            self.assertEqual(actual['prefix'],original['prefix']);self.assertNotEqual(actual['source_integrity_metadata'],original['source_integrity_metadata'])
            self.assertEqual(before,fingerprint(changed));records.append(dict(control=spec,actual=actual,same_current_prefix=True))
        self.assertNotIn('B-breakout',[x['id'] for x in original['prefix']['observations']])
        self.assertTrue(original['prefix']['reassessment_required']);self.assertFalse(original['prefix']['automatic_exit_or_transfer'])
        self.assertEqual(original['prefix']['usable_historical_signal_ids'],[])
        save(ROOT/'test-evidence/future-prefix.json',dict(spec=self.spec['future_edits'],original=original,controls=records))

    def test_05_missing_choice_quote_and_unbound_source_remain_unknown(self):
        request=deepcopy(self.explicit);request['paths'][2]['b_intent']=None
        r=inspect(request,self.saved);self.assertEqual(r['actual']['status'],'AWAITING_EXPLICIT_INPUT');self.assertIsNone(r['actual']['compiled_accounts'])
        self.assertEqual(r['calls']['source_qualify'],0);save(ROOT/'test-evidence/missing-B-intent.json',dict(input=request,actual=r))
        changed=deepcopy(self.saved)
        next(x for x in changed['quotes']['assets']['2884']['bars'] if x['date']=='2026-05-06')['close']=None
        request=deepcopy(self.draft);request['source_binding']=source_binding(changed)
        r=inspect(request,changed);self.assertEqual(r['actual']['b_first_strict_breakout']['status'],'UNKNOWN_INCOMPLETE_PREFIX')
        self.assertIsNone(r['actual']['b_first_strict_breakout']['date']);save(ROOT/'test-evidence/missing-B-quote.json',dict(delta=self.spec['missing_quote'],input=request,actual=r))
        r=inspect(load(ROOT/'controls/explicit-input.json'),self.saved)
        self.assertEqual(r['error'],'FILL_QUOTE_SOURCE_OUT_OF_PERIOD');self.assertEqual(r['calls']['source_qualify'],0)
        save(ROOT/'test-evidence/original-wrong-source.json',r)

    def test_06_explicit_IO_and_saved_draft_readback(self):
        original=(ROOT/'saved/market-case-draft.json').read_bytes()
        receipt=load(ROOT/'after-final/saved/market-case-draft.json')
        self.assertEqual(receipt['value']['request'],self.draft);self.assertEqual(receipt['value']['source_spec'],load(ROOT/'source-spec.json'))
        self.assertEqual(receipt['value']['result'],load(ROOT/'after-final/actual/draft/actual.json')['actual'])
        bad=deepcopy(load(ROOT/'source-spec.json'));bad['files']['quotes']['sha256']='0'*64
        with self.assertRaisesRegex(CaseError,'SAVED_SOURCE_BYTES_MISMATCH'):load_saved(REPO,bad)
        bad['files']['quotes']['path']='../source-not-in-repository'
        with self.assertRaisesRegex(CaseError,'SOURCE_PATH_OUTSIDE_REPOSITORY'):load_saved(REPO,bad)
        self.assertEqual((ROOT/'saved/market-case-draft.json').read_bytes(),original)
        save(ROOT/'test-evidence/IO.json',dict(original_draft_bytes_preserved=True,readback_equal=True,
            source_sha_mismatch='REJECTED',path_escape='REJECTED',numeric_replay_calls=0))

    def test_07_fresh_pure_API_and_context(self):
        done=subprocess.run([sys.executable,'-B','-m','rotation_research.market_case_20261027.guard'],cwd=PROJECT,
            capture_output=True,text=True,check=True)
        self.assertEqual(done.stderr,'');r=json.loads(done.stdout);save(ROOT/'test-evidence/fresh-pure-context.json',r)
        self.assertEqual(r['status'],'REFUSED_SOURCE_QUALIFICATION');self.assertEqual(r['source_qualification_calls'],3)
        self.assertEqual(r['forbidden_effects'],[]);self.assertTrue(r['caller_unchanged']);self.assertTrue(r['default_unchanged'])
        self.assertEqual(r['numeric_replay'],'NOT_PERFORMED')

    def test_08_explicit_costs_and_qualifications_are_separate(self):
        request=load(ROOT/'controls/explicit-cost-override-input.json');r=inspect(request,self.saved)
        save(ROOT/'test-evidence/explicit-cost-override.json',dict(input=request,expected=load(ROOT/'controls/explicit-cost-override-expected.json'),actual=r))
        a=r['actual'];self.assertEqual(a['status'],'REFUSED_SOURCE_QUALIFICATION')
        for account in a['compiled_accounts'].values():self.assertEqual(account['terminal_costs']['minimum_fee'],'21')
        for key in ['data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized']:self.assertFalse(a[key])
        for key in ['total_net_return','scenario_net_return','actual_realized_investor_return','primary_pressure_id','ranking']:self.assertIsNone(a[key])
        self.assertEqual(a['numeric_replay'],'NOT_PERFORMED');self.assertEqual(a['order_generation'],'NOT_PERFORMED')
        self.assertTrue(r['input_unchanged']);self.assertTrue(r['sources_unchanged']);check_frozen()


if __name__=='__main__':unittest.main()
