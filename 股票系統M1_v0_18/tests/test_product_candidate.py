"""Candidate engineering expectations are specified before scenario execution.

Synthetic saved evidence tests causality and explicit conditions, not trading
classification accuracy. Real-store checks are separate and trace original IDs.
"""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal, localcontext
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from contracts import fingerprint
from analysis_jobs import run_analysis_job
from product_candidate.macd import macd
from product_candidate.context import frame_context, activity, background_evidence
from product_candidate.build import series_from_saved, publish_immutable, render


def fixture(close='125', *, zone_state='ACTIVE_CANDIDATE', low='109', high='111', histogram='3'):
    rows = [dict(date=(date(2026, 1, 1) + timedelta(days=i)).isoformat(),
                 open=close, high=str(Decimal(close) + 1), low=str(Decimal(close) - 1),
                 close=close, volume_shares_scaled='1000') for i in range(45)]
    q = dict(code='SYNTHETIC', exchange='TWSE', price_mode='RAW_CANDIDATE',
             source=dict(id='SYNTHETIC_NOT_MARKET', volume_unit='SHARES_REPORTED'), candles=rows,
             corporate_actions=dict(records=[]))
    pivots = []
    for i, (kind, price) in enumerate([('HIGH', '120'), ('LOW', '100'), ('HIGH', '130'), ('LOW', '110')]):
        pivots.append(dict(id='p'+str(i), kind=kind, profile='major', price=price,
                           occurred_at=rows[i*7]['date'], first_observed_at=rows[i*7+1]['date'],
                           confirmed_at=rows[i*7+3]['date'], status='RULE_CONFIRMED_CANDIDATE'))
    z = dict(id='zone:p3', pivot_id='p3', profile='major', role='SUPPORT_CANDIDATE',
             low=low, high=high, created_at=rows[24]['date'], invalidated_at=rows[-1]['date'] if zone_state=='BREACHED_CANDIDATE' else None,
             state=zone_state, touch_episodes=2, outside_streak=2 if zone_state=='BREACHED_CANDIDATE' else 0,
             invalidation_rule='2 consecutive closes beyond boundary', formation_basis='Saved synthetic pivot/width')
    s = dict(as_of=rows[-1]['date'], adjustment_anchor=rows[-1]['date'], price_mode=q['price_mode'],
             pivots=pivots, zones=[z], snapshot_id='SYNTHETIC_SNAPSHOT', data_fingerprint=fingerprint(rows),
             effective_events_fingerprint=fingerprint([]), daily_events=[])
    m = dict(as_of=s['as_of'], snapshot_id='SYNTHETIC_MA', curves={'20':['110','111']})
    return q, s, m, rows, dict(dif='2', dea='1', histogram=histogram, reason='AVAILABLE')


def saved_job(n=60, mode='RAW_CANDIDATE', future_event=False):
    rows = []
    for i in range(n):
        price = Decimal(100) + Decimal(i % 15) / 2
        rows.append(dict(date=(date(2026, 1, 1)+timedelta(days=i)).isoformat(),open=str(price),
                         high=str(price+2), low=str(price-2),close=str(price+1), volume_shares_scaled=str(1000+i)))
    events = [dict(effective_date='2026-02-10',factor='0.95')]
    if future_event:
        events.append(dict(effective_date='2026-03-01',factor='0.9'))
    q = dict(schema_version='stock-analysis/1.0', code='SYNTHETIC', exchange='TWSE',
             price_mode=mode, timeframe='daily', source=dict(id='FIXED_TEST_SOURCE',code='SYNTHETIC',
             exchange='TWSE',volume_unit='SHARES_REPORTED'), candles=rows,
             corporate_actions=dict(records=events,coverage_status='UNVERIFIED'))
    return dict(record_id='SYNTHETIC_RECORD',request=q,result=run_analysis_job(q))


