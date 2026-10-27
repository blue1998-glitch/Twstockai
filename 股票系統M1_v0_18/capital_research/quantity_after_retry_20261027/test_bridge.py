"""Focused full-generator bridge checks; no old replay or suite execution."""
from copy import deepcopy
import hashlib
import socket
import subprocess
import unittest
from unittest.mock import patch

from capital_research import order_review  # Load source before the pure-call IO guard.
from capital_research.quantity_after_retry import generate_after_retry
from .fixtures import ROOT, REPO, load, materialize, fingerprint
from .verify import verify


def actual(name):
    return load(ROOT / 'after-final' / name / 'actual.json')


class BridgeTests(unittest.TestCase):
    def test_frozen_outcomes_and_independent_four_point_domain(self):
        cases = sorted((ROOT / 'cases').iterdir())
        self.assertEqual(len(cases), 20)
        for case in cases:
            with self.subTest(case=case.name):
                spec = load(case / 'input.json')
                request = materialize(spec)
                self.assertEqual(fingerprint(request), spec['materialized_input_id'])
                verify(request, load(case / 'expected.json'), actual(case.name))

    def test_original_book_latest_receipts_and_all_tokens_are_retained(self):
        spec = load(ROOT / 'cases/new-independent-trigger/input.json')
        request = materialize(spec)
        r = request['saved_result']['review']
        a = actual('new-independent-trigger')['adapter']
        cp = a['quantity_request']['continuation']['checkpoint']
        self.assertEqual(cp, request['checkpoint'])
        self.assertEqual(cp['execution_result'], r['execution'])
        self.assertEqual(cp['origin_ledger_input'], r['execution_job']['ledger_input'])
        self.assertEqual(a['binding']['received_attempt_ids'], [v['attempt_id'] for v in r['execution']['reassessment_attempts']])
        self.assertEqual([v['outcome'] for v in cp['execution_result']['reassessment_attempts']], ['REJECTED', 'ACCEPTED'])
        self.assertEqual(a['binding']['latest_decision_id'], r['execution']['latest_decision_id'])
        self.assertEqual(a['binding']['latest_common_account_id'], r['execution']['latest_common_account_id'])
        self.assertEqual(a['account']['cash_claims'], cp['state']['row']['cash_claims'])
        self.assertEqual(a['account']['share_claims'], cp['state']['row']['share_receivables'])
        self.assertEqual(len(a['binding']['reviewed_evidence_tokens']), 12)
        self.assertEqual(a['quantity_request']['decision_input']['consumed_evidence_tokens'], a['binding']['reviewed_evidence_tokens'])
        self.assertEqual(a['quantity_request']['batch_context']['account_id'], fingerprint(a['account']))
        self.assertEqual(a['binding']['origin_initial_capital'], '1430')
        self.assertEqual(a['generation']['research']['initial_capital'], '1425.100')

    def test_public_bridge_is_pure_and_never_calls_market_execution(self):
        request = materialize(load(ROOT / 'cases/new-independent-trigger/input.json'))
        before = deepcopy(request)
        blocked = AssertionError('Bridge must not RUN old retry, simulate, or perform IO')
        with patch('capital_research.execution.simulate', side_effect=blocked), \
             patch('capital_research.quantity_replay.simulate', side_effect=blocked), \
             patch('capital_research.quantity_replay.replay_sequence', side_effect=blocked), \
             patch('capital_research.conditional_retry.simulate', side_effect=blocked), \
             patch('capital_research.conditional_retry.retry_rejected', side_effect=blocked), \
             patch('builtins.open', side_effect=blocked), \
             patch.object(socket.socket, 'connect', side_effect=blocked), \
             patch.object(subprocess, 'Popen', side_effect=blocked):
            result = generate_after_retry(request)
        self.assertEqual(result, actual('new-independent-trigger'))
        self.assertEqual(request, before)
        for source in load(ROOT / 'intake.json')['source_originals']:
            raw = (REPO / source['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])

    def test_full_outer_gate_blocks_old_trigger_unknown_and_false_first_entry(self):
        for name in ('old-trigger', 'unknown-qualification'):
            a = actual(name)['adapter']
            self.assertEqual(a['status'], 'GENERATED')
            buys = [c for c in a['generation']['research']['candidates'] if c['plan'] and int(c['additional_B']) > 0]
            self.assertTrue(buys)
            self.assertTrue(all(not c['feasible_for_research'] for c in buys))
        self.assertIsNone(actual('false-first-entry')['adapter']['generation'])
        limited = actual('search-limit')['adapter']['generation']['research']
        self.assertEqual(limited['candidates'], [])
        self.assertFalse(limited['enumeration_complete'])

    def test_original_role_and_approval_reproduced_then_blocked_without_oracle_change(self):
        for name in ('wrong-incumbent-role', 'changed-original-approval'):
            before = load(ROOT / 'before-role-binding' / name / 'actual.json')['adapter']
            after = actual(name)['adapter']
            self.assertEqual(before['status'], 'GENERATED')
            self.assertEqual(after['status'], 'STOPPED_INPUT_ERROR')
            self.assertIsNone(after['generation'])
        incorrect_fix = load(ROOT / 'after-role-binding/wrong-incumbent-role/actual.json')['adapter']
        self.assertEqual(incorrect_fix['reasons'], ["'edge_budget'"])
        self.assertEqual(actual('wrong-incumbent-role')['adapter']['reasons'], ['INCUMBENT_DIFFERS_FROM_ORIGINAL_ROLE'])

    def test_integrity_metadata_is_separate_and_no_candidate_is_auto_selected(self):
        a = actual('new-independent-trigger')
        b = actual('integrity-metadata-control')
        self.assertEqual(a['adapter']['generation']['research'], b['adapter']['generation']['research'])
        self.assertNotEqual(a['source_integrity_metadata']['full_input_id'], b['source_integrity_metadata']['full_input_id'])
        for name in ('new-independent-trigger', 'old-trigger', 'integrity-metadata-control'):
            adapter = actual(name)['adapter']
            research = adapter['generation']['research']
            self.assertIsNone(adapter['selected_id'])
            self.assertIsNone(research['selected_id'])
            self.assertIsNone(research['ranking'])
            self.assertEqual(research['execution'], 'NOT_PERFORMED')
            self.assertEqual(research['order_generation'], 'NOT_PERFORMED')


if __name__ == '__main__':
    unittest.main()
