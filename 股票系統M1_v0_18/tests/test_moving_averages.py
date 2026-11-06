import copy,json,sys,unittest
from decimal import Decimal, localcontext
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from contracts import DataError
from moving_averages import PERIODS,analyze_daily_ma
from structure import D,project_prices


def sample(n):
    from datetime import date,timedelta
    return [dict(date=(date(2025,1,1)+timedelta(days=i)).isoformat(),
                 open=str(i+1),high=str(i+2),low=str(i+1),close=str(i+1)) for i in range(n)]


class MovingAverageTests(unittest.TestCase):
    def test_full_windows_and_260_record_boundary(self):
        r=analyze_daily_ma(sample(261),code='FIXTURE',mode='RAW_CANDIDATE')
        for p in PERIODS:
            self.assertIsNone(r['snapshots'][p-2]['curves'][str(p)][-1])
            self.assertEqual(Decimal(r['snapshots'][p-1]['curves'][str(p)][-1]),Decimal(p+1)/2)
            self.assertTrue(r['snapshots'][p-1]['available'][str(p)])
        self.assertEqual(Decimal(r['snapshots'][260]['curves']['260'][-1]),Decimal('131.5'))

    def test_decimal_precision_and_formatted_prices(self):
        rows=sample(5)
        for r in rows:r.update(open='1,000.10',high='1,000.20',low='999.90',close='1,000.10')
        r=analyze_daily_ma(rows,code='FIXTURE',mode='RAW_CANDIDATE')
        self.assertEqual(Decimal(r['snapshots'][-1]['curves']['5'][-1]),Decimal('1000.10'))

    def test_prefix_and_changed_future_leave_earlier_snapshots_unchanged(self):
        rows=sample(8);event=[dict(effective_date=rows[6]['date'],factor='0.5')]
        early=analyze_daily_ma(rows[:6],code='FIXTURE',mode='ADJUSTED_CANDIDATE')
        full=analyze_daily_ma(rows,event,code='FIXTURE',mode='ADJUSTED_CANDIDATE')
        altered=copy.deepcopy(rows);altered[7].update(open='900',high='1000',low='800',close='900')
        changed=analyze_daily_ma(altered,event,code='FIXTURE',mode='ADJUSTED_CANDIDATE')
        self.assertEqual(early['snapshots'],full['snapshots'][:6])
        self.assertEqual(full['snapshots'][:7],changed['snapshots'][:7])

    def test_adjusted_curves_use_each_snapshot_anchor_without_overwriting_past(self):
        rows=sample(7);events=[dict(effective_date=rows[5]['date'],factor='0.5')]
        r=analyze_daily_ma(rows,events,code='FIXTURE',mode='ADJUSTED_CANDIDATE')
        self.assertEqual(Decimal(r['snapshots'][4]['curves']['5'][4]),Decimal(3))
        self.assertEqual(Decimal(r['snapshots'][5]['curves']['5'][4]),Decimal('1.5'))
        self.assertEqual(Decimal(r['snapshots'][5]['curves']['5'][5]),Decimal('2.6'))
        self.assertEqual(Decimal(r['snapshots'][4]['curves']['5'][4]),Decimal(3))

    def test_raw_series_keeps_unadjusted_full_windows_at_cash_event(self):
        rows=sample(7);event=[dict(effective_date=rows[5]['date'],factor='0.5')]
        r=analyze_daily_ma(rows,event,code='FIXTURE',mode='RAW_CANDIDATE')
        self.assertEqual(Decimal(r['snapshots'][5]['curves']['5'][-1]),Decimal(4))
        self.assertEqual(r['action_qualification'],'NOT_EVALUATED')

    def test_empty_and_invalid_inputs(self):
        self.assertEqual(analyze_daily_ma([],code='FIXTURE',mode='RAW_CANDIDATE')['snapshots'],[])
        for rows,mode in [(sample(1)*2,'RAW_CANDIDATE'),(sample(1),'AUTO')]:
            with self.assertRaises(DataError):analyze_daily_ma(rows,code='FIXTURE',mode=mode)
        rows=sample(5);rows[0]['close']=None
        with self.assertRaises(DataError):analyze_daily_ma(rows,code='FIXTURE',mode='RAW_CANDIDATE')

    def test_source_inputs_are_not_mutated(self):
        rows=sample(6);events=[dict(effective_date=rows[-1]['date'],factor='0.8')]
        before=copy.deepcopy((rows,events));analyze_daily_ma(rows,events,code='FIXTURE',mode='ADJUSTED_CANDIDATE')
        self.assertEqual((rows,events),before)

    def test_adjustment_decimals_do_not_leave_residue_after_the_window_rolls_out(self):
        rows=sample(11)
        for row in rows:row.update(open='160.10',close='160.10',high='161',low='159')
        event=[dict(effective_date=rows[5]['date'],factor='0.9764317865950925628752421999')]
        r=analyze_daily_ma(rows,event,code='FIXTURE',mode='ADJUSTED_CANDIDATE')
        self.assertEqual(Decimal(r['snapshots'][-1]['curves']['5'][-1]),Decimal('160.10'))

    def test_real_sample_output_matches_manual_close_mean(self):
        for code in ['8069','6488']:
            candles=json.loads((ROOT/'data'/f'{code}_candles.json').read_text())
            events=json.loads((ROOT/'data'/f'{code}_events.json').read_text())
            for mode in ['RAW_CANDIDATE','ADJUSTED_CANDIDATE']:
                r=json.loads((ROOT/'output'/f'{code}_{mode}_MA.json').read_text())
                for i in [4,19,59,129,259,282]:
                    rows=project_prices(candles,events,candles[i]['date'],mode)
                    for p in PERIODS:
                        v=r['snapshots'][i]['curves'][str(p)][-1]
                        if i+1<p:self.assertIsNone(v)
                        else:
                            with localcontext() as ctx:
                                ctx.prec=80
                                total=sum((D(c['close']) for c in rows[-p:]),Decimal(0))
                            self.assertEqual(Decimal(v),total/p)


if __name__=='__main__':unittest.main()
