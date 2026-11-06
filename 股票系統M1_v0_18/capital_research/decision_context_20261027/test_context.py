"""Only direct decision isolation, account proofs and one affected integration."""
from copy import deepcopy
from decimal import localcontext
import json
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch
from capital_research import order_review
from capital_research.core import decide,resume_decision
from capital_research.lifecycle import _fp,FLAGS
from capital_research.quantity_candidates import generate
from capital_research.candidate_context_20261027.reproduce import case as quantity_case
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .prepare import ROOT,PROJECT,CASES,load,save,info
from .reproduce import case,controls,preset,regression,actual_value,stored_actual

FRESH=r'''
import os,sys,json,decimal
from pathlib import Path
def audit(event,args):
 if event=='open':
  mode,flags=args[1:3]
  if (mode and any(c in mode for c in 'wax+')) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('WRITE_FORBIDDEN')
 if event in ('os.mkdir','os.remove','os.rename','subprocess.Popen','socket.connect','socket.getaddrinfo'):raise RuntimeError('SIDE_EFFECT:'+event)
sys.addaudithook(audit)
from capital_research.core import decide,resume_decision
from capital_research.decision_context_20261027.prepare import projection
from capital_research.lifecycle import _fp
root=Path(sys.argv[1]);project=Path(sys.argv[2]);name=sys.argv[3];s=json.loads((root/'input.json').read_text())
spec=next(c for c in s['cases'] if c['name']==name);source=json.loads((project/s['source']['path']).read_text())
args,expected=projection(source,spec['round_index']);input_id=_fp(args)
for ctx in (decimal.getcontext(),decimal.DefaultContext):
 ctx.prec=5;ctx.rounding=decimal.ROUND_UP;ctx.Emin=-2;ctx.Emax=2;ctx.capitals=0;ctx.clamp=1
 for signal in ctx.traps:ctx.traps[signal]=True
 ctx.flags[decimal.Inexact]=True;ctx.flags[decimal.Rounded]=True
before=repr(decimal.getcontext());default_before=repr(decimal.DefaultContext)
calls=dict(decide=0,resume=0,inner_decide=0,bind_resume=0,ledger_replay=0,simulate=0,replay_sequence=0,save=0)
def profile(frame,event,arg):
 if event!='call':return
 p=frame.f_code.co_filename;n=frame.f_code.co_name
 for key,path,name in [('decide','/capital_research/core.py','decide'),('resume','/capital_research/core.py','resume_decision'),
  ('inner_decide','/capital_research/core.py','_decide'),('bind_resume','/continuity.py','bind_resume'),
  ('ledger_replay','/rotation_research/action_ledger.py','replay'),('simulate','/execution.py','simulate'),
  ('replay_sequence','/quantity_replay.py','replay_sequence'),('save','/rotation_research/store.py','save')]:
  if p.endswith(path) and n==name:calls[key]+=1
sys.setprofile(profile);actual=(resume_decision if name=='resume' else decide)(**args);sys.setprofile(None)
assert actual==expected and _fp(actual)==spec['expected_wrapper_id'],'ORIGINAL_DECISION_OR_METADATA_CHANGED'
assert _fp(args)==input_id and repr(decimal.getcontext())==before and repr(decimal.DefaultContext)==default_before,'CALLER_OR_INPUT_CHANGED'
assert calls['inner_decide']==1 and calls['decide']==(name=='initial') and calls['resume']==(name=='resume')
assert all(calls[k]==0 for k in ('simulate','replay_sequence','save'))
print(json.dumps(dict(case=name,actual_id=_fp(actual),equal_original_projection=True,input_unchanged=True,
 caller_unchanged=True,DefaultContext_unchanged=True,calls=calls,guard='NO_WRITE_NO_NETWORK_NO_NEW_EXECUTION_OR_REPLAY_SEQUENCE')))
'''


