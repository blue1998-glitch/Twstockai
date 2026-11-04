"""Only new full-cash scope, shared-account comparison, accounting and packaging."""
import unittest,json,re,zipfile
from copy import deepcopy
from unittest.mock import patch
from decimal import localcontext,Inexact,ROUND_DOWN
from fractions import Fraction
from rotation_research.store import Journal
from . import basket
from .audit import audit,cash_state
from .compare import compare
from .build import CAP,OLD,DELIVERY,read,write,preservation
from .package import HTML_NAME,ZIP_NAME,render
from ..core import fingerprint

class CashTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        j=Journal(CAP/'artifacts/journal');cls.cases={n:j.read('new-'+n)['value'] for n in ('hold','reduce','partial','cash')}
        cls.result=read(CAP/'artifacts/comparison.json');cls.receipt=cls.cases['cash']['receipt']
    def test_01_four_same_account_information_and_timeline(self):
        self.assertEqual(compare(self.cases),self.result)
        r=self.result;self.assertEqual(r['status'],'COMPARABLE_SYNTHETIC_ACCOUNTS')
        for b in r['branches'].values():
            self.assertEqual(b['metrics']['initial_capital'],'1240')
            self.assertEqual([x['date'] for x in b['ledger']['daily']],[x['date'] for x in r['branches']['hold']['ledger']['daily']])
            self.assertEqual(b['ledger']['daily'][:2],r['branches']['hold']['ledger']['daily'][:2])
    def test_02_independent_whole_account_oracles(self):
        oracle=read(CAP/'declaration-v03.json')['oracle']
        for n,b in self.result['branches'].items():
            m=b['metrics'];self.assertEqual(m['terminal_accrual_equity'],oracle['equity_end'][n]);self.assertEqual(m['costs']['recorded_fill_fee_tax'],oracle['fees'][n])
            self.assertEqual(b['ledger']['daily'][-1]['settled_cash'],oracle['cash_end'][n])
            expected=Fraction(oracle['equity_end'][n])/1240-1
            self.assertLess(abs(Fraction(m['statistics']['period_accrual_growth'])-expected),Fraction(1,10**45))
            self.assertEqual(m['statistics']['maximum_drawdown'],m['statistics']['period_accrual_growth'])
    def test_03_full_cash_zero_holdings_rights_and_payables(self):
        b=self.result['branches']['cash'];a=b['liquidation'];row=b['ledger']['daily'][-1]
        self.assertEqual(a['status'],'VERIFIED_ALL_CASH_SYNTHETIC');self.assertEqual(a['reasons'],[])
        self.assertTrue(all(x=='0' for x in row['shares'].values()));self.assertEqual(row['cash_claims'],[]);self.assertEqual(row['share_receivables'],[])
        self.assertEqual(row['cash_receivable'],'0');self.assertEqual(row['purchase_payable'],'0')
        self.assertEqual(row['settled_cash'],row['net_accrual_equity']);self.assertEqual(row['settled_cash'],'1235.760')
        self.assertEqual(b['metrics']['terminal_net_equity'],b['metrics']['terminal_accrual_equity'])
        self.assertEqual(b['metrics']['costs']['terminal_estimated_exit_cost'],'0')
    def test_04_both_assets_actual_fills_and_settlement_records(self):
        e=self.receipt['execution'];self.assertEqual({f['code']:f['shares'] for f in e['fills']},{'B':'7','C':'4'})
        for f in e['fills']:
            js=[x for x in e['ledger']['journal'] if x['type']=='CASH_RECEIVED' and x.get('claim_id')==f['id']]
            self.assertEqual(len(js),1);self.assertEqual(js[0]['date'],'2026-01-09')
        self.assertEqual(self.result['branches']['partial']['ledger']['daily'][-1]['shares']['C'],'4')
        self.assertEqual(self.result['branches']['partial']['liquidation']['status'],'NOT_FULLY_CASH')
    def test_05_no_advance_cash_before_explicit_settlement(self):
        rows={r['date']:r for r in self.receipt['execution']['ledger']['daily']}
        for day in ('2026-01-07','2026-01-08'):
            self.assertEqual(rows[day]['settled_cash'],'1000');self.assertEqual(rows[day]['cash_receivable'],'235.760')
            self.assertEqual(cash_state(rows[day]),'AWAITING_SETTLEMENT_OR_RIGHTS')
        self.assertEqual(cash_state(rows['2026-01-09']),'ALL_CASH_AT_SAVED_CLOSE')
    def test_06_original_C_pending_rights_still_refused(self):
        x=read(CAP/'original-account-refusal.json');self.assertEqual(x['original_C_rights'][0]['tradable_date'],'2026-01-12')
        self.assertIn('SELL_QUANTITY_EXCEEDS_AVAILABLE_SHARES',str(x['C4_probe_result']))
        self.assertIn('PENDING_OR_UNKNOWN_SHARE_RIGHTS_PREVENT_FULL_EXIT',str(x['basket_probe_result']))
        self.assertIsNone(x['full_cash_metrics']);self.assertEqual(x['original_execution_calls'],0)
    def test_07_missing_extra_or_buy_order_rejected(self):
        r=self.receipt
        for variant in ('omit_C','extra_B','BUY'):
            spec=deepcopy(r['execution_spec'])
            if variant=='omit_C':spec['orders']=spec['orders'][:1]
            if variant=='extra_B':spec['orders'][0]['shares']='8'
            if variant=='BUY':spec['orders'][1]['side']='BUY'
            with self.assertRaises(ValueError):basket.job_for(r['request'],r['checked'],spec)
    def test_08_wrong_stock_source_or_basis_rejected(self):
        for key in ('code','basis_id','source_id'):
            r=deepcopy(self.receipt)
            if key=='code':r['request']['sales']={'B':'7','D':'4'}
            else:r['request']['seed_action_input']['decision_template']['assets']['C'][key]='WRONG'
            r['receipt_id']=fingerprint({k:v for k,v in r.items() if k!='receipt_id'})
            m=basket.metrics(r,self.cases['cash']['evaluation_at']);self.assertEqual(m['status'],'REFUSED');self.assertIsNone(m['statistics'])
    def test_09_changed_cost_input_cannot_reuse_checked_result(self):
        r=deepcopy(self.receipt);r['request']['seed_action_input']['decision_template']['cost_model']['minimum_fee']='2'
        with patch.object(basket,'simulate',side_effect=AssertionError('must not execute')):
            result=basket.execute(r['request'],r['checked'],r['execution_spec'])
        self.assertEqual(result['status'],'REFUSED');self.assertEqual(result['execution_calls'],0)
    def test_10_close_not_yet_available_refuses_metrics(self):
        m=basket.metrics(self.receipt,'2026-01-08T16:00:00+08:00');self.assertEqual(m['status'],'REFUSED');self.assertIsNone(m['statistics'])
    def test_11_rehashed_watermark_change_still_rejected(self):
        r=deepcopy(self.receipt);r['execution_spec']['observed_until']='2026-01-08T16:00:00+08:00';r['execution_job']['observed_until']='2026-01-08T16:00:00+08:00'
        r['receipt_id']=fingerprint({k:v for k,v in r.items() if k!='receipt_id'})
        m=basket.metrics(r,self.cases['cash']['evaluation_at']);self.assertEqual(m['status'],'REFUSED');self.assertIn('EXECUTION_SPEC_CONFLICT',str(m['reasons']))
    def test_12_missing_rows_marks_or_unknown_rights_refuse(self):
        for key in ('row','mark','rights'):
            r=deepcopy(self.receipt);ledger=r['execution']['ledger']
            if key=='row':ledger['daily'].pop(2)
            elif key=='mark':ledger['daily'][0]['marks']['B']=None
            else:ledger['daily'][-1]['cash_claims']=None
            r['receipt_id']=fingerprint({k:v for k,v in r.items() if k!='receipt_id'})
            m=basket.metrics(r,self.cases['cash']['evaluation_at']);self.assertEqual(m['status'],'REFUSED');self.assertIsNone(m['statistics'])
    def test_13_missing_settlement_open_orders_or_coverage_not_cash(self):
        for key in ('journal','order','coverage'):
            e=deepcopy(self.receipt['execution'])
            if key=='journal':e['ledger']['journal']=[x for x in e['ledger']['journal'] if x['type']!='CASH_RECEIVED']
            if key=='order':next(iter(e['order_states'].values()))['status']='OPEN'
            if key=='coverage':e['ledger']['source_qualification']['calendar']='UNKNOWN'
            self.assertEqual(audit(e)['status'],'NOT_FULLY_CASH')
    def test_14_cannot_mix_original_and_new_account(self):
        cases=deepcopy(self.cases);cases['reduce']=Journal(OLD/'artifacts/journal').read('cap1-reduce')['value']
        r=compare(cases);self.assertEqual(r['status'],'REFUSED');self.assertEqual(r['branches'],{})
    def test_15_unknown_values_never_filled_with_zero(self):
        base=self.receipt['execution']['ledger']['daily'][-1]
        for key in ('shares','settled_cash','cash_receivable','purchase_payable','cash_claims','share_receivables','net_accrual_equity'):
            row=deepcopy(base);row[key]=None;self.assertEqual(cash_state(row),'INSUFFICIENT_EVIDENCE')
        for key,value in [('cash_claims',{}),('share_receivables',{})]:
            row=deepcopy(base);row[key]=value;self.assertEqual(cash_state(row),'INSUFFICIENT_EVIDENCE')
    def test_16_hostile_decimal_context_and_no_input_mutation(self):
        before=deepcopy(self.cases)
        with localcontext() as c:
            c.prec=3;c.rounding=ROUND_DOWN;c.traps[Inexact]=True
            self.assertEqual(compare(self.cases),self.result)
        self.assertEqual(self.cases,before)
    def test_17_read_only_comparison_never_replays_engines(self):
        fail=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('READ must not execute'))
        with patch.object(basket,'single_evaluate',fail),patch.object(basket,'resume_decision',fail),patch.object(basket,'simulate',fail):
            self.assertEqual(compare(self.cases),self.result)
    def counter(self,name,change):
        j=Journal(CAP/'artifacts/counters');r=self.receipt;spec=deepcopy(r['execution_spec']);change(spec)
        q=dict(request=r['request'],checked=r['checked'],spec=spec)
        write(CAP/'counter-inputs'/(name+'.json'),q)
        if j.path(name).exists():return j.read(name)['value']
        result=basket.execute(q['request'],q['checked'],q['spec']);j.save(name,result);return result
    def test_18_partial_fill_is_not_full_liquidation(self):
        def change(s):s['tape'][0]['capacity_shares']='3'
        result=self.counter('partial-fill',change);self.assertEqual(result['status'],'REPLAYED_EXPLICIT_FULL_EXIT')
        self.assertEqual(result['execution']['ledger']['daily'][-1]['shares']['B'],'4')
        self.assertEqual(audit(result['execution'])['status'],'NOT_FULLY_CASH')
    def test_19_zero_holdings_unsettled_proceeds_are_not_cash(self):
        def change(s):s['observed_until']='2026-01-08T16:00:00+08:00'
        result=self.counter('before-settlement',change);self.assertEqual(result['status'],'REPLAYED_EXPLICIT_FULL_EXIT')
        row=result['execution']['ledger']['daily'][-1];self.assertTrue(all(x=='0' for x in row['shares'].values()))
        self.assertEqual(row['cash_receivable'],'235.760');self.assertEqual(audit(result['execution'])['status'],'NOT_FULLY_CASH')
    def test_20_html_payload_and_zip_keep_exact_original_values(self):
        body=(DELIVERY/HTML_NAME).read_bytes();h=body.decode();d=json.loads(re.search(r'<script id="cap1-data" type="application/json">(.*?)</script>',h,re.S).group(1))
        self.assertEqual(d['branches'],self.result['branches']);self.assertTrue(d['source_manifest']['new_account_not_old_rights_release'])
        with zipfile.ZipFile(DELIVERY/ZIP_NAME) as z:self.assertIsNone(z.testzip());self.assertEqual(z.read(HTML_NAME),body)
        self.assertIn("connect-src 'none'",h);self.assertNotIn('<script src=',h)
        declared=read(CAP/'declaration-v03.json');self.assertEqual(render(self.result,declared).encode(),body)
        wrong=deepcopy(declared);wrong['seed_execution_spec']['origin_ledger']['opening']['cash']='1001'
        with self.assertRaises(ValueError):render(self.result,wrong)
    def test_21_general_reserve_and_formal_restrictions_preserved(self):
        for b in self.result['branches'].values():
            self.assertEqual(b['metrics']['account']['general_reserved_cash'],'100');self.assertEqual(b['metrics']['account']['external_flow'],'0')
            self.assertFalse(b['metrics']['historical_signal_eligible']);self.assertFalse(b['metrics']['policy_authorized'])
        self.assertIsNone(self.result['ranking']);self.assertIsNone(self.result['primary_pressure_id'])
        self.assertTrue(self.result['branches']['cash']['liquidation']['general_reserve_unchanged'])
    def test_22_original_three_actions_and_engines_unchanged(self):
        self.assertEqual(preservation(),read(CAP/'preserved-source-manifest.json'))

if __name__=='__main__':unittest.main()
