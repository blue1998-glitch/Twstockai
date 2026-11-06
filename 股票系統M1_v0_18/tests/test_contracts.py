import copy
import sys
import unittest
from datetime import date,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from contracts import DataError,quality,validate_candles,validate_events,validate_output,SCHEMA_VERSION
from structure import analyze,Config
from jobs import run_job


def sample(n=22,flat=False):
    return [dict(date=(date(2026,1,1)+timedelta(days=i)).isoformat(),open='100',high='100' if flat else '101',low='100' if flat else '99',close='100',volume_shares_scaled='1000') for i in range(n)]


def job():
    return dict(schema_version=SCHEMA_VERSION,code='T',exchange='TPEX',price_mode='RAW_CANDIDATE',timeframe='daily',
                source=dict(id='fixture',code='T',exchange='TPEX',volume_unit='SHARES_SCALED_FROM_LOTS'),
                candles=sample(3),corporate_actions=dict(records=[],coverage_status='UNVERIFIED'))


class ContractsTests(unittest.TestCase):
    def test_missing_field_and_null_are_distinct(self):
        cs=sample(1);del cs[0]['close']
        with self.assertRaises(DataError) as e:validate_candles(cs)
        self.assertEqual(e.exception.code,'MISSING_FIELD')
        cs=sample(1);cs[0]['close']=None
        with self.assertRaises(DataError) as e:validate_candles(cs)
        self.assertEqual(e.exception.code,'MISSING_VALUE')

    def test_nonfinite_and_boolean_rejected(self):
        for v in ['NaN','Infinity',float('nan'),True,'broken']:
            cs=sample(1);cs[0]['close']=v
            with self.assertRaises(DataError):validate_candles(cs)

    def test_duplicate_out_of_order_and_invalid_date(self):
        cs=sample(3)
        for bad,code in [(cs+[cs[-1]],'DUPLICATE_DATE'),(cs[::-1],'OUT_OF_ORDER_DATE')]:
            with self.assertRaises(DataError) as e:validate_candles(bad)
            self.assertEqual(e.exception.code,code)
        cs[0]['date']='2026-02-30'
        with self.assertRaises(DataError):validate_candles(cs)

    def test_missing_volume_is_not_zero_volume(self):
        cs=sample(2);cs[0]['volume_shares_scaled']=None
        self.assertEqual(quality(cs)['volume_context'],'PARTIAL')
        cs[0]['volume_shares_scaled']='0'
        self.assertEqual(quality(cs)['volume_context'],'AVAILABLE_SOURCE_PRECISION')
        cs[0]['volume_shares_scaled']='-1'
        with self.assertRaises(DataError):quality(cs)

    def test_empty_warmup_zero_volatility_and_no_event(self):
        empty=analyze([],code='T',mode='RAW_CANDIDATE',source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
        self.assertEqual(empty['data_quality']['status'],'EMPTY_INPUT')
        a=analyze(sample(),code='T',mode='RAW_CANDIDATE',source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
        self.assertEqual(a['snapshots'][0]['event_status'],'WARMUP')
        self.assertEqual(a['snapshots'][-1]['event_status'],'NO_NEW_EVENTS')
        flat=analyze(sample(flat=True),code='T',mode='RAW_CANDIDATE',source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
        self.assertEqual(flat['snapshots'][-1]['event_status'],'ZERO_VOLATILITY')
        self.assertEqual(flat['snapshots'][-1]['evidence_sufficiency'],'ZERO_VOLATILITY')

    def test_causal_fingerprints_and_parameter_identity(self):
        cs=sample();a=analyze(cs,code='T',mode='RAW_CANDIDATE',source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
        b=copy.deepcopy(cs);b[-1].update(open='110',high='110',low='110',close='110')
        changed=analyze(b,code='T',mode='RAW_CANDIDATE',source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
        self.assertNotEqual(a['data_fingerprint'],changed['data_fingerprint'])
        self.assertEqual(a['snapshots'][:-1],changed['snapshots'][:-1])
        different=analyze(cs,code='T',mode='RAW_CANDIDATE',source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS',cfg=Config(minor_multiple='1.6'))
        self.assertNotEqual(a['parameters_fingerprint'],different['parameters_fingerprint'])

    def test_events_invalid_duplicate_and_unknown_mode(self):
        for es in [[dict(effective_date='bad',factor='0.9')],[dict(effective_date='2026-01-01',factor='0')],[dict(effective_date='2026-01-01',factor='0.9')]*2]:
            with self.assertRaises(DataError):validate_events(es)
        with self.assertRaises(DataError):analyze(sample(),code='T',mode='UNKNOWN',source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')

    def test_calendar_is_explicit_and_gaps_are_not_filled(self):
        cs=sample(3);self.assertEqual(quality(cs)['calendar_status'],'UNVERIFIED')
        expected=[x['date'] for x in cs];self.assertEqual(quality(cs,expected_dates=expected)['calendar_status'],'MATCHES_SUPPLIED_CALENDAR')
        missing=quality(cs[:2],expected_dates=expected)
        self.assertEqual(missing['missing_dates'],[cs[2]['date']]);self.assertEqual(len(cs[:2]),2)

    def test_job_stock_and_unit_mismatch(self):
        self.assertEqual(run_job(job())['source']['id'],'fixture')
        for field,value in [('code','OTHER'),('volume_unit','LOTS')]:
            j=job();j['source'][field]=value
            with self.assertRaises(DataError):run_job(j)

    def test_output_future_or_trading_qualification_rejected(self):
        a=analyze(sample(3),code='T',mode='RAW_CANDIDATE',source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
        a['snapshots'][0]['action_qualification']='BUY'
        with self.assertRaises(DataError):validate_output(a)
        a['snapshots'][0]['action_qualification']='NOT_EVALUATED';a['schema_version']='bad'
        with self.assertRaises(DataError):validate_output(a)

    def test_invalid_integer_configuration(self):
        for c in [Config(window=True),Config(minor_bars=1.5)]:
            with self.assertRaises(ValueError):c.validate()


if __name__=='__main__':unittest.main()
