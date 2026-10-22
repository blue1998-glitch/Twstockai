"""Offline tests of actual official reports and qualification, never synthetic prices."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from . import source_capture as collector
from . import source_qualification as producer
from .action_sources import HERE
from .action_study import verified_quotes,candidate_input
from .action_ledger import replay


class OfficialSourceQualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports={m:producer.load_capture('market-'+m) for m in producer.months(producer.START,producer.END)}
        cls.calendar=producer.calendar_from_reports(cls.reports,producer.START,producer.END)
        cls.old,cls.manifest=verified_quotes()
        cls.catalog=json.loads((HERE/'action_data_20261022/events.json').read_text())

    def test_actual_sessions_exactly_match_both_saved_sources(self):
        self.assertEqual(self.calendar['calendar_days'],473);self.assertEqual(self.calendar['trading_dates'],317)
        for asset in self.old['assets'].values():self.assertEqual(set(self.calendar['sessions']),{b['date'] for b in asset['bars']})

    def test_security_no_quote_days_are_market_open_not_holidays(self):
        for d in ('2025-08-13','2025-11-05'):self.assertIn(d,self.calendar['sessions'])
        self.assertNotIn('2026-07-10',self.calendar['sessions'])
        self.assertNotIn('2026-07-11',self.calendar['sessions'])
        self.assertEqual(self.calendar['settlement_calendar'],'NOT_VERIFIED_NOT_INFERRED_T_PLUS_2')

    def test_every_day_binds_official_month_and_open_row(self):
        for r in self.calendar['calendar']:
            self.assertTrue(all(s in self.calendar['sources'] for s in r['source_ids']))
            if r['trading']:
                ref=self.calendar['sessions'][r['date']];key=ref['source_id'].removeprefix('market-')
                idx=int(ref['locator'].split('[')[1].split(']')[0])
                self.assertEqual(self.reports[key][0]['data'][idx][0],ref['raw_date'])

    def test_missing_month_never_implies_closed_dates(self):
        reports=deepcopy(self.reports);reports.pop('202608')
        with self.assertRaisesRegex(ValueError,'month reports'):producer.calendar_from_reports(reports,producer.START,producer.END)

    def test_wrong_status_month_or_empty_report_rejected(self):
        for key,value in [('stat','NO_DATA'),('date','20250801'),('data',[])]:
            with self.subTest(key=key):
                reports=deepcopy(self.reports);reports['202507'][0][key]=value
                with self.assertRaises(ValueError):producer.calendar_from_reports(reports,producer.START,producer.END)

    def test_invalid_duplicate_out_of_month_and_totals_rejected(self):
        for fault in ('duplicate','out-of-month','totals'):
            with self.subTest(fault=fault):
                reports=deepcopy(self.reports);r=reports['202507'][0]['data']
                if fault=='duplicate':r.append(deepcopy(r[-1]))
                if fault=='out-of-month':r[0][0]='114/08/01'
                if fault=='totals':r[0][1]='0'
                with self.assertRaises(ValueError):producer.calendar_from_reports(reports,producer.START,producer.END)

    def test_capture_same_day_or_earlier_does_not_certify_completed_window(self):
        reports=deepcopy(self.reports);reports['202610'][1]['captured_at']='2026-10-16T01:00:00+00:00'
        with self.assertRaisesRegex(ValueError,'after the completed'):producer.calendar_from_reports(reports,producer.START,producer.END)

    def test_future_rows_do_not_change_earlier_calendar_or_add_prices(self):
        reports=deepcopy(self.reports)
        for r in reports['202610'][0]['data']:
            if producer.iso(r[0],True)>producer.END:r[1:]=['0']*(len(r)-1)
        self.assertEqual(producer.calendar_from_reports(reports,producer.START,producer.END),self.calendar)
        self.assertTrue(all('close' not in r for r in self.calendar['calendar']))

    def test_calendar_binding_does_not_mutate_inputs_or_bypass_other_gates(self):
        inp=candidate_input(self.old,self.catalog,self.manifest,'2026-06-30','2026-07-29','1101');original=deepcopy(inp)
        bound=producer.bind_observed_calendar(inp,self.calendar);result=replay(bound)
        self.assertEqual(inp,original);self.assertEqual(bound['qualification']['calendar'],'VERIFIED_COMPLETE')
        self.assertNotIn('CALENDAR_NOT_VERIFIED_COMPLETE',result['refusal_reasons'])
        self.assertIn('ACTION_COVERAGE_INCOMPLETE:1101',result['refusal_reasons'])
        self.assertIn('OPENING_ENTITLEMENTS_UNKNOWN',result['refusal_reasons'])
        self.assertIn('NET_DISTRIBUTIONS_TAX_FEES_UNKNOWN',result['refusal_reasons'])
        self.assertEqual(result['daily'],[]);self.assertIsNone(result['total_net_return'])

    def test_calendar_extrapolation_and_tampering_rejected(self):
        inp=candidate_input(self.old,self.catalog,self.manifest,'2026-06-30','2026-07-29','1101')
        cal=deepcopy(self.calendar);cal['calendar'][0]['trading']=not cal['calendar'][0]['trading']
        with self.assertRaisesRegex(ValueError,'fingerprint'):producer.bind_observed_calendar(inp,cal)
        inp['end']='2026-10-17'
        with self.assertRaisesRegex(ValueError,'extrapolate'):producer.bind_observed_calendar(inp,self.calendar)

    def test_all_research_windows_still_refuse_total_net_return(self):
        audit=producer.window_audit(self.old,self.catalog,self.manifest,self.calendar)
        self.assertEqual(audit['calendar_qualified_windows'],70)
        self.assertEqual(audit['total_net_return_qualified_windows'],0)
        self.assertEqual(len(audit['windows']),72)
        self.assertEqual(sum(w['end'] is None for w in audit['windows']),2)
        self.assertIsNone(audit['ranking'])

    def test_action_notices_no_target_rows_are_not_no_action_proof(self):
        audit=producer.action_source_audit(self.catalog)
        self.assertFalse(audit['complete_corporate_action_coverage'])
        self.assertEqual(audit['event_components_unchanged'],self.catalog['events'])
        for r in audit['observations'][:2]:self.assertFalse(r['no_target_rows_proves_no_events']);self.assertEqual(r['target_rows'],[])
        self.assertEqual(audit['observations'][2]['capture']['status'],'FAILED')

    def test_failed_and_tampered_captures_cannot_be_empty_valid_data(self):
        with self.assertRaisesRegex(ValueError,'failed'):producer.load_capture('reduction-resumptions')
        with tempfile.TemporaryDirectory() as td:
            raw=Path(td)/'raw';raw.mkdir();(raw/'example.response').write_bytes(b'changed')
            meta=dict(status='CAPTURED',http=200,url='https://www.twse.com.tw/example',final_url='https://www.twse.com.tw/example',sha256='0'*64,bytes=7)
            (raw/'example.meta.json').write_text(json.dumps(meta))
            with patch.object(producer,'OUT',Path(td)),self.assertRaisesRegex(ValueError,'fingerprint'):producer.load_capture('example')

    def test_prohibited_and_unlisted_requests_never_reach_network(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('network attempted')):
            for url in ('https://www.twse.com.tw/rwd/zh/exRight/TWT49U','https://www.twse.com.tw/rwd/zh/exRight/twt49u','http://www.twse.com.tw/report','https://www.esunbank.com/file.pdf'):
                with self.assertRaises(ValueError):collector.capture('test',url)

    def test_cached_failure_not_retried_and_existing_body_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            raw=Path(td)/'raw';raw.mkdir();meta=dict(name='denied',url='https://www.twse.com.tw/test',status='FAILED',error='HTTP 307')
            (raw/'denied.meta.json').write_text(json.dumps(meta))
            with patch.object(collector,'OUT',Path(td)),patch('urllib.request.urlopen',side_effect=AssertionError('retry attempted')):
                self.assertEqual(collector.capture('denied',meta['url']),meta)


if __name__=='__main__':unittest.main()
