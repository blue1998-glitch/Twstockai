"""Verify composition joins, time projection, stale archives and label isolation."""
import copy,gzip,json
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
from observation_bundle import ROOT,load_inputs,compose,project_history,unpack_snapshots,location,sha,write
src,c=load_inputs();saved=unpack_snapshots(json.loads(gzip.decompress((ROOT/'observation-bundles.json.gz').read_bytes())),c)
specs=json.loads((ROOT/'query-specs.json').read_text());counts=Counter();pm={p['comparison_id']:p for p in c['pairs']};evm={e['event_id']:e for e in c['events']};zm={z['zone_id']:z for z in c['zones']};lm={l['link_id']:l for l in c['followup_links']}
for name,r in saved.items():
 s=src[r['code']];start,cut=r['requested_seed_start'],r['requested_cutoff'];prefix=[b for b in s['bars']if b['date']<=cut];last=prefix[-1]
 assert r==compose(s,start,cut,c);assert r['last_bar']==last
 assert r['observation_records']==sum(start<=b['date']<=cut for b in s['bars'])
 eligible=[]
 for z in c['zones']:
  if z['code']!=r['code']or z['known_on_saved_bar']>cut:continue
  tids={tid for lid in z['leg_ids']for tid in [c['legs'][lid]['from_turn_id'],c['legs'][lid]['to_turn_id']]}
  if min(c['turns'][t]['left_evidence_date']for t in tids)>=start:eligible.append(z)
 ids={z['zone_id']for z in eligible};assert ids=={v['zone_id']for v in r['local_activity_views']}
 for v in r['local_activity_views']:
  z=zm[v['zone_id']];assert v['current_close_vs_common']==location(last['close'],z['common_close_low'],z['common_close_high'])
  assert v['current_close_vs_raw_path']==location(last['close'],z['raw_path_frame']['observed_low'],z['raw_path_frame']['observed_high'])
  assert v['maximal_available_saved_path_view']==(not any(set(z['leg_ids'])<set(q['leg_ids'])for q in eligible));counts['local_zone_view_checks']+=1
 expected={p['comparison_id']:p['role_candidate']for p in c['pairs']if p['older_zone_id']in ids and p['later_zone_id']in ids and p['known_on_saved_bar']<=cut}
 got={i:role for role,items in r['archived_pair_role_buckets'].items()for i in items};assert got==expected;counts['archived_pair_joins']+=len(got)
 possible=sum(a['known_on_saved_bar']!=b['known_on_saved_bar']for i,a in enumerate(eligible)for b in eligible[i+1:])
 assert r['known_zone_pairs_without_archived_comparison']==possible-len(expected)>=0
 pivots=[p for p in c['pivots']if p['code']==r['code']and p['known_on']<=cut]
 contexts=[q for q in c['contexts']if q['code']==r['code']and q['known_on']<=cut]
 assert {p['id']for p in pivots}=={v['pivot_id']for v in r['retained_original_pivot_views']}
 assert {q['context_id']for q in contexts}=={v['context_id']for v in r['retained_original_context_views']}
 pv={v['pivot_id']:v for v in r['retained_original_pivot_views']}
 for p in pivots:
  candidates=[b for b in prefix if b['date']>=p['known_on']and(D(b['close'])>D(p['price'])if p['kind']=='HIGH'else D(b['close'])<D(p['price']))]
  expected_hit={'date':candidates[0]['date'],'close':candidates[0]['close']}if candidates else None
  assert pv[p['id']]['first_saved_crossing_from_availability']==expected_hit
  assert pv[p['id']]['current_close_relation']==location(last['close'],p['price'],p['price']);counts['retained_pivot_and_first_crossing_checks']+=1
 cv={v['context_id']:v for v in r['retained_original_context_views']}
 for q in contexts:assert cv[q['context_id']]['current_close_vs_research_bounds']==location(last['close'],q['low'],q['high']);counts['retained_context_checks']+=1
 eventids={e['event_id']for e in c['events']if e['code']==r['code']and e['known_on_saved_bar']<=cut and e['frozen_frame']['frame_start']>=start}
 assert eventids=={v['event_id']for v in r['departure_return_views']};eps={}
 for v in r['departure_return_views']:
  e=evm[v['event_id']];h=c['histories'][e['event_id']];covered=min(cut,h['archive_observed_through']);f=e['frozen_frame']
  assert v['history']['observed_through']==covered and v['history']['covers_requested_cutoff']==(h['archive_observed_through']>=cut)
  assert v['current_close_vs_frozen_frame']==location(last['close'],f['lower'],f['upper'])
  assert {ep['episode_id']for ep in v['history']['episodes']}=={ep['episode_id']for ep in h['episodes']if ep['start']<=covered}
  original={ep['episode_id']:ep for ep in h['episodes']}
  for ep in v['history']['episodes']:
   arch=original[ep['episode_id']];ending=arch['ended_on']if arch['ended_on']is not None and arch['ended_on']<=covered else None
   assert ep['ended_on']==ending
   expected_status='ENDED_AT_SAVED_EVENT'if ending is not None else'OPEN_THROUGH_REQUESTED_CUTOFF'if covered==cut else'OPEN_AT_ARCHIVE_END_CURRENT_CONTINUITY_UNKNOWN'
   assert ep['current_evidence_status']==expected_status
   for key in ['first_whole_bar_on_side','first_boundary_contact']:
    assert ep[key]==(arch[key]if arch[key]is not None and arch[key]<=covered else None)
   assert ep['last_observed_outside_close']<=covered
   bs=[b for b in prefix if ep['start']<=b['date']<=ep['last_observed_outside_close']]
   assert all(D(b['close'])>D(f['upper'])if e['direction']=='UP'else D(b['close'])<D(f['lower'])for b in bs)
   eps[ep['episode_id']]=ep;counts['cutoff_episode_projection_checks']+=1
  counts['event_archive_coverage_checks']+=1
 expected_links={l['link_id']for l in c['followup_links']if l['event_id']in eventids and l['zone_id']in ids and l['known_on']<=cut}
 assert expected_links=={v['link_id']for v in r['separated_followup_views']}
 for v in r['separated_followup_views']:
  l=lm[v['link_id']];assert v['status_at_birth']==l['status_at_birth'];assert v['current_episode_evidence']==eps.get(l['episode_id'],{}).get('current_evidence_status','NO_PROJECTED_ARCHIVE_EPISODE_CURRENT_UNKNOWN');counts['followup_join_and_current_status_checks']+=1
 assert r['source_qualification']['listed_missing_dates_in_observation']==[d for d in s['source_gaps']['known_calendar_missing_dates']if start<=d<=cut]
 for key in ['formal_interval','formal_start','formal_end','formal_membership','formal_parent','formal_merge','selected_role','primary_pressure_id','historical_selection_time','original_core_snapshot_2026_10_07','numeric_frame_2026_10_07']:assert r[key]is None
 assert r['historical_signal_eligible']is False;counts['snapshot_checks']+=1
 # Truncation and future payload poison. Original archive coverage metadata stays fixed.
 short={**s,'bars':[copy.deepcopy(b)for b in prefix]};assert compose(short,start,cut,c)==r;counts['source_prefix_truncation_checks']+=1
 poison={**s,'bars':copy.deepcopy(s['bars']),'source_gaps':copy.deepcopy(s['source_gaps']),'manual_case_audit':{'POISON':'CHANGE_ALL_MANUAL_LABELS'},'core':{'POISON':'NOT_AN_INPUT'}}
 for b in poison['bars']:
  if b['date']>cut:b.update(close='99999',low='-99999',high='999999',open='99999')
 poison['source_gaps']['known_calendar_missing_dates']+=['2099-01-01']
 pc={**c,'pivots':[({**p,'price':'999999'}if p['known_on']>cut else p)for p in c['pivots']],
     'contexts':[({**q,'low':'-999999','high':'999999'}if q['known_on']>cut else q)for q in c['contexts']],
     'zones':[({**z,'common_close_low':'-999999','common_close_high':'999999'}if z['known_on_saved_bar']>cut else z)for z in c['zones']],
     'histories':copy.deepcopy(c['histories']),'manual_review':{'ALL_CASES':'POISON_NOT_AN_INPUT'}}
 for h in pc['histories'].values():
  for ep in h['episodes']:
   for key in ['first_whole_bar_on_side','first_boundary_contact','last_observed_outside_close','ended_on']:
    if ep[key]is not None and ep[key]>cut:ep[key]='2099-01-01'
   if ep['ended_on']=='2099-01-01':ep['end_reason']='POISON_FUTURE_END'
 assert compose(poison,start,cut,pc)==r;counts['future_and_manual_label_poison_checks']+=1

