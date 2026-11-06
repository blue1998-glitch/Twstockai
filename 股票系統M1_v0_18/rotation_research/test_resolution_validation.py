"""Additional environment/source checks for the existing canonical 0.4."""
from decimal import Decimal
import hashlib
import json
import unittest
from . import action_resolution as resolution
from . import action_resolution_sources as sources

OUT = sources.HERE / 'resolution_validation_20261023'


class ResolutionEnvironmentValidation(unittest.TestCase):
    def test_extractor_versions_preserve_claimed_pages_and_resolution_fields(self):
        texts, registry = sources.load_review()
        old = texts['tcc-2026-agm-minutes']
        current_bytes = (OUT / 'pdf-text-recheck-current.txt').read_bytes()
        record = json.loads((OUT / 'pdf-extraction-recheck.json').read_text())
        self.assertEqual(hashlib.sha256(current_bytes).hexdigest(), record['current_text_sha256'])
        self.assertEqual(registry['tcc-2026-agm-minutes']['sha256'], record['source_pdf_sha256'])
        current = current_bytes.decode('utf-8')
        for page in (1, 3, 4, 6, 7):
            self.assertEqual(old.split('\f')[page-1], current.split('\f')[page-1])
        self.assertEqual(sources.parse_minutes(old), sources.parse_minutes(current))
        self.assertFalse(record['whole_document_text_byte_equal'])

    def test_different_holders_round_separately_not_on_combined_quantity(self):
        catalog = sources.build_catalog()
        v = next(v for v in catalog['inventory'] if v['action_type'] == 'CASH_DISTRIBUTION_RESOLUTION')
        bound = v['fields']['approved_cash_per_share']
        request = {k: v[k] for k in ('family', 'issuer_code', 'entitled_old_code', 'action_type', 'old_instrument')}
        request.update(version_id=v['id'], field='approved_cash_per_share', unit=bound['unit'],
                       date_role=bound['date_role'], observed_as_of=v['observed_at'], historical_signal=False,
                       purpose='SOURCE_DIAGNOSTIC')
        def preview(holder, quantity):
            return resolution.preview_shareholder_cash(catalog, request, dict(
                kind='HYPOTHETICAL_ENTITLED_SHARES', assumption='工程假想，非個人帳戶或零權利證明',
                hypothetical_holder=holder, shares=quantity, issuer_code=v['issuer_code'],
                old_instrument=v['old_instrument'], version_id=v['id']))
        a, b, combined = preview('A', '1'), preview('B', '4'), preview('COMPARISON_ONLY', '5')
        separate = Decimal(a['rounded_shareholder_gross_twd']) + Decimal(b['rounded_shareholder_gross_twd'])
        self.assertEqual(separate, Decimal('3'))
        self.assertEqual(combined['rounded_shareholder_gross_twd'], '4')
        for result in (a, b, combined):
            self.assertIsNone(result['net_cash_twd'])
            self.assertIsNone(result['net_cash_per_share'])
            self.assertIsNone(result['actual_investor_receipt'])
            self.assertIsNone(result['total_net_return'])


if __name__ == '__main__': unittest.main()
