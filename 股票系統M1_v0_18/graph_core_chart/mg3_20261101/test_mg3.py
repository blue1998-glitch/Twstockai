"""Focused M-G3 source, projection and fixed real-case acceptance."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest

from graph_core.core import analyze, fingerprint
from graph_core_chart.build import input_for, selection, render, PARENT_SHA256
from graph_core_chart.evidence import bind_input, input_binding, layers, validate_source_spec
from candle_region_chart.build import load_parent
from technical_chart.build import unpack

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
OUTPUT = ROOT/'graph_core_chart/output/mg3_20261101'


def read_html(path):
    return unpack(json.loads(re.search(r'<script id="payload" type="application/json">(.*?)</script>', path.read_text(), re.S)[1]))


class MG3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = read_html(OUTPUT/'M1_v019_graph_recognition_v02.html')
        cls.old = read_html(ROOT/'graph_core_chart/generated/M1_v019_graph_recognition_v01.html')
        cls.parent = load_parent()
        cls.expected = json.loads((HERE/'expected.json').read_text())
        cls.spec = json.loads((HERE/'source-input-spec.json').read_text())

    def series(self, code):
        return next(s for s in self.bundle['series'] if s['code'] == code)

    def frame(self, code, day):
        return next(r for r in self.series(code)['results'] if r['as_of'] == day)

    def test_protected_originals_frozen_input_and_legacy_render(self):
        baseline = json.loads((HERE/'baseline.json').read_text())
        for row in baseline['protected_files']:
            raw = (ROOT.parent/row['path']).read_bytes()
            self.assertEqual(len(raw), row['bytes'], row['path'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'], row['path'])
        for path, digest in baseline['frozen'].items():
            self.assertEqual(hashlib.sha256((HERE/path).read_bytes()).hexdigest(), digest)
        self.assertEqual(render(self.old).encode(), (ROOT/'graph_core_chart/generated/M1_v019_graph_recognition_v01.html').read_bytes())
        validate_source_spec(self.spec, ROOT, PARENT_SHA256)
        bad = deepcopy(self.spec); bad['basis_warnings']['2884'][0]['sha256'] = '0'*64
        with self.assertRaises(ValueError): validate_source_spec(bad, ROOT, PARENT_SHA256)

    def test_all_numeric_parents_core_prefixes_and_three_layers_exact(self):
        """Each new saved frame equals a direct call of the unchanged core."""
        self.assertEqual(self.bundle['view_version'], self.expected['view_version'])
        oracles = json.loads((OUTPUT/'selection-oracle.json').read_text())['cases']
        for s in self.bundle['series']:
            parent = next(p for p in self.parent['history_series'] if p['code'] == s['code'])
            f = parent['frames'][-1]; base = parent['bases'][f['chart_base']]
            for key in ('bars', 'macd', 'moving_averages'): self.assertEqual(s[key], base[key])
            self.assertEqual(s['source'], parent['source'])
            payload = bind_input(input_for(parent, f), self.spec, s['code'])
            for r in s['results']:
                self.assertEqual(r, analyze(payload, as_of=r['as_of']))
                self.assertEqual(s['box_evidence'][r['as_of']], layers(r, s['bars']))
                self.assertEqual(s['input_bindings'][r['as_of']], input_binding(payload, self.spec, s['code'], r['as_of']))
                self.assertEqual(s['numeric_frame_ids'][r['as_of']], next(p['frame_id'] for p in parent['frames'] if p['as_of'] == r['as_of']))
                self.assertIsNone(r['comparison']['primary_pressure_id'])
                self.assertEqual(r['classification_quality'], 'NOT_VALIDATED')
                self.assertEqual(r['action_qualification'], 'NOT_EVALUATED')
                self.assertFalse(r['manual_case_inputs_used'])
                for b in r['boxes']:
                    e = s['box_evidence'][r['as_of']][b['id']]
                    self.assertEqual(e['formation']['records'], b['last_index']-b['first_index']+1)
                    self.assertEqual(e['observation']['events'], b['path']['events'])
                    self.assertEqual(e['history']['parent_ids'], b['parent_ids'])
                    self.assertEqual(e['history']['successor_after_breakdown_ids'], b['successor_after_breakdown_ids'])
                    self.assertTrue(all(s['bars'][i]['date'] <= r['as_of'] for i, _ in e['observation']['completed_records']))
        for row in oracles:
            self.assertEqual(fingerprint(selection(self.bundle, row['code'], row['as_of'])), row['fingerprint'])

    def test_1101_formation_confirmation_breakdown_and_pressure_distinction(self):
        case = self.expected['automatic_local']; l3 = case['L3_id']; l6 = case['L6_id']
        early = self.frame('1101', case['L6_absent_at'])
        self.assertNotIn(l6, [b['id'] for b in early['boxes']])
        b = next(b for b in early['boxes'] if b['id'] == l3)
        self.assertEqual(b['anchor_relation'], 'BELOW')
        self.assertEqual(b['path']['last_close_location'], 'INSIDE')
        for day in (case['L6_present_at'], case['breakdown_at'], case['breakdown_still_present_at']):
            r = self.frame('1101', day)
            for identity in (l3, l6):
                b = next(b for b in r['boxes'] if b['id'] == identity)
                self.assertEqual((b['start'], b['source_end'], b['duration_records']), (case['start'], case['end'], case['records']))
                self.assertLessEqual(b['confirmed_at'], day)
                if day >= case['breakdown_at']: self.assertEqual(b['path']['first_breakdown_at'], case['breakdown_at'])
        for r in self.series('1101')['results']:
            self.assertTrue(all(p['confirmed_at'] <= r['as_of'] for p in r['pivots']))
            if r['as_of'] != '2026-10-16': self.assertNotIn(r['as_of'], self.series('1101')['manual_audits'])
        a = self.series('1101')['manual_audits']['2026-10-16']['previous_manual_box']
        self.assertEqual((a['start'], a['end'], a['records']), ('2025-04-07', '2025-06-02', 39))

    def test_all_1101_ids_geometries_relationships_and_five_day_events_preserved(self):
        old = next(s for s in self.old['series'] if s['code'] == '1101')
        for oldr in old['results']:
            r = self.frame('1101', oldr['as_of'])
            self.assertEqual(r['pivots'], oldr['pivots'])
            self.assertEqual([b['id'] for b in r['boxes']], [b['id'] for b in oldr['boxes']])
            for before, after in zip(oldr['boxes'], r['boxes']):
                for key in ('id','research_bounds','display_extent','source_turn_ids','start','source_end','confirmed_at','parent_ids','successor_after_breakdown_ids','path','volume'):
                    self.assertEqual(after[key], before[key], (r['as_of'], key))
        self.assertEqual(self.series('1101')['manual_audits'], old['manual_audits'])
        # Exact original reference traces include all 10/12..16 transitions;
        # no display labels replace the core's event history.
        for day in ('2026-10-12','2026-10-13','2026-10-14','2026-10-15','2026-10-16'):
            before = next(r for r in old['results'] if r['as_of']==day)
            self.assertEqual([r['path'] for r in self.frame('1101',day)['reference_candidates']], [r['path'] for r in before['reference_candidates']])

    def test_2884_warning_f01_nulls_and_unchanged_prebreak_formation(self):
        s = self.series('2884')
        for day in ('2026-07-21','2026-07-22'):
            r = self.frame('2884', day)
            self.assertIn('2026-07-01', r['data_gaps']['basis_resets'])
            stopped = [b for b in r['boxes'] if not b['usable_at_anchor']]; self.assertTrue(stopped)
            for b in stopped:
                self.assertIsNone(b['pressure_distance_fraction']); self.assertIsNone(b['relative_width_to_anchor'])
                self.assertNotIn(b['id'], r['comparison']['relevant_pressure_ids'])
                self.assertEqual(s['box_evidence'][day][b['id']]['observation']['whole_range_location'], 'NOT_COMPARABLE_AFTER_GAP')
            refs = [p for p in r['reference_candidates'] if p['path']['last_relation']=='NOT_COMPARABLE_AFTER_GAP']; self.assertTrue(refs)
            self.assertTrue(all(p['distance_to_anchor'] is None for p in refs))
            self.assertEqual(s['input_bindings'][day]['historical_available_at'], 'UNKNOWN')
            self.assertEqual(s['input_bindings'][day]['source_role'], 'RETAINED_OFFICIAL_PARENT_NOT_FINMIND')
        old = next(s for s in self.old['series'] if s['code']=='2884')['results'][-1]
        current = {b['id']: b for b in s['results'][-1]['boxes']}
        for b in old['boxes']:
            if b['confirmed_at'] < '2026-07-01':
                self.assertIn(b['id'], current)
                for key in ('research_bounds','display_extent','confirmed_at','source_turn_ids'): self.assertEqual(current[b['id']][key], b[key])

    def test_6488_8069_returns_keep_prior_failure_and_pending_qualifications(self):
        for code, expected in self.expected['return_counterexamples'].items():
            r = self.frame(code, expected['event']['date'])
            b = next(b for b in r['boxes'] if b['id']==expected['box_id'])
            self.assertIn(expected['event'], b['path']['events'])
            self.assertLess(b['path']['first_breakdown_at'], expected['event']['date'])
            self.assertEqual(b['path']['last_close_location'], 'INSIDE')
            self.assertEqual(self.series(code)['box_evidence'][r['as_of']][b['id']]['history']['lifecycle'], 'UNKNOWN_RETURN_IS_NOT_FORMAL_REACTIVATION')
            last = self.series(code)['results'][-1]
            self.assertTrue(last['pending_extrema'])
            self.assertEqual(last['context']['volume_unit'], 'SHARES_REPORTED')
            old = next(s for s in self.old['series'] if s['code']==code)['results'][-1]
            self.assertEqual(last['pivots'], old['pivots'])
            self.assertEqual([b['id'] for b in last['boxes']], [b['id'] for b in old['boxes']])

    def test_future_mutation_truncation_and_projection_input_unchanged(self):
        for code, day in (('1101','2025-05-14'), ('2884','2026-07-21')):
            p = next(p for p in self.parent['history_series'] if p['code']==code)
            payload = bind_input(input_for(p,p['frames'][-1]), self.spec, code); saved = deepcopy(payload)
            expected = analyze(payload, as_of=day)
            prefix = deepcopy(payload); prefix['bars'] = [r for r in prefix['bars'] if r['date']<=day]
            self.assertEqual(expected, analyze(prefix, as_of=day))
            changed = deepcopy(payload)
            for row in changed['bars']:
                if row['date'] > day: row.update(high='NaN', close='INVALID_FUTURE')
            changed['basis_break_dates'].append('2099-01-01')
            self.assertEqual(expected, analyze(changed, as_of=day))
            self.assertEqual(input_binding(payload,self.spec,code,day), input_binding(changed,self.spec,code,day))
            before = deepcopy(expected); e = layers(expected, payload['bars'])
            self.assertEqual(expected,before); self.assertEqual(payload,saved)
            self.assertEqual(e, layers(analyze(changed,as_of=day), changed['bars']))

    def test_synthetic_gap_missing_price_and_no_gap_projection(self):
        cases = json.loads((HERE/'synthetic-input.json').read_text())['cases']
        for c in cases:
            r = analyze(c['input'], as_of=c['as_of']); before = deepcopy(r)
            e = layers(r,c['input']['bars']); self.assertEqual(r,before)
            if c['id'] in ('basis-break','missing-price','missing-session'):
                stopped = [b for b in r['boxes'] if not b['usable_at_anchor']]; self.assertTrue(stopped)
                for b in stopped:
                    o = e[b['id']]['observation']; self.assertIsNone(o['pressure_distance_fraction'])
                    self.assertEqual(o['whole_range_location'],'NOT_COMPARABLE_AFTER_GAP')
                    self.assertTrue(o['stopped_at']); self.assertTrue(o['events'])
                    self.assertEqual(o['completed_records'][-1][1], 'NOT_COMPARABLE_AFTER_GAP')
            else:
                self.assertTrue(all(b['usable_at_anchor'] for b in r['boxes']))
                self.assertTrue(all(e[b['id']]['observation']['pressure_distance_fraction']==b['pressure_distance_fraction'] for b in r['boxes']))


if __name__=='__main__': unittest.main()
