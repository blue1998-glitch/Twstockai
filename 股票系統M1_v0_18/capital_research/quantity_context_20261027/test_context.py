"""Bounded wrapper determinism and the directly affected account/trigger gates."""
from copy import deepcopy
from decimal import Decimal,localcontext
import json
import subprocess
import sys
import unittest
from unittest.mock import patch
from capital_research.quantity_replay import replay_sequence
from capital_research.lifecycle import _fp,FLAGS
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .prepare import ROOT,PROJECT,load,save,info
from .reproduce import probe,save_object

FRESH=r'''
import os,sys,json,decimal
from pathlib import Path
def audit(event,args):
 if event=='open':
  m,f=args[1:3]
  if (m and any(c in m for c in 'wax+')) or f&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('WRITE_FORBIDDEN')
 if event in ('os.mkdir','os.remove','os.rename','subprocess.Popen','socket.connect','socket.getaddrinfo'):raise RuntimeError('SIDE_EFFECT:'+event)
sys.addaudithook(audit)
from capital_research.quantity_replay import replay_sequence
from capital_research.lifecycle import _fp
root=Path(sys.argv[1]);request=json.loads((root/'cases/complete/input.json').read_text())
normal=json.loads((root/'before/normal/actual.json').read_text())['actual']['id']
for c in (decimal.DefaultContext,decimal.getcontext()):
 c.prec=5;c.rounding=decimal.ROUND_UP;c.Emin=-2;c.Emax=2;c.capitals=0;c.clamp=1
 for signal in c.traps:c.traps[signal]=True
 c.flags[decimal.Inexact]=True;c.flags[decimal.Rounded]=True
before=repr(decimal.getcontext());default_before=repr(decimal.DefaultContext);request_id=_fp(request)
counts={'replay':0,'execution':0,'evaluation':0,'save':0}
def profile(frame,event,arg):
 if event!='call':return
 p=frame.f_code.co_filename;n=frame.f_code.co_name
 if p.endswith('/quantity_replay.py') and n=='replay_sequence':counts['replay']+=1
 if p.endswith('/execution.py') and n=='simulate':counts['execution']+=1
 if p.endswith('/account_metrics.py') and n=='evaluate_saved':counts['evaluation']+=1
 if p.endswith('/rotation_research/store.py') and n=='save':counts['save']+=1
sys.setprofile(profile);result=replay_sequence(request);sys.setprofile(None)
assert _fp(result)==normal,'RAW_NORMAL_RESULT_CHANGED'
assert _fp(request)==request_id and repr(decimal.getcontext())==before and repr(decimal.DefaultContext)==default_before,'CALLER_OR_INPUT_CHANGED'
print(json.dumps(dict(actual_id=_fp(result),caller_unchanged=True,DefaultContext_unchanged=True,input_unchanged=True,calls=counts,
 guard='FRESH_EXPLICIT_SYNTHETIC_REPLAY_NO_WRITE_NO_NETWORK')))
'''


def stored(stage,name):
    record=load(ROOT/stage/name/'actual.json')
    result=load(ROOT/record['actual']['path']) if record['actual'] else None
    if result is not None:assert _fp(result)==record['actual']['id']
    return record,result


