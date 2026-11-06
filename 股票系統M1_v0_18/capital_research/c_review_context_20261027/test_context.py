"""Only two C outer scopes and selected dependent saved outcomes."""
from copy import deepcopy
from decimal import localcontext
import json
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch
from capital_research import order_review
from capital_research.conditional_quantity_review import reassess_conditional
from capital_research.conditional_retry import retry_rejected
from capital_research.lifecycle import _fp,FLAGS,summarize_saved
from capital_research.c_order_review_20261026.verify import verify as verify_review
from capital_research.c_order_retry_20261027.verify import verify as verify_retry
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .prepare import ROOT,PROJECT,PRIMARY,load,save,info
from .reproduce import case,controls,preset,source_versions,actual_value,stored_actual

FRESH=r'''
import os,sys,json,decimal
from pathlib import Path
def audit(event,args):
 if event=='open':
  mode,flags=args[1:3]
  if (mode and any(c in mode for c in 'wax+')) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('WRITE_FORBIDDEN')
 if event in ('os.mkdir','os.remove','os.rename','subprocess.Popen','socket.connect','socket.getaddrinfo'):raise RuntimeError('SIDE_EFFECT:'+event)
sys.addaudithook(audit)
from capital_research.conditional_quantity_review import reassess_conditional
from capital_research.conditional_retry import retry_rejected
from capital_research.lifecycle import _fp
root=Path(sys.argv[1]);project=Path(sys.argv[2]);name=sys.argv[3];s=json.loads((root/'input.json').read_text())
spec=next(c for c in s['cases'] if c['name']==name)
request=json.loads((project/spec['input']['path']).read_text());expected=json.loads((project/spec['original_actual']['path']).read_text());input_id=_fp(request)
for ctx in (decimal.getcontext(),decimal.DefaultContext):
 ctx.prec=5;ctx.rounding=decimal.ROUND_UP;ctx.Emin=-2;ctx.Emax=2;ctx.capitals=0;ctx.clamp=1
 for signal in ctx.traps:ctx.traps[signal]=True
 ctx.flags[decimal.Inexact]=True;ctx.flags[decimal.Rounded]=True
before=repr(decimal.getcontext());default_before=repr(decimal.DefaultContext)
calls=dict(review=0,retry=0,quantity_replay=0,simulate=0,ledger_replay=0,generate=0,save=0)
def profile(frame,event,arg):
 if event!='call':return
 p=frame.f_code.co_filename;n=frame.f_code.co_name
 for key,path,name in [('review','/conditional_quantity_review.py','reassess_conditional'),('retry','/conditional_retry.py','retry_rejected'),
  ('quantity_replay','/quantity_replay.py','replay_sequence'),('simulate','/execution.py','simulate'),
  ('ledger_replay','/rotation_research/action_ledger.py','replay'),('generate','/quantity_candidates.py','generate'),
  ('save','/rotation_research/store.py','save')]:
  if p.endswith(path) and n==name:calls[key]+=1
sys.setprofile(profile);actual=(reassess_conditional if spec['entry']=='review' else retry_rejected)(request);sys.setprofile(None)
assert actual==expected and _fp(actual)==spec['expected_result_id'],'ORIGINAL_C_RESULT_CHANGED'
assert _fp(request)==input_id and repr(decimal.getcontext())==before and repr(decimal.DefaultContext)==default_before,'CALLER_OR_INPUT_CHANGED'
assert calls['save']==0 and calls['review']==1 and calls['quantity_replay']==1 and calls['generate']==1
assert calls['retry']==(spec['entry']=='retry') and calls['simulate']>0 and calls['ledger_replay']>0
print(json.dumps(dict(case=name,actual_id=_fp(actual),equal_original=True,input_unchanged=True,caller_unchanged=True,
 DefaultContext_unchanged=True,calls=calls,guard='EXPLICIT_C_CALL_WITH_REQUIRED_NESTED_VERIFICATION_NO_SAVE_NO_WRITE_NO_NETWORK')))
'''