class DecisionContextTests(unittest.TestCase):
    def test_frozen_before_after_and_resume_precheck_boundary(self):
        for name in CASES:
            _,expected,_=case(name)
            for c in controls():
                b=load(ROOT/'before'/name/c['name']/'actual.json');a=load(ROOT/'after'/name/c['name']/'actual.json')
                if c['name']=='narrow-exponents':
                    self.assertEqual(b['error']['type'],'Overflow');self.assertIsNone(b['actual'])
                    if name=='resume':
                        self.assertEqual(b['calls']['inner_decide'],0);self.assertEqual(b['calls']['bind_resume'],1)
                        self.assertEqual(b['calls']['ledger_replay'],1);self.assertIn('bind_resume',b['traceback'])
                else:self.assertIsNone(b['error']);self.assertEqual(actual_value(b),expected)
                self.assertIsNone(a['error']);self.assertEqual(actual_value(a),expected)
                self.assertEqual(a['source_version'],info(ROOT.parent/'core.py'))
                self.assertTrue(a['input_unchanged']);self.assertTrue(a['caller_context_unchanged'])

    def test_original_capital_account_rights_fills_reserve_latest_and_all_tokens(self):
        oracle=load(ROOT/'expected.json');rows=[]
        for name in CASES:
            args,expected,_=case(name);r=actual_value(load(ROOT/'after'/name/'normal/actual.json'));d=r['decision'];a=args['data']['account']
            self.assertEqual(d['common_account_id'],_fp(a));self.assertEqual(d['reserved_cash'],oracle['reserve'])
            self.assertEqual(a['cash_claims'][0]['amount'],oracle['cash_claim']);self.assertEqual(a['share_claims'][0]['shares'],oracle['share_claim'])
            self.assertEqual(r['source_integrity_metadata'],expected['source_integrity_metadata'])
            if name=='initial':self.assertEqual(d['initial_capital'],oracle['initial_capital'])
            else:
                cp=args['checkpoint'];s=cp['state'];e=cp['execution_result'];old=args['previous']['decision']
                self.assertEqual(d['initial_capital'],oracle['current_resume_value']);self.assertEqual(a['settled_cash'],oracle['resume_cash'])
                self.assertEqual({c:h['shares'] for c,h in a['holdings'].items()},oracle['resume_holdings'])
                self.assertEqual(s['accepted_fills'],e['fills']);self.assertEqual([f['id'] for f in s['accepted_fills']],['r1-A-fill-0','r1-B-fill-1'])
                self.assertEqual(s['order_states'],e['order_states']);self.assertEqual([s['order_states'][k]['remaining'] for k in ('r1-A','r1-B')],['30','13'])
                self.assertTrue(all(st['status']=='EXPIRED_UNFILLED' for st in s['order_states'].values()))
                self.assertEqual(a['cash_claims'],s['row']['cash_claims']);self.assertEqual(a['share_claims'],s['row']['share_receivables'])
                self.assertEqual(d['continuity']['origin_initial_capital'],oracle['initial_capital']);self.assertEqual(s['origin_initial_capital'],oracle['initial_capital'])
                self.assertEqual(d['continuity']['latest_predecessor_id'],old['decision_id']);self.assertEqual(old['decision_id'],e['latest_decision_id'])
                self.assertEqual(old['common_account_id'],e['latest_common_account_id']);self.assertEqual(d['continuity']['checkpoint_id'],cp['checkpoint_id'])
                self.assertTrue(set(s['reviewed_evidence_tokens'])<=set(d['reviewed_evidence_tokens']))
                self.assertTrue(set(old['reviewed_evidence_tokens'])<=set(d['reviewed_evidence_tokens']))
            for k in FLAGS:self.assertIs(d[k],False)
            self.assertIsNone(d['primary_pressure_id']);self.assertEqual(d['decision_id'],expected['decision']['decision_id'])
            rows.append(dict(case=name,decision_id=d['decision_id'],account=a,current_value=d['initial_capital'],
                continuity=d.get('continuity'),reviewed_tokens=d['reviewed_evidence_tokens'],metadata=r['source_integrity_metadata']))
        for e in load(ROOT/'intake.json')['originals']:self.assertEqual(info(PROJECT/e['path']),e)
        save(ROOT/'test-evidence/account-and-history.json',rows)

    def test_five_rejections_remain_exact_under_normal_and_preset(self):
        for spec in load(ROOT/'regression-specs.json'):
            for c in ('normal','preset'):
                b=load(ROOT/'before/regressions'/spec['name']/c/'actual.json');a=load(ROOT/'after/regressions'/spec['name']/c/'actual.json')
                self.assertIsNone(a['actual']);self.assertEqual(a['error']['type'],'ValueError');self.assertIn(spec['error'],a['error']['detail'])
                self.assertTrue(a['expected_rejection']);self.assertTrue(a['input_unchanged']);self.assertTrue(a['caller_context_unchanged'])
                self.assertEqual(a['input_id'],_fp(regression(spec['name'])))
                if c=='normal' or spec['name']=='missing-checkpoint':self.assertEqual(a['error'],b['error'])
                else:self.assertEqual(b['error']['type'],'Clamped')

    def test_preset_pure_calls_preserve_input_and_all_context_fields(self):
        rows=[];blocked=AssertionError('PURE_DECISION_SIDE_EFFECT')
        for name in CASES:
            args,expected,spec=case(name);unchanged=deepcopy(args)
            with localcontext(context(preset())) as ctx:
                before=snapshot(ctx)
                with patch('builtins.open',side_effect=blocked),patch.object(socket.socket,'connect',side_effect=blocked), \
                        patch('capital_research.execution.simulate',side_effect=blocked), \
                        patch('capital_research.quantity_replay.replay_sequence',side_effect=blocked):
                    value=(resume_decision if name=='resume' else decide)(**args)
                after=snapshot(ctx)
            self.assertEqual(value,expected);self.assertEqual(args,unchanged);self.assertEqual(before,after)
            rows.append(dict(case=name,actual=stored_actual(value,spec,expected),caller_before=before,caller_after=after,input_unchanged=True))
        save(ROOT/'test-evidence/preset.json',rows)

    def test_fresh_DefaultContext_both_entries_no_IO_or_market_replay(self):
        rows=[]
        for name in CASES:
            p=subprocess.run([sys.executable,'-B','-c',FRESH,str(ROOT),str(PROJECT),name],cwd=PROJECT,text=True,capture_output=True)
            save(ROOT/'test-evidence/fresh'/name/'actual.json',dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
            self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(p.stderr);v=json.loads(p.stdout)
            for k in ('equal_original_projection','input_unchanged','caller_unchanged','DefaultContext_unchanged'):self.assertTrue(v[k])
            self.assertEqual(v['calls']['inner_decide'],1)
            for k in ('simulate','replay_sequence','save'):self.assertEqual(v['calls'][k],0)
            rows.append(v)
        save(ROOT/'test-evidence/fresh/summary.json',rows)

    def test_existing_quantity_gate_full_result_unchanged(self):
        data,expected,spec=quantity_case('initial');unchanged=deepcopy(data)
        with localcontext(context(preset())) as ctx:
            before=snapshot(ctx);value=generate(data);after=snapshot(ctx)
        self.assertEqual(value,expected);self.assertEqual(data,unchanged);self.assertEqual(before,after)
        save(ROOT/'test-evidence/quantity-integration.json',dict(input_id=_fp(data),expected_generation_id=spec['expected_generation_id'],
            actual_generation_id=_fp(value),full_output_equal=True,input_unchanged=True,caller_unchanged=True,
            original_source=spec['source'],round_index=spec['round_index']))


if __name__=='__main__':unittest.main()
