"""Only this repair scope and five necessary storage/input regressions."""
import sys
import unittest

TESTS=[
    'capital_research.repair_20261025.test_repairs',
    'capital_research.test_mechanisms.MechanismTests.test_cli_READ_never_imports_or_recalculates_engines',
    'capital_research.test_mechanisms.MechanismTests.test_immutable_store_conflict_and_partial_file_preserved',
    'capital_research.test_mechanisms.MechanismTests.test_missing_company_action_net_still_refused',
    'capital_research.test_mechanisms.MechanismTests.test_real_flag_and_unknown_numeric_inputs_fail_closed',
    'capital_research.test_mechanisms.MechanismTests.test_missing_mark_never_fills_or_zeros']


def main():
    suite=unittest.defaultTestLoader.loadTestsFromNames(TESTS)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':sys.exit(main())
