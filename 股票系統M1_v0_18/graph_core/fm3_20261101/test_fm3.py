"""Synthetic controls only; real raw and full results are Git-external."""
from copy import deepcopy
from datetime import date,timedelta
from decimal import localcontext,Inexact,ROUND_DOWN
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from graph_core import market_finmind as f
from graph_core.finmind_adapter import history_payload,IntakeError
from graph_core.core import analyze
from graph_core.market_daily import Journal


def fixture():
    rows=[]
    for i in range(65):
        d=(date(2020,1,1)+timedelta(days=i)).isoformat();v=100+[0,3,8,4,-2,1][i%6]
        rows.append(dict(date=d,stock_id='SYNTHETIC',open=str(v),max=str(v+1),min=str(v-1),close=str(v),Trading_Volume=1000+i))
    m=dict(code='SYNTHETIC',market='TPEX',identity='TPEX:SYNTHETIC',cfi='ESVUFR',listed_at='2010-01-01')
    j=dict(schema_version='finmind-history-request/0.1',member=m,start_date=rows[0]['date'],end_date=rows[-1]['date'],as_of=rows[-1]['date'],retrieved_at='2021-01-01T00:00:00+08:00',expected_dates=[r['date'] for r in rows],basis_warnings=[])
    return dict(status=200,data=rows),j


