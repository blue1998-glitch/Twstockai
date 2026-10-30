"""Archived-original acceptance; mutated inputs below are engineered negatives."""
from copy import deepcopy
from datetime import datetime,timedelta
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from . import capital_components as core
from . import capital_components_sources as source
from .action_scope import identify
from .action_study import verified_quotes
from .source_qualification import build_calendar
from .test_offline_source_bridge import request


class CapitalComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=source.build_catalog();cls.old,cls.manifest=verified_quotes();cls.calendar=build_calendar()

    def obs(self,kind):return next(o for o in self.catalog['observations'] if o['action_type']==kind)
    def data(self):return source.study_input(self.old,self.catalog,self.manifest,self.calendar,'2026-06-01','2026-09-10','1101')
    def text(self,page):return self.catalog['source']['native_evidence'][str(page)]

    def test_actual_pdf_meta_native_sha_and_no_new_originals_or_fetches(self):
        b=(source.OLD/(core.SOURCE_ID+'.response')).read_bytes()
        self.assertEqual(len(b),14607733);self.assertEqual(hashlib.sha256(b).hexdigest(),source.PDF_SHA)
        m=self.catalog['source']['manifest']
        self.assertEqual(m['original_official_capture']['http'],200)
        self.assertEqual(m['official_network_requests'],0);self.assertEqual(m['source_pdf_github_requests'],0)
        self.assertEqual(m['original_official_capture']['url'],source.parent_source.URLS[core.SOURCE_ID])

    def test_reextracted_two_physical_pages_equal_archived_native_and_xref_retained(self):
        v=json.loads((source.OUT/'pdf-extraction-verification.json').read_text())
        self.assertEqual(v['total_original_pages'],765);self.assertFalse(v['whole_book_visually_reviewed'])
        self.assertEqual([(x['physical_pdf_page'],x['printed_page']) for x in v['checks']],[(391,11),(456,76)])
        self.assertTrue(all(x['byte_equal_to_archived_full_native_page'] and x['extraction_returncode']==0 and x['render_returncode']==0 for x in v['checks']))
        self.assertTrue(all('xref num 5429' in x['extraction_stderr'] for x in v['checks']))

    def test_metadata_text_or_original_tamper_refused(self):
        for kind in ['manifest','page','pdf']:
            with tempfile.TemporaryDirectory() as td:
                folder=Path(td)/'new';shutil.copytree(source.OUT/'raw',folder/'raw');shutil.copyfile(source.OUT/'source-manifest.json',folder/'source-manifest.json')
                old=source.OLD
                if kind=='manifest':
                    p=folder/'source-manifest.json';p.write_bytes(p.read_bytes()+b' ')
                elif kind=='page':
                    p=folder/'raw/esun-prospectus-p391.txt';p.write_bytes(p.read_bytes().replace(b'160,200',b'313,800'))
                else:
                    old=Path(td)/'old';old.mkdir()
                    for p in source.OLD.glob('esun-prospectus-20260722.*'):shutil.copyfile(p,old/p.name)
                    p=old/(core.SOURCE_ID+'.response');p.write_bytes(p.read_bytes()+b'changed')
                with self.assertRaises(ValueError):source.load_source(folder,old)

    def test_lower_year_boundaries_select_160200_not_upper_313800(self):
        p=core.parse_equity(self.text(391),'2025','2024')
        self.assertEqual(p['start_after_balance_date'],'2024-12-31');self.assertEqual(p['end_before_balance_date'],'2025-12-31')
        self.assertEqual(p['rows']['B9']['cells']['share_count']['value'],'160200')
        self.assertIn('313,800',self.text(391))
        with self.assertRaises(ValueError):core.parse_equity(self.text(391),'2025','2023')

    def test_prior_balance_digits_do_not_merge_with_profit_year_heading(self):
        self.assertIn('253,474,357',self.text(391))
        p=core.parse_equity(self.text(391),'2025','2024')
        self.assertEqual(p['earnings_year'],'2024')
        self.assertEqual(p['rows']['N1']['cells']['capital_surplus']['value'],'342900')

    def test_missing_reversed_or_duplicate_closing_balance_boundaries_refused(self):
        t=self.text(391)
        for changed in [t.replace('Z1    113 年 12 月 31 日餘額','Z1    112 年 12 月 31 日餘額'),t+t]:
            with self.assertRaises(ValueError):core.parse_equity(changed,'2025','2024')

    def test_b9_n1_exact_column_names_units_and_financial_accounts(self):
        rows=self.catalog['facts']['equity_table']['rows'];b,n=rows['B9']['cells'],rows['N1']['cells']
        self.assertEqual([n[k]['value'] for k in ['share_count','ordinary_share_capital','capital_surplus','total_equity']],['18000','180000','342900','522900'])
        self.assertEqual(n['share_count']['unit'],'THOUSAND_SHARES')
        self.assertTrue(all(n[k]['unit']=='THOUSAND_TWD' for k in ['ordinary_share_capital','capital_surplus','total_equity']))
        self.assertEqual(b['share_count']['column_label'],'股數(仟股)');self.assertEqual(n['total_equity']['column_label'],'權益總額')

    def test_column_unit_or_column_order_mismatch_refused(self):
        t=self.text(391)
        for changed in [t.replace('仟 股','仟 元'),t.replace('普 通 股 股 本','普通股未知'),t.replace('股 數 （ 仟 股 ）','普通股股本')]:
            self.assertNotEqual(changed,t)
            with self.assertRaises(ValueError):core.parse_equity(changed,'2025','2024')

    def test_missing_numeric_column_and_inconsistent_accounts_refused(self):
        t=self.text(391)
        for changed in [t.replace('342,900','342,901'),t.replace('342,900','')]:
            with self.assertRaises(ValueError):core.parse_equity(changed,'2025','2024')

    def test_dash_marker_not_defaulted_to_zero(self):
        b=self.catalog['facts']['equity_table']['rows']['B9']['cells']
        self.assertIsNone(b['capital_surplus']['value']);self.assertIsNone(b['total_equity']['value'])
        self.assertEqual(b['total_equity']['source_marker'],'DASH_NOT_DEFAULTED_TO_ZERO')
        self.assertEqual(b['unappropriated_earnings']['value'],'-1602000')

    def test_explicit_113_earnings_selects_2025_board_and_2905_reference(self):
        p=core.parse_board(self.text(456),'2024')['selected']
        self.assertEqual(p['board_date'],'2025-03-07');self.assertEqual(p['employee_quantity'],'18000')
        self.assertEqual(p['calculation_reference'],'29.05');self.assertEqual(p['source_column_label'],'113年度')
        self.assertEqual(p['source_column_ordinal'],2)

    def test_114_earnings_2026_board_3305_preserved_separately(self):
        p=core.parse_board(self.text(456),'2025')['selected']
        self.assertEqual(p['board_date'],'2026-03-13');self.assertEqual(p['calculation_reference'],'33.05')
        self.assertEqual(p['source_column_label'],'114年度')
        self.assertEqual(len(self.catalog['facts']['board_reference']['versions']),2)
        with self.assertRaises(ValueError):core.parse_board(self.text(456),'2023')

    def test_board_table_and_quantity_year_pairing_mismatch_refused(self):
        t=self.text(456)
        changed=t.replace('114 及 113 年 度 員 工 酬 勞 股 數','113 及 114 年 度 員 工 酬 勞 股 數')
        self.assertNotEqual(changed,t)
        with self.assertRaises(ValueError):core.parse_board(changed,'2024')

    def test_reported_calculation_reference_never_raw_trade_or_valuation(self):
        o=self.obs('EMPLOYEE_BOARD_CALCULATION_REFERENCE');f=o['fields']
        self.assertEqual(f['calculation_reference']['value'],'29.05')
        self.assertIn('NOT_RAW_PRICE_TRADE_OR_VALUATION',f['calculation_reference']['date_role'])
        for k in ['personal_transaction_price','raw_price','imputed_close','valuation']:
            self.assertIsNone(f[k]['value'])
            with self.assertRaises(ValueError):core.resolve(self.catalog,k,request(o,k))

    def test_group_holders_and_instruments_not_personal_or_2867_exchange(self):
        a=self.obs('SHAREHOLDER_STOCK_BONUS_GROUP_REPORTED');b=self.obs('EMPLOYEE_CAPITALIZATION_GROUP_REPORTED')
        self.assertNotEqual(a['entitled_old_code'],b['entitled_old_code'])
        for change in [dict(entitled_old_code='2884'),dict(entitled_old_code='2867'),dict(old_instrument='2867_ORDINARY_OLD_SHARES')]:
            with self.assertRaises(ValueError):core.resolve(self.catalog,'share_count',request(a,'share_count',**change))

    def test_parent_nulls_preserved_despite_new_company_18000(self):
        p=self.catalog['parent_catalog']
        employee=next(o for o in p['observations'] if o['action_type']=='EMPLOYEE_REMUNERATION_CAPITALIZATION_REPORTED')
        combined=next(o for o in p['observations'] if o['action_type']=='COMBINED_CAPITALIZATION_SHARES_REPORTED')
        self.assertIsNone(employee['fields']['employee_issued_shares']['value'])
        self.assertIsNone(combined['fields']['employee_quantity']['value'])
        self.assertEqual(self.obs('EMPLOYEE_CAPITALIZATION_GROUP_REPORTED')['fields']['share_count']['value'],'18000')

    def test_personal_ratio_allotment_fractional_tradability_and_opening_claims_unknown(self):
        o=self.obs('SHAREHOLDER_STOCK_BONUS_GROUP_REPORTED')
        for k in ['personal_allotted_shares','personal_unrounded_ratio','fractional_deadline','fractional_disposition','listing_date','tradable_date','personal_net_cash','opening_entitlement']:
            self.assertIsNone(o['fields'][k]['value'])
            with self.assertRaises(ValueError):core.resolve(self.catalog,k,request(o,k))

    def test_same_family_shares_and_accounts_reconcile_to_parent_p461(self):
        r=self.catalog['reconciliation']
        self.assertEqual(r['share_sum'],'178200');self.assertEqual(r['share_unit'],'THOUSAND_SHARES')
        self.assertEqual(r['employee_account_sum'],'522900');self.assertEqual(r['money_unit'],'THOUSAND_TWD')
        self.assertTrue(all(r['checks'].values()));self.assertEqual(len(r['parent_p461_observation_ids']),3)
        self.assertEqual(r['numeric_ledger_events_added'],0);self.assertEqual(r['independent_market_samples_added'],0)
        self.assertIn('NOT_AUTOMATIC_EVENT_MERGE_OR_PERSONAL_ALLOCATION',r['qualification'])

    def test_reconciliation_rejects_share_money_unit_borrowing_and_duplicate_event_counts(self):
        c=deepcopy(self.catalog);c['facts']['equity_table']['rows']['N1']['cells']['share_count']['unit']='THOUSAND_TWD'
        with self.assertRaises(ValueError):core.reconcile(c)
        c=deepcopy(self.catalog);c['facts']['equity_table']['rows']['N1']['cells']['capital_surplus']['unit']='THOUSAND_SHARES'
        with self.assertRaises(ValueError):core.reconcile(c)
        c=deepcopy(self.catalog);c['reconciliation']['numeric_ledger_events_added']=3
        with self.assertRaises(ValueError):core.validate(identify(c))

    def test_official_capture_prior_codex_readback_and_new_local_observation_separate(self):
        s=self.catalog['source'];m=s['manifest']
        self.assertEqual(m['original_official_capture']['completed_at'],'2026-10-23T03:28:35.939691+00:00')
        self.assertEqual(s['prior_codex_github_readback_at'],'2026-10-23T09:31:15.448898+00:00')
        self.assertEqual(m['work_reported_local_reuse']['observed_at'],'2026-10-23T11:37:58.421958Z')
        self.assertIn('USER_REPORTED_WORK_LOCAL_REUSE',m['work_reported_local_reuse']['role'])
        self.assertIsNone(s['work_github_readback_at']);self.assertIsNone(s['announced_at'])
        self.assertGreater(datetime.fromisoformat(s['codex_analysis_observed_at']),datetime.fromisoformat(s['prior_codex_github_readback_at']))

    def test_work_local_time_cannot_fill_unknown_github_or_official_capture(self):
        for what in ['work','official','prior']:
            c=deepcopy(self.catalog);s=c['source'];work=s['manifest']['work_reported_local_reuse']['observed_at']
            if what=='work':s['work_github_readback_at']=work
            elif what=='official':s['original_official_capture']['completed_at']=work
            else:s['prior_codex_github_readback_at']=work
            with self.assertRaises(ValueError):core.validate(identify(c))

    def test_observation_cutoff_and_date_role_unit_version_binding(self):
        o=self.obs('EMPLOYEE_BOARD_CALCULATION_REFERENCE');name='board_date'
        self.assertEqual(core.resolve(self.catalog,name,request(o,name))['value'],'2025-03-07')
        before=(datetime.fromisoformat(o['observed_at'])-timedelta(seconds=1)).isoformat()
        for change in [dict(observed_as_of=before),dict(version_id='latest'),dict(date_role='LISTING_DATE'),dict(unit='TWD')]:
            with self.assertRaises(ValueError):core.resolve(self.catalog,name,request(o,name,**change))

    def test_final_ledger_and_historical_signal_usage_refused(self):
        o=self.obs('SHAREHOLDER_STOCK_BONUS_GROUP_REPORTED')
        for change in [dict(purpose='FINAL_LEDGER'),dict(historical_signal=True)]:
            with self.assertRaises(ValueError):core.resolve(self.catalog,'share_count',request(o,'share_count',**change))

    def test_issuer_source_or_native_fact_mutation_refused(self):
        for what in ['issuer','native','fact']:
            c=deepcopy(self.catalog)
            if what=='issuer':c['source']['issuer_code']='1101'
            elif what=='native':c['source']['native_evidence']['391']='different source'
            else:c['facts']['board_reference']['selected']['calculation_reference']='33.05'
            with self.assertRaises(ValueError):core.validate(identify(c))

    def test_rehashed_personal_zero_or_company_unit_promotions_refused(self):
        for name,attr,value in [('personal_allotted_shares','value','160200000'),('personal_net_cash','value','0'),('share_count','unit','SHARES')]:
            c=deepcopy(self.catalog);o=c['observations'][0];o['fields'][name][attr]=value;c['observations'][0]=identify(o)
            with self.assertRaises(ValueError):core.validate(identify(c))

    def test_exact_parent_full_object_and_coverage_not_promoted(self):
        self.assertEqual(self.catalog['parent_catalog'],json.loads((source.parent_source.OUT/'catalog-v08.json').read_text()))
        c=deepcopy(self.catalog);c['coverage']['2884']['status']='VERIFIED_COMPLETE'
        with self.assertRaises(ValueError):core.validate(identify(c))
        c=deepcopy(self.catalog);c['parent_catalog_id']='latest'
        with self.assertRaises(ValueError):core.validate(identify(c))

    def test_parent_qualification_unchanged_and_incomplete_flags_still_refuse(self):
        d=self.data()
        for v in d['coverage'].values():v['status']='VERIFIED_COMPLETE'
        prior=deepcopy(d);prior.pop('capital_components_catalog_id')
        with patch('rotation_research.action_scope.replay',side_effect=AssertionError('No unauthorized numeric replay')):
            a=core.qualify(d,self.catalog);b=core.parent.qualify(prior,self.catalog['parent_catalog'])
        self.assertEqual({k:v for k,v in a.items() if k!='capital_components_catalog_id'},b)
        self.assertTrue(any('SOURCE_ACTION_COVERAGE_INCOMPLETE' in x for x in a['refusal_reasons']))
        self.assertTrue(any('OPENING' in x for x in a['refusal_reasons']));self.assertTrue(any('NET' in x for x in a['refusal_reasons']))
        self.assertEqual(a['daily'],[]);self.assertEqual(a['journal'],[]);self.assertIsNone(a['total_net_return'])

    def test_research_flags_and_input_binding_cannot_promote(self):
        for k,v in [('historical_signal_eligible',True),('primary_pressure_id','2884'),('policy_authorized',True)]:
            c=deepcopy(self.catalog);c[k]=v
            with self.assertRaises(ValueError):core.validate(identify(c))
        d=self.data();d['capital_components_catalog_id']='latest'
        with self.assertRaises(ValueError):core.qualify(d,self.catalog)

    def test_actual_window_grid_summary_derived_from_rows_and_old_missing_preserved(self):
        values=source.run();v=values['verification.json'];windows=values['window-qualification.json']['windows']
        self.assertEqual(v['qualification_calls'],sum(w['end'] is not None for w in windows))
        self.assertEqual(v['refused_windows'],sum(w['status']=='REFUSED_INCOMPLETE_EVENT_ACCOUNTING' for w in windows))
        self.assertEqual((v['refused_windows'],v['insufficient_windows'],v['exchange_unsupported_windows'],v['qualified_total_net_return_windows']),(70,2,8,0))
        self.assertTrue(all(w.get('daily',[])==[] and w.get('journal',[])==[] and w.get('total_net_return') is None for w in windows))
        self.assertEqual(values['missing-quotes.json'],json.loads((source.parent_source.OUT/'missing-quotes.json').read_text()))
