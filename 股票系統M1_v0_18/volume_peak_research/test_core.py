"""New research tests. Synthetic engineering counterexamples are NOT market samples."""
from copy import deepcopy
from datetime import date, timedelta
from itertools import combinations
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from graph_core.core import fingerprint, number
from reaction_facts.core import BINDING, compare
from .core import INPUT, CONFIG_STATUS, evaluate
from .build import load


def fixture(volumes, current='20'):
    rows = [dict(date=(date(2000, 1, 1)+timedelta(days=i)).isoformat(),
                 open='10.00', high='11.00', low='9.00', close='10.00', volume_shares_scaled=v)
            for i, v in enumerate([*volumes, current])]
    context = dict(code='SYNTHETIC_NOT_MARKET', source_id='fixture-source', price_basis_id='fixture-raw',
                   source_frame_id='fixture-frame', source_prefix_fingerprint=fingerprint(rows),
                   price_mode='RAW_CANDIDATE', adjustment_version='NOT_APPLICABLE_RAW', volume_unit='SHARES_REPORTED')
    selection = {key: context[key] for key in ('code', 'source_id', 'price_basis_id', 'price_mode', 'adjustment_version', 'volume_unit')}
    selection.update(binding={key: context[key] for key in BINDING}, candidate_id='explicit-fixture',
                     member_dates=[r['date'] for r in rows[:-1]], member_fingerprint=fingerprint(rows[:-1]),
                     reference_known_on=rows[-2]['date'], actual_selected_at='2001-01-01T00:00:00+00:00',
                     qualification='RESEARCH_CANDIDATE', formal_price_bounds=None, formal_region_membership=None)
    return dict(schema_version=INPUT, as_of=rows[-1]['date'], context=context, selection=selection,
                bars=rows, known_gap_dates=[], basis_break_dates=[], limitations={'fixture':'SYNTHETIC_NOT_MARKET'})


def rebind(p, *, members=True):
    prefix=[r for r in p['bars'] if r['date'] <= p['as_of']]
    p['context']['source_prefix_fingerprint']=fingerprint(prefix)
    p['selection']['binding']={key:p['context'][key] for key in BINDING}
    if members:
        p['selection']['member_fingerprint']=fingerprint([r for r in prefix if r['date'] in p['selection']['member_dates']])
    return p


def run(p, k=1, r='1.15'):
    return evaluate(p, config=dict(k=k, r=r, qualification=CONFIG_STATUS))