for group,sp in specs.items():
 previous=None
 for cut in sp['cutoffs']:
  r=saved[group+'-'+cut]
  if previous:
   assert {v['zone_id']for v in previous['local_activity_views']}<={v['zone_id']for v in r['local_activity_views']}
   assert {v['pivot_id']for v in previous['retained_original_pivot_views']}<={v['pivot_id']for v in r['retained_original_pivot_views']}
   oldpairs={i for ids in previous['archived_pair_role_buckets'].values()for i in ids};newpairs={i for ids in r['archived_pair_role_buckets'].values()for i in ids};assert oldpairs<=newpairs
   now={v['pivot_id']:v for v in r['retained_original_pivot_views']}
   for v in previous['retained_original_pivot_views']:
    if v['first_saved_crossing_from_availability']is not None:assert v['first_saved_crossing_from_availability']==now[v['pivot_id']]['first_saved_crossing_from_availability']
   counts['append_preserves_prior_evidence_checks']+=1
  previous=r

# Synthetic stale archive: current close is outside again after an unarchived return.
bars=[{'date':f'2040-01-{i:02}','open':str(v),'high':str(v+1),'low':str(v-1),'close':str(v),'volume_shares_scaled':'1'}for i,v in [(1,9),(2,11),(3,12),(4,12),(5,9),(6,11),(7,12)]]
s={'code':'SYNTHETIC','bars':bars,'source_gaps':{'known_calendar_missing_dates':[]}}
e={'event_id':'e','code':'SYNTHETIC','known_on_saved_bar':'2040-01-03','direction':'UP','frozen_frame':{'frame_start':'2040-01-01','lower':'0','upper':'10'}}
ep={'episode_id':'ep','start':'2040-01-02','previous_listed_gap':None,'first_whole_bar_on_side':'2040-01-03','first_boundary_contact':'2040-01-02','last_observed_outside_close':'2040-01-04','ended_on':None,'end_reason':None}
cat={'zones':[],'turns':{},'legs':{},'pairs':[],'events':[e],'histories':{'e':{'archive_observed_through':'2040-01-04','episodes':[ep]}},'followup_links':[],'pivots':[],'contexts':[]}
r=compose(s,'2040-01-01','2040-01-07',cat);v=r['departure_return_views'][0];assert v['current_close_vs_frozen_frame']=='ABOVE'and v['history']['episodes'][0]['current_evidence_status']=='OPEN_AT_ARCHIVE_END_CURRENT_CONTINUITY_UNKNOWN'
future=copy.deepcopy(cat);future['histories']['e']['archive_observed_through']='2040-01-07';future['histories']['e']['episodes'][0].update(ended_on='2040-01-05',end_reason='CLOSE_RETURN_INSIDE');future['histories']['e']['episodes'].append({**ep,'episode_id':'future-episode','start':'2040-01-06','last_observed_outside_close':'2040-01-07','first_whole_bar_on_side':'2040-01-07','first_boundary_contact':'2040-01-06'})
v=compose(s,'2040-01-01','2040-01-04',future)['departure_return_views'][0]['history'];assert len(v['episodes'])==1 and v['episodes'][0]['ended_on']is None
try:compose(s,'2040-01-07','2040-01-01',cat);raise AssertionError('must reject reversed window')
except ValueError:pass
counts['synthetic_staleness_future_end_and_reversed_window_checks']=3

