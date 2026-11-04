"""Capture unique targeted methods and all failures without touching old evidence."""
import io, json, sys, unittest
from .build import CAP, write
from .test_compare import Cap1Tests

def main(label, methods=()):
    stream=io.StringIO();suite=unittest.TestSuite(Cap1Tests(n) for n in methods) if methods else unittest.defaultTestLoader.loadTestsFromTestCase(Cap1Tests)
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    write(CAP/('tests-'+label+'.log'),stream.getvalue().encode())
    write(CAP/('tests-'+label+'.json'),dict(unique_methods=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        status='PASS' if result.wasSuccessful() else 'FAIL',old_test_batches_added=0))
    print(stream.getvalue());sys.exit(not result.wasSuccessful())

if __name__=='__main__':main(sys.argv[1],sys.argv[2:])