class FM3Tests(unittest.TestCase):
    def test_exact_native_mapping_and_original_core(self):
        r,j=fixture();old=deepcopy((r,j));p=history_payload(r,j)
        self.assertEqual(p['bars'][0]['volume_shares_scaled'],'1000')
        self.assertEqual(p['context']['exchange'],'TPEX');self.assertIsNone(p['bars'][0]['available_at'])
        self.assertEqual(old,(r,j));result=analyze(p,as_of=j['as_of']);self.assertEqual(result['source_records'],65)
        self.assertIsNone(result['comparison']['primary_pressure_id'])

    def test_bad_source_identity_basis_volume_date_ohlc_and_role_refuse(self):
        r,j=fixture()
        for field,value in [('stock_id','WRONG'),('source_id','WRONG'),('price_basis_id','WRONG'),('Trading_Volume',None),('Trading_Volume','1.1'),('max','1'),('date','not-date')]:
            b=deepcopy(r);b['data'][2][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(IntakeError):history_payload(b,j)
        b=deepcopy(j);b['member']['cfi']='ETF'
        with self.assertRaises(IntakeError):history_payload(r,b)
        b=deepcopy(r);b['data'].insert(1,b['data'][0])
        with self.assertRaises(IntakeError):history_payload(b,j)

    def test_known_gap_and_basis_reset_without_fabricating_bars(self):
        r,j=fixture();absent=r['data'].pop(20)['date'];j['basis_warnings']=[dict(date=r['data'][40]['date'],source_id='synthetic-source',kind='NON_COMPARABLE_MARKER_EVENT_TYPE_UNKNOWN')]
        p=history_payload(r,j);result=analyze(p,as_of=j['as_of'])
        self.assertIn(absent,result['data_gaps']['missing_expected_dates'])
        self.assertIn(r['data'][20]['date'],result['data_gaps']['basis_resets']);self.assertEqual(len(p['bars']),64)
        self.assertIn(r['data'][40]['date'],result['data_gaps']['basis_resets'])
        self.assertIn('UNKNOWN',p['context']['corporate_action_comparability'])

    def test_prefix_future_change_and_fixed_numeric_environment(self):
        r,j=fixture();j['as_of']=r['data'][40]['date'];j['expected_dates']=j['expected_dates'][:41]
        p=history_payload(r,j);q=deepcopy(r)
        for row in q['data'][41:]:row['close']='INVALID_FUTURE'
        self.assertEqual(p,history_payload(q,j))
        with localcontext() as ctx:
            ctx.prec=3;ctx.rounding=ROUND_DOWN;ctx.traps[Inexact]=True
            self.assertEqual(p,history_payload(r,j));self.assertEqual(ctx.prec,3)

    def test_short_history_zero_volume_and_missing_anchor_remain_explicit(self):
        r,j=fixture();r['data']=r['data'][-1:];r['data'][0]['Trading_Volume']=0
        self.assertEqual(history_payload(r,j)['bars'][0]['volume_shares_scaled'],'0')
        r['data']=[]
        with self.assertRaisesRegex(IntakeError,'HISTORY_UNAVAILABLE'):history_payload(r,j)
        r,j=fixture();r['data'].pop()
        with self.assertRaisesRegex(IntakeError,'MISSING_ANCHOR_QUOTE'):history_payload(r,j)

    def test_quota_reservation_cache_integrity_and_no_paid_route(self):
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,n):return b'{"status":200,"data":[]}'
        with tempfile.TemporaryDirectory() as td:
            transport=unittest.mock.Mock(return_value=Response());s=f.FreeSource(td,limit=1,clock=lambda:10000,transport=transport,delay=0)
            params=dict(dataset='TaiwanStockPrice',data_id='SYNTHETIC')
            first=s.obtain(params);self.assertEqual(first,s.obtain(params));self.assertEqual(transport.call_count,1)
            with self.assertRaisesRegex(f.Pause,'BUDGET'):s.obtain(dict(params,data_id='SECOND'))
            with self.assertRaises(ValueError):s.obtain(dict(dataset='TaiwanStockPrice'))
            with self.assertRaises(ValueError):s.obtain(dict(dataset='PAID_DATASET'))
            receipt=first[1];(Path(td)/'source-raw'/receipt['sha256']).write_bytes(b'changed')
            with self.assertRaises(ValueError):s.obtain(params)

    def test_denial_and_crash_never_retry_same_request(self):
        with tempfile.TemporaryDirectory() as td:
            transport=unittest.mock.Mock(side_effect=HTTPError('synthetic',429,'rate',None,None));s=f.FreeSource(td,transport=transport,delay=0);p=dict(dataset='TaiwanStockPrice',data_id='SYNTHETIC')
            for _ in range(2):
                with self.assertRaises(f.Pause):s.obtain(p)
            self.assertEqual(transport.call_count,1)
        with tempfile.TemporaryDirectory() as td:
            s=f.FreeSource(td,delay=0);key=f.capture_key(p);s.slots.save(key,dict(epoch=1,parameters=p))
            with self.assertRaisesRegex(f.Pause,'UNKNOWN'):s.obtain(p)

    def test_single_stock_failure_checkpoint_and_replay_isolation(self):
        r,j=fixture();member=dict(j['member'],name='SYNTHETIC',isin='SYNTHETIC',registry_present=True)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);stocks=[dict(member,code=c,identity='TPEX:'+c) for c in ['GOOD','BAD','LATER']]
            ref=dict(as_of=j['as_of'],stocks=stocks,summary=dict(expected=3,expected_by_market={'TPEX':3}))
            Journal(root/'runs').save('reference',ref)
            def compute(root,ref,m,*a):
                if m['code']=='BAD':raise IntakeError('INVALID_VOLUME')
                return dict(status='INSUFFICIENT_HISTORY',history_records=1),None
            with patch.object(f,'observed_calendar',return_value=(j['expected_dates'],{})),patch.object(f,'analyze_stock',side_effect=compute):
                first=f.run(root,'reference',j['start_date']);second=f.run(root,'reference',j['start_date'])
                self.assertEqual(first,second);self.assertEqual(first['summary']['terminal_counts'],{'INSUFFICIENT_HISTORY':2,'DATA_QUALITY_REFUSED':1})
            with patch.object(f,'observed_calendar',return_value=(j['expected_dates'],{})),patch.object(f,'analyze_stock',side_effect=AssertionError('No replay computation')):
                self.assertEqual(f.run(root,'reference',j['start_date'])['new_core_calls'],0)

    def test_zero_placeholder_retains_null_gap_and_indicators_reset(self):
        r,j=fixture();r['data'][20].update(open=0,max=0,min=0,close=0,Trading_Volume=0)
        p=history_payload(r,j);self.assertIsNone(p['bars'][20]['close']);self.assertEqual(p['bars'][20]['volume_shares_scaled'],'0')
        result=analyze(p,as_of=j['as_of']);self.assertIn(p['bars'][20]['date'],result['data_gaps']['missing_price_rows'])
        from graph_core.market_preview import source_segment_ma
        ma=source_segment_ma(p['bars'],[]);self.assertIsNone(ma['5'][20]);self.assertIsNone(ma['5'][24]);self.assertIsNotNone(ma['5'][25])
        from moving_averages import curves
        self.assertEqual(source_segment_ma(p['bars'][:20],[]),curves(p['bars'][:20]))
        self.assertEqual(r['data'][20]['close'],0)

    def test_single_writer_lock_does_not_delete_other_writer_lock(self):
        with tempfile.TemporaryDirectory() as td:
            lock=Path(td)/'fm3-writer.lock';lock.write_text('SYNTHETIC-OTHER-WRITER')
            with self.assertRaises(FileExistsError):f.run(td,'reference','2020-01-01')
            self.assertEqual(lock.read_text(),'SYNTHETIC-OTHER-WRITER')

    def test_daily_opt_in_uses_existing_reference_run_and_preserves_official_head(self):
        from graph_core import daily_update as daily
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'current-run.json').write_text('{"id":"SYNTHETIC_OLD"}')
            result=dict(id='synthetic-new',summary={'status':'PARTIAL'})
            with patch.object(daily,'capture',return_value='synthetic-capture'),patch.object(daily,'process',side_effect=AssertionError('No duplicate single-day analysis')),patch.object(f,'reference',return_value='synthetic-reference') as ref,patch.object(f,'run',return_value=result) as run,patch.object(daily,'build',return_value={'status':'synthetic-preview'}):
                actual=daily.update(root,finmind_start='2020-01-01')
            self.assertEqual(actual['id'],'synthetic-new');self.assertEqual(json.loads((root/'current-run.json').read_text())['id'],'SYNTHETIC_OLD')
            self.assertEqual(json.loads((root/'current-finmind-run.json').read_text())['id'],'synthetic-new');ref.assert_called_once_with(root,'synthetic-capture');run.assert_called_once_with(root,'synthetic-reference','2020-01-01',limit=240)

    def test_continuation_waits_budget_without_requerying(self):
        from graph_core.fm3_20261101 import continue_batch as driver
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);Journal(root/'source-slots').save('slot',{'epoch':99})
            r={'id':'synthetic','summary':{'pause_reason':'LOCAL_FREE_HOURLY_BUDGET_EXHAUSTED'}}
            with patch.object(driver,'run',return_value=r) as run,patch.object(driver,'build',return_value={}),patch.object(driver.time,'time',return_value=100),patch.object(driver.time,'sleep',side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):driver.continue_batch(root,'synthetic','2020-01-01')
            self.assertEqual(run.call_count,1);self.assertEqual(json.loads((root/'fm3-continuation.json').read_text())['status'],'WAITING_CONSERVATIVE_FREE_BUDGET')
            self.assertFalse((root/'fm3-continuation.lock').exists())

    def test_continuation_provider_failure_stops_and_source_exception_is_recorded(self):
        from graph_core.fm3_20261101 import continue_batch as driver
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);r={'id':'synthetic','summary':{'pause_reason':'PROVIDER_OR_NETWORK_REFUSED_NO_RETRY'}}
            with patch.object(driver,'run',return_value=r) as run,patch.object(driver,'build',return_value={}),patch.object(driver.time,'sleep',side_effect=AssertionError('No retry')):
                driver.continue_batch(root,'synthetic','2020-01-01')
            self.assertEqual(run.call_count,1);self.assertEqual(json.loads((root/'fm3-continuation.json').read_text())['status'],'STOPPED_PROVIDER_OR_SOURCE')
        with tempfile.TemporaryDirectory() as td:
            with patch.object(driver,'run',side_effect=ValueError('SYNTHETIC_SOURCE_FAILURE')):
                driver.continue_batch(td,'synthetic','2020-01-01')
            self.assertEqual(json.loads((Path(td)/'fm3-continuation.json').read_text())['status'],'STOPPED_SOURCE_OR_EXECUTION')

    def test_git_tree_real_data_paths_refused(self):
        with self.assertRaises(IntakeError):f.FreeSource(Path(__file__).parent/'private')

if __name__=='__main__':unittest.main()
