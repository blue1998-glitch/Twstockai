"""M2-3 synthetic-only intake controls. No live queries or quote fixtures."""
from copy import deepcopy
from decimal import Decimal, Inexact, ROUND_FLOOR, getcontext, setcontext
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from graph_core.core import analyze
from graph_core.finmind_adapter import (IntakeError, analyze_response, public_summary,
                                       assess_integer_lot_display)
from graph_core.finmind_run import (run, external_path, PARAMETERS, ENDPOINT, REPOSITORY, _parse)

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]


def fixture():
    return json.loads((HERE / 'input.json').read_text())


def compute(job):
    return analyze_response(job['response'], job['request'])


class FinMindTests(unittest.TestCase):
    def test_mapping_matches_unchanged_core_and_input_unchanged(self):
        job = fixture(); before = deepcopy(job); result = compute(job)
        self.assertEqual(job, before)
        self.assertEqual(result['analysis'], analyze(result['graph_input'], as_of=job['request']['as_of']))
        for row, bar in zip(job['response']['data'], result['graph_input']['bars']):
            self.assertEqual(bar['volume_shares_scaled'], row['Trading_Volume'])
            for target, field in [('open','open'),('high','max'),('low','min'),('close','close')]:
                self.assertEqual(bar[target], row[field])
            self.assertIsNone(bar['available_at'])

    def test_frozen_refusal_inputs(self):
        for case in json.loads((HERE / 'refusal-inputs.json').read_text()):
            with self.subTest(case=case['id']):
                with self.assertRaisesRegex(IntakeError, '^' + case['expected'] + '$'):
                    compute(case['input'])

    def test_future_prefix_and_full_integrity_are_separate(self):
        job = fixture(); before = compute(job)
        short = deepcopy(job)
        short['response']['data'] = [r for r in short['response']['data'] if r['date'] <= job['request']['as_of']]
        changed = deepcopy(job)
        for row in changed['response']['data']:
            if row['date'] > job['request']['as_of']:
                row.update(open='300', max='301', min='299', close='300', Trading_Volume='999')
        for other in (short, changed):
            after = compute(other)
            self.assertEqual(before['analysis'], after['analysis'])
            self.assertEqual(before['graph_input'], after['graph_input'])
            self.assertNotEqual(before['provenance']['response_identity'], after['provenance']['response_identity'])
        self.assertNotIn('2026-07-22', json.dumps(before['analysis']))
        later = deepcopy(job); later['request']['as_of'] = '2026-07-22'
        self.assertEqual(compute(later)['analysis']['anchor']['date'], '2026-07-22')

    def test_basis_reset_keeps_unknown_and_stops_old_references(self):
        result = compute(fixture()); core = result['analysis']; cutoff = '2026-07-01'
        self.assertEqual(core['data_gaps']['basis_resets'], [cutoff])
        self.assertTrue(core['reference_candidates'])
        self.assertTrue(any(p['path']['last_relation'] == 'NOT_COMPARABLE_AFTER_GAP'
                            for p in core['reference_candidates'] if p['confirmed_at'] < cutoff))
        for box in core['boxes']:
            self.assertFalse(box['start'] < cutoff <= box['source_end'])
        summary = public_summary(result)
        self.assertFalse(summary['continuous_structure_qualified'])
        self.assertEqual(summary['corporate_action_type'], 'UNKNOWN')
        self.assertIsNone(summary['primary_pressure_id'])

    def test_volume_zero_is_data_but_integer_lots_cannot_verify_shares(self):
        job = fixture(); job['response']['data'][0]['Trading_Volume'] = 0
        self.assertEqual(compute(job)['graph_input']['bars'][0]['volume_shares_scaled'], '0')
        display = assess_integer_lot_display(official_unit='成交張數', displayed_value='1,234')
        self.assertFalse(display['exact_shares_verified'])
        self.assertEqual(display['exact_shares_status'], 'UNKNOWN')
        self.assertNotIn('volume_shares_scaled', display)
        with self.assertRaises(IntakeError):
            assess_integer_lot_display(official_unit='UNKNOWN', displayed_value='1')

    def test_retrieval_day_gate_uses_equivalent_timezones(self):
        job = fixture()
        for stamp in ('2026-07-22T23:59:59+08:00', '2026-07-22T15:59:59+00:00'):
            job['request']['retrieved_at'] = stamp
            with self.assertRaisesRegex(IntakeError, 'INCOMPLETE_DAY'):
                compute(job)
        results = []
        for stamp in ('2026-07-23T00:00:00+08:00', '2026-07-22T16:00:00+00:00'):
            job['request']['retrieved_at'] = stamp; results.append(compute(job))
        self.assertEqual(results[0]['analysis'], results[1]['analysis'])
        self.assertEqual(results[0]['provenance']['historical_available_at'], 'UNKNOWN')

    def test_decimal_context_isolation(self):
        job = fixture(); before = deepcopy(job); expected = compute(job)
        original = getcontext().copy()
        try:
            ctx = getcontext(); ctx.prec = 3; ctx.rounding = ROUND_FLOOR
            ctx.Emin = -3; ctx.Emax = 3; ctx.traps[Inexact] = True
            snapshot = repr(ctx), dict(ctx.flags), dict(ctx.traps)
            self.assertEqual(compute(job), expected)
            self.assertEqual((repr(ctx), dict(ctx.flags), dict(ctx.traps)), snapshot)
        finally:
            setcontext(original)
        self.assertEqual(job, before)

    def test_pure_adapter_has_no_io(self):
        job = fixture()
        with patch('builtins.open', side_effect=AssertionError('file IO')), \
                patch('socket.socket', side_effect=AssertionError('network')):
            result = compute(job)
        self.assertEqual(result['analysis']['context']['code'], '2884')

    def test_public_allowlist_excludes_reconstructable_quote_data(self):
        job = fixture(); job['request']['source_id'] = 'RESTRICTED_SOURCE_ID_CANARY'
        result = compute(job); safe = public_summary(result); text = json.dumps(safe)
        for key in ('anchor', 'bars', 'pivots', 'reference_candidates', 'response_identity', 'RESTRICTED_SOURCE_ID_CANARY'):
            self.assertNotIn(key, text)
        for key in ('data_qualified', 'execution_model_qualified', 'historical_signal_eligible',
                    'policy_authorized', 'live_execution_authorized'):
            self.assertIs(safe[key], False)

    def test_repository_output_and_symlink_paths_refused(self):
        with self.assertRaisesRegex(IntakeError, 'INSIDE_REPOSITORY'):
            run(output_dir=REPOSITORY / 'restricted-must-not-be-created')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'link').symlink_to(REPOSITORY, target_is_directory=True)
            with self.assertRaises(IntakeError): external_path(root / 'link' / 'raw')
            (root / '.git').write_text('gitdir: elsewhere')
            with self.assertRaisesRegex(IntakeError, 'INSIDE_GIT_TREE'): external_path(root / 'raw')
        self.assertFalse((REPOSITORY / 'restricted-must-not-be-created').exists())

    def test_json_original_lexemes_duplicates_nonfinite(self):
        self.assertEqual(str(_parse('{"price":1.12345678901234567890}')['price']), '1.12345678901234567890')
        self.assertIsInstance(_parse('{"price":1.2}')['price'], Decimal)
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.assertRaises(IntakeError): _parse(raw)

    def test_file_run_reuses_saved_response_and_safe_summary(self):
        job = fixture(); original = deepcopy(job)
        official = [dict(date=r['date'], open=r['open'], high=r['max'], low=r['min'],
                         close=r['close'], volume_shares_scaled=r['Trading_Volume']) for r in job['response']['data']]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); response = root / 'response.json'; acquisition = root / 'acquisition.json'
            raw = json.dumps(job['response']).encode(); response.write_bytes(raw)
            acquisition.write_text(json.dumps(dict(endpoint=ENDPOINT, parameters=PARAMETERS, http_status=200,
                response_sha256=hashlib.sha256(raw).hexdigest(), requested_at=job['request']['retrieved_at'])))
            with patch('graph_core.finmind_run.urlopen', side_effect=AssertionError('must not query')), \
                    patch('graph_core.finmind_run._retained_sources', return_value=(official, [], job['request']['basis_warnings'])), \
                    patch('graph_core.finmind_run._volume_precision_8069', return_value={'status':'SYNTHETIC_CONTROL'}):
                original_context = getcontext().copy()
                try:
                    getcontext().prec = 3; getcontext().rounding = ROUND_FLOOR
                    getcontext().traps[Inexact] = True
                    snapshot = repr(getcontext()), dict(getcontext().flags), dict(getcontext().traps)
                    result = run(output_dir=root / 'run', response_path=response, acquisition_path=acquisition)
                    self.assertEqual((repr(getcontext()), dict(getcontext().flags), dict(getcontext().traps)), snapshot)
                finally:
                    setcontext(original_context)
            self.assertEqual(result['status'], 'LIMITED_RESEARCH_COMPLETED')
            self.assertEqual(json.loads((root / 'run/public-summary.json').read_text()), result)
            self.assertTrue(result['prefix_control']['analysis_equal'])
            for p in (root / 'run').iterdir(): self.assertEqual(p.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                run(output_dir=root / 'run', response_path=response, acquisition_path=acquisition)
        self.assertEqual(job, original)

    def test_request_cannot_expand_approved_window(self):
        for key, value in [('start_date', '2026-02-28'), ('end_date', '2026-07-23')]:
            job = fixture(); job['request'][key] = value
            with self.assertRaisesRegex(IntakeError, 'UNSUPPORTED_SCOPE'): compute(job)

    def test_blocked_http_is_not_retried(self):
        error = HTTPError(ENDPOINT, 403, 'forbidden', {}, None)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'blocked'
            with patch('graph_core.finmind_run.urlopen', side_effect=error) as fetch:
                with self.assertRaisesRegex(IntakeError, 'NO_RETRY'): run(output_dir=out)
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(json.loads((out / 'blocked.json').read_text())['status'], 'BLOCKED')

    def test_frozen_inputs_and_old_sources_unchanged(self):
        baseline = json.loads((HERE / 'baseline.json').read_text())
        for row in baseline['files']:
            raw = (PROJECT / row['path']).read_bytes()
            self.assertEqual(len(raw), row['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
        for name, digest in baseline['frozen'].items():
            self.assertEqual(hashlib.sha256((HERE / name).read_bytes()).hexdigest(), digest)


if __name__ == '__main__': unittest.main()
