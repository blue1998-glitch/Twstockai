"""Focused source/recipient/date/null/admission regressions, not strategy tests."""
from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from . import source_diagnostics as core
from . import source_diagnostics_sources as source
from .action_scope import identify
from .action_scope_sources import field
from .action_resolution_sources import input_for
from .action_study import verified_quotes
from .source_qualification import build_calendar


def request(obs, name, **changes):
    r = {k:obs[k] for k in ('family', 'issuer_code', 'entitled_old_code', 'old_instrument', 'action_type')}
    r.update(version_id=obs['id'], field=name, unit=obs['fields'][name]['unit'],
        date_role=obs['fields'][name]['date_role'], observed_as_of=obs['observed_at'],
        historical_signal=False, purpose='SOURCE_DIAGNOSTIC')
    r.update(changes)
    return r


class SourceDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = source.build_catalog()
        cls.texts, cls.sources, cls.failed = source.load_sources()
        cls.old, cls.manifest = verified_quotes(); cls.calendar = build_calendar()

    def obs(self, kind, name=None):
        return next(o for o in self.catalog['observations'] if o['action_type'] == kind and (name is None or name in o['fields']))

    def probe(self):
        d = input_for(self.old, self.catalog['parent_catalog'], self.manifest, self.calendar,
            '2026-06-01', '2026-09-10', '1101')
        d['source_diagnostics_catalog_id'] = self.catalog['id']
        return d

    def test_exact_formal_parent_and_unknown_coverage_preserved(self):
        parent = json.loads((source.HERE / 'action_resolution_20261023/events-v04.json').read_text())
        self.assertEqual(self.catalog['parent_catalog'], parent)
        self.assertEqual(self.catalog['coverage'], parent['coverage'])
        self.assertEqual(len(parent['inventory']), 8)

    def test_prospectus_matches_user_sha_and_only_claimed_pages(self):
        sid = 'esun-prospectus-20260722'
        self.assertEqual(self.sources[sid]['sha256'], '926f1f871a294702d3e4f5e4d89cf5aeb5e64808593efa2d99b95ed7375388fa')
        p = source.parse_prospectus(self.texts[sid])
        self.assertEqual(p['expected_issue_shares'], '1531510471')
        self.assertEqual(p['ordinary_outstanding_shares'], '16192000000')
        self.assertEqual(p['target_holder_ratio'], '0.2596')

    def test_failed_sources_not_usable_originals_or_empty_reports(self):
        self.assertEqual(len(self.failed), 3)
        self.assertFalse(set(self.failed) & set(self.sources))
        self.assertNotIn('mof-interpretation-143802', self.catalog['sources'])

    def test_missing_days_are_market_open_not_exchange_holidays(self):
        for code, when in [('1101','2025-08-13'),('2884','2025-11-05')]:
            self.assertIn(when, self.calendar['sessions'])
            d = core.quote_diagnostic(self.catalog, code, when, None, True)
            self.assertTrue(d['market_session'])
            self.assertEqual(d['old_missing_cause'], 'UNKNOWN')
            self.assertEqual(d['new_missing_explanation'], 'UNKNOWN')
            self.assertIsNone(d['security_tradable'])

    def test_resume_notice_does_not_supply_suspension_start(self):
        obs = self.obs('SECURITY_RESUMPTION_NOTICE')
        self.assertEqual(obs['fields']['resume_date']['value'], '2025-08-14')
        self.assertIsNone(obs['fields']['suspension_date']['value'])
        d = core.quote_diagnostic(self.catalog, '1101', '2025-08-13', None, True)
        self.assertEqual(len(d['related_resumption_notices']), 1)
        self.assertEqual(d['suspension_observation_ids'], [])

    def test_other_stock_cannot_borrow_resumption(self):
        d = core.quote_diagnostic(self.catalog, '2884', '2025-11-05', None, True)
        self.assertEqual(d['related_resumption_notices'], [])

    def test_null_quote_not_imputed_or_made_executable(self):
        d = core.quote_diagnostic(self.catalog, '1101', '2025-08-13', None, True)
        for k in ['raw_close','imputed_close','valuation']:
            self.assertIsNone(d[k])
        self.assertFalse(d['execution_qualified'])
        self.assertTrue(d['missing_quote_blocks_accounting'])
        with self.assertRaises(ValueError):core.quote_diagnostic(self.catalog,'1101','2025-08-13',None,1)

    def test_engineered_direct_suspension_never_fills_price(self):
        # Synthetic branch coverage only; never saved as an actual market observation.
        c = deepcopy(self.catalog); sid = 'SYNTHETIC_TEST_ONLY'
        c['sources'][sid] = {'kind':'SYNTHETIC_TEST_ONLY_NOT_MARKET_EVIDENCE'}
        obs = identify(dict(family=sid,issuer_code='1101',entitled_old_code='1101',
            old_instrument='1101_ORDINARY_OLD_SHARES',action_type='SECURITY_SUSPENSION_NOTICE',
            source_ids=[sid],observed_at='2026-10-23T00:00:00+00:00',announced_at=None,
            historical_signal_eligible=False,accounting_eligible=False,
            fields={'suspension_date':field('2025-08-13','ISO_DATE','SECURITY_SUSPENSION_ON_DATE',
                [dict(source_id=sid,raw_value='synthetic')],core.QUALIFICATION)}))
        c['observations'].append(obs); c=identify(c)
        d = core.quote_diagnostic(c,'1101','2025-08-13',None,True)
        self.assertEqual(d['new_missing_explanation'],'OFFICIAL_SECURITY_SUSPENSION_ON_DATE')
        self.assertTrue(d['market_session']); self.assertFalse(d['security_tradable'])
        self.assertFalse(d['execution_qualified']); self.assertIsNone(d['imputed_close'])
        self.assertEqual(core.quote_diagnostic(c,'1101','2025-08-12',None,True)['suspension_observation_ids'],[])

    def test_registration_record_and_listing_roles_not_interchangeable(self):
        v = self.obs('EMPLOYEE_CAPITAL_REGISTRATION', 'registration_date')
        self.assertEqual(core.resolve(self.catalog,'registration_date',request(v,'registration_date'))['value'],'2026-06-30')
        for role in ['ACTUAL_SECURITY_LISTING_NOT_AUTHENTICATED','EMPLOYEE_CAPITAL_RECORD_NOT_REGISTRATION_OR_LISTING']:
            with self.assertRaises(ValueError):
                core.resolve(self.catalog,'registration_date',request(v,'registration_date',date_role=role))
        with self.assertRaises(ValueError): core.resolve(self.catalog,'listing_date',request(v,'listing_date'))

    def test_employee_record_date_is_separate_from_registration(self):
        v = self.obs('EMPLOYEE_CAPITAL_REGISTRATION', 'employee_capital_record_date')
        self.assertEqual(core.resolve(self.catalog,'employee_capital_record_date',request(v,'employee_capital_record_date'))['value'],'2026-07-07')
        self.assertNotEqual(v['fields']['employee_capital_record_date']['date_role'],
            self.obs('EMPLOYEE_CAPITAL_REGISTRATION','registration_date')['fields']['registration_date']['date_role'])

    def test_dividend_record_date_not_ex_trading_date(self):
        v = self.obs('ISSUER_DISTRIBUTION_COMPLETION_REPORT')
        with self.assertRaises(ValueError):
            core.resolve(self.catalog,'dividend_record_date',request(v,'dividend_record_date',date_role='EX_TRADING_DATE'))
        self.assertEqual(v['fields']['dividend_record_date']['value'],'2026-07-07')

    def test_employee_shares_not_old_2884_stock_dividend(self):
        v = self.obs('EMPLOYEE_CAPITAL_REGISTRATION','registration_date')
        with self.assertRaises(ValueError):
            core.resolve(self.catalog,'registration_date',request(v,'registration_date',entitled_old_code='2884',old_instrument='2884_ORDINARY_OLD_SHARES'))

    def test_target_exchange_cannot_credit_existing_2884(self):
        v = self.obs('SHARE_EXCHANGE_EXPECTED_ISSUANCE')
        for changes in [dict(entitled_old_code='2884'),dict(unit='NEW_2884_PER_OLD_2884'),dict(action_type='STOCK_DIVIDEND')]:
            with self.assertRaises(ValueError):
                core.resolve(self.catalog,'target_holder_ratio',request(v,'target_holder_ratio',**changes))
        with self.assertRaises(ValueError):core.resolve(self.catalog,'existing_2884_share_grant',request(v,'existing_2884_share_grant'))

    def test_expected_issue_not_actual_issued_shares(self):
        v = self.obs('SHARE_EXCHANGE_EXPECTED_ISSUANCE')
        self.assertEqual(v['fields']['expected_issue_shares']['value'],'1531510471')
        with self.assertRaises(ValueError):core.resolve(self.catalog,'actual_issued_shares',request(v,'actual_issued_shares'))

    def test_issuer_paid_not_personal_net_or_receipt(self):
        v = self.obs('ISSUER_DISTRIBUTION_COMPLETION_REPORT')
        self.assertEqual(v['fields']['issuer_completed_pay_date']['value'],'2026-07-27')
        self.assertEqual(v['fields']['issuer_reported_gross_per_share']['value'],'1.40')
        for f in ['investor_net_cash','actual_investor_receipt']:
            with self.assertRaises(ValueError):core.resolve(self.catalog,f,request(v,f))

    def test_every_known_source_field_refuses_final_ledger(self):
        for v in self.catalog['observations']:
            for name, f in v['fields'].items():
                if f['value'] is not None:
                    with self.assertRaises(ValueError):core.resolve(self.catalog,name,request(v,name,purpose='FINAL_LEDGER'))

    def test_observation_cutoff_cannot_backfill_history(self):
        v = self.obs('ISSUER_DISTRIBUTION_COMPLETION_REPORT'); f='issuer_completed_pay_date'
        early=(datetime.fromisoformat(v['observed_at'])-timedelta(seconds=1)).isoformat()
        for changes in [dict(observed_as_of=early),dict(observed_as_of='2026-10-23'),dict(historical_signal=True)]:
            with self.assertRaises(ValueError):core.resolve(self.catalog,f,request(v,f,**changes))

    def test_explicit_observation_no_latest_or_unknown_version(self):
        v=self.obs('ISSUER_DISTRIBUTION_COMPLETION_REPORT')
        for version in [None,'latest','wrong']:
            with self.assertRaises(ValueError):core.resolve(self.catalog,'issuer_completed_pay_date',request(v,'issuer_completed_pay_date',version_id=version))

    def test_scope_tamper_rejected_even_with_recomputed_fingerprint(self):
        c=deepcopy(self.catalog);v=next(o for o in c['observations'] if o['action_type']=='SHARE_EXCHANGE_EXPECTED_ISSUANCE')
        v['entitled_old_code']='2884';c['observations'][c['observations'].index(v)]=identify(v)
        with self.assertRaises(ValueError):core.validate(identify(c))

    def test_catalog_complete_flag_cannot_overrule_parent(self):
        c=deepcopy(self.catalog);c['coverage']['2884']['status']='VERIFIED_COMPLETE'
        with self.assertRaises(ValueError):core.validate(identify(c))

    def test_input_complete_flags_do_not_bypass_source_gaps(self):
        d=self.probe()
        for v in d['coverage'].values():v['status']='VERIFIED_COMPLETE'
        result=core.qualify(d,self.catalog)
        self.assertEqual(result['status'],'REFUSED_INCOMPLETE_EVENT_ACCOUNTING')
        self.assertTrue(any(x.startswith('SOURCE_ACTION_COVERAGE_INCOMPLETE:') for x in result['refusal_reasons']))
        self.assertEqual(result['daily'],[]);self.assertEqual(result['journal'],[])
        self.assertIsNone(result['total_net_return'])

    def test_refusal_delegates_parent_without_replay_or_mutation(self):
        d=self.probe();before=deepcopy(d)
        with patch('rotation_research.action_ledger.replay',side_effect=AssertionError('Must not replay')):
            r=core.qualify(d,self.catalog)
        self.assertEqual(d,before)
        self.assertIn('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED',r['refusal_reasons'])
        self.assertFalse(r['original_numeric_replay_called'])
        self.assertEqual(r['parent_qualification']['refusal_reasons'],r['refusal_reasons'])

    def test_source_proof_outside_bound_original_rejected(self):
        c=deepcopy(self.catalog);v=c['observations'][0]
        v['fields']['resume_date']['proofs'][0]['source_id']='esun-prospectus-20260722'
        c['observations'][0]=identify(v)
        with self.assertRaises(ValueError):core.validate(identify(c))

    def test_original_and_derived_text_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);shutil.copytree(source.OUT/'raw',p/'raw');shutil.copy2(source.OUT/'source-manifest.json',p/'source-manifest.json')
            for name in ['tcc-resume-20250814.response','esun-prospectus-20260722.txt']:
                f=p/'raw'/name;b=f.read_bytes();f.write_bytes(b+b'changed')
                with self.assertRaises(ValueError):source.load_sources(p)
                f.write_bytes(b)

    def test_lost_expected_or_actual_condition_is_rejected(self):
        t=self.texts['esun-prospectus-20260722']
        for text in [t.replace('預計','已完成'),t.replace('實際發行新股之數額','')]:
            with self.assertRaises(ValueError):source.parse_prospectus(text)

    def test_followup_column_interleave_is_explicit_not_loose_matching(self):
        t=self.texts['esun-meeting-followup-2026']
        self.assertEqual(source.parse_followup(t)['record_date'],'2026-07-07')
        with self.assertRaises(ValueError):source.parse_followup(t.replace('員工酬勞','既有股東'))

    def test_mof_api_scoped_fields_ignore_viewcount_synthetic_only(self):
        # Engineered contract response, NOT the inaccessible official API original.
        row=dict(TaxVer='所得稅法一一四年版',Title='第14條第一51則',
            Content='101年8月17日台財稅字第10100097670號令',ViewCount=1)
        a=source.parse_mof_api({'Data':{'Table':[row]}})
        row['ViewCount']=99999;b=source.parse_mof_api({'Data':{'Table':[row]}})
        self.assertEqual(a,b)
        for k in ['personal_net','personal_tax','nhi','fees']:self.assertIsNone(a[k])

    def test_mof_api_wrong_edition_or_identity_rejected_synthetic_only(self):
        row=dict(TaxVer='所得稅法114年版',Title='第14條第一51則',Content='101年8月17日台財稅字第10100097670號令')
        for key,value in [('TaxVer','113年版'),('Content','另一函釋'),('Title','')]:
            r=dict(row);r[key]=value
            with self.assertRaises(ValueError):source.parse_mof_api({'Data':{'Table':[r]}})

    def test_general_tax_context_cannot_become_final_or_personal_model(self):
        c=deepcopy(self.catalog);v=deepcopy(c['observations'][0])
        v.update(family='SYNTHETIC_TAX_TEST_ONLY',issuer_code='GENERAL',entitled_old_code='NOT_INVESTOR_SPECIFIC',
            old_instrument='NOT_AN_ENTITLEMENT',action_type='GENERAL_TAX_INTERPRETATION')
        v['fields']={'investor_tax':field('0','TWD','PERSONAL_TAX',[],core.QUALIFICATION)}
        c['observations'].append(identify(v))
        with self.assertRaises(ValueError):core.validate(identify(c))

    def test_no_tuning_or_strategy_qualification_added(self):
        self.assertFalse(self.catalog['historical_signal_eligible'])
        self.assertFalse(self.catalog['policy_authorized'])
        self.assertIsNone(self.catalog['primary_pressure_id'])
        self.assertEqual(len(self.catalog['observations']),5) # not five independent actions


if __name__ == '__main__':unittest.main()
