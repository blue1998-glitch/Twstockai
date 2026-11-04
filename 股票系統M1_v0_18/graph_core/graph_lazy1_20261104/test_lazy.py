"""New cache/binding/resource controls are SYNTHETIC, no actual market claims."""
import unittest,json,io,copy,time,threading,tempfile,http.client,base64
from pathlib import Path
from unittest.mock import patch
from .common import WORK,PROJECT,write,encode,sha
from .provider import Provider,Refused,Busy,MAX_ENTRIES,MAX_BYTES
from .worker import run as calculate
CALLS=0
class CacheTests(unittest.TestCase):
    def setup_provider(self,n=1,*,status='SOURCE_BAR_AVAILABLE',wrong_identity=False,bad_basis=False):
        folder=WORK/'unit-fixtures'/self._testMethodName;folder.mkdir(parents=True,exist_ok=False);source=folder/'synthetic-source';write(source,b'SYNTHETIC_SOURCE_ONLY_NOT_MARKET');st=source.stat();h=sha(source.read_bytes());allowed={};actions=[]
        for i in range(n):
            code='TEST'+str(i);ident='TWSE:'+code;dt='2026-11-03'
            f=dict(schema='official-daily-fact/0.1',fixture_kind='SYNTHETIC_TEST_ONLY',identity='WRONG' if wrong_identity else ident,code=code,name='Synthetic only',market='TWSE',isin='SYNTHETIC',cfi='ESVUFR',as_of=dt,source_status=status,source_label='Synthetic refusal',bar=None if status!='SOURCE_BAR_AVAILABLE' else dict(date=dt,open='10.0000',high='11.0',low='9.0',close='10.2500',volume_shares_scaled='12345678901234567'),continuity='NOT_CERTIFIED_NO_HISTORY_APPENDED',source=dict(capture_id='c'*64,daily_sha256=h,volume_unit='SHARES_REPORTED',price_mode='RAW_CANDIDATE',price_basis_id='WRONG' if bad_basis else ident+'-OFFICIAL-RAW-UNBRIDGED-'+dt))
            raw=encode(f);fh=sha(raw);path=folder/('series-'+fh+'.json');write(path,raw);desc=dict(bytes=len(raw),sha256=fh,path=path.name);route='action-'+str(i);factroute='fact-'+str(i);allowed[factroute]=dict(path=path,bytes=len(raw),sha256=fh)
            actions.append(dict(route=route,request_id='r'+str(i),identity=ident,code=code,market='TWSE',isin='SYNTHETIC',cfi='ESVUFR',as_of=dt,fact_route=factroute,fact_path=str(path),fact=desc))
        protected=PROJECT/'graph_core/core.py';spec=dict(schema='private-lazy-graph-actions/0.1',actions=actions,capture_id='c'*64,protected_code={str(protected):sha(protected.read_bytes())},original_daily_sources={'TWSE':dict(path=str(source),sha256=h,metadata=[st.st_size,st.st_mtime_ns,st.st_ino,st.st_dev])})
        raw=encode(spec);manifest=folder/'catalogue.json';write(manifest,raw);clock=[100.]
        def runner(f):
            global CALLS;CALLS+=1;return calculate(f)
        provider=Provider(manifest,sha(raw),runner=runner,clock=lambda:clock[0]);return provider,allowed,clock,source,protected
    def test_01_repeat_is_ram_hit_with_identical_result_bytes(self):
        p,a,_,_,_=self.setup_provider();x,first=p.get('action-0',a);y,second=p.get('action-0',a);self.assertEqual((first,second),('MISS','HIT'));self.assertEqual(x,y);self.assertEqual(p.metrics['core_calls'],1)
    def test_02_over_eight_keys_is_bounded_LRU(self):
        p,a,_,_,_=self.setup_provider(10)
        for i in range(10):p.get('action-'+str(i),a)
        self.assertLessEqual(len(p.cache),MAX_ENTRIES);self.assertLessEqual(p.used,MAX_BYTES);self.assertEqual(p.metrics['evictions'],2)
    def test_03_expiration_requires_fresh_bounded_calculation(self):
        p,a,t,_,_=self.setup_provider();p.get('action-0',a);t[0]+=601;_,flag=p.get('action-0',a);self.assertEqual(flag,'MISS');self.assertEqual(p.metrics['core_calls'],2)
    def test_04_rejected_source_does_not_call_core(self):
        p,a,_,_,_=self.setup_provider(status='MISSING_QUOTE');raw,flag=p.get('action-0',a);self.assertEqual(flag,'REFUSED');self.assertIsNone(json.loads(raw)['series']);self.assertEqual(p.metrics['core_calls'],0)
    def test_05_wrong_identity_rejected(self):
        p,a,_,_,_=self.setup_provider(wrong_identity=True)
        with self.assertRaises(Refused):p.get('action-0',a)
    def test_06_wrong_price_basis_rejected(self):
        p,a,_,_,_=self.setup_provider(bad_basis=True)
        with self.assertRaises(Refused):p.get('action-0',a)
    def test_07_corrupt_fact_never_reuses_cached_result(self):
        p,a,_,_,_=self.setup_provider();p.get('action-0',a);path=a['fact-0']['path'];original=Path.read_bytes
        with patch.object(Path,'read_bytes',lambda q:b'changed' if q==path else original(q)):
            with self.assertRaises(Refused):p.get('action-0',a)
        self.assertEqual(p.used,0)
    def test_08_changed_engine_code_invalidates_cache(self):
        p,a,_,_,target=self.setup_provider();p.get('action-0',a);original=Path.read_bytes
        with patch.object(Path,'read_bytes',lambda q:b'changed' if q==target else original(q)):
            with self.assertRaises(Refused):p.get('action-0',a)
        self.assertEqual(p.used,0)
    def test_09_source_metadata_change_refuses(self):
        p,a,_,source,_=self.setup_provider();source.write_bytes(b'PURE_SYNTHETIC_TAMPER_CONTROL')
        with self.assertRaises(Refused):p.get('action-0',a)
    def test_10_unknown_action_is_not_an_arbitrary_file_read(self):
        p,a,_,_,_=self.setup_provider()
        with self.assertRaises(KeyError):p.get('../../raw',a)
    def test_11_existing_worker_prevents_parallel_worker(self):
        p,a,_,_,_=self.setup_provider();p.lock.acquire()
        try:
            with self.assertRaises(Busy):p.get('action-0',a)
        finally:p.lock.release()
    def test_12_resource_rate_is_finite(self):
        p,a,_,_,_=self.setup_provider(13)
        for i in range(12):p.get('action-'+str(i),a)
        with self.assertRaises(Busy):p.get('action-12',a)
        self.assertEqual(p.metrics['core_calls'],12)
