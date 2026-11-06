"""Causal engineering cases for explicit user-selected levels, not profit tests."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from product_candidate.attempt_evidence import evaluate


def fixture():
    return json.loads((ROOT / 'product_candidate/fixtures/attempt_evidence_v01.json').read_text())


def kinds(result, reference=None):
    return [e['kind'] for e in result['events']
            if reference is None or e['reference_id'] == reference]


class AttemptEvidenceTests(unittest.TestCase):
    def test_101_attempt_does_not_require_volume_lead_or_106(self):
        p = fixture(); p['observations'] = p['observations'][:1]
        result = evaluate(p); frame = result['frames'][0]
        self.assertEqual(frame['attempt_levels'][0]['price_attempt_condition'], 'MET')
        self.assertEqual(frame['attempt_levels'][1]['price_attempt_condition'], 'NOT_MET')
        self.assertEqual(frame['volume_lead_evidence_ids'], [])
        self.assertIn('INTRADAY_CROSSED_ABOVE', kinds(result, 'NEAR_HIGH'))
        self.assertNotIn('CLOSE_CROSSED_ABOVE', kinds(result))

    def test_volume_benchmark_is_left_max_not_mean_or_recent_volume(self):
        result = evaluate(fixture())
        self.assertEqual(result['left_zone_max_volume_shares'], '8000')
        self.assertEqual(result['frames'][0]['volume_relation'], 'LOWER')
        self.assertEqual(result['frames'][1]['volume_relation'], 'HIGHER')

    def test_volume_lead_is_known_before_price_passes_106(self):
        result = evaluate(fixture())
        event = next(e for e in result['events'] if e['kind'] == 'VOLUME_LEAD_OBSERVED')
        self.assertEqual(event['first_observed_at'], '2026-09-14T09:30:00+08:00')
        self.assertIsNone(event['occurred_at'])
        self.assertIsNone(event['confirmed_at'])
        self.assertEqual(event['evidence']['observed_high'], '103')
        self.assertIn(event['id'], result['frames'][3]['volume_lead_evidence_ids'])

    def test_price_inside_old_zone_is_not_over_upper_edge(self):
        p = fixture(); p['observations'] = p['observations'][:1]
        p['observations'][0].update(high='105', last='105')
        self.assertEqual(evaluate(p)['frames'][0]['attempt_levels'][1]['relation'], 'BELOW')

    def test_106_is_a_separate_attempt_then_close_fact(self):
        result = evaluate(fixture())
        self.assertEqual(result['frames'][3]['attempt_levels'][1]['price_attempt_condition'], 'MET')
        self.assertIn('INTRADAY_CROSSED_ABOVE', kinds(result, 'LEFT_ZONE_UPPER'))
        self.assertIn('CLOSE_CROSSED_ABOVE', kinds(result, 'LEFT_ZONE_UPPER'))
        self.assertEqual(result['frames'][3]['attempt_levels'][1]['latest_completed_close_relation'], 'BELOW')
        self.assertEqual(result['frames'][4]['attempt_levels'][1]['latest_completed_close_relation'], 'ABOVE')

    def test_return_below_106_does_not_erase_prior_attempt_or_101(self):
        result = evaluate(fixture()); frame = result['frames'][5]
        self.assertEqual([r['relation'] for r in frame['attempt_levels']], ['ABOVE', 'BELOW'])
        self.assertIn('CLOSE_RETURNED_BELOW', kinds(result, 'LEFT_ZONE_UPPER'))
        self.assertIn('CLOSE_CROSSED_ABOVE', kinds(result, 'LEFT_ZONE_UPPER'))
        self.assertIn('CLOSE_RETURNED_BELOW', kinds(result, 'NEAR_HIGH'))

    def test_intraday_above_then_close_below_are_distinct(self):
        p = fixture(); p['observations'] = p['observations'][:3]
        p['observations'][-1].update(low='99', last='100')
        result = evaluate(p)
        self.assertIn('INTRADAY_CROSSED_ABOVE', kinds(result, 'NEAR_HIGH'))
        self.assertNotIn('CLOSE_CROSSED_ABOVE', kinds(result, 'NEAR_HIGH'))
        self.assertEqual(result['frames'][-1]['attempt_levels'][0]['relation'], 'BELOW')

    def test_daily_high_and_final_volume_do_not_invent_intraday_order(self):
        p = fixture(); p['observations'] = [p['observations'][2]]
        p['observations'][0].update(high='107', last='105')
        result = evaluate(p)
        self.assertIn('VOLUME_EXCESS_ORDER_UNKNOWN', kinds(result))
        self.assertNotIn('VOLUME_LEAD_OBSERVED', kinds(result))
        self.assertFalse(any(k.startswith('INTRADAY_') for k in kinds(result)))

    def test_observed_price_already_passed_cannot_be_relabelled_volume_lead(self):
        p = fixture(); p['observations'] = p['observations'][:2]
        p['observations'][0].update(high='107', last='107')
        p['observations'][1].update(high='107', last='105')
        result = evaluate(p)
        self.assertIn('VOLUME_EXCESS_PRICE_ALREADY_PASSED', kinds(result))
        self.assertNotIn('VOLUME_LEAD_OBSERVED', kinds(result))

    def test_missing_selected_source_volume_stays_unknown(self):
        p = fixture(); p['history'][1]['volume_shares'] = None
        result = evaluate(p)
        self.assertIsNone(result['left_zone_max_volume_shares'])
        self.assertTrue(all(f['volume_relation'] == 'UNKNOWN' for f in result['frames']))
        self.assertNotIn('VOLUME_LEAD_OBSERVED', kinds(result))
        self.assertEqual(result['frames'][0]['attempt_levels'][0]['price_attempt_condition'], 'MET')

    def test_supplied_history_already_over_106_does_not_become_new_volume_lead(self):
        p = fixture(); p['history'][-1]['high'] = '107'
        result = evaluate(p)
        self.assertNotIn('VOLUME_LEAD_OBSERVED', kinds(result))
        self.assertIn('VOLUME_EXCESS_PRICE_ALREADY_PASSED', kinds(result))

    def test_output_preserves_exact_source_records_for_readback(self):
        p = fixture(); result = evaluate(p)
        self.assertEqual(result['source_history'], p['history'])
        self.assertEqual([f['source_observation'] for f in result['frames']], p['observations'])
        reconstructed = dict(schema_version=p['schema_version'], context=result['context'],
                             history=result['source_history'], references=result['reference_set'],
                             observations=[f['source_observation'] for f in result['frames']])
        self.assertEqual(evaluate(reconstructed), result)

    def test_missing_source_date_does_not_use_partial_maximum(self):
        p = fixture(); p['history'].pop(1)
        with self.assertRaisesRegex(ValueError, 'partial maximum'):
            evaluate(p)

    def test_equal_price_or_equal_volume_is_not_exceeded(self):
        p = fixture(); p['observations'] = p['observations'][:1]
        p['observations'][0].update(last='101', volume_shares='8000')
        frame = evaluate(p)['frames'][0]
        self.assertEqual(frame['attempt_levels'][0]['price_attempt_condition'], 'AT_BOUNDARY')
        self.assertEqual(frame['volume_relation'], 'EQUAL')
        self.assertEqual(frame['volume_lead_evidence_ids'], [])

    def test_equality_does_not_disarm_previous_close_above(self):
        p = fixture(); p['observations'][5]['last'] = '106'
        p['observations'][6]['last'] = '105'
        result = evaluate(p)
        returns = [e for e in result['events'] if e['reference_id'] == 'LEFT_ZONE_UPPER'
                   and e['kind'] == 'CLOSE_RETURNED_BELOW']
        self.assertEqual([e['bar_date'] for e in returns], ['2026-09-17'])

    def test_more_precise_than_two_decimals_is_used_for_price_fact(self):
        p = fixture(); p['observations'] = p['observations'][:1]
        p['observations'][0]['last'] = '101.0000000000000001'
        self.assertEqual(evaluate(p)['frames'][0]['attempt_levels'][0]['relation'], 'ABOVE')

    def test_every_truncated_prefix_preserves_earlier_frames_and_event_ids(self):
        p = fixture(); complete = evaluate(p)
        for count in range(1, len(p['observations']) + 1):
            with self.subTest(count=count):
                prefix = deepcopy(p); prefix['observations'] = prefix['observations'][:count]
                result = evaluate(prefix)
                self.assertEqual(result['frames'], complete['frames'][:count])
                self.assertEqual(result['events'], [e for e in complete['events']
                                                   if e['observation_index'] < count])

    def test_probability_trend_and_full_trade_qualification_are_not_invented(self):
        result = evaluate(fixture())
        self.assertEqual(result['action_qualification'], 'NOT_EVALUATED')
        for frame in result['frames']:
            self.assertIsNone(frame['probability_estimate'])
            self.assertEqual(frame['trend_strength'], 'NOT_CLASSIFIED')
            self.assertEqual(frame['action_qualification'], 'NOT_EVALUATED')

    def test_input_not_mutated_and_repeat_is_deterministic(self):
        p = fixture(); original = deepcopy(p)
        first = evaluate(p)
        self.assertEqual(p, original)
        self.assertEqual(first, evaluate(p))

    def test_volume_reset_next_day_is_allowed_and_prior_lead_is_history(self):
        p = fixture(); p['observations'][3]['volume_shares'] = '1000'
        result = evaluate(p)
        self.assertEqual(result['frames'][3]['volume_relation'], 'LOWER')
        self.assertTrue(result['frames'][3]['volume_lead_evidence_ids'])

    def test_reject_invalid_timing_basis_units_and_cumulative_updates(self):
        changes = [
            lambda p: p['observations'][0].update(price_basis_id='OTHER_ANCHOR'),
            lambda p: p['history'][0].update(price_basis_id='OTHER_ANCHOR'),
            lambda p: p['context'].update(volume_unit='LOTS'),
            lambda p: p['references'].update(known_at='2026-09-14T10:00:00+08:00'),
            lambda p: p['history'][-1].update(known_at='2026-09-14T12:00:00+08:00'),
            lambda p: p['observations'][1].update(observed_at='2026-09-14T09:00:00+08:00'),
            lambda p: p['observations'][1].update(volume_shares='4000'),
            lambda p: p['observations'][1].update(high='101'),
            lambda p: p['observations'][0].update(is_close=True),
            lambda p: p['observations'][0].update(last=101.5),
            lambda p: p['observations'][0].update(observed_at='2026-09-14T09:10:00'),
            lambda p: p['observations'][0].update(volume_shares='1.5'),
            lambda p: p['observations'][0].update(last='NaN'),
            lambda p: p['references']['near_high'].update(price='100'),
        ]
        for mutation in changes:
            with self.subTest(mutation=changes.index(mutation)):
                p = fixture(); mutation(p)
                with self.assertRaises(ValueError):
                    evaluate(p)

    def test_new_day_requires_previous_daily_final_observation(self):
        p = fixture(); p['observations'].pop(2)
        with self.assertRaisesRegex(ValueError, 'final daily'):
            evaluate(p)

    def test_adjusted_requires_explicit_common_anchor(self):
        p = fixture(); p['context']['price_mode'] = 'ADJUSTED_CANDIDATE'
        with self.assertRaises(ValueError):
            evaluate(p)
        p['context']['adjustment_anchor'] = '2026-09-30'
        with self.assertRaisesRegex(ValueError, 'future'):
            evaluate(p)
        p['context']['adjustment_anchor'] = '2026-09-14'
        self.assertEqual(evaluate(p)['context']['price_mode'], 'ADJUSTED_CANDIDATE')

    def test_provenance_changes_have_new_fingerprints_and_event_ids(self):
        p = fixture(); old = evaluate(p)
        p['context']['source_id'] = 'ANOTHER_DECLARED_SOURCE'
        new = evaluate(p)
        self.assertNotEqual(old['history_fingerprint'], new['history_fingerprint'])
        self.assertNotEqual(old['events'][0]['id'], new['events'][0]['id'])


if __name__ == '__main__':
    unittest.main()
