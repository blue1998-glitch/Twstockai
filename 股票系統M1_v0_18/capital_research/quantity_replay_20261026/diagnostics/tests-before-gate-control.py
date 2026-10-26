"""Focused integration checks reuse saved actuals; no old-suite reruns."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from capital_research.quantity_replay import replay_sequence

HERE=Path(__file__).parent


def saved(name,kind='actual'):
    return json.loads((HERE/('after-final' if kind=='actual' else 'cases')/name/(kind+'.json')).read_text())


class BridgeTests(unittest.TestCase):
    def test_partial_fills_then_independent_round_preserves_original_capital(self):
        r=saved('partial-then-independent')['replay'];first,second=r['rounds']
        a=first['execution']['ledger']['daily'][-1];b=second['execution']['ledger']['daily'][-1]
        self.assertEqual(a['shares'],dict(A='80',B='7',C='2'));self.assertEqual(Decimal(a['settled_cash']),Decimal('1056.66'))
        self.assertEqual(Decimal(a['net_accrual_equity']),Decimal('2226.66'))
        self.assertEqual(b['shares'],dict(A='90',B='8',C='2'));self.assertEqual(Decimal(b['settled_cash']),Decimal('1115.64'))
        self.assertEqual(Decimal(b['net_accrual_equity']),Decimal('2225.64'))
        self.assertEqual(Decimal(r['historical_checkpoint']['state']['origin_initial_capital']),Decimal('2230'))
        self.assertEqual(b['cash_claims'],[]);self.assertEqual(b['share_receivables'],[])

    def test_settled_money_does_not_release_conditional_buy(self):
        r=saved('settled-not-reapproved')['replay'];e=r['last_execution'];row=e['ledger']['daily'][-1]
        self.assertEqual(Decimal(row['settled_cash']),Decimal('596.5'));self.assertEqual(row['shares']['B'],'0')
        self.assertEqual(e['order_states']['r1-B']['status'],'WAITING_REASSESSMENT')
        self.assertTrue(e['order_states']['r1-B']['requires_reassessment'])
        self.assertEqual(r['rounds'][0]['selected_candidate']['classification'],'WAIT_SETTLEMENT_REASSESSMENT')

    def test_explicit_cancel_and_new_review_do_not_resurrect_old_order(self):
        r=saved('wait-then-new-review')['replay'];e=r['last_execution']
        self.assertEqual(e['order_states']['r1-B']['status'],'CANCELLED_AT_REVIEW')
        self.assertEqual(e['order_states']['r1-B']['remaining'],'20')
        self.assertEqual(e['fill_order_ids'][e['new_fill_ids'][0]],'r2-B')
        self.assertTrue(r['rounds'][1]['cancellations_applied'])
        self.assertEqual(Decimal(e['ledger']['daily'][-1]['net_accrual_equity']),Decimal('1325.48'))

    def test_outer_gate_is_applied_before_executor_not_raw_core_only(self):
        r=saved('outer-gate-before-execution')['replay'];c=r['rounds'][0]['selected_candidate']
        self.assertTrue(c['core_evaluation']['feasible']);self.assertEqual(c['classification'],'REJECTED')
        self.assertEqual(r['execution_calls'],0);self.assertIsNone(r['last_execution'])
        self.assertIsNone(r['rounds'][0]['execution_job'])

    def test_new_batch_cannot_reuse_trigger_first_label_or_shared_bar(self):
        for name in ('old-trigger-blocked','false-first-blocked','shared-bar-blocked'):
            r=saved(name)['replay']
            with self.subTest(name=name):
                self.assertEqual(r['status'],'STOPPED_CANDIDATE_GATE');self.assertEqual(r['execution_calls'],1)
                self.assertEqual(len(r['last_execution']['fills']),2);self.assertIsNone(r['rounds'][1]['execution'])
                self.assertIsNotNone(r['rounds'][1]['quantity_request'])
                self.assertEqual(r['execution_watermark'],'2026-01-08T16:00:00+08:00')

    def test_price_limit_and_unsold_A_do_not_become_completed_rotation(self):
        e=saved('limit-up-unfilled')['replay']['last_execution']
        self.assertEqual(e['ledger']['daily'][-1]['shares']['B'],'0')
        e=saved('unsold-A-joint-risk')['replay']['last_execution']
        self.assertEqual(e['fills'],[]);self.assertEqual(e['ledger']['daily'][-1]['shares']['A'],'100')
        self.assertTrue(any(x.get('reason')=='ACTUAL_RIGHTS_AND_POSSIBLE_FILLS_EXCEED_RISK_OR_MARKS_STALE' for x in e['execution_events']))

    def test_unsupported_payable_retains_actual_prefix_and_liabilities(self):
        r=saved('opening-payable-unsupported')['replay']
        self.assertEqual(r['status'],'STOPPED_NOT_IMPLEMENTED');self.assertEqual(r['execution_calls'],1)
        self.assertEqual(Decimal(r['historical_checkpoint']['state']['row']['purchase_payable']),Decimal('141.14'))
        self.assertEqual(len(r['last_execution']['fills']),2);self.assertIsNone(r['rounds'][1]['execution'])

    def test_late_close_and_account_reset_are_rejected_before_new_generation(self):
        for name,reason in [('close-not-yet-known','LEDGER_CLOSE_NOT_YET_AVAILABLE'),('account-reset-refused','TEMPLATE_ACCOUNT_OR_PLANS_FORBIDDEN')]:
            r=saved(name)['replay']
            with self.subTest(name=name):
                self.assertEqual(r['status'],'STOPPED_INPUT_ERROR');self.assertIn(reason,r['reasons'])
                self.assertEqual(r['execution_calls'],1);self.assertIsNone(r['rounds'][1]['generation'])

    def test_embedded_reassessment_cannot_bypass_quantity_gate(self):
        r=saved('embedded-review-refused')['replay']
        self.assertEqual(r['execution_calls'],0);self.assertIn('ROUND_FIELDS_NOT_SUPPORTED',r['reasons'])
        self.assertIsNone(r['last_execution'])

    def test_future_prefix_and_full_integrity_are_compared_separately(self):
        initial=saved('prefix-only')
        for name in ('future-A-wins','future-B-wins','future-both-fall'):
            after=saved(name)
            self.assertEqual(initial['replay']['rounds'][0]['numeric_prefix'],after['replay']['rounds'][0]['numeric_prefix'])
            self.assertNotEqual(initial['source_integrity_metadata'],after['source_integrity_metadata'])
            self.assertNotEqual(initial['replay']['last_execution']['result_id'],after['replay']['last_execution']['result_id'])

    def test_exact_decision_latest_fills_reserve_and_tokens_remain_bound(self):
        for name in ('partial-then-independent','wait-then-new-review'):
            records=saved(name)['replay']['rounds'];first,second=records
            cp=first['checkpoint'];cont=second['execution_job']['continuation'];e=second['execution']
            self.assertEqual(cont['checkpoint'],cp)
            self.assertEqual(cont['previous_decision']['decision']['decision_id'],cp['state']['latest_decision_id'])
            self.assertEqual(e['fills'][:len(first['execution']['fills'])],first['execution']['fills'])
            self.assertTrue(set(cp['state']['reviewed_evidence_tokens'])<=set(second['checkpoint']['state']['reviewed_evidence_tokens']))
            self.assertEqual(second['checkpoint']['state']['general_reserved_cash'],'100')
            for record in records:self.assertEqual(record['selected_candidate']['core_decision_id'],record['execution']['decision_id'])

    def test_explicit_hold_immutability_and_no_automatic_order_generation(self):
        request=saved('prefix-only','input');first=request['rounds'][0]
        first['selection']=dict(mode='HOLD',sell_A=None,additional_B=None,reason='EXPLICIT_SYNTHETIC_HOLD_CONTROL')
        first['orders']=[];original=deepcopy(request)
        actual=replay_sequence(request)['replay'];self.assertEqual(request,original)
        self.assertEqual(actual['status'],'COMPLETED_PROVIDED_ROUNDS');self.assertEqual(actual['last_execution']['orders'],[])
        self.assertEqual(actual['last_execution']['fills'],[])

    def test_resource_budget_and_missing_selection_have_no_fallback(self):
        request=saved('partial-then-independent','input');request['run_policy']['max_rounds']='1'
        with patch('capital_research.quantity_replay.simulate') as executor:
            r=replay_sequence(request)['replay'];executor.assert_not_called()
        self.assertEqual(r['status'],'REFUSED_ROUND_LIMIT');self.assertEqual(r['rounds'],[])
        request=saved('prefix-only','input');request['rounds'][0].pop('selection')
        r=replay_sequence(request)['replay'];self.assertEqual(r['status'],'STOPPED_INPUT_ERROR')
        self.assertEqual(r['execution_calls'],0);self.assertIsNone(r['last_execution'])

    def test_explicit_order_exceeding_target_is_still_rejected_by_original_executor(self):
        request=saved('prefix-only','input');request['rounds'][0]['orders'][1]['shares']='21'
        r=replay_sequence(request)['replay']
        self.assertEqual(r['status'],'STOPPED_INPUT_ERROR');self.assertEqual(r['execution_calls'],1)
        self.assertTrue(any('Order exceeds selected target change' in x for x in r['reasons']))
        self.assertIsNone(r['last_execution'])

    def test_replay_is_not_strategy_performance_or_authorization(self):
        for name in json.loads((HERE/'intake.json').read_text())['case_names']:
            r=saved(name)['replay'];self.assertIsNone(r['ranking']);self.assertIsNone(r['selected_strategy'])
            self.assertFalse(r['strategy_validated'])
            for key in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'):self.assertIs(r[key],False)


if __name__=='__main__':unittest.main()
