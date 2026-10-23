"""Real archived-original checks; mutations below are engineered rejection cases."""
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from . import source_followup as core
from . import source_followup_sources as source
from .action_scope import identify
from .action_study import verified_quotes
from .source_qualification import build_calendar
from .test_offline_source_bridge import request


class SourceFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=source.build_catalog();cls.raw=source.OUT/'raw'
        cls.old,cls.manifest=verified_quotes();cls.calendar=build_calendar()

    def obs(self, kind):
        return next(o for o in self.catalog['observations'] if o['action_type']==kind)

    def data(self):
        return source.study_input(self.old,self.catalog,self.manifest,self.calendar,'2026-06-01','2026-09-10','1101')

    def test_three_actual_originals_sha_size_http_and_metadata(self):
        for sid,(size,sha,meta_sha) in source.PINS.items():
            raw=(self.raw/(sid+'.response')).read_bytes();m=(self.raw/(sid+'.meta.json')).read_bytes()
            self.assertEqual(len(raw),size);self.assertEqual(hashlib.sha256(raw).hexdigest(),sha)
            self.assertEqual(hashlib.sha256(m).hexdigest(),meta_sha)
            source.validate_original(sid,raw,json.loads(m))

    def test_original_mutation_wrong_host_redirect_status_or_length_refused(self):
        sid=core.TAIFEX;raw=(self.raw/(sid+'.response')).read_bytes();m=json.loads((self.raw/(sid+'.meta.json')).read_text())
        for change in [dict(url=source.URLS[core.ESUN]),dict(final_url=source.URLS[core.ESUN]),dict(http=403),
                dict(bytes=len(raw)+1),dict(sha256='0'*64),dict(redirects_followed=True),dict(retries=1)]:
            with self.assertRaises(ValueError):source.validate_original(sid,raw,dict(m,**change))
        with self.assertRaises(ValueError):source.validate_original(sid,raw+b'changed',m)

    def test_metadata_manifest_and_native_text_tamper_rejected_offline(self):
        for name in [core.ESUN+'.meta.json',core.TAIFEX+'.txt',core.TCC+'.evidence.json']:
            with tempfile.TemporaryDirectory() as td:
                folder=Path(td)/'source_followup_20261023';(folder/'raw').mkdir(parents=True)
                shutil.copyfile(source.OUT/'source-manifest.json',folder/'source-manifest.json')
                for p in self.raw.iterdir():shutil.copyfile(p,folder/'raw'/p.name)
                target=folder/'raw'/name;target.write_bytes(target.read_bytes()+b' ')
                if name.endswith('evidence.json'):
                    value=json.loads(target.read_text());value['52']='wrong issuer';target.write_text(json.dumps(value))
                with self.assertRaises(ValueError):source.load_sources(folder)

    def test_taifex_stock_and_dn_roles_document_and_resumption_dates(self):
        f=self.catalog['facts'][core.TAIFEX]
        self.assertEqual(f['document_date'],'2025-11-05');self.assertEqual(f['document_number'],'台期交字第1140202330號')
        self.assertEqual(f['stock_resumption_date'],'2025-11-06');self.assertEqual(f['contract_code'],'DN')
        stock=self.obs('TAIFEX_CORROBORATES_UNDERLYING_RESUMPTION');derivative=self.obs('DERIVATIVES_RESUMPTION')
        self.assertEqual(stock['old_instrument'],'2884_ORDINARY_OLD_SHARES')
        self.assertEqual(derivative['old_instrument'],'DN_FUTURES_AND_OPTIONS')
        self.assertIn('NOT_TWSE_DIRECT',stock['fields']['authority']['value'])

    def test_taifex_wrong_issuer_instrument_or_contract_rejected(self):
        text=self.catalog['sources'][core.TAIFEX]['native_evidence']['text']
        for code,instrument in [('1101','1101_ORDINARY_OLD_SHARES'),('2884','DN_FUTURES_AND_OPTIONS')]:
            with self.assertRaises(ValueError):core.parse_taifex(text,code,instrument)
        with self.assertRaises(ValueError):core.parse_taifex(text.replace('DN','XX'),'2884','2884_ORDINARY_OLD_SHARES')

    def test_taifex_conflicting_dates_rejected_not_conflated(self):
        text=self.catalog['sources'][core.TAIFEX]['native_evidence']['text']
        normalized=core.compact(text)
        for changed in [normalized.replace('11月6日','11月7日',1),normalized.replace('發文日期:中華民國114年11月5日','發文日期:中華民國114年11月7日')]:
            with self.assertRaises(ValueError):core.parse_taifex(changed,'2884','2884_ORDINARY_OLD_SHARES')

    def test_no_suspension_end_span_fill_or_execution_promotion(self):
        o=self.obs('TAIFEX_CORROBORATES_UNDERLYING_RESUMPTION')
        self.assertIsNone(o['fields']['suspension_end_date']['value'])
        d=core.quote_diagnostic(self.catalog,'2884','2025-11-06',None,True)
        self.assertEqual(d['related_resumption_corroboration_ids'],[o['id']])
        self.assertFalse(d['direct_twse_resumption_acquired']);self.assertFalse(d['execution_qualified'])
        self.assertTrue(d['missing_quote_blocks_accounting'])
        for k in ('raw_close','imputed_close','valuation','suspension_end_date'):self.assertIsNone(d[k])
        for when in ('2025-11-04','2025-11-05','2025-11-07'):
            self.assertEqual(core.quote_diagnostic(self.catalog,'2884',when,None,True)['related_resumption_corroboration_ids'],[])

    def test_old_missing_quotes_and_market_session_separate(self):
        old=json.loads((source.parent_source.OUT/'missing-quotes.json').read_text())['diagnostics']
        for code,when in [('1101','2025-08-13'),('2884','2025-11-05')]:
            self.assertIn(when,self.calendar['sessions'])
            d=core.quote_diagnostic(self.catalog,code,when,None,True)['parent_diagnostic']
            self.assertIn(d,old);self.assertFalse(d['security_tradable'])
            self.assertEqual(d['parent_diagnostic']['new_missing_explanation'],'UNKNOWN')

    def test_html_new_capture_different_sha_not_claimed_work_bytes(self):
        s=self.catalog['sources'][core.ESUN]
        self.assertNotEqual(s['sha256'],s['work_comparison_only']['expected_sha256'])
        self.assertFalse(s['work_sha_match']);self.assertEqual(s['bytes'],103632)
        for sid in (core.TAIFEX,core.TCC):self.assertTrue(self.catalog['sources'][sid]['work_sha_match'])

    def test_html_scoped_article_excludes_related_news_and_scripts(self):
        html=(self.raw/(core.ESUN+'.response')).read_text()
        before=core.article_text(html)
        after=core.article_text(html.replace('2026/09/07','1900/01/01')+'<script>玉山金控今(9)日完成</script>')
        self.assertEqual(before,after);self.assertNotIn('2026/09/07',before['date'])
        with self.assertRaises(ValueError):core.article_text(html.replace('class="l-news"','class="other"'))

    def test_company_closing_and_conflicting_date_not_canonical(self):
        o=self.obs('ISSUER_CLOSING_REPORT');f=o['fields']
        self.assertEqual(f['stage']['value'],'ISSUER_REPORTED_CLOSING_COMPLETED')
        self.assertEqual(f['page_display_date']['value'],'2026-09-02')
        self.assertIn('今(1)日',f['body_day_text']['value']);self.assertTrue(f['date_conflict']['value'])
        self.assertIsNone(f['canonical_effective_at']['value'])

    def test_board_approval_not_paid_and_policyholders_not_shareholders(self):
        f=self.obs('ISSUER_CLOSING_REPORT')['fields']
        self.assertEqual(f['board_participation_amount']['value'],'160')
        self.assertEqual(f['board_participation_amount']['unit'],'HUNDRED_MILLION_TWD')
        self.assertEqual(f['capital_increase_stage']['value'],'BOARD_APPROVED_PARTICIPATION_ONLY')
        self.assertIsNone(f['capital_increase_paid']['value'])
        self.assertIn('NOT_2884_SHAREHOLDERS',f['protected_recipient']['value'])
        for k in ('actual_issued_shares','existing_2884_entitlement','existing_2884_impact'):self.assertIsNone(f[k]['value'])

    def test_incomplete_or_wrong_issuer_article_refused(self):
        a=self.catalog['sources'][core.ESUN]['native_evidence']
        for part,old,new in [('title','玉山金控','其他公司'),('body','股權交割程序','尚未交割'),('body','董事會也通過參與','已繳款')]:
            b=deepcopy(a);b[part]=b[part].replace(old,new)
            with self.assertRaises(ValueError):core.parse_esun(b)

    def test_tcc_month_thousand_shares_not_pro_rata_holder_action(self):
        o=self.obs('TREASURY_CANCELLATION_MONTH_REPORTED');f=o['fields']
        self.assertEqual(f['cancellation_month']['value'],'2026-01')
        self.assertEqual(f['cancellation_month']['unit'],'ISO_MONTH')
        self.assertEqual(f['cancellation_quantity']['value'],'28000')
        self.assertEqual(f['cancellation_quantity']['unit'],'THOUSAND_SHARES')
        self.assertEqual(o['entitled_old_code'],'ISSUER_TREASURY_NOT_PRO_RATA_HOLDERS')
        for k in ('exact_effective_date','holder_conversion_ratio','holder_cashflow'):self.assertIsNone(f[k]['value'])

    def test_reconciliation_is_one_cancellation_not_three_events(self):
        obs=[o for o in self.catalog['observations'] if o['action_type']=='TREASURY_CANCELLATION_MONTH_REPORTED']
        self.assertEqual(len(obs),1);f=obs[0]['fields']
        self.assertEqual([f[k]['value'] for k in ('treasury_opening','treasury_cancelled','treasury_closing')],['58000','28000','30000'])
        self.assertIn('NOT_EVENT',f['treasury_opening']['date_role'])

    def test_tcc_unit_or_reconciliation_mutation_refused(self):
        a=self.catalog['sources'][core.TCC]['native_evidence']
        for page,old,new in [('52','仟 股','股'),('57','仟股數','股數'),('57','30,000','31,000')]:
            b=deepcopy(a);self.assertIn(old,b[page]);b[page]=b[page].replace(old,new)
            with self.assertRaises(ValueError):core.parse_tcc(b)

    def test_report_thousand_twd_does_not_replace_approved_exact_twd(self):
        p=core.precision_comparison(self.catalog)
        self.assertEqual(p['parent_approved_total_twd'],'5994545394')
        self.assertEqual(p['new_report_total'],'5994545');self.assertEqual(p['new_report_unit'],'THOUSAND_TWD')
        self.assertEqual(p['difference_from_scaled_display_twd'],'394');self.assertFalse(p['parent_total_replaced'])
        self.assertIn('NOT_EVIDENCE_OF_ADJUSTMENT_OR_CONTRADICTION',p['interpretation'])

    def test_blank_native_scanned_page_is_not_absent_page(self):
        e=self.catalog['sources'][core.TCC]['native_evidence']
        self.assertEqual(e['7'],'');self.assertTrue(self.catalog['facts'][core.TCC]['native_page7_text_empty'])
        image=source.OUT/'visual/tcc-2026-q2-consolidated-report-p7.png'
        self.assertTrue(image.read_bytes().startswith(b'\x89PNG'));self.assertGreater(image.stat().st_size,50000)
        self.assertEqual(json.loads((self.raw/(core.TCC+'.extraction.json')).read_text())['pages'],124)

    def test_capital_balance_and_general_law_not_personal_net(self):
        o=self.obs('FINANCIAL_REPORT_RESOLUTION_CORROBORATION')
        for k in ('final_adjusted_per_share','tax_origin_subtype','personal_net_cash','actual_investor_receipt'):
            self.assertIsNone(o['fields'][k]['value'])
            with self.assertRaises(ValueError):core.resolve(self.catalog,k,request(o,k))
        tax=next(o for o in self.catalog['parent_catalog']['observations'] if o['action_type']=='GENERAL_TAX_INTERPRETATION')
        self.assertIsNone(tax['fields']['personal_net_cash']['value'])

    def test_capture_and_readback_not_announcement_or_historical_availability(self):
        for o in self.catalog['observations']:
            s=self.catalog['sources'][o['source_ids'][0]]
            self.assertEqual(o['observed_at'],s['readback_at']);self.assertIsNone(o['announced_at'])
            self.assertLessEqual(datetime.fromisoformat(s['captured_at']),datetime.fromisoformat(o['observed_at']))
            self.assertFalse(o['historical_signal_eligible'])
        o=self.obs('TAIFEX_CORROBORATES_UNDERLYING_RESUMPTION')
        before=(datetime.fromisoformat(o['observed_at'])-timedelta(seconds=1)).isoformat()
        with self.assertRaises(ValueError):core.resolve(self.catalog,'stock_resumption_date',request(o,'stock_resumption_date',observed_as_of=before))

    def test_correct_source_query_and_date_role_mismatch_refusal(self):
        o=self.obs('TAIFEX_CORROBORATES_UNDERLYING_RESUMPTION');name='stock_resumption_date'
        self.assertEqual(core.resolve(self.catalog,name,request(o,name))['value'],'2025-11-06')
        for change in [dict(issuer_code='1101'),dict(old_instrument='DN_FUTURES_AND_OPTIONS'),dict(date_role='SOURCE_DOCUMENT_DATE_NOT_PUBLICATION'),
                dict(entitled_old_code='2884'),dict(unit='TWD'),dict(version_id='latest')]:
            with self.assertRaises(ValueError):core.resolve(self.catalog,name,request(o,name,**change))

    def test_source_facts_never_final_ledger_or_historical_signal(self):
        o=self.obs('TAIFEX_CORROBORATES_UNDERLYING_RESUMPTION');name='stock_resumption_date'
        for change in [dict(purpose='FINAL_LEDGER'),dict(historical_signal=True)]:
            with self.assertRaises(ValueError):core.resolve(self.catalog,name,request(o,name,**change))

    def test_rehashed_scope_units_authority_or_unknown_promotions_refused(self):
        cases=[('TAIFEX_CORROBORATES_UNDERLYING_RESUMPTION','authority','value','TWSE_DIRECT'),
            ('TAIFEX_CORROBORATES_UNDERLYING_RESUMPTION','suspension_end_date','value','2025-11-05'),
            ('ISSUER_CLOSING_REPORT','canonical_effective_at','value','2026-09-01'),
            ('ISSUER_CLOSING_REPORT','existing_2884_impact','value','NONE'),
            ('TREASURY_CANCELLATION_MONTH_REPORTED','exact_effective_date','value','2026-01-01'),
            ('TREASURY_CANCELLATION_MONTH_REPORTED','cancellation_quantity','unit','SHARES'),
            ('FINANCIAL_REPORT_RESOLUTION_CORROBORATION','personal_net_cash','value','0')]
        for kind,name,key,value in cases:
            c=deepcopy(self.catalog);i=next(i for i,o in enumerate(c['observations']) if o['action_type']==kind)
            c['observations'][i]['fields'][name][key]=value;c['observations'][i]=identify(c['observations'][i])
            with self.assertRaises(ValueError):core.validate(identify(c))

    def test_rehashed_native_evidence_or_parsed_facts_mutation_refused(self):
        for which in ('facts','native'):
            c=deepcopy(self.catalog)
            if which=='facts':c['facts'][core.TCC]['cancellation_month']='2026-01-01'
            else:c['sources'][core.TCC]['native_evidence']['52']='invented'
            with self.assertRaises(ValueError):core.validate(identify(c))

    def test_exact_parent_and_coverage_immutable(self):
        self.assertEqual(self.catalog['parent_catalog'],json.loads((source.parent_source.OUT/'catalog-v06.json').read_text()))
        self.assertEqual(self.catalog['coverage'],self.catalog['parent_catalog']['coverage'])
        c=deepcopy(self.catalog);c['coverage']['1101']['status']='VERIFIED_COMPLETE'
        with self.assertRaises(ValueError):core.validate(identify(c))

    def test_accounting_still_refused_for_coverage_net_and_opening_claims(self):
        d=self.data()
        for v in d['coverage'].values():v['status']='VERIFIED_COMPLETE'
        r=core.qualify(d,self.catalog)
        self.assertTrue(any(x.startswith('SOURCE_ACTION_COVERAGE_INCOMPLETE') for x in r['refusal_reasons']))
        self.assertTrue(any('NET' in x for x in r['refusal_reasons']))
        self.assertTrue(any('OPENING' in x for x in r['refusal_reasons']))
        self.assertIn('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED',r['refusal_reasons'])
        self.assertEqual(r['daily'],[]);self.assertEqual(r['journal'],[]);self.assertIsNone(r['total_net_return'])
        self.assertFalse(r['original_numeric_replay_called'])

    def test_source_binding_mismatch_rejected_before_parent_qualification(self):
        d=self.data();d['source_followup_catalog_id']='latest'
        with self.assertRaises(ValueError):core.qualify(d,self.catalog)

    def test_research_flags_cannot_be_promoted(self):
        for key,value in [('historical_signal_eligible',True),('primary_pressure_id','1101'),('policy_authorized',True)]:
            c=deepcopy(self.catalog);c[key]=value
            with self.assertRaises(ValueError):core.validate(identify(c))

    def test_parent_qualification_retained_and_numeric_replay_not_called(self):
        with patch('rotation_research.action_scope.replay',side_effect=AssertionError('No numeric replay permitted')):
            r=core.qualify(self.data(),self.catalog)
        old=r['source_followup_parent_qualification']
        for key in ('daily','journal','total_net_return','refusal_reasons','status'):self.assertEqual(r[key],old[key])
        self.assertFalse(r['original_numeric_replay_called'])