def advance(args, *, close=None, histogram=None, zone_state=None):
    """Append one observation to a synthetic saved-evidence stub, preserving prefix."""
    values=list(deepcopy(args))
    row=deepcopy(values[3][-1]);row['date']=(date.fromisoformat(row['date'])+timedelta(days=1)).isoformat()
    if close is not None:
        row.update(open=close,close=close,high=str(Decimal(close)+1),low=str(Decimal(close)-1))
    values[3].append(row)
    values[1]['as_of']=values[1]['adjustment_anchor']=values[2]['as_of']=row['date']
    values[1]['data_fingerprint']=fingerprint(values[3])
    if histogram is not None:values[4]['histogram']=histogram
    if zone_state is not None:
        values[1]['zones'][0]['state']=zone_state
        values[1]['zones'][0]['invalidated_at']=row['date'] if zone_state=='BREACHED_CANDIDATE' else None
    return values


class MACDCandidateTests(unittest.TestCase):
    def test_constant_and_linear_closed_form_warmup(self):
        constant = macd(['100']*60)
        self.assertIsNone(constant[24]['dif'])
        self.assertIsNone(constant[32]['histogram'])
        self.assertEqual(Decimal(constant[33]['histogram']), 0)
        ramp = macd(list(range(1,61)))
        self.assertEqual(Decimal(ramp[25]['dif']), 7)
        self.assertEqual(Decimal(ramp[33]['dea']), 7)
        self.assertEqual(Decimal(ramp[-1]['histogram']), 0)

    def test_independent_weighted_closed_form_not_recurrence(self):
        prices = [Decimal(100+i%11) for i in range(70)]
        def closed(values, length):
            a = Decimal(2)/(length+1); seed = sum(values[:length])/length
            n = len(values)-length
            return seed*(1-a)**n + sum(a*values[j]*(1-a)**(len(values)-1-j) for j in range(length,len(values)))
        with localcontext() as ctx:
            ctx.prec = 70
            difs = [closed(prices[:i],12)-closed(prices[:i],26) for i in range(26,71)]
            expected_dea = closed(difs,9)
            actual = macd(prices)[-1]
            self.assertLess(abs(Decimal(actual['dif'])-difs[-1]), Decimal('1e-45'))
            self.assertLess(abs(Decimal(actual['dea'])-expected_dea), Decimal('1e-45'))
            self.assertLess(abs(Decimal(actual['histogram'])-2*(difs[-1]-expected_dea)), Decimal('1e-45'))

    def test_missing_price_and_explicit_reset_need_full_rewarm(self):
        rows = ['100']*40 + [None] + ['101']*40
        value = macd(rows)
        self.assertEqual(value[40]['reason'], 'MISSING_PRICE_RESET')
        self.assertIsNone(value[73]['histogram'])
        self.assertEqual(value[74:], macd(['101']*40)[33:])
        self.assertEqual(macd(['100']*80,resets=[40])[40:], macd(['100']*40))

    def test_prefix_values_are_stable_with_appends_and_future_changes(self):
        rows = [str(100+i%7) for i in range(80)]
        self.assertEqual(macd(rows[:50]),macd(rows)[:50])
        self.assertEqual(macd(rows)[:50],macd(rows[:50]+['10000']*30)[:50])
        for parameters in [(0,26,9),(26,12,9),(True,26,9)]:
            with self.assertRaises(ValueError):macd(rows,fast=parameters[0],slow=parameters[1],signal=parameters[2])


