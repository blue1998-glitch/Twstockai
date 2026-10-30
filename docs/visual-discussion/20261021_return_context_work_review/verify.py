"""Meaningful cutoff/source-freshness checks; prior product tests are not run."""
import copy,hashlib,json
from decimal import Decimal as D
from pathlib import Path
from study import ROOT,SOURCE,project,write,left_date,turn_ids
s=json.loads(SOURCE.read_text());c=json.loads((ROOT/'study-inputs.json').read_text());views=json.loads((ROOT/'context-views.json').read_text())
for cut,r in views.items():
    assert project(s,c,cut)==r
    prefix=copy.deepcopy(s);prefix['bars']=[b for b in prefix['bars']if b['date']<=cut]
    assert project(prefix,c,cut)==r
    poison=copy.deepcopy(s);poison['manual_labels']={'formal_parent':'G2','importance':999}
    for b in poison['bars']:
        if b['date']>cut:b.update(open='999',high='999',low='-999',close='999',volume_shares_scaled='9999999999')
    assert project(poison,c,cut)==r
    future=copy.deepcopy(c)
    for z in future['zones'].values():
        if z['known_on_saved_bar']>cut:z.update(path_start='1900-01-01',path_end='2099-01-01',common_close_low='-999',common_close_high='999',leg_ids=['FORBIDDEN_FUTURE_LEG'])
    for x in future['contexts'].values():
        if x['known_on']>cut:x.update(low='-999',high='999',source_turn_ids=['FORBIDDEN_FUTURE_TURN'])
    for p in future['pivots'].values():
        if p['known_on']>cut:p.update(price='999',occurred_at='1900-01-01')
    assert project(s,future,cut)==r
    for field in ['formal_structure','formal_parent','formal_merge','formal_end','formal_reaction','selected_role','importance_score','primary_pressure_id','independent_confirmation_count']:assert r[field]is None
    assert not r['historical_signal_eligible']and not r['manual_labels_used']
    for item in r['local_activities'].values():
        if item is None:continue
        z=item['zone'];paths=[b for b in prefix['bars']if z['path_start']<=b['date']<=z['path_end']]
        assert len(paths)==z['raw_path_frame']['records']
        assert min(D(b['low'])for b in paths)==D(z['raw_path_frame']['observed_low'])and max(D(b['high'])for b in paths)==D(z['raw_path_frame']['observed_high'])
        legs=[c['legs'][i]for i in z['leg_ids']]
        assert max(D(l['close_low'])for l in legs)==D(z['common_close_low'])and min(D(l['close_high'])for l in legs)==D(z['common_close_high'])
        assert item['complete_evidence_start']==min(c['turns'][i]['left_evidence_date']for i in turn_ids(z,c))
    for cmp in r['local_comparisons']:
        a,b=[r['local_activities'][cmp[k]]['zone']for k in ['older','later']]
        assert not cmp['shared_leg_ids']and not cmp['shared_turn_ids']
        assert cmp['later_complete_evidence_strictly_after_older_known']
# Explicit chronology and semantic counterexamples, all with exact saved values.
assert views['2023-07-18']['local_activities']['lower-local']is None
assert views['2023-07-19']['local_activities']['lower-local']['zone']['common_close_high']=='37.00'
assert views['2023-07-24']['original_points']['new-low']is None and views['2023-07-24']['original_boxes']['later-original-box']is None
r=views['2023-07-25'];assert r['current_bar']['close']=='37.40'
assert r['original_points']['later-low']['current_close_side']=='ABOVE'and r['original_points']['earlier-high']['current_close_side']=='BELOW'and r['original_points']['retained-high']['current_close_side']=='BELOW'
assert r['local_activities']['earlier-local']['current_vs_common']=='BELOW'and r['local_activities']['rebound-local']is None
assert r['original_boxes']['later-original-box']['context']['low']=='36.00'
assert len(r['box_source_comparison']['shared_turn_ids'])==2 and r['box_source_comparison']['same_high_price']
assert views['2023-07-28']['local_activities']['rebound-local']is None
r=views['2023-07-31'];cmp=next(x for x in r['local_comparisons']if x['older']=='lower-local'and x['later']=='rebound-local')
assert cmp['both_common_edges_higher']and cmp['raw_price_ranges_overlap']
assert r['local_activities']['rebound-local']['zone']['raw_path_frame']['observed_low']=='36.80'
assert r['local_activities']['earlier-local']['current_vs_common']=='BELOW'
assert '2023-08-03' in s['source_gaps']['known_calendar_missing_dates'] and max(views)=='2023-08-02'
# Published old cutoff views must survive appending a future source bar.
extended=copy.deepcopy(s);extended['bars'].append({'date':'2099-01-01','open':'1','high':'999','low':'0','close':'1','volume_shares_scaled':'0'})
assert all(project(extended,c,cut)==r for cut,r in views.items())
provenance=json.loads((ROOT/'source-provenance.json').read_text())
for x in provenance['inputs']:assert hashlib.sha256(Path(x['local']).read_bytes()).hexdigest()==x['sha256']
assert hashlib.sha256((ROOT/'study-inputs.json').read_bytes()).hexdigest()==provenance['new_selection_file_sha256']
write('verification.json',{'status':'PASS_SCOPED_CONTEXT_STUDY','cutoff_views':13,'source_prefix_checks':13,'future_price_volume_and_manual_poison_checks':13,'unavailable_zone_context_point_geometry_poison_checks':13,'future_append_keeps_old_views':13,'formal_and_action_fields_not_promoted':13,'selected_local_source_and_common_geometry_independent_checks':3,'pair_source_freshness_checks':3,'exact_chronology_and_semantic_counterexamples':10,'source_hashes_verified':7,'new_driver_runs':1,'new_verifier_runs':1,'old_drivers_verifiers_and_product_tests_rerun':0,'market_classifier':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD','selection':'EX_POST_OVERLAPPING_CONTEXT_STUDY_NOT_BLIND_SCAN_OR_SUCCESS_RATE'})
print('PASS: 13 cutoffs, isolation/append, exact source geometry and chronology; no formal promotion')
