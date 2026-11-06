"""Meaningful version, account-level rounding and admission regressions."""
from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from . import action_resolution as core
from . import action_resolution_sources as source
from . import action_scope
from .action_sources import HERE
from .action_study import verified_quotes
from .source_qualification import build_calendar


def request(v, field='approved_cash_per_share', **changes):
    result = {k:v[k] for k in ('family', 'issuer_code', 'entitled_old_code', 'action_type', 'old_instrument')}
    result.update(version_id=v['id'], field=field, unit=v['fields'][field]['unit'],
        date_role=v['fields'][field]['date_role'], observed_as_of=v['observed_at'],
        historical_signal=False, purpose='SOURCE_DIAGNOSTIC')
    result.update(changes); return result


class ResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = source.build_catalog()
        cls.approved = next(v for v in cls.catalog['inventory'] if v['action_type'] == 'CASH_DISTRIBUTION_RESOLUTION')
        cls.old, cls.manifest = verified_quotes(); cls.calendar = build_calendar()

    def preview(self, shares='3', **changes):
        entitled = dict(kind='HYPOTHETICAL_ENTITLED_SHARES', assumption='Synthetic engineering case only',
            shares=shares, issuer_code='1101', old_instrument=self.approved['old_instrument'], version_id=self.approved['id'])
        entitled.update(changes)
        return core.preview_shareholder_cash(self.catalog, request(self.approved), entitled)

    def data(self):
        return source.input_for(self.old, self.catalog, self.manifest, self.calendar, '2026-06-01', '2026-09-10', '1101')

    def test_exact_parent_and_original_versions_unchanged(self):
        old = json.loads((HERE / 'action_scope_20261023/events-v03.json').read_text())
        self.assertEqual(self.catalog['parent_catalog'], old)
        self.assertEqual(self.catalog['events'], old['events'])
        self.assertEqual(self.catalog['inventory'][:5], old['inventory'])
        self.assertEqual(len(self.catalog['inventory']), 8)

    def test_proposal_and_approval_kept_as_distinct_explicit_versions(self):
        proposal = next(v for v in self.catalog['inventory'] if v['action_type'] == 'CASH_DISTRIBUTION_PROPOSAL')
        self.assertEqual(proposal['stage'], 'BOARD_PROPOSAL_NOT_TAX_MODEL')
        self.assertNotEqual(proposal['id'], self.approved['id'])
        self.assertEqual(self.approved['stage'], 'SHAREHOLDER_APPROVED_ADJUSTABLE')
        self.assertIsNone(proposal['fields']['final_funding_source']['value'])
        with self.assertRaises(ValueError): core.explicit_version(self.catalog, None)
        with self.assertRaises(ValueError): core.explicit_version(self.catalog, 'latest')

    def test_approved_label_is_exact_and_not_tax_subtype(self):
        f = core.resolve(self.catalog, 'approved_funding_label', request(self.approved, 'approved_funding_label'))
        self.assertEqual(f['value'], '超過票面金額發行股票所得溢額')
        self.assertIsNone(self.approved['fields']['tax_origin_subtype']['value'])
        self.assertEqual(f['proofs'][0]['pdf_pages'], [6])

    def test_resolution_vote_is_scoped_not_preceding_preferred_share_vote(self):
        text, _ = source.load_review(); p = source.parse_minutes(text['tcc-2026-agm-minutes'])
        self.assertEqual(p['vote']['yes'], '5078871021')
        self.assertEqual(p['vote']['attending'], '5366379935')
        self.assertEqual(p['percent'], '94.64')
        self.assertEqual(p['total'], '5994545394')

    def test_vote_arithmetic_drift_fails_closed(self):
        text, _ = source.load_review()
        with self.assertRaisesRegex(ValueError, 'arithmetic'):
            source.parse_minutes(text['tcc-2026-agm-minutes'].replace('5,078,871,021', '5,078,871,022'))

    def test_missing_approval_or_rounding_clause_is_rejected(self):
        text, _ = source.load_review()
        for old in ['本案依表決結果，照案通過。', '元以下捨去']:
            with self.assertRaises(ValueError): source.parse_minutes(text['tcc-2026-agm-minutes'].replace(old, ''))

    def test_three_shares_round_once_at_total_and_preserve_remainder(self):
        result = self.preview('3')
        self.assertEqual(result['unrounded_shareholder_gross_twd'], '2.4')
        self.assertEqual(result['rounded_shareholder_gross_twd'], '2')
        self.assertEqual(result['rounding_remainder_twd'], '0.4')
        self.assertIsNone(result['net_cash_per_share'])

    def test_rounding_is_nonlinear_and_not_sum_of_individual_share_floors(self):
        one, five = self.preview('1'), self.preview('5')
        self.assertEqual(one['rounded_shareholder_gross_twd'], '0')
        self.assertEqual(five['rounded_shareholder_gross_twd'], '4')
        self.assertNotEqual(int(one['rounded_shareholder_gross_twd']) * 5, int(five['rounded_shareholder_gross_twd']))
        self.assertIsNone(one['net_cash_twd'])

    def test_large_odd_quantity_keeps_decimal_precision(self):
        result = self.preview('999999999999999999999999999999')
        self.assertEqual(result['unrounded_shareholder_gross_twd'], '799999999999999999999999999999.2')
        self.assertEqual(result['rounding_remainder_twd'], '0.2')

    def test_no_implicit_zero_quantity(self):
        for value in [None, 0, 3, '3.0', '-1', '1e3', 'NaN', '9'*31, True]:
            with self.subTest(value=value), self.assertRaises(ValueError): self.preview(value)

    def test_explicit_zero_is_only_hypothetical_not_zero_account_proof(self):
        r = self.preview('0')
        self.assertEqual(r['rounded_shareholder_gross_twd'], '0')
        self.assertFalse(r['opening_entitlement_verified'])
        self.assertIsNone(r['actual_investor_receipt'])

    def test_current_holdings_or_blank_assumption_not_entitlement(self):
        for changes in [dict(kind='CURRENT_HOLDING'), dict(assumption=''), dict(assumption=None)]:
            with self.assertRaises(ValueError): self.preview(**changes)

    def test_other_issuer_instrument_or_version_cannot_borrow_rounding(self):
        for changes in [dict(issuer_code='2884'), dict(old_instrument='1101_PREFERRED_SHARES'), dict(version_id='latest')]:
            with self.assertRaises(ValueError): self.preview(**changes)

    def test_preview_leaves_every_net_and_actual_field_unknown(self):
        r = self.preview()
        for k in ('tax_twd', 'fees_twd', 'net_cash_twd', 'net_cash_per_share', 'actual_investor_receipt', 'pay_date', 'record_date', 'total_net_return'):
            self.assertIsNone(r[k], k)
        self.assertFalse(r['final_after_adjustments_verified'])
        self.assertFalse(r['policy_authorized'])

    def test_meeting_date_never_becomes_ex_record_or_pay_date(self):
        r = core.resolve(self.catalog, 'meeting_date', request(self.approved, 'meeting_date'))
        self.assertEqual(r['value'], '2026-05-22')
        for role in ('ACTUAL_PAY_DATE', 'ACTUAL_RECORD_DATE', 'EX_DATE'):
            with self.assertRaises(ValueError): core.resolve(self.catalog, 'meeting_date', request(self.approved, 'meeting_date', date_role=role))

    def test_final_ratio_tax_and_actual_receipt_cannot_default(self):
        for k in ('final_cash_per_share', 'tax_origin_subtype', 'actual_investor_receipt', 'pay_date', 'net_cash_per_share'):
            with self.assertRaisesRegex(ValueError, 'Unknown field'): core.resolve(self.catalog, k, request(self.approved, k))
        with self.assertRaisesRegex(ValueError, 'not final ledger'):
            core.resolve(self.catalog, 'approved_cash_per_share', request(self.approved, purpose='FINAL_LEDGER'))

    def test_later_observation_does_not_authenticate_historical_signal(self):
        before = (datetime.fromisoformat(self.approved['observed_at']) - timedelta(microseconds=1)).isoformat()
        with self.assertRaises(ValueError): core.resolve(self.catalog, 'approved_cash_per_share', request(self.approved, observed_as_of=before))
        with self.assertRaises(ValueError): core.resolve(self.catalog, 'approved_cash_per_share', request(self.approved, historical_signal=True))
        self.assertIsNone(self.approved['announced_at'])

    def test_treasury_cancelled_quantity_not_holder_cashflow(self):
        seventh = next(v for v in self.catalog['inventory'] if v['family'] == '1101-seventh-treasury-repurchase')
        self.assertEqual(seventh['fields']['reported_cancellation']['value'], '28000')
        self.assertEqual(seventh['fields']['actual_repurchase_quantity']['unit'], '張_AS_PUBLISHED')
        for k in ('cancellation_effective_date', 'holder_conversion_ratio', 'holder_cashflow'):
            self.assertIsNone(seventh['fields'][k]['value'])

    def test_no_cancellation_is_scoped_to_sixth_tranche_only(self):
        sixth = next(v for v in self.catalog['inventory'] if v['family'] == '1101-sixth-treasury-repurchase')
        self.assertEqual(sixth['fields']['reported_cancellation']['value'], 'NONE_REPORTED_THIS_TRANCHE')
        self.assertEqual(self.catalog['coverage']['1101']['status'], 'INCOMPLETE')

    def test_new_inventory_cannot_be_omitted_from_qualification(self):
        data = self.data(); data['coverage']['1101']['known_company_action_ids'] = []
        result = core.refuse_accounting(data, self.catalog)
        self.assertIn('RESOLUTION_INVENTORY_MISSING:1101', result['refusal_reasons'])

    def test_input_complete_flags_still_refuse_and_never_replay(self):
        data = self.data()
        for c in data['coverage'].values(): c['status'] = 'VERIFIED_COMPLETE'
        data['qualification'].update(opening_claims='VERIFIED', net_distributions='VERIFIED')
        with patch.object(action_scope, 'replay', side_effect=AssertionError('Forbidden replay')):
            r = core.refuse_accounting(data, self.catalog)
        self.assertIn('SOURCE_ACTION_COVERAGE_INCOMPLETE:1101', r['refusal_reasons'])
        self.assertIn('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED', r['refusal_reasons'])
        self.assertIsNone(r['total_net_return']); self.assertEqual(r['daily'], [])
        self.assertFalse(r['original_numeric_replay_called'])

    def test_missing_account_evidence_still_blocks_initial_rights_and_net(self):
        r = core.refuse_accounting(self.data(), self.catalog)
        self.assertIn('OPENING_ENTITLEMENTS_UNKNOWN', r['refusal_reasons'])
        self.assertIn('NET_DISTRIBUTIONS_TAX_FEES_UNKNOWN', r['refusal_reasons'])
        self.assertEqual(r['journal'], [])

    def test_wrong_catalog_input_binding_rejected(self):
        d = self.data(); d['resolution_catalog_id'] = self.catalog['parent_catalog_id']
        with self.assertRaises(ValueError): core.refuse_accounting(d, self.catalog)

    def test_catalog_tampering_or_rehashed_complete_flag_rejected(self):
        c = deepcopy(self.catalog); c['coverage']['1101']['status'] = 'VERIFIED_COMPLETE'
        with self.assertRaisesRegex(ValueError, 'fingerprint'): core.validate(c)
        c = action_scope.identify(c)
        with self.assertRaisesRegex(ValueError, 'complete coverage'): core.validate(c)

    def test_rehashed_component_replacement_cannot_change_original_ledger(self):
        c = deepcopy(self.catalog); c['events'] = []
        with self.assertRaisesRegex(ValueError, 'components'): core.validate(action_scope.identify(c))

    def test_missing_quote_causes_and_2884_tradability_stay_unknown(self):
        for code, date in [('1101','2025-08-13'), ('2884','2025-11-05')]:
            self.assertIsNone(next(b for b in self.old['assets'][code]['bars'] if b['date']==date)['close'])
        stock = next(v for v in self.catalog['inventory'] if v['action_type']=='STOCK_DIVIDEND')
        self.assertIsNone(stock['fields']['tradable_date']['value'])

    def test_rebuild_is_deterministic_and_no_input_mutation(self):
        before = deepcopy(self.catalog); data = self.data(); data_before = deepcopy(data)
        core.refuse_accounting(data, self.catalog); self.preview()
        self.assertEqual(data, data_before); self.assertEqual(before, self.catalog)
        self.assertEqual(source.build_catalog(), self.catalog)


class SourceIntegrity(unittest.TestCase):
    def test_original_and_derivative_tamper_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)/'review'; shutil.copytree(source.REVIEW, root)
            for suffix in ('.response', '.txt'):
                path = root/'raw'/('tcc-2026-agm-minutes'+suffix); old = path.read_bytes()
                path.write_bytes(old+b'bad')
                with self.assertRaisesRegex(ValueError, 'fingerprint'): source.load_review(root)
                path.write_bytes(old)

    def test_matching_metadata_cannot_replace_pinned_origin(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)/'review'; shutil.copytree(source.REVIEW, root)
            for name in ('source-manifest.json','raw/tcc-meeting-index.meta.json'):
                path=root/name; obj=json.loads(path.read_text()); target=obj['tcc-meeting-index'] if name=='source-manifest.json' else obj
                target['url']='https://example.com/'; path.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError, 'official source'): source.load_review(root)


if __name__ == '__main__':
    unittest.main()