class ContextCandidateTests(unittest.TestCase):
    def test_zone_evidence_preserves_occurrence_observation_confirmation_and_pending_separation(self):
        args=list(fixture());args[1]['pending']=[dict(id='unconfirmed',status='PENDING')]
        result=frame_context(*args);zone=result['zones'][0];pivot=args[1]['pivots'][-1]
        for key in ['occurred_at','first_observed_at','confirmed_at']:
            self.assertEqual(zone[key],pivot[key])
        self.assertEqual(result['pending'],args[1]['pending'])
        self.assertFalse(any(l['end_id']=='unconfirmed' for l in result['legs']))

    def test_rising_swing_consolidation_then_readvance_keeps_reference_and_history(self):
        args = fixture(close='125')
        before = deepcopy(args)
        first = frame_context(*args)
        self.assertEqual(first['structure']['candidate_state'],'RISING_SWINGS_REFERENCE_INTACT')
        next_args = advance(args,close='129')
        second = frame_context(*next_args,previous=first)
        self.assertEqual(second['previous_frame_id'],first['frame_id'])
        self.assertEqual(second['structure_id'],first['structure_id'])
        self.assertEqual(args,before)
        self.assertEqual(first['lifecycle']['stage'],'UNKNOWN')
        self.assertEqual(first['action_qualification'],'NOT_EVALUATED')

    def test_momentum_weakens_while_major_reference_remains_intact(self):
        earlier=fixture(histogram='5')
        previous = frame_context(*earlier)
        now = frame_context(*advance(earlier,histogram='3'),previous=previous)
        self.assertEqual(now['structure']['candidate_state'],'RISING_SWINGS_REFERENCE_INTACT')
        self.assertIn('POSITIVE_MACD_HISTOGRAM_DECREASING',[x['code'] for x in now['opposing']])
        self.assertEqual(now['structure']['primary_low_condition'],'NOT_BREACHED')

    def test_retest_break_and_rebuild_are_explicit_without_rewriting_previous(self):
        a=fixture();intact = frame_context(*a)
        b=advance(a,close='108');challenged = frame_context(*b,previous=intact)
        self.assertEqual(challenged['structure']['candidate_state'],'PRIMARY_LOW_REFERENCE_CHALLENGED')
        c=advance(b,close='108',zone_state='BREACHED_CANDIDATE');broken = frame_context(*c,previous=challenged)
        self.assertEqual(broken['structure']['candidate_state'],'PRIMARY_LOW_REFERENCE_BREACHED')
        self.assertTrue(any(c['kind']=='STRUCTURE_CONTEXT_CHANGED' for c in broken['changes']))
        fresh = advance(c,close='115',zone_state='ACTIVE_CANDIDATE')
        fresh[1]['zones'][0].update(low='104',high='106')
        fresh[1]['pivots'][-1]['id']='new_low'
        fresh[1]['zones'][0]['pivot_id']='new_low';fresh[1]['zones'][0]['id']='zone:new_low'
        rebuilt=frame_context(*fresh,previous=broken)
        self.assertEqual(rebuilt['structure']['primary_low_condition'],'NOT_BREACHED')
        self.assertEqual(broken['structure']['candidate_state'],'PRIMARY_LOW_REFERENCE_BREACHED')

    def test_breached_resistance_reentry_is_evidence_not_role_swap_or_formal_pattern(self):
        args=list(fixture(close='128',low='129',high='131',zone_state='BREACHED_CANDIDATE'))
        args[1]['zones'][0].update(role='RESISTANCE_CANDIDATE',pivot_id='p2')
        now=frame_context(*args)
        self.assertIn('RETURNED_INTO_OR_BELOW_PREVIOUSLY_BREACHED_RESISTANCE',[r['code'] for r in now['opposing']])
        self.assertEqual(now['zones'][0]['role'],'RESISTANCE_CANDIDATE')
        self.assertEqual(now['pattern'],'UNKNOWN_FORMAL_RULES_UNDEFINED')

    def test_timeframe_conflict_is_separate_and_missing_background_never_uses_nearest(self):
        block=dict(periods=[4],elapsed=dict(curves={'4':['120','119']},latest={'4':dict(value='119',reason='VALUE_AVAILABLE')}),
                   candidate=dict(curves={'4':['121','120']},latest={'4':dict(value='120',reason='VALUE_AVAILABLE')}))
        period=dict(alignment_status='ALIGNED_INPUTS',analysis_id='TEST_PERIOD',record_fingerprint='TEST_FP',snapshot=dict(weekly=block,monthly=block))
        frame=frame_context(*fixture(),period=period)
        self.assertEqual(len(frame['background']['conflicts']),2)
        self.assertIn('TIMEFRAME_CONFLICT',[e['code'] for e in frame['opposing']])
        self.assertEqual(background_evidence(None,'HIGHER')['status'],'NOT_SAVED_AT_THIS_AS_OF')
        period['alignment_status']='CONFLICT'
        self.assertEqual(background_evidence(period,'HIGHER')['status'],'CONFLICT')

    def test_insufficient_evidence_and_contraction_do_not_become_lifecycle_or_ownership(self):
        args=list(fixture())
        args[1]['pivots']=[];args[1]['zones']=[]
        args[-1]=dict(dif=None,dea=None,histogram=None,reason='FULL_WINDOW_WARMUP')
        frame=frame_context(*args)
        self.assertEqual(frame['structure']['candidate_state'],'UNKNOWN')
        self.assertEqual(frame['correction']['state'],'UNKNOWN')
        self.assertEqual(frame['intraday'],'INTRADAY_NOT_EVALUABLE')
        rows=deepcopy(args[3]);rows[-1]['volume_shares_scaled']=None
        self.assertIsNone(activity(rows)['volume_mean_5'])
        self.assertIsNone(activity(rows)['volume_vs_previous20'])
        for row in rows[-5:]:row.update(volume_shares_scaled='1',high='125.1',low='124.9',close='125')
        facts=activity(rows)
        self.assertEqual(facts['volume_5_vs_20'],'LOWER')
        self.assertEqual(facts['range_5_vs_20'],'LOWER')
        self.assertEqual(facts['ownership_claim'],'UNKNOWN_NO_HOLDER_OR_BROKER_DATA')

    def test_future_pivot_or_wrong_anchor_is_rejected_not_rendered(self):
        args=list(fixture());args[1]['pivots'][0]['confirmed_at']='2099-01-01'
        with self.assertRaises(ValueError):frame_context(*args)
        args=list(fixture());args[1]['adjustment_anchor']='2020-01-01'
        with self.assertRaises(ValueError):frame_context(*args)

    def test_momentum_comparison_uses_same_price_anchor_not_previous_adjusted_frame(self):
        a=list(fixture(histogram='2'));a[0]['price_mode']=a[1]['price_mode']='ADJUSTED_CANDIDATE'
        previous=frame_context(*a)
        b=advance(a,histogram='3');b[1]['effective_events_fingerprint']='NEW_EFFECTIVE_ACTION_BASIS'
        self.assertEqual(frame_context(*b,previous=previous)['momentum']['histogram_change'],'UNKNOWN')
        current=frame_context(*b,previous=previous,prior_indicator=dict(histogram='4'))
        self.assertEqual(current['momentum']['histogram_change'],'LOWER')
        self.assertEqual(current['momentum']['previous_histogram_same_anchor'],'4')


