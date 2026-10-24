"""Actual archived source checks; altered copies are negative engineering fixtures."""
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import json
import shutil
import tempfile
import unittest

from . import subsidiary_proposal as core
from . import subsidiary_proposal_sources as source
from .action_scope import identify
from .test_offline_source_bridge import request


class SubsidiaryProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = source.build_catalog()
        cls.old, cls.manifest = source.parent_source.verified_quotes()
        cls.calendar = source.parent_source.build_calendar()

    def obs(self): return self.catalog['observations'][0]
    def text(self): return self.catalog['source']['native_evidence'][core.VOTING]
    def data(self):
        return source.study_input(self.old, self.catalog, self.manifest, self.calendar, '2026-06-01', '2026-09-10', '1101')
    def reject_catalog(self, change):
        c = deepcopy(self.catalog); change(c)
        with self.assertRaises(ValueError): core.validate(identify(c))

    def test_two_actual_pdf_originals_http_sizes_and_sha(self):
        for sid, size, digest in [(core.MINUTES, 1463099, '861283c21d87e0511c43485874592102dc8d4a73099271a5d23edcbf5dc44b7b'),
                (core.VOTING, 135295, 'af2524a2a9ef722266fd82dceb95fbc5c4a0222793a0f965bbc27266aec48154')]:
            m = self.catalog['source']['manifest']['official_captures'][sid]
            b = (source.OUT / 'raw' / (sid + '.response')).read_bytes()
            self.assertEqual((len(b), hashlib.sha256(b).hexdigest()), (size, digest))
            self.assertEqual(m['http'], 200); self.assertEqual(m['url'], m['final_url'])
            self.assertFalse(m['redirects_followed']); self.assertEqual(m['retries'], 0)

    def test_actual_index_binds_original_href_and_standard_url_encoding(self):
        s = self.catalog['source']['manifest']; index = (source.ROOT / s['index']['path']).read_text()
        self.assertIn('2026第一次股東臨時會', index); self.assertIn('2026.10.13', index)
        for m in s['official_captures'].values():
            self.assertIn('href="' + m['original_href'] + '"', index)
            self.assertIn('2026%20First%20Extraordinary', m['url'])

    def test_original_meta_native_image_and_manifest_tampering_rejected(self):
        for name in ['raw/' + core.MINUTES + '.response', 'raw/' + core.VOTING + '.meta.json',
                     'raw/' + core.VOTING + '.txt', 'visual/' + core.MINUTES + '-p1.png', 'source-manifest.json']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                folder = Path(td) / 'new'; shutil.copytree(source.OUT, folder)
                p = folder / name; p.write_bytes(p.read_bytes() + b'changed')
                with self.assertRaises(ValueError): source.load_source(folder)

    def test_wrong_issuer_rejected_by_native_parser(self):
        with self.assertRaises(ValueError): core.parse_voting(self.text().replace('臺灣水泥股份有限公司', '玉山金融控股股份有限公司'))

    def test_wrong_subject_or_absent_proposed_ipo_phrase_rejected(self):
        for t in [self.text().replace('Cimpor', 'Another'), self.text().replace('擬於', '已於')]:
            with self.assertRaises(ValueError): core.parse_voting(t)

    def test_native_voting_issuer_date_subject_and_approval(self):
        f = self.catalog['facts']['voting_native']
        self.assertEqual((f['issuer_code'], f['meeting_date'], f['subject_entity']), ('1101', '2026-10-13', 'Cimpor International Holdings'))
        self.assertEqual(f['phase'], 'ISSUER_REPORTED_SUBSIDIARY_IPO_PROPOSAL_APPROVED')
        with self.assertRaises(ValueError): core.parse_voting(self.text().replace('照案通過', '照案保留'))

    def test_vote_percentage_not_allocation_dilution_or_return(self):
        o = self.obs(); r = core.resolve(self.catalog, 'for_percentage', request(o, 'for_percentage'))
        self.assertEqual(r['value'], '94.74')
        for changed in [dict(unit='PERCENT_OF_SHARES_GRANTED'), dict(date_role='PERSONAL_RETURN')]:
            with self.assertRaises(ValueError): core.resolve(self.catalog, 'for_percentage', request(o, 'for_percentage', **changed))
        self.assertIn('NOT_ALLOCATION', r['unit'])

    def test_vote_counts_sum_and_published_percentages_not_renormalized(self):
        f = self.catalog['facts']['voting_native']
        self.assertEqual(f['total_voting_rights'], '4525340566')
        self.assertEqual(f['percentage_sum'], '99.98'); self.assertFalse(f['percentage_normalized'])
        self.assertEqual(f['votes']['invalid']['percentage'], '0.00')  # Reported voting number, not unknown personal fee.

    def test_missing_duplicate_vote_row_or_wrong_percentage_denominator_rejected(self):
        for t in [self.text().replace('贊成權數', '遺失權數'), self.text() + self.text(),
                  self.text().replace('占出席股東表決權數%', '占配股比例%')]:
            with self.assertRaises(ValueError): core.parse_voting(t)

    def test_scanned_four_formfeeds_are_not_blank_pages_or_fake_native(self):
        self.assertEqual(self.catalog['source']['native_evidence'][core.MINUTES], '\f' * 4)
        r = self.catalog['source']['manifest']['visual_review']
        self.assertEqual(len(r['images']), 5); self.assertTrue(all(x['viewed_by_codex'] for x in r['images']))
        self.assertTrue(r['no_ocr_performed'])
        self.reject_catalog(lambda c: c['source']['native_evidence'].__setitem__(core.MINUTES, '人工摘要假作native'))

    def test_detailed_scan_parser_unimplemented_and_manual_proof_explicit(self):
        f = self.catalog['facts']['minutes_scanned']
        self.assertEqual(f['detail_clause_parser'], 'NOT_IMPLEMENTED_INVENTORY_ONLY')
        self.assertFalse(f['numeric_clause_fields_extracted'])
        proof = self.obs()['fields']['authorization']['proofs'][0]
        self.assertEqual(proof['evidence_kind'], 'MANUAL_VISUAL_INVENTORY'); self.assertEqual(proof['physical_pdf_page'], 4)

    def test_ordinal_conflict_remains_null_and_voting_has_no_ordinal(self):
        f = self.catalog['facts']['meeting_ordinal']
        self.assertEqual((f['index_path_filename'], f['minutes_p1'], f['voting_body']), ('第一次', '第二次', None))
        self.assertIsNone(f['canonical_meeting_ordinal'])
        with self.assertRaises(ValueError): core.resolve(self.catalog, 'canonical_meeting_ordinal', request(self.obs(), 'canonical_meeting_ordinal'))
        self.reject_catalog(lambda c: c['facts']['meeting_ordinal'].__setitem__('canonical_meeting_ordinal', '第一次'))

    def test_one_case_two_sources_not_two_actions_or_market_samples(self):
        f = self.catalog['facts']['relationship']
        self.assertEqual(f['source_ids'], [core.MINUTES, core.VOTING]); self.assertEqual(len(self.catalog['observations']), 1)
        self.assertEqual((f['numeric_ledger_events_added'], f['independent_market_samples_added']), (0, 0))
        self.reject_catalog(lambda c: c['facts']['relationship'].__setitem__('numeric_ledger_events_added', 2))

    def test_subsidiary_instrument_cannot_credit_1101_personal_holders_or_2884(self):
        o = self.obs()
        for changed in [dict(entitled_old_code='1101'), dict(old_instrument='1101_ORDINARY'), dict(issuer_code='2884'),
                        dict(action_type='CAPITAL_REDUCTION')]:
            with self.assertRaises(ValueError): core.resolve(self.catalog, 'phase', request(o, 'phase', **changed))

    def test_planning_or_authorization_not_completion_or_zero_impact(self):
        for field, value in [('phase', 'IPO_COMPLETED'), ('personal_shares', '0'), ('zero_impact', True)]:
            def change(c):
                o = c['observations'][0]; o['fields'][field]['value'] = value; c['observations'][0] = identify(o)
            self.reject_catalog(change)
        for key in self.catalog['facts']['unknown']:
            self.assertIsNone(self.catalog['facts']['unknown'][key])

    def test_meeting_last_modified_creation_and_observation_not_announced_or_effective(self):
        m = self.catalog['source']['manifest']
        self.assertIsNone(m['announced_at']); self.assertIsNone(self.catalog['facts']['unknown']['actual_effective_at'])
        for meta in m['official_captures'].values():
            self.assertEqual(meta['headers']['last-modified'], 'Mon, 19 Oct 2026 07:30:57 GMT')
            self.assertNotEqual(meta['captured_at'], meta['headers']['last-modified'])
        self.reject_catalog(lambda c: c['source']['manifest'].__setitem__('announced_at', '2026-10-13'))

    def test_work_attestation_not_actual_codex_capture_or_work_github(self):
        m = self.catalog['source']['manifest']; self.assertIsNone(m['work_github_readback_at'])
        self.assertEqual(m['work_attachment'], 'NOT_VISIBLE_NOT_OBTAINED_NOT_READ')
        for sid in [core.MINUTES, core.VOTING]:
            self.assertNotEqual(m['work_reported_captures'][sid]['completed_at'], m['official_captures'][sid]['completed_at'])

    def test_before_actual_observation_and_historical_signal_rejected(self):
        o = self.obs(); before = (datetime.fromisoformat(o['observed_at']) - timedelta(microseconds=1)).isoformat()
        for changed in [dict(observed_as_of=before), dict(historical_signal=True)]:
            with self.assertRaises(ValueError): core.resolve(self.catalog, 'meeting_date', request(o, 'meeting_date', **changed))

    def test_final_ledger_and_unknown_zero_default_rejected(self):
        o = self.obs()
        with self.assertRaises(ValueError): core.resolve(self.catalog, 'for_percentage', request(o, 'for_percentage', purpose='FINAL_LEDGER'))
        for k in ['personal_cash', 'personal_shares', 'net_cash', 'completed_listing_at']:
            with self.assertRaises(ValueError): core.resolve(self.catalog, k, request(o, k))

    def test_exact_complete_parent_preserves_original_null_and_old_versions(self):
        p = self.catalog['parent_catalog']
        self.assertEqual(p, source.parent_source.build_catalog()); self.assertEqual(p['id'], core.PARENT_ID)
        employee = next(o for o in p['parent_catalog']['observations'] if o['action_type'] == 'EMPLOYEE_REMUNERATION_CAPITALIZATION_REPORTED')
        self.assertIsNone(employee['fields']['employee_issued_shares']['value'])
        self.reject_catalog(lambda c: c.__setitem__('parent_catalog_id', 'sha256:other'))
        self.reject_catalog(lambda c: c['parent_catalog'].__setitem__('policy_authorized', True))

    def test_rehashed_source_date_subject_or_proof_mutations_rejected(self):
        for change in [lambda c: c['source']['manifest']['official_captures'][core.VOTING].__setitem__('url', 'https://example.com/fake'),
                       lambda c: c['facts']['voting_native'].__setitem__('meeting_date', '2026-10-16'),
                       lambda c: c['facts']['voting_native'].__setitem__('subject_entity', '1101 holders')]:
            self.reject_catalog(change)

    def test_manual_native_case_mismatch_refused(self):
        s = deepcopy(self.catalog['source']); s['manifest']['visual_review']['manual_inventory']['p4']['vote_counts']['for'] = '1'
        with self.assertRaises(ValueError): core.facts(s)

    def test_incomplete_coverage_net_receipt_and_opening_rights_still_refused(self):
        d = self.data()
        q = core.qualify(d, self.catalog)
        self.assertEqual(q['status'], 'REFUSED_INCOMPLETE_EVENT_ACCOUNTING')
        self.assertEqual((q['daily'], q['journal'], q['total_net_return'], q['original_numeric_replay_called']), ([], [], None, False))
        for code in d['coverage']: d['coverage'][code]['status'] = 'VERIFIED_COMPLETE'
        self.assertEqual(core.qualify(d, self.catalog)['status'], 'REFUSED_INCOMPLETE_EVENT_ACCOUNTING')
        self.reject_catalog(lambda c: c['coverage']['1101'].__setitem__('status', 'VERIFIED_COMPLETE'))

    def test_qualification_version_and_policy_flags_cannot_be_promoted(self):
        d = self.data(); d.pop('subsidiary_proposal_catalog_id')
        with self.assertRaises(ValueError): core.qualify(d, self.catalog)
        for key, value in [('historical_signal_eligible', True), ('policy_authorized', True), ('primary_pressure_id', 'G1')]:
            self.reject_catalog(lambda c, k=key, v=value: c.__setitem__(k, v))


if __name__ == '__main__': unittest.main()
