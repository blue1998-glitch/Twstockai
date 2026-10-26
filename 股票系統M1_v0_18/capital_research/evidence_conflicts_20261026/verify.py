"""New directed cases plus selected regressions, never an old complete suite."""
import sys
import unittest

TESTS = [
    'capital_research.evidence_conflicts_20261026.test_conflicts',
    *['capital_research.evidence_lineage_20261025.test_lineage.FactLineageTests.'+name for name in (
        'test_rejected_rewrite_does_not_permanently_taint_unchanged_valid_fact',
        'test_valid_old_fact_keeps_identity_and_does_not_become_new_event',
        'test_independent_new_fact_does_not_erase_or_inherit_old_invalidity',
        'test_future_revocation_is_absent_from_numeric_prefix_but_kept_in_integrity',
        'test_finite_expiry_cannot_be_removed_or_extended',
        'test_explicit_alias_preserves_the_original_revocation',
    )],
    *['capital_research.repair_20261025.test_repairs.RepairTests.'+name for name in (
        'test_reassessment_then_another_execution_keeps_all_fills_and_tokens',
        'test_partial_fills_cancel_and_continue_without_losing_claims_or_reserves',
        'test_partial_fills_expire_and_continue_without_inventing_cancellation',
    )],
    'capital_research.repair_ab_20261025.test_ab.ABTests.test_foreign_evidence_rejects_buy_and_recommendation_in_both_asset_orders',
    'capital_research.repair_ab_20261025.test_ab.ABTests.test_delayed_cancellation_refuses_before_new_execution_and_keeps_old_reserve',
    'capital_research.test_mechanisms.MechanismTests.test_cli_READ_never_imports_or_recalculates_engines',
]


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(TESTS))
    sys.exit(0 if result.wasSuccessful() else 1)