class CandidateReplayTests(unittest.TestCase):
    def test_real_engine_saved_fixture_prefix_append_and_future_action_do_not_rewrite_frames(self):
        for mode in ['RAW_CANDIDATE','ADJUSTED_CANDIDATE']:
            earlier=saved_job(50,mode)
            later=saved_job(65,mode,future_event=True)
            a=series_from_saved(earlier,'SYNTHETIC',{})
            b=series_from_saved(later,'SYNTHETIC',{})
            self.assertEqual(a['frames'],b['frames'][:50])
            for index,frame in enumerate(a['frames']):
                self.assertEqual(frame['frame_id'],fingerprint({k:v for k,v in frame.items() if k!='frame_id'}))
                self.assertEqual(a['bases'][frame['chart_base']]['bars'][:index+1],b['bases'][frame['chart_base']]['bars'][:index+1])
            self.assertIsNone(b['frames'][40]['momentum']['histogram']) if mode=='RAW_CANDIDATE' else None

    def test_existing_candidate_files_never_overwrite_or_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'candidate.json'
            self.assertEqual(publish_immutable(path,b'original'),'CREATED')
            self.assertEqual(publish_immutable(path,b'original'),'EXISTING')
            with self.assertRaises(ValueError):publish_immutable(path,b'different')
            self.assertEqual(path.read_bytes(),b'original')
            link=Path(temp)/'alias';link.symlink_to(path)
            with self.assertRaises(ValueError):publish_immutable(link,b'original')

    def test_candidate_html_escaping_and_no_ui_numeric_engine_or_network(self):
        html=render(dict(value='</script><script>BAD()</script>'))
        self.assertNotIn('</script><script>BAD()',html)
        self.assertIn("connect-src 'none'",html)
        script=(ROOT/'product_candidate/viewer.js').read_text()
        for token in ['fetch(', 'XMLHttpRequest', 'WebSocket', 'localStorage', 'innerHTML']:
            self.assertNotIn(token,script)
        self.assertNotIn('ema_fast',script)


if __name__=='__main__':unittest.main()
