"""Contract oracles: real retained values + explicitly synthetic boundary fixtures."""
from copy import deepcopy
from decimal import Decimal, localcontext
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from graph_core.core import fingerprint, volume_observation, trace_reference
from reaction_facts.core import evaluate, compare, BINDING
from reaction_facts.source import make_input
from reaction_facts.verify import verify
from reaction_facts.package import package

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT.parent / 'docs/visual-discussion/20261020_reaction_facts_contract'


def real():
    data = json.loads((ROOT / 'cross_scale_chart/generated/comparison-data.json').read_text())
    fixture = json.loads((CONTRACT / 'facts.json').read_text())
    selection = dict(schema_version='explicit-reaction-reference-selection/0.1',
                     binding={k: data['core']['context'].get(k, data.get(k)) for k in BINDING},
                     selected_at='2026-10-20T12:00:00+08:00', references=[
                         dict(kind='RESEARCH_BOUND', box_id=data['layers'][1]['box_ids'][0], field='low'),
                         dict(kind='BAR_FIELD', date='2025-05-14', field='high'),
                         dict(kind='RESEARCH_BOUND', box_id=data['layers'][-1]['box_ids'][0], field='high'),
                         dict(kind='BAR_FIELD', date='2026-10-14', field='high')])
    return data, fixture, selection


def synthetic(prices=('10', '11', '10', '9', '10', '11')):
    """Engineering fixture, never shipped as real market data."""
    rows = [dict(date=f'2000-01-{i+1:02}', open=p, high=p, low=p, close=p,
                 volume_shares_scaled='10') for i, p in enumerate(prices)]
    c = dict(code='ENGINEERING_FIXTURE', source_id='synthetic-not-market', price_basis_id='test-raw',
             source_frame_id='test-frame', source_prefix_fingerprint=fingerprint(rows), volume_unit='SHARES_REPORTED')
    r = dict(id='original-first-high', binding={k: c[k] for k in BINDING}, price=rows[0]['high'],
             origin_id=fingerprint(rows[0]), source_kind='BAR_FIELD', source_field='high',
             occurred_at=rows[0]['date'], known_on=rows[0]['date'], selected_at=None,
             qualification='EXPLICIT_RESEARCH_QUERY', historical_signal_eligible=False)
    return dict(schema_version='reaction-facts-input/0.1', context=c, bars=rows,
                macd=[dict(dif=None, dea=None, histogram=None, reason='TEST_NULL') for _ in rows], references=[r])


def rebind(p):
    p['context']['source_prefix_fingerprint'] = fingerprint(p['bars'])
    for r in p['references']:
        r['binding']['source_prefix_fingerprint'] = p['context']['source_prefix_fingerprint']
        source = next((b for b in p['bars'] if b['date'] == r['occurred_at']), None)
        if r['qualification'] == 'EXPLICIT_RESEARCH_QUERY' and source:
            r['origin_id'] = fingerprint(source)
    return p


class ReactionFacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.fixture, cls.selection = real()
        cls.payload = make_input(cls.data, cls.selection)
        cls.result = evaluate(cls.payload, as_of=cls.data['as_of'])
        cls.rows = {r['date']: r for r in cls.result['records']}
        cls.ids = [r['id'] for r in cls.payload['references']]

    def test_real_nine_record_oracle_all_original_values_and_relations(self):
        for ex in self.fixture['examples']:
            row = self.rows[ex['bar']['date']]
            self.assertEqual(row['original_bar'], ex['bar'])
            self.assertEqual(row['macd']['original'], ex['macd_original'])
            for actual, expected in [('body', 'body_direction')]:
                self.assertEqual(row[actual]['relation'], ex[expected])
            for key, expected in [('close', 'close_vs_previous_close'), ('high', 'high_vs_previous_high'), ('low', 'low_vs_previous_low')]:
                self.assertEqual(row['adjacent'][key]['relation'], ex[expected])
            self.assertEqual(Decimal(row['adjacent']['close']['delta']), Decimal(ex['close_change']))
            self.assertEqual(row['adjacent']['range_geometry'] == 'ENTIRELY_BELOW', ex['raw_range_below_previous_range'])
            # Independent exact fraction oracle, not the rounded Work 28-digit ratio.
            with localcontext() as ctx:
                ctx.prec = 50
                expected = Decimal(ex['bar']['volume_shares_scaled']) / Decimal(ex['previous_record']['volume_shares_scaled'])
            self.assertEqual(Decimal(row['volume']['ratio']), expected)
            self.assertEqual(row['volume']['denominator_dates'], [ex['previous_record']['date']])
            for expected in ex['reference_comparisons']:
                reference = next(r for r in self.payload['references'] if r['price'] == expected['value'])
                observed = row['references'][reference['id']]
                self.assertFalse(observed['historical_signal_eligible'])
                if not expected['source_exists_by_example_date']:
                    self.assertEqual(observed['status'], 'NOT_AVAILABLE')
                else:
                    for key in ('close', 'high', 'low'):
                        self.assertEqual(observed['fields'][key]['relation'], expected[key])
                        oracle = Decimal(ex['bar'][key]) - Decimal(expected['value'])
                        self.assertEqual(Decimal(observed['fields'][key]['delta']), oracle)

    def test_full_may_path_and_two_references_not_one_breakout(self):
        paths = []
        for d in ('2025-05-19', '2025-05-20', '2025-05-21', '2025-05-22'):
            row = self.rows[d]; lower = row['references'][self.ids[0]]['fields']
            paths.append(lower['close']['relation'])
            if d in ('2025-05-20', '2025-05-21'):
                self.assertEqual(row['references'][self.ids[1]]['fields']['high']['relation'], 'BELOW')
        self.assertEqual(paths, ['BELOW', 'ABOVE', 'ABOVE', 'BELOW'])
        self.assertEqual(self.rows['2025-05-20']['references'][self.ids[0]]['fields']['close']['transition']['kind'], 'BELOW_TO_ABOVE')
        self.assertEqual(self.rows['2025-05-22']['references'][self.ids[0]]['fields']['close']['transition']['kind'], 'ABOVE_TO_BELOW')

    def test_oct_path_high_close_equal_low_and_range_move(self):
        positions = [self.rows[f'2026-10-{d}']['references'][self.ids[2]]['fields']['close']['relation'] for d in range(12, 17)]
        self.assertEqual(positions, ['ABOVE', 'BELOW', 'ABOVE', 'BELOW', 'ABOVE'])
        r = self.rows['2026-10-16']
        self.assertEqual(r['references'][self.ids[3]]['fields']['high']['relation'], 'ABOVE')
        self.assertEqual(r['references'][self.ids[3]]['fields']['close']['relation'], 'BELOW')
        self.assertEqual(r['references'][self.ids[2]]['fields']['low']['relation'], 'EQUAL')
        self.assertEqual(r['adjacent']['range_direction'], 'BOTH_ENDS_UP')
        self.assertEqual(r['intraday_sequence'], 'UNKNOWN_FROM_DAILY_OHLC')

    def test_price_counterevidence_does_not_disappear_under_positive_macd(self):
        may = self.rows['2025-05-19']; oct13 = self.rows['2026-10-13']
        for row, rid in ((may, self.ids[0]), (oct13, self.ids[2])):
            self.assertEqual(row['references'][rid]['fields']['close']['relation'], 'BELOW')
            self.assertEqual(row['macd']['field_observations']['histogram']['sign']['relation'], 'ABOVE')
        self.assertEqual(oct13['macd']['field_observations']['histogram']['versus_previous']['relation'], 'ABOVE')
        near_zero = self.rows['2025-05-26']['macd']['field_observations']['histogram']
        self.assertEqual(near_zero['sign']['relation'], 'BELOW')
        self.assertEqual(near_zero['value'], '-0.00307575569432120026846986357371843860771300970856')

    def test_three_state_equal_path_no_implied_direct_cross(self):
        p = synthetic(); r = evaluate(p, as_of=p['bars'][-1]['date']); rid = p['references'][0]['id']
        kinds = [v['references'][rid]['fields']['close']['transition']['kind'] for v in r['records']]
        self.assertEqual(kinds, ['SEGMENT_START', 'EQUAL_TO_ABOVE', 'ABOVE_TO_EQUAL', 'EQUAL_TO_BELOW', 'BELOW_TO_EQUAL', 'EQUAL_TO_ABOVE'])
        self.assertFalse(any(x in kinds for x in ('ABOVE_TO_BELOW', 'BELOW_TO_ABOVE')))

    def test_long_decimal_subtraction_ignores_global_context(self):
        a = '1.' + '0' * 90 + '1'; b = '1.' + '0' * 91
        with localcontext() as ctx:
            ctx.prec = 3
            observed = compare(a, b)
        self.assertEqual(observed['relation'], 'ABOVE')
        self.assertEqual(Decimal(observed['delta']), Decimal('1e-91'))
        self.assertEqual(compare('0.0000000000000000000000000000000000000000000000001', '0')['relation'], 'ABOVE')
        self.assertEqual(compare('10.000', '10')['relation'], 'EQUAL')

    def test_same_price_different_source_remains_separate(self):
        p = synthetic(('10', '10', '11')); r = deepcopy(p['references'][0]); r['id'] = 'second-high'
        r.update(occurred_at=p['bars'][1]['date'], known_on=p['bars'][1]['date'], origin_id=fingerprint(p['bars'][1]))
        p['references'].append(r); result = evaluate(p, as_of=p['bars'][-1]['date'])
        self.assertEqual(len(result['reference_catalog']), 2)
        self.assertEqual(result['records'][0]['references'][r['id']]['status'], 'NOT_AVAILABLE')

    def test_confirmation_date_source_date_and_selection_timestamp_separated(self):
        before = self.rows['2025-03-21']['references'][self.ids[0]]
        after = self.rows['2025-03-24']['references'][self.ids[0]]
        self.assertEqual(before['status'], 'NOT_AVAILABLE'); self.assertNotEqual(after['status'], 'NOT_AVAILABLE')
        ref = self.result['reference_catalog'][0]
        self.assertEqual(ref['known_on'], '2025-03-24'); self.assertEqual(ref['occurred_at'], '2025-03-12')
        self.assertEqual(ref['selected_at'], self.selection['selected_at']); self.assertFalse(ref['historical_signal_eligible'])
        p = deepcopy(self.payload); p['references'][0]['known_on'] = '2025-03-12'
        with self.assertRaises(ValueError): evaluate(p, as_of=self.data['as_of'])

    def test_prefixes_and_changed_future_do_not_rewrite_old_observations(self):
        for as_of in ('2025-05-13', '2025-05-22', '2026-10-13'):
            full = evaluate(self.payload, as_of=as_of)
            p = deepcopy(self.payload); n = sum(b['date'] <= as_of for b in p['bars'])
            p['bars'] = p['bars'][:n]; p['macd'] = p['macd'][:n]; rebind(p)
            short = evaluate(p, as_of=as_of)
            self.assertEqual(full['records'], short['records'])
            self.assertEqual(full['transitions'], short['transitions'])
            p = deepcopy(self.payload); p['bars'][-1]['volume_shares_scaled'] = '1'; p['macd'][-1]['histogram'] = '999'; rebind(p)
            changed = evaluate(p, as_of=as_of)
            self.assertEqual(full['records'], changed['records'])
            for ref in full['reference_catalog']:
                if ref['known_on'] > as_of: self.assertIsNone(ref['price'])

    def test_missing_price_breaks_path_and_resumes_without_crossing_gap(self):
        p = synthetic(('10', '11', '9', '8')); p['bars'][2]['close'] = None; rebind(p)
        r = evaluate(p, as_of=p['bars'][-1]['date']); rid = p['references'][0]['id']
        self.assertIsNone(r['records'][2]['references'][rid]['fields']['close']['relation'])
        self.assertEqual(r['records'][3]['references'][rid]['fields']['close']['transition']['kind'], 'SEGMENT_START')
        self.assertIsNone(r['records'][3]['adjacent']['close']['relation'])

    def test_calendar_gap_starts_new_segment_without_fake_bars(self):
        p = synthetic(('10', '11', '9')); p['bars'][2]['date'] = '2000-01-04'
        p['known_gap_dates'] = ['2000-01-03']; rebind(p)
        r = evaluate(p, as_of='2000-01-04'); row = r['records'][-1]
        self.assertEqual(len(r['records']), 3)
        self.assertEqual(row['continuity']['reason'], 'KNOWN_UNVERIFIED_CALENDAR_GAP')
        self.assertIsNone(row['adjacent']['range_direction']); self.assertIsNone(row['volume']['ratio'])
        self.assertEqual(row['references'][p['references'][0]['id']]['fields']['close']['transition']['kind'], 'SEGMENT_START')

    def test_basis_interruption_stops_old_reference_comparison(self):
        p = synthetic(); p['basis_break_dates'] = ['2000-01-03']
        r = evaluate(p, as_of=p['bars'][-1]['date']); rid = p['references'][0]['id']
        for row in r['records'][2:]:
            self.assertEqual(row['references'][rid]['reason'], 'REFERENCE_BEFORE_BASIS_INTERRUPTION')
            self.assertIsNone(row['references'][rid]['fields']['close']['relation'])

    def test_zero_missing_volume_and_null_macd_preserve_reasons(self):
        p = synthetic(); p['bars'][1]['volume_shares_scaled'] = '0'; p['bars'][3]['volume_shares_scaled'] = None
        p['macd'][4] = None; rebind(p); r = evaluate(p, as_of=p['bars'][-1]['date'])
        self.assertEqual(r['records'][2]['volume']['reason'], 'ZERO_DENOMINATOR')
        self.assertEqual(r['records'][3]['volume']['reason'], 'MISSING_CURRENT_VOLUME')
        self.assertEqual(r['records'][4]['volume']['reason'], 'MISSING_PREVIOUS_VOLUME')
        self.assertIsNone(r['records'][4]['macd']['original'])
        self.assertIsNone(r['records'][4]['macd']['field_observations']['histogram']['sign']['relation'])

    def test_delayed_source_knowledge_is_not_available_on_earlier_record_day(self):
        p = synthetic(); p['bars'][1]['known_on'] = '2000-01-03'
        p['macd'][1] = dict(dif='1', dea='1', histogram='0', reason='AVAILABLE'); rebind(p)
        r = evaluate(p, as_of=p['bars'][-1]['date']); row = r['records'][1]
        self.assertIsNone(row['body']['relation']); self.assertIsNone(row['volume']['ratio'])
        self.assertIsNone(row['macd']['field_observations']['histogram']['sign']['relation'])
        self.assertEqual(row['original_value_known_on'], '2000-01-03')
        self.assertEqual(row['references'][p['references'][0]['id']]['status'], 'NOT_AVAILABLE')
        self.assertEqual(r['records'][2]['adjacent']['close']['relation'], 'BELOW')

    def test_appended_future_and_global_rounding_cannot_change_prior_facts(self):
        from decimal import ROUND_UP
        p = synthetic(('10', '11', '9')); p['bars'][1]['volume_shares_scaled'] = '3'; rebind(p)
        before = evaluate(p, as_of=p['bars'][-1]['date'])
        p['bars'].append(dict(date='2000-01-04', open='999', high='999', low='999', close='999', volume_shares_scaled='999'))
        p['macd'].append(None); rebind(p)
        with localcontext() as ctx:
            ctx.prec = 3; ctx.rounding = ROUND_UP
            after = evaluate(p, as_of='2000-01-03')
        self.assertEqual(before['records'], after['records'])
        self.assertEqual(before['transitions'], after['transitions'])

    def test_range_touch_overlap_and_equal_body_not_formal_gap(self):
        p = synthetic(('10', '10', '11')); r = evaluate(p, as_of=p['bars'][-1]['date'])
        self.assertEqual(r['records'][1]['adjacent']['range_geometry'], 'TOUCHING')
        self.assertEqual(r['records'][1]['body']['relation'], 'EQUAL')
        self.assertEqual(r['records'][1]['adjacent']['range_direction'], 'BOTH_EQUAL')

    def test_reject_duplicate_unsorted_nonfinite_float_and_incomplete(self):
        mutations = [lambda p: p['bars'][1].update(date=p['bars'][0]['date']),
                     lambda p: p['bars'].reverse(), lambda p: p['bars'][1].update(close=1.0),
                     lambda p: p['bars'][1].update(close='NaN'), lambda p: p['bars'][1].update(complete=False),
                     lambda p: p['bars'][1].update(close=None, high='1', low='11')]
        for mutate in mutations:
            p = synthetic(); mutate(p); rebind(p)
            with self.assertRaises(ValueError): evaluate(p, as_of='2000-01-06')

    def test_reject_binding_and_tampered_value_or_historical_signal_claim(self):
        for key in BINDING:
            p = deepcopy(self.payload); p['references'][0]['binding'][key] = 'wrong'
            with self.assertRaises(ValueError): evaluate(p, as_of=self.data['as_of'])
        for key, value in [('price', '999'), ('historical_signal_eligible', True), ('selected_at', '2026-10-20T12:00:00')]:
            p = deepcopy(self.payload); p['references'][1][key] = value
            with self.assertRaises(ValueError): evaluate(p, as_of=self.data['as_of'])
        p = deepcopy(self.payload); p['macd'].pop()
        with self.assertRaises(ValueError): evaluate(p, as_of=self.data['as_of'])

    def test_adapter_refuses_source_schema_or_selection_mismatch_and_manual_audit(self):
        for key in BINDING:
            sel = deepcopy(self.selection); sel['binding'][key] = 'other'
            with self.assertRaises(ValueError): make_input(self.data, sel)
        data = deepcopy(self.data); data['bars'][0]['close'] = '1'
        with self.assertRaises(ValueError): make_input(data, self.selection)
        sel = deepcopy(self.selection); sel['references'][0]['kind'] = 'MANUAL_AUDIT'
        with self.assertRaises(ValueError): make_input(self.data, sel)

    def test_equivalent_helpers_reused_without_modifying_original_functions(self):
        # Earlier helper is equivalent only away from gaps/equality; don't change its semantics.
        p = synthetic(('10', '11', '9')); r = evaluate(p, as_of=p['bars'][-1]['date'])
        old = trace_reference(p['bars'], '10', 0)
        self.assertEqual(old['last_relation'], r['records'][-1]['references'][p['references'][0]['id']]['fields']['close']['relation'])
        for i in range(1, 3):
            self.assertEqual(volume_observation(p['bars'], i)['ratio_to_previous_means']['1'], r['records'][i]['volume']['ratio'])

    def test_pure_no_mutation_no_strategy_fields_or_input_constants(self):
        before = deepcopy(self.payload); evaluate(self.payload, as_of=self.data['as_of']); self.assertEqual(before, self.payload)
        self.assertIsNone(self.result['primary_pressure_id']); self.assertIsNone(self.result['whole_pressure_clearance'])
        for name in ('core.py', 'source.py', 'build.py'):
            text = (ROOT / 'reaction_facts' / name).read_text()
            for token in ('1101', '30.05', '30.50', '27.40', '2025-05', '2026-10', 'manual_case_audit', 'analyze('):
                self.assertNotIn(token, text)

    def test_cli_new_json_exact_reproduction_and_conflict_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp); selected = temp / 'selection.json'; output = temp / 'facts.json'
            selected.write_text(json.dumps(self.selection))
            cmd = [sys.executable, '-m', 'reaction_facts.build', '--data', str(ROOT/'cross_scale_chart/generated/comparison-data.json'),
                   '--selection', str(selected), '--as-of', self.data['as_of'], '--output', str(output)]
            completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(output.read_text()), self.result)
            checked = verify(ROOT/'cross_scale_chart/generated/comparison-data.json', selected, output)
            self.assertEqual(checked['status'], 'PASS')
            packed = package(ROOT/'cross_scale_chart/generated/comparison-data.json', selected, output, temp/'archive')
            self.assertEqual(packed['crc'], 'PASS'); self.assertEqual(len(packed['members']), 6)
            corrupted = json.loads(output.read_text()); corrupted['records'][-1]['body']['relation'] = 'BELOW'
            output.write_text(json.dumps(corrupted))
            with self.assertRaises(ValueError): verify(ROOT/'cross_scale_chart/generated/comparison-data.json', selected, output)
            output.write_text('existing user file')
            completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(output.read_text(), 'existing user file')


if __name__ == '__main__':
    unittest.main()
