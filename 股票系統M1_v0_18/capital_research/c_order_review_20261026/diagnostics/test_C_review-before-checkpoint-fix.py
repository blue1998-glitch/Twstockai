"""Focused C continuation boundaries and direct legacy regression only."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
import unittest

from capital_research.conditional_quantity_review import reassess_conditional
from capital_research.core import fingerprint
from capital_research.continuity import make_checkpoint
from capital_research.lifecycle import summarize_saved
from capital_research.lifecycle_compare import compare_saved,INPUT
from capital_research.order_review import validate_saved
from .directed import gateway_inputs,edit_gateway,resume,materialize_next

ROOT=Path(__file__).parent
CAPITAL=ROOT.parent


def load(path):return json.loads(path.read_text())


class COrderTests(unittest.TestCase):
    def result(self,name):return load(ROOT/'after-final'/name/'actual.json')['review']

    def test_valid_original_C_order_has_no_new_trigger_or_quantity(self):
        r=self.result('valid-C-same-order');d=r['review_decision'];s=d['same_order_continuation']
        self.assertEqual(d['new_evidence_tokens'],[])
        self.assertEqual(s['trigger_ids'],['B-event']);self.assertEqual(s['remaining'],'20')
        self.assertEqual(r['execution']['order_history'],r['prefix_execution']['order_history'])
        self.assertEqual(r['checkpoint']['state']['row']['shares'],dict(A='50',B='25',C='2'))
        self.assertEqual(Decimal(r['checkpoint']['state']['row']['purchase_payable']),Decimal('401.4'))
        self.assertEqual(Decimal(r['checkpoint']['state']['row']['net_accrual_equity']),Decimal('1425.1'))

    def test_partial_and_limit_up_keep_original_order(self):
        p=self.result('partial-C-same-order');st=p['execution']['order_states']['r1-B']
        self.assertEqual(st['remaining'],'13');self.assertEqual(st['reserved_cash'],'261.65039')
        self.assertEqual(Decimal(p['checkpoint']['state']['row']['purchase_payable']),Decimal('141.14'))
        u=self.result('valid-review-but-limit-up');self.assertEqual(u['execution']['order_states']['r1-B']['remaining'],'20')

    def test_invalid_unknown_conflict_risk_cost_and_funding_still_reject(self):
        for name in ('revoked-trigger','unknown-current-eligibility','rejected-conflict-retained','current-risk-limit','current-cost-band','sale-still-unsettled'):
            with self.subTest(name=name):
                r=self.result(name);self.assertEqual(r['status'],'REPLAYED_REJECTED_REVIEW')
                self.assertEqual(r['execution']['reassessment_attempts'][-1]['outcome'],'REJECTED')
                self.assertFalse(any(f['code']=='B' for f in r['execution']['fills']))
        self.assertTrue(self.result('rejected-conflict-retained')['checkpoint']['state']['fact_history']['restriction_conflicts'])

    def test_all_gateway_edits_fail_before_permission(self):
        rows=load(ROOT/'gateway/summary.json');self.assertEqual(len(rows),7)
        self.assertTrue(all(x['status']=='PASS' for x in rows),rows)

    def test_raw_input_flag_cannot_create_scope_permission(self):
        base=gateway_inputs(load(ROOT/'after-final/valid-C-same-order/actual.json'))
        base.pop('same_order_id');base['decision_input']['same_order_continuation']=deepcopy(self.result('valid-C-same-order')['review_decision']['same_order_continuation'])
        r=resume(base)['decision'];p=next(p for p in r['layer3']['alternatives'] if p['family']=='C')
        self.assertIn('NO_NEW_INDEPENDENT_TRIGGER',p['reasons']);self.assertEqual(r['schema'],'capital-decision/0.8')

    def test_new_batch_old_trigger_rejects_new_independent_trigger_qualifies(self):
        old=load(ROOT/'new-batch/old-trigger-actual.json')['decision'];new=load(ROOT/'new-batch/new-trigger-actual.json')['decision']
        p=next(p for p in old['layer3']['alternatives'] if p['id']=='next-C-batch')
        self.assertIn('NO_NEW_INDEPENDENT_TRIGGER',p['reasons'])
        p=next(p for p in new['layer3']['alternatives'] if p['id']=='next-C-batch');self.assertTrue(p['feasible'],p['reasons'])
        self.assertEqual(p['family'],'C');self.assertEqual(p['targets']['B'],'26')
        self.assertEqual(new['continuity']['origin_initial_capital'],'1430')
        self.assertNotIn('same_order_continuation',new)
        self.assertTrue(any('B-independent-next' in t for t in new['new_evidence_tokens']))

    def test_future_revocation_prefix_and_later_cancellation(self):
        a=self.result('valid-C-same-order');b=self.result('future-revocation-prefix')
        self.assertEqual(a['numeric_result'],b['numeric_result']);self.assertNotEqual(a['execution']['result_id'],b['execution']['result_id'])
        late=self.result('future-revocation-known-after-partial');st=late['execution']['order_states']['r1-B']
        self.assertEqual(st['status'],'CANCELLED_EVIDENCE');self.assertEqual(st['remaining'],'13');self.assertEqual(st['reserved_cash'],'0')
        self.assertEqual(late['checkpoint']['state']['row']['shares'],dict(A='60',B='12',C='2'))

    def test_scope_tamper_or_version_downgrade_is_rejected(self):
        r=self.result('valid-C-same-order');d=deepcopy(r['review_decision'])
        d['same_order_continuation']['remaining']='21'
        s=d['same_order_continuation'];s['scope_id']=fingerprint({k:v for k,v in s.items() if k!='scope_id'})
        with self.assertRaisesRegex(ValueError,'SAME_ORDER_SCOPE_QUANTITY_CONFLICT'):validate_saved(d,r['execution'])
        d=deepcopy(r['review_decision']);d['schema']='capital-decision/0.8'
        with self.assertRaisesRegex(ValueError,'VERSION_0_9'):validate_saved(d,r['execution'])
        d=deepcopy(r['review_decision']);d.pop('same_order_continuation')
        with self.assertRaisesRegex(ValueError,'SAME_ORDER_SCOPE_REQUIRED'):validate_saved(d,r['execution'])

    def test_ledger_checkpoint_and_READ_preserve_rights_latest_tokens(self):
        saved=load(ROOT/'after-final/valid-C-same-order/actual.json');r=saved['review'];summary=summarize_saved(saved)
        self.assertEqual(summary['status'],'READABLE',summary['reasons'])
        cp=make_checkpoint(r['execution_job']['ledger_input'],r['execution'],through_at=r['execution']['observed_until'])
        self.assertEqual(cp['state'],r['checkpoint']['state'])
        self.assertEqual(summary['account']['reviewed_evidence_tokens'],r['execution']['reviewed_evidence_tokens'])
        self.assertEqual(summary['account']['saved_row'],cp['state']['row'])
        self.assertIn('same_order_continuation',next(o for o in summary['orders'] if o['order_id']=='r1-B')['reviews'][0])
        comparison=compare_saved(dict(schema=INPUT,synthetic=True,items=[dict(label='一',saved_result=saved),dict(label='二',saved_result=deepcopy(saved))]))
        self.assertEqual(comparison['status'],'COMPARABLE',comparison['refusals'])

    def test_legacy_E_path_exactly_matches_saved_0_8_result(self):
        request=load(CAPITAL/'conditional_quantity_review_20261026/cases/valid-old-fact/input.json')
        expected=load(CAPITAL/'conditional_quantity_review_20261026/after-final/valid-old-fact/actual.json')
        before=deepcopy(request);actual=reassess_conditional(request)
        self.assertEqual(actual,expected);self.assertEqual(request,before)
        old_summary=load(CAPITAL/'lifecycle_20261026/after-final/full-pending/actual.json')
        self.assertEqual(summarize_saved(expected),old_summary)

    def test_old_C_wrapper_stays_unsupported_and_unscoped_resume_unchanged(self):
        self.assertEqual(self.result('old-wrapper-keeps-C-unsupported')['status'],'STOPPED_NOT_IMPLEMENTED')
        old=load(ROOT/'before/raw-resume-input.json')
        current=resume(old);self.assertEqual(current,load(ROOT/'before/raw-resume-actual.json'))

    def test_public_adapter_is_pure_for_C_request(self):
        x=load(ROOT/'cases/valid-C-same-order/input.json');before=deepcopy(x)
        self.assertEqual(reassess_conditional(x),load(ROOT/'after-final/valid-C-same-order/actual.json'))
        self.assertEqual(x,before)

    def test_new_version_READ_does_not_import_engines_or_write(self):
        script=r'''
import sys,os,runpy,importlib.abc
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith(('graph_core','rotation_research')) or (fullname.startswith('capital_research.') and fullname not in ('capital_research.lifecycle','capital_research.lifecycle_read')):raise RuntimeError('ENGINE_IMPORT:'+fullname)
sys.meta_path.insert(0,Guard())
def audit(event,args):
 if event=='open':
  mode=args[1];flags=args[2]
  if (mode is not None and any(x in mode for x in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('READ_WRITE')
 if event in ('os.remove','os.rename','os.mkdir','subprocess.Popen','socket.connect'):raise RuntimeError('READ_SIDE_EFFECT')
sys.addaudithook(audit)
sys.argv=['capital_research.lifecycle_read',sys.argv[1],'--format','json']
runpy.run_module('capital_research.lifecycle_read',run_name='__main__')
'''
        source=(ROOT/'after-final/valid-C-same-order/actual.json').resolve()
        result=subprocess.run([sys.executable,'-B','-c',script,str(source)],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['summary']['status'],'READABLE')


if __name__=='__main__':unittest.main()
