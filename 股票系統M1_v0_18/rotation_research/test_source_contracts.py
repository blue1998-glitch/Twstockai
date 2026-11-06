"""Actual archived-source checks and explicitly engineered negative mutations."""
from copy import deepcopy
from datetime import datetime,timedelta
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from . import source_contracts as core
from . import source_contracts_sources as source
from .action_scope import identify
from .action_study import verified_quotes
from .source_qualification import build_calendar
from .test_offline_source_bridge import request


class SourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=source.build_catalog();cls.old,cls.manifest=verified_quotes();cls.calendar=build_calendar()

    def obs(self,kind):return next(o for o in self.catalog['observations'] if o['action_type']==kind)
    def data(self):return source.study_input(self.old,self.catalog,self.manifest,self.calendar,'2026-06-01','2026-09-10','1101')
    def pages(self):return deepcopy(self.catalog['sources'][core.PROSPECTUS]['native_evidence'])

    def test_actual_originals_lengths_hashes_urls_http_and_metadata(self):
        for sid,(size,sha) in source.PINS.items():
            prefix=(source.OLD/sid) if sid==core.PROSPECTUS else (source.OUT/'raw'/sid)
            b=prefix.with_suffix('.response').read_bytes();m=json.loads(Path(str(prefix)+'.meta.json').read_text())
            self.assertEqual(len(b),size);self.assertEqual(hashlib.sha256(b).hexdigest(),sha)
            source.validate_original(sid,b,m)

    def test_wrong_url_http_redirect_bytes_or_meta_rejected(self):
        sid=core.FOLLOWUP;p=source.OUT/'raw'/sid;b=p.with_suffix('.response').read_bytes();m=json.loads(Path(str(p)+'.meta.json').read_text())
        for change in [dict(http=403),dict(url=source.URLS[core.PROSPECTUS]),dict(final_url=source.URLS[core.PROSPECTUS]),
                dict(redirects_followed=True),dict(bytes=len(b)+1),dict(sha256='0'*64)]:
            with self.assertRaises(ValueError):source.validate_original(sid,b,dict(m,**change))
        with self.assertRaises(ValueError):source.validate_original(sid,b+b'changed',m)

    def test_captured_and_fixed_github_original_readback_separate(self):
        s=self.catalog['sources'][core.PROSPECTUS]
        self.assertEqual(s['captured_at'],'2026-10-23T03:28:35.939691+00:00')
        self.assertEqual(s['readback_at'],'2026-10-23T09:31:15.448898+00:00')
        self.assertLess(datetime.fromisoformat(s['captured_at']),datetime.fromisoformat(s['readback_at']))
        self.assertIsNone(s['work_github_readback_at']);self.assertIsNone(s['announced_at'])
        self.assertEqual(s['work_report_status'],'NOT_AVAILABLE_IN_THIS_ENVIRONMENT')

    def test_source_meta_or_selected_page_mutation_rejected(self):
        for name in ['esun-follow-up-2026.meta.json','esun-prospectus-selected.evidence.json']:
            with tempfile.TemporaryDirectory() as td:
                folder=Path(td)/'source';shutil.copytree(source.OUT/'raw',folder/'raw')
                shutil.copyfile(source.OUT/'source-manifest.json',folder/'source-manifest.json')
                p=folder/'raw'/name
                if name.endswith('meta.json'):p.write_bytes(p.read_bytes()+b' ')
                else:
                    value=json.loads(p.read_text());value['175']='unconditional payment';p.write_text(json.dumps(value))
                with self.assertRaises(ValueError):source.load_sources(folder)

    def test_xref_warning_and_765_page_scope_not_erased(self):
        x=json.loads((source.OLD/'esun-prospectus-20260722.extraction.json').read_text())
        self.assertEqual(x['pages'],765);self.assertIn('xref num 5429',x['stderr'])
        self.assertEqual(set(self.pages()),{'162','163','175','176','461'})
        x=json.loads((source.OUT/'pdf-extraction-verification.json').read_text())
        self.assertFalse(x['whole_book_visually_reviewed'])
        self.assertTrue(all(v['extraction_returncode']==0 and v['render_returncode']==0 for v in x['checks']))

    def test_parties_uniform_ids_signature_and_conditional_both_shareholders(self):
        o=self.obs('CONTRACT_PARTIES_AND_CONDITIONAL_DISSENT');f=o['fields']
        self.assertEqual([f[k]['value'] for k in ['party_a_code','party_a_uniform_id','party_b_code','party_b_uniform_id']],['2884','70796305','2867','84443471'])
        self.assertEqual(f['contract_signed_date']['value'],'2025-11-05')
        self.assertEqual(o['entitled_old_code'],'BOTH_2884_AND_2867_CONDITIONAL_DISSENTERS')
        self.assertIn('依法表示異議並請求買回',f['dissent_clause']['value'])
        self.assertIn('IF_EITHER_PARTY',f['condition']['value'])

    def test_party_swap_or_missing_condition_rejected(self):
        p=self.pages()
        with self.assertRaises(ValueError):core.parse_prospectus(p,'2867','2884','2025')
        for n,old,new in [('162','70796305','84443471'),('175','倘甲乙任一方','甲乙任一方')]:
            changed=deepcopy(p);changed[n]=changed[n].replace(old,new)
            with self.assertRaises(ValueError):core.parse_prospectus(changed,'2884','2867','2025')

    def test_personal_dissent_eligibility_exercise_price_quantity_and_cash_all_unknown(self):
        o=self.obs('CONTRACT_PARTIES_AND_CONDITIONAL_DISSENT')
        for k in ['personal_eligibility','person_exercised','request_date','repurchase_price','quantity','payment','actual_disposition','later_amendment_applicability']:
            self.assertIsNone(o['fields'][k]['value'])
            with self.assertRaises(ValueError):core.resolve(self.catalog,k,request(o,k))

    def test_original_and_later_ratio_versions_preserved_not_grant(self):
        v=core.ratio_versions(self.catalog)
        self.assertEqual(v['contract_ratio']['value'],'0.2486')
        self.assertEqual([o['fields']['shares_per_share']['value'] for o in v['exact_parent_versions']],['0.2486','0.2596'])
        self.assertEqual(v['exact_parent_versions'][1]['stage'],'ANNOUNCED_SCHEDULE')
        self.assertIsNone(v['existing_2884_allotment']);self.assertIsNone(v['later_amendment_applicability'])
        self.assertEqual(v['selection'],'NO_AUTOMATIC_ACTIVE_VERSION_OR_PERSONAL_GRANT')

    def test_ratio_and_fractional_policy_cannot_be_borrowed_by_2884_or_2025_dividend(self):
        o=self.obs('ORIGINAL_EXCHANGE_TERMS')
        self.assertEqual(o['entitled_old_code'],'2867')
        self.assertEqual(o['fields']['fractional_rounding']['value'],'ROUND_TO_WHOLE_TWD')
        for change in [dict(entitled_old_code='2884'),dict(old_instrument='2884_ORDINARY_OLD_SHARES'),dict(action_type='2025_STOCK_DIVIDEND')]:
            with self.assertRaises(ValueError):core.resolve(self.catalog,'original_ratio',request(o,'original_ratio',**change))
        self.assertIn('NOT_2025_DIVIDEND',o['fields']['fractional_scope']['value'])
        self.assertIsNone(o['fields']['personal_fractional_payment']['value'])

    def test_projected_total_not_actual_issue_and_equal_rights_not_zero_impact(self):
        f=self.obs('ORIGINAL_EXCHANGE_TERMS')['fields']
        self.assertEqual(f['estimated_post_exchange_total_shares']['value'],'17640615960')
        self.assertIn('ESTIMATED_TOTAL',f['estimated_post_exchange_total_shares']['date_role'])
        self.assertIsNone(f['actual_issued_shares']['value']);self.assertIsNone(f['existing_2884_impact']['value'])
        self.assertIn('權利義務',f['new_share_rights_clause']['value'])

    def test_employee_contract_scope_is_not_shareholder_allotment(self):
        o=self.obs('CONTRACT_EMPLOYEE_AND_TAX_SCOPE')
        self.assertIn('2867_EMPLOYEES',o['fields']['protected_employees']['value'])
        self.assertIsNone(o['fields']['employee_share_grant']['value'])
        o=self.obs('EMPLOYEE_REMUNERATION_CAPITALIZATION_REPORTED')
        self.assertEqual(o['entitled_old_code'],'EMPLOYEES')
        with self.assertRaises(ValueError):core.resolve(self.catalog,'remuneration_amount',request(o,'remuneration_amount',entitled_old_code='2884'))

    def test_2025_capitalization_components_keep_separate_units_and_recipients(self):
        a=self.obs('SHAREHOLDER_BONUS_CAPITALIZATION_REPORTED');b=self.obs('EMPLOYEE_REMUNERATION_CAPITALIZATION_REPORTED');c=self.obs('COMBINED_CAPITALIZATION_SHARES_REPORTED')
        self.assertEqual(a['fields']['bonus_amount']['value'],'1602000')
        self.assertEqual(b['fields']['remuneration_amount']['value'],'522900')
        self.assertEqual(c['fields']['combined_quantity']['value'],'178200')
        self.assertEqual(a['fields']['bonus_amount']['unit'],'THOUSAND_TWD')
        self.assertEqual(c['fields']['combined_quantity']['unit'],'THOUSAND_SHARES')
        self.assertEqual([a['entitled_old_code'],b['entitled_old_code'],c['entitled_old_code']],['2884','EMPLOYEES','MIXED_SHAREHOLDERS_AND_EMPLOYEES'])
        self.assertEqual(a['fields']['meeting_year']['value'],'2025');self.assertEqual(a['fields']['earnings_year']['value'],'2024')

    def test_no_employee_share_count_from_par_and_no_total_allocated_to_shareholders(self):
        e=self.obs('EMPLOYEE_REMUNERATION_CAPITALIZATION_REPORTED')['fields']
        self.assertEqual(e['par_value']['value'],'10')
        self.assertIn('NOT_EMPLOYEE_ISSUE_PRICE',e['par_value']['date_role'])
        for k in ['employee_issued_shares','employee_issue_price']:self.assertIsNone(e[k]['value'])
        o=self.obs('COMBINED_CAPITALIZATION_SHARES_REPORTED')
        for k in ['shareholder_quantity','employee_quantity']:self.assertIsNone(o['fields'][k]['value'])
        with self.assertRaises(ValueError):core.resolve(self.catalog,'combined_quantity',request(o,'combined_quantity',entitled_old_code='2884'))

    def test_registration_not_listing_or_tradability(self):
        f=self.obs('COMBINED_CAPITALIZATION_SHARES_REPORTED')['fields']
        self.assertIn('NOT_LISTING',f['registration_stage']['value'])
        self.assertIsNone(f['registration_date']['value']);self.assertIsNone(f['listing_date']['value'])
        self.assertIsNone(self.obs('SHAREHOLDER_BONUS_CAPITALIZATION_REPORTED')['fields']['tradable_date']['value'])

    def test_explicit_meeting_year_not_last_statement_or_earnings_year(self):
        p=self.pages();f=core.parse_prospectus(p,'2884','2867','2025')
        self.assertEqual(f['meeting_year'],'2025');self.assertEqual(f['earnings_year'],'2024')
        with self.assertRaises(ValueError):core.parse_prospectus(p,'2884','2867','2026')
        changed=deepcopy(p);changed['461']=changed['461'].replace('仟 股','股')
        with self.assertRaises(ValueError):core.parse_prospectus(changed,'2884','2867','2025')

    def test_followup_actual_resolution_and_approval_date_roles(self):
        f=self.obs('FOLLOWUP_APPROVAL_REPORT')['fields']
        self.assertEqual(f['meeting_resolution_date']['value'],'2026-01-23')
        self.assertEqual(f['regulatory_approval_date']['value'],'2026-07-07')
        self.assertEqual(f['meeting_resolution_date']['date_role'],'MEETING_RESOLUTION_NOT_CLOSING')
        self.assertIn('NOT_CODE_PRINTED_IN_BODY',f['issuer_identity_basis']['value'])
        self.assertIsNone(f['canonical_effective_at']['value'])

    def test_followup_wrong_owner_subject_or_conflicting_date_refused(self):
        p=deepcopy(self.catalog['sources'][core.FOLLOWUP]['native_evidence'])
        with self.assertRaises(ValueError):core.parse_followup(p,'1101')
        for old,new in [('三商美邦','另一公司'),('2026.01.23','2026.08.23'),('取得金管會核准','尚未取得核准')]:
            changed={'1':p['1'].replace(old,new)}
            with self.assertRaises(ValueError):core.parse_followup(changed,'2884')

    def test_followup_does_not_resolve_parent_closing_date_conflict(self):
        o=next(o for o in self.catalog['parent_catalog']['observations'] if o['action_type']=='ISSUER_CLOSING_REPORT')
        self.assertEqual(o['fields']['page_display_date']['value'],'2026-09-02')
        self.assertIn('今(1)日',o['fields']['body_day_text']['value'])
        self.assertTrue(o['fields']['date_conflict']['value']);self.assertIsNone(o['fields']['canonical_effective_at']['value'])

    def test_tax_expense_clause_not_exemption_zero_fees_or_personal_net(self):
        o=self.obs('CONTRACT_EMPLOYEE_AND_TAX_SCOPE')
        self.assertIn('各自負擔',o['fields']['tax_expense_clause']['value'])
        for k in ['personal_tax','nhi','fees','personal_net_cash','tax_exempt']:
            self.assertIsNone(o['fields'][k]['value'])
            with self.assertRaises(ValueError):core.resolve(self.catalog,k,request(o,k))

    def test_knowledge_time_not_signature_date_or_missing_work_readback(self):
        o=self.obs('CONTRACT_PARTIES_AND_CONDITIONAL_DISSENT')
        self.assertIsNone(o['announced_at']);self.assertFalse(o['historical_signal_eligible'])
        before=(datetime.fromisoformat(o['observed_at'])-timedelta(seconds=1)).isoformat()
        with self.assertRaises(ValueError):core.resolve(self.catalog,'contract_signed_date',request(o,'contract_signed_date',observed_as_of=before))
        c=deepcopy(self.catalog);c['sources'][core.PROSPECTUS]['work_github_readback_at']=o['observed_at']
        with self.assertRaises(ValueError):core.validate(identify(c))

    def test_correct_query_and_wrong_date_role_version_unit_or_holder_refused(self):
        o=self.obs('FOLLOWUP_APPROVAL_REPORT');name='regulatory_approval_date'
        self.assertEqual(core.resolve(self.catalog,name,request(o,name))['value'],'2026-07-07')
        for change in [dict(version_id='latest'),dict(date_role='ACTUAL_CLOSING_DATE'),dict(unit='YEAR'),dict(issuer_code='1101'),dict(entitled_old_code='2884')]:
            with self.assertRaises(ValueError):core.resolve(self.catalog,name,request(o,name,**change))

    def test_no_final_ledger_or_historical_signal_usage(self):
        o=self.obs('ORIGINAL_EXCHANGE_TERMS');name='original_ratio'
        for change in [dict(purpose='FINAL_LEDGER'),dict(historical_signal=True)]:
            with self.assertRaises(ValueError):core.resolve(self.catalog,name,request(o,name,**change))

    def test_rehashed_promotions_of_condition_unit_date_or_personal_zero_refused(self):
        cases=[('CONTRACT_PARTIES_AND_CONDITIONAL_DISSENT','personal_eligibility','value',True),
            ('CONTRACT_PARTIES_AND_CONDITIONAL_DISSENT','later_amendment_applicability','value',True),
            ('COMBINED_CAPITALIZATION_SHARES_REPORTED','combined_quantity','unit','SHARES'),
            ('EMPLOYEE_REMUNERATION_CAPITALIZATION_REPORTED','employee_issued_shares','value','52290000'),
            ('FOLLOWUP_APPROVAL_REPORT','canonical_effective_at','value','2026-07-07'),
            ('CONTRACT_EMPLOYEE_AND_TAX_SCOPE','fees','value','0')]
        for kind,key,attr,value in cases:
            c=deepcopy(self.catalog);i=next(i for i,o in enumerate(c['observations']) if o['action_type']==kind)
            c['observations'][i]['fields'][key][attr]=value;c['observations'][i]=identify(c['observations'][i])
            with self.assertRaises(ValueError):core.validate(identify(c))

    def test_source_native_evidence_or_fact_mutation_rejected(self):
        for which in ['facts','native']:
            c=deepcopy(self.catalog)
            if which=='facts':c['facts'][core.PROSPECTUS]['original_exchange_ratio']='0.2596'
            else:c['sources'][core.PROSPECTUS]['native_evidence']['175']='no conditions'
            with self.assertRaises(ValueError):core.validate(identify(c))

    def test_exact_parent_object_and_incomplete_coverage_preserved(self):
        self.assertEqual(self.catalog['parent_catalog'],json.loads((source.parent_source.OUT/'catalog-v07.json').read_text()))
        self.assertEqual(self.catalog['coverage'],self.catalog['parent_catalog']['coverage'])
        for which in ['parent_catalog_id','coverage']:
            c=deepcopy(self.catalog)
            if which=='parent_catalog_id':c[which]='latest'
            else:c[which]['2884']['status']='VERIFIED_COMPLETE'
            with self.assertRaises(ValueError):core.validate(identify(c))

    def test_old_missing_nulls_unknowns_and_tcc_precision_preserved(self):
        p=self.catalog['parent_catalog'];q=json.loads((source.parent_source.OUT/'catalog-v07.json').read_text())
        self.assertEqual(p,q)
        for when in ['2025-11-05','2025-11-06']:
            d=core.parent.quote_diagnostic(p,'2884',when,None,True)
            self.assertFalse(d['execution_qualified']);self.assertIsNone(d['imputed_close']);self.assertIsNone(d['valuation']);self.assertIsNone(d['suspension_end_date'])
        o=next(o for o in p['observations'] if o['action_type']=='TREASURY_CANCELLATION_MONTH_REPORTED')
        self.assertEqual(o['fields']['cancellation_month']['value'],'2026-01')
        self.assertEqual(o['fields']['cancellation_quantity']['unit'],'THOUSAND_SHARES')

    def test_full_flags_do_not_cover_net_opening_or_exchange_gaps(self):
        d=self.data()
        for v in d['coverage'].values():v['status']='VERIFIED_COMPLETE'
        r=core.qualify(d,self.catalog)
        self.assertTrue(any(x.startswith('SOURCE_ACTION_COVERAGE_INCOMPLETE') for x in r['refusal_reasons']))
        self.assertTrue(any('NET' in x for x in r['refusal_reasons']));self.assertTrue(any('OPENING' in x for x in r['refusal_reasons']))
        self.assertIn('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED',r['refusal_reasons'])
        self.assertEqual(r['daily'],[]);self.assertEqual(r['journal'],[]);self.assertIsNone(r['total_net_return'])

    def test_research_flags_and_binding_cannot_promote_or_skip_parent(self):
        for k,v in [('historical_signal_eligible',True),('primary_pressure_id','2884'),('policy_authorized',True)]:
            c=deepcopy(self.catalog);c[k]=v
            with self.assertRaises(ValueError):core.validate(identify(c))
        d=self.data();d['source_contracts_catalog_id']='latest'
        with self.assertRaises(ValueError):core.qualify(d,self.catalog)

    def test_parent_qualification_exact_and_no_numeric_replay(self):
        d=self.data();prior=deepcopy(d);prior.pop('source_contracts_catalog_id')
        with patch('rotation_research.action_scope.replay',side_effect=AssertionError('No unauthorized accounting')):
            a=core.qualify(d,self.catalog);b=core.parent.qualify(prior,self.catalog['parent_catalog'])
        self.assertEqual({k:v for k,v in a.items() if k!='source_contracts_catalog_id'},b)
        self.assertFalse(a['original_numeric_replay_called'])

    def test_actual_window_grid_computed_from_saved_inputs_not_summary_literals(self):
        values=source.run();windows=values['window-qualification.json']['windows'];v=values['verification.json']
        self.assertEqual(v['qualification_calls'],sum(w['end'] is not None for w in windows))
        self.assertEqual(v['refused_windows'],sum(w['status']=='REFUSED_INCOMPLETE_EVENT_ACCOUNTING' for w in windows))
        self.assertEqual((v['refused_windows'],v['insufficient_windows'],v['exchange_unsupported_windows'],v['qualified_total_net_return_windows']),(70,2,8,0))
        self.assertTrue(all(w.get('daily',[])==[] and w.get('journal',[])==[] and w.get('total_net_return') is None for w in windows))
        self.assertEqual(values['missing-quotes.json'],json.loads((source.parent_source.OUT/'missing-quotes.json').read_text()))
