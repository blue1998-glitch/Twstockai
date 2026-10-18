"""Real-source manual binding, rejection and unchanged historical selections."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest

from hurdle_chart.build import ROOT, CASE, attach, selection
from hurdle_chart.manual import bind
from pressure_chart.build import selection as pressure_selection
from technical_chart.build import unpack


class ManualHurdleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = (ROOT / 'pressure_chart/generated/M1_v0_19_pressure_chart.html').read_text()
        cls.old = unpack(json.loads(re.search(r'id="payload">(.*?)</script>', html, re.S).group(1)))
        cls.raw = CASE.read_bytes()
        cls.case = json.loads(cls.raw)
        cls.source = next(s for s in cls.old['history_series'] if s['code'] == '1101')
        cls.frame = cls.source['frames'][-1]
        cls.layer = bind(cls.case, cls.raw, cls.source, cls.frame)

    def test_exact_real_case_and_all_five_price_only_dates(self):
        self.assertIsNotNone(self.layer)
        self.assertEqual(self.layer['review'], self.case)
        self.assertEqual([r['reference']['raw_high'] for r in self.layer['references']], ['35.50', '40.25', '50.20'])
        third = self.layer['references'][2]
        self.assertIsNone(third['reference']['source_date'])
        self.assertEqual(len(third['reference']['source_bars']), 5)
        self.assertEqual([self.source['bases'][self.frame['chart_base']]['bars'][i]['date'] for i in third['source_indices']],
                         ['2021-10-18', '2022-03-29', '2022-03-31', '2022-04-06', '2022-04-07'])
        self.assertEqual(self.layer['source_fingerprints']['review_file_sha256'], hashlib.sha256(self.raw).hexdigest())

    def test_other_stocks_sources_frames_dates_or_basis_do_not_match(self):
        for s in [*self.old['numbers']['series'], *self.old['history_series']]:
            for f in [s['frames'][0], s['frames'][-1]]:
                if s['key'] == self.source['key'] and f['frame_id'] == self.frame['frame_id']:
                    continue
                with self.subTest(source=s['key'], date=f['as_of']):
                    self.assertIsNone(bind(self.case, self.raw, s, f))
        for key in ['code', 'price_mode', 'source_id', 'frame_id', 'chart_base', 'analysis_as_of']:
            case = deepcopy(self.case)
            case[key] = 'mismatch'
            with self.subTest(key=key):
                self.assertIsNone(bind(case, self.raw, self.source, self.frame))

    def test_each_preceding_real_day_is_unannotated(self):
        for f in self.source['frames'][:-1]:
            self.assertIsNone(bind(self.case, self.raw, self.source, f))

    def test_mismatching_source_ohlcv_is_rejected(self):
        for field in ['date', 'open', 'high', 'low', 'close', 'volume_shares_scaled']:
            case = deepcopy(self.case)
            case['references'][0]['source_bars'][0][field] = '999'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'OHLCV'):
                bind(case, self.raw, self.source, self.frame)

    def test_cannot_silently_pick_one_of_five_dates(self):
        case = deepcopy(self.case)
        ref = case['references'][2]
        ref['matching_source_dates'] = ref['matching_source_dates'][:1]
        ref['source_bars'] = ref['source_bars'][:1]
        with self.assertRaisesRegex(ValueError, 'all matching'):
            bind(case, self.raw, self.source, self.frame)

    def test_undefined_rules_remain_null_and_order_is_preserved(self):
        for key in ['region_start', 'region_end', 'region_price_bounds', 'region_total_volume',
                    'volume_expansion_rule', 'automatic_selection_rule']:
            case = deepcopy(self.case)
            case['references'][0][key] = 3
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'unknown'):
                bind(case, self.raw, self.source, self.frame)
        case = deepcopy(self.case)
        case['references'].reverse()
        with self.assertRaisesRegex(ValueError, 'order'):
            bind(case, self.raw, self.source, self.frame)

    def test_conflicting_current_relation_rejected(self):
        case = deepcopy(self.case)
        case['references'][0]['current_raw_close_relation'] = 'ABOVE'
        with self.assertRaisesRegex(ValueError, 'relation'):
            bind(case, self.raw, self.source, self.frame)

    def test_new_layer_preserves_original_outputs_and_prior_downloads(self):
        augmented = attach(self.old)
        for key in self.old:
            if key not in ('schema_version', 'view_version', 'artifact_id'):
                self.assertEqual(augmented[key], self.old[key], key)
        matches = [v for rows in augmented['manual_hurdle_layers'].values() for v in rows if v]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], self.layer)
        for s, day in [(self.source, self.source['frames'][-2]['as_of']),
                       (self.old['numbers']['series'][0], self.old['numbers']['series'][0]['frames'][-1]['as_of'])]:
            actual = selection(augmented, s['key'], day)
            self.assertIsNone(actual.pop('manual_hurdles'))
            expected = pressure_selection(self.old, s['key'], day)
            actual['schema_version'] = expected['schema_version']
            actual['view_version'] = expected['view_version']
            self.assertEqual(actual, expected)
        self.assertEqual(selection(augmented, self.source['key'], '2026-10-16')['manual_hurdles'], self.layer)


if __name__ == '__main__':
    unittest.main()
