"""Only new orchestration boundaries. Mocks are not market execution evidence."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from . import flow as f
class FlowTests(unittest.TestCase):
    def setUp(self):
        # Fresh small isolated synthetic controls; retained by the runner.
        self.tmp=Path(tempfile.mkdtemp(prefix='case-',dir=str(f.WORK/'tests')))
        self.w=f.init(self.tmp/'product');self.sw=self.tmp/'scan';self.sw.mkdir()
        self.spec=dict(id='synthetic-spec',as_of='2026-01-02')
        (self.sw/'manifest-private.json').write_bytes(f.encode(self.spec))
        (self.sw/'complete-index.json').write_bytes(f.encode(dict(expected=2,markets={},counts={'EXECUTED_INSUFFICIENT_HISTORY':2})))
        self.complete=dict(status='COMPLETE',new_core_calls=0,new_records=0)
        self.fakeview=dict(catalogue='SYNTHETIC_NO_SERVICE',providers=[])
    def call(self,result=None):
        with patch.object(f,'source_check',return_value=self.spec),patch.object(f.scan,'run',return_value=result or self.complete),patch('graph_core.prod_core1_20261105.view.build',return_value=self.fakeview):
            result=f.saved('2026-01-02',work=self.w,scanwork=self.sw)
            if result['status']=='COMPLETE':f.point(self.w,'head-private.json',f.read(self.w/'prepared-head-private.json')) # synthetic activation commit
            return result
    def test_completed_replay_zero_writes(self):
        a=self.call();before={str(p):p.read_bytes() for p in self.w.rglob('*') if p.is_file()};b=self.call()
        self.assertFalse(a['reused']);self.assertTrue(b['reused']);self.assertEqual(b['this_execution_new_core_calls'],0)
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.w.rglob('*') if p.is_file()})
    def test_partial_never_publishes(self):
        r=self.call(dict(status='PARTIAL',new_core_calls=1,new_records=1));self.assertEqual(r['status'],'PARTIAL');self.assertFalse((self.w/'head-private.json').exists())
    def test_changed_saved_index_refuses_without_repair(self):
        self.call();head=(self.w/'head-private.json').read_bytes();(self.sw/'complete-index.json').write_bytes(b'{}')
        with self.assertRaises(ValueError):self.call()
        self.assertEqual((self.w/'head-private.json').read_bytes(),head)
    def test_failed_source_preserves_last_head(self):
        self.call();head=(self.w/'head-private.json').read_bytes()
        with patch.object(f,'source_check',side_effect=ValueError('BAD_SOURCE')),patch.object(f.scan,'run') as core:
            with self.assertRaises(ValueError):f.saved('2026-01-02',work=self.w,scanwork=self.sw)
            core.assert_not_called()
        self.assertEqual((self.w/'head-private.json').read_bytes(),head)
    def test_capacity_refuses_before_file(self):
        with patch.object(f.shutil,'disk_usage',return_value=type('Usage',(),dict(free=f.RESERVE))()):
            with self.assertRaises(OSError):f.put(self.w,self.w/'must-not-exist',b'x')
        self.assertFalse((self.w/'must-not-exist').exists())
    def test_blocked_intake_cannot_call_scan_or_change_head(self):
        self.call();head=(self.w/'head-private.json').read_bytes()
        report=dict(qualification=dict(status='BLOCKED_SOURCE_QUALIFICATION',reason='SYNTHETIC_WRONG_DATE'),actual_market_dates={'TWSE':'2026-01-02'},this_execution_GETs=0,capture_id='a'*64)
        with patch('graph_core.daily_chain1_20261104.intake.run',return_value=report),patch.object(f,'saved') as saved:
            r=f.fetch('2026-01-05',work=self.w,attempt='explicit-operator-review');saved.assert_not_called()
        self.assertEqual(r['status'],'BLOCKED_SOURCE');self.assertEqual((self.w/'head-private.json').read_bytes(),head)
    def test_invalid_new_attempt_name_cannot_capture(self):
        with patch('graph_core.daily_chain1_20261104.intake.run') as intake:
            with self.assertRaises(ValueError):f.fetch('2026-01-05',work=self.w,attempt='../escape')
            intake.assert_not_called()
    def test_new_attempt_cannot_bypass_prior_source_denial(self):
        q=self.w/'intake/2026-01-05/result-private.json';f.put(self.w,q,f.encode(dict(http_trace=[dict(http_status=403)])))
        with patch('graph_core.daily_chain1_20261104.intake.run') as intake:
            with self.assertRaises(ValueError):f.fetch('2026-01-06',work=self.w,attempt='new-name')
            intake.assert_not_called()
    def test_exact_target_required_before_source_io(self):
        with patch.object(f.inc,'sources') as source:
            with self.assertRaises(ValueError):f.source_check(self.sw,'2026-01-03')
            source.assert_not_called()
    def test_completed_numerical_stage_does_not_publish_before_activation(self):
        with patch.object(f,'source_check',return_value=self.spec),patch.object(f.scan,'run',return_value=self.complete),patch('graph_core.prod_core1_20261105.view.build',return_value=self.fakeview):
            f.saved('2026-01-02',work=self.w,scanwork=self.sw)
        self.assertTrue((self.w/'prepared-head-private.json').exists());self.assertFalse((self.w/'head-private.json').exists())
    def test_status_reads_durable_receipt_no_writes(self):
        self.call();before={str(p):p.read_bytes() for p in self.w.rglob('*') if p.is_file()};r=f.status(self.w)
        self.assertEqual(r['reference'],2);self.assertFalse(r['scheduled']);self.assertEqual(r['android'],'ANDROID_EXTERNAL_NOT_CONNECTED')
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.w.rglob('*') if p.is_file()})
    def test_qualified_new_day_materializes_and_resumes_original_core(self):
        from graph_core.daily_chain1_20261104.test_intake import GateTests
        from graph_core.graph_lazy1_20261104.worker import run as original_worker
        from graph_core import market_daily as d
        root=self.tmp/'synthetic-base';(root/'scan1_20261104').mkdir(parents=True)
        real=f.read(f.BASE/'scan1_20261104/manifest-private.json')
        (root/'scan1_20261104/manifest-private.json').write_bytes(f.encode(dict(stocks=[],protected_code=real['protected_code'])))
        (root/'scan1_20261104/view-state-private.json').write_bytes(f.encode(dict(stocks=[])))
        values=GateTests.data(None,dt='2026-01-02');cap=self.tmp/'synthetic-capture';receipts=[]
        for name,url in d.URLS.items():
            b=values[url];h=f.sha(b);f.put(self.w,self.w/'fixture-raw'/h,b)
            dest=cap/'raw'/h;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
            receipts.append(dict(name=name,url=url,status='RECEIVED',sha256=h,bytes=len(b)))
        cid=f.sha(f.encode(receipts));(cap/'captures').mkdir();(cap/'captures'/(cid+'.json')).write_bytes(f.encode(receipts))
        with patch.object(f,'BASE',root):
            sw=f.materialize(cap,cid,'2026-01-02',self.w);f.source_check(sw,'2026-01-02')
            a=f.scan.run(sw,limit=1,runner=original_worker);b=f.scan.run(sw,runner=original_worker)
            self.assertEqual((a['status'],a['new_core_calls'],b['new_core_calls']),('PARTIAL',1,1))
            with patch.object(f.scan.OriginalProvider,'_worker',side_effect=AssertionError('NO_REPEAT_CORE')):
                c=f.scan.run(sw)
            self.assertEqual((c['processed'],c['new_records'],c['new_core_calls']),(2,0,0))
            self.assertEqual(c['counts'],{'EXECUTED_INSUFFICIENT_HISTORY':2})
if __name__=='__main__':unittest.main(verbosity=2)
