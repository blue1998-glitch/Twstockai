"""One real saved-source positive; engineered negative copies, no market tests."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import unittest
from unittest.mock import patch
from rotation_research.action_scope import identify
from rotation_research.source_followup import compact
from rotation_research.treasury_date_roles import observe,parse_page,resolve,validate,NULL_FIELDS,PRIOR_ID
from .build import verify_input,HERE,ROOT


class DateRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((HERE/'input.json').read_text())
        cls.expected=json.loads((HERE/'expected.json').read_text())

    def request(self,r,name):
        f=r['fields'][name]
        q={k:r[k] for k in ('family','issuer_code','entitled_old_code','action_type','old_instrument')}
        q.update(version_id=r['id'],field=name,date_role=f['date_role'],unit=f['unit'],
                 observed_as_of=r['observed_at'],historical_signal=False,purpose='SOURCE_DIAGNOSTIC')
        return q

    def test_real_saved_source_matches_frozen_oracle(self):
        r=observe(self.data);p=parse_page(self.data['source']['page_text'])
        for key in ('board_approval_month','registration_completed_month','cancellation_quantity','quantity_unit'):
            self.assertEqual(p[key],self.expected[key])
        for key in NULL_FIELDS:self.assertIsNone(r['fields'][key]['value'])
        for key in ('numeric_ledger_events_added','historical_signal_eligible','accounting_eligible','policy_authorized','primary_pressure_id'):
            self.assertEqual(r[key],self.expected[key])
        self.assertEqual(r['linked_prior_observation_id'],PRIOR_ID)
        self.assertEqual(r['fields']['cancellation_quantity']['unit'],'THOUSAND_SHARES')

    def test_source_issuer_url_pdf_native_and_page_identity_are_bound(self):
        for key,value in [('issuer_code','2884'),('source_id','other'),('url','https://invalid.example'),
            ('pdf_sha256','0'*64),('native_sha256','0'*64),('page_sha256','0'*64),
            ('page_number',57),('printed_page','57'),('pdf_bytes',1)]:
            d=deepcopy(self.data);d['source'][key]=value
            with self.assertRaisesRegex(ValueError,'identity conflict',msg=key):observe(d)

    def test_page_bytes_cannot_be_replaced_even_with_same_declared_hash(self):
        d=deepcopy(self.data);d['source']['page_text']+='\n'
        with self.assertRaisesRegex(ValueError,'content conflict'):observe(d)

    def test_parser_rejects_missing_duplicate_day_unit_and_bad_month(self):
        s=compact(self.data['source']['page_text'])
        variants=[s.replace('115年1月','115年13月'),s.replace('115年2月','114年12月'),
            s.replace('仟股','元'),s.replace('月經董事會','月2日經董事會'),
            s.replace('月辦理變更','月2日辦理變更'),s.replace('經董事會通過','經股東個人通過'),
            s+s,'沒有來源句子-58-',s.replace('-58-','-57-')]
        for v in variants:
            with self.assertRaises(ValueError):parse_page(v)

    def test_month_resolution_requires_exact_holder_unit_role_and_version(self):
        r=observe(self.data);name='board_approval_month';q=self.request(r,name)
        self.assertEqual(resolve(r,name,q)['value'],'2026-01')
        for key,value in [('issuer_code','2884'),('entitled_old_code','1101'),
            ('old_instrument','1101_ORDINARY_OLD_SHARES'),('version_id','latest'),
            ('date_role','EXACT_EFFECTIVE_DATE'),('unit','ISO_DATE')]:
            bad=deepcopy(q);bad[key]=value
            with self.assertRaisesRegex(ValueError,'Wrong holder'):resolve(r,name,bad)

    def test_unknown_dates_and_personal_fields_never_default_to_zero(self):
        r=observe(self.data)
        for name in NULL_FIELDS:
            with self.assertRaisesRegex(ValueError,'Unknown field'):resolve(r,name,self.request(r,name))

    def test_no_final_ledger_or_historical_signal_route(self):
        r=observe(self.data);name='registration_completed_month';q=self.request(r,name)
        self.assertEqual(resolve(r,name,q)['value'],'2026-02')
        q['purpose']='FINAL_LEDGER'
        with self.assertRaisesRegex(ValueError,'not final ledger'):resolve(r,name,q)
        q=self.request(r,name);q['historical_signal']=True
        with self.assertRaisesRegex(ValueError,'Historical availability'):resolve(r,name,q)

    def test_capture_and_observation_cannot_be_backdated_to_january(self):
        d=deepcopy(self.data);d['observed_at']='2026-01-09T16:00:00+08:00'
        with self.assertRaisesRegex(ValueError,'chronology'):observe(d)
        d=deepcopy(self.data);d['source']['official_captured_at']='2026-01-01T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError,'identity conflict'):observe(d)
        r=observe(self.data);q=self.request(r,'board_approval_month');q['observed_as_of']='2026-01-09T16:00:00+08:00'
        with self.assertRaisesRegex(ValueError,'not yet observed'):resolve(r,'board_approval_month',q)
        d=deepcopy(self.data);d['observed_at']='2026-10-26T08:26:28'
        with self.assertRaisesRegex(ValueError,'timezone'):observe(d)

    def test_rehashed_output_cannot_promote_dates_or_qualifications(self):
        for name in ('exact_effective_date','holder_conversion_ratio','holder_cashflow'):
            r=observe(self.data);r['fields'][name]['value']='0'
            with self.assertRaisesRegex(ValueError,'differs from source'):validate(identify(r))
        r=observe(self.data);r['data_qualified']=True
        with self.assertRaisesRegex(ValueError,'differs from source'):validate(identify(r))

    def test_reader_binds_pdf_extraction_full_native_and_exact_page(self):
        receipt=verify_input(self.data)
        self.assertEqual(receipt['original_pdf_bytes'],3320224)
        self.assertEqual(receipt['native_pages'],124)
        self.assertEqual(receipt['selected_page'],58)
        d=deepcopy(self.data);d['source']['page_text']='different page'
        with self.assertRaisesRegex(ValueError,'does not match'):verify_input(d)

    def test_reader_rejects_tampered_pdf_without_touching_original(self):
        original=Path.read_bytes
        def altered(path):
            b=original(path)
            return b+b'X' if path.name=='tcc-2026-q2-consolidated-report.response' else b
        with patch.object(Path,'read_bytes',altered):
            with self.assertRaisesRegex(ValueError,'fingerprint conflict'):verify_input(self.data)

    def test_legacy_sources_catalogs_ledger_and_selection_remain_exact(self):
        inventory=json.loads((HERE/'source-inventory-before.json').read_text())
        for row in inventory:
            if row['path'] in ('AGENTS.md','CONTINUE_IN_WORK_MODE.md'):continue
            b=(ROOT/row['path']).read_bytes()
            self.assertEqual(len(b),row['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),row['sha256'])
        selected=json.loads((ROOT/'股票系統M1_v0_18/rotation_research/source_followup_20261023/raw/tcc-2026-q2-consolidated-report.evidence.json').read_text())
        self.assertNotIn('58',selected)

    def test_pure_observation_does_not_open_files_or_run_accounts(self):
        with patch('builtins.open',side_effect=AssertionError('core opened a file')), \
             patch('rotation_research.action_scope.qualify',side_effect=AssertionError('account qualification')), \
             patch('rotation_research.action_scope.replay',side_effect=AssertionError('account replay')):
            self.assertEqual(observe(self.data)['fields']['board_approval_month']['value'],'2026-01')


if __name__=='__main__':unittest.main()
