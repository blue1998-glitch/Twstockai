"""Cross-artifact invariants, run after build_review.py."""
import json
import re
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


class GeneratedOutputTests(unittest.TestCase):
    def test_ledger_provenance_and_snapshot_times(self):
        for code in ['8069','6488']:
            for mode in ['RAW_CANDIDATE','ADJUSTED_CANDIDATE']:
                r=json.loads((ROOT/'output'/f'{code}_{mode}.json').read_text())
                known=set();ids=set()
                for e in r['event_ledger']:
                    self.assertNotIn(e['event_id'],ids);ids.add(e['event_id'])
                    if e['type']=='CANDIDATE_OBSERVED':known.add(e['candidate']['id'])
                    if e['type'] in ('CANDIDATE_REPLACED','CANDIDATE_CANCELLED_CORPORATE_ACTION','BOOTSTRAP_OTHER_CANDIDATE_CANCELLED'):
                        self.assertIn(e['candidate_id'],known)
                    if e['type']=='PIVOT_RULE_CONFIRMED_CANDIDATE':self.assertIn(e['pivot']['id'],known)
                for s in r['snapshots']:
                    self.assertEqual(s['action_qualification'],'NOT_EVALUATED')
                    for p in s['pivots']:
                        self.assertLessEqual(p['occurred_at'],p['first_observed_at'])
                        self.assertLessEqual(p['first_observed_at'],p['confirmed_at'])
                        self.assertLessEqual(p['confirmed_at'],s['as_of'])

    def test_compact_viewer_preserves_engine_points_and_zones(self):
        html=(ROOT/'價格結構重播.html').read_text()
        data=json.loads(re.search(r'const DATA=(.*?);\nfor\(const rec',html,re.S).group(1))
        for code,rec in data.items():
            for mode,view in rec['modes'].items():
                full=json.loads((ROOT/'output'/f'{code}_{mode}.json').read_text())['snapshots']
                self.assertEqual(len(view),len(full))
                for v,f in zip(view,full):
                    self.assertEqual(len(v['p']),len(f['pivots']))
                    for p,source in zip(v['p'],f['pivots']):
                        self.assertEqual((p[2],p[3],p[4]),(source['occurred_index'],source['confirmed_index'],source['price']))
                    self.assertEqual(len(v['z']),sum(z['state']=='ACTIVE_CANDIDATE' for z in f['zones']))
                    self.assertEqual(v['d'],f['daily_events'])

    def test_viewer_uses_actual_source_candles(self):
        html=(ROOT/'價格結構重播.html').read_text()
        data=json.loads(re.search(r'const DATA=(.*?);\nfor\(const rec',html,re.S).group(1))
        for code,rec in data.items():
            source=json.loads((ROOT/'data'/f'{code}_candles.json').read_text())
            self.assertEqual(rec['candles'],source)
            self.assertEqual(len(source),283)


if __name__=='__main__':unittest.main()
