"""Real archived-source acceptance plus clearly engineered negative cases."""
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import offline_source_bridge as core
from . import offline_source_bridge_sources as source
from .action_scope import identify
from .action_resolution_sources import input_for
from .action_study import verified_quotes
from .source_qualification import build_calendar
from .source_diagnostics_sources import parse_mof_api as old_tax_parser


def request(obs, name, **changes):
    r={k:obs[k] for k in ('family','issuer_code','entitled_old_code','old_instrument','action_type')}
    r.update(version_id=obs['id'],field=name,unit=obs['fields'][name]['unit'],
        date_role=obs['fields'][name]['date_role'],observed_as_of=obs['observed_at'],
        historical_signal=False,purpose='SOURCE_DIAGNOSTIC')
    r.update(changes);return r


class OfflineBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.members,cls.entries=source.read_bridge()
        cls.catalog=source.build_catalog()
        cls.api=json.loads(cls.members['archived_work/mof-tax-api-143802.response'])
        cls.old,cls.manifest=verified_quotes();cls.calendar=build_calendar()

    def suspension(self, code='1101'):
        return next(o for o in self.catalog['observations'] if o['issuer_code']==code)

    def data(self):
        d=input_for(self.old,self.catalog['parent_catalog']['parent_catalog'],self.manifest,self.calendar,
            '2026-06-01','2026-09-10','1101')
        d.update(source_diagnostics_catalog_id=self.catalog['parent_catalog_id'],bridge_catalog_id=self.catalog['id'])
        return d

    def test_actual_zip_sha_length_and_all_40_members(self):
        b=source.BRIDGE.read_bytes()
        self.assertEqual(len(b),941229);self.assertEqual(hashlib.sha256(b).hexdigest(),source.BRIDGE_SHA)
        self.assertEqual(len(self.members),41);self.assertEqual(len(self.entries),40)
        for n,e in self.entries.items():
            self.assertEqual(len(self.members[n]),e['bytes'])
            self.assertEqual(hashlib.sha256(self.members[n]).hexdigest(),e['sha256'])

    def test_changed_zip_bytes_rejected_before_ingestion(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'changed.zip';p.write_bytes(source.BRIDGE.read_bytes()+b'changed')
            with self.assertRaises(ValueError):source.read_bridge(p)

    def test_original_meta_origin_http_size_hash_and_capture_tamper_rejected(self):
        sid='twse-tcc-suspension-20250812';prefix='archived_work/'+sid
        raw=self.members[prefix+'.response'];m=json.loads(self.members[prefix+'.meta.json']);e=self.entries[prefix+'.response']
        for changes in [dict(url=source.SOURCE_URLS['twse-esun-suspension-20251104']),dict(status=403),
                dict(bytes=len(raw)+1),dict(sha256='0'*64),dict(observed_at='2026-10-23'),dict(redirects_followed=True)]:
            bad=dict(m,**changes)
            with self.assertRaises(ValueError):source.validate_original(sid,raw,bad,e)
        with self.assertRaises(ValueError):source.validate_original(sid,raw+b'changed',m,e)

    def test_actual_document_and_start_dates_parsed_from_both_original_texts(self):
        for sid,code,document,start in [('twse-tcc-suspension-20250812','1101','2025-08-12','2025-08-13'),
                ('twse-esun-suspension-20251104','2884','2025-11-04','2025-11-05')]:
            p=core.parse_suspension(self.members['archived_work/'+sid+'.txt'].decode(),code,code+'_ORDINARY_OLD_SHARES')
            self.assertEqual(p['document_date'],document);self.assertEqual(p['suspension_start_date'],start)
            self.assertIsNone(p['suspension_end_date']);self.assertIsNone(p['announced_at'])

    def test_pdf_issuer_and_instrument_mismatch_rejected(self):
        text=self.members['archived_work/twse-tcc-suspension-20250812.txt'].decode()
        for code,instrument in [('2884','2884_ORDINARY_OLD_SHARES'),('1101','1101_PREFERRED_SHARES')]:
            with self.assertRaises(ValueError):core.parse_suspension(text,code,instrument)

    def test_missing_or_conflicting_start_wording_rejected(self):
        t=self.members['archived_work/twse-tcc-suspension-20250812.txt'].decode()
        for changed in [t.replace('暫停交易','恢復交易'),t.replace('8 月 13 日','8 月 14 日')]:
            with self.assertRaises(ValueError):core.parse_suspension(changed,'1101','1101_ORDINARY_OLD_SHARES')

    def test_parent_catalog_exact_and_old_unknown_snapshots_unchanged(self):
        old=json.loads((source.parent_source.OUT/'catalog-v05.json').read_text())
        self.assertEqual(self.catalog['parent_catalog'],old)
        self.assertEqual(self.catalog['coverage'],old['coverage'])
        missing=json.loads((source.parent_source.OUT/'missing-quotes.json').read_text())['diagnostics']
        self.assertTrue(all(d['new_missing_explanation']=='UNKNOWN' for d in missing))

    def test_new_start_explains_saved_null_but_market_stays_open(self):
        for code,when in [('1101','2025-08-13'),('2884','2025-11-05')]:
            self.assertIn(when,self.calendar['sessions'])
            d=core.quote_diagnostic(self.catalog,code,when,None,True)
            self.assertEqual(d['new_missing_explanation'],'DIRECT_OFFICIAL_SUSPENSION_START_ON_DATE')
            self.assertEqual(d['parent_diagnostic']['new_missing_explanation'],'UNKNOWN')
            self.assertTrue(d['market_session']);self.assertFalse(d['security_tradable'])

    def test_no_price_imputation_valuation_or_execution_eligibility(self):
        d=core.quote_diagnostic(self.catalog,'1101','2025-08-13',None,True)
        for k in ['raw_close','imputed_close','valuation','suspension_end_date']:self.assertIsNone(d[k])
        self.assertFalse(d['execution_qualified']);self.assertTrue(d['missing_quote_blocks_accounting'])

    def test_start_not_extended_to_prior_later_or_other_stock(self):
        for code,when in [('1101','2025-08-12'),('1101','2025-08-14'),('2884','2025-08-13'),('2884','2025-11-06')]:
            d=core.quote_diagnostic(self.catalog,code,when,None,True)
            self.assertEqual(d['direct_suspension_start_observation_ids'],[])
            self.assertEqual(d['new_missing_explanation'],'UNKNOWN')

    def test_resumption_remains_separate_not_inferred_end(self):
        a=core.quote_diagnostic(self.catalog,'1101','2025-08-13',None,True)
        b=core.quote_diagnostic(self.catalog,'2884','2025-11-05',None,True)
        self.assertEqual(a['related_resumption_notices'][0]['resume_date'],'2025-08-14')
        self.assertEqual(b['related_resumption_notices'],[])
        self.assertIsNone(a['suspension_end_date']);self.assertIsNone(b['suspension_end_date'])

    def test_document_date_cannot_be_used_as_start_or_announced(self):
        o=self.suspension()
        for role in ['SOURCE_DOCUMENT_DATE_NOT_PUBLICATION','ACTUAL_ANNOUNCED_AT','SUSPENSION_END_NOT_AUTHENTICATED']:
            with self.assertRaises(ValueError):core.resolve(self.catalog,'suspension_start_date',request(o,'suspension_start_date',date_role=role))

    def test_request_wrong_issuer_instrument_or_unknown_end_refused(self):
        o=self.suspension()
        for changes in [dict(issuer_code='2884'),dict(old_instrument='1101_PREFERRED_SHARES'),dict(unit='TWD')]:
            with self.assertRaises(ValueError):core.resolve(self.catalog,'suspension_start_date',request(o,'suspension_start_date',**changes))
        with self.assertRaises(ValueError):core.resolve(self.catalog,'suspension_end_date',request(o,'suspension_end_date'))

    def test_rehashed_end_or_role_mutation_still_refused(self):
        for field,key,value in [('suspension_end_date','value','2025-08-14'),('suspension_start_date','date_role','EX_TRADING_DATE')]:
            c=deepcopy(self.catalog);o=c['observations'][0];o['fields'][field][key]=value;c['observations'][0]=identify(o)
            with self.assertRaises(ValueError):core.validate(identify(c))

    def test_original_capture_and_new_ingestion_kept_separate(self):
        o=self.suspension();s=self.catalog['sources'][o['source_ids'][0]]
        self.assertEqual(s['captured_at'],'2026-10-23T03:06:59.401522+00:00')
        self.assertLess(datetime.fromisoformat(s['captured_at']),datetime.fromisoformat(s['ingested_at']))
        self.assertEqual(o['observed_at'],s['ingested_at']);self.assertIsNone(o['announced_at'])
        before=(datetime.fromisoformat(o['observed_at'])-timedelta(seconds=1)).isoformat()
        with self.assertRaises(ValueError):core.resolve(self.catalog,'suspension_start_date',request(o,'suspension_start_date',observed_as_of=before))

    def test_historical_signal_and_final_ledger_usage_refused(self):
        o=self.suspension()
        for changes in [dict(historical_signal=True),dict(purpose='FINAL_LEDGER'),dict(version_id='latest')]:
            with self.assertRaises(ValueError):core.resolve(self.catalog,'suspension_start_date',request(o,'suspension_start_date',**changes))

    def test_true_archived_api_and_official_page_script_query_chain(self):
        p=source.validate_tax_chain(self.members)
        self.assertEqual(p['TaxVer'],'一一四年版');self.assertEqual(p['Title'],core.TAX_TITLE)
        self.assertEqual(p['Content_sha256'],source.CONTENT_SHA)
        self.assertIn('財政部101/08/17台財稅字第10100097670號令',p['Content'])

    def test_page_taxsn_and_linked_script_mismatch_rejected(self):
        for name,old,new in [('mof-tax-rule-143802','value="143802"','value="143803"'),
                ('mof-tax-page-script','TaxSN: id','TaxSN: 143803'),('mof-tax-site-script',"type: 'POST'","type: 'GET'")]:
            m=dict(self.members);n='archived_work/'+name+'.response';m[n]=m[n].replace(old.encode(),new.encode())
            with self.assertRaises(ValueError):source.validate_tax_chain(m)

    def test_api_query_function_or_taxsn_meta_mismatch_rejected(self):
        sid='mof-tax-api-143802';prefix='archived_work/'+sid;m=json.loads(self.members[prefix+'.meta.json'])
        for k,v in [('FunctionID','FB12002'),('ObjParams[TaxSN]','143803')]:
            bad=deepcopy(m);bad['form'][k]=v
            with self.assertRaises(ValueError):source.validate_original(sid,self.members[prefix+'.response'],bad,self.entries[prefix+'.response'])

    def test_actual_api_wrong_taxver_title_content_or_context_refused(self):
        for key,value in [('TaxVer','一一三年版'),('Title','別的函釋'),('Content','101/08/17台財稅字第10100097670號令'),
                ('Article','第十五條'),('Terms',2),('Subsection',52),('TaxAct','其他稅法')]:
            p=deepcopy(self.api);p['Data']['Table'][0][key]=value
            with self.assertRaises(ValueError):core.parse_mof_api(p,source.CONTENT_SHA)

    def test_api_unsuccessful_duplicate_or_missing_rows_refused(self):
        for change in ['failed','duplicate','empty']:
            p=deepcopy(self.api)
            if change=='failed':p['Code']='0'
            elif change=='duplicate':p['Data']['Table']*=2
            else:p['Data']['Table']=[]
            with self.assertRaises(ValueError):core.parse_mof_api(p,source.CONTENT_SHA)

    def test_viewcount_change_semantics_equal_raw_archive_sha_preserved(self):
        before=core.parse_mof_api(self.api,source.CONTENT_SHA);p=deepcopy(self.api);p['Data']['Table'][0]['ViewCount']+=1
        self.assertEqual(before,core.parse_mof_api(p,source.CONTENT_SHA))
        self.assertEqual(hashlib.sha256(self.members['archived_work/mof-tax-api-143802.response']).hexdigest(),
            '0616b330ca5fbd08d692546e5ce0c0f9f4d6bdeeb99ca5b6691d70b4b44b65b3')

    def test_real_api_not_rewritten_to_fit_old_synthetic_parser(self):
        with self.assertRaises(ValueError):old_tax_parser(self.api)
        self.assertEqual(core.parse_mof_api(self.api,source.CONTENT_SHA)['TaxVer'],'一一四年版')

    def test_general_law_does_not_assign_issuer_or_personal_net(self):
        o=next(x for x in self.catalog['observations'] if x['action_type']=='GENERAL_TAX_INTERPRETATION')
        self.assertEqual(o['issuer_code'],'GENERAL')
        for name in ['issuer_funding_subtype','personal_tax_residency','personal_tax','nhi','fees','personal_net_cash','actual_investor_receipt']:
            self.assertIsNone(o['fields'][name]['value'])
            with self.assertRaises(ValueError):core.resolve(self.catalog,name,request(o,name))

    def test_rehashed_personal_tax_zero_not_allowed(self):
        c=deepcopy(self.catalog);o=c['observations'][-1];o['fields']['personal_tax']['value']='0';c['observations'][-1]=identify(o)
        with self.assertRaises(ValueError):core.validate(identify(c))

    def test_source_complete_flags_do_not_cover_evidence_gaps(self):
        d=self.data()
        for c in d['coverage'].values():c['status']='VERIFIED_COMPLETE'
        r=core.qualify(d,self.catalog)
        self.assertTrue(any(x.startswith('SOURCE_ACTION_COVERAGE_INCOMPLETE:') for x in r['refusal_reasons']))
        self.assertTrue(any('OPENING' in x for x in r['refusal_reasons']))
        self.assertTrue(any('NET' in x for x in r['refusal_reasons']))
        self.assertEqual(r['daily'],[]);self.assertIsNone(r['total_net_return'])

    def test_catalog_coverage_promotion_refused(self):
        c=deepcopy(self.catalog);c['coverage']['1101']['status']='VERIFIED_COMPLETE'
        with self.assertRaises(ValueError):core.validate(identify(c))

    def test_parent_qualification_preserved_and_numeric_replay_not_called(self):
        d=self.data();before=deepcopy(d)
        with patch('rotation_research.action_ledger.replay',side_effect=AssertionError('No replay allowed')):r=core.qualify(d,self.catalog)
        self.assertEqual(d,before);self.assertEqual(r['daily'],[]);self.assertEqual(r['journal'],[])
        self.assertEqual(r['bridge_parent_qualification']['refusal_reasons'],r['refusal_reasons'])
        self.assertIn('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED',r['refusal_reasons'])

    def test_input_catalog_binding_required(self):
        d=self.data();d['bridge_catalog_id']='latest'
        with self.assertRaises(ValueError):core.qualify(d,self.catalog)

    def test_research_qualification_and_predecessor_attestation_limits(self):
        self.assertFalse(self.catalog['historical_signal_eligible']);self.assertFalse(self.catalog['policy_authorized'])
        self.assertIsNone(self.catalog['primary_pressure_id'])
        self.assertEqual(self.catalog['archive_verification']['manifest_entries_verified'],40)
        self.assertIn('NOT_INCLUDED_OR_REVERIFIED',self.catalog['archive_verification']['original_91_member_archive'])


if __name__=='__main__':unittest.main()
