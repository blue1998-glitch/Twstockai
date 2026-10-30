"""Independent numeric oracles, chronology and data-quality boundaries."""
from copy import deepcopy
from datetime import date,timedelta
from decimal import Decimal,localcontext,ROUND_FLOOR,Inexact
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from contracts import DataError
from period_ma import analyze_period_ma


def candle(dt,close,volume='100'):
    n=int(close)
    return dict(date=dt,open=str(n-1),high=str(n+2),low=str(n-2),close=str(n),volume_shares_scaled=volume)


def weekdays(start,end):
    rows=[];dt=date.fromisoformat(start);last=date.fromisoformat(end)
    while dt<=last:
        if dt.weekday()<5:rows.append(candle(dt.isoformat(),100+len(rows)))
        dt+=timedelta(days=1)
    return rows


def analyze(rows,as_of,**kw):
    return analyze_period_ma(rows,kw.pop('events',[]),code='FIXTURE',exchange=kw.pop('exchange','TWSE'),mode=kw.pop('mode','RAW_CANDIDATE'),as_of=as_of,source_id='explicit-synthetic',volume_unit=kw.pop('volume_unit','SHARES_REPORTED'),**kw)


class PeriodMATests(unittest.TestCase):
    def test_monthly_ohlc_and_volume_use_actual_source_records(self):
        rows=weekdays('2026-01-01','2026-02-27');r=analyze(rows,'2026-02-28');jan=r['monthly']['bars'][0]
        part=[c for c in rows if c['date'].startswith('2026-01')]
        self.assertEqual((jan['open'],jan['high'],jan['low'],jan['close']),('99',str(100+len(part)-1+2),'98',str(100+len(part)-1)))
        self.assertEqual(jan['volume_shares'],str(len(part)*100));self.assertEqual(jan['daily_records'],len(part))
        self.assertEqual(jan['calendar_status'],'UNVERIFIED')

    def test_iso_week_crosses_year_without_splitting_at_january_first(self):
        r=analyze(weekdays('2020-12-28','2021-01-05'),'2021-01-05')
        self.assertEqual([b['period'] for b in r['weekly']['bars']],['2020-W53','2021-W01'])
        self.assertEqual(r['weekly']['bars'][0]['period_end'],'2021-01-03')
        self.assertEqual(r['weekly']['bars'][0]['daily_records'],5)

    def test_friday_is_still_open_calendar_week_sunday_eod_elapsed(self):
        rows=weekdays('2026-01-05','2026-01-09');a=analyze(rows,'2026-01-09');b=analyze(rows,'2026-01-11')
        self.assertEqual(a['weekly']['bars'][0]['calendar_state'],'OPEN_CALENDAR_PERIOD')
        self.assertEqual(a['weekly']['elapsed']['latest']['4']['reason'],'NO_ELAPSED_PERIODS')
        self.assertEqual(b['weekly']['bars'][0]['calendar_state'],'ELAPSED_CALENDAR_PERIOD')
        self.assertEqual(b['calendar_authentication'],'UNVERIFIED')

    def test_month_end_weekend_does_not_certify_market_calendar(self):
        rows=weekdays('2026-01-01','2026-01-30')
        self.assertEqual(analyze(rows,'2026-01-30')['monthly']['bars'][0]['calendar_state'],'OPEN_CALENDAR_PERIOD')
        r=analyze(rows,'2026-01-31');self.assertEqual(r['monthly']['bars'][0]['calendar_state'],'ELAPSED_CALENDAR_PERIOD')
        self.assertEqual(r['calendar_authentication'],'UNVERIFIED');self.assertEqual(r['last_price_date'],'2026-01-30')

    def test_four_week_sma_has_independent_hand_calculated_value(self):
        rows=weekdays('2026-01-05','2026-01-30');r=analyze(rows,'2026-02-01')
        self.assertEqual(r['weekly']['elapsed']['latest']['4']['value'],'111.5')
        self.assertEqual(r['weekly']['elapsed']['latest']['4']['window_periods'],['2026-W02','2026-W03','2026-W04','2026-W05'])

    def test_open_week_candidate_can_exist_without_four_elapsed_weeks(self):
        r=analyze(weekdays('2026-01-05','2026-01-30'),'2026-01-30')
        self.assertEqual(r['weekly']['candidate']['latest']['4']['value'],'111.5')
        self.assertEqual(r['weekly']['candidate']['latest']['4']['calendar_state'],'OPEN_CALENDAR_PERIOD')
        self.assertIsNone(r['weekly']['elapsed']['latest']['4']['value'])

    def test_three_month_sma_is_monthly_closes_not_twenty_daily_closes(self):
        rows=[candle('2026-01-01',10),candle('2026-02-01',20),candle('2026-03-01',30)]
        r=analyze(rows,'2026-03-31')
        self.assertEqual(r['monthly']['elapsed']['latest']['3']['value'],'20')
        self.assertEqual(r['monthly']['bars'][1]['daily_records'],1)
        self.assertEqual(r['data_quality']['calendar_status'],'UNVERIFIED')

    def test_long_synthetic_series_supports_all_windows_and_leap_february(self):
        rows=weekdays('2024-01-01','2026-02-27')
        for row in rows:row.update(open='99',high='102',low='98',close='100')
        r=analyze(rows,'2026-02-28')
        for scale in ['weekly','monthly']:
            for point in r[scale]['elapsed']['latest'].values():self.assertEqual(Decimal(point['value']),100)
        self.assertEqual(r['monthly']['bars'][1]['period_end'],'2024-02-29')
        self.assertEqual(r['monthly']['periods'],[3,6,12,24]);self.assertEqual(r['weekly']['periods'],[4,13,26,52])

    def test_uncertain_left_edge_is_not_counted_as_a_whole_week(self):
        rows=weekdays('2026-01-06','2026-01-30');r=analyze(rows,'2026-02-01')
        self.assertEqual(r['weekly']['bars'][0]['ma_block_reason'],'LEFT_EDGE_UNCERTAIN')
        self.assertIsNone(r['weekly']['elapsed']['latest']['4']['value'])
        self.assertEqual(len(r['weekly']['elapsed']['latest']['4']['window_periods']),3)

    def test_supplied_calendar_can_cover_holiday_at_start_without_authentication_upgrade(self):
        rows=weekdays('2026-01-02','2026-03-31')
        cal=dict(coverage_start='2026-01-01',coverage_end='2026-03-31',expected_dates=[c['date'] for c in rows])
        r=analyze(rows,'2026-03-31',calendar=cal)
        self.assertEqual(r['monthly']['bars'][0]['range_start_status'],'CALENDAR_COVERS_START')
        self.assertTrue(r['monthly']['elapsed']['latest']['3']['available'])
        self.assertEqual(r['calendar_authentication'],'SUPPLIED_UNVERIFIED')

    def test_missing_month_is_null_and_breaks_windows_without_forward_fill(self):
        rows=[candle('2026-01-01',10),candle('2026-03-01',30),candle('2026-04-01',40)]
        r=analyze(rows,'2026-04-30');gap=r['monthly']['bars'][1]
        self.assertIsNone(gap['close']);self.assertIsNone(gap['volume_shares']);self.assertFalse(gap['skip_supplied_no_trading_period'])
        self.assertIsNone(r['monthly']['elapsed']['latest']['3']['value'])
        rows.append(candle('2026-05-01',50));r=analyze(rows,'2026-05-31')
        self.assertEqual(r['monthly']['elapsed']['latest']['3']['value'],'40')

    def test_explicit_zero_trading_week_skipped_without_synthetic_price(self):
        all_rows=weekdays('2026-01-05','2026-02-06');rows=[c for c in all_rows if not '2026-01-12'<=c['date']<='2026-01-18']
        cal=dict(coverage_start='2026-01-05',coverage_end='2026-02-08',expected_dates=[c['date'] for c in rows])
        r=analyze(rows,'2026-02-08',calendar=cal);gap=r['weekly']['bars'][1]
        self.assertTrue(gap['skip_supplied_no_trading_period']);self.assertIsNone(gap['close'])
        self.assertTrue(r['weekly']['elapsed']['latest']['4']['available'])
        self.assertIsNone(analyze(rows,'2026-02-08')['weekly']['elapsed']['latest']['4']['value'])

    def test_missing_expected_daily_record_breaks_period_window(self):
        all_rows=weekdays('2026-01-05','2026-01-30');rows=[c for c in all_rows if c['date']!='2026-01-21']
        cal=dict(coverage_start='2026-01-05',coverage_end='2026-02-01',expected_dates=[c['date'] for c in all_rows])
        r=analyze(rows,'2026-02-01',calendar=cal)
        self.assertEqual(r['data_quality']['missing_dates'],['2026-01-21']);self.assertIsNone(r['weekly']['elapsed']['latest']['4']['value'])

    def test_unexpected_trading_date_is_not_hidden_by_calendar(self):
        rows=weekdays('2026-01-05','2026-01-09');cal=dict(coverage_start='2026-01-05',coverage_end='2026-01-11',expected_dates=[c['date'] for c in rows]);rows.append(candle('2026-01-10',110))
        r=analyze(rows,'2026-01-11',calendar=cal)
        self.assertEqual(r['weekly']['bars'][0]['unexpected_dates'],['2026-01-10']);self.assertEqual(r['weekly']['bars'][0]['ma_block_reason'],'CALENDAR_MISMATCH')

    def test_partial_calendar_does_not_label_outside_scope_prices_unexpected(self):
        rows=weekdays('2026-01-05','2026-01-16');cal=dict(coverage_start='2026-01-12',coverage_end='2026-01-16',expected_dates=[c['date'] for c in rows if c['date']>='2026-01-12'])
        r=analyze(rows,'2026-01-18',calendar=cal)
        self.assertEqual(r['data_quality']['unexpected_dates'],[]);self.assertEqual(r['data_quality']['calendar_status'],'PARTIAL_SUPPLIED_CALENDAR_SCOPE')

    def test_old_calendar_scope_does_not_falsely_resolve_a_later_left_edge(self):
        rows=weekdays('2026-02-03','2026-02-27');cal=dict(coverage_start='2026-01-01',coverage_end='2026-01-31',expected_dates=[])
        r=analyze(rows,'2026-02-28',calendar=cal)
        self.assertEqual(r['monthly']['bars'][-1]['ma_block_reason'],'LEFT_EDGE_UNCERTAIN')

    def test_future_prices_events_and_calendar_do_not_change_earlier_snapshot(self):
        rows=weekdays('2026-01-05','2026-03-31');cal=dict(coverage_start='2026-01-05',coverage_end='2026-03-31',expected_dates=[c['date'] for c in rows])
        a=analyze(rows,'2026-02-02',calendar=cal,mode='ADJUSTED_CANDIDATE')
        changed=deepcopy(rows);changed[-1].update(open='199',high='202',low='198',close='200');cal2=deepcopy(cal);cal2['expected_dates'].pop()
        b=analyze(changed,'2026-02-02',calendar=cal2,mode='ADJUSTED_CANDIDATE',events=[dict(effective_date='2026-03-01',factor='0.5')])
        self.assertEqual(a,b)

    def test_truncated_and_full_source_give_identical_same_date_snapshot(self):
        rows=weekdays('2026-01-05','2026-03-31');dt='2026-02-03'
        self.assertEqual(analyze(rows,dt),analyze([c for c in rows if c['date']<=dt],dt))

    def test_adjustment_is_applied_to_daily_prices_before_week_month_aggregation(self):
        rows=[candle('2026-01-05',100),candle('2026-01-06',100),candle('2026-01-07',50)];events=[dict(effective_date='2026-01-07',factor='0.5')]
        raw=analyze(rows,'2026-01-07',events=events);adj=analyze(rows,'2026-01-07',events=events,mode='ADJUSTED_CANDIDATE')
        for scale in ['weekly','monthly']:
            self.assertEqual(Decimal(adj[scale]['bars'][0]['open']),Decimal('49.5'))
            self.assertEqual(Decimal(raw[scale]['bars'][0]['open']),99)
            self.assertEqual(adj[scale]['bars'][0]['volume_shares'],'300')
        a=analyze(rows,'2026-01-06',events=events,mode='ADJUSTED_CANDIDATE');b=analyze(rows,'2026-01-06',mode='ADJUSTED_CANDIDATE');self.assertEqual(a,b)

    def test_raw_sma_keeps_price_series_across_cash_boundary(self):
        rows=[candle(dt,v) for dt,v in [('2026-01-05',100),('2026-01-12',100),('2026-01-19',100),('2026-01-26',50)]];events=[dict(effective_date='2026-01-26',factor='0.5')]
        self.assertEqual(analyze(rows,'2026-02-01',events=events)['weekly']['elapsed']['latest']['4']['value'],'87.5')
        self.assertEqual(analyze(rows,'2026-02-01',events=events,mode='ADJUSTED_CANDIDATE')['weekly']['elapsed']['latest']['4']['value'],'50.0')

    def test_missing_and_zero_volume_are_distinct_with_partial_known_sum(self):
        rows=[candle('2026-01-05',100,None),candle('2026-01-06',101,'0'),candle('2026-01-07',102,'7')]
        b=analyze(rows,'2026-01-11')['weekly']['bars'][0]
        self.assertIsNone(b['volume_shares']);self.assertEqual(b['known_volume_sum_shares'],'7');self.assertEqual(b['volume_context'],'PARTIAL')
        rows[0]['volume_shares_scaled']='0';self.assertEqual(analyze(rows,'2026-01-11')['weekly']['bars'][0]['volume_shares'],'7')

    def test_decimal_context_rounding_and_inexact_trap_do_not_change_results(self):
        rows=weekdays('2026-01-05','2026-05-29');base=analyze(rows,'2026-05-31',mode='ADJUSTED_CANDIDATE',events=[dict(effective_date='2026-02-02',factor='0.9123456789012345678901234567')])
        with localcontext() as ctx:
            ctx.prec=3;ctx.rounding=ROUND_FLOOR;ctx.traps[Inexact]=True
            changed=analyze(rows,'2026-05-31',mode='ADJUSTED_CANDIDATE',events=[dict(effective_date='2026-02-02',factor='0.9123456789012345678901234567')])
        self.assertEqual(base,changed)

    def test_empty_and_future_only_inputs_remain_empty(self):
        for rows in [[],[candle('2026-02-01',100)]]:
            r=analyze(rows,'2026-01-01');self.assertEqual(r['status'],'EMPTY_INPUT');self.assertEqual(r['weekly']['bars'],[]);self.assertIsNone(r['monthly']['candidate']['latest']['3']['value'])

    def test_invalid_calendar_and_unit_are_explicit_typed_errors(self):
        for cal in [{},dict(coverage_start='2026-02-01',coverage_end='2026-01-01',expected_dates=[]),dict(coverage_start='2026-01-01',coverage_end='2026-02-01',expected_dates=['2026-01-05']*2)]:
            with self.assertRaises(DataError):analyze([], '2026-01-01',calendar=cal)
        with self.assertRaises(DataError):analyze([],'2026-01-01',volume_unit='LOTS')
        with self.assertRaises(DataError):analyze([],'2026-02-30')
        with self.assertRaises(DataError):analyze([],'2026-01-01',exchange='UNKNOWN')

    def test_inputs_not_mutated_and_identity_records_source_unit_and_mode(self):
        rows=weekdays('2026-01-05','2026-02-27');before=deepcopy(rows);a=analyze(rows,'2026-02-28');b=analyze(rows,'2026-02-28',volume_unit='SHARES_SCALED_FROM_LOTS')
        self.assertEqual(rows,before);self.assertNotEqual(a['snapshot_id'],b['snapshot_id']);self.assertEqual(a['weekly'],b['weekly']);self.assertEqual(a['action_qualification'],'NOT_EVALUATED');self.assertNotEqual(a['snapshot_id'],analyze(rows,'2026-02-28',exchange='TPEX')['snapshot_id'])


if __name__=='__main__':unittest.main()