class HTTPGate(unittest.TestCase):
    def test_13_auth_origin_method_and_HEAD_precede_callback(self):
        from graph_core_chart.mobile_private import make_server,create_auth
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);page=root/'index.html';page.write_text('<script id="market-state" type="application/json">'+json.dumps(dict(stocks=[],summary=dict(as_of='2026-11-03')))+'</script>');auth=root/'auth.json';create_auth(auth,'synthetic','SYNTHETIC_PASSWORD_ONLY_123')
            class Dummy:
                calls=0
                def routes(self):return ['action.json']
                def get(self,*a):self.calls+=1;return b'{}','MISS'
            dummy=Dummy();server=make_server(page,auth,lazy_provider=dummy);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                token='Basic '+base64.b64encode(b'synthetic:SYNTHETIC_PASSWORD_ONLY_123').decode()
                def req(path,expected,method='GET',authorized=True,origin=None):
                    h={'Authorization':token} if authorized else {}
                    if origin:h['Origin']=origin
                    c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5);c.request(method,path,headers=h);r=c.getresponse();body=r.read();c.close();self.assertEqual(r.status,expected);return r,body
                req('/action.json',401,authorized=False);req('/action.json',403,origin='https://invalid.example');req('/action.json',204,method='HEAD');req('/action.json?code=all',404);req('/unknown.json',404);req('/action.json',405,method='POST');self.assertEqual(dummy.calls,0);r,b=req('/action.json',200);self.assertEqual(dummy.calls,1);self.assertEqual(r.getheader('X-Artifact-SHA256'),sha(b))
            finally:server.shutdown();server.server_close();thread.join()
def main():
    from graph_core.mob1_20261102.test_private import PrivateTests
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(CacheTests),unittest.defaultTestLoader.loadTestsFromTestCase(HTTPGate),unittest.defaultTestLoader.loadTestsFromTestCase(PrivateTests)])
    stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);write(WORK/'tests.log',stream.getvalue().encode());report=dict(status='PASS' if r.wasSuccessful() else 'FAIL',unique_methods=r.testsRun,new_methods=13,necessary_owner_regression_methods=7,synthetic_core_calls=CALLS,real_market_core_calls_in_unit_suite=0,failures=len(r.failures),errors=len(r.errors));write(WORK/'tests-private.json',encode(report));print(stream.getvalue());print(json.dumps(report));raise SystemExit(not r.wasSuccessful())
if __name__=='__main__':main()
