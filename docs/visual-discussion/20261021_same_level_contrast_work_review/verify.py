"""Verify price evidence and matched-cohort limits without supplying merge answers."""
import copy,json,gzip
from decimal import Decimal as D
from pathlib import Path
from study import ROOT,SOURCE,REGISTRY,CUTS,select,observe,loc,sha,write

def main():
 reg=json.loads(gzip.decompress(REGISTRY.read_bytes()));data=select(reg);bars=json.loads(SOURCE.read_text())['bars'];final=json.loads((ROOT/'contrast-evidence.json').read_text());n=0
 for cut in CUTS:
  current=observe(bars,data,cut);prefix=[b for b in bars if b['date']<=cut];future=copy.deepcopy(bars);vol=copy.deepcopy(bars);geometry=copy.deepcopy(data);labels=copy.deepcopy(data)
  for b in future:
   if b['date']>cut:b.update(open='9900',high='9999',low='1',close='9998',volume_shares_scaled='9999999999')
  for b in vol:b['volume_shares_scaled']='1'
  for z in geometry['zones'].values():
   if z['known_on_saved_bar']>cut:z.update(zone_id='UNKNOWN_FUTURE_ID',common_close_low='9000',common_close_high='9999',raw_path_frame={},leg_ids=['UNKNOWN_FUTURE_LEG'])
  labels['original_nested_B_answer']={'formal_merge':True,'user_approved_all':True};labels['latest_volume_decision']={'low_volume_means_failure':True}
  assert current==observe(prefix,data,cut)==observe(future,data,cut)==observe(vol,data,cut)==observe(bars,geometry,cut)==observe(bars,labels,cut)
  assert all(f['bar']['date']<=cut for f in current['price_history'])
  assert all(a['birth']['known_on']<=cut for a in current['activities'].values())
  for name,a in current['activities'].items():assert a['birth']==final['activities'][name]['birth']
  if cut=='2026-02-10':
   assert 'close_inside'not in current['activities']
   assert current['price_history'][-1]['close_on_or_inside_reference']
  n+=1
 # Original dependency geometry and source data, independent of the display view.
 for z in data['zones'].values():
  ls=[data['legs'][i]for i in z['leg_ids']];bs=[b for b in bars if z['path_start']<=b['date']<=z['path_end']]
  assert len(bs)==z['raw_path_frame']['records']
  assert max(D(l['close_low'])for l in ls)==D(z['common_close_low'])and min(D(l['close_high'])for l in ls)==D(z['common_close_high'])
  assert max(l['known_on_saved_bar']for l in ls)==z['known_on_saved_bar']
  assert min(D(b['low'])for b in bs)==D(z['raw_path_frame']['observed_low'])and max(D(b['high'])for b in bs)==D(z['raw_path_frame']['observed_high'])
  assert next(b for b in bars if b['date']==z['known_on_saved_bar'])==z['right_evidence_bar']
 inside=final['activities']['close_inside']['birth']['later_source_facts_vs_reference'];outside=final['activities']['sides_crossed']['birth']['later_source_facts_vs_reference']
 assert len(inside)==9 and[f['bar']['date']for f in inside if f['close_on_or_inside_reference']]==['2026-02-10']
 assert len(outside)==5 and not any(f['close_on_or_inside_reference']for f in outside)
 hits=[f for f in outside if f['daily_range_intersects_reference']]
 assert [f['bar']['date']for f in hits]==['2026-03-04','2026-03-05']
 assert[(f['bar']['date'],f['adjacent_saved_close_sides_crossing'])for f in outside if f['adjacent_saved_close_sides_crossing']]==[('2026-03-04','DOWN_ACROSS_BOTH_BOUNDARIES'),('2026-03-05','UP_ACROSS_BOTH_BOUNDARIES')]
 assert hits[0]['bar']['close']=='33.65'and hits[1]['bar']['close']=='34.05'
 assert hits[1]['bar']['low']=='33.75'
 for f in inside+outside:assert not f['intraday_order_or_continuous_trade_path_inferred']
 q=json.loads((ROOT/'registry-query.json').read_text());assert q['eligible_saved_pairs']==len(q['eligible_pairs'])==434
 assert q['same_later_common_bounds']['nonoverlapping_later_source_contrast_combinations']==0
 assert q['same_coarse_relations']['nonoverlapping_later_source_contrast_combinations']==93
 zm={z['zone_id']:z for z in reg['zones']};lm={l['leg_id']:l for l in reg['legs']};tm={t['turn_id']:t for t in reg['turns']}
 expected_visits={}
 for row in q['eligible_pairs']:
  a,b=zm[row['older_zone_id']],zm[row['later_zone_id']]
  assert a['path_start']>= '2025-11-06'and b['known_on_saved_bar']<='2026-05-29'
  assert not any(z['path_start']<='2026-04-27'and z['path_end']>='2026-04-16'for z in(a,b))
  turns={lm[i][k]for i in b['leg_ids']for k in ('from_turn_id','to_turn_id')}
  assert min(tm[i]['left_evidence_date']for i in turns)>a['known_on_saved_bar']
  visit=any(D(a['common_close_low'])<=D(x['close'])<=D(a['common_close_high'])for x in bars if b['path_start']<=x['date']<=b['path_end'])
  assert visit==row['has_saved_source_close_inside_old_common'];expected_visits[(row['older_zone_id'],row['later_zone_id'])]=visit
 # Independently count the two matching schemes from the published eligible rows.
 grouped={}
 for row in q['eligible_pairs']:grouped.setdefault(row['older_zone_id'],[]).append(row)
 strict=coarse=0
 for rows in grouped.values():
  yes=[r for r in rows if r['has_saved_source_close_inside_old_common']];no=[r for r in rows if not r['has_saved_source_close_inside_old_common']]
  for a in yes:
   for b in no:
    za,zb=zm[a['later_zone_id']],zm[b['later_zone_id']]
    if za['path_end']>=zb['path_start']and zb['path_end']>=za['path_start']:continue
    coarse+=1
    if(za['common_close_low'],za['common_close_high'])==(zb['common_close_low'],zb['common_close_high']):strict+=1
 assert(strict,coarse)==(0,93)
 for name in ('close_inside','sides_crossed'):
  assert expected_visits[(data['zones']['reference']['zone_id'],data['zones'][name]['zone_id'])]==(name=='close_inside')
 a,b=[data['zones'][n]for n in('close_inside','sides_crossed')];assert a['path_end']<b['path_start']
 def tids(z):return{lm[i][k]for i in z['leg_ids']for k in('from_turn_id','to_turn_id')}
 assert not(set(a['leg_ids'])&set(b['leg_ids']))and not(tids(a)&tids(b))
 assert data['original_nested_B_answer']['adjudication']=='ANSWERED_NESTED_LARGE_AND_SMALL_BANDS'
 assert data['original_nested_B_answer']['formal_small_band_membership_and_bounds']is None
 prov=json.loads((ROOT/'source-provenance.json').read_text())
 for s in prov['inputs']:assert sha(Path(s['local']))==s['sha256']
 write('verification.json',{'status':'PASS','cutoff_checks':n,'prefix_future_price_volume_and_geometry_poison':True,'manual_answers_not_inputs_to_price_view':True,'volume_one_no_veto':True,'immutable_activity_births':True,'three_original_source_and_leg_geometry_oracles':True,'434_eligible_rows_actual_close_visits_independently_checked':True,'strict_0_and_coarse_93_disjoint_contrasts_recounted':True,'selected_later_sources_disjoint_and_no_shared_leg_turn':True,'no_close_inside_but_two_contact_and_side_cross_dates':True,'price_event_available_before_later_activity_birth':True,'original_B_nested_answer_preserved':True,'same_level_approved_positive_negative_labels':None,'formal_merge_validated':False,'source_hashes_verified':4,'old_core_driver_verifier_product_browser_Android_downloads':0})
 print('PASS: 11 cutoff views; 3 fixed sources; 434 rows checked; strict0/coarse93 recount; no formal merge labels invented')
if __name__=='__main__':main()
