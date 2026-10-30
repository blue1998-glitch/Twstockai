"""Diagnostics must explain frozen results, never fit manual answers."""
from copy import deepcopy
from decimal import Decimal, localcontext
import unittest

from graph_core.core import analyze, _range, fingerprint
from graph_core_chart.build import display_ids
from graph_diagnostics.diagnose import diagnose, range_checks
from graph_diagnostics.build import load_html,PARENT,input_for
from test_graph_core import payload,OSC


class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.series=load_html(PARENT)['series'][0]
        cls.source=input_for(cls.series)
        cls.result=cls.series['results'][-1]
        cls.report=diagnose(cls.source,cls.result)

    def test_original_source_and_result_not_mutated(self):
        p=deepcopy(self.source);r=deepcopy(self.result)
        self.assertEqual(diagnose(p,r),self.report)
        self.assertEqual(p,self.source);self.assertEqual(r,self.result)
        self.assertFalse(self.report['core_modified']);self.assertFalse(self.report['manual_answers_used'])

    def test_every_trial_reason_parity_and_signed_margins(self):
        points={p['id']:p for p in self.result['pivots']}
        with localcontext() as ctx:
            ctx.prec=50
            for t in self.report['enumeration']:
                sl=t['source_turn_slice']
                seq=next(s['turn_ids'] for s in self.report['enumeration_scope']['source_turn_sequences'] if s['scale']==sl['scale'] and s['segment']==sl['segment'])
                p=[points[i] for i in seq[sl['start']:sl['end']+1]]
                self.assertEqual(p[0]['id'],t['first_turn_id']);self.assertEqual(p[-1]['id'],t['last_turn_id'])
                self.assertEqual(t['checks'],range_checks(p,Decimal('0.35')))
                self.assertEqual(t['checks']['passed'],_range(p,Decimal('0.35')) is not None)
                m=t['checks']['metrics']
                if 'HIGH_CLUSTER_SPREAD_EXCEEDS_RESEARCH_LIMIT' in t['checks']['failed_checks']:
                    self.assertLess(Decimal(m['high_spread_margin']),0)
                self.assertEqual(t['observed_at'],p[-1]['confirmed_at'])

    def test_emitted_order_and_valid_unselected_traces(self):
        ts=self.report['enumeration']
        self.assertEqual([t['box_id'] for t in ts if t['decision']=='EMITTED'],[b['id'] for b in self.result['boxes']])
        unselected=[t for t in ts if t['decision']=='VALID_NOT_SELECTED_BY_LONGEST_OR_FOUR_TURN_POLICY']
        self.assertTrue(unselected)
        for t in unselected:
            self.assertTrue(t['checks']['passed']);self.assertIsNone(t['box_id']);self.assertTrue(t['selected_alternative_ids'])

    def test_b77_actual_left_and_right_rejections_not_tuned(self):
        b=self.result['boxes'][76]
        left=[t for t in self.report['enumeration'] if t['scale']==b['scale'] and t['last_turn_id']==b['source_turn_ids'][-1] and t['first_index']<b['first_index']]
        self.assertTrue(left);self.assertTrue(all(t['decision']=='REJECTED_GEOMETRY' for t in left))
        right=[t for t in self.report['enumeration'] if t['scale']==b['scale'] and t['first_turn_id']==b['source_turn_ids'][0] and t['last_index']>b['last_index']]
        self.assertTrue(right);self.assertTrue(all(t['decision']=='REJECTED_GEOMETRY' for t in right))
        self.assertEqual(self.report['original_parameters'],self.result['parameters'])

    def test_same_geometry_different_confirmation_not_independent_votes(self):
        a,b=[self.report['boxes'][i] for i in (43,79)]
        self.assertEqual(a['same_geometry_group_id'],b['same_geometry_group_id'])
        self.assertIn(b['box_id'],a['same_geometry_other_ids'])
        self.assertNotEqual(a['windows']['date_semantics']['confirmed_at'],b['windows']['date_semantics']['confirmed_at'])
        self.assertIsNone(self.report['summary']['independent_pattern_count'])
        self.assertTrue(all(g['independent_pattern_votes'] is False for g in self.report['geometry_groups']))

    def test_prefix_version_edges_strictly_forward_and_not_local_suffix(self):
        byid={b['id']:b for b in self.result['boxes']}
        for e in self.report['source_prefix_version_edges']:
            a,b=byid[e['from_id']],byid[e['to_id']]
            self.assertLess(a['confirmed_at'],b['confirmed_at'])
            self.assertEqual(a['scale'],b['scale']);self.assertLess(a['turns'],b['turns'])
            self.assertEqual(b['source_turn_ids'][:a['turns']],a['source_turn_ids'])
        chain=[66,67,69,71,73,75,76]
        for a,b in zip(chain,chain[1:]):
            self.assertIn(self.result['boxes'][a]['id'],self.report['boxes'][b]['immediate_source_prefix_predecessor_ids'])
        self.assertIn(self.result['boxes'][87]['id'],self.report['boxes'][88]['local_subsequence_of_ids'])
        self.assertNotIn(self.result['boxes'][87]['id'],self.report['boxes'][88]['all_source_prefix_ancestor_ids'])

    def test_source_confirmation_exit_and_manual_endpoint_separate(self):
        for i,confirmed in [(43,'2025-05-14'),(79,'2025-05-27')]:
            t=self.report['boxes'][i]['windows']['date_semantics']
            self.assertEqual(t['source_last_turn'],'2025-05-13');self.assertEqual(t['confirmed_at'],confirmed)
            self.assertEqual(t['previous_observed_inside_record'],'2025-05-29')
            self.assertEqual(t['first_below_close_at'],'2025-06-02');self.assertIsNone(t['formal_whole_box_end'])
            self.assertIsNone(t['formal_membership'])

    def test_observation_lengths_and_broad_later_not_direct_successor(self):
        a,b=[self.report['boxes'][i] for i in (76,87)]
        self.assertNotEqual(a['windows']['path_observation']['records'],b['windows']['path_observation']['records'])
        self.assertEqual(len(a['later_after_breakdown']),32)
        for d in self.report['boxes']:
            self.assertIsNone(d['direct_successor_id'])
            for later in d['later_after_breakdown']:
                self.assertLess(d['windows']['date_semantics']['first_below_close_at'],later['source_start'])
                self.assertGreaterEqual(later['relation_observed_at'],later['confirmed_at'])

    def test_display_explanations_match_original_and_preserve_nonselected(self):
        self.assertEqual(self.report['presentation']['selected_ids'],display_ids(self.result)['ids'])
        for i in (43,79):
            d=self.report['boxes'][i]['default_display']
            self.assertFalse(d['selected']);self.assertTrue(d['original_dominated_by'])
            self.assertTrue(all(not c['selected'] for c in d['criteria']))

    def test_full_source_prefix_future_mutation_and_append_stability(self):
        p=payload(OSC*2);full=deepcopy(p);date=p['bars'][30]['date'];r=analyze(p,as_of=date);d=diagnose(p,r)
        q=deepcopy(p);q['bars']=q['bars'][:31]
        self.assertEqual(d,diagnose(q,analyze(q,as_of=date)))
        for row in p['bars'][31:]:row.update(open='999',high='1000',low='998',close='999')
        self.assertEqual(d,diagnose(p,analyze(p,as_of=date)))
        earlier={t['id']:t for t in d['enumeration']}
        later=diagnose(full,analyze(full,as_of=full['bars'][-1]['date']))
        self.assertGreater(len(later['enumeration']),len(earlier))
        for t in later['enumeration']:
            if t['id'] in earlier:self.assertEqual(t,earlier[t['id']])

    def test_event_and_anchor_volume_windows_exclude_current(self):
        windows=self.report['volume_observation_windows']
        self.assertIn(self.result['as_of'],windows)
        for day,v in windows.items():
            for count,w in v['previous_windows'].items():
                self.assertFalse(w['includes_observed_day'])
                if w['end']:self.assertLess(w['end'],day)
                self.assertLessEqual(w['records'],int(count))

    def test_exact_check_boundary_and_rejection_counterexamples(self):
        def points(values):return [dict(id=str(i),kind='HIGH' if i%2==0 else 'LOW',price=str(v)) for i,v in enumerate(values)]
        with localcontext() as ctx:
            ctx.prec=50
            accepted=range_checks(points([120,100,113,107]),Decimal('0.35'))
            self.assertTrue(accepted['passed']);self.assertEqual(accepted['metrics']['high_spread_margin'],'0.00')
            rejected=range_checks(points([120,100,112.99,107]),Decimal('0.35'))
            self.assertIn('HIGH_CLUSTER_SPREAD_EXCEEDS_RESEARCH_LIMIT',rejected['failed_checks'])
            self.assertEqual(range_checks(points([120,100,113]),Decimal('0.35'))['first_failed_check'],'FEWER_THAN_TWO_LOWS')

    def test_missing_price_volume_calendar_and_basis_stop_windows(self):
        p=payload(OSC*3,missing_volume=(12,));p['basis_break_dates']=[p['bars'][37]['date']]
        for k in ('open','high','low','close'):p['bars'][25][k]=None
        p['expected_dates']=[r['date'] for r in p['bars']];del p['bars'][55]
        r=analyze(p,as_of=p['bars'][-1]['date']);d=diagnose(p,r)
        self.assertTrue(d['enumeration'])
        for b in d['boxes']:
            w=b['windows']['path_observation']
            if w['stopped_at']:self.assertLess(w['end'],w['stopped_at'])
        self.assertTrue(any(b['windows']['source_volume_window']['missing_dates'] for b in d['boxes']))

    def test_identity_tampering_and_manual_answers_refused(self):
        r=deepcopy(self.result);r['boxes'][0]['start']='2000-01-01'
        with self.assertRaises(ValueError):diagnose(self.source,r)
        p=deepcopy(self.source);p['context']['source_id']='other-source'
        with self.assertRaises(ValueError):diagnose(p,self.result)
        p=deepcopy(self.source);p['manual_cases']=[]
        with self.assertRaises(ValueError):diagnose(p,self.result)


if __name__=='__main__':unittest.main()
