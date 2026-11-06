"""Offline source, precision and fail-closed tests for the issuer supplement."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
import urllib.error

from graph_core.core import fingerprint
from . import official_action_capture as capture
from . import official_actions as facts
from .action_sources import HERE


class OfficialActionFacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = facts.build()
        cls.original = json.loads((HERE / 'action_data_20261022/events.json').read_text())
        cls.minutes_text = facts.read_pdf_text('esun-2025-minutes')[0]
        cls.stock = next(e for e in cls.result['catalog']['events'] if e['type'] == 'STOCK_DIVIDEND')

    def test_actual_dated_issue_par_is_sourced_not_assumed(self):
        m = self.result['minutes']
        self.assertEqual(m['meeting_date'], '2025-06-13')
        self.assertEqual(m['fiscal_year'], 2024)
        self.assertEqual(m['par_value'], '10')
        self.assertEqual(m['issue_pdf_page'], 19)
        self.assertEqual(m['resolution_pdf_page'], 20)
        self.assertEqual(m['shareholder_issue_amount'], '1602000000')
        self.assertEqual(m['shareholder_issue_shares'], '160200000')

    def test_final_published_money_not_approximate_meeting_ratio(self):
        self.assertEqual(self.stock['stock_dividend_money_per_share'], '0.10015129')
        self.assertEqual(self.stock['shares_per_share'], '0.010015129')
        self.assertNotEqual(self.stock['shares_per_share'], '0.01')
        self.assertFalse(self.result['minutes']['proposal_is_final_ratio'])
        self.assertIn('NOT_EXACT_UNROUNDED_ALLOTMENT', self.stock['ratio_role'])

    def test_record_ex_completion_and_tradability_remain_distinct(self):
        self.assertEqual(self.stock['ex_date'], '2025-07-22')
        self.assertEqual(self.stock['record_date'], '2025-07-28')
        self.assertEqual(self.stock['issuer_completion']['issuer_reported_distribution_completed_on'], '2025-08-27')
        self.assertIsNone(self.stock['tradable_date'])
        self.assertIsNone(self.stock['issuer_completion']['investor_receipt_at'])
        self.assertIsNone(self.stock['issuer_completion']['investor_net_amount'])

    def test_fraction_policy_is_not_actual_holder_disposition(self):
        self.assertIn('PAR_CASH_TO_WHOLE_TWD', self.stock['fractional_policy'])
        self.assertIsNone(self.stock['fractional_deadline'])
        self.assertIsNone(self.stock['fractional_disposition'])
        self.assertEqual(self.result['minutes']['cash_distribution_rounding'], 'FLOOR_TO_WHOLE_TWD_REMAINDER_TO_ISSUER')

    def test_original_cash_components_and_coverage_qualifications_unchanged(self):
        catalog = self.result['catalog']
        self.assertEqual([e for e in catalog['events'] if e['type'] == 'CASH_DIVIDEND'],
                         [e for e in self.original['events'] if e['type'] == 'CASH_DIVIDEND'])
        self.assertEqual(len(catalog['events']), 5)
        for code in catalog['coverage']:
            for key in ('status', 'start', 'end', 'other_actions_checked', 'gaps'):
                self.assertEqual(catalog['coverage'][code][key], self.original['coverage'][code][key])
        self.assertFalse(catalog['total_net_return_qualified'])
        self.assertFalse(catalog['historical_signal_eligible'])
        self.assertIsNone(catalog['primary_pressure_id'])
        self.assertIsNone(self.stock['announced_at'])

    def test_component_lineage_fingerprint_and_every_field_source_resolve(self):
        self.assertEqual(self.stock['id'], fingerprint({k: v for k, v in self.stock.items() if k != 'id'}))
        old = next(e for e in self.original['events'] if e['type'] == 'STOCK_DIVIDEND')
        self.assertEqual(self.stock['supersedes_event_id'], old['id'])
        self.assertNotEqual(self.stock['id'], old['id'])
        self.assertEqual(self.stock['original_component_observed_at'], old['observed_at'])
        self.assertGreater(self.stock['observed_at'], old['observed_at'])
        for e in self.result['catalog']['events']:
            for proofs in e['field_sources'].values():
                for p in proofs:
                    self.assertIn(p['source_id'], self.result['catalog']['sources'])
        self.assertIn(self.stock['id'], self.result['catalog']['coverage']['2884']['event_ids'])
        self.assertNotIn(old['id'], self.result['catalog']['coverage']['2884']['event_ids'])

    def test_document_join_mismatches_rejected_without_mutating_inputs(self):
        sources = self.result['source_manifest']['sources']
        before = deepcopy(self.original)
        for field, value in [('meeting_date', '2025-06-14'), ('issuer_record_date', '2025-07-29'),
                             ('issuer_reported_distribution_completed_on', '2025-08-28')]:
            with self.subTest(field=field):
                f = deepcopy(self.result['follow_up']); f[field] = value
                with self.assertRaises(ValueError):
                    facts.supplement_catalog(self.original, self.result['minutes'], f, sources)
        self.assertEqual(self.original, before)

    def test_unapproved_or_inconsistent_issue_cannot_supply_par(self):
        for changed in (self.minutes_text.replace('每 股 面 額 10 元', '每 股 面 額 5 元'),
                        self.minutes_text.replace('本案表決通過', '尚未通過'),
                        self.minutes_text.replace('按 面 額 折 發 現 金', '待定')):
            with self.assertRaises(ValueError):
                facts.parse_minutes(changed)

    def test_wrong_or_uncompleted_followup_cannot_confirm_payment(self):
        text = facts.read_pdf_text('esun-2025-follow-up', variant='.reading-order')[0]
        with self.assertRaises(ValueError):
            facts.parse_follow_up(text.replace('發放完畢', '預定發放'))
        # Old layout interleaves the decision column; retained failure is not silently accepted.
        with self.assertRaises(ValueError):
            facts.parse_follow_up(facts.read_pdf_text('esun-2025-follow-up')[0])

    def test_numeric_ratio_has_no_implicit_par_or_float_rounding(self):
        self.assertEqual(facts.stock_ratio('0.123456789123456789', '10'), '0.0123456789123456789')
        for money, par in [('1', None), ('1', '0'), ('1', '-10'), ('NaN', '10'), ('1', 'Infinity'), ('-1', '10')]:
            with self.assertRaises(ValueError):
                facts.stock_ratio(money, par)

    def test_security_page_http_200_is_unusable_not_empty_action_register(self):
        body, _, meta = facts.read_capture('mops-announcements-entry')
        self.assertEqual(meta['http'], 200)
        self.assertTrue(facts.security_denial(body))
        self.assertFalse(self.result['source_manifest']['mops']['usable'])
        with self.assertRaisesRegex(ValueError, 'Not an official PDF'):
            facts.read_pdf_text('mops-announcements-entry')

    def test_pdf_and_extracted_text_tampering_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            raw = Path(td) / 'raw'; raw.mkdir()
            name = 'esun-2025-minutes'
            for p in (facts.OUT / 'raw').glob(name + '.*'):
                (raw / p.name).write_bytes(p.read_bytes())
            for suffix in ('.response', '.txt'):
                path = raw / (name + suffix); before = path.read_bytes(); path.write_bytes(before + b'corrupt')
                with self.assertRaisesRegex(ValueError, 'fingerprint'):
                    facts.read_pdf_text(name, Path(td))
                path.write_bytes(before)

    def test_all_windows_still_refuse_with_other_missing_sources(self):
        audit = self.result['windows']
        self.assertEqual(len(audit['windows']), 72)
        self.assertEqual(audit['calendar_qualified_windows'], 70)
        self.assertEqual(audit['total_net_return_qualified_windows'], 0)
        self.assertIsNone(audit['ranking'])
        for w in audit['windows']:
            if w['end'] is None:
                continue
            self.assertEqual(w['status'], 'REFUSED_INCOMPLETE_EVENT_ACCOUNTING')
            self.assertIn('OPENING_ENTITLEMENTS_UNKNOWN', w['refusal_reasons'])
            self.assertIn('NET_DISTRIBUTIONS_TAX_FEES_UNKNOWN', w['refusal_reasons'])
            self.assertTrue(any(x.startswith('ACTION_COVERAGE_INCOMPLETE') for x in w['refusal_reasons']))

    def test_rebuild_is_deterministic_and_does_not_change_prior_catalog(self):
        self.assertEqual(facts.build(), self.result)
        self.assertEqual(json.loads((HERE / 'action_data_20261022/events.json').read_text()), self.original)


class ExplicitCapture(unittest.TestCase):
    URL = 'https://www.esunbank.com/official.pdf'

    def test_unsupported_prohibited_and_nonhttps_never_reach_network(self):
        client = Mock(); client.open.side_effect = AssertionError('Network attempted')
        for url in ('http://www.esunbank.com/doc', 'https://other.com/doc',
                    'https://www.esunbank.com:443/doc', 'https://mops.twse.com.tw/TWT49U',
                    'https://mops.twse.com.tw/twtauu'):
            with self.assertRaises(ValueError):
                capture.capture('test', url, opener=client)
        client.open.assert_not_called()

    def test_failed_redirect_is_preserved_without_following_or_retry(self):
        with tempfile.TemporaryDirectory() as td:
            client = Mock()
            client.open.side_effect = urllib.error.HTTPError(self.URL, 302, 'Moved', {'Location': 'https://unapproved.example/doc'}, None)
            first = capture.capture('redirect', self.URL, td, client)
            self.assertEqual(first['status'], 'FAILED')
            self.assertEqual(first['http'], 302)
            self.assertEqual(first['location'], 'https://unapproved.example/doc')
            self.assertFalse((Path(td) / 'raw/redirect.response').exists())
            self.assertEqual(capture.capture('redirect', self.URL, td, client), first)
            self.assertEqual(client.open.call_count, 1)
            self.assertIsNone(capture.NoRedirect().redirect_request(None, None, 302, None, {}, self.URL))

    def test_transport_success_is_cached_but_not_data_qualification(self):
        with tempfile.TemporaryDirectory() as td:
            body = b'FOR SECURITY REASONS, THIS PAGE CAN NOT BE ACCESSED.'
            response = io.BytesIO(body); response.status = 200; response.url = self.URL; response.headers = {'Content-Type': 'text/html'}
            client = Mock(); client.open.return_value = response
            meta = capture.capture('denied', self.URL, td, client)
            self.assertEqual(meta['status'], 'CAPTURED')
            self.assertEqual(meta['sha256'], hashlib.sha256(body).hexdigest())
            self.assertTrue(facts.security_denial(body))
            self.assertEqual(capture.capture('denied', self.URL, td, client), meta)
            self.assertEqual(client.open.call_count, 1)
            (Path(td) / 'raw/denied.response').write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'changed'):
                capture.capture('denied', self.URL, td, client)


if __name__ == '__main__':
    unittest.main()
