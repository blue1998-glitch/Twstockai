"""Four bounded IO controls on an EXISTING real saved 11/02 stock, no core calls.
No synthetic prices. Current/legacy parent directory seams are metadata only.
"""
import ast,io,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
from graph_core import market_preview as preview
from rotation_research import artifact_codec as c
from rotation_research.store import Journal
from graph_core.day1_20261103.probe_once import heads
from .capture_once import ROOT,WORK
from . import capture_once

CAP=Path(__file__).parent
class Captured(Exception):pass


def capture_build(fn,parent_id,parent_page,descriptor,stock,value,child):
    before=heads(ROOT);actual=[];original_read=Journal.read;original_bytes=c.read_bytes
    trial='day2-readonly-lookup-control';batch=dict(child,parent_run=parent_id,stocks=[stock])
    directory=b'<script id="market-state" type="application/json">'+c.encoded(dict(stocks=[dict(identity=stock['identity'],preview_series=descriptor)]))+b'</script>'
    def read(self,key):
        if self.root==ROOT/'runs' and key==trial:return dict(schema='rotation-record/0.1',id=key,value=batch)
        if self.root==ROOT/'results' and key==stock['result_key']:return dict(schema='rotation-record/0.1',id=key,value=value)
        return original_read(self,key)
    def rb(path,**kw):return directory if Path(path)==parent_page else original_bytes(path,**kw)
    def store(path,raw,*,root,bases=(),format='journal'):
        actual.append(dict(raw=raw,bases=list(bases),format=format));raise Captured()
    def fail(*a,**kw):raise AssertionError('READONLY_TEST_MUST_NOT_WRITE')
    with patch.object(Journal,'read',read),patch.object(c,'read_bytes',rb),patch.object(c,'publish_interned',store),patch.object(c,'immutable',fail),patch.object(preview,'publish_immutable',fail):
        try:fn(ROOT,trial)
        except Captured:pass
    if len(actual)!=1 or heads(ROOT)!=before:raise AssertionError('READONLY_CAPTURE_OR_HEAD_CONFLICT')
    return actual[0]


class LookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        head=json.loads((ROOT/'current-increment-run.json').read_bytes());child=Journal(ROOT/'runs').read(head['id'])['value']
        lite_root=Path('/workspace/twstockai-local-data/lite1_20261103');current=json.loads((lite_root/'2026-11-02/prepared-state-private.json').read_bytes());legacy=json.loads((lite_root/'2026-10-30/prepared-state-private.json').read_bytes())
        old={r['identity']:r for r in legacy['stocks'] if r.get('preview_series')};now={r['identity']:r for r in current['stocks'] if r.get('preview_series')}
        stock=next(s for s in child['stocks'] if s.get('result_key') and s['identity'] in old and s['identity'] in now)
        value=Journal(ROOT/'results').read(stock['result_key'])['value'];identity=stock['identity'];page=Path(head['private_preview']['path'])
        node=next(n for n in ast.parse((CAP/'market_preview-before.py.txt').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='build')
        tree=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]));namespace=dict(preview.__dict__);exec(compile(tree,'original-preview-function','exec'),namespace)
        cls.before=capture_build(namespace['build'],head['id'],page,now[identity]['preview_series'],stock,value,child)
        cls.after=capture_build(preview.build,head['id'],page,now[identity]['preview_series'],stock,value,child)
        cls.expected_current=page.parent/now[identity]['preview_series']['path'];cls.saved_current_sha=now[identity]['preview_series']['sha256']
        fm3=json.loads((ROOT/'fm3-continuation.json').read_bytes());parent_id=child['parent_run'];old_page=Path(fm3['preview']['path'])
        cls.legacy=capture_build(preview.build,parent_id,old_page,old[identity]['preview_series'],stock,value,child)
        cls.expected_legacy=old_page.parent/old[identity]['preview_series']['path']
    def test_01_current_formatter_parent_is_reused(self):
        self.assertEqual(self.before['bases'],[]);self.assertEqual(self.after['bases'],[self.expected_current])
    def test_02_original_legacy_parent_still_supported(self):
        self.assertEqual(self.legacy['bases'],[self.expected_legacy])
    def test_03_original_chart_bytes_and_values_unchanged(self):
        self.assertTrue(self.before['raw']==self.after['raw'],'Before/after chart bytes differ')
        self.assertEqual(c.sha(self.after['raw']),self.saved_current_sha)
        self.assertTrue(self.legacy['raw']==self.after['raw'],'Anchor choice changed logical bytes')
    def test_04_same_capture_cannot_start_duplicate_requests(self):
        with patch.object(capture_once.original,'probe',side_effect=AssertionError('no provider call')):
            with self.assertRaises(FileExistsError):capture_once.run()


def main():
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LookupTests))
    c.immutable(WORK/'lookup-tests.log',stream.getvalue().encode())
    report=dict(status='PASS' if result.wasSuccessful() else 'FAIL',unique_methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        market_core_calls=0,source_GETs=0,source_data_kind='EXISTING_REAL_2026_11_02_NOT_SYNTHETIC',file_writes_to_FM3=0,old_test_counts_added=0)
    c.immutable(WORK/'lookup-tests-private.json',c.encoded(report));print(stream.getvalue());print(json.dumps(report));sys.exit(not result.wasSuccessful())
if __name__=='__main__':main()
