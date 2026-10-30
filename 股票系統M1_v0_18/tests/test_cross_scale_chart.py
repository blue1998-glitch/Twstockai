"""Exact fixed-artifact projection, not new recognition or manual-answer fitting."""
from copy import deepcopy
import unittest
from unittest.mock import patch
from graph_core.core import fingerprint
from cross_scale_chart.build import load_fixed,make


class CrossScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source,cls.diagnostic=load_fixed();cls.data=make(cls.source,cls.diagnostic)

    def test_real_source_all_values_and_original_core_preserved(self):
        for key in ['bars','macd','moving_averages','source','price_basis_id','core','source_gaps']:
            self.assertEqual(self.data[key],self.source[key])
        self.assertEqual(len(self.data['bars']),1213)
        self.assertEqual((self.data['bars'][0]['date'],self.data['bars'][-1]['date']),('2021-10-18','2026-10-16'))
        self.assertEqual(self.data['source_prefix_fingerprint'],fingerprint(self.data['bars']))

    def test_display_envelopes_from_full_real_wicks_not_pivots(self):
        from decimal import Decimal
        for l in self.data['layers']:
            selected=self.data['bars'][l['first_index']:l['last_index']+1];e=l['display_extent']
            self.assertEqual(e['source_rows_fingerprint'],fingerprint(selected))
            self.assertEqual(e['low'],min(selected,key=lambda r:Decimal(r['low']))['low'])
            self.assertEqual(e['high'],max(selected,key=lambda r:Decimal(r['high']))['high'])
            self.assertIsNone(l['formal_price_bounds']);self.assertIsNone(l['formal_membership'])

    def test_manual_month_context_and_exact39_are_not_engine_answers(self):
        major=next(l for l in self.data['layers'] if l['id']=='major')
        self.assertEqual(major['display_extent']['records'],463)
        self.assertIsNone(major['manual']['exact_start']);self.assertIsNone(major['manual']['exact_end'])
        self.assertEqual(major['date_markers'],[])
        previous=next(l for l in self.data['layers'] if l['id']=='manual39')
        self.assertEqual(previous['display_extent']['records'],39)
        self.assertEqual(previous['date_markers'],[{'kind':'MANUAL_WHOLE_END','date':'2025-06-02'}])
        self.assertFalse(self.data['core']['manual_case_inputs_used'])

    def test_rejected_run_margins_and_witness_ids_preserved(self):
        left=next(l for l in self.data['layers'] if l['id']=='left')['trace'];right=next(l for l in self.data['layers'] if l['id']=='right')['trace']
        for t in [left,right]:
            self.assertEqual(t,next(v for v in self.diagnostic['enumeration'] if v['id']==t['id']))
            self.assertEqual(t['decision'],'REJECTED_GEOMETRY')
        self.assertEqual(left['checks']['metrics']['high_cluster_spread'],'6.05')
        self.assertEqual(left['checks']['metrics']['allowed_cluster_spread'],'3.5700')
        self.assertEqual(left['checks']['metrics']['high_spread_margin'],'-2.4800')
        self.assertEqual(right['checks']['metrics']['low_cluster_spread'],'3.25')
        self.assertEqual(right['checks']['metrics']['allowed_cluster_spread'],'2.4675')
        self.assertEqual(right['checks']['metrics']['low_spread_margin'],'-0.7825')

    def test_same_geometry_date_semantics_and_relationships_not_merged(self):
        group=next(l for l in self.data['layers'] if l['id']=='same')
        self.assertEqual(group['display_extent']['records'],25)
        markers=group['date_markers']
        self.assertEqual([m['date'] for m in markers if m['kind']=='CONFIRMED'],['2025-05-14','2025-05-27'])
        self.assertTrue(all(m['date']=='2025-05-13' for m in markers if m['kind']=='SOURCE_LAST_TURN'))
        self.assertTrue(all(m['date']=='2025-06-02' for m in markers if m['kind']=='FIRST_OUTSIDE_RESEARCH_CLOSE'))
        self.assertIsNone(self.data['diagnostics']['summary']['independent_pattern_count'])
        for d in self.data['diagnostics']['selected_box_diagnostics']:
            self.assertEqual(d,next(v for v in self.diagnostic['boxes'] if v['box_id']==d['box_id']))
            self.assertIsNone(d['direct_successor_id'])

    def test_fixed_analysis_source_refused_if_mismatched(self):
        for key in ['bars','macd','source','price_basis_id','code','core']:
            s=deepcopy(self.source)
            if key=='bars':s['bars']=s['bars'][:-1]
            elif key=='macd':s['macd'][3]['date']='1990-01-01'
            elif key=='source':s['source']['id']='other'
            elif key=='code':s['code']='other'
            elif key=='core':s['core']['as_of']='2026-10-13'
            else:s[key]='other'
            with self.assertRaises(ValueError):make(s,self.diagnostic)

    def test_no_engine_call_or_input_mutation_during_projection(self):
        before=fingerprint(self.source)
        with patch('graph_core.core.analyze',side_effect=AssertionError('No engine execution')):
            self.assertEqual(make(self.source,self.diagnostic),self.data)
        self.assertEqual(before,fingerprint(self.source))
        self.assertTrue(self.data['provenance']['original_core_unchanged'])
        self.assertIsNone(self.data['core']['comparison']['primary_pressure_id'])


if __name__=='__main__':unittest.main()
