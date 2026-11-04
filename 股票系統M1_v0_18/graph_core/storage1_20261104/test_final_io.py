"""Two added IO controls; do not rerun or recount prior 13 methods."""
import unittest,io,json
from pathlib import Path
from . import build,activate
from .common import WORK,BASE,sha,read_json,protected_heads,write,encode
class FinalIO(unittest.TestCase):
    def test_14_full_same_source_entry_does_not_add_or_modify_artifacts(self):
        before={(str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in WORK.rglob('*') if p.is_file()};heads=protected_heads();r=build.run()
        self.assertTrue(r['facts']['reused']);self.assertEqual(r['facts']['new_bytes'],0);self.assertEqual(r['facts']['new_stock_writes'],0)
        after={(str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in WORK.rglob('*') if p.is_file()};self.assertEqual(before,after);self.assertEqual(heads,protected_heads())
    def test_15_cached_route_status_matches_actual_final_view_pointer(self):
        r=activate.run();self.assertTrue(r['reused']);self.assertEqual(r['new_view_head_sha256'],sha((BASE/'lite1_20261103/view-head-private.json').read_bytes()));self.assertEqual(read_json(BASE/'lite1_20261103/view-head-private.json')['batch_index'],r['new_catalogue'])
def main():
    out=io.StringIO();r=unittest.TextTestRunner(stream=out,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FinalIO));write(WORK/'python-final-io.log',out.getvalue().encode());report=dict(status='PASS' if r.wasSuccessful() else 'FAIL',unique_methods=r.testsRun,failures=len(r.failures),errors=len(r.errors),prior_13_methods_rerun=False,new_core_calls=0,new_provider_requests=0)
    write(WORK/'python-final-io-private.json',encode(report));print(out.getvalue());print(json.dumps(report));raise SystemExit(not r.wasSuccessful())
if __name__=='__main__':main()
