"""Source-derived display geometry must not become formal strategy bounds."""
from copy import deepcopy
from decimal import Decimal
import unittest
from candle_region_chart.build import attach, load_parent, selection
from contracts import fingerprint
from candle_region_chart.extents import envelope, prepare
from region_chart.build import selection as old_selection


class CandleRegionExtentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = load_parent()
        cls.series = next(s for s in cls.parent['history_series'] if s['code'] == '1101')
        cls.frame = cls.series['frames'][-1]
        cls.layer = cls.parent['region_layers'][cls.series['key']][-1]
        cls.bars = cls.series['bases'][cls.frame['chart_base']]['bars']
        cls.display = prepare(cls.series,cls.frame,cls.layer)
        cls.g2 = cls.display['extents']['G2']

    def test_g2_actual_136_selected_wicks_not_canvas_or_representative_only(self):
        self.assertEqual((self.g2['first_source_date'],self.g2['last_source_date'],self.g2['included_source_bars']),('2023-01-16','2023-08-16',136))
        self.assertEqual(self.g2['price']['high'],'40.25')
        self.assertEqual(self.g2['price']['low'],'35.90')
        self.assertEqual(self.g2['price']['high_dates'],['2023-05-02'])
        self.assertEqual(self.g2['price']['low_dates'],['2023-01-17'])
        self.assertIsNone(self.g2['formal_price_bounds'])
        self.assertIsNone(self.g2['formal_volume_measure'])
        self.assertIsNone(self.display['total_volume'])

    def test_selected_endpoints_included_and_outside_extrema_excluded(self):
        a,b=self.g2['first_index'],self.g2['last_index']
        bars=deepcopy(self.bars)
        for i in (0,a-1,b+1,len(bars)-1):
            bars[i]['high']='999999';bars[i]['low']='0.00001';bars[i]['volume_shares_scaled']='999999999999'
        self.assertEqual(envelope(bars,a,b),self.g2)
        self.assertEqual(self.bars[a]['date'],'2023-01-16')
        self.assertEqual(self.bars[b]['date'],'2023-08-16')
        bars[a]['high']='41.010000000000000000001'
        bars[b]['low']='34.900000000000000000001'
        d=envelope(bars,a,b)
        self.assertEqual(d['price']['high'],bars[a]['high'])
        self.assertEqual(d['price']['low'],bars[b]['low'])
        self.assertEqual(d['price']['high_dates'],[bars[a]['date']])
        self.assertEqual(d['price']['low_dates'],[bars[b]['date']])

    def test_decimal_precision_and_wicks_not_open_close(self):
        rows=deepcopy(self.bars[:2])
        rows[0].update(low='35.900000000000000000002',high='40.250000000000000000001',open='36.00',close='36.10')
        rows[1].update(low='35.900000000000000000001',high='40.250000000000000000002',open='36.00',close='36.10')
        e=envelope(rows,0,1)
        self.assertEqual(e['price']['low'],rows[1]['low']);self.assertEqual(e['price']['high'],rows[1]['high'])

    def test_volume_encloses_actual_source_columns_not_sum_or_representative_volume(self):
        a,b=self.g2['first_index'],self.g2['last_index'];rows=self.bars[a:b+1]
        actual=max(rows,key=lambda r:Decimal(r['volume_shares_scaled']))
        self.assertEqual(self.g2['volume']['max_volume_shares_scaled'],actual['volume_shares_scaled'])
        self.assertEqual(self.g2['volume']['known_max_dates'],[r['date'] for r in rows if r['volume_shares_scaled']==actual['volume_shares_scaled']])
        self.assertEqual(self.g2['volume']['known_records'],136)
        self.assertNotEqual(Decimal(actual['volume_shares_scaled']),sum(Decimal(r['volume_shares_scaled']) for r in rows))

    def test_g1_month_anchor_is_approximate_and_left_edge_open(self):
        g1=self.display['extents']['G1']
        self.assertEqual(g1['uncertain_start_month'],'2023-09')
        self.assertEqual(g1['left_edge'],'OPEN_UNCERTAIN_MONTH_ANCHOR')
        self.assertTrue(g1['first_source_date'].startswith('2023-09'))
        self.assertEqual(g1['last_source_date'],'2024-01-19')
        self.assertIsNone(self.layer['regions'][0]['exact_start_date'])
        self.assertIsNone(self.layer['regions'][0]['bar_membership'])
        self.assertIsNone(g1['formal_bar_membership'])
        self.assertIsNone(g1['formal_price_bounds'])

    def test_c_right_not_closed_at_reading_window_or_all_later_data(self):
        self.assertIsNone(self.display['c_right_extent'])
        self.assertIn('NO_CLOSED_REGION',self.display['c_right_qualification'])
        self.assertIsNone(self.layer['regions'][2]['end_date'])

    def test_missing_volume_never_becomes_zero_or_known_envelope(self):
        rows=deepcopy(self.bars[:2]);rows[0]['volume_shares_scaled']=None;rows[1]['volume_shares_scaled']='0'
        v=envelope(rows,0,1)['volume']
        self.assertIsNone(v['max_volume_shares_scaled'])
        self.assertEqual(v['known_max_volume_shares_scaled'],'0')
        self.assertEqual(v['missing_dates'],[rows[0]['date']])
        self.assertEqual(v['true_zero_dates'],[rows[1]['date']])
        self.assertEqual(v['completeness'],'MISSING_NO_ENVELOPE')

    def test_all_missing_and_all_real_zero_are_distinct(self):
        rows=deepcopy(self.bars[:2])
        for r in rows:r['volume_shares_scaled']=None
        v=envelope(rows,0,1)['volume'];self.assertIsNone(v['known_max_volume_shares_scaled']);self.assertEqual(v['known_records'],0)
        for r in rows:r['volume_shares_scaled']='0'
        v=envelope(rows,0,1)['volume'];self.assertEqual(v['max_volume_shares_scaled'],'0');self.assertEqual(v['completeness'],'COMPLETE_SOURCE_ROWS')

    def test_source_rows_and_review_layer_not_mutated(self):
        before=fingerprint([self.series,self.frame,self.layer]);prepare(self.series,self.frame,self.layer)
        self.assertEqual(fingerprint([self.series,self.frame,self.layer]),before)
        a,b=self.g2['first_index'],self.g2['last_index']
        self.assertEqual(self.g2['selected_source_rows_fingerprint'],fingerprint(self.bars[a:b+1]))

    def test_reject_changed_source_prefix_and_binding(self):
        for field in ('source_id','frame_id','chart_base','analysis_as_of','code','price_mode'):
            layer=deepcopy(self.layer);layer[field]='wrong'
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'binding'):prepare(self.series,self.frame,layer)
        layer=deepcopy(self.layer);layer['data_prefix_fingerprint']='wrong'
        with self.assertRaisesRegex(ValueError,'prefix'):prepare(self.series,self.frame,layer)

    def test_no_display_layer_for_unmatched_frames(self):
        self.assertIsNone(prepare(self.series,self.series['frames'][-2],None))
        p=attach(self.parent)
        self.assertEqual(sum(v is not None for frames in p['candle_region_extents'].values() for v in frames),1)
        self.assertTrue(all(v is None for v in p['candle_region_extents'][self.series['key']][:-1]))

    def test_parent_every_old_field_and_old_download_values_preserved(self):
        p=attach(self.parent)
        for k,v in self.parent.items():
            if k not in ('schema_version','view_version','artifact_id'):self.assertEqual(p[k],v,k)
        key=self.series['key'];new=selection(p,key,self.frame['as_of']);old=old_selection(self.parent,key,self.frame['as_of'])
        self.assertEqual(new['schema_version'],'manual-region-chart-selection/0.2')
        self.assertEqual(new.pop('region_display'),self.display)
        for k,v in old.items():
            if k not in ('schema_version','view_version'):self.assertEqual(new[k],v,k)

    def test_reject_missing_or_reversed_wicks_and_nonfinite_numbers(self):
        for low,high in [(None,'40'),('41','40'),('NaN','40'),('35','Infinity')]:
            rows=deepcopy(self.bars[:2]);rows[0]['low']=low;rows[0]['high']=high
            with self.subTest(low=low,high=high),self.assertRaises(ValueError):envelope(rows,0,1)

    def test_reject_filled_formal_unknowns_and_changed_endpoint_indices(self):
        for field in ('price_bounds','exact_start_date'):
            layer=deepcopy(self.layer);layer['regions'][0][field]='filled'
            with self.assertRaisesRegex(ValueError,'Formal'):prepare(self.series,self.frame,layer)
        layer=deepcopy(self.layer);layer['regions'][1]['display']['start_index']+=1
        with self.assertRaisesRegex(ValueError,'endpoints'):prepare(self.series,self.frame,layer)

    def test_invalid_display_indices_and_negative_volume_rejected(self):
        for a,b in [(-1,2),(2,1),(0,len(self.bars))]:
            with self.assertRaises(ValueError):envelope(self.bars,a,b)
        rows=deepcopy(self.bars[:2]);rows[0]['volume_shares_scaled']='-1'
        with self.assertRaises(ValueError):envelope(rows,0,1)


if __name__=='__main__':unittest.main()
