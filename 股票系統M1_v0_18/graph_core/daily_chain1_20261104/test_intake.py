"""Only synthetic source/IO controls; never fetch real sources or call core."""
import io,json,unittest,shutil,hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
from urllib.error import HTTPError
from . import intake as m
WORK=m.WORK
class Response(io.BytesIO):
    status=200
    def __init__(self,url,b):super().__init__(b);self.url=url;self.headers={'Content-Length':str(len(b))}
    def geturl(self):return self.url
class Fake:
    def __init__(self,data,*,denied=False,partial=False):self.data=data;self.calls=[];self.denied=denied;self.partial=partial
    def open(self,url,timeout):
        self.calls.append(url)
        if self.denied:raise HTTPError(url,403,'SYNTHETIC DENIAL',{},None)
        r=Response(url,self.data[url])
        if self.partial:
            old=r.read;counter=[0]
            def read(n):
                counter[0]+=1
                if counter[0]>1:raise OSError('SYNTHETIC INTERRUPTED BODY')
                return old(n)
            r.read=read
        return r
class GateTests(unittest.TestCase):
    def setUp(self):
        self.root=WORK/'synthetic-tests'/self._testMethodName;self.root.mkdir(parents=True,exist_ok=False)
        self.w=self.root/'stage';self.w.mkdir();(self.w/'baseline-private.json').write_text(json.dumps(dict(free_bytes=shutil.disk_usage(self.w).free)))
        (self.root/'lite1_20261103').mkdir();(self.root/'lite1_20261103/view-head-private.json').write_text('{"SYNTHETIC":"ONLY"}')
        (self.root/'graph_lazy1_20261104').mkdir();stocks=[dict(identity=x+':'+c,market=x,isin='SYNTHETIC-'+x) for x,c in [('TWSE','TESTA'),('TPEX','TESTB')]]
        (self.root/'graph_lazy1_20261104/source-state-private.json').write_text(json.dumps(dict(stocks=stocks)))
        self.patch=patch.multiple(m,BASE=self.root,ROOT=self.root/'SYNTHETIC_ROOT');self.patch.start();self.sleep=patch.object(m.time,'sleep',lambda _:None);self.sleep.start()
    def tearDown(self):self.sleep.stop();self.patch.stop()
    def data(self,dt='2026-11-04',other=None):
        values={}
        for market,lower,code in [('TWSE','twse','TESTA'),('TPEX','tpex','TESTB')]:
            day=other if market=='TPEX' and other else dt
            company={'公司代號':code,'公司簡稱':'合成甲'} if market=='TWSE' else {'SecuritiesCompanyCode':code,'CompanyAbbreviation':'合成乙'}
            row=dict(Date=day,**({'Code':code,'OpeningPrice':'21.0000','HighestPrice':'22','LowestPrice':'20','ClosingPrice':'21.5','TradeVolume':'123456'} if market=='TWSE' else {'SecuritiesCompanyCode':code,'Open':'21.0000','High':'22','Low':'20','Close':'21.5','TradingShares':'123456'}))
            html='最近更新日期:2026/11/04 CFICode<table><tr>'+''.join('<td>'+x+'</td>' for x in [code+' 合成','SYNTHETIC-'+market,'2020/01/02','上市' if market=='TWSE' else '上櫃','合成','ESVUFR','合成'])+'</tr></table>'
            values[m.d.URLS[lower+'-universe.json']]=m.d.encode([company]);values[m.d.URLS[lower+'-daily.json']]=m.d.encode([row]);values[m.d.URLS[market+'-classification.html']]=html.encode('cp950')
        return values
    def run_source(self,*,dt='2026-11-04',other=None,clock='2026-11-05T10:00:00+08:00',**options):
        f=Fake(self.data(dt,other),**options);r=m.run('2026-11-04',work=self.w,opener=f,now=datetime.fromisoformat(clock));return r,f
    def test_01_same_day_keeps_original_prior_closed_guard(self):
        r,f=self.run_source(clock='2026-11-04T23:59:00+08:00');self.assertIn('prior closed date',r['qualification']['reason']);self.assertEqual(r['processed_by_core'],0)
    def test_02_old_day_is_not_new_target(self):
        r,f=self.run_source(dt='2026-11-03');self.assertIn('SOURCE_DATE_NOT_TARGET',r['qualification']['reason']);self.assertFalse(r['new_batch_published'])
    def test_03_two_market_date_conflict_is_rejected(self):
        r,f=self.run_source(other='2026-11-03');self.assertIn('Markets have different dates',r['qualification']['reason'])
    def test_04_same_source_repeat_has_zero_network_core_and_writes(self):
        r,f=self.run_source();before={str(p):p.read_bytes() for p in self.w.rglob('*') if p.is_file()};again=m.run('2026-11-04',work=self.w,opener=Fake({},denied=True));self.assertEqual((again['this_execution_GETs'],again['this_execution_core_calls'],again['this_execution_new_outputs']),(0,0,0));self.assertEqual(before,{str(p):p.read_bytes() for p in self.w.rglob('*') if p.is_file()});self.assertEqual(r['status'],'BLOCKED_CONTINUITY_EVIDENCE')
    def test_05_corrupt_raw_refuses_repeat_without_new_request(self):
        r,f=self.run_source();(self.w/'capture/raw'/r['receipts'][0]['sha256']).write_bytes(b'SYNTHETIC TAMPER');f=Fake({})
        with self.assertRaises(ValueError):m.run('2026-11-04',work=self.w,opener=f)
        self.assertEqual(len(f.calls),0)
    def test_06_403_stops_remaining_requests_and_never_retries(self):
        r,f=self.run_source(denied=True);self.assertEqual(len(f.calls),1);self.assertEqual(r['source_GETs'],1);self.assertEqual(r['processed_by_core'],0);again=m.run('2026-11-04',work=self.w,opener=f);self.assertEqual(len(f.calls),1);self.assertTrue(again['reused'])
    def test_07_unknown_interrupted_attempt_is_not_retried(self):
        (self.w/'attempts').mkdir();(self.w/'attempts/0.json').write_text('{"SYNTHETIC":"ATTEMPT_UNKNOWN"}');r,f=self.run_source();self.assertEqual(len(f.calls),0);self.assertEqual(r['this_execution_GETs'],0);self.assertIsNone(r['source_GETs']);self.assertEqual(r['per_stock_gate_terminal_count'],2)
    def test_08_completed_receipts_resume_only_missing_requests(self):
        data=self.data();(self.w/'receipts').mkdir()
        for i,(name,url) in enumerate(list(m.d.URLS.items())[:2]):
            b=data[url];h=m.sha(b);m.write(self.w,self.w/'capture/raw'/h,b);r=dict(name=name,url=url,status='RECEIVED',sha256=h,bytes=len(b),fetched_at='SYNTHETIC');m.write(self.w,self.w/'receipts'/(str(i)+'.json'),m.d.encode(dict(receipt=r,trace=dict(name=name,url=url,complete=True,http_status=200))))
        r,f=self.run_source();self.assertEqual(len(f.calls),4);self.assertEqual(r['this_execution_GETs'],4);self.assertEqual(r['source_GETs'],6)
    def test_09_new_clock_does_not_rewrite_saved_rejection(self):
        r,f=self.run_source(clock='2026-11-04T23:59:00+08:00');a=m.run('2026-11-04',work=self.w,opener=f,now=datetime.fromisoformat('2026-11-06T10:00:00+08:00'));self.assertEqual(a['qualification_clock_taipei'],r['qualification_clock_taipei']);self.assertEqual(a['qualification'],r['qualification']);self.assertEqual(len(f.calls),6)
    def test_10_low_capacity_fails_before_get(self):
        f=Fake(self.data())
        with patch.object(m.shutil,'disk_usage',return_value=type('Usage',(),dict(free=m.RESERVE))()):
            with self.assertRaises(OSError):m.run('2026-11-04',work=self.w,opener=f)
        self.assertEqual(len(f.calls),0)
    def test_11_unknown_producer_without_archived_source_refuses(self):
        r,f=self.run_source();p=self.w/'binding-private.json';v=json.loads(p.read_bytes());v['producer_sha256']='0'*64;p.write_bytes(m.d.encode(v))
        with self.assertRaises(ValueError):m.run('2026-11-04',work=self.w,opener=f)
        self.assertEqual(len(f.calls),6)
    def test_12_incomplete_body_stops_and_keeps_unqualified_fragment(self):
        r,f=self.run_source(partial=True);self.assertEqual(len(f.calls),1);self.assertEqual(r['receipts'][0]['status'],'SOURCE_FAILURE');self.assertEqual(len(list((self.w/'partial-not-qualified').iterdir())),1);self.assertFalse(r['new_batch_published'])
if __name__=='__main__':unittest.main(verbosity=2)
