"""Only fact-lineage methods and directly affected historical regressions."""
import sys
import unittest

TESTS = [
    'capital_research.evidence_lineage_20261025.test_lineage',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_old_valid_facts_survive_a_current_review_without_becoming_new_events',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_expired_fact_cannot_be_revived_by_a_current_review',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_future_revocation_does_not_rewrite_current_decision',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_expiry_and_invalidation_cancel_standing_orders_inside_limit',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_reassessment_then_another_execution_keeps_all_fills_and_tokens',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_partial_fills_cancel_and_continue_without_losing_claims_or_reserves',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_partial_fills_expire_and_continue_without_inventing_cancellation',
    'capital_research.repair_ab_20261025.test_ab.ABTests.test_foreign_evidence_rejects_buy_and_recommendation_in_both_asset_orders',
    'capital_research.repair_ab_20261025.test_ab.ABTests.test_delayed_cancellation_refuses_before_new_execution_and_keeps_old_reserve',
    'capital_research.test_mechanisms.MechanismTests.test_cli_READ_never_imports_or_recalculates_engines',
]


def main():
    suite = unittest.defaultTestLoader.loadTestsFromNames(TESTS)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__': sys.exit(main())