high=next(p for p in c['pivots']if p['code']=='2884'and p['scale']=='0.03'and p['occurred_at']=='2026-09-17')
av={v['pivot_id']:v for v in saved['A-2026-10-16']['retained_original_pivot_views']};assert av[high['id']]['first_saved_crossing_from_availability']=={'date':'2026-10-15','close':'48.80'}
gaps=saved['G2-2023-08-16']['source_qualification']['listed_missing_dates_in_observation'];assert '2023-08-03'in gaps
assert saved['ABC-2025-06-13']['observation_records']==48 and saved['ABC-2025-06-02']['observation_records']==39
assert saved['ABC-2025-06-13']['known_zone_pairs_without_archived_comparison']==0
counts['selected_scope_reference_gap_unknown_assertions']=4
for path,info in json.loads((ROOT/'source-provenance.json').read_text())['files'].items():assert sha(Path(path).read_bytes())==info['sha256'];counts['unchanged_input_hashes']+=1
expected={'overlap-role-research/overlap-role-registry.json.gz':'ab016b7c32ac0c80674d5235d4c23b76a75da345b9fe5a356b8f297ed03e953c','followup-role-research/followup-role-registry.json.gz':'e3769c491f1fe9c5862c56ca3114b2cb8aac3d2e09080d1dcf55e8bb3a2f36ca','source-role-research/source-role-registry.json.gz':'d337e10f56586c493f9cc4d608040181fc5a98bdc37845b0f106dec8da1b9cea'}
for path,h in expected.items():assert sha(gzip.decompress((ROOT.parent/path).read_bytes()))==h
# Supplemental work must preserve baseline facts and be validated separately.
baseline=unpack_snapshots(json.loads(gzip.decompress((ROOT/'baseline-observation-bundles.json.gz').read_bytes())),c)
for name,old in baseline.items():
 now=saved[name]
 for key in ['local_activity_views','retained_original_pivot_views','retained_original_context_views','observation_raw_extent','observation_records','last_bar','source_qualification']:assert now[key]==old[key]
 assert {i for ids in old['archived_pair_role_buckets'].values()for i in ids}<={i for ids in now['archived_pair_role_buckets'].values()for i in ids}
 counts['baseline_facts_preserved_after_extension']+=1
