"""Real saved oracle + marked engineering boundaries; no market-sample counting."""
from copy import deepcopy
from decimal import localcontext
import builtins,json,socket,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

from graph_core.core import fingerprint
from reaction_facts.band_volume import prepare,evaluate
from pressure_chart.facts import volume_facts

ROOT=Path(__file__).resolve().parents[1]


def fixture(volumes=('10','20','20','5','15')):
    bars=[dict(date=f'2000-01-{i+1:02}',open='10',high='11',low='9',close='10',volume_shares_scaled=v) for i,v in enumerate(volumes)]
    binding=dict(code='ENGINEERING_NOT_MARKET',source_id='synthetic',price_basis_id='test-raw',source_frame_id='later-frame',source_prefix_fingerprint=fingerprint(bars))
    context={**binding,'price_mode':'RAW_CANDIDATE','adjustment_version':'NOT_APPLICABLE_RAW','volume_unit':'SHARES_REPORTED'}
    stats=volume_facts(bars[:3]);selection=dict(binding=deepcopy(binding),price_mode='RAW_CANDIDATE',adjustment_version='NOT_APPLICABLE_RAW',candidate_id='fixture-box',member_dates=[r['date'] for r in bars[:3]],reference_known_on='2000-01-04',selected_at='2000-02-01T00:00:00+00:00',qualification='RESEARCH_CANDIDATE')
    box=dict(id='fixture-box',start='2000-01-01',source_end='2000-01-03',confirmed_at='2000-01-04',display_extent=dict(source_rows_fingerprint=fingerprint(bars[:3])),volume=dict(records=3,known_records=3,missing_dates=[],maximum=stats['max_single_day_shares'],maximum_dates=stats['max_single_day_dates']))
    return dict(schema_version='explicit-band-volume-input/0.1',engineering_fixture=True,context=context,bars=bars,selection=selection,candidate=box,known_gap_dates=[],basis_break_dates=[],limits={'fixture':'ENGINEERING_NOT_MARKET'})


def rebind(p):
    fp=fingerprint(p['bars']);p['context']['source_prefix_fingerprint']=fp;p['selection']['binding']['source_prefix_fingerprint']=fp


