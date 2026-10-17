"""Adapter acceptance against the unchanged core, causal prefixes and exact bytes.

All fixtures here are synthetic engineering inputs, not market classifications.
Browser rendering and downloaded bytes are tested separately in real Chromium.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from product_candidate.attempt_evidence import evaluate
from product_candidate.attempt_view import build_case, build_bundle, export, render, HTML_NAME

SOURCES = ROOT / 'product_candidate/attempt_sources.json'
MANIFEST = json.loads(SOURCES.read_text())


def fixture(case_id='explicit_101_106'):
    metadata = next(c for c in MANIFEST['cases'] if c['id'] == case_id)
    payload = json.loads((SOURCES.parent / metadata['input']).read_text())
    return payload, deepcopy(metadata)


class AttemptViewTests(unittest.TestCase):
    def test_every_display_selection_is_exact_independent_core_prefix(self):
        for metadata in MANIFEST['cases']:
            payload, _ = fixture(metadata['id'])
            case = build_case(payload, metadata)
            for i, view in enumerate(case['views']):
                with self.subTest(case=metadata['id'], index=i):
                    prefix = deepcopy(payload); prefix['observations'] = prefix['observations'][:i+1]
                    selection = json.loads(view['selection_text'])
                    self.assertEqual(selection['input'], prefix)
                    self.assertEqual(selection['result'], evaluate(prefix))
                    self.assertEqual(view['frame']['frame_id'], selection['result']['frames'][-1]['frame_id'])
                    self.assertEqual(view['selection_sha256'], sha256(view['selection_text'].encode()).hexdigest())
                    self.assertEqual(selection['action_qualification'], 'NOT_EVALUATED')

    def test_truncated_or_changed_future_input_does_not_rewrite_earlier_view_or_download(self):
        payload, metadata = fixture()
        full = build_case(payload, metadata)
        for n in range(1, len(payload['observations'])+1):
            shortened = deepcopy(payload); shortened['observations'] = shortened['observations'][:n]
            self.assertEqual(build_case(shortened, metadata)['views'], full['views'][:n])
        changed = deepcopy(payload)
        changed['observations'][-1].update(high='999', last='999')
        self.assertEqual(build_case(changed, metadata)['views'][:-1], full['views'][:-1])

    def test_early_view_has_no_later_volume_high_or_106_event(self):
        payload, metadata = fixture(); view = build_case(payload, metadata)['views'][0]
        result = json.loads(view['selection_text'])
        self.assertEqual(view['chart']['daily'][-1]['high'], '101.5')
        self.assertEqual(view['frame']['volume_shares'], '4500')
        self.assertEqual(len(view['chart']['intraday']['points']), 1)
        self.assertEqual(view['chart']['intraday']['points'][0]['observed_at'], '2026-09-14T09:10:00+08:00')
        self.assertFalse(any(e['kind'] == 'VOLUME_LEAD_OBSERVED' for e in view['events']))
        self.assertFalse(any(e['reference_id'] == 'LEFT_ZONE_UPPER' for e in view['events']))
        self.assertEqual(len(result['input']['observations']), 1)
        self.assertFalse(any(r['date'] > '2026-09-14' for r in view['chart']['daily']))

    def test_new_day_keeps_previous_completed_bar_but_current_bar_is_unfinished(self):
        payload, metadata = fixture(); view = build_case(payload, metadata)['views'][3]
        yesterday, today = view['chart']['daily'][-2:]
        self.assertEqual(yesterday['date'], '2026-09-14')
        self.assertEqual(yesterday['close'], '102')
        self.assertTrue(yesterday['is_close'])
        self.assertEqual(today['high'], '107')
        self.assertFalse(today['is_close'])
        self.assertEqual(len(view['chart']['intraday']['points']), 1)

    def test_daily_only_source_has_no_manufactured_intraday_path_or_order(self):
        payload, metadata = fixture('completed_days')
        for view in build_case(payload, metadata)['views']:
            self.assertEqual(view['chart']['intraday']['status'], 'INTRADAY_DATA_MISSING')
            self.assertEqual(view['chart']['intraday']['points'], [])
            self.assertFalse(any(e['kind'].startswith('INTRADAY_') for e in view['events']))
            self.assertTrue(any('盤中觀察' in s for s in view['presentation']['missing']))
        payload, metadata = fixture('daily_order'); view = build_case(payload, metadata)['views'][0]
        self.assertIn('先後未知', view['presentation']['volume_text'])
        self.assertNotIn('VOLUME_LEAD_OBSERVED', [e['kind'] for e in view['events']])

    def test_missing_volume_remains_unknown_without_revoking_101_price_condition(self):
        payload, metadata = fixture('missing_volume'); view = build_case(payload, metadata)['views'][0]
        self.assertIsNone(view['chart']['volume_benchmark'])
        self.assertIsNone(view['frame']['left_zone_max_volume_shares'])
        self.assertEqual(view['frame']['volume_relation'], 'UNKNOWN')
        self.assertEqual(view['frame']['attempt_levels'][0]['price_attempt_condition'], 'MET')
        self.assertIn('未知', view['presentation']['volume_text'])

    def test_fall_back_below_106_does_not_erase_101_or_prior_attempt_events(self):
        payload, metadata = fixture(); views = build_case(payload, metadata)['views']
        fallen = views[5]
        self.assertEqual([r['price_attempt_condition'] for r in fallen['frame']['attempt_levels']], ['MET','NOT_MET'])
        kinds = [(e['reference_id'], e['kind']) for e in fallen['events']]
        self.assertIn(('LEFT_ZONE_UPPER','CLOSE_CROSSED_ABOVE'), kinds)
        self.assertIn(('LEFT_ZONE_UPPER','CLOSE_RETURNED_BELOW'), kinds)
        self.assertNotIn(('NEAR_HIGH','CLOSE_RETURNED_BELOW'), kinds)
        self.assertEqual(views[0]['events'], fallen['events'][:len(views[0]['events'])])

    def test_arbitrary_size_integer_input_and_subcent_price_survive_download(self):
        payload, metadata = fixture('integer_precision'); view = build_case(payload, metadata)['views'][0]
        downloaded = json.loads(view['selection_text'])
        self.assertEqual(downloaded['input']['history'][1]['volume_shares'], 9007199254740993)
        self.assertEqual(view['frame']['left_zone_max_volume_shares'], '9007199254740993')
        self.assertEqual(view['frame']['volume_shares'], '9007199254740994')
        self.assertEqual(view['chart']['volume_benchmark'], '9007199254740993')
        payload, metadata = fixture('price_precision'); view = build_case(payload, metadata)['views'][0]
        self.assertEqual(view['frame']['current_price'], '101.0000000000000001')
        self.assertEqual(view['frame']['attempt_levels'][0]['price_attempt_condition'], 'MET')
        self.assertIn('101.0000000000000001', view['selection_text'])

    def test_adjusted_is_separate_and_never_rebased_by_the_adapter(self):
        payload, metadata = fixture('adjusted_basis'); view = build_case(payload, metadata)['views'][0]
        result = json.loads(view['selection_text'])
        self.assertEqual(result['input']['context']['adjustment_anchor'], '2026-09-14')
        self.assertEqual(result['input'], dict(payload, observations=payload['observations'][:1]))
        self.assertEqual(result['result']['context']['price_mode'], 'ADJUSTED_CANDIDATE')

    def test_real_source_incomplete_references_and_unverified_coverage_are_not_promoted(self):
        payload, metadata = fixture()
        invalid = deepcopy(metadata); invalid['data_kind'] = 'REAL_MARKET'
        with self.assertRaisesRegex(ValueError, 'authentication'): build_case(payload, invalid)
        invalid = deepcopy(metadata); invalid['history_coverage'] = 'COMPLETE'
        with self.assertRaisesRegex(ValueError, 'partial history'): build_case(payload, invalid)
        incomplete = deepcopy(payload); incomplete['references']['left_zone']['bar_dates'] = []
        with self.assertRaises(ValueError): build_case(incomplete, metadata)
        future = deepcopy(payload); future['references']['known_at'] = '2026-09-16T14:00:00+08:00'
        with self.assertRaises(ValueError): build_case(future, metadata)

    def test_bundle_is_deterministic_and_has_unique_explicit_sources(self):
        first = build_bundle(SOURCES)
        self.assertEqual(first, build_bundle(SOURCES))
        self.assertEqual(len(first['cases']), 7)
        self.assertEqual(sum(len(c['views']) for c in first['cases']), 28)
        for case in first['cases']:
            self.assertEqual(case['info']['data_kind'], 'SYNTHETIC_ENGINEERING_FIXTURE')
            self.assertTrue(all(v['frame']['probability_estimate'] is None for v in case['views']))

    def test_export_preflights_conflicts_and_refuses_symlinks_without_partial_new_files(self):
        payload, metadata = fixture('price_precision')
        bundle = dict(cases=[build_case(payload, metadata)], bundle_id='TEST')
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp); (p/HTML_NAME).write_text('existing candidate')
            with self.assertRaisesRegex(ValueError, 'overwrite'): export(bundle, p)
            self.assertFalse((p/'attempt-candidate.json').exists())
            self.assertEqual((p/HTML_NAME).read_text(), 'existing candidate')
            (p/HTML_NAME).unlink(); (p/HTML_NAME).symlink_to(p/'missing-target')
            with self.assertRaises(ValueError): export(bundle, p)
            (p/HTML_NAME).unlink()
            self.assertTrue(all(value == 'CREATED' for value in export(bundle, p).values()))
            self.assertTrue(all(value == 'EXISTING' for value in export(bundle, p).values()))

    def test_source_manifest_rejects_duplicates_and_external_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp); metadata = deepcopy(MANIFEST['cases'][0])
            metadata['input'] = '../outside.json'
            source = p/'sources.json'; source.write_text(json.dumps(dict(schema_version='attempt-view-sources/0.1', cases=[metadata])))
            with self.assertRaisesRegex(ValueError, 'below'): build_bundle(source)
            payload, metadata = fixture(); (p/'input.json').write_text(json.dumps(payload))
            metadata['input'] = 'input.json'
            source.write_text(json.dumps(dict(schema_version='attempt-view-sources/0.1', cases=[metadata,metadata])))
            with self.assertRaisesRegex(ValueError, 'Duplicate'): build_bundle(source)

    def test_renderer_escapes_source_and_browser_only_uses_exact_prebuilt_download(self):
        payload, metadata = fixture('price_precision')
        metadata['label'] = '</script><script>INJECTED()</script>'
        html = render(dict(cases=[build_case(payload,metadata)]))
        self.assertNotIn('</script><script>INJECTED()', html)
        self.assertIn("connect-src 'none'", html)
        script = (ROOT/'product_candidate/attempt_viewer.js').read_text()
        self.assertIn('new Blob([current.selection_text]', script)
        for forbidden in ['fetch(', 'XMLHttpRequest', 'WebSocket', 'localStorage', 'innerHTML', 'JSON.stringify(current.selection_text)']:
            self.assertNotIn(forbidden, script)

    def test_adapter_does_not_import_original_engines_stores_or_ui_modules(self):
        process = subprocess.run([sys.executable, '-c',
            "import sys; import product_candidate.attempt_view; "
            "assert not {'analysis_store','structure','cross_view','streamlit'}.intersection(sys.modules)"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)


if __name__ == '__main__':
    unittest.main()
