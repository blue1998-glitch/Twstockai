"""Directed A/B counterexamples and positive controls, not market validation."""
from copy import deepcopy
from decimal import Decimal
import unittest
from unittest.mock import patch
from capital_research.core import decide
from capital_research.execution import simulate
from capital_research.continuity import validate_checkpoint
from capital_research.eligibility import entry_review
from .fixtures import cases, saved_pair, rebind, delayed


class ABTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jobs = cases(current_lineage=True)

    def test_foreign_evidence_rejects_buy_and_recommendation_in_both_asset_orders(self):
        for name in ('A-foreign-ABC', 'A-foreign-BAC'):
            job = self.jobs[name]
            d = decide(job['decision_input'])['decision']
            self.assertFalse(d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
            self.assertNotIn('E-partial', d['research_recommendation']['candidate_ids'])
            out = simulate(job)
            self.assertEqual(out['status'], 'REFUSED')
            self.assertEqual(out['fills'], [])
        self.assertEqual(decide(self.jobs['A-foreign-ABC']['decision_input'])['decision'],
                         decide(self.jobs['A-foreign-BAC']['decision_input'])['decision'])

    def test_own_evidence_positive_is_order_invariant_and_partially_fills(self):
        job = deepcopy(self.jobs['A-own-evidence'])
        other = deepcopy(job)
        assets = other['decision_input']['assets']
        other['decision_input']['assets'] = {c: assets[c] for c in ('B', 'A', 'C')}
        self.assertEqual(decide(job['decision_input']), decide(other['decision_input']))
        one, two = simulate(job), simulate(other)
        self.assertEqual(one['fills'], two['fills'])
        self.assertEqual([(f['code'], f['shares']) for f in one['fills']], [('A', '20'), ('B', '7')])

    def test_foreign_owner_is_rejected_even_with_identical_source_and_basis(self):
        data = deepcopy(self.jobs['A-foreign-ABC']['decision_input'])
        asset = data['assets']['B']
        fact = deepcopy(data['assets']['A']['evidence'][0])
        for key in ('source_id', 'basis_id', 'adjustment_version'):
            fact[key] = asset[key]
        out = entry_review(asset, 'B', data, {'A-event': fact})
        self.assertFalse(out['qualified_for_synthetic_proposal'])
        self.assertIn('REVIEW_EVIDENCE_NOT_OWNED_OR_BINDING_MISMATCH:A-event', out['reasons'])

    def test_owned_fact_requires_all_source_basis_adjustment_fields(self):
        data = self.jobs['A-own-evidence']['decision_input']
        asset = data['assets']['B']
        for key in ('source_id', 'basis_id', 'adjustment_version'):
            fact = deepcopy(asset['evidence'][0]); fact[key] = 'wrong'
            out = entry_review(asset, 'B', data, {fact['id']: fact})
            self.assertFalse(out['qualified_for_synthetic_proposal'])
            self.assertTrue(any('BINDING_MISMATCH' in x for x in out['reasons']))

    def test_buy_without_target_increase_and_oversized_split_still_refuse(self):
        job = deepcopy(self.jobs['A-own-evidence'])
        buy = deepcopy(job['orders'][1]); buy['shares'] = '1'
        zero = deepcopy(job); zero.update(plan_id='A-zero', orders=[buy])
        with self.assertRaisesRegex(ValueError, 'target change'):
            simulate(zero)
        split = deepcopy(job)
        one, two = deepcopy(job['orders'][1]), deepcopy(job['orders'][1])
        one.update(id='split-1', shares='11'); two.update(id='split-2', shares='10')
        split['orders'] = [job['orders'][0], one, two]
        with self.assertRaisesRegex(ValueError, 'target change'):
            simulate(split)

    def test_delayed_cancellation_refuses_before_new_execution_and_keeps_old_reserve(self):
        job = self.jobs['B-delayed-cancel']
        saved = deepcopy(job['continuation']['checkpoint'])
        self.assertEqual(saved['state']['order_states']['B-buy']['reserved_cash'], '261.65039')
        with patch('capital_research.execution.replay', side_effect=AssertionError('must refuse before new execution')):
            with self.assertRaisesRegex(ValueError, 'ACTIVE_ORDER_GAP_CONTINUATION_NOT_IMPLEMENTED'):
                simulate(job)
        self.assertEqual(job['continuation']['checkpoint'], saved)

    def test_omitting_earlier_tape_does_not_prove_no_old_fills(self):
        with self.assertRaisesRegex(ValueError, 'ACTIVE_ORDER_GAP_CONTINUATION_NOT_IMPLEMENTED'):
            simulate(self.jobs['B-delayed-omitted-tape'])

    def test_same_close_review_records_actual_cancel_time_and_keeps_capital_rights(self):
        job = self.jobs['B-same-close-review']; out = simulate(job)
        self.assertEqual(out['ledger']['initial_equity'], '2180')
        self.assertEqual(job['decision_input']['account']['reserved_cash'], '100')
        self.assertEqual(out['fills'][:2], job['continuation']['checkpoint']['state']['accepted_fills'])
        for key in ('A-sell', 'B-buy'):
            state = out['order_states'][key]
            self.assertEqual(state['cancelled_at'], '2026-01-08T17:00:00+08:00')
            self.assertEqual(state['reserved_cash'], '0')
            self.assertIn(dict(at=state['cancelled_at'], order_id=key, status='CANCELLED_AT_REVIEW',
                               reason='EXPLICIT_REVIEW_BEFORE_NEXT_DECLARED_TRADING_DATE'), out['execution_events'])
        last = out['ledger']['daily'][-1]
        self.assertEqual(last['shares'], dict(A='10', B='0', C='0'))
        self.assertEqual(last['cash_claims'], [])
        self.assertEqual(last['share_receivables'], [])
        self.assertEqual(Decimal(last['net_accrual_equity']) + Decimal('9') + Decimal('1.28'), Decimal('2180'))

    def test_already_expired_orders_allow_later_review_without_fake_cancellation(self):
        job = self.jobs['B-already-expired']; out = simulate(job)
        self.assertEqual(job['continuation']['cancelled_order_ids'], [])
        for key in ('A-sell', 'B-buy'):
            self.assertEqual(out['order_states'][key]['status'], 'EXPIRED_UNFILLED')
        self.assertEqual(out['ledger']['initial_equity'], '2180')
        self.assertEqual(job['decision_input']['account']['reserved_cash'], '100')

    def test_declared_nontrading_gap_is_not_a_fixed_review_day_deadline(self):
        pair = saved_pair()
        for row in pair['first']['ledger_input']['calendar']:
            if row['date'] == '2026-01-09': row['trading'] = False
        pair['next']['ledger_input'] = deepcopy(pair['first']['ledger_input'])
        pair = rebind(pair)
        job = delayed(pair['next'])
        job['tape'] = [o for o in job['tape'] if o['at'][:10] == '2026-01-12']
        self.assertEqual(simulate(job)['status'], 'SYNTHETIC_EXECUTION_REPLAY')

    def test_historical_v03_checkpoint_is_not_implicitly_upgraded(self):
        old = saved_pair()['next']['continuation']['checkpoint']
        with self.assertRaisesRegex(ValueError, 'Versioned lifecycle checkpoint required'):
            validate_checkpoint(old)


if __name__ == '__main__':
    unittest.main()
