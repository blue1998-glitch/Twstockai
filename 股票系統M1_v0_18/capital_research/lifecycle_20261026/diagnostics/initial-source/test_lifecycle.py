"""Necessary read-only acceptance; no saved producer or engine run."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from capital_research.lifecycle import summarize_saved, render_text
from .fixtures import ROOT, load
from .verify import verify


def actual(name):return json.loads((ROOT/'initial'/name/'actual.json').read_text())


class LifecycleTests(unittest.TestCase):
    def case(self,name):
        saved=load(name);original=deepcopy(saved);result=summarize_saved(saved)
        verify(json.loads((ROOT/'cases'/name/'expected.json').read_text()),result)
        self.assertEqual(saved,original);self.assertEqual(result,actual(name))
        self.assertTrue(all(result[k] is False for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized')))
        return result

    def test_partial_pending_keeps_cash_rights_and_reservation(self):
        r=self.case('partial-pending');source=load('partial-pending')['review']
        self.assertEqual(r['account']['saved_row'],source['checkpoint']['state']['row'])
        self.assertEqual(r['account']['reviewed_evidence_tokens'],source['execution']['reviewed_evidence_tokens'])
        self.assertEqual(r['account']['general_reserved_cash'],'100')
        self.assertEqual(r['account']['saved_row']['cash_claims'][0]['amount'],'80')
        self.assertEqual(r['account']['saved_row']['share_receivables'][0]['shares'],'10')
        b=next(o for o in r['orders'] if o['order_id']=='r1-B')
        self.assertEqual(b['approved_order_quantity'],'20')
        self.assertIsNone(b['fills'][0]['settlement']['pending_amount'])
        self.assertEqual(b['fills'][0]['record'],source['execution']['fills'][1])

    def test_settled_cancelled_is_not_still_live(self):
        r=self.case('settled-cancelled');b=next(o for o in r['orders'] if o['order_id']=='r1-B')
        self.assertEqual(b['settled_fill_quantity'],'7')
        self.assertEqual(b['fills'][0]['settlement']['records'][0]['record']['amount'],'141.140')
        self.assertEqual(r['account']['saved_row']['cash_claims'],[])
        self.assertEqual(r['account']['saved_row']['share_receivables'],[])
        self.assertEqual(len(r['snapshots']),2)
        self.assertNotEqual(r['snapshots'][0]['latest_decision_id'],r['snapshots'][1]['latest_decision_id'])

    def test_waiting_full_and_limit_up_are_distinct(self):
        for name in ('waiting','full-pending','limit-up'):
            with self.subTest(name=name):self.case(name)

    def test_rejected_review_keeps_reason_and_conflicts(self):
        r=self.case('rejected-conflict');b=next(o for o in r['orders'] if o['order_id']=='r1-B')
        self.assertEqual(len(b['reviews']),1)
        self.assertIn('NEW_CAPITAL_NOT_QUALIFIED:B',b['reviews'][0]['reasons'])
        self.assertTrue(b['reviews'][0]['restriction_conflicts'])
        self.assertEqual(b['reviews'][0]['observed_at'],'2026-01-09T09:01:00+08:00')
        self.assertEqual(b['reviews'][0]['decision_at'],'2026-01-08T17:00:00+08:00')

    def test_expiry_and_new_batch_do_not_merge(self):
        r=self.case('expired-and-new-batch')
        self.assertEqual(len(r['approvals']),2)
        self.assertEqual(r['approvals'][0]['shared_order_ids'],['r1-A','r1-B'])
        self.assertEqual(sum(int(o['filled_quantity']) for o in r['orders'] if o['side']=='BUY'),8)
        self.assertEqual(len({f['record']['id'] for o in r['orders'] for f in o['fills']}),3)

    def test_cancel_then_new_order_is_distinct(self):self.case('cancel-and-new-batch')

    def test_stopped_round_is_historical_not_new_approval(self):
        r=self.case('stopped-historical');self.assertEqual(len(r['approvals']),1)
        r=self.case('no-execution');self.assertIsNone(r['account']);self.assertEqual(r['orders'],[])

    def test_missing_or_inconsistent_data_never_zero_filled(self):
        for name in ('unknown-schema','corrupt-execution','missing-payable','quantity-conflict'):
            with self.subTest(name=name):self.case(name)

    def test_date_alone_does_not_prove_settlement(self):
        r=self.case('missing-settlement-proof');b=next(o for o in r['orders'] if o['order_id']=='r1-B')
        self.assertEqual(b['settled_fill_quantity'],'0')
        self.assertEqual(b['fills'][0]['settlement']['status'],'UNKNOWN_MISSING_SETTLEMENT_PROOF')
        self.assertEqual(r['account']['saved_row']['purchase_payable'],'141.140')

    def test_saved_future_branches_do_not_reinterpret_current_orders(self):
        for name in ('future-A-wins','future-B-wins','future-both-fall'):
            with self.subTest(name=name):self.assertEqual(self.case(name)['orders'],actual('full-pending')['orders'])

    def test_readable_text_keeps_unknown_and_account_scope(self):
        text=render_text(actual('partial-pending'))
        self.assertEqual(text,(ROOT/'initial/partial-pending/readable.txt').read_text())
        self.assertIn('20 | 7 | 13 | 0 | 0 | 7 | 0 | 261.65039',text)
        self.assertEqual(text.count('全帳已結現金'),1)
        self.assertIn('UNKNOWN_MISSING_SETTLEMENT_PROOF',json.dumps(actual('missing-settlement-proof')))

    def test_fresh_read_and_cli_cannot_import_engines_or_write(self):
        # Fresh process: an already-imported producer cannot hide an accidental dependency.
        source=ROOT.parents[0]/'conditional_quantity_review_20261026/after-final/partial-original-order/actual.json'
        before=hashlib.sha256(source.read_bytes()).hexdigest()
        script=r'''
import sys,os,importlib.abc,runpy
class NoEngine(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith(('graph_core','rotation_research')) or (fullname.startswith('capital_research.') and fullname not in ('capital_research.lifecycle','capital_research.lifecycle_read')):
   raise RuntimeError('READ_IMPORTED_ENGINE:'+fullname)
sys.meta_path.insert(0,NoEngine())
def audit(event,args):
 if event=='open':
  mode=args[1];flags=args[2]
  if (mode is not None and any(x in mode for x in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('READ_ATTEMPTED_WRITE')
 if event in ('os.remove','os.rename','os.mkdir','subprocess.Popen','socket.connect'):raise RuntimeError('READ_SIDE_EFFECT:'+event)
sys.addaudithook(audit)
sys.argv=['capital_research.lifecycle_read',sys.argv[1],'--format','json']
runpy.run_module('capital_research.lifecycle_read',run_name='__main__')
'''
        run=subprocess.run([sys.executable,'-B','-c',script,str(source)],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)['summary'],actual('partial-pending'))
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)


if __name__=='__main__':unittest.main()
