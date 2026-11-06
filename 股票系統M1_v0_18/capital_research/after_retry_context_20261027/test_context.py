"""Only outer bridge isolation and directly dependent invariants; no old suite."""
from copy import deepcopy
from decimal import localcontext
import json
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch
from capital_research import order_review
from capital_research.quantity_after_retry import generate_after_retry
from capital_research.lifecycle import _fp,FLAGS
from capital_research.quantity_after_retry_20261027.verify import verify
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .prepare import ROOT,PROJECT,PRIMARY,REGRESSIONS,load,save,info
from .reproduce import case,controls,preset,probe,stored_actual,actual_value

FRESH=r'''
import os,sys,json,decimal
from pathlib import Path
def audit(event,args):
 if event=='open':
  mode,flags=args[1:3]
  if (mode and any(c in mode for c in 'wax+')) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('WRITE_FORBIDDEN')
 if event in ('os.mkdir','os.remove','os.rename','subprocess.Popen','socket.connect','socket.getaddrinfo'):raise RuntimeError('SIDE_EFFECT:'+event)
sys.addaudithook(audit)
from capital_research.quantity_after_retry import generate_after_retry
from capital_research.quantity_after_retry_20261027.fixtures import materialize
from capital_research.lifecycle import _fp
root=Path(sys.argv[1]);project=Path(sys.argv[2]);spec=json.loads((root/'input.json').read_text())['cases'][0]
data=materialize(json.loads((project/spec['input_spec']['path']).read_text()))
expected=json.loads((project/spec['original_actual']['path']).read_text());input_id=_fp(data)
for ctx in (decimal.getcontext(),decimal.DefaultContext):
 ctx.prec=5;ctx.rounding=decimal.ROUND_UP;ctx.Emin=-2;ctx.Emax=2;ctx.capitals=0;ctx.clamp=1
 for signal in ctx.traps:ctx.traps[signal]=True
 ctx.flags[decimal.Inexact]=True;ctx.flags[decimal.Rounded]=True
before=repr(decimal.getcontext());default_before=repr(decimal.DefaultContext)
calls=dict(bridge=0,generate=0,ledger_replay=0,simulate=0,replay_sequence=0,retry=0,save=0)
def profile(frame,event,arg):
 if event!='call':return
 p=frame.f_code.co_filename;n=frame.f_code.co_name
 for key,path,name in [('bridge','/quantity_after_retry.py','generate_after_retry'),('generate','/quantity_candidates.py','generate'),
  ('ledger_replay','/action_ledger.py','replay'),('simulate','/execution.py','simulate'),('replay_sequence','/quantity_replay.py','replay_sequence'),
  ('retry','/conditional_retry.py','retry_rejected'),('save','/rotation_research/store.py','save')]:
  if p.endswith(path) and n==name:calls[key]+=1
sys.setprofile(profile);actual=generate_after_retry(data);sys.setprofile(None)
assert actual==expected and _fp(actual)==spec['expected_result_id'],'SAVED_RESULT_CHANGED'
assert _fp(data)==input_id and repr(decimal.getcontext())==before and repr(decimal.DefaultContext)==default_before,'CALLER_OR_INPUT_CHANGED'
assert calls['bridge']==1 and calls['generate']==1 and calls['ledger_replay']>0
assert all(calls[k]==0 for k in ('simulate','replay_sequence','retry','save'))
print(json.dumps(dict(actual_id=_fp(actual),equal_saved_result=True,input_unchanged=True,caller_unchanged=True,
 DefaultContext_unchanged=True,calls=calls,guard='NO_WRITE_NO_NETWORK_NO_MARKET_REPLAY_OR_NEW_EXECUTION')))
'''


