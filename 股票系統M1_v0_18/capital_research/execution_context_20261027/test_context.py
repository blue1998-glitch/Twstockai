"""Only direct execution context and directly dependent account/checkpoint gates."""
from copy import deepcopy
from decimal import localcontext
import json
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch
from capital_research import order_review
from capital_research.execution import simulate
from capital_research.continuity import make_checkpoint
from capital_research.lifecycle import _fp,FLAGS
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .prepare import ROOT,PROJECT,CASES,load,save,info
from .reproduce import source,case,controls,preset,regression,actual_value,stored_actual

FRESH=r'''
import os,sys,json,decimal
from pathlib import Path
def audit(event,args):
 if event=='open':
  mode,flags=args[1:3]
  if (mode and any(c in mode for c in 'wax+')) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('WRITE_FORBIDDEN')
 if event in ('os.mkdir','os.remove','os.rename','subprocess.Popen','socket.connect','socket.getaddrinfo'):raise RuntimeError('SIDE_EFFECT:'+event)
sys.addaudithook(audit)
from capital_research.execution import simulate
from capital_research.lifecycle import _fp
root=Path(sys.argv[1]);project=Path(sys.argv[2]);name=sys.argv[3];s=json.loads((root/'input.json').read_text())
spec=next(c for c in s['cases'] if c['name']==name);source=json.loads((project/s['source']['path']).read_text())
frame=source['replay']['rounds'][spec['round_index']];job=frame['execution_job'];expected=frame['execution'];input_id=_fp(job)
for ctx in (decimal.getcontext(),decimal.DefaultContext):
 ctx.prec=5;ctx.rounding=decimal.ROUND_UP;ctx.Emin=-2;ctx.Emax=2;ctx.capitals=0;ctx.clamp=1
 for signal in ctx.traps:ctx.traps[signal]=True
 ctx.flags[decimal.Inexact]=True;ctx.flags[decimal.Rounded]=True
before=repr(decimal.getcontext());default_before=repr(decimal.DefaultContext)
calls=dict(simulate=0,decide=0,resume=0,ledger_replay=0,risk=0,replay_sequence=0,generate=0,save=0)
def profile(frame,event,arg):
 if event!='call':return
 p=frame.f_code.co_filename;n=frame.f_code.co_name
 for key,path,name in [('simulate','/capital_research/execution.py','simulate'),('decide','/capital_research/core.py','decide'),
  ('resume','/capital_research/core.py','resume_decision'),('ledger_replay','/rotation_research/action_ledger.py','replay'),
  ('risk','/transition_risk.py','inspect_risk'),('replay_sequence','/quantity_replay.py','replay_sequence'),
  ('generate','/quantity_candidates.py','generate'),('save','/rotation_research/store.py','save')]:
  if p.endswith(path) and n==name:calls[key]+=1
sys.setprofile(profile);actual=simulate(job);sys.setprofile(None)
assert actual==expected and _fp(actual)==spec['expected_execution_id'],'SAVED_EXECUTION_CHANGED'
assert _fp(job)==input_id and repr(decimal.getcontext())==before and repr(decimal.DefaultContext)==default_before,'CALLER_OR_INPUT_CHANGED'
assert calls['simulate']==1 and calls['ledger_replay']>0 and calls['risk']>0
assert all(calls[k]==0 for k in ('replay_sequence','generate','save'))
print(json.dumps(dict(case=name,actual_id=_fp(actual),result_id=actual['result_id'],equal_original_execution=True,
 input_unchanged=True,caller_unchanged=True,DefaultContext_unchanged=True,calls=calls,
 guard='ONE_DIRECT_SYNTHETIC_SIMULATE_NO_QUANTITY_PRODUCER_NO_WRITE_NO_NETWORK')))
'''


