"""Directed behaviour checks; all values are synthetic, no strategy ranking."""
from copy import deepcopy
import json
import unittest
from capital_research.continuity import validate_checkpoint
from .fixtures import CASES, ROOT, specification, materialize, observed


class RestrictionConflictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = {name:materialize(specification(name)) for name in CASES}

    def check(self, name):
        expected = specification(name)['expected']; actual = observed(self.results[name])
        self.assertEqual(actual['B_qualified'], expected['B_qualified'])
        self.assertEqual(actual['E_partial_candidate'], expected['E_partial_candidate'])
        self.assertEqual(not actual['new_tokens'], expected['new_tokens_empty'])
        self.assertEqual(actual['B_order_status'], expected['B_order_status'])
        self.assertEqual(actual['new_B_fill_shares'], expected['new_B_fill_shares'])
        return self.results[name]

    def test_mixed_null_expiry_and_known_revocation_cannot_revive_capital(self):
        r = self.check('mixed-null-revocation')
        self.assertTrue(any('RESTRICTION_CONFLICT' in x for x in observed(r)['reasons']))

    def test_extended_finite_expiry_cannot_discard_new_revocation(self):
        self.check('mixed-later-revocation')

    def test_rejected_value_rewrite_cannot_discard_new_revocation(self):
        self.check('rejected-value-revocation')

    def test_rejected_value_rewrite_cannot_discard_earlier_expiry(self):
        self.check('rejected-value-earlier-expiry')

    def test_alias_cannot_escape_the_original_restriction_conflict(self):
        self.check('alias-after-conflict')

    def test_genuinely_independent_fact_can_compete_without_erasing_conflict(self):
        r = self.check('independent-new-fact')
        self.assertTrue(r['resumed']['decision']['fact_history']['restriction_conflicts'])

    def test_exact_valid_original_recovers_after_value_only_rejection(self):
        self.check('restore-valid-original')

    def test_exact_original_recovers_after_extension_only_rejection(self):
        self.check('restore-after-extension-only')

    def test_future_conflict_preserves_numeric_prefix_then_cancels_at_known_time(self):
        r = self.check('future-revocation')
        plain = specification('future-revocation')
        plain['second_fact']['validity']['invalidation'] = None
        baseline = materialize(plain)
        self.assertEqual(r['resumed']['decision'], baseline['resumed']['decision'])
        self.assertNotEqual(r['execution']['fact_sources'], baseline['execution']['fact_sources'])
        event = next(e for e in r['execution']['execution_events'] if e['order_id']=='next-B-buy' and e['status']=='CANCELLED_EVIDENCE')
        self.assertEqual(event['at'], '2026-01-09T09:01:00+08:00')

    def test_later_available_revocation_does_not_delete_prior_legal_fill(self):
        self.check('late-revocation')

    def test_simultaneous_expiry_keeps_expired_order_status(self):
        self.check('equal-expiry-revocation')

    def test_without_tape_conflict_keeps_effective_and_observed_times(self):
        r = self.check('future-no-tape')
        event = next(e for e in r['execution']['execution_events'] if e['order_id']=='next-B-buy' and e['status']=='CANCELLED_EVIDENCE')
        self.assertEqual(event['at'], '2026-01-09T09:01:00+08:00')
        self.assertEqual(event['observed_at'], r['execution']['observed_until'])

    def test_original_account_rights_reserve_latest_and_old_READ_boundary(self):
        r = self.results['mixed-null-revocation']; c1,c2=r['checkpoints']
        self.assertEqual(c1['origin_ledger_input'], c2['origin_ledger_input'])
        self.assertEqual(c2['state']['origin_initial_capital'], '2180')
        self.assertEqual(c1['state']['row']['settled_cash'], '1000')
        self.assertEqual(c2['state']['row']['settled_cash'], '1080')
        self.assertEqual(c1['state']['row']['shares']['A'], '100')
        self.assertEqual(c2['state']['row']['shares']['A'], '110')
        self.assertEqual(c1['state']['row']['cash_receivable'], '80')
        self.assertEqual(c2['state']['row']['cash_receivable'], '0')
        for c in (c1,c2):
            self.assertEqual(c['state']['general_reserved_cash'], '100')
            self.assertEqual(c['state']['accepted_fills'], [])
            self.assertEqual(c['state']['unfilled_orders'], [])
        d = r['resumed']['decision']
        self.assertEqual(d['continuity']['latest_predecessor_id'], c2['state']['latest_decision_id'])
        self.assertTrue(set(c2['state']['reviewed_evidence_tokens']) <= set(d['reviewed_evidence_tokens']))
        self.assertEqual(d['schema'], 'capital-decision/0.6')
        for flag in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'):
            self.assertFalse(d[flag])
        self.assertIsNone(d['primary_pressure_id'])
        old = json.loads((ROOT/'evidence_lineage_20261025/after-final/valid-old-fact/input.json').read_text())
        with self.assertRaisesRegex(ValueError, 'Versioned lifecycle checkpoint required'):
            validate_checkpoint(old['next']['continuation']['checkpoint'])


if __name__=='__main__':unittest.main()