class QuantityContextTests(unittest.TestCase):
    def test_frozen_before_after_results_match_expected_failures_and_controls(self):
        _,normal=stored('before','normal')
        self.assertTrue(load(ROOT/'before/summary.json')[0]['equal_before_normal'])
        for name in ('normal','round-down'):self.assertEqual(stored('before',name)[1],normal)
        self.assertNotEqual(stored('before','round-up')[1],normal)
        self.assertEqual(stored('before','inexact-trap')[0]['error']['type'],'Inexact')
        self.assertEqual(stored('before','narrow-exponents')[0]['error']['type'],'Overflow')
        for item in load(ROOT/'contexts.json'):
            record,result=stored('after',item['name']);self.assertIsNone(record['error']);self.assertEqual(result,normal)
            self.assertTrue(record['caller_context_unchanged']);self.assertTrue(record['input_unchanged'])
            self.assertEqual(record['source_version'],info(ROOT.parent/'quantity_replay.py'))

    def test_every_round_preserves_original_account_fills_rights_reserve_latest_and_all_tokens(self):
        _,wrapper=stored('after','normal');r=wrapper['replay'];expected=load(ROOT/'cases/complete/expected.json')
        self.assertEqual(r['status'],expected['status']);self.assertEqual(r['execution_calls'],2)
        first,last=[f['execution'] for f in r['rounds']];a,b=[f['checkpoint']['state'] for f in r['rounds']]
        self.assertEqual(first['ledger']['daily'][0]['cash_receivable'],'80')
        self.assertEqual(first['ledger']['daily'][0]['share_receivables'][0]['shares'],'10')
        self.assertEqual(a['row']['shares'],expected['first_shares']);self.assertEqual(Decimal(a['row']['settled_cash']),Decimal(expected['first_cash']))
        self.assertEqual(b['row']['shares'],expected['final_shares']);self.assertEqual(Decimal(b['row']['settled_cash']),Decimal(expected['final_cash']))
        self.assertEqual(Decimal(b['row']['net_accrual_equity']),Decimal(expected['final_nav']))
        self.assertEqual(len(last['fills']),3);self.assertEqual(last['fills'][:len(first['fills'])],first['fills'])
        self.assertEqual(last['order_history'][:len(first['order_history'])],first['order_history'])
        self.assertEqual(len({f['id'] for f in last['fills']}),3)
        for execution,state in [(first,a),(last,b)]:
            self.assertEqual(state['origin_initial_capital'],'2230');self.assertEqual(state['general_reserved_cash'],'100')
            self.assertEqual(state['row'],execution['ledger']['daily'][-1]);self.assertEqual(state['accepted_fills'],execution['fills'])
            for key in ('latest_decision_id','latest_common_account_id','reviewed_evidence_tokens','order_states'):
                self.assertEqual(state[key],execution[key])
            for k in FLAGS:self.assertIs(execution[k],False)
        self.assertTrue(set(a['reviewed_evidence_tokens'])<=set(b['reviewed_evidence_tokens']))
        self.assertEqual(first['origin_ledger_input_id'],last['origin_ledger_input_id'])
        self.assertEqual(first['origin_common_account_id'],last['origin_common_account_id'])
        self.assertEqual(b['row']['cash_claims'],[]);self.assertEqual(b['row']['share_receivables'],[])
        journal=last['ledger']['journal']
        self.assertEqual(len([j for j in journal if j['type']=='CASH_RECEIVED' and j.get('claim_id')=='opening-cash']),1)
        self.assertEqual(len([j for j in journal if j['type']=='SHARES_TRADABLE' and j.get('event_id')=='opening-shares']),1)
        for entry in load(ROOT/'intake.json')['originals']:self.assertEqual(info(PROJECT/entry['path']),entry)
        old=load(ROOT/'intake.json')['source_before'];self.assertEqual(info(ROOT/'before/source/quantity_replay.py')['sha256'],old['sha256'])
        save(ROOT/'test-evidence/account-chain.json',dict(first_state=a,final_state=b,
            fill_ids=[f['id'] for f in last['fills']],cash_right_credited_once=True,share_right_credited_once=True,
            comparison_scope='COMPLETE_RAW_OUTPUT_EQUALITY_AND_EACH_SAVED_ROUND_NOT_JUST_TERMINAL_NAV'))

    def test_hostile_caller_flags_are_unchanged_and_entry_needs_no_file_IO(self):
        data=load(ROOT/'cases/complete/input.json');before_data=deepcopy(data);spec=load(ROOT/'test-controls.json')['preset']
        with localcontext(context(spec)) as ctx:
            before=snapshot(ctx)
            with patch('builtins.open',side_effect=AssertionError('PURE_REPLAY_FILE_IO')):result=replay_sequence(data)
            after=snapshot(ctx)
        self.assertEqual(result,stored('before','normal')[1]);self.assertEqual(before,after);self.assertEqual(data,before_data)
        save(ROOT/'test-evidence/caller-state.json',dict(actual=save_object(result),caller_before=before,caller_after=after,input_unchanged=True))

    def test_reused_trigger_remains_rejected_and_preserves_stopped_prefix_rights(self):
        data=load(ROOT/'cases/old-trigger/input.json');expected=load(ROOT/'cases/old-trigger/expected.json')
        normal=load(ROOT/'contexts.json')[0]['context'];hostile=load(ROOT/'test-controls.json')['preset'];rows=[]
        for name,spec in [('normal',normal),('hostile',hostile)]:
            result,record=probe(data,spec);self.assertIsNone(record['error']);r=result['replay']
            self.assertEqual(r['status'],expected['status']);self.assertIn(expected['reason'],r['reasons'])
            self.assertEqual(r['execution_calls'],1);self.assertEqual(len(r['last_execution']['fills']),2)
            s=r['historical_checkpoint']['state'];self.assertEqual(s['origin_initial_capital'],'2230')
            self.assertEqual(s['row']['shares'],dict(A='80',B='7',C='2'));self.assertEqual(s['row']['cash_receivable'],'80')
            self.assertEqual(s['row']['share_receivables'][0]['shares'],'10');self.assertEqual(s['general_reserved_cash'],'100')
            self.assertTrue(r['rounds'][1]['selected_candidate']['reasons']);self.assertTrue(r['checkpoint_resume_api'].startswith('NOT_IMPLEMENTED'))
            self.assertTrue(record['input_unchanged']);self.assertTrue(record['caller_context_unchanged'])
            record['actual']=save_object(result);save(ROOT/'test-evidence/old-trigger'/name/'actual.json',record);rows.append(result)
            for k in FLAGS:self.assertIs(r[k],False)
            self.assertIsNone(r['ranking']);self.assertIsNone(r['selected_strategy']);self.assertIsNone(r['primary_pressure_id'])
        self.assertEqual(rows[0],rows[1])

    def test_fresh_process_DefaultContext_cannot_change_result_or_write_files(self):
        p=subprocess.run([sys.executable,'-B','-c',FRESH,str(ROOT)],cwd=PROJECT,text=True,capture_output=True)
        save(ROOT/'test-evidence/fresh-process.json',dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
        self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(p.stderr);r=json.loads(p.stdout)
        self.assertEqual(r['actual_id'],load(ROOT/'before/normal/actual.json')['actual']['id'])
        self.assertEqual(r['calls'],dict(replay=1,execution=2,evaluation=0,save=0))
        self.assertTrue(r['caller_unchanged']);self.assertTrue(r['DefaultContext_unchanged']);self.assertTrue(r['input_unchanged'])


if __name__=='__main__':unittest.main()
