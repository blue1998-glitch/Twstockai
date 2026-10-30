"""Focused capability tests. No old suite, producer or real data."""
from copy import deepcopy
import json
from pathlib import Path
from decimal import Decimal
import unittest

from capital_research.conditional_quantity_review import reassess_conditional
from capital_research.quantity_replay import replay_sequence
from capital_research.continuity import make_checkpoint
from .verify import verify

ROOT=Path(__file__).parent


def load(name,kind):return json.loads((ROOT/('after-final' if kind=='actual' else 'cases')/name/(kind+'.json')).read_text())


class ConditionalReviewTests(unittest.TestCase):
    def check_case(self,name):
        request=load(name,'input');before=deepcopy(request);actual=reassess_conditional(request)
        verify(request,load(name,'expected'),actual);self.assertEqual(before,request)
        self.assertEqual(actual,load(name,'actual'))
        return actual['review']

    def test_valid_old_fact_same_order_and_cost(self):
        r=self.check_case('valid-old-fact');row=r['checkpoint']['state']['row']
        self.assertEqual(Decimal(row['settled_cash']),Decimal('596.5'));self.assertEqual(row['shares'],dict(A='50',B='20',C='2'))
        self.assertEqual(Decimal(row['purchase_payable']),Decimal('401.4'))
        self.assertEqual(Decimal(row['available_cash_strict']),Decimal('195.1'))
        self.assertEqual(Decimal(row['net_accrual_equity']),Decimal('1325.1'))
        old=load('valid-old-fact','input')['replay_input']['rounds'][0]['decision_template']['assets']['B']['evidence']
        self.assertEqual(old,r['review_request']['decision_input']['assets']['B']['evidence'])

    def test_partial_same_id_no_new_batch(self):
        r=self.check_case('partial-original-order');row=r['checkpoint']['state']['row']
        self.assertEqual(Decimal(row['settled_cash']),Decimal('596.5'));self.assertEqual(row['shares']['B'],'7')
        self.assertEqual(Decimal(row['purchase_payable']),Decimal('141.14'))
        self.assertEqual(Decimal(row['available_cash_strict']),Decimal('455.36'))
        self.assertEqual(Decimal(row['net_accrual_equity']),Decimal('1325.36'))

    def test_partial_then_known_revocation_preserves_fill(self):
        r=self.check_case('partial-then-known-cancel');row=r['checkpoint']['state']['row']
        self.assertEqual(row['shares'],dict(A='60',B='7',C='2'));self.assertEqual(Decimal(row['settled_cash']),Decimal('535.36'))
        self.assertEqual(row['cash_claims'],[]);self.assertEqual(row['share_receivables'],[])
        self.assertEqual(r['execution']['order_states']['r1-B']['reserved_cash'],'0')

    def test_rejected_declaration_retained(self):
        r=self.check_case('rejected-restriction-retained')
        self.assertTrue(r['execution']['reassessment_attempts'])
        declared=r['execution']['reassessment_attempts'][-1]['fact_source']
        self.assertIn('review-revocation',json.dumps(declared))

    def test_rejected_content_conflict_retained(self):
        r=self.check_case('rejected-conflict-retained')
        self.assertTrue(r['checkpoint']['state']['fact_history']['restriction_conflicts'])

    def test_unknown_qualification_refuses(self):self.check_case('unknown-current-qualification')
    def test_receivable_not_available_cash(self):self.check_case('sale-unsettled')
    def test_unknown_order_no_authorization(self):self.check_case('unknown-order-refused')
    def test_no_arbitrary_target_override(self):self.check_case('target-injection-refused')
    def test_basis_bound(self):self.check_case('basis-change-refused')
    def test_full_outer_gate_before_review(self):self.check_case('outer-gate-refused')
    def test_multiple_live_orders_explicitly_unsupported(self):self.check_case('multiple-live-orders-unsupported')
    def test_limit_up_after_valid_review_stays_unfilled(self):self.check_case('limit-up-after-review')
    def test_close_knowledge_bound(self):self.check_case('close-not-yet-known')

    def test_future_tail_isolation(self):
        control=load('valid-old-fact','actual')
        for name in ('future-A-wins','future-B-wins','future-both-fall'):
            r=self.check_case(name)
            self.assertEqual(r['numeric_result'],control['review']['numeric_result'])
            self.assertNotEqual(r['original_approval']['origin_ledger_input_id'],control['review']['original_approval']['origin_ledger_input_id'])

    def test_no_review_still_waits_and_checkpoint_is_native(self):
        request=load('valid-old-fact','input')['replay_input'];out=replay_sequence(request)['replay']
        self.assertEqual(out['status'],'COMPLETED_PROVIDED_ROUNDS')
        e=out['last_execution'];self.assertFalse(any(f['code']=='B' for f in e['fills']))
        self.assertTrue(e['order_states']['r1-B']['requires_reassessment'])
        saved=load('valid-old-fact','actual')['review']
        cp=make_checkpoint(request['origin_ledger'],saved['execution'],through_at=request['rounds'][-1]['observed_until'])
        self.assertEqual(cp['state'],saved['checkpoint']['state'])


if __name__=='__main__':unittest.main()