x=json.loads(gzip.decompress((ROOT/'evidence-extensions.json.gz').read_bytes()))
for item in x['trace_extension_receipts']:assert item['prior_prefix_exactly_preserved'];counts['extended_trace_prior_prefix_checks']+=1
for p in x['new_comparisons']:
 a,b=zm[p['older_zone_id']],zm[p['later_zone_id']];s=src[p['code']]
 assert p['known_on_saved_bar']==b['known_on_saved_bar']and a['known_on_saved_bar']<b['known_on_saved_bar']
 assert D(b['common_close_high'])<D(a['common_close_low'])
 assert p['actual_later_path_close_visits_older_core']==[{'date':bar['date'],'close':bar['close']}for bar in s['bars']if b['path_start']<=bar['date']<=b['path_end']and D(a['common_close_low'])<=D(bar['close'])<=D(a['common_close_high'])]
 counts['supplemental_pair_timing_geometry_visit_checks']+=1
assert all(r['known_zone_pairs_without_archived_comparison']==0 for r in saved.values())
assert all(v['history']['covers_requested_cutoff']for r in saved.values()for v in r['departure_return_views'])
write(ROOT/'verification.json',{'status':'PASS','checks':dict(counts),'new_composer_driver_runs':3,'lossless_storage_conversion_runs':1,'new_verifier_runs':2,'extension_generator_runs':1,'prior_drivers_or_product_tests_rerun':0,'new_seed_turn_or_original_core_generation':0,'supplemental_evidence':x['summary'],'classification':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD','capital_growth_flywheel_effectiveness':'NOT_EVALUATED'})
print(json.dumps(dict(counts)))
