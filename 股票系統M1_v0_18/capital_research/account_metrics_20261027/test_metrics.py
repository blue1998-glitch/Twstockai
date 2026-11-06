"""Finite arithmetic, original account, refusal and side-effect boundary tests."""
from copy import deepcopy
from decimal import Decimal,localcontext
import json
import subprocess
import sys
import unittest
from unittest.mock import patch
from capital_research.account_metrics import evaluate_saved,_curve_statistics,MetricsError
from capital_research.lifecycle import FLAGS
from .prepare import ROOT,PROJECT,load,save,file_info
from .fixtures import resolve

FINAL=ROOT/'final'
GUARD=r'''
import sys,os,runpy,importlib.abc
allowed={'capital_research.account_metrics','capital_research.account_metrics_read','capital_research.lifecycle'}
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith(('graph_core','rotation_research')) or (fullname.startswith('capital_research.') and fullname not in allowed):raise RuntimeError('ENGINE_IMPORT_FORBIDDEN:'+fullname)
sys.meta_path.insert(0,Guard())
def audit(event,args):
 if event=='open':
  mode,flags=args[1:3]
  if (mode and any(c in mode for c in 'wax+')) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('WRITE_FORBIDDEN')
 if event in ('os.mkdir','os.remove','os.rename','subprocess.Popen','socket.connect'):raise RuntimeError('SIDE_EFFECT:'+event)
sys.addaudithook(audit);sys.argv=['account_metrics']+sys.argv[1:]
runpy.run_module('capital_research.account_metrics_read',run_name='__main__')
'''


def result(name):return load(FINAL/'saved'/name/'result.json')


