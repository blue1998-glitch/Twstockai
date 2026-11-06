"""Audit six fixed activity sources and new causal relationship views."""
import copy,gzip,json
from decimal import Decimal as D
from study import ROOT,SOURCE_PATHS,REGISTRY,SOURCE_REGISTRY,CUTS,CODE,select,observe,sha,interval,write

def main():
 data=select();sources={k:json.loads(p.read_text())for k,p in SOURCE_PATHS.items()};checks=0
 final=json.loads((ROOT/'activity-evidence.json').read_text())
 for case,cuts in CUTS.items():
  for cut in cuts:
   actual=observe(sources,data,case,cut)
   prefix=copy.deepcopy(sources);poisoned=copy.deepcopy(sources);lowvol=copy.deepcopy(sources);future=copy.deepcopy(data)
   for code,s in prefix.items():s['bars']=[b for b in s['bars']if b['date']<=cut]
   for s in poisoned.values():
    for b in s['bars']:
     if b['date']>cut:b.update(open='9990',high='9999',low='1',close='9998',volume_shares_scaled='999999999')
   for s in lowvol.values():
    for b in s['bars']:b['volume_shares_scaled']='1'
   for z in future['zones'].values():
    if z['known_on_saved_bar']>cut:z.update(zone_id='FUTURE_MUST_NOT_APPEAR',common_close_low='999',common_close_high='1000',raw_path_frame={},leg_ids=['FUTURE_LEG'])
   for r in future['references'][case]:
    if r['known_on']>cut:r.update(low='999',high='1000')
   for e in future['prior_price_events'][case]:
    if e['date']>cut:e['bar']={'future':'hidden'}
   assert actual==observe(prefix,data,case,cut)==observe(poisoned,data,case,cut)==observe(lowvol,data,case,cut)==observe(sources,future,case,cut)
   for name,fact in actual['available_activities'].items():assert fact==final[case]['available_activities'][name]
   for name,pair in actual['available_pairs'].items():assert pair==final[case]['available_pairs'][name]
   assert all(z['available_on']<=cut for z in actual['available_activities'].values())
   assert actual['formal_merge']is None and actual['formal_larger_structure_change']is None
   checks+=1
 # Independently reconstruct source spans and birth geometry from dependent legs/turns.
 for name,z in data['zones'].items():
  ls=[data['legs'][i]for i in z['leg_ids']]
  assert max(D(x['close_low'])for x in ls)==D(z['common_close_low'])
  assert min(D(x['close_high'])for x in ls)==D(z['common_close_high'])
  assert max(x['known_on_saved_bar']for x in ls)==z['known_on_saved_bar']
  for leg in ls:
   a,b=[data['turns'][leg[k]]for k in ('from_turn_id','to_turn_id')]
   assert sorted([D(a['close']),D(b['close'])])==[D(leg['close_low']),D(leg['close_high'])]
 # Exact oracles expose two different returns, shared origins, and source/current separation.
 b=final['B'];g=final['G2'];ba,bh,br=[b['available_activities'][k]for k in ('B_advance','B_high','B_return')]
 assert [x['common']for x in (ba,bh,br)]==[['33.65','34.20'],['35.40','35.50'],['35.00','35.45']]
 assert ba['against_references']['small_raw_high_proxy']['source_close_counts']=={'ABOVE':7,'EQUAL':0,'BELOW':0}
 assert ba['against_references']['small_raw_high_proxy']['raw_relation']=='STRADDLES_REFERENCE'
 assert bh['against_references']['broader_raw_high_proxy']['common_relation']=='BOUNDARY_TOUCH'
 assert br['against_references']['broader_raw_high_proxy']['source_close_counts']=={'ABOVE':2,'EQUAL':0,'BELOW':2}
 assert br['against_references']['broader_raw_high_proxy']['common_relation']=='STRICTLY_BELOW'
 assert br['against_references']['broader_raw_high_proxy']['raw_relation']=='STRADDLES_REFERENCE'
 for key,date in [('B_advance_B_high','2026-06-17'),('B_high_B_return','2026-06-22')]:
  p=b['available_pairs'][key];assert len(p['shared_turn_ids'])==1 and date in p['shared_source_bar_dates']
 p=b['available_pairs']['B_advance_B_return'];assert not p['shared_leg_ids']and not p['shared_turn_ids']and not p['all_later_left_evidence_after_older_known']
 p=g['available_pairs']['G_lower_G_rebound'];assert p['all_later_left_evidence_after_older_known']and not p['shared_turn_ids']and p['raw_relation_later_vs_earlier']=='POSITIVE_OVERLAP'
 p=g['available_pairs']['G_earlier_G_rebound'];v=p['actual_later_source_visits']
 assert v['later_source_close_in_earlier_common_dates']==[]
 assert v['later_source_range_intersects_earlier_common_dates']==[]
 assert v['later_source_close_in_earlier_raw_dates']==['2023-07-25','2023-07-26','2023-07-27','2023-07-28']
 assert len(v['later_source_range_intersects_earlier_raw_dates'])==4
 assert g['current_activity_locations']['G_earlier']['raw_location']=='BOUNDARY_TOUCH'
 born=observe(sources,data,'B','2026-06-26');assert born['current_price_bar']['close']=='34.55'
 assert born['current_activity_locations']['B_return']=={'common_location':'STRICTLY_BELOW','raw_location':'STRICTLY_BELOW'}
 assert g['current_activity_locations']['G_rebound']['common_location']=='STRICTLY_BELOW'
 assert g['current_reference_locations']['local_original_low']['close_relation']=='STRICTLY_ABOVE'
 assert interval('35.4','35.5','35.5','35.5')=='BOUNDARY_TOUCH'
 assert interval('35.5','35.5','35.5','35.5')=='EQUAL'
 assert interval('35','36','35.5','35.5')=='STRADDLES_REFERENCE'
 assert interval('37.2','37.2','37.2','38.5')=='BOUNDARY_TOUCH'
 assert interval('37.3','37.3','37.2','38.5')=='INSIDE_REFERENCE_RANGE'
 prov=json.loads((ROOT/'source-provenance.json').read_text())
 for row in prov['inputs']:assert sha(__import__('pathlib').Path(row['local']))==row['sha256']
 # Zone metadata is exact in two frozen registries, not invented by this study.
 for registry in (REGISTRY,SOURCE_REGISTRY):
  original={z['zone_id']:z for z in json.loads(gzip.decompress(registry.read_bytes()))['zones']}
  for z in data['zones'].values():assert z==original[z['zone_id']]
 write('verification.json',{'status':'PASS','case_cutoffs':checks,'six_activity_raw_source_and_leg_turn_birth_oracles':True,'six_pair_source_and_actual_visit_oracles':True,'prefix_future_price_volume_and_unavailable_geometry_poison':True,'all_volume_one_no_price_evidence_veto':True,'activity_and_pair_births_append_without_rewrite':True,'G2_all_four_source_closes_back_in_earlier_raw_but_none_in_common':True,'B_return_confirmation_day_already_below_source_range':True,'source_reuse_and_source_freshness_not_independence_or_merge':True,'strict_equal_touch_and_range_location_oracles':5,'original_metadata_equal_in_two_registries':True,'source_hashes_verified':7,'original_crossing_volume_core_or_old_driver_verifier_reruns':0,'product_browser_Android_tests_or_downloads':0,'formal_classifier_or_merge_validated':False})
 print('PASS: 14 cutoff views; 6 frozen activities and 6 pairs; actual raw/common return distinction; no formal merge validated')
if __name__=='__main__':main()