class SyntheticResearch(unittest.TestCase):
    def test_all_ties_and_overlap_retained(self):
        o=run(fixture(['1','100','1','110','1','120','1']),r='1.10')
        self.assertEqual(len(o['highest_vote_group_ids']),2)
        self.assertEqual([g['vote_count'] for g in o['groups']],[2,2])
        self.assertEqual(len(o['overlap_pairs']),1)
        self.assertEqual(o['distinct_confirmed_peak_count'],3)
        self.assertIsNone(o['independent_reaction_count'])

    def test_full_span_not_adjacent_chain(self):
        o=run(fixture(['1','100','1','110','1','120','1','126','1']))
        self.assertEqual([(g['min_volume_shares'],g['max_volume_shares']) for g in o['groups']],[('100','110'),('110','126')])

    def test_all_maximal_groups_against_exhaustive_subset_oracle(self):
        o=run(fixture(['1','100','1','110','1','120','1','126','1']))
        peaks=o['peaks']; admissible=[]
        for size in range(1,len(peaks)+1):
            for subset in combinations(peaks,size):
                values=[number(p['original_bar']['volume_shares_scaled']) for p in subset]
                if max(values)<=min(values)*number('1.15'):
                    admissible.append(frozenset(p['date'] for p in subset))
        maximal={s for s in admissible if not any(s<t for t in admissible)}
        self.assertEqual({frozenset(g['member_dates']) for g in o['groups']},maximal)

    def test_all_equal_distant_peak_dates_retained(self):
        o=run(fixture(['1','100','1','100','1']),r='1')
        self.assertEqual(len(o['peaks']),2)
        self.assertEqual(o['groups'][0]['vote_count'],2)
        self.assertEqual(len(o['groups'][0]['min_dates']),2)

    def test_platform_refuses_without_first_day_choice(self):
        o=run(fixture(['1','100','100','1']))
        self.assertEqual(o['status'],'REFUSED_PLATFORM_AMBIGUITY')
        self.assertEqual([r['date'] for r in o['platform_ambiguities']],['2000-01-02','2000-01-03'])
        self.assertEqual(o['groups'],[])
        self.assertEqual(len(o['reference']['source_rows']),4)
        self.assertEqual(o['reference']['maximum']['max_single_day_dates'],['2000-01-02','2000-01-03'])

    def test_nearby_noncontiguous_equal_tops_also_refuse(self):
        o=run(fixture(['1','1','100','1','100','1','1']),k=2)
        self.assertEqual(o['status'],'REFUSED_PLATFORM_AMBIGUITY')
        self.assertEqual(len(o['platform_ambiguities']),2)

    def test_extreme_is_retained_as_peak_and_singleton(self):
        o=run(fixture(['1','100','1','1000000000','1']))
        self.assertIn('1000000000',[p['original_bar']['volume_shares_scaled'] for p in o['peaks']])
        self.assertIn(['2000-01-04'],[g['member_dates'] for g in o['groups']])
        self.assertEqual(o['reference']['maximum']['max_single_day_shares'],'1000000000')

    def test_zero_preserved_and_refused(self):
        o=run(fixture(['1','0','1']))
        self.assertIn('ZERO_SOURCE_VOLUME_UNDEFINED_PEAK_RESEARCH',o['reasons'])
        self.assertEqual(o['reference']['source_rows'][1]['volume_shares_scaled'],'0')
        self.assertEqual(o['groups'],[])

    def test_missing_volume_is_not_zero_or_partial_reference(self):
        o=run(fixture(['1',None,'1']))
        self.assertIn('MISSING_SOURCE_VOLUME',o['reasons'])
        self.assertIsNone(o['reference']['maximum'])
        self.assertIsNone(o['reference']['source_rows'][1]['volume_shares_scaled'])

    def test_negative_and_float_values_refused(self):
        for value in ['-1',1.25,'NaN']:
            with self.subTest(value=value):
                o=run(fixture(['1',value,'1']))
                self.assertEqual(o['status'],'REFUSED_SOURCE_EVIDENCE')

    def test_source_basis_version_unit_row_conflicts(self):
        for key,value in [('code','OTHER'),('source_id','OTHER'),('price_basis_id','OTHER'),
                          ('adjustment_version','OTHER'),('volume_unit','LOTS')]:
            with self.subTest(key=key):
                p=fixture(['1','10','1']);p['bars'][1][key]=value;rebind(p)
                self.assertIn('ROW_SOURCE_BASIS_VERSION_UNIT_CONFLICT',run(p)['reasons'])

    def test_binding_conflict_rejected(self):
        p=fixture(['1','10','1']);p['selection']['binding']['code']='OTHER'
        with self.assertRaisesRegex(ValueError,'binding conflict'):run(p)

    def test_prefix_fingerprint_tampering_rejected(self):
        p=fixture(['1','10','1']);p['bars'][1]['volume_shares_scaled']='11'
        with self.assertRaisesRegex(ValueError,'fingerprint'):run(p)

    def test_member_fingerprint_conflict_refuses(self):
        p=fixture(['1','10','1']);p['selection']['member_fingerprint']='wrong'
        self.assertIn('MEMBER_FINGERPRINT_CONFLICT',run(p)['reasons'])

    def test_exact_ratio_boundary(self):
        o=run(fixture(['1','100','1','115','1']))
        self.assertEqual(len(o['groups']),1)
        o=run(fixture(['1','100','1','115.0000000000000000000000000000001','1']))
        self.assertEqual(len(o['groups']),2)

    def test_long_precision_product_not_rounded(self):
        low='10000000000000000000000000000000000000000'
        high='11500000000000000000000000000000000000001'
        self.assertEqual(len(run(fixture(['1',low,'1',high,'1']))['groups']),2)

    def test_equal_current_and_exact_delta(self):
        o=run(fixture(['1','100','1'],current='100.000'))
        comparison=o['groups'][0]['comparisons']['to_max']
        self.assertEqual(comparison,compare('100.000','100'))
        self.assertEqual(comparison['relation'],'EQUAL')

    def test_current_zero_and_missing_preserved_refuse_comparison(self):
        for current in ['0',None]:
            p=fixture(['1','100','1'],current=current);o=run(p)
            self.assertIsNone(o['groups'][0]['comparisons']['to_max']['relation'])
            self.assertEqual(o['current_original_bar']['volume_shares_scaled'],current)

    def test_pending_right_and_confirmation_day(self):
        o=run(fixture(['1','10']))
        self.assertEqual(len(o['pending_peaks']),1)
        self.assertIsNone(o['pending_peaks'][0]['confirmed_on'])
        self.assertEqual(o['peaks'],[])
        confirmed=run(fixture(['1','10','1']))['peaks'][0]
        self.assertEqual(confirmed['date'],'2000-01-02')
        self.assertEqual(confirmed['confirmed_on'],'2000-01-03')

    def test_delayed_right_record_availability_distinct_from_record_date(self):
        p=fixture(['1','10','1']);p['bars'][2]['known_on']=p['as_of'];rebind(p)
        peak=run(p)['peaks'][0]
        self.assertEqual(peak['right_window_end_on'],'2000-01-03')
        self.assertEqual(peak['confirmed_on'],'2000-01-04')
        self.assertEqual(peak['known_on'],'2000-01-04')

    def test_maximum_comparison_independent_of_platform_refusal(self):
        o=run(fixture(['1','100','100','1'],current='110'))
        self.assertEqual(o['status'],'REFUSED_PLATFORM_AMBIGUITY')
        self.assertEqual(o['comparison_to_original_maximum'],compare('110','100'))

    def test_source_units_and_selection_mode_mismatch_rejected(self):
        p=fixture(['1','10','1']);p['context']['volume_unit']='LOTS'
        with self.assertRaisesRegex(ValueError,'SHARES_REPORTED'):run(p)
        p=fixture(['1','10','1']);p['selection']['adjustment_version']='OTHER'
        with self.assertRaisesRegex(ValueError,'source/basis/version'):run(p)

    def test_duplicate_and_unsorted_records_rejected(self):
        for duplicate in [True,False]:
            p=fixture(['1','10','1'])
            if duplicate:p['bars'].insert(1,deepcopy(p['bars'][1]))
            else:p['bars'][0],p['bars'][1]=p['bars'][1],p['bars'][0]
            rebind(p)
            with self.assertRaisesRegex(ValueError,'increasing'):run(p)

    def test_insufficient_left_not_borrowed_from_outside_members(self):
        o=run(fixture(['10','1','1']))
        self.assertEqual(o['peak_assessments'][0]['status'],'INSUFFICIENT_LEFT_RECORDS')

    def test_unknown_cutoff_hides_complete_reference(self):
        p=fixture(['1','100','1']);p['as_of']='2000-01-02';rebind(p,members=False)
        o=run(p)
        self.assertIsNone(o['reference']);self.assertEqual(o['groups'],[]);self.assertEqual(o['peaks'],[])

    def test_append_and_modify_future_do_not_change_entire_old_result(self):
        p=fixture(['1','10','1']);old=run(p)
        p['bars'].append(dict(date='2099-01-01',volume_shares_scaled='99999999999',price_basis_id='OTHER'))
        self.assertEqual(old,run(p))
        p['bars'][-1]['volume_shares_scaled']=None
        self.assertEqual(old,run(p))

    def test_known_date_delayed_or_impossible_refuses(self):
        for known in ['2099-01-01','1999-01-01']:
            p=fixture(['1','10','1']);p['bars'][1]['known_on']=known;rebind(p)
            self.assertIn('SOURCE_RECORD_INCOMPLETE_OR_NOT_YET_KNOWN',run(p)['reasons'])

    def test_gap_and_missing_member_refuse_not_partial_max(self):
        p=fixture(['1','10','1']);p['known_gap_dates']=['2000-01-02']
        self.assertIn('KNOWN_SOURCE_MEMBER_GAP',run(p)['reasons'])
        p=fixture(['1','10','1']);del p['bars'][1];rebind(p,members=False)
        self.assertIn('MISSING_OR_UNEXPECTED_EXPLICIT_MEMBER_DATES',run(p)['reasons'])

    def test_basis_break_and_post_reference_gap(self):
        p=fixture(['1','10','1']);p['basis_break_dates']=[p['as_of']]
        self.assertIn('BASIS_INTERRUPTION',run(p)['reasons'])
        p=fixture(['1','10','1']);p['known_gap_dates']=[p['as_of']]
        self.assertIsNone(run(p)['groups'][0]['comparisons']['to_max']['relation'])

    def test_only_explicit_member_anchor_is_proposal(self):
        p=fixture(['1','100','1','110','1']);group=run(p)['groups'][0]
        p['candidate_anchor']=dict(group_member_dates=group['member_dates'],date=group['member_dates'][0],actual_selected_at='2001-01-01T00:00:00Z')
        o=run(p);self.assertEqual(o['groups'][0]['candidate_anchor']['status'],'PROPOSAL_NOT_APPROVED')
        self.assertEqual(o['representative_volume_line'],dict(status='NOT_IMPLEMENTED',value=None))
        p['candidate_anchor']['date']='1999-01-01'
        o=run(p);self.assertIsNone(o['groups'][0]['candidate_anchor']);self.assertTrue(o['candidate_anchor_diagnostic'].startswith('REFUSED'))

    def test_no_config_default_and_invalid_probe_refused(self):
        p=fixture(['1','10','1'])
        for config in [{},dict(k=True,r='1.15',qualification=CONFIG_STATUS),dict(k=1,r=1.15,qualification=CONFIG_STATUS),dict(k=1,r='0.9',qualification=CONFIG_STATUS)]:
            with self.subTest(config=config),self.assertRaises(ValueError):evaluate(p,config=config)

    def test_input_immutable_and_no_product_flags_promoted(self):
        p=fixture(['1','10','1']);before=deepcopy(p);o=run(p)
        self.assertEqual(p,before)
        for key in ['execution_qualified','historical_signal_eligible','policy_authorized']:self.assertIs(o[key],False)
        for key in ['imputed_close','valuation','primary_pressure_id']:self.assertIsNone(o[key])
        self.assertIsNone(o['groups'][0]['candidate_anchor'])

    def test_pure_call_has_no_io_or_original_graph_analysis(self):
        p=fixture(['1','10','1'])
        with patch('builtins.open',side_effect=AssertionError('I/O forbidden')), \
             patch('graph_core.core.analyze',side_effect=AssertionError('Original analyze forbidden')):
            self.assertEqual(run(p)['status'],'RESEARCH_CANDIDATES_ONLY')


class RealSavedSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app=Path(__file__).resolve().parents[1]
        request=json.loads((app/'volume_peak_research/examples/request.json').read_bytes())
        cls.payload,cls.lineage=load(app/'pressure_chart/data/history-20261018/raw',
                                   app/'structure_state_chart/examples/band-volume-selection.json',request)

    def test_real_21_peaks_all_five_tied_seven_member_groups(self):
        o=run(self.payload,k=3);best=[g for g in o['groups'] if g['id'] in o['highest_vote_group_ids']]
        self.assertEqual(len(o['peaks']),21);self.assertEqual(len(o['reference']['source_rows']),155)
        self.assertEqual([(g['min_volume_shares'],g['max_volume_shares'],g['vote_count']) for g in best],
                         [('43882131','49699249',7),('44638336','50595969',7),('45105494','51860722',7),
                          ('46730970','52859340',7),('48157632','54198777',7)])
        self.assertEqual(best[-1]['member_dates'],['2025-11-28','2026-02-02','2026-03-05','2026-03-20','2026-05-29','2026-06-08','2026-07-01'])
        self.assertEqual(best[-1]['comparisons']['to_max']['delta'],'3239107')
        self.assertEqual(best[-1]['comparisons']['to_original_maximum']['delta'],'-40779250')
        self.assertEqual(o['reference']['maximum']['max_single_day_dates'],['2026-01-12'])
        self.assertTrue(any(g['max_volume_shares']=='98217134' for g in o['groups']))

    def test_true_source_scope_times_and_no_original_frame_impersonation(self):
        p=self.payload;o=run(p,k=3)
        self.assertEqual(o['reference']['reference_known_on'],'2026-09-01')
        self.assertNotEqual(p['context']['source_frame_id'],self.lineage['original_selection_binding']['source_frame_id'])
        self.assertEqual(o['reference']['calendar_qualification'],'EXPLICIT_SAVED_MEMBERS_NOT_COMPLETE_MARKET_CALENDAR')
        self.assertEqual(len(self.lineage['sources']),12)
        self.assertIsNone(self.lineage['sources'][2]['http_status'])

    def test_saved_raw_tamper_refused(self):
        app=Path(__file__).resolve().parents[1];request=json.loads((app/'volume_peak_research/examples/request.json').read_bytes())
        request['months']=['2025-11']
        with tempfile.TemporaryDirectory() as d:
            raw=app/'pressure_chart/data/history-20261018/raw'
            for suffix in ['.json','_meta.json']:
                name='1101_2025-11'+suffix;data=(raw/name).read_bytes()
                (Path(d)/name).write_bytes(data+b' ' if suffix=='.json' else data)
            with self.assertRaisesRegex(ValueError,'SHA mismatch'):
                load(d,app/'structure_state_chart/examples/band-volume-selection.json',request)

    def test_saved_meta_identity_or_status_conflict_refused(self):
        app=Path(__file__).resolve().parents[1];request=json.loads((app/'volume_peak_research/examples/request.json').read_bytes());request['months']=['2025-11']
        raw=app/'pressure_chart/data/history-20261018/raw';stem='1101_2025-11'
        for key,value in [('url','https://example.invalid/other'),('http_status',403)]:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as d:
                (Path(d)/(stem+'.json')).write_bytes((raw/(stem+'.json')).read_bytes())
                meta=json.loads((raw/(stem+'_meta.json')).read_bytes());meta[key]=value
                (Path(d)/(stem+'_meta.json')).write_text(json.dumps(meta))
                with self.assertRaisesRegex(ValueError,'URL/HTTP/identity'):
                    load(d,app/'structure_state_chart/examples/band-volume-selection.json',request)
