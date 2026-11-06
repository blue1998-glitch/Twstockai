"""New identity methods plus nine directly necessary regressions; no old suite."""
import sys
import unittest

TESTS=[
    'capital_research.review_identity_20261026.test_identity',
    *['capital_research.rejected_reassessment_20261026.test_reassessment.RejectedReassessmentTests.'+name for name in (
        'test_rejected_restriction_survives_restore_with_current_review',
        'test_pre_funded_buy_is_blocked_on_the_review_observation',
        'test_rejected_value_only_edit_does_not_cancel_valid_old_order',
        'test_valid_review_can_authorize_the_existing_order',
        'test_partial_fill_survives_later_conflict_and_settles_once',
        'test_checkpoint_keeps_original_account_rights_and_all_review_tokens',
    )],
    'capital_research.repair_20261025.test_repairs.RepairTests.test_reassessment_then_another_execution_keeps_all_fills_and_tokens',
    'capital_research.repair_ab_20261025.test_ab.ABTests.test_delayed_cancellation_refuses_before_new_execution_and_keeps_old_reserve',
    'capital_research.test_mechanisms.MechanismTests.test_cli_READ_never_imports_or_recalculates_engines',
]


def methods(suite):
    for test in suite:
        if isinstance(test,unittest.TestSuite):yield from methods(test)
        else:yield test.id()


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromNames(TESTS);names=list(methods(suite))
    if len(names)!=len(set(names)):raise ValueError('Duplicate method ID')
    print('UNIQUE_METHODS='+str(len(names)),flush=True)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
