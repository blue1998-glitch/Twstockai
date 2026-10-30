"""Only the reproduced ambient-context defect and directly affected interfaces."""
from copy import deepcopy
import decimal
import json
import subprocess
import sys
import unittest
from unittest.mock import patch
from capital_research.account_metrics import evaluate_saved
from capital_research.lifecycle import _fp,FLAGS
from capital_research.account_metrics_20261027.fixtures import resolve
from .prepare import ROOT,PROJECT,load,save,info
from .reproduce import context,snapshot,request

FRESH=r'''
import sys,os,json,decimal,importlib.abc
from pathlib import Path
allowed={'capital_research.account_metrics','capital_research.lifecycle'}
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith(('graph_core','rotation_research')) or (fullname.startswith('capital_research.') and fullname not in allowed):raise RuntimeError('UNRELATED_ENGINE_IMPORT:'+fullname)
sys.meta_path.insert(0,Guard())
def audit(event,args):
 if event=='open':
  m,f=args[1:3]
  if (m and any(c in m for c in 'wax+')) or f&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('WRITE_FORBIDDEN')
 if event in ('os.mkdir','os.rename','os.remove','subprocess.Popen','socket.connect','socket.getaddrinfo'):raise RuntimeError('SIDE_EFFECT:'+event)
sys.addaudithook(audit)
root=Path(sys.argv[1]);project=Path(sys.argv[2]);spec=json.loads((root/'input.json').read_text())
for c in (decimal.DefaultContext,decimal.getcontext()):
 c.prec=5;c.rounding=decimal.ROUND_DOWN;c.Emin=-2;c.Emax=2;c.capitals=0;c.clamp=1
 for signal in c.traps:c.traps[signal]=True
 c.flags[decimal.Inexact]=True;c.flags[decimal.Rounded]=True
before=repr(decimal.getcontext());default_before=repr(decimal.DefaultContext)
from capital_research.account_metrics import evaluate_saved
saved=json.loads((project/spec['saved_source']['path']).read_text());expected=json.loads((project/spec['baseline_expected']['path']).read_text())
actual=evaluate_saved(dict(schema='capital-account-metrics-input/0.1',synthetic=True,evaluation_at=spec['evaluation_at'],saved_result=saved))
assert actual==expected,'NORMAL_SAVED_RESULT_CHANGED'
assert repr(decimal.getcontext())==before and repr(decimal.DefaultContext)==default_before,'CALLER_CONTEXT_CHANGED'
print(json.dumps(dict(status=actual['status'],evaluation_id=actual['evaluation_id'],equal_original_normal=True,caller_context_unchanged=True,
 default_context_unchanged=True,guard='FRESH_MUTATED_DEFAULTCONTEXT_NO_REPLAY_NO_WRITE_NO_NETWORK')))
'''


class ContextTests(unittest.TestCase):
    def test_frozen_before_and_after_results_confirm_only_actual_failures(self):
        spec=load(ROOT/'input.json');expected=load(PROJECT/spec['baseline_expected']['path'])
        names=[v['name'] for v in spec['contexts']]+['different-rounding-down']
        before={n:load(ROOT/'before'/n/'actual.json') for n in names}
        self.assertTrue(before['normal']['equal_original_normal'])
        self.assertTrue(before['different-rounding']['equal_original_normal'])
        self.assertEqual(before['inexact-trap']['error']['type'],'Inexact')
        self.assertEqual(before['narrow-exponents']['error']['type'],'Overflow')
        self.assertFalse(before['different-rounding-down']['equal_original_normal'])
        for name in names:
            r=load(ROOT/'after'/name/'actual.json')
            self.assertIsNone(r['error']);self.assertEqual(r['actual'],expected)
            self.assertTrue(r['caller_context_unchanged']);self.assertTrue(r['input_unchanged'])
            self.assertEqual(r['source_version'],info(ROOT.parent/'account_metrics.py'))

    def test_pure_evaluation_preserves_caller_flags_traps_and_exact_input(self):
        controls=load(ROOT/'test-controls.json');data=request();saved=deepcopy(data)
        with decimal.localcontext(context(controls['preset_context'])) as ctx:
            before=snapshot(ctx)
            with patch('builtins.open',side_effect=AssertionError('PURE_IO')):r=evaluate_saved(data)
            after=snapshot(ctx)
        expected=load(PROJECT/load(ROOT/'input.json')['baseline_expected']['path'])
        self.assertEqual(r,expected);self.assertEqual(before,after);self.assertEqual(data,saved)
        save(ROOT/'test-evidence/preset-state.json',dict(actual=r,caller_before=before,caller_after=after,input_unchanged=data==saved))

    def test_unknown_ledger_still_refuses_without_zero_or_qualification_promotion(self):
        controls=load(ROOT/'test-controls.json')
        for key in ('negative_recipe','negative_expected'):self.assertEqual(info(PROJECT/controls[key]['path']),controls[key])
        data=resolve(load(PROJECT/controls['negative_recipe']['path']));before=_fp(data)
        with decimal.localcontext(context(controls['preset_context'])):r=evaluate_saved(data)
        self.assertEqual(r,load(PROJECT/controls['negative_expected']['path']));self.assertEqual(_fp(data),before)
        self.assertEqual(r['status'],'REFUSED');self.assertIsNone(r['statistics'])
        for k in FLAGS:self.assertIs(r[k],False)
        self.assertIsNone(r['primary_pressure_id']);self.assertIsNone(r['ranking'])
        save(ROOT/'test-evidence/unknown-refused.json',dict(actual=r,input_unchanged=True))

    def test_existing_workflow_evaluation_hook_inherits_fix_without_new_replay(self):
        from capital_research import evaluated_replay as flow
        data=request();before=_fp(data);controls=load(ROOT/'test-controls.json')
        with decimal.localcontext(context(controls['preset_context'])):
            with patch.object(flow,'_replay',side_effect=AssertionError('REPLAY_NOT_AUTHORIZED')):r=flow._evaluate(data)
        self.assertEqual(r,load(PROJECT/load(ROOT/'input.json')['baseline_expected']['path']))
        self.assertEqual(before,_fp(data));self.assertEqual(r['account']['origin_initial_capital'],'2230')
        self.assertEqual(r['account']['general_reserved_cash'],'100')
        save(ROOT/'test-evidence/existing-evaluation-hook.json',dict(status=r['status'],evaluation_id=r['evaluation_id'],
            replay_calls=0,request_unchanged=True,account_id=r['account']['latest_common_account_id'],
            reviewed_tokens=r['account']['reviewed_evidence_tokens']))

    def test_fresh_process_is_independent_of_mutated_DefaultContext_and_has_no_side_effects(self):
        p=subprocess.run([sys.executable,'-B','-c',FRESH,str(ROOT),str(PROJECT)],cwd=PROJECT,text=True,capture_output=True)
        save(ROOT/'test-evidence/fresh-process.json',dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
        self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(p.stderr)
        r=json.loads(p.stdout);self.assertTrue(r['equal_original_normal']);self.assertTrue(r['caller_context_unchanged'])
        self.assertTrue(r['default_context_unchanged'])


if __name__=='__main__':unittest.main()
