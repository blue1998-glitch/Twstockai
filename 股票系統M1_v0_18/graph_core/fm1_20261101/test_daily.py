from copy import deepcopy
from datetime import datetime,timezone,date,timedelta
from decimal import localcontext,Inexact,ROUND_DOWN
import json
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from graph_core.market_daily import (classify,quote_map,candle,process,import_saved,Journal,URLS,encode,outside,digest)

HERE=Path(__file__).parent


def sources(folder,dt='1151029',close='11',zero=False,missing=False):
    fixture=json.loads((HERE/'synthetic-input-expected.json').read_text())
    for market,lower in [('TWSE','twse'),('TPEX','tpex')]:
        companies=fixture['universe'] if market=='TWSE' else fixture['tpex_universe']
        (folder/(lower+'-universe.json')).write_bytes(encode(companies))
        html='最近更新日期:2026/11/01<table><tr><td>CFICode</td></tr>'
        for code,label,cfi in fixture['html_rows'][market]:html+='<tr>'+''.join('<td>'+s+'</td>' for s in [code+' Synthetic',code+'-ISIN','2020/01/01',label,'',cfi,''])+'</tr>'
        (folder/(market+'-classification.html')).write_bytes((html+'</table>').encode('cp950'))
        if market=='TWSE':q=dict(Date=dt,Code='A',OpeningPrice='10',HighestPrice='12',LowestPrice='9',ClosingPrice=close,TradeVolume='0' if zero else '100',Change='0')
        else:q=dict(Date=dt,SecuritiesCompanyCode='B',Open='10',High='12',Low='9',Close=close,TradingShares='100',Change='0')
        rows=[q]
        if missing and market=='TWSE':rows=[dict(q,Code='OTHER_NON_MEMBER')]
        (folder/(lower+'-daily.json')).write_bytes(encode(rows))


class DailyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name);self.source=self.base/'input';self.source.mkdir();self.root=self.base/'runtime';sources(self.source)
    def capture(self):return import_saved(self.source,self.root)
    def read(self,r):return Journal(self.root/'runs').read(r['id'])['value']

    def test_ordinary_classification_includes_innovation_not_code_length(self):
        r=classify(json.loads((self.source/'twse-universe.json').read_text()),(self.source/'TWSE-classification.html').read_bytes(),'TWSE','2026-10-29')
        self.assertEqual([m['code'] for m in r['members']],['A']);self.assertEqual(r['classification_counts']['EXCLUDED_NON_ORDINARY'],1)
        self.assertEqual(r['historical_membership_at_as_of'],'UNKNOWN')

    def test_daily_validation_zero_missing_price_duplicates_and_dates(self):
        q=json.loads((self.source/'twse-daily.json').read_text())[0]
        self.assertEqual(candle(q,'TWSE')[0]['volume_shares_scaled'],'100')
        self.assertEqual(candle(dict(q,TradeVolume='0'),'TWSE')[1],'NO_TRADE_REPORTED_ZERO_VOLUME')
        self.assertEqual(candle(dict(q,ClosingPrice='--'),'TWSE')[0],None)
        for x in [dict(q,ClosingPrice='0'),dict(q,HighestPrice='1'),dict(q,TradeVolume='NaN')]:
            with self.assertRaises(Exception):candle(x,'TWSE')
        with self.assertRaises(ValueError):quote_map([q,q],'TWSE')
        with self.assertRaises(ValueError):quote_map([q,dict(q,Code='NEW',Date='1151030')],'TWSE')

    def test_core_calls_terminal_accounting_reuse_and_immutability(self):
        cap=self.capture();r=process(self.root,cap);self.assertEqual(r['new_core_calls'],2)
        v=self.read(r);self.assertEqual(v['summary']['terminal_counts'],{'INSUFFICIENT_HISTORY':2})
        before={p:p.read_bytes() for p in self.root.rglob('*.json')}
        with patch('graph_core.market_daily.analyze',side_effect=AssertionError('READ must not calculate')):
            again=process(self.root,cap,parent_run=r['id'])
        self.assertTrue(again['reused']);self.assertEqual(again['new_core_calls'],0)
        self.assertEqual(before,{p:p.read_bytes() for p in self.root.rglob('*.json')})
        old=deepcopy(v);old['version']='OLD_SYNTHETIC_PRODUCER'
        Journal(self.root/'runs').save('old-producer',old)
        with self.assertRaisesRegex(ValueError,'Cross-producer'):process(self.root,cap,parent_run='old-producer')

    def test_continuous_history_correction_preserves_old_versions(self):
        first=process(self.root,self.capture());old=Journal(self.root/'runs').path(first['id']).read_bytes()
        sources(self.source,dt='1151030');second=process(self.root,self.capture(),parent_run=first['id'])
        self.assertEqual(second['summary']['terminal_counts'],{'ANALYZED_RESEARCH':2})
        for stock in self.read(second)['stocks']:
            self.assertEqual(stock['history_records'],2)
            self.assertIsNone(Journal(self.root/'results').read(stock['result_key'])['value']['result']['comparison']['primary_pressure_id'])
        sources(self.source,dt='1151030',close='10');cap=self.capture()
        with self.assertRaises(ValueError):process(self.root,cap,parent_run=second['id'])
        revision=process(self.root,cap,parent_run=second['id'],correction_of=second['id'],correction_reason='SYNTHETIC_OFFICIAL_RESPONSE_REVISION')
        self.assertNotEqual(revision['id'],second['id']);self.assertEqual(Journal(self.root/'runs').path(first['id']).read_bytes(),old)

    def test_missing_quote_and_core_error_do_not_hide_other_stocks(self):
        sources(self.source,missing=True);r=process(self.root,self.capture());self.assertEqual(r['summary']['terminal_counts'],{'INSUFFICIENT_HISTORY':1,'MISSING_QUOTE':1})
        other=self.base/'other';real=__import__('graph_core.core',fromlist=['analyze']).analyze
        def fail_one(payload,**kwargs):
            if payload['context']['code']=='A':raise RuntimeError('SYNTHETIC_CORE_FAILURE')
            return real(payload,**kwargs)
        with patch('graph_core.market_daily.analyze',side_effect=fail_one):
            sources(self.source);cap=import_saved(self.source,other);r=process(other,cap)
        self.assertEqual(r['summary']['terminal_counts'],{'CORE_FAILURE':1,'INSUFFICIENT_HISTORY':1})
        self.assertEqual(r['summary']['processed'],r['summary']['expected'])

    def test_source_failure_unknown_universe_future_and_raw_tamper(self):
        (self.source/'tpex-daily.json').unlink();r=process(self.root,self.capture());self.assertEqual(r['summary']['terminal_counts'],{'INSUFFICIENT_HISTORY':1,'SOURCE_FAILURE':1})
        sources(self.source);cap=self.capture()
        with self.assertRaisesRegex(ValueError,'Completion'):process(self.root,cap,now=datetime(2026,10,29,tzinfo=timezone.utc))
        receipt=json.loads((self.root/'captures'/(cap+'.json')).read_text());q=next(x for x in receipt if x['name']=='twse-daily.json')
        (self.root/'raw'/q['sha256']).write_bytes(b'[]')
        with self.assertRaisesRegex(ValueError,'fingerprint'):process(self.root,cap)
        with self.assertRaises(ValueError):outside(HERE)

    def test_numeric_context_isolation_and_capture_does_not_mutate_input(self):
        cap=self.capture();seed=process(self.root,cap);parent=self.read(seed)
        # Explicit synthetic multi-record history forces non-terminating volume
        # ratios; a one-bar warmup would not detect inherited Inexact traps.
        bars=[]
        for i in range(30):
            value=[10,11,12,11,9,10][i%6]
            bars.append(dict(date=(date(2026,9,30)+timedelta(days=i)).isoformat(),open=str(value),high=str(value+1),low=str(value-1),close=str(value),volume_shares_scaled=str(100+i)))
        target=self.base/'different-context'
        for root in (self.root,target):
            Journal(root/'histories').save('synthetic-ratio-history',{'bars':bars,'basis_break_dates':[]})
            synthetic=deepcopy(parent)
            for s in synthetic['stocks']:s['history_key']='synthetic-ratio-history'
            Journal(root/'runs').save('synthetic-parent',synthetic)
        sources(self.source,dt='1151030');before={p:p.read_bytes() for p in self.source.iterdir()}
        normal=process(self.root,self.capture(),parent_run='synthetic-parent')
        with localcontext() as ctx:
            ctx.prec=3;ctx.rounding=ROUND_DOWN;ctx.Emax=9;ctx.Emin=-9;ctx.traps[Inexact]=True
            second=process(target,import_saved(self.source,target),parent_run='synthetic-parent')
            self.assertEqual(ctx.prec,3);self.assertTrue(ctx.traps[Inexact])
        first=self.read(normal);other=Journal(self.base/'different-context/runs').read(second['id'])['value']
        self.assertEqual([s['result_key'] for s in first['stocks']],[s['result_key'] for s in other['stocks']])
        self.assertEqual(normal['summary']['terminal_counts'],{'ANALYZED_RESEARCH':2})
        self.assertEqual(before,{p:p.read_bytes() for p in self.source.iterdir()})

    def test_prepared_coordinator_serializes_and_reuses_saved_run(self):
        from graph_core.daily_update import update
        cap=self.capture()
        with patch('graph_core.daily_update.capture',return_value=cap),patch('graph_core.daily_update.build',return_value={'status':'SYNTHETIC_PREVIEW'}):
            first=update(self.root)
            with patch('graph_core.market_daily.analyze',side_effect=AssertionError('No repeated core call')):
                second=update(self.root)
        self.assertEqual(first['id'],second['id']);self.assertTrue(second['reused'])
        self.assertEqual(json.loads((self.root/'current-run.json').read_text())['id'],first['id'])
        with patch('graph_core.daily_update.capture',return_value=cap),patch('graph_core.daily_update.process',side_effect=ValueError('Same-date updated registry, no new accepted session')):
            blocked=update(self.root)
        self.assertEqual(blocked['status'],'BLOCKED');self.assertTrue(blocked['head_unchanged']);self.assertFalse(blocked['new_capture_applied'])

    def test_unknown_registry_preserved_and_receipt_tampering_refused(self):
        (self.source/'tpex-universe.json').unlink();cap=self.capture();r=process(self.root,cap)
        self.assertIsNone(r['summary']['expected_by_market']['TPEX'])
        self.assertFalse(r['summary']['both_market_universes_read'])
        receipt=self.root/'captures'/(cap+'.json');receipt.write_text('[]')
        with self.assertRaisesRegex(ValueError,'receipt fingerprint'):process(self.root,cap)
        with self.assertRaisesRegex(ValueError,'identity'):process(self.root,'../../invalid')

    def test_market_change_observation_does_not_merge_price_histories(self):
        first=process(self.root,self.capture());sources(self.source,dt='1151030')
        file=self.source/'TWSE-classification.html';html=file.read_bytes().decode('cp950')
        file.write_bytes(re.sub(r'<tr><td>A Synthetic</td>.*?</tr>','',html).encode('cp950'))
        file=self.source/'tpex-universe.json';rows=json.loads(file.read_text());rows.append({'SecuritiesCompanyCode':'A','CompanyAbbreviation':'Synthetic moved'});file.write_bytes(encode(rows))
        file=self.source/'TPEX-classification.html';html=file.read_bytes().decode('cp950');extra='<tr>'+''.join('<td>'+s+'</td>' for s in ['A Synthetic','A-ISIN','2020/01/01','上櫃','','ESVUFR',''])+'</tr>';file.write_bytes((html+extra).encode('cp950'))
        file=self.source/'tpex-daily.json';rows=json.loads(file.read_text());rows.append(dict(rows[0],SecuritiesCompanyCode='A'));file.write_bytes(encode(rows))
        second=process(self.root,self.capture(),parent_run=first['id']);v=self.read(second)
        self.assertEqual(v['market_changes'][0]['old_identity'],'TWSE:A');self.assertEqual(v['market_changes'][0]['new_identity'],'TPEX:A')
        self.assertEqual(next(r for r in v['stocks'] if r['identity']=='TPEX:A')['history_records'],1)
        self.assertTrue(v['removed_registry_entries'])

    def test_preview_ma_does_not_bridge_known_basis_or_data_reset(self):
        from graph_core.market_preview import source_segment_ma
        from moving_averages import curves
        bars=[dict(date='2026-10-'+str(i+1).zfill(2),open='10',high='10',low='10',close='10',volume_shares_scaled='100') for i in range(10)]
        self.assertEqual(source_segment_ma(bars,[]),curves(bars))
        values=source_segment_ma(bars,[7])['5'];self.assertIsNotNone(values[6]);self.assertEqual(values[7:],[None,None,None])


if __name__=='__main__':unittest.main()