class AfterRetryContextTests(unittest.TestCase):
    def test_saved_before_after_and_boundary_match_frozen_oracles(self):
        for name in PRIMARY:
            _,expected,spec=case(name)
            for c in controls():
                before=load(ROOT/'before'/name/c['name']/'actual.json');after=load(ROOT/'after'/name/c['name']/'actual.json')
                error={'inexact-trap':'Inexact','narrow-exponents':'Overflow'}.get(c['name'])
                if error:
                    self.assertEqual(before['error']['type'],error);self.assertIsNone(before['actual'])
                else:self.assertIsNone(before['error']);self.assertEqual(actual_value(before),expected)
                self.assertIsNone(after['error']);self.assertEqual(actual_value(after),expected)
                self.assertEqual(after['source_version'],info(ROOT.parent/'quantity_after_retry.py'))
                self.assertTrue(after['caller_context_unchanged']);self.assertTrue(after['input_unchanged'])
                self.assertEqual(after['input_id'],spec['materialized_input_id'])
        for c in ('inexact-trap','narrow-exponents'):
            b=load(ROOT/'before/boundary'/c/'actual.json')
            self.assertEqual(b['calls'],dict(bridge=1,generate=0,ledger_replay=1,simulate=0,retry=0))
            self.assertIn('validate_checkpoint',b['traceback']);self.assertIn('action_ledger.py',b['traceback'])
            self.assertEqual(b['source_version'],load(ROOT/'intake.json')['source_before'])

    def test_current_account_origin_rights_reserve_latest_tokens_and_candidates(self):
        rows=[];oracle=load(ROOT/'expected.json')
        for name in PRIMARY:
            data,_,spec=case(name);value=actual_value(load(ROOT/'after'/name/'normal/actual.json'))
            verify(data,load(PROJECT/spec['expected_spec']['path']),value)
            a=value['adapter'];r=a['generation']['research'];cp=data['checkpoint'];s=cp['state'];e=cp['execution_result'];b=a['binding']
            self.assertEqual(a['quantity_request']['continuation']['checkpoint'],cp)
            self.assertEqual(cp['origin_ledger_input'],data['saved_result']['review']['execution_job']['ledger_input'])
            self.assertEqual(s['accepted_fills'],e['fills']);self.assertEqual(s['order_states'],e['order_states'])
            self.assertEqual(b['latest_decision_id'],e['latest_decision_id']);self.assertEqual(b['latest_common_account_id'],e['latest_common_account_id'])
            self.assertEqual(b['reviewed_evidence_tokens'],s['reviewed_evidence_tokens']);self.assertEqual(len(b['reviewed_evidence_tokens']),oracle['historical_tokens'])
            self.assertEqual(a['quantity_request']['decision_input']['consumed_evidence_tokens'],s['reviewed_evidence_tokens'])
            self.assertEqual([v['outcome'] for v in e['reassessment_attempts']],oracle['received_attempt_outcomes'])
            self.assertEqual(b['received_attempt_ids'],[v['attempt_id'] for v in e['reassessment_attempts']])
            self.assertEqual(b['origin_initial_capital'],oracle['origin_initial_capital'])
            self.assertEqual(r['initial_capital'],oracle['current_account_value'])
            self.assertEqual(a['account']['settled_cash'],oracle['settled_cash']);self.assertEqual(a['account']['reserved_cash'],oracle['general_reserved_cash'])
            self.assertEqual({c:h['shares'] for c,h in a['account']['holdings'].items()},oracle['holdings'])
            self.assertEqual(a['account']['cash_claims'],s['row']['cash_claims']);self.assertEqual(a['account']['share_claims'],s['row']['share_receivables'])
            self.assertEqual(a['account']['payables'],[]);self.assertEqual(a['account']['pending_orders'],[]);self.assertEqual(s['unfilled_orders'],[])
            self.assertEqual(r['baseline']['continuity']['latest_predecessor_id'],e['latest_decision_id'])
            self.assertTrue(set(s['reviewed_evidence_tokens'])<=set(r['baseline']['reviewed_evidence_tokens']))
            if name=='new-independent-trigger':self.assertIn('WAIT_SETTLEMENT_REASSESSMENT',[c['classification'] for c in r['candidates']])
            for v in (a,r):
                for k in FLAGS:self.assertIs(v[k],False)
                self.assertIsNone(v['ranking']);self.assertIsNone(v['selected_id']);self.assertIsNone(v['primary_pressure_id'])
                self.assertEqual(v['execution'],'NOT_PERFORMED');self.assertEqual(v['order_generation'],'NOT_PERFORMED')
            rows.append(dict(case=name,account=a['account'],binding=b,origin_opening=cp['origin_ledger_input']['opening'],
                accepted_fill_ids=[f['id'] for f in s['accepted_fills']],order_states=s['order_states'],current_account_value=r['initial_capital'],
                candidates=[{k:c[k] for k in ('id','classification','additional_B','reasons')} for c in r['candidates']]))
        for meta in load(ROOT/'intake.json')['originals']:self.assertEqual(info(PROJECT/meta['path']),meta)
        save(ROOT/'test-evidence/account-and-candidates.json',rows)

    def test_preset_input_and_context_preserved_without_IO_or_market_execution(self):
        data,expected,spec=case(PRIMARY[0]);unchanged=deepcopy(data);blocked=AssertionError('PUBLIC_BRIDGE_SIDE_EFFECT')
        with localcontext(context(preset())) as ctx:
            before=snapshot(ctx)
            with patch('builtins.open',side_effect=blocked),patch.object(socket.socket,'connect',side_effect=blocked), \
                    patch('capital_research.execution.simulate',side_effect=blocked), \
                    patch('capital_research.quantity_replay.simulate',side_effect=blocked), \
                    patch('capital_research.quantity_replay.replay_sequence',side_effect=blocked), \
                    patch('capital_research.conditional_retry.retry_rejected',side_effect=blocked), \
                    patch('capital_research.conditional_retry.simulate',side_effect=blocked):value=generate_after_retry(data)
            after=snapshot(ctx)
        self.assertEqual(value,expected);self.assertEqual(data,unchanged);self.assertEqual(before,after)
        save(ROOT/'test-evidence/preset.json',dict(actual=stored_actual(value,spec,expected),caller_before=before,caller_after=after,input_unchanged=True))

    def test_latest_token_and_search_limit_refusals_preserved(self):
        rows=[]
        for name in REGRESSIONS:
            data,expected,spec=case(name)
            for setting in (controls()[0],dict(name='preset',context=preset())):
                value,trace=probe(data,setting['context']);self.assertIsNone(trace['error']);self.assertEqual(value,expected)
                verify(data,load(PROJECT/spec['expected_spec']['path']),value)
                self.assertTrue(trace['input_unchanged']);self.assertTrue(trace['caller_context_unchanged'])
                rows.append(dict(case=name,context=setting['name'],actual=stored_actual(value,spec,expected),trace=trace))
        save(ROOT/'test-evidence/refusals.json',rows)

    def test_fresh_process_DefaultContext_isolated_no_write_or_replay(self):
        p=subprocess.run([sys.executable,'-B','-c',FRESH,str(ROOT),str(PROJECT)],cwd=PROJECT,text=True,capture_output=True)
        save(ROOT/'test-evidence/fresh-process.json',dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
        self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(p.stderr);r=json.loads(p.stdout)
        for k in ('equal_saved_result','input_unchanged','caller_unchanged','DefaultContext_unchanged'):self.assertTrue(r[k])
        self.assertEqual(r['calls']['bridge'],1);self.assertEqual(r['calls']['generate'],1);self.assertGreater(r['calls']['ledger_replay'],0)
        for k in ('simulate','replay_sequence','retry','save'):self.assertEqual(r['calls'][k],0)


if __name__=='__main__':unittest.main()