class ExplicitBandVolume(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'cross_scale_chart/generated/comparison-data.json').read_bytes())
        cls.selection=json.loads((ROOT/'structure_state_chart/examples/band-volume-selection.json').read_bytes())
        cls.real=prepare(cls.data,cls.selection)

    def test_real_complete_155_oracle_and_price_peak_is_different_day(self):
        out=evaluate(self.real,as_of='2026-10-16');r=out['reference']
        self.assertEqual((r['source_start'],r['source_end'],r['actual_records']),('2025-11-19','2026-07-14',155))
        self.assertEqual(r['max_single_day_shares'],'98217134');self.assertEqual(r['max_single_day_dates'],['2026-01-12'])
        self.assertEqual(out['current_volume_shares'],'57437884');self.assertEqual(out['comparison'],dict(relation='BELOW',delta='-40779250',reason='AVAILABLE'))
        self.assertEqual(r['maximum_original_bars'][0],next(x for x in self.data['bars'] if x['date']=='2026-01-12'))
        self.assertNotEqual(r['max_single_day_dates'],['2026-01-27']);self.assertIsNone(r['formal_price_bounds'])

    def test_ties_keep_all_original_ohlcv(self):
        p=fixture();r=evaluate(p,as_of='2000-01-05')['reference']
        self.assertEqual(r['max_single_day_dates'],['2000-01-02','2000-01-03'])
        self.assertEqual(r['maximum_original_bars'],p['bars'][1:3]);self.assertEqual(r['source_rows'],p['bars'][:3])

    def test_equal_is_not_above(self):
        o=evaluate(fixture(('10','20','20','5','20')),as_of='2000-01-05')
        self.assertEqual(o['comparison'],dict(relation='EQUAL',delta='0',reason='AVAILABLE'))

    def test_above_exact_delta(self):
        self.assertEqual(evaluate(fixture(('10','20','20','5','21')),as_of='2000-01-05')['comparison'],dict(relation='ABOVE',delta='1',reason='AVAILABLE'))

    def test_true_zero_not_missing(self):
        o=evaluate(fixture(('0','0','0','0','0')),as_of='2000-01-05')
        self.assertTrue(o['available']);self.assertEqual(o['comparison']['relation'],'EQUAL');self.assertEqual(len(o['reference']['max_single_day_dates']),3)

    def test_missing_volume_no_partial_maximum(self):
        p=fixture();p['bars'][0]['volume_shares_scaled']=None;rebind(p);o=evaluate(p,as_of='2000-01-05')
        self.assertIn('MISSING_SOURCE_VOLUME',o['reasons']);self.assertIsNone(o['reference']['max_single_day_shares']);self.assertEqual(o['reference']['maximum_original_bars'],[])

    def test_all_missing_no_zero_substitution(self):
        p=fixture()
        for row in p['bars'][:3]:row['volume_shares_scaled']=None
        rebind(p);o=evaluate(p,as_of='2000-01-05');self.assertFalse(o['available']);self.assertIsNone(o['reference']['max_single_day_shares'])

    def test_removed_member_date_explicit_and_count_preserved(self):
        p=fixture();p['bars'].pop(1);rebind(p);o=evaluate(p,as_of='2000-01-05')
        self.assertEqual(o['reference']['missing_member_dates'],['2000-01-02']);self.assertEqual(o['reference']['expected_records'],3);self.assertEqual(o['reference']['actual_records'],2);self.assertFalse(o['available'])

    def test_known_missing_calendar_day_refuses_full_source(self):
        p=fixture();p['known_gap_dates']=['2000-01-02'];o=evaluate(p,as_of='2000-01-05');self.assertIn('KNOWN_SOURCE_CALENDAR_GAPS',o['reasons']);self.assertIsNone(o['reference']['max_single_day_shares'])

    def test_basis_interruption_no_cross_basis_comparison(self):
        p=fixture();p['basis_break_dates']=['2000-01-03'];o=evaluate(p,as_of='2000-01-05');self.assertIn('BASIS_INTERRUPTION',o['reasons']);self.assertFalse(o['available'])

    def test_row_source_basis_or_version_conflict(self):
        for key in ['source_id','price_basis_id','price_mode','adjustment_version','code']:
            with self.subTest(key=key):
                p=fixture();p['bars'][1][key]='other';rebind(p);o=evaluate(p,as_of='2000-01-05');self.assertIn('ROW_SOURCE_BASIS_VERSION_CONFLICT',o['reasons']);self.assertFalse(o['available'])

    def test_not_yet_known_hides_entire_reference(self):
        o=evaluate(fixture(),as_of='2000-01-03');self.assertIsNone(o['reference']);self.assertIsNone(o['comparison']['relation']);self.assertEqual(o['reasons'],['REFERENCE_NOT_YET_KNOWN'])

    def test_real_candidate_end_is_not_confirmation(self):
        o=evaluate(self.real,as_of='2026-07-14');self.assertIsNone(o['reference']);self.assertEqual(o['comparison']['reason'],'REFERENCE_NOT_YET_KNOWN')

    def test_original_volume_day_confirmation_and_later_selection_separate(self):
        o=evaluate(self.real,as_of='2026-10-16');r=o['reference']
        self.assertNotEqual(r['max_single_day_dates'][0],r['candidate_confirmed_on']);self.assertEqual(r['candidate_confirmed_on'],'2026-09-01');self.assertEqual(r['selected_at'],self.selection['selected_at']);self.assertIsNone(o['historical_selection_time']);self.assertFalse(o['historical_signal_eligible'])

    def test_modified_future_values_do_not_rewrite_old_facts(self):
        p=fixture();old=evaluate(p,as_of='2000-01-04');p['bars'][-1].update(high='invalid-future',volume_shares_scaled='999999999999999');rebind(p);new=evaluate(p,as_of='2000-01-04')
        for key in ['reference','comparison','current_volume_shares','evaluated_prefix_fingerprint','reasons']:self.assertEqual(old[key],new[key])

    def test_appended_future_does_not_change_prior_reference_or_comparison(self):
        p=fixture();old=evaluate(p,as_of='2000-01-05');p['bars'].append(dict(p['bars'][-1],date='2000-01-06',volume_shares_scaled='999999999'));rebind(p);new=evaluate(p,as_of='2000-01-05')
        for key in ['reference','comparison','current_volume_shares','evaluated_prefix_fingerprint']:self.assertEqual(old[key],new[key])

    def test_source_fp_tampering_refused(self):
        p=fixture();p['bars'][-1]['volume_shares_scaled']='999'
        with self.assertRaisesRegex(ValueError,'source fingerprint'):evaluate(p,as_of='2000-01-05')

    def test_saved_candidate_stats_conflict_does_not_select_new_answer(self):
        p=fixture();p['candidate']['volume']['maximum']='30';o=evaluate(p,as_of='2000-01-05');self.assertIn('EXISTING_VOLUME_HELPERS_OR_SAVED_CANDIDATE_CONFLICT',o['reasons']);self.assertIsNone(o['reference']['max_single_day_shares'])

    def test_current_missing_volume_retains_qualified_reference_but_refuses_compare(self):
        p=fixture();p['bars'][-1]['volume_shares_scaled']=None;rebind(p);o=evaluate(p,as_of='2000-01-05');self.assertEqual(o['reference']['max_single_day_shares'],'20');self.assertEqual(o['comparison']['reason'],'MISSING_CURRENT_VOLUME')

    def test_delayed_source_member_unavailable(self):
        p=fixture();p['bars'][1]['known_on']='2000-01-06';rebind(p);p['candidate']['display_extent']['source_rows_fingerprint']=fingerprint(p['bars'][:3]);o=evaluate(p,as_of='2000-01-05');self.assertIn('SOURCE_MEMBERS_NOT_YET_KNOWN_OR_INCOMPLETE',o['reasons']);self.assertFalse(o['available'])

    def test_gap_between_reference_and_analysis_does_not_certify_continuity(self):
        p=fixture();p['known_gap_dates']=['2000-01-04'];o=evaluate(p,as_of='2000-01-05');self.assertEqual(o['reference']['max_single_day_shares'],'20');self.assertIn('GAP_BETWEEN_REFERENCE_AND_ANALYSIS',o['reasons']);self.assertFalse(o['available'])

    def test_old_gap_before_source_does_not_replace_source_scope(self):
        p=fixture();p['known_gap_dates']=['1999-12-30'];self.assertTrue(evaluate(p,as_of='2000-01-05')['available'])

    def test_precise_long_decimal_under_small_global_precision(self):
        p=fixture(('10','20.00000000000000000000000000001','20.00000000000000000000000000001','5','20.00000000000000000000000000002'))
        with localcontext() as c:
            c.prec=2;o=evaluate(p,as_of='2000-01-05')
        self.assertEqual(o['comparison']['relation'],'ABOVE');self.assertEqual(o['comparison']['delta'],'0.00000000000000000000000000001')

    def test_adapter_binding_mode_version_time_and_qualification_refused(self):
        changes=[('binding',{**self.selection['binding'],'source_id':'other'}),('price_mode','ADJUSTED_CANDIDATE'),('adjustment_version','other'),('selected_at',None),('qualification','HUMAN_CONFIRMED')]
        for key,value in changes:
            with self.subTest(key=key):
                choice=deepcopy(self.selection);choice[key]=value
                with self.assertRaises(ValueError):prepare(self.data,choice)

    def test_full_member_selection_required(self):
        choice=deepcopy(self.selection);choice['member_dates']=choice['member_dates'][1:]
        with self.assertRaisesRegex(ValueError,'Full candidate member'):prepare(self.data,choice)

    def test_no_input_mutation_io_indicator_or_core_evaluation(self):
        p=fixture();before=deepcopy(p)
        with patch('graph_core.core.analyze',side_effect=AssertionError('RECOGNITION')),patch('structure_state.core.evaluate',side_effect=AssertionError('P03')),patch.object(builtins,'open',side_effect=AssertionError('IO')),patch.object(socket,'socket',side_effect=AssertionError('NETWORK')):
            o=evaluate(p,as_of='2000-01-05')
        self.assertEqual(p,before);self.assertFalse(o['policy_authorized']);self.assertIsNone(o['primary_pressure_id']);self.assertEqual(o['representative_volume_line']['status'],'NOT_IMPLEMENTED')


if __name__=='__main__':unittest.main()
