"""Tests for actual source admission and cross-case errors, not trading rules."""
from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from . import action_scope as scope
from . import action_scope_sources as source
from .action_sources import HERE
from .action_study import verified_quotes
from .source_qualification import build_calendar


def request(version, field, **overrides):
    result = {k: version[k] for k in ('family', 'issuer_code', 'entitled_old_code', 'action_type', 'old_instrument')}
    result.update(version_id=version['id'], field=field,
                  unit=version['fields'][field]['unit'], date_role=version['fields'][field]['date_role'],
                  observed_as_of=version['observed_at'], purpose='SOURCE_DIAGNOSTIC', historical_signal=False)
    result.update(overrides)
    return result


class ScopedEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = source.build_catalog()
        cls.stock = next(v for v in cls.catalog['inventory'] if v['action_type'] == 'STOCK_DIVIDEND')
        cls.proposal = next(v for v in cls.catalog['inventory'] if v['action_type'] == 'SHARE_EXCHANGE' and v['stage'] == 'BOARD_PROPOSAL')
        cls.scheduled = next(v for v in cls.catalog['inventory'] if v['stage'] == 'ANNOUNCED_SCHEDULE')
        cls.qa = next(v for v in cls.catalog['inventory'] if v['stage'] == 'CASE_SPECIFIC_QA_NOT_INVESTOR_RECEIPT')
        cls.tcc = next(v for v in cls.catalog['inventory'] if v['action_type'] == 'CASH_DISTRIBUTION_PROPOSAL')
        cls.old, cls.manifest = verified_quotes(); cls.calendar = build_calendar()

    def input(self, start='2026-08-03', end='2026-09-10'):
        return source.scoped_input(self.old, self.catalog, self.manifest, self.calendar, start, end, '2884')

    def test_direct_issuer_quantity_preserves_unit_and_published_precision(self):
        result = scope.resolve_field(self.stock, 'shares_per_share', request(self.stock, 'shares_per_share'))
        self.assertEqual(result['value'], '0.010015129')
        self.assertEqual(result['qualification'], 'DIRECT_PUBLISHED')
        event = next(e for e in self.catalog['events'] if e['type'] == 'STOCK_DIVIDEND')
        self.assertEqual(event['published_new_shares_per_thousand_old_shares'], '10.015129')
        self.assertEqual(event['shares_per_share'], result['value'])
        self.assertIsNone(event['tradable_date']); self.assertIsNone(event['announced_at'])
        self.assertIn('NOT_VERIFIED_UNROUNDED', event['ratio_role'])

    def test_decimal_conversion_requires_strings_and_never_defaults_units(self):
        self.assertEqual(scope.per_old_share('10.015129', '1000'), '0.010015129')
        self.assertEqual(scope.per_old_share('0.123456789123456789', '1000'), '0.000123456789123456789')
        for a, b in [(None, '1000'), ('1', None), ('1', '0'), ('NaN', '1'), ('1', 'Infinity'), (10.015129, '1000')]:
            with self.assertRaises(ValueError): scope.per_old_share(a, b)

    def test_target_shareholders_cannot_credit_existing_acquirer_shares(self):
        self.assertEqual(self.scheduled['entitled_old_code'], '2867')
        with self.assertRaisesRegex(ValueError, 'Wrong holder'):
            scope.resolve_field(self.scheduled, 'shares_per_share', request(self.scheduled, 'shares_per_share', entitled_old_code='2884'))

    def test_wrong_issuer_action_family_instrument_and_unit_rejected(self):
        for key, value in [('issuer_code', '2867'), ('action_type', 'STOCK_DIVIDEND'),
                           ('family', self.stock['family']), ('old_instrument', '2884_ORDINARY_OLD_SHARES'),
                           ('unit', 'NEW_2884_SHARES_PER_OLD_2884_SHARE')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                scope.resolve_field(self.scheduled, 'shares_per_share', request(self.scheduled, 'shares_per_share', **{key: value}))

    def test_two_ratio_versions_remain_separate_no_implicit_latest(self):
        self.assertEqual(scope.resolve_field(self.proposal, 'shares_per_share', request(self.proposal, 'shares_per_share'))['value'], '0.2486')
        self.assertEqual(scope.resolve_field(self.scheduled, 'shares_per_share', request(self.scheduled, 'shares_per_share'))['value'], '0.2596')
        with self.assertRaises(ValueError):
            scope.resolve_field(self.proposal, 'shares_per_share', request(self.proposal, 'shares_per_share', version_id=self.scheduled['id']))
        self.assertNotEqual(self.proposal['id'], self.scheduled['id'])
        self.assertEqual(self.catalog['version_relations'][0]['earlier_document_version'], self.proposal['id'])

    def test_document_claimed_time_not_authenticated_historical_signal(self):
        self.assertEqual(self.proposal['fields']['document_claimed_statement_at']['value'], '2025-11-05T17:37:58+08:00')
        self.assertEqual(self.scheduled['fields']['document_claimed_statement_at']['value'], '2026-07-13T15:03:17+08:00')
        for v in (self.stock, self.proposal, self.scheduled):
            self.assertIsNone(v['announced_at'])
            with self.assertRaisesRegex(ValueError, 'Historical availability'):
                scope.resolve_field(v, 'shares_per_share', request(v, 'shares_per_share', historical_signal=True))

    def test_evidence_observation_cutoff_rejects_future_capture_and_naive_time(self):
        before = (datetime.fromisoformat(self.stock['observed_at']) - timedelta(microseconds=1)).isoformat()
        with self.assertRaisesRegex(ValueError, 'not yet observed'):
            scope.resolve_field(self.stock, 'shares_per_share', request(self.stock, 'shares_per_share', observed_as_of=before))
        for cutoff in (None, '2026-10-23T00:00:00'):
            with self.assertRaises(ValueError):
                scope.resolve_field(self.stock, 'shares_per_share', request(self.stock, 'shares_per_share', observed_as_of=cutoff))

    def test_certificate_listing_cannot_be_dividend_ordinary_tradability(self):
        actual = scope.resolve_field(self.qa, 'certificate_listing_date', request(self.qa, 'certificate_listing_date'))
        self.assertEqual(actual['value'], '2026-09-01')
        for overrides in [dict(date_role='STOCK_DIVIDEND_ORDINARY_SHARE_TRADABILITY'),
                          dict(family=self.stock['family'], entitled_old_code='2884', version_id=self.stock['id'])]:
            with self.assertRaises(ValueError):
                scope.resolve_field(self.qa, 'certificate_listing_date', request(self.qa, 'certificate_listing_date', **overrides))

    def test_scheduled_effective_and_issuer_pay_date_not_interchangeable(self):
        self.assertEqual(self.scheduled['fields']['scheduled_effective_date']['value'], '2026-09-01')
        with self.assertRaises(ValueError):
            scope.resolve_field(self.stock, 'tentative_pay_date', request(self.stock, 'tentative_pay_date', date_role='SCHEDULED_SHARE_EXCHANGE_EFFECTIVE'))
        self.assertEqual(self.stock['fields']['tentative_pay_date']['value'], '2025-08-27')

    def test_unknown_tradability_not_filled_from_schedule_or_certificate(self):
        with self.assertRaisesRegex(ValueError, 'Unknown field'):
            scope.resolve_field(self.stock, 'tradable_date', request(self.stock, 'tradable_date'))
        self.assertIsNone(self.stock['fields']['tradable_date']['value'])

    def test_qa_fraction_and_fee_not_reusable_for_2025_dividend(self):
        self.assertEqual(self.qa['fields']['conditional_remittance_fee']['value'], '10')
        self.assertEqual(self.qa['fields']['fractional_rounding']['value'], 'ROUND_TO_WHOLE_TWD')
        for f in ('conditional_remittance_fee', 'fractional_rounding'):
            with self.assertRaises(ValueError):
                scope.resolve_field(self.qa, f, request(self.qa, f, family=self.stock['family'], action_type='STOCK_DIVIDEND'))
        self.assertNotIn('conditional_remittance_fee', self.stock['fields'])

    def test_tcc_proposal_classification_not_final_funding_or_zero_tax(self):
        evidence = scope.resolve_field(self.tcc, 'proposed_funding_source', request(self.tcc, 'proposed_funding_source'))
        self.assertEqual(evidence['value'], 'CAPITAL_SURPLUS')
        self.assertEqual(self.tcc['fields']['proposed_cash_per_share']['value'], '0.8')
        with self.assertRaisesRegex(ValueError, 'not final ledger'):
            scope.resolve_field(self.tcc, 'proposed_funding_source', request(self.tcc, 'proposed_funding_source', purpose='FINAL_LEDGER'))
        for f in ('final_funding_source', 'capital_surplus_subtype', 'net_cash_per_share'):
            with self.assertRaisesRegex(ValueError, 'Unknown field'):
                scope.resolve_field(self.tcc, f, request(self.tcc, f))

    def test_direct_published_ratio_not_final_unrounded_allotment(self):
        with self.assertRaisesRegex(ValueError, 'not final ledger'):
            scope.resolve_field(self.stock, 'shares_per_share', request(self.stock, 'shares_per_share', purpose='FINAL_LEDGER'))

    def test_every_version_proof_binds_retained_usable_source(self):
        for v in self.catalog['inventory']:
            scope.verify(v)
            for bound in v['fields'].values():
                for p in bound['proofs']:
                    self.assertIn(p['source_id'], v['source_ids'])
                    self.assertIn(p['source_id'], self.catalog['sources'])
                    self.assertTrue(p['raw_value']); self.assertTrue(p['locator'])
        self.assertNotIn('nhi-capital-surplus', self.catalog['sources'])
        self.assertEqual(self.catalog['source_failure']['status'], 'FAILED_HTTP_403_NOT_USABLE_NOT_RETRIED')

    def test_old_cash_components_and_stock_lineage_preserved(self):
        old = json.loads((HERE / 'official_actions_20261022/events-v02.json').read_text())
        self.assertEqual([e for e in self.catalog['events'] if e['type'] == 'CASH_DIVIDEND'], [e for e in old['events'] if e['type'] == 'CASH_DIVIDEND'])
        old_stock = next(e for e in old['events'] if e['type'] == 'STOCK_DIVIDEND')
        new = next(e for e in self.catalog['events'] if e['type'] == 'STOCK_DIVIDEND')
        self.assertEqual(new['supersedes_event_id'], old_stock['id'])
        self.assertEqual(new['prior_observed_at'], old_stock['observed_at'])
        self.assertGreater(new['observed_at'], old_stock['observed_at'])
        scope.verify(new)

    def test_coverage_retains_known_company_action_inventory_not_only_dividends(self):
        for code in ('1101', '2884'):
            self.assertEqual(self.catalog['coverage'][code]['known_company_action_ids'], scope.required_inventory(self.catalog, code))
            self.assertNotEqual(self.catalog['coverage'][code]['status'], 'VERIFIED_COMPLETE')
        self.assertEqual(len(scope.required_inventory(self.catalog, '2884')), 4)
        data = self.input(); data['coverage']['2884']['known_company_action_ids'] = []
        self.assertIn('KNOWN_COMPANY_ACTION_INVENTORY_MISSING:2884', scope.admit_and_replay(data, self.catalog)['refusal_reasons'])

    def test_exchange_inside_window_or_on_opening_day_blocks_unsupported_accounting(self):
        for start in ('2026-08-03', '2026-09-01'):
            result = scope.admit_and_replay(self.input(start), self.catalog)
            self.assertIn('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED', result['refusal_reasons'])
            finding = next(x for x in result['scope_findings'] if x['reason'] == 'SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED')
            self.assertEqual(finding['entitled_old_code'], '2867')
            self.assertIsNone(finding['existing_acquirer_share_grant'])
            self.assertEqual(result['daily'], []); self.assertIsNone(result['total_net_return'])

    def test_later_scheduled_exchange_not_claimed_to_happen_earlier(self):
        result = scope.admit_and_replay(self.input(end='2026-08-31'), self.catalog)
        self.assertNotIn('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED', result['refusal_reasons'])
        self.assertIn('SOURCE_ACTION_COVERAGE_INCOMPLETE:2884', result['refusal_reasons'])
        self.assertFalse(result['historical_signal_eligible'])

    def test_changed_input_qualification_flags_cannot_override_catalog_evidence(self):
        data = self.input()
        for code, c in data['coverage'].items():
            c.update(status='VERIFIED_COMPLETE', types=['CASH_DIVIDEND', 'STOCK_DIVIDEND', 'CAPITAL_REDUCTION'], other_actions_checked=True,
                     event_ids=[e['id'] for e in data['events'] if e['code'] == code and data['start'] < e['ex_date'] <= data['end']])
        data['qualification'].update(opening_claims='VERIFIED', net_distributions='VERIFIED')
        with patch.object(scope, 'replay', side_effect=AssertionError('Unqualified numeric replay')):
            result = scope.admit_and_replay(data, self.catalog)
        self.assertIn('SOURCE_ACTION_COVERAGE_INCOMPLETE:2884', result['refusal_reasons'])
        self.assertIn('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED', result['refusal_reasons'])
        self.assertFalse(result['original_numeric_replay_called'])

    def test_cash_source_unknown_keeps_net_receivable_and_profit_uncomputed(self):
        data = self.input('2026-06-30', '2026-07-29')
        result = scope.admit_and_replay(data, self.catalog)
        self.assertTrue(any(x.startswith('FINAL_CASH_DISTRIBUTION_NATURE_UNVERIFIED') for x in result['refusal_reasons']))
        self.assertIn('NET_DISTRIBUTIONS_TAX_FEES_UNKNOWN', result['refusal_reasons'])
        self.assertIn('OPENING_ENTITLEMENTS_UNKNOWN', result['refusal_reasons'])
        self.assertEqual(result['journal'], []); self.assertIsNone(result['scenario_net_return'])

    def test_catalog_version_component_or_fingerprint_mismatch_rejected(self):
        data = self.input(); data['events'] = []
        with self.assertRaisesRegex(ValueError, 'exact catalog'): scope.admit_and_replay(data, self.catalog)
        catalog = deepcopy(self.catalog); catalog['coverage']['2884']['status'] = 'VERIFIED_COMPLETE'
        with self.assertRaisesRegex(ValueError, 'fingerprint'): scope.admit_and_replay(self.input(), catalog)
        v = deepcopy(self.stock); v['fields']['shares_per_share']['value'] = '0'
        with self.assertRaisesRegex(ValueError, 'fingerprint'): scope.resolve_field(v, 'shares_per_share', request(v, 'shares_per_share'))

    def test_no_mna_ratio_or_stop_date_fills_original_quote_gap(self):
        for code, when in [('1101', '2025-08-13'), ('2884', '2025-11-05')]:
            bar = next(b for b in self.old['assets'][code]['bars'] if b['date'] == when)
            self.assertIsNone(bar['close']); self.assertTrue(bar['missing'])
        self.assertEqual(source.build_catalog(), self.catalog)


class SourceCorruption(unittest.TestCase):
    def test_source_or_derived_text_tampering_cannot_reach_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            shutil.copytree(source.REVIEW, Path(td) / 'review'); review = Path(td) / 'review'
            for suffix in ('.response', '.txt'):
                p = review / 'raw' / ('esun-direct-2025-ratio' + suffix); old = p.read_bytes(); p.write_bytes(old + b'corrupt')
                with self.assertRaisesRegex(ValueError, 'fingerprint'): source.load_review(review)
                p.write_bytes(old)

    def test_changed_origin_even_with_matching_manifest_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            shutil.copytree(source.REVIEW, Path(td) / 'review'); review = Path(td) / 'review'
            p = review / 'source-manifest.json'; m = json.loads(p.read_text()); m['esun-direct-2025-ratio']['url'] = 'https://example.com/ratio'; p.write_text(json.dumps(m))
            p = review / 'raw/esun-direct-2025-ratio.meta.json'; m = json.loads(p.read_text()); m['url'] = 'https://example.com/ratio'; p.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError, 'origin'): source.load_review(review)


if __name__ == '__main__':
    unittest.main()
