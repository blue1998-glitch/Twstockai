"""Only this repair's methods and nine directly relevant regressions."""
import sys
import unittest

TESTS = [
    'capital_research.rejected_reassessment_20261026.test_reassessment',
    *['capital_research.repair_20261025.test_repairs.RepairTests.'+name for name in (
        'test_old_valid_facts_survive_a_current_review_without_becoming_new_events',
        'test_expired_fact_cannot_be_revived_by_a_current_review',
        'test_latest_reassessment_resumes_and_old_predecessor_refuses',
        'test_reassessment_then_another_execution_keeps_all_fills_and_tokens',
        'test_partial_fills_cancel_and_continue_without_losing_claims_or_reserves',
        'test_partial_fills_expire_and_continue_without_inventing_cancellation',
    )],
    'capital_research.repair_ab_20261025.test_ab.ABTests.test_foreign_evidence_rejects_buy_and_recommendation_in_both_asset_orders',
    'capital_research.repair_ab_20261025.test_ab.ABTests.test_delayed_cancellation_refuses_before_new_execution_and_keeps_old_reserve',
    'capital_research.test_mechanisms.MechanismTests.test_cli_READ_never_imports_or_recalculates_engines',
]


def methods(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from methods(test)
        else:
            yield test.id()


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromNames(TESTS)
    names=list(methods(suite))
    if len(names)!=len(set(names)):
        raise ValueError('Duplicate method count')
    print(f'UNIQUE_METHODS={len(names)}',flush=True)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
