"""Targeted CAP1 tests. No writes to historical fixtures; no market IO."""
import unittest, json, hashlib, zipfile, re
from copy import deepcopy
from decimal import localcontext, Inexact, ROUND_DOWN
from fractions import Fraction
from .compare import compare, basis
from .build import CAP, OLD, ROOT, DELIVERY, read, source_manifest
from .package import HTML_NAME, ZIP_NAME
from ..action_account_metrics import evaluate_saved
from ..cash_action_execution import execute
from rotation_research.store import Journal

class Cap1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        j=Journal(CAP/'artifacts/journal')
        cls.cases={n:j.read('cap1-'+n)['value'] for n in ('hold','reduce','exit_b')}
        cls.out=read(CAP/'artifacts/comparison.json')
    def refused(self,case):
        out=evaluate_saved(case);self.assertEqual(out['status'],'REFUSED');self.assertIsNone(out['statistics']);return out
    def fixture(self,n):return read(OLD/'cases'/n/'input.json')
    def test_01_complete_same_account_information_period(self):
        self.assertEqual(compare(self.cases),self.out)
        self.assertEqual(basis(self.cases['hold']),basis(self.cases['reduce']))
        self.assertEqual(basis(self.cases['reduce']),basis(self.cases['exit_b']))
        self.assertEqual(self.out['status'],'COMPARABLE_SYNTHETIC_ACCOUNTS')
    def test_02_whole_account_financial_oracles(self):
        expected={'hold':('1178.860','938.860','1','7'),
                  'reduce':('1176.800','996.800','3','4'),
                  'exit_b':('1176.720','1076.720','3','0')}
        for n,(equity,cash,fees,bshares) in expected.items():
            b=self.out['branches'][n];m=b['metrics'];s=m['statistics'];r=b['ledger']['daily'][-1]
            self.assertEqual(m['initial_capital'],'1180');self.assertEqual(m['terminal_accrual_equity'],equity)
            self.assertEqual(r['settled_cash'],cash);self.assertEqual(m['costs']['recorded_fill_fee_tax'],fees)
            self.assertEqual(r['shares']['B'],bshares);self.assertEqual(r['shares']['C'],'4')
            expected_growth=Fraction(equity)/1180-1
            self.assertLess(abs(Fraction(s['period_accrual_growth'])-expected_growth),Fraction(1,10**45))
            self.assertEqual(s['maximum_drawdown'],s['period_accrual_growth'])
            self.assertTrue(s['recovery_censored']);self.assertEqual(s['ongoing_underwater_calendar_days'],7)
    def test_03_saved_financial_outputs_and_original_inputs_preserved(self):
        for n,old in [('hold','v01-hold'),('reduce','reduce-B3'),('exit_b','exit-B7')]:
            m=self.out['branches'][n]['metrics'];o=read(OLD/'final-corrected'/old/'actual.json')
            for k in ('statistics','costs','initial_capital','terminal_accrual_equity'):self.assertEqual(m[k],o[k])
        self.assertEqual(read(CAP/'source-manifest.json'),source_manifest())
    def test_04_original_hold_information_mismatch_is_refused(self):
        cases=deepcopy(self.cases);cases['hold']=self.fixture('v01-hold')
        out=compare(cases);self.assertEqual(out['status'],'REFUSED');self.assertEqual(out['branches'],{})
        self.assertIn('SAME_ACCOUNT',out['reasons'][0])
    def test_05_mixed_evaluation_time_is_refused(self):
        cases=deepcopy(self.cases);cases['hold']['evaluation_at']='2026-01-13T16:00:00+08:00'
        self.assertEqual(compare(cases)['status'],'REFUSED')
    def test_06_modified_opening_and_model_are_refused(self):
        for key in ('opening','model'):
            cases=deepcopy(self.cases);r=cases['hold']['saved_result']['action_request']
            if key=='opening':r['execution_spec']['origin_ledger']['opening']['cash']='1001'
            else:r['action_input']['decision_template']['cost_model']['commission_rate']='0'
            self.assertEqual(compare(cases)['status'],'REFUSED')
    def test_07_unknown_rights_refused_not_zero(self):
        out=self.refused(self.fixture('unknown-rights'));self.assertIn('UNKNOWN_CASH_CLAIMS',str(out['reasons']))
    def test_08_missing_calendar_day_refused(self):
        out=self.refused(self.fixture('missing-day'));self.assertIn('INCOMPLETE_CALENDAR_CURVE',str(out['reasons']))
    def test_09_missing_mark_refused(self):
        out=self.refused(self.fixture('missing-mark'));self.assertIn('UNKNOWN_HELD_ASSET_MARK',str(out['reasons']))
    def test_10_future_quote_and_premature_close_refused(self):
        for name in ('future-mark','early'):self.refused(self.fixture(name))
    def test_11_incomplete_prefix_and_market_relabel_refused(self):
        for name in ('partial-prefix','real-relabel'):self.refused(self.fixture(name))
    def test_12_no_early_spending_of_receivables(self):
        for n in self.cases:
            b=self.out['branches'][n];days={r['date']:r for r in b['ledger']['daily']}
            self.assertEqual(days['2026-01-09']['settled_cash'],'858.860')
            self.assertEqual(days['2026-01-09']['shares']['C'],'2')
            self.assertTrue(days['2026-01-09']['share_receivables'])
            self.assertFalse(days['2026-01-12']['share_receivables'])
            self.assertEqual(b['metrics']['account']['general_reserved_cash'],'100')
            self.assertEqual(b['metrics']['account']['external_flow'],'0')
    def test_13_common_prefix_and_same_origin_rights(self):
        prefixes=[]
        for n in self.cases:
            prefixes.append(self.out['branches'][n]['ledger']['daily'][:4])
            cp=self.cases[n]['saved_result']['action_request']['action_input']['account_source']['checkpoint']
            self.assertEqual(cp['state']['origin_initial_capital'],'1180')
        self.assertEqual(prefixes[0],prefixes[1]);self.assertEqual(prefixes[0],prefixes[2])
    def test_14_false_qualification_no_ranking_no_real_return(self):
        self.assertIsNone(self.out['ranking']);self.assertIsNone(self.out['primary_pressure_id'])
        for b in self.out['branches'].values():
            m=b['metrics'];self.assertFalse(m['policy_authorized']);self.assertFalse(m['historical_signal_eligible'])
            self.assertIsNone(b['ledger']['total_net_return']);self.assertIsNone(b['ledger']['actual_realized_investor_return'])
    def test_15_hostile_decimal_context_and_no_input_mutation(self):
        before=deepcopy(self.cases)
        with localcontext() as ctx:
            ctx.prec=3;ctx.rounding=ROUND_DOWN;ctx.traps[Inexact]=True
            result=compare(self.cases)
        self.assertEqual(result,self.out);self.assertEqual(self.cases,before)
    def test_16_tampered_execution_receipt_refused(self):
        r=deepcopy(self.cases['reduce']['saved_result']['action_request'])
        r['action_input']['action']['sell_shares']='4'
        out=execute(r)['run'];self.assertNotEqual(out['status'],'REPLAYED_EXPLICIT_ACTION');self.assertEqual(out['execution_calls'],0)
    def test_17_single_file_payload_matches_original_exact_values(self):
        html=(DELIVERY/HTML_NAME).read_text()
        payload=json.loads(re.search(r'<script id="cap1-data" type="application/json">(.*?)</script>',html,re.S).group(1))
        self.assertEqual(payload['branches'],self.out['branches'])
        self.assertIsNone(payload['unavailable']['metrics']);self.assertEqual(payload['unavailable']['kind'],'EXIT_ALL_TO_CASH')
        self.assertIn("connect-src 'none'",html);self.assertNotIn('<script src=',html)
        self.assertNotIn('https://',html)
    def test_18_download_lossless_and_only_synthetic(self):
        with zipfile.ZipFile(DELIVERY/ZIP_NAME) as z:
            self.assertIsNone(z.testzip());self.assertEqual(len(z.namelist()),2)
            self.assertEqual(z.read(HTML_NAME),(DELIVERY/HTML_NAME).read_bytes())
    def test_19_unsupported_and_duplicate_actions_refused(self):
        self.assertEqual(compare({})['status'],'REFUSED')
        self.assertEqual(compare(dict(a=self.cases['hold'],b=self.cases['hold']))['status'],'REFUSED')
    def test_20_original_journal_readback_and_costs_not_double_deducted(self):
        for name in self.cases:
            self.assertEqual(Journal(CAP/'artifacts/journal').read('cap1-'+name)['value'],self.cases[name])
            b=self.out['branches'][name];m=b['metrics']
            self.assertEqual(m['terminal_accrual_equity'],b['ledger']['daily'][-1]['net_accrual_equity'])
            self.assertNotEqual(m['terminal_accrual_equity'],m['terminal_net_equity'])

if __name__=='__main__':unittest.main()
