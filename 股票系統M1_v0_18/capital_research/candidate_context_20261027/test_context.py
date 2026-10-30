"""Only independent candidate entry stability and directly affected gates."""
from copy import deepcopy
from decimal import localcontext
import json
import subprocess
import sys
import unittest
from unittest.mock import patch
from capital_research.quantity_candidates import generate
from capital_research.lifecycle import FLAGS,_fp
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .prepare import ROOT,PROJECT,load,save,info
from .reproduce import case,controls,preset,probe,actual_value,stored_actual

FRESH=r'''
import os,sys,json,decimal
from pathlib import Path
def audit(event,args):
 if event=='open':
  m,f=args[1:3]
  if (m and any(c in m for c in 'wax+')) or f&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('WRITE_FORBIDDEN')
 if event in ('os.mkdir','os.remove','os.rename','subprocess.Popen','socket.connect','socket.getaddrinfo'):raise RuntimeError('SIDE_EFFECT:'+event)
sys.addaudithook(audit)
from capital_research.quantity_candidates import generate
from capital_research.lifecycle import _fp
root=Path(sys.argv[1]);project=Path(sys.argv[2]);spec=json.loads((root/'input.json').read_text())['cases'][0]
source=json.loads((project/spec['source']['path']).read_text());f=source['replay']['rounds'][spec['round_index']]
data=f['quantity_request'];expected=f['generation'];request_id=_fp(data)
for c in (decimal.DefaultContext,decimal.getcontext()):
 c.prec=5;c.rounding=decimal.ROUND_UP;c.Emin=-2;c.Emax=2;c.capitals=0;c.clamp=1
 for signal in c.traps:c.traps[signal]=True
 c.flags[decimal.Inexact]=True;c.flags[decimal.Rounded]=True
before=repr(decimal.getcontext());default_before=repr(decimal.DefaultContext)
counts={'generate':0,'simulate':0,'replay_sequence':0,'save':0}
def profile(frame,event,arg):
 if event!='call':return
 p=frame.f_code.co_filename;n=frame.f_code.co_name
 if p.endswith('/quantity_candidates.py') and n=='generate':counts['generate']+=1
 if p.endswith('/execution.py') and n=='simulate':counts['simulate']+=1
 if p.endswith('/quantity_replay.py') and n=='replay_sequence':counts['replay_sequence']+=1
 if p.endswith('/rotation_research/store.py') and n=='save':counts['save']+=1
sys.setprofile(profile);actual=generate(data);sys.setprofile(None)
assert actual==expected and _fp(actual)==spec['expected_generation_id'],'EXPECTED_GENERATION_CHANGED'
assert _fp(data)==request_id and repr(decimal.getcontext())==before and repr(decimal.DefaultContext)==default_before,'CALLER_OR_INPUT_CHANGED'
print(json.dumps(dict(actual_id=_fp(actual),equal_saved_generation=True,calls=counts,caller_unchanged=True,input_unchanged=True,
 DefaultContext_unchanged=True,guard='FRESH_DIRECT_GENERATE_NO_SIMULATE_NO_REPLAY_SEQUENCE_NO_SAVE_NO_WRITE_NO_NETWORK')))
'''


