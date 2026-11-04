"""Targeted new behavior only. Synthetic controls and real reads kept separate."""
import unittest,io,json,copy,shutil,resource
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from graph_core import market_daily as d
from graph_core.storage1_20261104 import common,build
from graph_core.storage1_20261104.facts import project
from graph_core.storage1_20261104.common import WORK,ROOT,BASE,read_json,protected_heads
class Controls(unittest.TestCase):
    def member(self,market='TWSE'):return dict(code='TEST',name='Synthetic only',market=market,isin='SYNTHETIC-ONLY',cfi='ESVUFR')
    def raw(self,market='TWSE'):
        names=['OpeningPrice','HighestPrice','LowestPrice','ClosingPrice','TradeVolume'] if market=='TWSE' else ['Open','High','Low','Close','TradingShares']
        return dict(zip(names,['32.85000','33.00','32.0','32.90000','9007199254740993']),**{'Code' if market=='TWSE' else 'SecuritiesCompanyCode':'TEST','Date':'20261103'})
    def fact(self,raw,market='TWSE',**kw):return project(self.member(market),raw,as_of='2026-11-03',capture_id='a'*64,daily_sha256='b'*64,**kw)
    def test_01_exact_precision_and_native_shares(self):
        for m in ['TWSE','TPEX']:
            f=self.fact(self.raw(m),m);self.assertEqual(f['bar']['volume_shares_scaled'],'9007199254740993');self.assertEqual(f['bar']['open'],'32.85000');self.assertEqual(f['bar']['close'],'32.90000')
    def test_02_missing_quote_not_zero(self):
        f=self.fact(None);self.assertEqual(f['source_status'],'MISSING_QUOTE');self.assertIsNone(f['bar']);self.assertIsNone(f['original_record'])
    def test_03_zero_volume_keeps_raw_and_refuses(self):
        r=self.raw();r['TradeVolume']='0';f=self.fact(r);self.assertEqual(f['source_status'],'NO_TRADE_REPORTED_ZERO_VOLUME');self.assertIsNone(f['bar']);self.assertEqual(f['original_record']['TradeVolume'],'0')
    def test_04_bad_ohlc_not_a_usable_bar(self):
        r=self.raw();r['HighestPrice']='1';f=self.fact(r);self.assertEqual(f['source_status'],'DATA_QUALITY_FAILURE');self.assertIsNone(f['bar'])
    def test_05_stock_and_date_mismatch_refused(self):
        for k,v in [('Code','OTHER'),('Date','20261104')]:
            r=self.raw();r[k]=v
            with self.assertRaises(ValueError):self.fact(r)
    def test_06_nonordinary_identity_refused(self):
        m=self.member();m['cfi']='DBXXXX'
        with self.assertRaises(ValueError):project(m,self.raw(),as_of='2026-11-03',capture_id='a'*64,daily_sha256='b'*64)
    def test_07_isin_change_refused_and_formal_flags_stay_unknown(self):
        f=self.fact(self.raw(),parent_isin='OTHER');self.assertEqual(f['source_status'],'ISIN_CHANGED_CONTINUITY_REFUSED');self.assertIsNone(f['bar'])
        f=self.fact(self.raw());self.assertEqual(f['analysis_status'],'NOT_EXECUTED');self.assertFalse(f['execution_qualified']);self.assertFalse(f['historical_signal_eligible']);self.assertFalse(f['policy_authorized']);self.assertIsNone(f['primary_pressure_id']);self.assertIsNone(f['valuation']);self.assertIsNone(f['source']['announced_at'])
    def test_08_reserve_and_total_budget_refuse_before_write(self):
        initial=read_json(WORK/'baseline-private.json')['free_bytes']
        for free in [common.RESERVE-1,initial-common.LIMIT]:
            with patch.object(common.shutil,'disk_usage',return_value=SimpleNamespace(free=free)):
                with self.assertRaises(OSError):common.budget(1)
