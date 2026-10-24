"""Cutoff leakage and exact cross-case counterexamples; no product validation."""
import copy,hashlib,json
from decimal import Decimal as D
from pathlib import Path
from study import ROOT,SOURCES,G2,project,findings,write,turns,left
c=json.loads((ROOT/'study-inputs.json').read_text());sources={code:json.loads(p.read_text())for code,p in SOURCES.items()};views=json.loads((ROOT/'cross-case-views.json').read_text());geometries=set();relations=set()
for key,r in views.items():
    case,cut=r['case'],r['cutoff'];s=sources[r['code']]
    assert project(s,c,case,cut)==r
    prefix=copy.deepcopy(s);prefix['bars']=[b for b in prefix['bars']if b['date']<=cut]
    assert project(prefix,c,case,cut)==r
    poison=copy.deepcopy(s);poison['manual_labels']={'A_approved':True,'ABC_end':'2025-06-02','force_main':True}
    for b in poison['bars']:
        if b['date']>cut:b.update(open='999',high='999',low='-999',close='999',volume_shares_scaled='9999999999')
    assert project(poison,c,case,cut)==r
    cc=copy.deepcopy(c)
    for z in cc['cases'][case]['zones'].values():
        if z['known_on_saved_bar']>cut:z.update(common_close_low='-999',common_close_high='999',leg_ids=['FUTURE'],path_start='1900-01-01',path_end='2099-01-01')
    for p in cc['cases'][case]['points'].values():
        if p['known_on']>cut:p.update(price='999',source_dates=['2099-01-01'])
    assert project(s,cc,case,cut)==r
    extension=copy.deepcopy(s);extension['bars'].append({'date':'2099-01-01','open':'999','high':'999','low':'-999','close':'999','volume_shares_scaled':'0'})
    assert project(extension,c,case,cut)==r
    for name,item in r['activities'].items():
        if item is None:continue
        z=item['zone'];ps=[b for b in prefix['bars']if z['path_start']<=b['date']<=z['path_end']];ls=[c['legs'][i]for i in z['leg_ids']]
        assert len(ps)==z['raw_path_frame']['records']and min(D(b['low'])for b in ps)==D(z['raw_path_frame']['observed_low'])and max(D(b['high'])for b in ps)==D(z['raw_path_frame']['observed_high'])
        assert max(D(l['close_low'])for l in ls)==D(z['common_close_low'])and min(D(l['close_high'])for l in ls)==D(z['common_close_high'])
        assert z['known_on_saved_bar']<=cut and all(l['known_on_saved_bar']<=cut for l in ls)
        geometries.add(z['zone_id'])
    for rel in r['activity_comparisons']:
        a,b=[c['cases'][case]['zones'][rel[k]]for k in ['earlier','later']]
        assert rel['shared_turn_ids']==sorted(turns(a,c)&turns(b,c))
        assert not rel['independence_or_importance_inferred'];relations.add((case,rel['earlier'],rel['later']))
    for name in ['formal_pattern','formal_structure_change','formal_parent','formal_end','formal_reaction','importance_score','independent_confirmation_count','primary_pressure_id']:assert r[name]is None
    assert not r['historical_signal_eligible']and not r['manual_labels_used']
def v(case,cut):return views[case+'@'+cut]
# ABC: locally weaker activity while ranges overlap; later close-through precedes new outside activity.
r=v('ABC','2025-05-26');p=next(p for p in r['activity_comparisons']if p['earlier']=='earlier'and p['later']=='lower')
assert p['both_common_edges_lower']and p['raw_ranges_overlap']and p['later_complete_source_after_earlier_known']and not p['shared_turn_ids']
assert v('ABC','2025-05-13')['points']['high']is None and v('ABC','2025-05-13')['current_bar']['high']=='31.40'
assert v('ABC','2025-05-14')['points']['high']['point']['price']=='31.40'
r=v('ABC','2025-06-02');assert r['current_bar']['close']=='27.70'and r['points']['low']['current_close_side']=='BELOW'and r['points']['low']['current_daily_range_contains_point']
assert r['activities']['earlier']['current_close_vs_raw']=='BELOW'and r['activities']['outside']is None
assert v('ABC','2025-06-03')['activities']['earlier']['whole_current_daily_range_vs_raw']=='BELOW'
assert v('ABC','2025-06-11')['activities']['outside']is None
assert v('ABC','2025-06-12')['activities']['outside']['zone']['common_close_high']=='27.30'
# A: local reclaim, equality, strict cross and source reuse are separate facts.
assert v('A','2026-10-06')['activities']['lower']['current_close_vs_common']=='ABOVE'and v('A','2026-10-06')['activities']['earlier']['current_close_vs_common']=='BELOW'
r=v('A','2026-10-14');assert r['current_bar']['close']=='47.30'and r['activities']['earlier']['current_close_vs_common']=='AT_HIGH'and r['points']['high']['current_close_side']=='BELOW'
r=v('A','2026-10-15');assert r['points']['high']['current_close_side']=='ABOVE'and not r['points']['high']['current_daily_range_contains_point']
assert r['activities']['earlier']['current_close_vs_common']=='ABOVE'and r['activities']['earlier']['current_close_vs_raw']=='ABOVE'and r['activities']['earlier']['whole_current_daily_range_vs_raw']=='ABOVE'
assert r['points']['high']['first_saved_close_above_from_availability']['date']=='2026-10-15'
assert r['earlier_activity_high_source_binding']['shared_raw_high_source_dates']==['2026-09-17']
assert v('A','2026-10-16')['current_bar']['close']=='49.15'and v('A','2026-10-16')['points']['high']['current_close_side']=='ABOVE'
shared=next(x for x in v('A','2026-10-12')['activity_comparisons']if x['earlier']=='lower'and x['later']=='later')
assert shared['shared_turn_ids']and not shared['later_complete_source_after_earlier_known']
# Cross-case claims are grounded in the saved G2 projection, not a rerun of its engine.
g2=json.loads(G2.read_text());out=json.loads((ROOT/'cross-case-findings.json').read_text());assert findings(views,g2)==out
assert out['G2']['relative_to_earlier_common']=='BELOW'and out['A']['relative_to_earlier_common']=='ABOVE'and out['ABC']['relative_to_earlier_common']=='BELOW'
provenance=json.loads((ROOT/'source-provenance.json').read_text())
for x in provenance['inputs']:assert hashlib.sha256(Path(x['local']).read_bytes()).hexdigest()==x['sha256']
assert hashlib.sha256((ROOT/'study-inputs.json').read_bytes()).hexdigest()==provenance['selection_sha256']
write('verification.json',{'status':'PASS_FINITE_CROSS_CASE_READING','cutoff_views':len(views),'prefix_checks':len(views),'future_price_volume_and_manual_poison_checks':len(views),'unavailable_geometry_poison_checks':len(views),'future_append_old_views_preserved':len(views),'formal_fields_not_promoted':len(views),'unique_local_geometries_checked':len(geometries),'unique_pair_source_relations_checked':len(relations),'explicit_ABC_A_chronology_equality_cross_and_source_reuse_assertions':'PASS','G2_saved_projection_findings_not_recomputed':'PASS','source_hashes_verified':6,'new_driver_runs':1,'new_verifier_runs':1,'old_drivers_verifiers_product_tests_rerun':0,'classifier':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD'})
print('PASS: 21 cutoff views, 6 local geometries, chronology/equality/cross/reuse and prior G2 projection')
