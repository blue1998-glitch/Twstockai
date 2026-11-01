from copy import deepcopy
from datetime import date,timedelta
from decimal import localcontext,ROUND_DOWN,Inexact
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from graph_core import market_history as h
from graph_core.market_daily import Journal
from graph_core.core import analyze


class HistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded=h.load_retained()

    def temporary_reference(self,root):
        # A small explicit current-reference cohort, not a fake historical universe.
        rows=[]
        for code,market in [('1101','TWSE'),('2884','TWSE'),('6488','TPEX'),('8069','TPEX'),('MISSING','TWSE')]:
            rows.append(dict(code=code,name='SYNTHETIC_REFERENCE_NAME',market=market,identity=market+':'+code,isin='SYNTHETIC-'+code,cfi='ESVUFR',listed_at='2000-01-01',registry_present=True))
        Journal(root/'runs').save('reference',dict(stocks=rows,as_of='2026-10-30'))

    def test_retained_parser_and_parent_have_full_original_precision(self):
        ledger,parent,spec=self.loaded
        with localcontext() as ctx:
            ctx.prec=3;ctx.rounding=ROUND_DOWN;ctx.traps[Inexact]=True
            guarded=h.load_retained()
            self.assertEqual(guarded[0],ledger)
            self.assertEqual(ctx.prec,3);self.assertTrue(ctx.traps[Inexact])
        for s in parent['history_series']:
            item=next(r for r in ledger['series'] if r['code']==s['code']);frame=s['frames'][-1]
            self.assertEqual(s['bases'][frame['chart_base']]['bars'],item['candles'])
            self.assertEqual(len(item['source_records']),61)
            self.assertEqual(len(item['candles']),1213 if s['code'] in ('1101','2884') else 1214)
        self.assertIn('2026-07-01',[r['date'] for r in spec['basis_warnings']['2884']])

    def test_complete_real_projection_checkpoint_resume_and_no_duplicate_core(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.temporary_reference(root)
            def stored_result(payload,as_of,expected):return expected
            # Storage/resume control uses existing real saved values; the separate
            # real run actually called core four times and is not counted here.
            with patch.object(h,'load_retained',return_value=self.loaded),patch.object(h,'checked_result',side_effect=stored_result):
                first=h.run(root,'reference')
            v=Journal(root/'runs').read(first['id'])['value'];self.assertEqual(v['summary']['terminal_counts'],{'ANALYZED_RETAINED_HISTORY':4,'HISTORY_SOURCE_UNAVAILABLE':1})
            for stock in v['stocks']:
                if not stock.get('result_key'):continue
                saved=Journal(root/'results').read(stock['result_key'])['value']
                source=next(s for s in self.loaded[0]['series'] if s['code']==stock['code'])
                self.assertEqual(stock['history_source_provenance']['retained_source_gaps'],{k:source[k] for k in ('known_calendar_missing_dates','calendar_status','actions_coverage','historical_publication_timing')})
                series=next(s for s in self.loaded[1]['history_series'] if s['code']==stock['code'])
                base=series['bases'][series['frames'][-1]['chart_base']]
                self.assertEqual(saved['retained_indicators']['macd'],base['macd'])
                self.assertEqual(saved['retained_indicators']['moving_averages'],base['moving_averages'])
                self.assertEqual(saved['indicators']['reset_dates'],saved['result']['data_gaps']['basis_resets'])
                for i,bar in enumerate(saved['input']['bars']):
                    if bar['date'] in saved['indicators']['reset_dates']:
                        self.assertIsNone(saved['indicators']['macd'][i]['histogram'])
                        self.assertTrue(all(values[i] is None for values in saved['indicators']['moving_averages'].values()))
            with patch.object(h,'load_retained',return_value=self.loaded),patch.object(h,'checked_result',side_effect=AssertionError('No duplicate core')):
                self.assertTrue(h.run(root,'reference')['reused'])
            # Simulate an interrupted final publication in a fresh root by copying
            # only the already committed immutable result/checkpoint records.
            import shutil
            other=root/'resume';other.mkdir();self.temporary_reference(other)
            for sub in ('histories','results','checkpoints'):shutil.copytree(root/sub,other/sub)
            with patch.object(h,'load_retained',return_value=self.loaded),patch.object(h,'checked_result',side_effect=AssertionError('Resume must use checked stock receipts')):
                resumed=h.run(other,'reference')
            self.assertEqual(resumed['new_core_calls'],0);self.assertEqual(resumed['summary']['terminal_counts'],v['summary']['terminal_counts'])
            missing=root/'missing-result';missing.mkdir();self.temporary_reference(missing)
            for sub in ('histories','checkpoints'):shutil.copytree(root/sub,missing/sub)
            with patch.object(h,'load_retained',return_value=self.loaded),patch.object(h,'checked_result',side_effect=AssertionError('Never repair missing result by recalculation')):
                refused=h.run(missing,'reference')
            self.assertEqual(refused['summary']['terminal_counts']['CHECKPOINT_DEPENDENCY_MISSING'],4)

    def test_wrong_date_and_one_stock_failure_are_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.temporary_reference(root)
            with patch.object(h,'load_retained',return_value=self.loaded):
                with self.assertRaises(ValueError):h.run(root,'reference','2026-10-30')
                def fail_one(payload,as_of,expected):
                    if payload['context']['code']=='1101':raise ValueError('SYNTHETIC_SOURCE_CONFLICT')
                    return expected
                with patch.object(h,'checked_result',side_effect=fail_one):r=h.run(root,'reference')
            self.assertEqual(r['summary']['terminal_counts']['HISTORY_SOURCE_OR_CORE_FAILURE'],1)
            self.assertEqual(r['summary']['terminal_counts']['ANALYZED_RETAINED_HISTORY'],3)

    def test_prefix_numeric_context_and_input_immutability(self):
        bars=[]
        values=[100,104,110,108,101,100,104,109,106,101,99,103,111,107,101,100]*3
        for i,n in enumerate(values):bars.append(dict(date=(date(2020,1,1)+timedelta(days=i)).isoformat(),open=str(n),high=str(n+1),low=str(n-1),close=str(n),volume_shares_scaled=str(1000+i)))
        p=dict(schema_version='graph-recognition-input/0.1',context=dict(code='SYNTHETIC_ONLY',source_id='synthetic',price_basis_id='synthetic-raw',price_mode='RAW_CANDIDATE',volume_unit='SHARES_REPORTED'),bars=bars,basis_break_dates=[bars[30]['date']])
        as_of=bars[25]['date'];expected=analyze(p,as_of=as_of);before=deepcopy(p)
        with localcontext() as ctx:
            ctx.prec=3;ctx.rounding=ROUND_DOWN;ctx.traps[Inexact]=True
            self.assertEqual(h.checked_result(p,as_of,expected),expected)
        self.assertEqual(p,before)
        for bar in p['bars'][26:]:bar['close']='INVALID_FUTURE'
        self.assertEqual(h.checked_result(p,as_of,expected),expected)
        bad=deepcopy(expected);bad['context']['source_id']='WRONG'
        with self.assertRaises(ValueError):h.checked_result(p,as_of,bad)
        full=before;last=full['bars'][-1]['date'];stopped=analyze(full,as_of=last)
        self.assertEqual(h.checked_result(full,last,stopped),stopped)
        boxes=[b for b in stopped['boxes'] if not b['usable_at_anchor']];self.assertTrue(boxes)
        self.assertTrue(all(b['pressure_distance_fraction'] is None for b in boxes))
        mixed=deepcopy(full);mixed['bars'][3]['price_basis_id']='MIXED'
        with self.assertRaises(ValueError):h.checked_result(mixed,last,stopped)


if __name__=='__main__':unittest.main()
