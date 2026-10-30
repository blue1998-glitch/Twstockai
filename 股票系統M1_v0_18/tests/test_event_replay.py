"""Behavioral replay integration and evidence-kind rejection tests."""
from copy import deepcopy
from datetime import date,timedelta
from decimal import Decimal
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from contracts import DataError
from event_replay import run_event_replay,make_replay_jobs,compare_replay_results,parse_contract_notice


def fixture():
    # Explicit synthetic engine fixture; no market, issuer or strategy claim.
    candles=[];day=date(2026,1,1)
    for i in range(90):
        close=Decimal(100+min(i%32,32-i%32));scale=Decimal('0.9') if i>=50 else Decimal(1)
        candles.append(dict(date=(day+timedelta(days=i)).isoformat(),open=str(close*scale),close=str(close*scale),
                            high=str((close+2)*scale),low=str((close-2)*scale),volume_shares_scaled=None if i==48 else str(100+i)))
    prev=Decimal(candles[49]['close']);cash=prev/10
    e=dict(code='SYNTHETIC',effective_date=candles[50]['date'],factor='0.9',cash_dividend=str(cash),previous_close=str(prev),
           formula='(previous_close-cash_dividend)/previous_close',source_sha256='a'*64)
    job=dict(schema_version='stock-analysis/1.0',code='SYNTHETIC',exchange='TWSE',timeframe='daily',price_mode='RAW_CANDIDATE',
             source=dict(id='synthetic-fixture-only',code='SYNTHETIC',exchange='TWSE',volume_unit='SHARES_REPORTED'),
             candles=candles,corporate_actions=dict(records=[],coverage_status='UNVERIFIED'))
    return job,[e]

class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.job,cls.events=fixture();cls.bundle=run_event_replay(cls.job,cls.events)
    def test_real_engine_fixture_comparison_passes_without_trading_upgrade(self):
        r=self.bundle['report'];self.assertEqual(r['status'],'PASS');self.assertEqual(r['trading_qualification'],'NOT_EVALUATED')
        self.assertEqual(r['period_action_coverage'],'UNVERIFIED')
    def test_cancellation_and_zone_checks_are_not_vacuous(self):
        b=self.bundle['report']['boundaries'][0]
        self.assertGreater(b['cancelled_candidates'],0);self.assertGreater(b['deactivated_active_zones'],0)
        self.assertEqual(b['warmup_bars_checked'],19)
    def test_future_price_removal_and_future_event_removal_preserve_snapshots(self):
        checks=[x for x in self.bundle['report']['checks'] if x['check']=='truncated_prices_and_removed_future_events_preserve_stored_snapshots']
        self.assertEqual(len(checks),2);self.assertTrue(all(x['status']=='PASS' and x['snapshots']==50 for x in checks))
    def test_later_event_does_not_rewrite_snapshots_after_first_event(self):
        job,events=fixture();prev=Decimal(job['candles'][74]['close'])
        second=deepcopy(events[0]);second.update(effective_date=job['candles'][75]['date'],previous_close=str(prev),cash_dividend=str(prev*Decimal('0.05')),factor='0.95')
        bundle=run_event_replay(job,events+[second]);self.assertEqual(bundle['report']['status'],'PASS')
        later=[c for c in bundle['report']['checks'] if c.get('before_event')==second['effective_date']]
        self.assertEqual(len(later),2);self.assertTrue(all(c['snapshots']==75 and c['status']=='PASS' for c in later))
    def test_prepared_scenarios_do_not_mutate_original(self):
        job,events=fixture();before=deepcopy((job,events));jobs=make_replay_jobs(job,events)
        self.assertEqual((job,events),before);self.assertEqual(jobs['RAW_WITHOUT_EVENTS']['corporate_actions']['records'],[])
        jobs['RAW_WITH_EVENTS']['candles'][0]['close']='1';self.assertEqual((job,events),before)
    def test_mismatched_price_basis_blocked(self):
        e=deepcopy(self.events);e[0]['previous_close']='999'
        with self.assertRaises(DataError):make_replay_jobs(self.job,e)
    def test_wrong_stock_event_blocked(self):
        e=deepcopy(self.events);e[0]['code']='ANOTHER'
        with self.assertRaises(DataError):make_replay_jobs(self.job,e)
    def test_unreviewed_empty_event_set_not_called_pass(self):
        with self.assertRaises(DataError):make_replay_jobs(self.job,[])
    def test_mismatched_factor_blocked(self):
        e=deepcopy(self.events);e[0]['factor']='0.8'
        with self.assertRaises(DataError):make_replay_jobs(self.job,e)
    def test_missing_recorded_provenance_blocked(self):
        e=deepcopy(self.events);e[0].pop('source_sha256')
        with self.assertRaises(DataError):make_replay_jobs(self.job,e)
    def test_corrupt_raw_ma_is_detected(self):
        r=deepcopy(self.bundle['results']);r['RAW_WITH_EVENTS']['components']['daily_ma']['snapshots'][-1]['curves']['5'][-1]='0'
        out=compare_replay_results(self.job,self.events,r)
        self.assertEqual(out['status'],'FAIL');self.assertTrue(any(c['check']=='raw_ma_values_unchanged_by_events' and c['status']=='FAIL' for c in out['checks']))
    def test_missing_raw_boundary_is_detected(self):
        r=deepcopy(self.bundle['results']);s=r['RAW_WITH_EVENTS']['components']['structure']['snapshots'][50]
        s['daily_events']=[x for x in s['daily_events'] if x['type']!='RAW_CORPORATE_ACTION_BOUNDARY']
        self.assertEqual(compare_replay_results(self.job,self.events,r)['status'],'FAIL')
    def test_tampered_adjusted_anchor_is_detected(self):
        r=deepcopy(self.bundle['results']);r['ADJUSTED_WITH_EVENTS']['components']['daily_ma']['snapshots'][50]['curves']['5'][-1]='999'
        self.assertEqual(compare_replay_results(self.job,self.events,r)['status'],'FAIL')

class ContractNoticeTests(unittest.TestCase):
    def text(self,code):return (ROOT/'event_replay/raw'/f'taifex_{code}_20260701.txt').read_text()
    def test_2884_contract_date_is_not_stock_ex_date(self):
        f=parse_contract_notice(self.text('2884'),code='2884')
        self.assertEqual((f['cash_per_share'],f['contract_adjustment_date']),('1.4','2026-07-01'))
        self.assertEqual(f['document_date'],'2026-06-15');self.assertIsNone(f['stock_ex_trading_date']);self.assertIsNone(f['stock_reference_price'])
    def test_1101_cash_and_document_date(self):
        f=parse_contract_notice(self.text('1101'),code='1101')
        self.assertEqual((f['cash_per_share'],f['document_date'],f['document_number']),('0.8','2026-06-22','1150201165'))
    def test_wrong_issuer_rejected(self):
        with self.assertRaises(DataError):parse_contract_notice(self.text('2884'),code='1101')
    def test_missing_contract_effective_date_rejected(self):
        with self.assertRaises(DataError):parse_contract_notice(self.text('2884').replace('調整生效日','調整說明'),code='2884')

if __name__=='__main__':unittest.main()
