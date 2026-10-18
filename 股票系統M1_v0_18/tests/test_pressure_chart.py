"""Source provenance, original OHLCV, causal interval facts and reviewed bindings."""
from copy import deepcopy
from decimal import Decimal,localcontext
import hashlib,json
from pathlib import Path
import unittest
from pressure_chart.history import ROOT,parse_month,months,url_for
from pressure_chart.facts import frame_facts,interval_facts,volume_facts,reviewed_layer,UNKNOWN
from pressure_chart.build import load_original,make,selection
from pressure_chart.history_adapter import validate_intake,series_from_intake

HERE=ROOT/'pressure_chart'
HISTORY=HERE/'data/history-20261018/history-candidate.json'

class OfficialMonthlyParserTests(unittest.TestCase):
    def test_native_twse_shares_no_scaling_and_explicit_no_price_row(self):
        p=json.loads((HERE/'fixtures/1101_2025-08.json').read_text());rows=parse_month(p,'1101','2025-08')
        self.assertNotIn('2025-08-13',[r['date'] for r in rows])
        self.assertTrue(any(r[0]=='114/08/13' and r[1]=='0' and r[3:7]==['--']*4 for r in p['data']))
        self.assertEqual(rows[0]['volume_shares_scaled'],p['data'][0][1].replace(',',''))
        self.assertTrue(all(Decimal(r['close'])>0 for r in rows))

    def test_tpex_thousand_share_unit_is_explicit_and_scaled_once(self):
        p=json.loads((HERE/'fixtures/6488_2024-12.json').read_text());rows=parse_month(p,'6488','2024-12')
        self.assertEqual(p['flagField'],'仟股');self.assertEqual(rows[0]['volume_shares_scaled'],'2906000')
        self.assertEqual(rows[0]['high'],'432.00')

    def test_wrong_stock_month_or_unsupported_unit_rejected(self):
        p=json.loads((HERE/'fixtures/6488_2024-12.json').read_text())
        with self.assertRaises(ValueError):parse_month(p,'8069','2024-12')
        with self.assertRaises(ValueError):parse_month(p,'6488','2025-12')
        p['flagField']='UNKNOWN'
        with self.assertRaises(ValueError):parse_month(p,'6488','2024-12')

    def test_positive_volume_without_prices_is_not_a_zero_price_candle(self):
        p=json.loads((HERE/'fixtures/1101_2025-08.json').read_text());r=next(r for r in p['data'] if r[0]=='114/08/13');r[1]='100'
        with self.assertRaises(ValueError):parse_month(p,'1101','2025-08')

    def test_five_year_month_manifest_and_real_official_destinations(self):
        m=list(months('2021-10-16','2026-10-16'));self.assertEqual(len(m),61);self.assertEqual((m[0],m[-1]),('2021-10','2026-10'))
        self.assertIn('www.twse.com.tw/exchangeReport/STOCK_DAY',url_for('1101','2026-10'))
        self.assertIn('www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock',url_for('6488','2021-10'))


class PressureFactsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=load_original();cls.s=next(s for s in cls.old['numbers']['series'] if s['code']=='1101' and s['price_mode']=='RAW_CANDIDATE')
        cls.f=cls.s['frames'][-1];cls.rows=cls.s['bases'][cls.f['chart_base']]['bars'];cls.basis=cls.f['chart_base']
        cls.kw=dict(code='1101',mode='RAW_CANDIDATE',basis_id=cls.basis,as_of='2026-09-30')

    def test_actual_wick_high_is_not_the_pivot_subset(self):
        f=interval_facts(self.rows,'2026-01-01','2026-01-31',**self.kw)
        self.assertEqual((f['high'],f['high_dates']),('26.95',['2026-01-27']))
        pivot=next(p for p in self.old['evidence'][self.s['key']][-1]['pivots'] if p['id']=='major:HIGH:2026-01-29:2026-01-29:3')
        self.assertEqual(pivot['price'],'26.85');self.assertGreater(Decimal(f['high']),Decimal(pivot['price']))

    def test_region_total_and_peak_day_not_confused(self):
        f=interval_facts(self.rows,'2026-08-01','2026-08-31',**self.kw)
        wanted=sum(int(r['volume_shares_scaled']) for r in self.rows if r['date'].startswith('2026-08'))
        self.assertEqual(f['volume']['total_shares'],str(wanted));self.assertEqual(f['volume']['max_single_day_shares'],'557094159')
        self.assertGreater(wanted,557094159);self.assertIsNone(f['unknown']['remaining_trapped_ownership'])

    def test_two_wall_dimensions_can_be_different_and_not_ranked(self):
        f=frame_facts(self.rows,**self.kw)
        self.assertEqual(f['price_wall_evidence']['dates'],['2026-01-27'])
        self.assertEqual(f['volume_wall_evidence']['max_single_day_dates'],['2026-08-31'])
        self.assertEqual(f['unknown'],UNKNOWN);self.assertNotIn('score',f)
        self.assertEqual(len(f['monthly_source_slices']),9)

    def test_original_daily_decline_path_kept_without_speed_classifier(self):
        f=interval_facts(self.rows,'2026-01-01','2026-01-31',**self.kw)
        self.assertEqual(f['elapsed_calendar_days'],243)
        self.assertEqual(f['elapsed_supplied_bars'],len([r for r in self.rows if r['date']>'2026-01-31']))
        self.assertEqual(f['after_interval']['speed_classification'],'UNKNOWN_NO_RAPID_OR_GRADUAL_THRESHOLD')
        self.assertEqual(f['after_interval']['path_to_index'],178)

    def test_missing_volume_stays_unknown_not_partial_maximum_proxy(self):
        rows=deepcopy(self.rows[:2]);rows[0]['volume_shares_scaled']=None
        f=volume_facts(rows);self.assertIsNone(f['total_shares']);self.assertEqual(f['missing_volume_dates'],[rows[0]['date']])
        self.assertEqual(f['known_volume_subtotal_shares'],rows[1]['volume_shares_scaled'])
        self.assertIsNone(f['max_single_day_shares'])
        self.assertEqual(f['max_single_day_dates'],[])

    def test_future_truncation_and_decimal_context_cannot_change_past_facts(self):
        prefix=self.rows[:100];kw={**self.kw,'as_of':prefix[-1]['date']}
        a=frame_facts(prefix,**kw)
        future=deepcopy(self.rows);future[100]['close']='999999.99'
        self.assertEqual(frame_facts(future[:100],**kw),a)
        with localcontext() as ctx:
            ctx.prec=7;self.assertEqual(frame_facts(prefix,**kw),a)
        self.assertTrue(all(e['date']<=kw['as_of'] for r in a['monthly_source_slices'] for e in r['close_events']))

    def test_open_source_slice_has_no_retrospectively_frozen_threshold(self):
        rows=self.rows[:40];f=interval_facts(rows,'2026-03-01','2026-03-31',**{**self.kw,'as_of':rows[-1]['date']})
        self.assertEqual(f['frozen_reference'],'OPEN_SLICE_NO_FIXED_THRESHOLD_EVENTS');self.assertEqual(f['close_events'],[])

    def test_review_requires_exact_source_snapshot_date_and_separates_review_time(self):
        case=json.loads((ROOT.parent/'docs/visual-discussion/20261018_1101_user_reviewed_case.json').read_text());ev=self.old['evidence'][self.s['key']][-1]
        layer=reviewed_layer(case,self.s,self.f,ev,self.rows)
        self.assertEqual(layer['focus_reference_states'][0]['close_relation'],'ABOVE')
        self.assertEqual(layer['focus_reference_states'][1]['close_relation'],'BELOW')
        self.assertEqual(layer['unknown']['volume_expansion_baseline'],None)
        self.assertGreater(layer['reviewed_at'][:10],layer['analysis_as_of'])
        other=deepcopy(self.s);other['source']['id']='different'
        self.assertIsNone(reviewed_layer(case,other,self.f,ev,self.rows))
        self.assertIsNone(reviewed_layer(case,self.s,self.s['frames'][-2],ev,self.rows))


class PressureRealHistoryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history=validate_intake(HISTORY);cls.p=make(HISTORY)

    def test_actual_five_year_sources_four_stocks_and_post_september(self):
        self.assertEqual(len(self.history['series']),4)
        for s in self.history['series']:
            self.assertEqual(len(s['source_records']),61);self.assertEqual(s['missing_months'],[])
            self.assertGreater(len(s['candles']),1100)
            self.assertEqual(s['actual_end'],'2026-10-16');self.assertLess(s['actual_start'],'2021-11-01')
            self.assertEqual(s['calendar_years_unverified'],[])

    def test_calendar_note_uses_cited_dates_not_last_trading_row_date(self):
        audit=json.loads(HISTORY.with_name('coverage-audit.json').read_text())
        dates=[r['date'] for r in audit['source_calendar_explicit_no_equity_trading_notes'] if r['date'].startswith('2023')]
        self.assertEqual(dates,['2023-01-18','2023-01-19'])
        self.assertTrue(all(r['unexpected_price_dates']==[] for r in audit['series']))

    def test_original_numbers_and_new_raw_indicator_versions(self):
        self.assertEqual(self.p['numbers'],load_original()['numbers'])
        for s in self.p['history_series']:
            self.assertIsNone(s['original_record_id']);self.assertEqual(s['price_mode'],'RAW_CANDIDATE')
            self.assertEqual(s['frames'][-1]['macd_version'],'macd-12-26-9-sma-seed/0.1')
            self.assertEqual(s['frames'][-1]['ma_version'],'daily-sma-0.1')
            self.assertEqual(self.p['evidence'][s['key']][-1]['pivots'],[])

    def test_all_daily_prefixes_and_sparse_details_never_use_future_detail(self):
        for s in self.p['history_series']:
            for f,w in zip(s['frames'],self.p['wall_frames'][s['key']]):
                self.assertEqual(f['as_of'],w['analysis_as_of']);self.assertEqual(w['all_supplied_prefix_bars'],f['index']+1)
                self.assertTrue(w['left_end'] is None or w['left_end']<f['as_of'])
                self.assertTrue(all(r['actual_end']<=f['as_of'] for r in w['monthly_source_slices']))
                if w['interval_detail_status'].startswith('NOT_EXPORTED'):self.assertEqual(w['monthly_source_slices'],[])

    def test_new_raw_curves_reuse_existing_numeric_engines_at_real_prefix(self):
        from moving_averages import curves
        from product_candidate.macd import macd
        for s in self.p['history_series']:
            f=s['frames'][900];b=s['bases'][f['chart_base']];rows=b['bars'][:901]
            self.assertEqual({k:v[:901] for k,v in b['moving_averages'].items()},curves(rows))
            resets=sorted({next(i for i,r in enumerate(rows) if r['date']>=e['effective_date']) for e in b['known_events'] if e['effective_date']<=rows[-1]['date']})
            self.assertEqual(b['macd'][:901],macd([r['close'] for r in rows],resets=resets))

    def test_1101_followup_only_after_breakout_and_no_invented_expansion(self):
        s=next(s for s in self.p['history_series'] if s['code']=='1101');f=s['frames'][-1];v=selection(self.p,s['key'],f['as_of']);follow=v['retrospective_followup']
        self.assertIsNone(v['saved_analysis']);self.assertIsNotNone(v['new_history_analysis'])
        self.assertTrue(all('2026-09-30'<r['date']<=f['as_of'] for r in follow['post_breakout_bars']))
        self.assertGreater(len(follow['post_breakout_bars']),0);self.assertEqual(follow['volume_expansion']['status'],'UNKNOWN')
        self.assertTrue(any(e['date']=='2026-09-30' for e in follow['references'][0]['close_events']))
        self.assertTrue(all(e['date']<=f['as_of'] for ref in follow['references'] for e in ref['close_events']))

    def test_no_case_leak_to_other_stock_or_unreviewed_past(self):
        for s in self.p['history_series']:
            for f,layer in zip(s['frames'],self.p['followup_layers'][s['key']]):
                if s['code']!='1101' or f['as_of']<'2026-09-30':self.assertIsNone(layer)

    def test_revised_source_conflict_not_overwritten(self):
        item=deepcopy(self.history['series'][0]);r=next(r for r in item['candles'] if r['date']=='2026-09-30');r['volume_shares_scaled']=str(int(r['volume_shares_scaled'])+1)
        with self.assertRaisesRegex(ValueError,'conflicts'):series_from_intake(item,self.p['numbers']['series'])

if __name__=='__main__':unittest.main()
