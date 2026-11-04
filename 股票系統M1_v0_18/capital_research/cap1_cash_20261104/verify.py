import io,json,sys,unittest
from .build import CAP,write
from .test_cash import CashTests

def main(label,methods=()):
    suite=unittest.TestSuite(CashTests(n) for n in methods) if methods else unittest.defaultTestLoader.loadTestsFromTestCase(CashTests)
    stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    write(CAP/('tests-'+label+'.log'),stream.getvalue().encode())
    write(CAP/('tests-'+label+'.json'),dict(unique_methods=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),status='PASS' if r.wasSuccessful() else 'FAIL',old_test_counts_added=0))
    print(stream.getvalue());sys.exit(not r.wasSuccessful())
if __name__=='__main__':main(sys.argv[1],sys.argv[2:])
