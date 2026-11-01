from copy import deepcopy
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from graph_core_chart.comparison_export import (ROOT,HERE,MG3,CODES,project,run,sha,EVENT_FIELDS,BOX_FIELDS)
from graph_core_chart.build import PARENT_SHA256
from candle_region_chart.build import load_parent
from technical_chart.build import unpack
from graph_core.core import fingerprint


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=unpack(json.loads(re.search(r'id="payload"[^>]*>(.*?)</script>',(MG3/'M1_v019_graph_recognition_v02.html').read_text(),re.S)[1]))
        cls.parent=load_parent();cls.spec=json.loads((HERE.parent/'mg3_20261101/source-input-spec.json').read_text())
        cls.ledger=json.loads((ROOT/'pressure_chart/data/history-20261018/history-candidate.json').read_text())
        cls.index=json.loads((HERE/'index.json').read_text())

    def args(self,code):
        s=next(s for s in self.bundle['series'] if s['code']==code)
        r=json.loads((MG3/f'core-{code}-latest.json').read_text())
        return [r,deepcopy(s),next(p for p in self.parent['history_series'] if p['code']==code),self.spec,
                next(p for p in self.ledger['series'] if p['code']==code),{}]

    def test_all_originals_and_full_8069_read(self):
        frozen=json.loads((HERE/'frozen.json').read_text())
        for row in frozen['files']:
            raw=(ROOT.parent/row['path']).read_bytes()
            self.assertEqual(len(raw),row['bytes']);self.assertEqual(sha(raw),row['sha256'])
        self.assertEqual((MG3/'core-8069-latest.json').stat().st_size,12430568)

    def test_complete_boxes_and_each_original_event_projection(self):
        for s in self.index['stocks']:
            r=self.args(s['code'])[0]
            boxes=[b for info in s['box_shards'] for b in json.loads((HERE/info['path']).read_text())['boxes']]
            self.assertEqual([b['id'] for b in boxes],[b['id'] for b in r['boxes']])
            for b,original in zip(boxes,r['boxes']):
                for key in BOX_FIELDS:self.assertEqual(b[key],original[key])
                self.assertEqual(len(b['events']),len(original['path']['events']))
                for event,raw in zip(b['events'],original['path']['events']):self.assertEqual(event,[raw.get(k) for k in EVENT_FIELDS])
            self.assertEqual(s['event_count'],sum(len(b['path']['events']) for b in r['boxes']))

    def test_missing_6488_basis_break_refused_even_with_new_result_id(self):
        args=self.args('6488');args[0]['data_gaps']['basis_resets'].remove('2026-07-16')
        args[0]['result_id']=fingerprint({k:v for k,v in args[0].items() if k!='result_id'})
        args[1]['results'][-1]=deepcopy(args[0])
        with self.assertRaisesRegex(ValueError,'interruptions'):project(*args)

    def test_wrong_day_source_incomplete_result_and_qualification_refused(self):
        for kind in ('date','source','missing-box','qualification','parent'):
            a=self.args('1101')
            if kind=='date':a[0]['as_of']='2026-10-15'
            elif kind=='source':a[0]['context']['source_id']='WRONG'
            elif kind=='missing-box':a[0]['boxes'].pop()
            elif kind=='qualification':a[0]['classification_quality']='VALIDATED'
            else:
                a[2]=deepcopy(a[2]);a[2]['source']['id']='WRONG'
            with self.subTest(kind=kind),self.assertRaises(ValueError):project(*a)

    def test_real_nulls_ties_volume_precision_and_manual_separation(self):
        stocks={s['code']:s for s in self.index['stocks']}
        b=stocks['2884'];self.assertEqual(b['box_count'],32);self.assertEqual(b['comparable_candidate_ids'],[])
        self.assertIsNone(b['nearest_above']['distance_fraction'])
        c=stocks['6488'];self.assertEqual(c['source_input_binding']['basis_break_dates'],['2025-12-31','2026-07-16'])
        self.assertEqual(len(c['nearest_above']['candidate_ids']),8)
        boxes=[b for info in c['box_shards'] for b in json.loads((HERE/info['path']).read_text())['boxes']]
        self.assertTrue(all(b['research_bounds']['pressure_band'][0]=='977.00' for b in boxes if b['id'] in c['nearest_above']['candidate_ids']))
        for code in ('6488','8069'):
            v=stocks[code]['volume_provenance'];self.assertEqual(v['multiplier'],'1000')
            self.assertFalse(v['native_exact_share_count_certified']);self.assertIn('NOT_NATIVE',v['precision'])
        a=stocks['1101'];self.assertEqual(a['manual_audit']['previous_manual_box']['records'],39)
        boxes=[b for info in a['box_shards'] for b in json.loads((HERE/info['path']).read_text())['boxes']]
        local=[b for b in boxes if b['start']=='2025-04-08' and b['source_end']=='2025-05-13']
        self.assertGreaterEqual(len(local),2);self.assertTrue(all(b['duration_records']==25 for b in local))
        for s in stocks.values():
            self.assertIsNone(s['primary_pressure_id']);self.assertFalse(s['policy_authorized']);self.assertEqual(s['classification_quality'],'NOT_VALIDATED')
            self.assertTrue(s['pending_extrema']);self.assertEqual(s['source_input_binding']['historical_available_at'],'UNKNOWN')

    def test_shards_complete_bounded_and_hash_verified(self):
        self.assertLess((HERE/'index.json').stat().st_size,1000000)
        for s in self.index['stocks']:
            self.assertEqual(sum(i['count'] for i in s['box_shards']),s['box_count'])
            for info in s['box_shards']:
                raw=(HERE/info['path']).read_bytes();self.assertLess(len(raw),1000000)
                self.assertEqual(len(raw),info['bytes']);self.assertEqual(sha(raw),info['sha256'])
                self.assertNotIn('RAW_CANDLES',json.loads(raw))

    def test_no_recognition_no_input_mutation_and_immutable_reexport(self):
        a=self.args('1101');before=deepcopy(a);project(*a);self.assertEqual(a,before)
        files=[HERE/'index.json']+[HERE/i['path'] for s in self.index['stocks'] for i in s['box_shards']]
        old={str(p):(p.read_bytes(),p.stat().st_mtime_ns) for p in files}
        with patch('graph_core_chart.build.analyze',side_effect=AssertionError('No recognition')):
            self.assertEqual(run(),self.index)
        self.assertEqual(old,{str(p):(p.read_bytes(),p.stat().st_mtime_ns) for p in files})


if __name__=='__main__':unittest.main()