class MetricsTests(unittest.TestCase):
    def assert_number(self,actual,expected):
        self.assertLessEqual(abs(Decimal(actual)-Decimal(expected)),Decimal('1e-45'))

    def test_hand_calculated_growth_drawdown_recovery_and_censoring(self):
        for folder in sorted((ROOT/'arithmetic').iterdir()):
            with self.subTest(folder.name):
                expected=load(folder/'expected.json');r=load(FINAL/'arithmetic'/folder.name/'result.json')
                self.assert_number(r['period_accrual_growth'],expected['growth'])
                self.assert_number(r['maximum_drawdown'],expected['maximum_drawdown'])
                self.assertEqual(r['maximum_drawdown_duration_calendar_days'],expected['maximum_duration_days'])
                self.assertIs(r['recovery_censored'],expected['recovery_censored'])
                episode=r['maximum_drawdown_episode']
                self.assertEqual(episode['recovery_date'] if episode else None,expected['worst_recovery_date'])
        flat=load(FINAL/'arithmetic/flat/result.json');self.assertEqual(flat['episodes'],[])
        equal=load(FINAL/'arithmetic/equal-high/result.json');self.assertEqual(equal['episodes'][0]['peak_date'],'2026-01-07')

    def test_saved_cases_match_frozen_oracles_and_preserve_false_qualifications(self):
        for folder in sorted((ROOT/'cases').iterdir()):
            with self.subTest(folder.name):
                expected=load(folder/'expected.json');r=result(folder.name)
                self.assertEqual(r['status'],expected['status'])
                if folder.name=='changed-capital':
                    self.assertEqual(r['reasons'][0]['reason'],'SAVED_RESULT_UNREADABLE')
                    self.assertIn('ORIGIN_CAPITAL_CHANGED',r['reasons'][0]['guard_reasons'])
                elif expected['reason']:self.assertEqual(r['reasons'][0]['reason'],expected['reason'])
                if r['status']=='REFUSED':
                    for k in ('statistics','account','source','costs','terminal_net_growth'):self.assertIsNone(r[k])
                for k in FLAGS:self.assertIs(r[k],False)
                for k in ('ranking','selected_strategy','primary_pressure_id'):self.assertIsNone(r[k])

    def test_recorded_costs_rights_capital_latest_and_tokens_are_used_once(self):
        r=result('complete-partial-chain');e=load(ROOT/'cases/complete-partial-chain/expected.json')
        for key in ('initial_capital','terminal_accrual_equity','terminal_net_equity'):self.assert_number(r[key],e[key])
        self.assert_number(r['statistics']['period_accrual_growth'],e['accrual_growth'])
        self.assert_number(r['statistics']['maximum_drawdown'],e['maximum_drawdown'])
        self.assert_number(r['terminal_net_growth'],e['terminal_net_growth'])
        self.assert_number(r['costs']['recorded_fill_fee_tax'],e['recorded_fill_fee_tax'])
        self.assert_number(r['costs']['terminal_estimated_exit_cost'],e['terminal_exit_cost'])
        request=resolve(load(ROOT/'cases/complete-partial-chain/input.json'))
        replay=request['saved_result']['replay'];cp=replay['historical_checkpoint']['state'];account=r['account']
        self.assertEqual(account['saved_row'],cp['row'])
        for key in ('general_reserved_cash','origin_initial_capital','external_flow','opening_unavailable_shares',
                    'latest_decision_id','latest_common_account_id','reviewed_evidence_tokens'):
            self.assertEqual(account[key],cp[key])
        self.assertEqual(r['source']['rows_used_once'],len(replay['last_execution']['ledger']['daily']))
        self.assertEqual(r['source']['snapshot_count'],2)
        self.assertGreater(sum(len(f['execution']['ledger']['daily']) for f in replay['rounds']),r['source']['rows_used_once'])
        self.assertEqual(replay['last_execution']['ledger']['daily'][0]['cash_receivable'],'80')
        self.assertTrue(replay['last_execution']['ledger']['daily'][0]['share_receivables'])

    def test_unknown_nonfinite_missing_and_duplicate_days_never_fill_forward(self):
        for case in load(ROOT/'arithmetic-invalid.json'):
            before=deepcopy(case)
            with self.subTest(case['name']),self.assertRaisesRegex(MetricsError,case['reason']):
                _curve_statistics(case['rows'])
            self.assertEqual(case,before)

    def test_equivalent_timezone_and_earlier_availability_boundaries(self):
        spec=load(ROOT/'cases/complete-partial-chain/input.json');request=resolve(spec);base=result('complete-partial-chain')
        for control in load(ROOT/'time-controls.json')['controls']:
            request['evaluation_at']=control['evaluation_at'];r=evaluate_saved(request)
            self.assertEqual(r['status'],control['expected'])
            if control['expected']=='EVALUATED':self.assertEqual(r['statistics'],base['statistics'])
            else:self.assertEqual(r['reasons'][0]['reason'],control['reason'])
            save(ROOT/'time-final'/('equivalent' if control['expected']=='EVALUATED' else 'early')/'result.json',r)

    def test_pure_evaluation_has_no_IO_and_does_not_mutate_source(self):
        request=resolve(load(ROOT/'cases/complete-partial-chain/input.json'));before=deepcopy(request)
        with patch('builtins.open',side_effect=AssertionError('PURE_IO')):
            r=evaluate_saved(request)
        self.assertEqual(r,result('complete-partial-chain'));self.assertEqual(request,before)

    def test_fresh_cli_cannot_import_engines_write_or_connect(self):
        for case,fmt in [('complete-partial-chain','json'),('complete-partial-chain','text'),('partial-ledger','json')]:
            spec=load(ROOT/'cases'/case/'input.json')
            args=['--source',str(PROJECT/spec['source']['path']),'--evaluation-at',spec['evaluation_at'],'--format',fmt]
            p=subprocess.run([sys.executable,'-B','-c',GUARD]+args,cwd=PROJECT,text=True,capture_output=True)
            self.assertEqual(p.returncode,0 if case=='complete-partial-chain' else 2);self.assertEqual(p.stderr,'')
            if fmt=='json':self.assertEqual(json.loads(p.stdout)['evaluation'],result(case))
            else:
                self.assertIn('不是每日可清倉',p.stdout);self.assertIn('截至終點未恢復',p.stdout)
            save(ROOT/'cli-final'/(case+'-'+fmt+'.json'),dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,
                guard='FRESH_NO_ENGINE_NO_REPLAY_NO_WRITE_NO_NETWORK'))

    def test_original_sources_and_unchanged_ledger_modules_match_intake(self):
        proof=load(FINAL/'preservation.json');self.assertEqual(proof['before'],proof['after'])
        for info in load(ROOT/'intake.json')['originals']:self.assertEqual(file_info(PROJECT/info['path']),info)
        for info in load(FINAL/'source-versions.json'):self.assertEqual(file_info(PROJECT/info['path']),info)


if __name__=='__main__':unittest.main()