class ExecutionContextTests(unittest.TestCase):
    def test_frozen_before_after_and_post_decision_failure_boundary(self):
        for name in CASES:
            _,expected,_=case(name)
            for c in controls():
                b=load(ROOT/'before'/name/c['name']/'actual.json');a=load(ROOT/'after'/name/c['name']/'actual.json')
                error={'inexact-trap':'Inexact','narrow-exponents':'Overflow'}.get(c['name'])
                if error:
                    self.assertEqual(b['error']['type'],error);self.assertIsNone(b['actual'])
                    self.assertIn('state = replay',b['traceback']);self.assertIn('action_ledger.py',b['traceback'])
                    self.assertEqual(b['calls']['decide']+b['calls']['resume'],1);self.assertEqual(b['calls']['risk'],0)
                elif name=='continuation' and c['name']=='round-up':
                    self.assertIsNone(b['error']);self.assertNotEqual(actual_value(b),expected)
                else:self.assertIsNone(b['error']);self.assertEqual(actual_value(b),expected)
                self.assertIsNone(a['error']);self.assertEqual(actual_value(a),expected)
                self.assertEqual(a['source_version'],info(ROOT.parent/'execution.py'))
                self.assertTrue(a['input_unchanged']);self.assertTrue(a['caller_context_unchanged'])
        delta=load(ROOT/'before/round-up-difference.json')
        self.assertEqual([e['path'] for e in delta['differences']],['/ledger/scenario_net_return','/result_id'])
        for k in ('fills_unchanged','daily_ledger_unchanged','orders_and_states_unchanged'):self.assertTrue(delta[k])

    def test_original_capital_fills_settlement_rights_reserve_latest_tokens_and_prefix(self):
        oracle=load(ROOT/'expected.json');records=[];values=[]
        for name in CASES:
            job,expected,_=case(name);a=actual_value(load(ROOT/'after'/name/'normal/actual.json'));values.append(a)
            self.assertEqual(a,expected);self.assertEqual(a['ledger']['initial_equity'],oracle['initial_capital'])
            self.assertEqual(a['origin_ledger_input_id'],_fp(job['ledger_input']))
            latest=a['decision_records'][a['latest_decision_id']]
            self.assertEqual(latest['common_account_id'],a['latest_common_account_id']);self.assertEqual(latest['reserved_cash'],oracle['general_reserve'])
            for k in FLAGS:self.assertIs(a[k],False)
            self.assertIsNone(a['ledger']['total_net_return']);self.assertIsNone(a['ledger']['primary_pressure_id'])
            self.assertEqual(len({f['id'] for f in a['fills']}),len(a['fills']))
            records.append(dict(case=name,origin_ledger_input_id=a['origin_ledger_input_id'],origin_common_account_id=a['origin_common_account_id'],
                initial_capital=a['ledger']['initial_equity'],general_reserve=latest['reserved_cash'],
                latest_decision_id=a['latest_decision_id'],latest_common_account_id=a['latest_common_account_id'],tokens=a['reviewed_evidence_tokens'],
                fills=a['fills'],order_states=a['order_states'],events=a['execution_events'],risk_observations=a['risk_observations'],
                account_curve=[{k:row[k] for k in ('date','settled_cash','available_cash_strict','cash_receivable','purchase_payable','shares','share_receivables','net_accrual_equity')} for row in a['ledger']['daily']]))
        first,last=values;x=first['ledger']['daily'][-1];y=last['ledger']['daily'][-1]
        self.assertEqual([f['id'] for f in first['fills']],oracle['first_fill_ids']);self.assertEqual([f['id'] for f in last['fills']],oracle['all_fill_ids'])
        self.assertEqual(last['fills'][:len(first['fills'])],first['fills']);self.assertEqual(last['order_history'][:len(first['order_history'])],first['order_history'])
        self.assertEqual(last['ledger']['daily'][:len(first['ledger']['daily'])],first['ledger']['daily'])
        self.assertEqual(last['ledger']['journal'][:len(first['ledger']['journal'])],first['ledger']['journal'])
        for key,remaining in [('r1-A','30'),('r1-B','13')]:
            self.assertEqual(first['order_states'][key],last['order_states'][key]);self.assertEqual(first['order_states'][key]['remaining'],remaining)
            self.assertEqual(first['order_states'][key]['status'],'EXPIRED_UNFILLED');self.assertEqual(first['order_states'][key]['reserved_cash'],'0')
        self.assertEqual(x['shares'],oracle['first_shares']);self.assertEqual(x['settled_cash'],oracle['first_cash']);self.assertEqual(x['cash_receivable'],'80')
        self.assertEqual(x['share_receivables'][0]['shares'],'10');self.assertNotIn('end_net_equity',first['ledger']);self.assertIsNone(first['ledger']['scenario_net_return'])
        self.assertEqual(y['shares'],oracle['final_shares']);self.assertEqual(y['settled_cash'],oracle['final_cash']);self.assertEqual(y['net_accrual_equity'],oracle['final_nav'])
        self.assertEqual(y['cash_claims'],[]);self.assertEqual(y['share_receivables'],[]);self.assertEqual(y['purchase_payable'],'0')
        self.assertEqual(last['ledger']['fees_and_tax_on_fills'],oracle['final_fill_fees_and_tax'])
        journal=last['ledger']['journal'];cash=[j for j in journal if j['type']=='CASH_RECEIVED' and j.get('claim_id')=='opening-cash']
        share=[j for j in journal if j['type']=='SHARES_TRADABLE' and j.get('event_id')=='opening-shares']
        self.assertEqual(len(cash),1);self.assertEqual(cash[0]['date'],'2026-01-12');self.assertEqual(cash[0]['amount'],'80')
        self.assertEqual(len(share),1);self.assertEqual(share[0]['date'],'2026-01-12');self.assertEqual(share[0]['shares'],'10')
        for fill in last['fills']:
            settled=[j for j in journal if (fill['side']=='BUY' and j['type']=='PURCHASE_SETTLED' and j.get('fill_id')==fill['id']) or (fill['side']=='SELL' and j['type']=='CASH_RECEIVED' and j.get('claim_id')==fill['id'])]
            self.assertEqual(len(settled),1);self.assertEqual(settled[0]['date'],fill['settlement_date'])
        self.assertEqual(first['origin_common_account_id'],last['origin_common_account_id']);self.assertTrue(set(first['reviewed_evidence_tokens'])<=set(last['reviewed_evidence_tokens']))
        for e in load(ROOT/'intake.json')['originals']:self.assertEqual(info(PROJECT/e['path']),e)
        save(ROOT/'test-evidence/account-chain.json',records)

    def test_cost_rights_and_latest_rejections_match_before_and_frozen_expectations(self):
        for spec in load(ROOT/'regression-specs.json'):
            for name in ('normal','preset'):
                b=load(ROOT/'before/regressions'/spec['name']/name/'actual.json');a=load(ROOT/'after/regressions'/spec['name']/name/'actual.json')
                self.assertIsNone(a['actual']);self.assertEqual(a['error'],b['error']);self.assertEqual(a['error']['type'],'ValueError')
                self.assertIn(spec['error'],a['error']['detail']);self.assertTrue(a['expected_rejection'])
                self.assertTrue(a['input_unchanged']);self.assertTrue(a['caller_context_unchanged']);self.assertEqual(a['input_id'],_fp(regression(spec['name'])))

    def test_preset_pure_call_preserves_input_and_all_caller_fields(self):
        rows=[];blocked=AssertionError('DIRECT_SIMULATE_SIDE_EFFECT')
        for name in CASES:
            job,expected,spec=case(name);unchanged=deepcopy(job)
            with localcontext(context(preset())) as ctx:
                before=snapshot(ctx)
                with patch('builtins.open',side_effect=blocked),patch.object(socket.socket,'connect',side_effect=blocked), \
                        patch('capital_research.quantity_replay.replay_sequence',side_effect=blocked), \
                        patch('capital_research.quantity_candidates.generate',side_effect=blocked):value=simulate(job)
                after=snapshot(ctx)
            self.assertEqual(value,expected);self.assertEqual(job,unchanged);self.assertEqual(before,after)
            rows.append(dict(case=name,actual=stored_actual(value,spec,expected),caller_before=before,caller_after=after,input_unchanged=True))
        save(ROOT/'test-evidence/preset.json',rows)

    def test_fresh_DefaultContext_both_jobs_no_producer_write_or_network(self):
        rows=[]
        for name in CASES:
            p=subprocess.run([sys.executable,'-B','-c',FRESH,str(ROOT),str(PROJECT),name],cwd=PROJECT,text=True,capture_output=True)
            save(ROOT/'test-evidence/fresh'/name/'actual.json',dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
            self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(p.stderr);a=json.loads(p.stdout)
            for k in ('equal_original_execution','input_unchanged','caller_unchanged','DefaultContext_unchanged'):self.assertTrue(a[k])
            self.assertEqual(a['calls'],load(ROOT/'after'/name/'normal/actual.json')['calls']);rows.append(a)
        save(ROOT/'test-evidence/fresh/summary.json',rows)

    def test_existing_checkpoint_accepts_complete_result_without_replaying_quantity_workflow(self):
        _,raw=source();rows=[]
        for name in CASES:
            job,_,spec=case(name);actual=actual_value(load(ROOT/'after'/name/'normal/actual.json'));before=_fp(actual)
            with localcontext(context(controls()[0]['context'])):
                cp=make_checkpoint(job['ledger_input'],actual,through_at=job['observed_until'])
            self.assertEqual(cp,raw['replay']['rounds'][spec['round_index']]['checkpoint']);self.assertEqual(_fp(actual),before)
            self.assertEqual(cp['checkpoint_id'],spec['expected_checkpoint_id'])
            rows.append(dict(case=name,checkpoint_id=cp['checkpoint_id'],state_id=cp['state_id'],state=cp['state'],source_result_id=actual['result_id']))
        save(ROOT/'test-evidence/checkpoint-compatibility.json',rows)


if __name__=='__main__':unittest.main()
