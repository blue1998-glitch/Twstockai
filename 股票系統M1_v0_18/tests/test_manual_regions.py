"""Real reviewed endpoints, uncertainty, source binding and immutable parent."""
from copy import deepcopy
import json
import re
import unittest
import zipfile

from region_chart.build import ROOT, attach, load_parent, selection
from region_chart.regions import bind, load_reviews
from hurdle_chart.build import selection as original_selection


class ManualRegionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = load_parent()
        cls.reviews, cls.digests = load_reviews()
        cls.series = next(s for s in cls.parent['history_series'] if s['code'] == '1101')
        cls.frame = cls.series['frames'][-1]
        cls.layer = bind(cls.reviews, cls.digests, cls.series, cls.frame)

    def test_exact_g2_dates_and_all_ten_endpoint_fields(self):
        g2 = next(r for r in self.layer['regions'] if r['id'] == 'G2')
        self.assertEqual((g2['exact_start_date'], g2['exact_end_date']), ('2023-01-16', '2023-08-16'))
        self.assertEqual(g2['endpoints'], {'start': self.reviews['g2']['region']['start'], 'end': self.reviews['g2']['region']['end']})
        self.assertEqual(len(self.layer['g2_endpoint_verification']['endpoint_field_checks']), 10)
        self.assertIsNone(self.layer['original_reviews']['g2']['reviewed_at'])
        self.assertEqual(g2['representative']['source_date'], '2023-05-02')
        self.assertEqual(g2['representative']['raw_high'], '40.25')

    def test_g1_month_is_not_silently_fixed_to_first_day(self):
        g1 = self.layer['regions'][0]
        self.assertIsNone(g1['exact_start_date'])
        self.assertEqual(g1['approximate_start_month'], '2023-09')
        self.assertIsNone(g1['bar_membership'])
        self.assertIsNone(g1['price_bounds'])
        self.assertIsNone(g1['total_volume'])
        self.assertEqual(g1['end_reference']['date'], '2024-01-19')
        self.assertEqual(g1['representative']['source_date'], '2023-11-28')
        self.assertEqual(g1['representative']['raw_high'], '35.50')

    def test_c_right_is_unknown_extent_and_not_verified_ownership(self):
        newer = self.layer['regions'][2]
        for key in ('exact_start_date', 'end_date', 'bar_membership'):
            self.assertIsNone(newer[key])
        self.assertIn('OPEN_DIRECTION_RAIL_ONLY', newer['display']['draw'])
        self.assertEqual(self.layer['c_source']['low'], '31.80')
        self.assertIsNone(self.layer['remaining_ownership'])

    def test_price_and_volume_references_are_separate_real_dates(self):
        rows = [e['bar'] for e in self.layer['volume_evidence']]
        self.assertEqual([r['date'] for r in rows], ['2023-10-18', '2023-11-30'])
        self.assertEqual([r['volume_shares_scaled'] for r in rows], ['110992007', '106415572'])
        self.assertEqual(self.layer['g1_source_facts']['exact_source_bars']['2023-09-14']['high'], '35.50')
        self.assertEqual(self.layer['g1_source_facts']['exact_source_bars']['2023-11-28']['volume_shares_scaled'], '65709089')

    def test_original_reviews_retained_and_immutable(self):
        self.assertEqual(self.layer['original_reviews']['g1'], self.reviews['g1'])
        self.assertEqual(self.layer['original_reviews']['g2'], self.reviews['g2'])
        self.assertEqual(self.layer['original_reviews']['g2']['product_integration'], 'NOT_IMPLEMENTED_THIS_TURN')
        self.assertIn('EXACT_MANUAL_TIME_REGIONS', self.layer['integration_status'])

    def test_other_stocks_modes_sources_and_every_prior_date_excluded(self):
        for s in [*self.parent['numbers']['series'], *self.parent['history_series']]:
            for f in (s['frames'][0], s['frames'][-1]):
                if s['key'] == self.series['key'] and f['as_of'] == '2026-10-16':
                    continue
                self.assertIsNone(bind(self.reviews, self.digests, s, f))
        for f in self.series['frames'][:-1]:
            self.assertIsNone(bind(self.reviews, self.digests, self.series, f))
        for key in ('source_id', 'frame_id', 'chart_base'):
            reviews = deepcopy(self.reviews)
            reviews['g2']['source_binding'][key] = 'mismatch'
            self.assertIsNone(bind(reviews, self.digests, self.series, self.frame))

    def test_changed_endpoint_prices_or_volume_rejected(self):
        for endpoint in ('start', 'end'):
            for key in ('open', 'high', 'low', 'close', 'volume_shares_scaled'):
                reviews = deepcopy(self.reviews)
                reviews['g2']['region'][endpoint][key] = '999'
                with self.subTest(endpoint=endpoint, key=key), self.assertRaises(ValueError):
                    bind(reviews, self.digests, self.series, self.frame)

    def test_endpoint_report_must_describe_same_selected_interval(self):
        reviews = deepcopy(self.reviews)
        reviews['g2_verification']['endpoints'].pop('2023-01-16')
        with self.assertRaisesRegex(ValueError, 'report'):
            bind(reviews, self.digests, self.series, self.frame)

    def test_false_or_missing_ten_field_checks_rejected(self):
        for change in ('false', 'missing', 'value'):
            reviews = deepcopy(self.reviews)
            checks = reviews['g2_verification']['endpoint_field_checks']
            if change == 'false': checks[0]['equal'] = False
            elif change == 'missing': checks.pop()
            else: checks[0]['source_value'] = '999'
            with self.assertRaisesRegex(ValueError, 'ten-field'):
                bind(reviews, self.digests, self.series, self.frame)

    def test_source_mutation_anywhere_in_prefix_is_rejected(self):
        s = deepcopy(self.series)
        s['bases'][self.frame['chart_base']]['bars'][0]['close'] = '999.12345678'
        with self.assertRaisesRegex(ValueError, 'prefix'):
            bind(self.reviews, self.digests, s, self.frame)

    def test_missing_real_date_is_not_filled_or_interpolated(self):
        s = deepcopy(self.series)
        s['bases'][self.frame['chart_base']]['bars'].pop(50)
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            bind(self.reviews, self.digests, s, self.frame)

    def test_g1_c_or_source_evidence_mismatch_rejected(self):
        for key in ('source_id', 'frame_id', 'chart_base'):
            reviews = deepcopy(self.reviews)
            reviews['g1_facts'][key] = 'wrong'
            with self.assertRaisesRegex(ValueError, 'binding'):
                bind(reviews, self.digests, self.series, self.frame)
        reviews = deepcopy(self.reviews)
        reviews['g1']['older_region']['end_reference']['source_low'] = '1'
        with self.assertRaisesRegex(ValueError, 'C source'):
            bind(reviews, self.digests, self.series, self.frame)

    def test_unapproved_boundaries_and_volume_rules_stay_null(self):
        for group, fields in [('g1', ['exact_start_date', 'price_bounds', 'total_volume', 'bar_membership']),
                              ('g2', ['price_bounds', 'total_volume', 'volume_measure_rule', 'automatic_region_split'])]:
            for key in fields:
                reviews = deepcopy(self.reviews)
                obj = reviews[group]['older_region' if group == 'g1' else 'region']
                obj[key] = 'invented'
                with self.subTest(group=group, key=key), self.assertRaises(ValueError):
                    bind(reviews, self.digests, self.series, self.frame)

    def test_newer_region_end_not_inferred_from_discussion_window(self):
        reviews = deepcopy(self.reviews)
        reviews['g1']['newer_region']['end_date'] = '2024-04-30'
        with self.assertRaisesRegex(ValueError, 'extent'):
            bind(reviews, self.digests, self.series, self.frame)

    def test_parent_fields_numbers_and_original_manual_layer_unchanged(self):
        new = attach(self.parent)
        for key in self.parent:
            if key not in ('view_version', 'schema_version', 'artifact_id'):
                self.assertEqual(new[key], self.parent[key], key)
        self.assertEqual(sum(v is not None for rows in new['region_layers'].values() for v in rows), 1)
        for day in ('2026-10-15', '2026-10-16'):
            actual = selection(new, self.series['key'], day)
            layer = actual.pop('manual_regions')
            old = original_selection(self.parent, self.series['key'], day)
            actual['schema_version'] = old['schema_version']
            actual['view_version'] = old['view_version']
            self.assertEqual(actual, old)
            self.assertEqual(layer is not None, day == '2026-10-16')

    def test_navigation_is_explicit_display_padding_not_formal_membership(self):
        for item in self.layer['regions']:
            n = item['navigation']
            self.assertGreaterEqual(n['start'], 0)
            self.assertLessEqual(n['end'], self.frame['index'])
            self.assertLessEqual(n['start'], n['cursor'])
            self.assertGreaterEqual(n['end'], n['cursor'])
            self.assertEqual(n['qualification'], 'DISPLAY_PADDING_ONLY_NOT_REGION_BOUNDARIES')


if __name__ == '__main__':
    unittest.main()
