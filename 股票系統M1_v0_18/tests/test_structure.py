import copy
import json
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from structure import Config, D, analyze, project_prices, _run_prefix, update_zone


def candles(values):
    return [dict(date=(date(2026,1,1)+timedelta(days=i)).isoformat(),open=str(v),high=str(v+1),low=str(v-1),close=str(v),volume_shares_scaled='1000') for i,v in enumerate(values)]


class StructureTests(unittest.TestCase):
    def setUp(self):
        self.cfg=Config(window=2,minor_multiple='1',major_multiple='2',minor_bars=2,major_bars=3)

    def test_prefix_stability_and_changed_future(self):
        cs=candles([10,12,14,16,18,20,22,22,20,18,16,18,20,24,22,19,17])
        full=analyze(cs,code='TEST',mode='RAW_CANDIDATE',cfg=self.cfg,source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
        for n in (1,5,9,13):
            part=analyze(cs[:n],code='TEST',mode='RAW_CANDIDATE',cfg=self.cfg,source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
            self.assertEqual(part['snapshots'],full['snapshots'][:n])
        changed=copy.deepcopy(cs);changed[-1].update(open='99',high='100',low='98',close='99')
        other=analyze(changed,code='TEST',mode='RAW_CANDIDATE',cfg=self.cfg,source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
        self.assertEqual(other['snapshots'][:-1],full['snapshots'][:-1])

    def test_occurrence_confirmation_and_plateau(self):
        cs=candles([10,12,14,16,18,20,22,22,20,18,16,18,20])
        r=_run_prefix(cs,self.cfg)
        p=next(p for p in r['pivots'] if p['profile']=='minor' and p['kind']=='HIGH')
        self.assertEqual(p['occurred_at'],cs[6]['date'])
        self.assertGreater(p['confirmed_at'],p['occurred_at'])
        self.assertGreaterEqual(p['confirmed_index']-p['occurred_index'],2)
        self.assertEqual(p['classification_quality'],'NOT_VALIDATED')

    def test_candidate_replacement_is_preserved(self):
        r=_run_prefix(candles([10,12,14,16,18,20,22,18,16]),self.cfg)
        replacements=[e for e in r['events'] if e['type']=='CANDIDATE_REPLACED']
        self.assertTrue(replacements)
        self.assertNotEqual(replacements[0]['candidate_id'],replacements[0]['replaced_by'])
        self.assertIn('previous_candidate',replacements[0])

    def test_same_day_both_directions_unknown(self):
        cs=candles([20,20,20])
        cs[1].update(high='30',low='10');cs[2].update(high='29',low='11')
        cfg=Config(window=2,minor_multiple='0.5',major_multiple='0.5',minor_bars=1,major_bars=1)
        r=_run_prefix(cs,cfg)
        self.assertFalse(r['pivots'])
        self.assertTrue(any(e['type']=='AMBIGUOUS_BOTH_DIRECTIONS' for e in r['events']))

    def test_missing_and_bad_data_rejected(self):
        cs=candles([10,11,12])
        for bad in [cs+[cs[-1]],list(reversed(cs))]:
            with self.assertRaises(ValueError):_run_prefix(bad,self.cfg)
        cs[0]['high']='1'
        with self.assertRaises(ValueError):_run_prefix(cs,self.cfg)
        with self.assertRaises(ValueError):Config(window=0).validate()

    def test_warmup_and_qualifications(self):
        r=analyze(candles([10,11]),code='T',mode='RAW_CANDIDATE',source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
        self.assertTrue(all(s['structure_status']=='UNKNOWN' and s['evidence_sufficiency']=='WARMUP' for s in r['snapshots']))
        self.assertTrue(all(s['action_qualification']=='NOT_EVALUATED' for s in r['snapshots']))

    def test_raw_corporate_boundary_resets(self):
        cs=candles([10,12,14,16,18,20,22,18,16,14,12,10,12,14])
        boundary=cs[10]['date']
        r=_run_prefix(cs[:11],self.cfg,raw_boundaries={boundary})
        self.assertTrue(r['warmup'])
        self.assertFalse(r['pending'])
        self.assertTrue(all(z['state']!='ACTIVE_CANDIDATE' for z in r['zones']))
        self.assertTrue(any(e['type']=='RAW_CORPORATE_ACTION_BOUNDARY' for e in r['events']))
        snap=analyze(cs[:11],[dict(effective_date=boundary,factor='0.9')],code='T',mode='RAW_CANDIDATE',cfg=self.cfg,source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')['snapshots'][-1]
        self.assertEqual(snap['structure_status'],'UNKNOWN')

    def test_adjusted_future_event_and_boundary(self):
        cs=candles([100,90,72]);cs[0]['date']='2026-01-01';cs[1]['date']='2026-01-02';cs[2]['date']='2026-01-03'
        events=[dict(effective_date='2026-01-02',factor='0.9'),dict(effective_date='2026-01-03',factor='0.8')]
        before=copy.deepcopy(cs)
        a=project_prices(cs,events,'2026-01-02','ADJUSTED_CANDIDATE')
        self.assertEqual([D(c['close']) for c in a],[D(90),D(90)])
        self.assertEqual(cs,before)
        future=events+[dict(effective_date='2099-01-01',factor='0.1')]
        self.assertEqual(a,project_prices(cs,future,'2026-01-02','ADJUSTED_CANDIDATE'))

    def zone(self):
        return dict(id='z',role='SUPPORT_CANDIDATE',low=D(10),high=D(12),created_index=0,state='ACTIVE_CANDIDATE',
                    touch_episodes=0,was_touching=False,last_close_location='NOT_OBSERVED',outside_streak=0,invalidated_at=None)

    def test_zone_contacts_count_episodes(self):
        z=self.zone()
        for i,c in enumerate(candles([11,11,11,15,11]),1):update_zone(z,c,i,self.cfg)
        self.assertEqual(z['touch_episodes'],2)

    def test_zone_single_breach_return_and_consecutive_failure(self):
        z=self.zone()
        for i,c in enumerate(candles([8,11,8]),1):update_zone(z,c,i,self.cfg)
        self.assertEqual(z['state'],'ACTIVE_CANDIDATE')
        update_zone(z,candles([8])[0],4,self.cfg)
        self.assertEqual(z['state'],'BREACHED_CANDIDATE')

    def test_real_samples_prefix_and_future_isolation(self):
        root=Path(__file__).resolve().parents[1]
        for code in ['8069','6488']:
            cs=json.loads((root/'data'/f'{code}_candles.json').read_text())
            events=json.loads((root/'data'/f'{code}_events.json').read_text())
            for mode in ['RAW_CANDIDATE','ADJUSTED_CANDIDATE']:
                full=analyze(cs,events,code=code,mode=mode,source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
                for count in (45,160,260):
                    part=analyze(cs[:count],events,code=code,mode=mode,source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
                    self.assertEqual(part['snapshots'],full['snapshots'][:count])
                changed=copy.deepcopy(cs);changed[-1].update(open='100',high='100',low='100',close='100')
                other=analyze(changed,events,code=code,mode=mode,source_id='fixture',volume_unit='SHARES_SCALED_FROM_LOTS')
                self.assertEqual(other['snapshots'][:-1],full['snapshots'][:-1])


if __name__=='__main__':unittest.main()
