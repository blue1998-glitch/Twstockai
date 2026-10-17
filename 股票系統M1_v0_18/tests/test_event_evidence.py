"""Real captured source fixtures plus altered-source rejection checks."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from contracts import DataError
from event_evidence import parse_tpex_reviewed_closure,parse_tcc_dividend,parse_esun_dividend,stage_cash_factor
RAW=ROOT/'event_audit/raw'

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.news=json.loads((RAW/'tpex_press_20260709.json').read_text())
        self.tcc=(RAW/'tcc_dividends.html').read_text()
        self.esun=(RAW/'esun_shareholders.html').read_text()
        self.candles=json.loads((ROOT/'data_audit/1101_candles.json').read_text())
    def test_primary_tpex_case_has_own_market(self):
        r=parse_tpex_reviewed_closure(self.news)
        self.assertEqual((r['exchange'],r['date'],r['announced_at_date']),('TPEX','2026-07-10','2026-07-09'))
    def test_wrong_query_period_rejected(self):
        self.news['date']='20250709~20250710'
        with self.assertRaises(DataError):parse_tpex_reviewed_closure(self.news)
    def test_partial_page_rejected(self):
        self.news['tables'][0]['totalCount']=3
        with self.assertRaises(DataError):parse_tpex_reviewed_closure(self.news)
    def test_wrong_announcement_year_rejected(self):
        self.news['tables'][0]['data'][0][0]='民國114年07月09日'
        with self.assertRaises(DataError):parse_tpex_reviewed_closure(self.news)
    def test_changed_closure_scope_rejected(self):
        self.news['tables'][0]['data'][0][1]='僅債券市場休市一日'
        with self.assertRaises(DataError):parse_tpex_reviewed_closure(self.news)
    def test_duplicate_reviewed_case_rejected(self):
        t=self.news['tables'][0];t['data'].append(t['data'][0]);t['totalCount']=3
        with self.assertRaises(DataError):parse_tpex_reviewed_closure(self.news)
    def test_tcc_actual_dates_and_amount(self):
        f=parse_tcc_dividend(self.tcc)
        self.assertEqual((f['cash_per_share'],f['effective_date'],f['payment_date']),('0.8','2026-07-01','2026-07-28'))
    def test_changed_tcc_date_header_rejected(self):
        with self.assertRaises(DataError):parse_tcc_dividend(self.tcc.replace('除息交易日','除息基準日'))
    def test_missing_target_year_rejected(self):
        with self.assertRaises(DataError):parse_tcc_dividend(self.tcc,2099)
    def test_esun_record_date_never_becomes_ex_date(self):
        f=parse_esun_dividend(self.esun)
        self.assertEqual(f['record_date'],'2026-07-07');self.assertIsNone(f['effective_date'])
        self.assertIsNone(f['stock_dividend_per_share']);self.assertEqual(f['cash_per_share'],'1.4')
        r=stage_cash_factor(f,self.candles)
        self.assertIsNone(r['diagnostic_factor']);self.assertEqual(r['blocked_reasons'],['EX_TRADING_DATE_NOT_VERIFIED'])
    def test_record_date_kind_blocks_even_when_date_accidentally_filled(self):
        f=parse_esun_dividend(self.esun);f.update(effective_date=f['record_date'],effective_date_kind='RECORD_DATE')
        self.assertIsNone(stage_cash_factor(f,self.candles)['diagnostic_factor'])
    def test_changed_esun_headers_rejected(self):
        with self.assertRaises(DataError):parse_esun_dividend(self.esun.replace('除息基準日','除息交易日'))
    def test_diagnostic_factor_requires_reference_before_forwarding(self):
        f=parse_tcc_dividend(self.tcc);r=stage_cash_factor(f,self.candles)
        self.assertEqual(r['basis']['date'],'2026-06-30')
        self.assertEqual(r['basis']['close'],'24.05')
        self.assertEqual(r['diagnostic_factor'],'0.9667359667359667359667359667')
        self.assertEqual(r['approved_engine_events'],[])
        self.assertEqual(r['period_action_coverage'],'UNVERIFIED')
    def test_stock_dividend_blocks_cash_only_formula(self):
        f=parse_tcc_dividend(self.tcc);f['stock_dividend_per_share']='0.1'
        self.assertEqual(stage_cash_factor(f,self.candles)['blocked_reasons'],['CASH_ONLY_EVENT_NOT_ESTABLISHED'])
    def test_missing_price_basis_not_inferred(self):
        f=parse_tcc_dividend(self.tcc);f['effective_date']='2026-07-04'
        self.assertEqual(stage_cash_factor(f,self.candles)['blocked_reasons'],['PRICE_BASIS_NOT_AVAILABLE'])
    def test_impossible_cash_factor_not_computed(self):
        f=parse_tcc_dividend(self.tcc);f['cash_per_share']='999'
        self.assertIsNone(stage_cash_factor(f,self.candles)['diagnostic_factor'])
    def test_duplicate_candle_date_rejected(self):
        with self.assertRaises(DataError):stage_cash_factor(parse_tcc_dividend(self.tcc),[self.candles[0]]*2)
    def test_staging_does_not_mutate_inputs(self):
        f=parse_tcc_dividend(self.tcc);before=copy.deepcopy((f,self.candles))
        stage_cash_factor(f,self.candles);self.assertEqual((f,self.candles),before)

if __name__=='__main__':unittest.main()