class CContextTests(unittest.TestCase):
    def test_before_intermediate_and_final_source_bound_results(self):
        old=load(ROOT/'intake.json')['sources_before']
        for name in PRIMARY:
            _,expected,_=case(name)
            for c in controls():
                b=load(ROOT/'before/primary'/name/c['name']/'actual.json');a=load(ROOT/'after/primary'/name/c['name']/'actual.json')
                error='Overflow' if c['name']=='narrow-exponents' else ('Inexact' if name=='retry' and c['name']=='inexact-trap' else None)
                if error:self.assertEqual(b['error']['type'],error);self.assertIsNone(b['actual'])
                else:self.assertIsNone(b['error']);self.assertEqual(actual_value(b),expected)
                self.assertEqual(b['source_versions'],old);self.assertIsNone(a['error']);self.assertEqual(actual_value(a),expected)
                self.assertEqual(a['source_versions'],source_versions());self.assertTrue(a['input_unchanged']);self.assertTrue(a['caller_context_unchanged'])
        for c in controls():
            m=load(ROOT/'after-review-only/primary/retry'/c['name']/'actual.json')
            self.assertEqual(m['source_versions']['conditional_retry.py'],old['conditional_retry.py'])
            self.assertEqual(m['source_versions']['conditional_quantity_review.py'],source_versions()['conditional_quantity_review.py'])
            error={'inexact-trap':'Inexact','narrow-exponents':'Overflow'}.get(c['name'])
            if error:
                self.assertEqual(m['error']['type'],error);self.assertIn('conditional_retry.py',m['traceback'])
                self.assertIn('make_checkpoint',m['traceback']);self.assertNotIn('in _reassess_conditional',m['traceback'])
                self.assertEqual(m['calls']['simulate'],3 if error=='Inexact' else 2)
            else:self.assertEqual(actual_value(m),case('retry')[1])

    def test_original_order_capital_rights_reserve_history_latest_and_tokens(self):
        rows=[];oracle=load(ROOT/'expected.json')
        for name in PRIMARY:
            request,_,s=case(name);value=actual_value(load(ROOT/'after/primary'/name/'normal/actual.json'))
            (verify_review if s['entry']=='review' else verify_retry)(request,load(PROJECT/s['expected']['path']),value)
            r=value['review'];e=r['execution'];cp=r['checkpoint'];d=r['review_decision'];scope=d['same_order_continuation']
            prior=r['prefix_execution'];order=r['original_approval']['order'];origin=r['execution_job']['ledger_input']
            self.assertEqual(scope['order_id'],oracle['order_id']);self.assertEqual(scope['original_order_quantity'],oracle['original_and_remaining_quantity'])
            self.assertEqual(scope['remaining'],oracle['original_and_remaining_quantity']);self.assertEqual(scope['trigger_ids'],oracle['trigger_ids'])
            self.assertEqual(d['new_evidence_tokens'],[]);self.assertEqual(e['order_history'],prior['order_history'])
            self.assertEqual(e['fills'][:len(prior['fills'])],prior['fills']);self.assertEqual(e['origin_ledger_input_id'],prior['origin_ledger_input_id'])
            self.assertEqual(e['origin_common_account_id'],prior['origin_common_account_id']);self.assertEqual(e['origin_ledger_input_id'],_fp(origin))
            self.assertEqual(cp['state']['origin_initial_capital'],oracle['original_capital']);self.assertEqual(cp['state']['general_reserved_cash'],oracle['general_reserve'])
            self.assertEqual(cp['state']['accepted_fills'],e['fills']);self.assertEqual(cp['state']['order_states'],e['order_states'])
            self.assertEqual(cp['state']['latest_decision_id'],e['latest_decision_id']);self.assertEqual(cp['state']['latest_common_account_id'],e['latest_common_account_id'])
            self.assertEqual(cp['state']['reviewed_evidence_tokens'],e['reviewed_evidence_tokens'])
            self.assertTrue(set(prior['reviewed_evidence_tokens'])<=set(e['reviewed_evidence_tokens']))
            self.assertEqual(len(e['fills']),len({f['id'] for f in e['fills']}))
            self.assertEqual([f['shares'] for f in e['fills'] if f['side']=='BUY' and f['code']=='B'],['20'])
            for f in e['fills']:
                if f['side']=='BUY' and f['code']=='B':self.assertEqual(e['fill_order_ids'][f['id']],order['id'])
            if s['entry']=='retry':
                previous=request['previous_result']['review']['execution']
                self.assertEqual(e['reassessment_attempts'][:len(previous['reassessment_attempts'])],previous['reassessment_attempts'])
                self.assertEqual([a['outcome'] for a in e['reassessment_attempts']],oracle['retry_attempts'])
                rejected=e['reassessment_attempts'][0]['decision']['decision_id'];self.assertNotIn(rejected,e['decision_records'])
                self.assertEqual(d['continuity']['latest_predecessor_id'],previous['latest_decision_id'])
                self.assertEqual(cp['state']['row']['settled_cash'],oracle['retry_final_cash']);self.assertEqual(cp['state']['row']['shares'],oracle['retry_final_shares'])
                self.assertEqual(cp['state']['row']['cash_claims'],[]);self.assertEqual(cp['state']['row']['share_receivables'],[])
            else:
                self.assertEqual(cp['state']['row']['cash_claims'][0]['amount'],'80');self.assertEqual(cp['state']['row']['share_receivables'][0]['shares'],'10')
            for obj in (r,d,e):
                for k in FLAGS:self.assertIs(obj[k],False)
            self.assertIsNone(r['ranking']);self.assertIsNone(r['primary_pressure_id']);self.assertIsNone(d['primary_pressure_id'])
            rows.append(dict(case=name,original_order=order,scope=scope,origin_opening=origin['opening'],row=cp['state']['row'],
                original_capital=cp['state']['origin_initial_capital'],general_reserve=cp['state']['general_reserved_cash'],
                prefix_fill_ids=[f['id'] for f in prior['fills']],fills=e['fills'],order_states=e['order_states'],
                attempts=[dict(id=a['id'],attempt_id=a['attempt_id'],outcome=a['outcome'],decision_id=a['decision']['decision_id']) for a in e['reassessment_attempts']],
                latest_decision_id=e['latest_decision_id'],latest_common_account_id=e['latest_common_account_id'],tokens=e['reviewed_evidence_tokens']))
        for m in load(ROOT/'intake.json')['originals']:self.assertEqual(info(PROJECT/m['path']),m)
        save(ROOT/'test-evidence/order-and-account.json',rows)

    def test_selected_unknown_partial_cancel_expiry_and_wrong_identity_cases(self):
        rows=[]
        for s in load(ROOT/'input.json')['cases']:
            if s['role']!='necessary_regression':continue
            request,expected,_=case(s['name'])
            for c in ('normal','preset'):
                a=load(ROOT/'after/regressions'/s['name']/c/'actual.json');self.assertIsNone(a['error'])
                value=actual_value(a);self.assertEqual(value,expected)
                (verify_review if s['entry']=='review' else verify_retry)(request,load(PROJECT/s['expected']['path']),value)
                self.assertTrue(a['input_unchanged']);self.assertTrue(a['caller_context_unchanged'])
            r=expected['review'];e=r.get('execution');state=e['order_states']['r1-B'] if e else None
            if 'unknown' in s['name']:
                self.assertEqual(r['status'],'REPLAYED_REJECTED_REVIEW');self.assertIn('NEW_CAPITAL_NOT_QUALIFIED:B',r['reasons'])
                self.assertFalse(any(f['code']=='B' and f['side']=='BUY' for f in e['fills']))
            if 'partial' in s['name']:
                self.assertEqual([f['shares'] for f in e['fills'] if f['code']=='B' and f['side']=='BUY'],['7']);self.assertEqual(state['remaining'],'13')
                self.assertEqual(state['status'],'CANCELLED_EVIDENCE' if s['entry']=='review' else 'EXPIRED_UNFILLED');self.assertEqual(state['reserved_cash'],'0')
                self.assertEqual(r['review_decision'],case(s['entry'])[1]['review']['review_decision'])
            if 'wrong' in s['name']:self.assertEqual(r['status'],'STOPPED_INPUT_ERROR');self.assertIsNone(e)
            rows.append(dict(case=s['name'],status=r['status'],reasons=r['reasons'],order_state=state,
                events=e['execution_events'] if e else None,actual_reference=s['original_actual']))
        save(ROOT/'test-evidence/selected-boundaries.json',rows)

    def test_preset_pure_calls_keep_input_and_context_without_IO(self):
        rows=[];blocked=AssertionError('C_OUTER_IO_FORBIDDEN')
        for name in PRIMARY:
            request,expected,spec=case(name);unchanged=deepcopy(request)
            with localcontext(context(preset())) as ctx:
                before=snapshot(ctx)
                with patch('builtins.open',side_effect=blocked),patch.object(socket.socket,'connect',side_effect=blocked),patch.object(subprocess,'Popen',side_effect=blocked):
                    value=(reassess_conditional if spec['entry']=='review' else retry_rejected)(request)
                after=snapshot(ctx)
            self.assertEqual(value,expected);self.assertEqual(request,unchanged);self.assertEqual(before,after)
            rows.append(dict(case=name,actual=stored_actual(value,spec,expected),caller_before=before,caller_after=after,input_unchanged=True))
        save(ROOT/'test-evidence/preset.json',rows)

    def test_fresh_DefaultContext_preserves_entries_and_reports_required_nested_calls(self):
        rows=[]
        for name in PRIMARY:
            p=subprocess.run([sys.executable,'-B','-c',FRESH,str(ROOT),str(PROJECT),name],cwd=PROJECT,text=True,capture_output=True)
            save(ROOT/'test-evidence/fresh'/name/'actual.json',dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
            self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(p.stderr);v=json.loads(p.stdout)
            for k in ('equal_original','input_unchanged','caller_unchanged','DefaultContext_unchanged'):self.assertTrue(v[k])
            self.assertEqual(v['calls'],load(ROOT/'after/primary'/name/'normal/actual.json')['calls']);rows.append(v)
        save(ROOT/'test-evidence/fresh/summary.json',rows)

    def test_existing_lifecycle_READ_preserves_results_without_recomputation(self):
        rows=[];blocked=AssertionError('READ_MUST_NOT_RUN_ENGINES')
        for name in PRIMARY:
            _,expected,_=case(name);value=actual_value(load(ROOT/'after/primary'/name/'normal/actual.json'));before=_fp(value)
            with patch('capital_research.execution.simulate',side_effect=blocked),patch('rotation_research.action_ledger.replay',side_effect=blocked), \
                    patch('capital_research.quantity_replay.replay_sequence',side_effect=blocked), \
                    patch('capital_research.conditional_quantity_review.reassess_conditional',side_effect=blocked), \
                    patch('capital_research.conditional_retry.retry_rejected',side_effect=blocked):
                actual=summarize_saved(value);original=summarize_saved(expected)
            self.assertEqual(actual['status'],'READABLE',actual['reasons']);self.assertEqual(actual,original);self.assertEqual(_fp(value),before)
            rows.append(dict(case=name,status=actual['status'],summary_id=_fp(actual),original_summary_id=_fp(original),input_unchanged=True,
                guard='EXISTING_READ_NO_ENGINE_REPLAY_OR_MIGRATION'))
        save(ROOT/'test-evidence/READ-compatibility.json',rows)


if __name__=='__main__':unittest.main()
