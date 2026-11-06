import hashlib
import tempfile
import unittest
from pathlib import Path
from graph_core.core import fingerprint
from .action_sources import build_catalog, checked_source, TableRows


class ArchivedActions(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.catalog=build_catalog()

    def test_cash_dates_amounts_from_independent_oracles(self):
        cash=[(e['code'],e['ex_date'],e['gross_per_share'],e['pay_date']) for e in self.catalog['events'] if e['type']=='CASH_DIVIDEND']
        self.assertEqual(cash,[('1101','2025-07-02','1','2025-07-29'),('2884','2025-07-22','1.2','2025-08-27'),
                               ('1101','2026-07-01','0.8','2026-07-28'),('2884','2026-07-01','1.4','2026-07-27')])

    def test_record_date_is_not_ex_date(self):
        event=next(e for e in self.catalog['events'] if e['code']=='2884' and e['ex_date']=='2026-07-01')
        self.assertEqual(event['record_date'],'2026-07-07')
        self.assertIsNone(event['announced_at']);self.assertIsNone(event['net_per_share'])

    def test_money_is_not_share_ratio_or_listing_date(self):
        event=next(e for e in self.catalog['events'] if e['type']=='STOCK_DIVIDEND')
        self.assertEqual(event['stock_dividend_money_per_share'],'0.10015129')
        self.assertIsNone(event['shares_per_share']);self.assertIsNone(event['tradable_date'])
        self.assertEqual(event['delivery_date'],'2025-08-27')

    def test_identity_field_proofs_and_no_completeness_inference(self):
        for e in self.catalog['events']:
            self.assertEqual(e['id'],fingerprint({k:v for k,v in e.items() if k!='id'}))
            for refs in e['field_sources'].values():
                for ref in refs:self.assertIn(ref['source_id'],e['source_ids']);self.assertTrue(ref['locator'])
        for c in self.catalog['coverage'].values():
            self.assertFalse(c['other_actions_checked']);self.assertNotEqual(c['status'],'VERIFIED_COMPLETE')
        self.assertFalse(self.catalog['total_net_return_qualified'])

    def test_tampered_archive_refused(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'response';p.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'mismatch'):
                checked_source(p,dict(sha256=hashlib.sha256(b'original').hexdigest(),bytes=8),'observed_at')

    def test_table_text_entities(self):
        parser=TableRows();parser.feed('<table><tr><th>除息基準日</th></tr><tr><td> 1<b>.4</b>&nbsp; </td></tr></table>')
        self.assertEqual(parser.rows,[['除息基準日'],['1.4']])


if __name__=='__main__':unittest.main()
