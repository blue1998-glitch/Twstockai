import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from source_audit import *
from analysis_jobs import run_analysis_job


class SourceAuditTests(unittest.TestCase):
    def test_http_success_does_not_hide_wrong_calendar_year(self):
        p=json.loads((ROOT/'data_audit/raw/twse_holiday_2025_rwd.json').read_text())
        with self.assertRaises(DataError) as e:parse_twse_holidays(p,2025)
        self.assertEqual(e.exception.code,'SOURCE_YEAR_MISMATCH')

    def test_tpex_stock_calendar_excludes_bond_only_closures_and_handles_rowspans(self):
        p=json.loads((ROOT/'data_audit/raw/tpex_holiday_2026.json').read_text());s=parse_tpex_holidays(p,2026)
        self.assertNotIn('2026-02-11',s['closed_dates'])
        self.assertIn('2026-02-12',s['closed_dates']);self.assertIn('2026-02-13',s['closed_dates'])
        for dt in ['2026-02-27','2026-02-28','2026-04-06','2026-10-26']:self.assertIn(dt,s['closed_dates'])

    def test_official_2026_schedules_agree_for_equities(self):
        tpex=parse_tpex_holidays(json.loads((ROOT/'data_audit/raw/tpex_holiday_2026.json').read_text()),2026)
        twse=parse_twse_holidays(json.loads((ROOT/'data_audit/raw/twse_holiday_2026_date.json').read_text()),2026)
        self.assertEqual(tpex['closed_dates'],twse['closed_dates'])

    def test_native_shares_are_not_scaled_again(self):
        p=json.loads((ROOT/'data_audit/raw/1101_202601.json').read_text());rows=parse_twse_month(p,code='1101',year=2026,month=1)
        self.assertEqual(rows[0]['volume_shares_scaled'],'29722691')
        self.assertEqual(rows[0]['date'],'2026-01-02');self.assertEqual(rows[0]['close'],'23.00')

    def test_wrong_stock_month_fields_or_incomplete_rows_are_rejected(self):
        p=json.loads((ROOT/'data_audit/raw/1101_202601.json').read_text())
        with self.assertRaises(DataError):parse_twse_month(p,code='2884',year=2026,month=1)
        with self.assertRaises(DataError):parse_twse_month(p,code='1101',year=2026,month=2)
        bad=copy.deepcopy(p);bad['fields'][1]='成交張數'
        with self.assertRaises(DataError):parse_twse_month(bad,code='1101',year=2026,month=1)
        bad=copy.deepcopy(p);bad['data'][0]=bad['data'][0][:-1]
        with self.assertRaises(DataError):parse_twse_month(bad,code='1101',year=2026,month=1)

    def test_missing_price_is_not_zero_or_silently_skipped(self):
        p=json.loads((ROOT/'data_audit/raw/1101_202601.json').read_text());p['data'][0][p['fields'].index('收盤價')]='--'
        with self.assertRaises(DataError):parse_twse_month(p,code='1101',year=2026,month=1)

    def test_planned_calendar_requires_year_coverage(self):
        s=dict(year=2026,closed_dates=['2026-01-01'])
        with self.assertRaises(DataError):planned_dates([s],'2025-12-31','2026-01-02')
        self.assertEqual(planned_dates([s],'2026-01-01','2026-01-04'),['2026-01-02'])

    def test_closure_evidence_cannot_be_borrowed_across_exchanges(self):
        item=dict(date='2026-07-10',exchange='TWSE',verification='OFFICIAL_PRIMARY_TEXT_RETRIEVED',source_url='https://www.twse.com.tw/example')
        self.assertEqual(apply_evidenced_closures(['2026-07-10'],[item],exchange='TWSE')['dates'],[])
        self.assertEqual(apply_evidenced_closures(['2026-07-10'],[item],exchange='TPEX')['dates'],['2026-07-10'])
        item['verification']='UNVERIFIED'
        with self.assertRaises(DataError):apply_evidenced_closures(['2026-07-10'],[item],exchange='TWSE')

    def test_unexplained_gap_is_not_automatically_called_bad_market_data(self):
        rows=[dict(date='2026-07-09',open='10',high='10',low='10',close='10')]
        r=compare_dates(rows,['2026-07-09','2026-07-10'])
        self.assertEqual(r['status'],'DIFFERENCES_REQUIRE_EVIDENCE');self.assertEqual(r['missing_dates'],['2026-07-10'])

    def test_native_share_job_runs_and_260_day_ma_remains_unavailable(self):
        j=json.loads((ROOT/'data_audit/1101_analysis_job.json').read_text());j['candles']=j['candles'][:5];j.pop('expected_dates')
        r=run_analysis_job(j);self.assertEqual(r['shared_input']['source']['volume_unit'],'SHARES_REPORTED')
        self.assertIsNone(r['components']['daily_ma']['snapshots'][-1]['curves']['260'][-1])

    def test_new_real_samples_have_179_aligned_rows_without_adjusted_claims(self):
        for code in ['1101','2884']:
            r=json.loads((ROOT/f'data_audit/output/{code}_RAW_ANALYSIS.json').read_text())
            self.assertEqual(len(r['aligned_snapshots']),179)
            self.assertEqual(r['shared_input']['corporate_action_coverage'],'UNVERIFIED')
            self.assertEqual(r['shared_input']['price_mode'],'RAW_CANDIDATE')
            self.assertIsNone(r['components']['daily_ma']['snapshots'][-1]['curves']['260'][-1])
            self.assertEqual(r['action_qualification'],'NOT_EVALUATED')


if __name__=='__main__':unittest.main()
