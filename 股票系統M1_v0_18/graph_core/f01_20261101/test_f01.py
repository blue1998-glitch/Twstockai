"""F-01 targeted synthetic checks against frozen pre-fix observations."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from graph_core.core import analyze
from graph_core.f01_20261101.evidence import check_after, state, STOP

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]


class F01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {c['id']: c for c in json.loads((HERE/'cases.json').read_text())}
        cls.before = {c['id']: c for c in json.loads((HERE/'synthetic-before.json').read_text())['cases']}
        cls.results = {name: analyze(c['input'], as_of=c['as_of']) for name,c in cls.cases.items()}

    def assert_stopped_fields(self, name):
        result = self.results[name]
        old_boxes = [b for b in result['boxes'] if not b['usable_at_anchor']]
        stopped_refs = [r for r in result['reference_candidates']
                        if r['path']['last_relation']=='NOT_COMPARABLE_AFTER_GAP']
        self.assertTrue(old_boxes); self.assertTrue(stopped_refs)
        for box in old_boxes:
            self.assertIsNone(box['pressure_distance_fraction'])
            self.assertIsNone(box['relative_width_to_anchor'])
            self.assertEqual(box['anchor_comparison_reason'], STOP)
            self.assertEqual(box['anchor_relation'], 'NOT_COMPARABLE_AFTER_GAP')
            self.assertNotIn(box['id'], result['comparison']['relevant_pressure_ids'])
            self.assertNotIn(box['id'], result['comparison']['pareto_frontier_ids'])
            self.assertTrue(any(e['type']==STOP for e in box['path']['events']))
        for ref in stopped_refs:
            self.assertIsNone(ref['distance_to_anchor'])
            self.assertEqual(ref['anchor_comparison_reason'], STOP)
            self.assertTrue(any(e['type']==STOP for e in ref['path']['events']))

    def test_explicit_basis_break_nulls_only_stopped_objects(self):
        self.assert_stopped_fields('basis-break')
        r = self.results['basis-break']
        current_boxes = [b for b in r['boxes'] if b['usable_at_anchor']]
        current_refs = [p for p in r['reference_candidates']
                        if p['path']['last_relation']!='NOT_COMPARABLE_AFTER_GAP']
        self.assertTrue(current_boxes); self.assertTrue(current_refs)
        for box in current_boxes:
            self.assertIsNotNone(box['pressure_distance_fraction'])
            self.assertIsNotNone(box['relative_width_to_anchor'])
            self.assertIsNone(box['anchor_comparison_reason'])
        for ref in current_refs: self.assertIsNotNone(ref['distance_to_anchor'])

    def test_missing_price_preserves_history_but_nulls_anchor_distances(self):
        self.assert_stopped_fields('missing-price')
        day = self.cases['missing-price']['input']['bars'][29]['date']
        self.assertIn(day, self.results['missing-price']['data_gaps']['missing_price_rows'])

    def test_known_missing_session_preserves_gap_and_nulls_distances(self):
        self.assert_stopped_fields('missing-session')
        expected = self.cases['missing-session']['input']['expected_dates'][29]
        self.assertEqual(self.results['missing-session']['data_gaps']['missing_expected_dates'], [expected])

    def test_before_break_and_gap_free_same_basis_numbers_exactly_preserved(self):
        for name in ('no-gap', 'before-basis-break'):
            with self.subTest(case=name):
                r = self.results[name]; before = self.before[name]['fields']; now = state(r)
                self.assertTrue(r['boxes']); self.assertTrue(r['reference_candidates'])
                self.assertEqual(before, now)
                self.assertTrue(all(b['usable_at_anchor'] for b in r['boxes']))
                self.assertTrue(all(b['anchor_comparison_reason'] is None for b in r['boxes']))
                self.assertTrue(all(p['anchor_comparison_reason'] is None for p in r['reference_candidates']))

    def test_break_exactly_at_anchor_is_already_incomparable(self):
        self.assert_stopped_fields('basis-break-at-anchor')
        r = self.results['basis-break-at-anchor']
        self.assertTrue(all(not b['usable_at_anchor'] for b in r['boxes']))

    def test_prefix_future_changes_and_input_immutability(self):
        for index in (28, 50):
            p = deepcopy(self.cases['basis-break']['input']); before = deepcopy(p)
            day = p['bars'][index]['date']; result = analyze(p, as_of=day)
            self.assertEqual(p, before)
            short = deepcopy(p); short['bars'] = short['bars'][:index+1]
            self.assertEqual(result, analyze(short, as_of=day))
            changed = deepcopy(p)
            for bar in changed['bars'][index+1:]:
                bar.update(high='NaN', close='INVALID_FUTURE', volume_shares_scaled='UNKNOWN_FUTURE')
            changed['basis_break_dates'].append(p['bars'][-1]['date'])
            self.assertEqual(result, analyze(changed, as_of=day))

    def test_complete_unauthorized_delta_check_and_qualifications(self):
        saved = {c['id']: c for c in json.loads((HERE/'synthetic-after.json').read_text())['cases']}
        for name, result in self.results.items():
            with self.subTest(case=name):
                self.assertTrue(all(v is True for k,v in check_after(self.before[name]['fields'], result).items()
                                    if k!='primary_pressure_id'))
                self.assertEqual(state(result), saved[name]['fields'])
                self.assertIsNone(result['comparison']['primary_pressure_id'])
                self.assertEqual(result['classification_quality'], 'NOT_VALIDATED')
                self.assertEqual(result['action_qualification'], 'NOT_EVALUATED')
                self.assertEqual(result['formal_strategy_parameters'], {})
                self.assertFalse(result['manual_case_inputs_used'])

    def test_frozen_oracles_and_unmodified_source_dependencies(self):
        baseline = json.loads((HERE/'baseline.json').read_text())
        for name, digest in baseline['frozen'].items():
            self.assertEqual(hashlib.sha256((HERE/name).read_bytes()).hexdigest(), digest)
        for row in baseline['files']:
            if row['path']=='graph_core/core.py': continue  # explicitly authorized target
            self.assertEqual(hashlib.sha256((PROJECT/row['path']).read_bytes()).hexdigest(), row['sha256'])


if __name__=='__main__': unittest.main()
