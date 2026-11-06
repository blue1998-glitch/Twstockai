"""Real-store, prefix, precision and lossless transport checks for new main chart."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from technical_chart.build import ROOT, make, audit, pack, unpack, selection, render
from cross_view_cli import read_config
from analysis_store import AnalysisStore

class TechnicalChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=read_config(ROOT/'cross_view/sources.json')
        cls.payload=make(cls.config)
        cls.series=cls.payload['numbers']['series']

    def test_actual_1101_2884_official_responses_and_calendar(self):
        for s in self.series:
            c=self.payload['coverage'][s['key']]
            if s['code'] not in ('1101','2884'):continue
            self.assertEqual((c['first_date'],c['last_date'],c['bars']),('2026-01-02','2026-09-30',179))
            self.assertEqual(len(c['captured_official_response_checks']),9)
            self.assertEqual(c['missing_supplied_calendar_dates'],[])
            self.assertEqual(c['unexpected_supplied_calendar_dates'],[])
            self.assertEqual(c['actions_coverage'],'UNVERIFIED')
            self.assertEqual(c['volume_unit'],'SHARES_REPORTED')

    def test_other_real_ranges_are_not_multiyear(self):
        self.assertEqual(len(self.series),6)
        for s in self.series:
            if s['code'] in ('6488','8069'):
                c=self.payload['coverage'][s['key']]
                self.assertEqual((c['first_date'],c['last_date'],c['bars']),('2025-08-01','2026-09-30',283))
                self.assertIn('MULTI_YEAR_HISTORY_NOT_PRESENT',c['gaps'])
                self.assertEqual(c['missing_supplied_calendar_dates'],[])
                self.assertEqual(c['unexpected_supplied_calendar_dates'],[])

    def test_explicit_entry_and_no_fabricated_adjusted(self):
        entry=self.payload['entry'];s=next(s for s in self.series if s['key']==entry['series'])
        self.assertEqual((s['code'],s['price_mode'],entry['as_of']),('1101','RAW_CANDIDATE','2026-09-30'))
        self.assertEqual(len([s for s in self.series if s['code'] in ('1101','2884')]),2)
        self.assertEqual(sum(len(s['frames']) for s in self.series),1490)

    def test_saved_snapshots_and_evidence_are_exact_not_reclassified(self):
        for s in self.series:
            saved=AnalysisStore(self.config['daily_stores'][s['store']]).load(s['original_record_id'])
            snaps=saved['result']['components']['structure']['snapshots']
            for f,e,orig in zip(s['frames'],self.payload['evidence'][s['key']],snaps):
                self.assertEqual(e['snapshot_id'],f['structure_snapshot_id'])
                self.assertEqual(e['pivots'],orig['pivots']);self.assertEqual(e['zones'],orig['zones'])
                self.assertEqual([r['original'] for r in e['daily_events']],orig['daily_events'])
                self.assertEqual(e['parameters'],orig['parameters'])
                self.assertTrue(all(p['confirmed_at']<=f['as_of'] for p in e['pivots']))
                self.assertTrue(all(z['created_at']<=f['as_of'] for z in e['zones']))
                self.assertEqual(f['lifecycle']['stage'],'UNKNOWN')

    def test_all_frames_have_only_selected_prefix_and_event_basis(self):
        for s in self.series:
            for f in s['frames']:
                b=s['bases'][f['chart_base']]
                self.assertEqual(b['bars'][f['index']]['date'],f['as_of'])
                self.assertTrue(all(e['effective_date']<=f['as_of'] for e in b['known_events']))
                self.assertEqual(len(b['bars']),len(b['macd']))
                self.assertTrue(all(len(v)==len(b['bars']) for v in b['moving_averages'].values()))

    def test_downloads_keep_exact_original_numbers_and_prefix(self):
        from product_candidate.build import selection_payload
        for s in self.series:
            for i in (0,33,60,len(s['frames'])-1):
                f=s['frames'][i];v=selection(self.payload,s['key'],f['as_of'])
                self.assertEqual(v['analysis'],selection_payload(self.payload['numbers'],s['key'],f['as_of']))
                self.assertEqual(v['analysis']['bars'][-1]['date'],f['as_of'])
                self.assertEqual(v['coverage_of_selected_prefix']['bars'],i+1)
                self.assertEqual(v['structure_evidence']['as_of'],f['as_of'])
                history=v['historical_structure_events']
                self.assertEqual(len(history),i+1)
                self.assertTrue(all(e['as_of']<=f['as_of'] for e in history))
                self.assertEqual(history[0]['daily_events'],self.payload['evidence'][s['key']][0]['daily_events'])
                self.assertTrue(all(isinstance(b['close'],str) for b in v['analysis']['bars']))

    def test_mutating_future_cannot_change_old_selection(self):
        for s in self.series:
            f=s['frames'][60];b=s['bases'][f['chart_base']];before=selection(self.payload,s['key'],f['as_of'])
            future=b['bars'][61:];old_frames=s['frames'][61:];old_ev=self.payload['evidence'][s['key']][61:]
            # Remove all future frames/evidence/bars without touching any selected prefix.
            b['bars'][61:]=[];s['frames'][61:]=[];self.payload['evidence'][s['key']][61:]=[]
            try:self.assertEqual(selection(self.payload,s['key'],f['as_of']),before)
            finally:b['bars'][61:]=future;s['frames'][61:]=old_frames;self.payload['evidence'][s['key']][61:]=old_ev

    def test_full_transport_roundtrip_preserves_decimal_strings(self):
        packed=pack(self.payload)
        self.assertEqual(unpack(packed),self.payload)
        self.assertLess(len(json.dumps(packed)),len(json.dumps(self.payload)))

    def test_transport_rejects_unsafe_numbers_instead_of_rounding(self):
        for v in (9007199254740992,1.5):
            with self.assertRaises(ValueError):pack({'value':v})
        self.assertEqual(unpack(pack({'volume':'9007199254740993123','price':'1.0010000000000000001'})),{'volume':'9007199254740993123','price':'1.0010000000000000001'})

    def test_raw_response_tamper_is_rejected(self):
        s=next(s for s in self.series if s['code']=='1101')
        saved=AnalysisStore(self.config['daily_stores'][s['store']]).load(s['original_record_id'])
        saved['request']['source']['source_records'][0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'checksum mismatch'):audit(saved)

    def test_no_browser_network_or_analysis_engine(self):
        source=(ROOT/'technical_chart/viewer.js').read_text()
        for banned in ('fetch(', 'XMLHttpRequest', 'WebSocket', 'indexedDB', 'sqlite', 'attempt_evidence'):
            self.assertNotIn(banned,source)
        self.assertIn('frame.index+1',source)

if __name__=='__main__':unittest.main()
