"""Causal automatic range recognition and counterexamples; no manual-answer fit."""
from copy import deepcopy
from datetime import date,timedelta
import json
from pathlib import Path
import unittest

from graph_core.core import analyze,DEFAULT_CONFIG,trace_reference,fingerprint,volume_observation


def payload(values,*,missing_volume=(),basis_breaks=()):
    rows=[]
    for i,value in enumerate(values):
        day=(date(2020,1,1)+timedelta(days=i)).isoformat()
        rows.append(dict(date=day,open=str(value),high=str(value+1),low=str(value-1),close=str(value),volume_shares_scaled=None if i in missing_volume else str(1000+i*7)))
    return dict(schema_version='graph-recognition-input/0.1',context=dict(code='SYNTHETIC_TEST_ONLY',source_id='test-source',price_basis_id='test-raw',price_mode='RAW_CANDIDATE',volume_unit='SHARES_REPORTED'),bars=rows,basis_break_dates=list(basis_breaks))

OSC=[100,104,110,108,101,100,104,109,106,101,99,103,111,107,101,100,105,110,104,101,99,104,110,106,100,104,110,105,100]


class GraphCoreTests(unittest.TestCase):
    def run_core(self,p,as_of=None):return analyze(p,as_of=as_of or p['bars'][-1]['date'])

    def test_repeated_swing_geometry_is_automatic_and_qualified(self):
        p=payload(OSC);r=self.run_core(p)
        self.assertGreater(len(r['boxes']),0)
        self.assertFalse(r['manual_case_inputs_used']);self.assertEqual(r['formal_strategy_parameters'],{})
        self.assertIsNone(r['comparison']['primary_pressure_id'])
        for b in r['boxes']:
            self.assertIsNone(b['formal_price_bounds']);self.assertGreaterEqual(b['turns'],4)
            self.assertLessEqual(b['source_end'],b['first_observed_at'])
            self.assertGreaterEqual(len(b['source_turn_ids']),4)

    def test_monotone_trend_and_too_short_source_are_not_boxes(self):
        for values in ([100+i for i in range(50)],OSC[:3],[100]*30):
            r=self.run_core(payload(values));self.assertEqual(r['boxes'],[])
            self.assertEqual(r['comparison']['primary_pressure_id'],None)

    def test_complete_vs_truncated_prefix_identical_with_future_mutation(self):
        p=payload(OSC+OSC+[115,120,90,80]);indices=[6,12,18,25,35,45]
        for i in indices:
            a=self.run_core(p,p['bars'][i]['date']);short=deepcopy(p);short['bars']=short['bars'][:i+1]
            self.assertEqual(a,self.run_core(short))
            changed=deepcopy(p)
            for row in changed['bars'][i+1:]:row['high']='NaN';row['volume_shares_scaled']='INVALID_FUTURE'
            self.assertEqual(a,self.run_core(changed,p['bars'][i]['date']))

    def test_confirmed_geometry_and_prior_events_survive_append(self):
        p=payload(OSC+OSC+[115,120,105,85]+OSC);before=self.run_core(p,p['bars'][45]['date']);after=self.run_core(p)
        later={b['id']:b for b in after['boxes']}
        for b in before['boxes']:
            other=later[b['id']]
            for k in ['research_bounds','display_extent','confirmed_at','source_turn_ids']:self.assertEqual(b[k],other[k])
            self.assertEqual(b['path']['events'],[e for e in other['path']['events'] if e['date']<=before['as_of']])

    def test_fake_breakout_return_and_breakdown_new_box_both_preserved(self):
        p=payload(OSC+[115,118,108,100,85,88,94,90,85,89,94,90,86,90,94,89,86,90,94,88])
        r=self.run_core(p);events=[e for b in r['boxes'] for e in b['path']['events']]
        self.assertTrue(any('FAILED_UP' in e['type'] for e in events))
        self.assertTrue(any(e['location']=='BELOW' for e in events if 'location'in e))
        self.assertTrue(any(b['successor_after_breakdown_ids'] for b in r['boxes']))
        self.assertTrue(any(b['start']>=p['bars'][33]['date'] for b in r['boxes']))

    def test_equal_high_sources_preserved_without_unique_date_invention(self):
        p=payload([100,104,110,110,108,101,100,104,110,110,108,100,104,110,106,100]);r=self.run_core(p)
        highs=[x for x in r['pivots'] if x['kind']=='HIGH']
        self.assertTrue(any(len(x['source_dates'])>1 for x in highs))
        for x in highs:self.assertTrue(all(d<=x['confirmed_at'] for d in x['source_dates']))

    def test_occurrence_before_confirmation_and_no_future_point_before_confirm(self):
        p=payload(OSC);r=self.run_core(p)
        for pivot in r['pivots']:
            self.assertLess(pivot['occurred_at'],pivot['confirmed_at'])
            prior=pivot['confirmed_index']-1
            self.assertNotIn(pivot['id'],[x['id'] for x in self.run_core(p,p['bars'][prior]['date'])['pivots']])

    def test_same_day_extreme_reversal_order_ambiguity_is_retained(self):
        p=payload([100,105,110,111,105,100,104,111,105,100,104])
        p['bars'][4]['high']='120'
        r=self.run_core(p)
        self.assertTrue(any(a['reason']=='SAME_BAR_NEW_EXTREME_AND_REVERSAL_ORDER_UNKNOWN' for a in r['ambiguities']))
        self.assertFalse(any(x['occurred_index']==4 and x['confirmed_index']==4 for x in r['pivots']))

    def test_missing_price_and_expected_date_split_not_bridge(self):
        p=payload(OSC+OSC);i=26
        for k in ['open','high','low','close']:p['bars'][i][k]=None
        r=self.run_core(p);self.assertIn(p['bars'][i]['date'],r['data_gaps']['missing_price_rows'])
        self.assertTrue(all(not b['first_index']<i<b['last_index'] for b in r['boxes']))
        for b in r['boxes']:
            if b['first_index']<i:self.assertFalse(b['usable_at_anchor'])
        q=payload(OSC+OSC);q['expected_dates']=[b['date'] for b in q['bars']];absent=q['bars'].pop(i)['date'];r=self.run_core(q)
        self.assertEqual(r['data_gaps']['missing_expected_dates'],[absent])
        self.assertTrue(all(not b['start']<absent<b['source_end'] for b in r['boxes']))

    def test_basis_reset_stops_old_comparison_reference_and_volume_baseline(self):
        p=payload(OSC+OSC);p['basis_break_dates']=[p['bars'][29]['date']];r=self.run_core(p)
        old=[b for b in r['boxes'] if b['segment']==0];self.assertTrue(old)
        self.assertTrue(all(not b['usable_at_anchor'] and b['anchor_relation']=='NOT_COMPARABLE_AFTER_GAP' for b in old))
        relevant=r['comparison']['relevant_pressure_ids'];self.assertTrue(all(b['id'] not in relevant for b in old))
        self.assertTrue(any(x['path']['last_relation']=='NOT_COMPARABLE_AFTER_GAP' for x in r['reference_candidates']))
        later=[b for b in r['boxes'] if b['segment']==1]
        self.assertTrue(later)
        for b in later:
            baseline=b['volume']['prior_equal_record_window']
            self.assertTrue(baseline['first_date'] is None or baseline['first_date']>=p['basis_break_dates'][0])
            if b['first_index']-29 < b['duration_records']:self.assertFalse(baseline['complete'])

    def test_volume_missing_unknown_vs_real_zero(self):
        p=payload(OSC,missing_volume=range(len(OSC)));r=self.run_core(p)
        self.assertTrue(r['boxes'])
        for b in r['boxes']:
            self.assertIsNone(b['volume']['supplied_interval_total']);self.assertIsNone(b['volume']['mean']);self.assertIsNone(b['volume']['mean_to_prior_ratio'])
        z=payload(OSC)
        for row in z['bars']:row['volume_shares_scaled']='0'
        r=self.run_core(z);self.assertTrue(all(b['volume']['supplied_interval_total']=='0' for b in r['boxes']))
        self.assertTrue(all(b['volume']['mean_to_prior_ratio'] is None for b in r['boxes']))

    def test_invalid_units_ohlc_dates_complete_publication_and_basis_refused(self):
        for mutation in ['unit','ohlc','duplicate','partial','incomplete','unavailable','basis','decimal']:
            p=payload(OSC)
            if mutation=='unit':p['context']['volume_unit']='LOTS'
            elif mutation=='ohlc':p['bars'][4]['low']='999'
            elif mutation=='duplicate':p['bars'][4]['date']=p['bars'][3]['date']
            elif mutation=='partial':p['bars'][4]['high']=None
            elif mutation=='incomplete':p['bars'][-1]['complete']=False
            elif mutation=='unavailable':p['bars'][4]['available_at']='2099-01-01T00:00:00+08:00'
            elif mutation=='basis':p['context']['price_mode']='ADJUSTED_CANDIDATE';p['context']['adjustment_anchor']='2099-01-01'
            else:p['bars'][4]['high']=111.0
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.run_core(p)

    def test_caller_manual_answers_and_strategy_promotion_refused(self):
        for key in ['manual_cases','references']:
            p=payload(OSC);p[key]={}
            with self.assertRaises(ValueError):self.run_core(p)
        cfg=deepcopy(DEFAULT_CONFIG);cfg['status']='APPROVED'
        with self.assertRaises(ValueError):analyze(payload(OSC),as_of=payload(OSC)['bars'][-1]['date'],config=cfg)

    def test_input_not_mutated_and_code_rename_not_change_geometry(self):
        p=payload(OSC);before=deepcopy(p);a=self.run_core(p);self.assertEqual(p,before)
        p['context']['code']='ANOTHER_CODE';b=self.run_core(p)
        self.assertEqual(a['boxes'],b['boxes']);self.assertEqual(a['pivots'],b['pivots']);self.assertNotEqual(a['result_id'],b['result_id'])

    def test_generic_reference_keeps_every_failed_cross_without_intraday_claim(self):
        p=payload([99,101,99,102,98,103]);path=trace_reference(p['bars'],'100',0)
        self.assertEqual([e['date'] for e in path['events']],[r['date'] for r in p['bars'][1:]])
        self.assertEqual(sum('FAILED_UP' in e['type'] for e in path['events']),2)
        self.assertEqual(path['last_relation'],'ABOVE')

    def test_multiscale_parent_geometry_and_conflicts_no_unique_ranking(self):
        r=self.run_core(payload(OSC+OSC+[115,110,100,90,95]+OSC));by_id={b['id']:b for b in r['boxes']}
        for child in r['boxes']:
            for pid in child['parent_ids']:
                p=by_id[pid];self.assertLessEqual(p['first_index'],child['first_index']);self.assertGreaterEqual(p['last_index'],child['last_index']);self.assertGreater(p['duration_records'],child['duration_records'])
        self.assertIsNone(r['comparison']['primary_pressure_id']);self.assertIn('UNRESOLVED',r['comparison']['ranking_status'])

    def test_missing_explicit_volume_and_conflicting_row_basis_refused(self):
        p=payload(OSC);p['bars'][4].pop('volume_shares_scaled')
        with self.assertRaises(ValueError):self.run_core(p)
        p=payload(OSC);p['bars'][4]['price_basis_id']='another-basis'
        with self.assertRaises(ValueError):self.run_core(p)

    def test_core_runs_without_ui_database_network_or_old_engine_imports(self):
        import subprocess,sys
        script="""import builtins,json,sys
original=builtins.__import__
def guarded(name,*args,**kwargs):
    if name.split('.')[0] in ('sqlite3','streamlit','requests','graph_core_chart','product_candidate','structure'):raise RuntimeError(name)
    return original(name,*args,**kwargs)
builtins.__import__=guarded
from graph_core import analyze
p=json.loads(sys.stdin.read());r=analyze(p,as_of=p['bars'][-1]['date']);assert r['boxes'];print(r['schema_version'])
"""
        result=subprocess.run([sys.executable,'-c',script],input=json.dumps(payload(OSC)),text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertIn('graph-recognition-research',result.stdout)

    def test_volume_event_comparisons_exclude_today_and_preserve_nulls(self):
        p=payload(OSC)
        for row in p['bars']:row['volume_shares_scaled']='100'
        p['bars'][-1]['volume_shares_scaled']='200'
        r=volume_observation(p['bars'],len(p['bars'])-1)
        self.assertEqual(r['ratio_to_previous_means'],{'1':'2','5':'2','20':'2'})
        self.assertFalse(r['baseline_includes_current'])
        p['bars'][-2]['volume_shares_scaled']=None
        self.assertTrue(all(v is None for v in volume_observation(p['bars'],len(p['bars'])-1)['ratio_to_previous_means'].values()))

    def test_path_decline_duration_and_event_volume_are_raw_evidence(self):
        p=payload(OSC+[115,118,105,85,90]);r=self.run_core(p)
        for b in r['boxes']:
            self.assertEqual(b['path']['route_classification'],'UNKNOWN_NO_APPROVED_FAST_SLOW_DECLINE_RULE')
            for event in b['path']['events']:
                if 'volume' in event:self.assertEqual(event['volume']['current_shares'],next(row['volume_shares_scaled'] for row in p['bars'] if row['date']==event['date']))

    def test_real_source_prefix_and_case_sequence_are_evidence_not_accuracy(self):
        from candle_region_chart.build import load_parent
        parent=load_parent();s=next(s for s in parent['history_series'] if s['code']=='1101');f=s['frames'][-1]
        bars=s['bases'][f['chart_base']]['bars'];p=dict(schema_version='graph-recognition-input/0.1',context=dict(code=s['code'],source_id=s['source']['id'],price_basis_id=f['chart_base'],price_mode=s['price_mode'],volume_unit='SHARES_REPORTED'),bars=bars)
        r=self.run_core(p);self.assertEqual(r['anchor']['close'],'27.30');self.assertTrue(r['boxes'])
        # Audit a supplied case price separately; never use it as algorithm input.
        known=next(i for i,b in enumerate(bars) if b['date']=='2026-03-20')
        events=trace_reference(bars,'26.95',known)['events'];recent=[e for e in events if e['date']>='2026-10-12']
        self.assertEqual([e['date'] for e in recent],['2026-10-12','2026-10-13','2026-10-14','2026-10-15','2026-10-16'])
        for dt in ['2025-06-02','2026-01-27','2026-10-13']:
            i=next(i for i,b in enumerate(bars) if b['date']==dt);short=deepcopy(p);short['bars']=bars[:i+1]
            self.assertEqual(analyze(p,as_of=dt),analyze(short,as_of=dt))
        self.assertEqual(bars[sum(b['date']<'2025-06-03' for b in bars)]['high'],'28.00')