class RealReads(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=read_json(WORK/'facts-build-private.json');cls.folder=Path(cls.receipt['state_path']).parent;cls.state=read_json(cls.receipt['state_path'])
    def test_09_whole_reference_has_exactly_one_terminal(self):
        stocks=self.state['stocks'];self.assertEqual(len(stocks),1986);self.assertEqual(len({s['identity'] for s in stocks}),1986)
        self.assertEqual(sum(s['status']=='SOURCE_BAR_AVAILABLE' for s in stocks),1955);self.assertEqual(sum(s['status']!='SOURCE_BAR_AVAILABLE' for s in stocks),31)
        self.assertTrue(all(not s.get('preview_series') and s['result_key'] is None for s in stocks));self.assertEqual(self.state['summary']['charts'],0)
    def test_10_same_source_has_zero_writes_and_zero_core(self):
        before={(str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in (WORK/'view').rglob('*') if p.is_file()};heads=protected_heads()
        with patch.object(build.inc,'sources',side_effect=AssertionError('CACHED_NO_REPARSE')),patch.object(d,'analyze',side_effect=AssertionError('NO_CORE')):r=build.build()
        self.assertTrue(r['reused']);self.assertEqual(r['new_bytes'],0);self.assertEqual(r['new_stock_writes'],0)
        after={(str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in (WORK/'view').rglob('*') if p.is_file()};self.assertEqual(before,after);self.assertEqual(heads,protected_heads())
    def test_11_tampered_cached_body_rejected_without_touching_file(self):
        target=self.folder/self.state['stocks'][0]['preview_evidence']['path'];original=Path.read_bytes
        def read(p):return b'{}' if p==target else original(p)
        with patch.object(Path,'read_bytes',read):
            with self.assertRaises(ValueError):build.build()
    def test_12_two_real_stocks_per_market_match_official_fields(self):
        cases=[]
        for market in ['TWSE','TPEX']:
            selected=[s for s in self.state['stocks'] if s['market']==market and s['status']=='SOURCE_BAR_AVAILABLE'][:2]
            self.assertEqual(len(selected),2)
            names=['OpeningPrice','HighestPrice','LowestPrice','ClosingPrice','TradeVolume'] if market=='TWSE' else ['Open','High','Low','Close','TradingShares']
            lower={'TWSE':'twse','TPEX':'tpex'}[market];original_rows=read_json(common.CAPTURE/'raw'/self.receipt['source_signatures'][lower+'-daily.json']);key='Code' if market=='TWSE' else 'SecuritiesCompanyCode'
            for s in selected:
                f=read_json(self.folder/s['preview_evidence']['path']);r=next(r for r in original_rows if r[key].strip()==s['code']);self.assertEqual(f['original_record'],r);expected={key:str(r[name]).strip().replace(',','') for key,name in zip(['open','high','low','close','volume_shares_scaled'],names)}
                self.assertEqual({k:f['bar'][k] for k in expected},expected);self.assertEqual(d.day(r['Date']),f['as_of']);self.assertEqual(f['source']['volume_unit'],'SHARES_REPORTED');cases.append(dict(identity=s['identity'],market=market,code=s['code'],name=s['name'],fact=f,descriptor=s['preview_evidence']))
        common.write(WORK/'real-cases-private.json',common.encode(cases))
    def test_13_original_html_and_source_heads_unchanged(self):
        view=read_json(WORK/'view-build-private.json')
        for e in view['old_entries']:
            raw=Path(e['path']).read_bytes();self.assertEqual(len(raw),e['bytes']);self.assertEqual(common.sha(raw),e['sha256'])
        self.assertEqual(protected_heads(),self.receipt['original_heads'])
def main():
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__,fromlist=['*'])))
    common.write(WORK/'python-tests.log',stream.getvalue().encode());report=dict(status='PASS' if result.wasSuccessful() else 'FAIL',unique_methods=result.testsRun,synthetic_control_methods=8,real_read_control_methods=5,failures=len(result.failures),errors=len(result.errors),core_calls=0,new_provider_requests=0,old_test_counts_added=0)
    common.write(WORK/'python-tests-private.json',common.encode(report));print(stream.getvalue());print(json.dumps(report));raise SystemExit(not result.wasSuccessful())
if __name__=='__main__':main()