class CandidateContextTests(unittest.TestCase):
    def test_frozen_before_after_results_separate_actual_failures_from_matching_controls(self):
        for name in ('initial','old-trigger'):
            _,expected,_=case(name)
            for c in controls():
                before=load(ROOT/'before'/name/c['name']/'actual.json');after=load(ROOT/'after'/name/c['name']/'actual.json')
                if c['name']=='narrow-exponents':
                    self.assertEqual(before['error']['type'],'Overflow');self.assertIsNone(before['actual'])
                else:
                    self.assertIsNone(before['error']);self.assertEqual(actual_value(before),expected)
                self.assertIsNone(after['error']);self.assertEqual(actual_value(after),expected)
                self.assertEqual(after['source_version'],info(ROOT.parent/'quantity_candidates.py'))
                self.assertTrue(after['input_unchanged']);self.assertTrue(after['caller_context_unchanged'])

    def test_initial_and_checkpoint_candidates_preserve_accounts_rights_tokens_WAIT_and_rejections(self):
        summary=[];oracle=load(ROOT/'expected.json')
        for name in ('initial','old-trigger'):
            data,expected,_=case(name);record=load(ROOT/'after'/name/'normal/actual.json');result=actual_value(record)['research']
            account=data['decision_input']['account'];baseline=result['baseline']
            self.assertEqual(result['schema'],oracle['original_schema']);self.assertEqual(result['status'],'COMPLETE')
            self.assertEqual(result['common_account_id'],_fp(account));self.assertEqual(result['batch_context'],data['batch_context'])
            # This field is current decision NAV; the checkpoint retains origin capital.
            self.assertEqual(result['initial_capital'],expected['research']['initial_capital'])
            self.assertEqual(baseline['reserved_cash'],'100')
            for c in result['candidates']:
                self.assertEqual(c['plan']['targets']['C'],'2')
                if name=='old-trigger' and int(c['additional_B'])>0:
                    self.assertEqual(c['classification'],'REJECTED');self.assertFalse(c['feasible_for_research'])
                    self.assertIn('NO_NEW_INDEPENDENT_TRIGGER',c['reasons'])
            if name=='initial':
                self.assertEqual(result['initial_capital'],oracle['original_initial_capital'])
                self.assertEqual([c['plan']['targets'] for c in result['candidates']],oracle['initial_targets'])
                self.assertEqual([c['classification'] for c in result['candidates']],oracle['initial_classifications'])
                self.assertEqual(account['cash_claims'][0]['amount'],'80');self.assertEqual(account['share_claims'][0]['shares'],'10')
            else:
                cp=data['continuation']['checkpoint'];s=cp['state']
                self.assertEqual(account['holdings']['B']['shares'],'7');self.assertEqual(account['settled_cash'],'1056.660')
                self.assertEqual(baseline['continuity']['checkpoint_id'],cp['checkpoint_id'])
                self.assertEqual(baseline['continuity']['latest_predecessor_id'],s['latest_decision_id'])
                self.assertTrue(set(s['reviewed_evidence_tokens'])<=set(baseline['reviewed_evidence_tokens']))
                self.assertEqual(s['general_reserved_cash'],'100')
                self.assertEqual(s['origin_initial_capital'],oracle['original_initial_capital'])
                self.assertEqual(baseline['continuity']['origin_initial_capital'],s['origin_initial_capital'])
            for k in FLAGS:self.assertIs(result[k],False)
            self.assertIsNone(result['ranking']);self.assertIsNone(result['selected_id']);self.assertIsNone(result['primary_pressure_id'])
            self.assertFalse(result['account_liquidation_claimed']);self.assertEqual(result['order_generation'],'NOT_PERFORMED')
            self.assertEqual(result['execution'],'NOT_PERFORMED')
            summary.append(dict(case=name,request_id=_fp(data),expected_generation_id=_fp(expected),
                account_id=result['common_account_id'],current_account_value=result['initial_capital'],
                batch_context=result['batch_context'],original_account=account,
                baseline_reserved_cash=baseline['reserved_cash'],baseline_tokens=baseline['reviewed_evidence_tokens'],
                baseline_continuity=baseline.get('continuity'),candidates=[{k:c[k] for k in ('id','kinds','classification','reasons','additional_B')} for c in result['candidates']]))
        for entry in load(ROOT/'intake.json')['originals']:self.assertEqual(info(PROJECT/entry['path']),entry)
        old=load(ROOT/'intake.json')['source_before'];self.assertEqual(info(ROOT/'before/source/quantity_candidates.py')['sha256'],old['sha256'])
        save(ROOT/'test-evidence/candidates-and-binding.json',summary)

    def test_preset_flags_traps_and_input_unchanged_without_file_IO(self):
        data,expected,spec=case('initial');unchanged=deepcopy(data)
        with localcontext(context(preset())) as ctx:
            before=snapshot(ctx)
            with patch('builtins.open',side_effect=AssertionError('PURE_GENERATE_IO')):value=generate(data)
            after=snapshot(ctx)
        self.assertEqual(value,expected);self.assertEqual(before,after);self.assertEqual(data,unchanged)
        save(ROOT/'test-evidence/preset-state.json',dict(actual=stored_actual(value,spec,expected),
            caller_before=before,caller_after=after,input_unchanged=True))

    def test_search_limit_still_refuses_and_never_promotes_candidates(self):
        spec=load(ROOT/'search-limit-spec.json');data,_,_=case(spec['source_case']);data.update(spec['only_change']);before=_fp(data)
        value,trace=probe(data,preset());self.assertIsNone(trace['error']);r=value['research']
        self.assertEqual(r['status'],spec['expected_status']);self.assertEqual(r['candidates'],[])
        self.assertEqual(r['enumeration_complete'],spec['enumeration_complete']);self.assertIn(spec['expected_reason'],r['reasons'])
        self.assertIsNone(r['baseline']);self.assertIsNone(r['selected_id']);self.assertIsNone(r['ranking'])
        for k in FLAGS:self.assertIs(r[k],False)
        self.assertEqual(_fp(data),before);self.assertTrue(trace['caller_context_unchanged'])
        save(ROOT/'test-evidence/search-limit.json',dict(actual=value,trace=trace))

    def test_fresh_process_DefaultContext_has_no_effect_or_side_effects(self):
        p=subprocess.run([sys.executable,'-B','-c',FRESH,str(ROOT),str(PROJECT)],cwd=PROJECT,text=True,capture_output=True)
        save(ROOT/'test-evidence/fresh-process.json',dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
        self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(p.stderr);r=json.loads(p.stdout)
        self.assertTrue(r['equal_saved_generation']);self.assertTrue(r['caller_unchanged']);self.assertTrue(r['DefaultContext_unchanged'])
        self.assertEqual(r['calls'],dict(generate=1,simulate=0,replay_sequence=0,save=0))


if __name__=='__main__':unittest.main()
