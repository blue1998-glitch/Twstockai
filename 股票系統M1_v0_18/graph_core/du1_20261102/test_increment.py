"""Synthetic engineering controls, never market samples/performance evidence."""
from copy import deepcopy
from datetime import date,datetime,timedelta,timezone
import fcntl,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

from graph_core import market_increment as m
from graph_core.market_daily import import_saved
from graph_core.fm1_20261101.test_daily import sources
from graph_core.core import analyze


def seed_fixture(root):
    stocks=[]
    for market,code in [('TWSE','A'),('TPEX','B')]:
        bars=[]
        for i in range(65):
            d=(date(2026,10,29)-timedelta(days=64-i)).isoformat()
            v=10+[0,1,2,1,0,-1][i%6]
            bars.append(dict(date=d,open=str(v),high=str(v+1),low=str(v-1),close=str(v),volume_shares_scaled=str(100+i)))
        payload=dict(schema_version='graph-recognition-input/0.1',context=dict(code=code,exchange=market,
            source_id='SYNTHETIC_SOURCE',price_basis_id=code+'-SYNTHETIC_RAW',price_mode='RAW_CANDIDATE',volume_unit='SHARES_REPORTED'),
            bars=bars,basis_break_dates=[],expected_dates=[b['date'] for b in bars])
        r=analyze(payload,as_of=bars[-1]['date']);value=dict(input=payload,result=r)
        rk='fm3-result-'+m.digest(m.encode(value));hk='history-'+m.fingerprint(dict(bars=bars,basis_break_dates=[])).split(':')[1]
        m.Journal(root/'results').save(rk,value);m.Journal(root/'histories').save(hk,dict(bars=bars,basis_break_dates=[]))
        stocks.append(dict(identity=market+':'+code,code=code,name='SYNTHETIC '+code,market=market,isin=code+'-ISIN',
            status='ANALYZED_FINMIND_HISTORY',result_key=rk,history_key=hk))
    batch=dict(version='finmind-market-history/0.1',as_of='2026-10-29',stocks=stocks,observed_sessions=['2026-10-29'],
        summary=dict(processed=2,expected=2,as_of='2026-10-29'))
    m.Journal(root/'runs').save('synthetic-seed',batch)
    return 'synthetic-seed'


class IncrementTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'private';self.root.mkdir()
        self.input=self.base/'input';self.input.mkdir();self.seed=seed_fixture(self.root)
        self.now=datetime(2026,11,4,tzinfo=timezone.utc)
    def cap(self,dt='1151030',**kw):
        sources(self.input,dt=dt,**kw);return import_saved(self.input,self.root)
    def run_saved(self,cap=None,**kw):return m.process(self.root,cap or self.cap(),seed_run=kw.pop('seed_run',self.seed),now=self.now,**kw)
    def batch(self,r):return m.Journal(self.root/'runs').read(r['id'])['value']
    def files(self):return {str(p.relative_to(self.root)):m.digest(p.read_bytes()) for p in self.root.rglob('*') if p.is_file()}

    def test_retains_prefix_resets_indicators_and_old_evidence(self):
        before=self.files();r=self.run_saved();self.assertEqual(r['new_core_calls'],2)
        b=self.batch(r);self.assertEqual(b['summary']['continuous_new_interval_certified'],0)
        self.assertEqual(b['summary']['multiday_retained_by_market'],{'TWSE':1,'TPEX':1})
        from graph_core.market_preview import source_segment_ma
        for row in b['stocks']:
            v=m.stock_history(self.root,row,b);p=v['input'];self.assertEqual(len(p['bars']),66)
            self.assertEqual(p['basis_break_dates'],['2026-10-30']);self.assertIsNone(source_segment_ma(p['bars'],[65])['5'][-1])
            self.assertEqual(v['result']['comparison']['primary_pressure_id'],None)
        self.assertTrue(all(self.files()[p]==sha for p,sha in before.items()))

    def test_same_sources_repeat_zero_core_and_zero_file_changes(self):
        cap=self.cap();r=self.run_saved(cap);before=self.files()
        with patch.object(m,'analyze',side_effect=AssertionError('No reanalysis')):
            repeat=self.run_saved(cap,seed_run=r['id']);same_seed=self.run_saved(cap)
        self.assertEqual(repeat['id'],r['id']);self.assertEqual(same_seed['id'],r['id'])
        self.assertEqual(repeat['new_core_calls'],0);self.assertEqual(before,self.files())

    def test_source_revision_explicit_version_preserves_old(self):
        r=self.run_saved();before=self.files();cap=self.cap(close='10.5')
        with self.assertRaisesRegex(ValueError,'revision'):self.run_saved(cap,seed_run=r['id'])
        revised=self.run_saved(cap,seed_run=r['id'],correction_of=r['id'],correction_reason='SYNTHETIC official revision')
        self.assertNotEqual(r['id'],revised['id']);self.assertTrue(all(self.files()[p]==s for p,s in before.items()))
        for row in self.batch(revised)['stocks']:self.assertEqual(row['history_records'],66)

    def test_source_incomplete_mixed_date_same_day_and_tampering_refuse(self):
        cap=self.cap();p=self.root/'captures'/(cap+'.json');r=json.loads(p.read_bytes());raw=self.root/'raw'/r[0]['sha256'];original=raw.read_bytes();raw.write_bytes(b'CORRUPT')
        with self.assertRaisesRegex(ValueError,'bytes changed'):self.run_saved(cap)
        raw.write_bytes(original)  # synthetic fixture reset only, not product recovery
        cap=self.cap(dt='1151104')
        with self.assertRaisesRegex(ValueError,'prior closed'):self.run_saved(cap)
        sources(self.input,dt='1151030');p=self.input/'tpex-daily.json';q=json.loads(p.read_bytes());q[0]['Date']='1151029';p.write_bytes(m.encode(q))
        with self.assertRaisesRegex(ValueError,'different dates'):self.run_saved(import_saved(self.input,self.root))
        p.unlink()
        with self.assertRaisesRegex(ValueError,'incomplete'):self.run_saved(import_saved(self.input,self.root))

    def test_gap_zero_missing_invalid_stock_isolation(self):
        cap=self.cap(dt='1151102',zero=True);r=self.run_saved(cap);b=self.batch(r)
        self.assertEqual([s['status'] for s in b['stocks']],['NO_TRADE_REPORTED_ZERO_VOLUME','SEGMENTED_RESEARCH'])
        cap=self.cap(dt='1151102',missing=True);r=self.run_saved(cap);self.assertEqual(self.batch(r)['stocks'][0]['status'],'MISSING_QUOTE')
        sources(self.input,dt='1151102');p=self.input/'twse-daily.json';q=json.loads(p.read_bytes());q[0]['HighestPrice']='1';p.write_bytes(m.encode(q))
        b=self.batch(self.run_saved(import_saved(self.input,self.root)))
        self.assertEqual(b['stocks'][0]['status'],'DATA_QUALITY_FAILURE');self.assertEqual(b['stocks'][1]['status'],'SEGMENTED_RESEARCH')
        v=m.stock_history(self.root,b['stocks'][1],b);self.assertEqual(v['input']['bars'][-2]['date'],'2026-10-29')
        self.assertIn('2026-11-02',v['input']['basis_break_dates']);self.assertEqual(len(v['input']['bars']),66)

    def test_crash_resume_checkpoints_only_unfinished_stock(self):
        cap=self.cap();real=m.analyze;calls=[]
        def fail(p,**kw):
            calls.append(p['context']['code'])
            if len(calls)==2:raise OSError('SYNTHETIC infrastructure interruption')
            return real(p,**kw)
        with patch.object(m,'analyze',side_effect=fail),self.assertRaises(OSError):self.run_saved(cap)
        self.assertEqual(len(list((self.root/'du1-checkpoints').glob('*.json'))),1)
        with patch.object(m,'analyze',wraps=real) as run:r=self.run_saved(cap)
        self.assertEqual(run.call_count,1);self.assertEqual(r['new_core_calls'],1)

    def test_corrupt_seed_binding_is_refused_without_fallback(self):
        batch=m.seed(self.root,self.seed);row=batch['stocks'][0];p=m.Journal(self.root/'results').path(row['result_key'])
        v=json.loads(p.read_bytes());v['value']['input']['context']['code']='WRONG';p.write_bytes(m.encode(v))
        b=self.batch(self.run_saved());self.assertEqual(b['stocks'][0]['status'],'DATA_QUALITY_FAILURE')
        self.assertIsNone(b['stocks'][0]['result_key']);self.assertEqual(b['stocks'][1]['status'],'SEGMENTED_RESEARCH')

    def test_missing_seed_dependency_isolated_without_reconstruction(self):
        old=m.seed(self.root,self.seed)['stocks'][0]
        p=m.Journal(self.root/'results').path(old['result_key']);p.unlink()  # synthetic loss only
        b=self.batch(self.run_saved());self.assertEqual(b['stocks'][0]['status'],'DATA_QUALITY_FAILURE')
        self.assertEqual(b['stocks'][1]['status'],'SEGMENTED_RESEARCH');self.assertFalse(p.exists())

    def test_market_change_new_member_and_absence_terminal_no_history_merge(self):
        sources(self.input,dt='1151030')
        p=self.input/'TWSE-classification.html';p.write_bytes('最近更新日期:2026/11/01<table>CFICode<tr><td>C SYNTHETIC</td><td>C-ISIN</td><td>2020/01/01</td><td>上市</td><td></td><td>ESVUFR</td><td></td></tr></table>'.encode('cp950'))
        p=self.input/'tpex-universe.json';q=json.loads(p.read_bytes());q.append(dict(SecuritiesCompanyCode='A',CompanyAbbreviation='Moved'));p.write_bytes(m.encode(q))
        p=self.input/'TPEX-classification.html';s=p.read_bytes().decode('cp950');p.write_bytes(s.replace('</table>','<tr><td>A SYNTHETIC</td><td>A-ISIN</td><td>2020/01/01</td><td>上櫃</td><td></td><td>ESVUFR</td><td></td></tr></table>').encode('cp950'))
        p=self.input/'tpex-daily.json';q=json.loads(p.read_bytes());q.append(dict(q[0],SecuritiesCompanyCode='A'));p.write_bytes(m.encode(q))
        b=self.batch(self.run_saved(import_saved(self.input,self.root)))
        self.assertEqual(len(b['stocks']),3);self.assertEqual(b['removed_registry_entries'][0]['identity'],'TWSE:A')
        self.assertEqual(b['market_changes'][0]['new_identity'],'TPEX:A')
        self.assertEqual(next(s for s in b['stocks'] if s['identity']=='TPEX:A')['history_records'],1)
        self.assertEqual(next(s for s in b['stocks'] if s['identity']=='TWSE:C')['status'],'MISSING_QUOTE')

    def test_failure_keeps_last_head_and_finalized_preview_reuses(self):
        cap=self.cap();r=m.update(self.root,now=self.now,seed_run=self.seed,capture_id=cap)
        self.assertNotEqual(r.get('status'),'BLOCKED',r.get('reason'));head=(self.root/'current-increment-run.json').read_bytes();before=self.files()
        with patch.object(m,'analyze',side_effect=AssertionError('No repeated computation')):
            repeated=m.update(self.root,now=self.now,capture_id=cap)
        self.assertTrue(repeated['reused']);self.assertEqual(before,self.files())
        cap=self.cap(dt='1151102')
        with patch('graph_core.market_preview.build',side_effect=ValueError('SYNTHETIC preview failure')):
            fail=m.update(self.root,now=self.now,capture_id=cap)
        self.assertEqual(fail['status'],'BLOCKED');self.assertEqual(head,(self.root/'current-increment-run.json').read_bytes())
        with patch.object(m,'analyze',side_effect=AssertionError('Saved run must resume without computation')):
            fixed=m.update(self.root,now=self.now,capture_id=cap)
        self.assertFalse(fixed['head_unchanged']);self.assertTrue(Path(fixed['batch_index']).is_file())

    def test_capacity_refusal_preserves_original_files_and_never_computes(self):
        from types import SimpleNamespace
        cap=self.cap();before=self.files()
        with patch.object(m.shutil,'disk_usage',return_value=SimpleNamespace(free=0)),patch.object(m,'analyze',side_effect=AssertionError('No analysis on inadequate private capacity')):
            with self.assertRaisesRegex(OSError,'capacity'):self.run_saved(cap)
        self.assertEqual(before,self.files())

    def test_single_writer_no_second_capture(self):
        with (self.root/'daily.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with patch.object(m,'capture',side_effect=AssertionError('No duplicate capture')),self.assertRaises(BlockingIOError):
                m.update(self.root,now=self.now,seed_run=self.seed,fetch=True)

    def test_source_cutoff_no_future_append_or_future_rewrite(self):
        r=self.run_saved();before=self.files();cap=self.cap(dt='1151102')
        later=self.run_saved(cap,seed_run=r['id']);self.assertNotEqual(r['id'],later['id'])
        self.assertTrue(all(self.files()[p]==sha for p,sha in before.items()))
        with self.assertRaisesRegex(ValueError,'older'):self.run_saved(self.cap(dt='1151030'),seed_run=later['id'])

    def test_original_calendar_gap_survives_increment(self):
        batch=m.seed(self.root,self.seed);row=batch['stocks'][0]
        old=m.stock_history(self.root,row,batch);p=deepcopy(old['input']);missing=p['bars'].pop(10)['date']
        result=analyze(p,as_of=batch['as_of']);v=dict(input=p,result=result)
        rk='fm3-result-'+m.digest(m.encode(v));hk='history-'+m.fingerprint(dict(bars=p['bars'],basis_break_dates=[])).split(':')[1]
        m.Journal(self.root/'results').save(rk,v);m.Journal(self.root/'histories').save(hk,dict(bars=p['bars'],basis_break_dates=[]))
        row.update(result_key=rk,history_key=hk);m.Journal(self.root/'runs').save('synthetic-gap-seed',batch)
        b=self.batch(self.run_saved(seed_run='synthetic-gap-seed'));v=m.stock_history(self.root,b['stocks'][0],b)
        self.assertIn(missing,v['result']['data_gaps']['missing_expected_dates'])
        self.assertIn(p['bars'][10]['date'],v['result']['data_gaps']['basis_resets'])

    def test_blocked_batch_has_per_member_diagnostic_not_new_results(self):
        sources(self.input);(self.input/'tpex-daily.json').unlink();cap=import_saved(self.input,self.root)
        r=m.update(self.root,now=self.now,seed_run=self.seed,capture_id=cap)
        self.assertEqual(r['status'],'BLOCKED');d=r['terminal_diagnostic']
        self.assertEqual(d['terminals'],2);self.assertEqual(d['expected_by_market'],{'TWSE':1,'TPEX':1})
        self.assertTrue(all(s['result_key'] is None for s in d['stocks']))
        self.assertFalse((self.root/'current-increment-run.json').exists())

    def test_catalogue_tamper_refused(self):
        from graph_core_chart.mobile_private import batch_index
        r=m.update(self.root,now=self.now,seed_run=self.seed,capture_id=self.cap())
        p=Path(r['batch_index']);v=json.loads(p.read_bytes());v['batches'][0]['sha256']='0'*64;p.write_bytes(m.encode(v))
        with self.assertRaisesRegex(ValueError,'fingerprint'):batch_index(p)

    def test_running_private_service_reads_new_completed_head(self):
        from graph_core_chart.mobile_private import create_auth,make_server
        from urllib.request import Request,urlopen
        import threading,base64
        first=m.update(self.root,now=self.now,seed_run=self.seed,capture_id=self.cap())
        auth=self.base/'live-auth.json';create_auth(auth,'owner','SYNTHETIC-ONLY-PASSWORD')
        server=make_server(None,auth,head=self.root/'current-increment-run.json');t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        token=base64.b64encode(b'owner:SYNTHETIC-ONLY-PASSWORD').decode()
        req=Request('http://127.0.0.1:'+str(server.server_port)+'/batches',headers={'Authorization':'Basic '+token})
        try:
            self.assertIn(b'2026-10-30',urlopen(req).read())
            second=m.update(self.root,now=self.now,capture_id=self.cap(dt='1151102'))
            raw=urlopen(req).read();self.assertIn(b'2026-11-02',raw);self.assertIn(b'2026-10-30',raw)
            self.assertEqual(len(server.preview_summary['batches']),2)
        finally:server.shutdown();server.server_close();t.join()

    def test_lazy_preview_exact_results_and_batch_catalogue_auth(self):
        from graph_core_chart.mobile_private import preview_index,batch_index,create_auth,make_server
        from urllib.request import Request,urlopen
        from urllib.error import HTTPError
        import base64,threading
        first=m.update(self.root,now=self.now,seed_run=self.seed,capture_id=self.cap())
        second=m.update(self.root,now=self.now,capture_id=self.cap(dt='1151102'))
        page,files,summary,hashes=batch_index(second['batch_index']);self.assertEqual(len(summary['batches']),2)
        self.assertEqual(summary['charts'],2)
        auth=self.base/'auth.json';create_auth(auth,'testowner','SYNTHETIC-ONLY-PASSWORD')
        server=make_server(None,auth,batches=second['batch_index']);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            base='http://127.0.0.1:'+str(server.server_port)
            with self.assertRaises(HTTPError) as error:urlopen(base+'/batches')
            self.assertEqual(error.exception.code,401)
            token=base64.b64encode(b'testowner:SYNTHETIC-ONLY-PASSWORD').decode()
            for route,item in server.allowed_files.items():
                raw=urlopen(Request(base+'/'+route,headers={'Authorization':'Basic '+token})).read()
                self.assertEqual(m.digest(raw),item['sha256'])
            with self.assertRaises(HTTPError):urlopen(Request(base+'/../runs/secret.json',headers={'Authorization':'Basic '+token}))
        finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main(verbosity=2)
