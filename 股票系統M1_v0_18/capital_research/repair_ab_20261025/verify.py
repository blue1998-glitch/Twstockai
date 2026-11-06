"""Only A/B methods and directly affected qualification/continuity regressions."""
import sys
import unittest

TESTS = [
    'capital_research.repair_ab_20261025.test_ab',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_not_qualified_excludes_candidate_and_prevents_fill',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_old_valid_facts_survive_a_current_review_without_becoming_new_events',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_delayed_daily_close_must_be_available_before_next_decision',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_reassessment_then_another_execution_keeps_all_fills_and_tokens',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_partial_fills_cancel_and_continue_without_losing_claims_or_reserves',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_partial_fills_expire_and_continue_without_inventing_cancellation',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_expiry_and_invalidation_cancel_standing_orders_inside_limit',
    'capital_research.repair_20261025.test_repairs.RepairTests.test_research_permission_never_grants_external_qualification_or_R2',
    'capital_research.test_mechanisms.MechanismTests.test_cli_READ_never_imports_or_recalculates_engines',
]


def main():
    suite = unittest.defaultTestLoader.loadTestsFromNames(TESTS)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
