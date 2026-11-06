"""Independent pair/source checks, prefix isolation and semantic edge cases."""
import copy,gzip,json
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
from overlap_roles import ROOT,inputs,compare,observe,expand_pair,sha,uid,write
src,zones,tm,lm,scopes,prior=inputs();p=json.loads(gzip.decompress((ROOT/'overlap-role-registry.json.gz').read_bytes()));selected=json.loads((ROOT/'selected-comparisons.json').read_text());specs=json.loads((ROOT/'selected-query-specs.json').read_text());zm={z['zone_id']:z for z in zones};counts=Counter()
assert p['zones']==zones and {t['turn_id']:t for t in p['turns']}==tm and {l['leg_id']:l for l in p['legs']}==lm
expected=set();same=set()
for scope in scopes.values():
 ids=[next(i for i,z in enumerate(zones)if z['zone_id']==zid)for zid in scope['zone_ids']]
 for off,a in enumerate(ids):
  for b in ids[off+1:]:
   if zones[a]['known_on_saved_bar']==zones[b]['known_on_saved_bar']:same.add(tuple(sorted([a,b])))
   elif zones[a]['known_on_saved_bar']<zones[b]['known_on_saved_bar']:expected.add((a,b))
   else:expected.add((b,a))
assert {(r[0],r[1])for r in p['pairs']}==expected;counts['scope_pair_membership_checks']=len(expected);counts['same_known_day_pairs_left_unordered']=len(same)
frames={}
for z in zones:
 bs=[b for b in src[z['code']]['bars']if z['path_start']<=b['date']<=z['path_end']]
 frames[z['zone_id']]=(min(D(b['low'])for b in bs),max(D(b['high'])for b in bs))
 assert frames[z['zone_id']]==(D(z['raw_path_frame']['observed_low']),D(z['raw_path_frame']['observed_high']));counts['saved_raw_frames']=counts['saved_raw_frames']+1
for row in p['pairs']:
 a,b=zones[row[0]],zones[row[1]];r=expand_pair(p,row);s=src[a['code']]
 # Independently compare endpoint pair identities, rather than just shared leg IDs.
 aa={(lm[l]['from_turn_id'],lm[l]['to_turn_id'])for l in a['leg_ids']};bb={(lm[l]['from_turn_id'],lm[l]['to_turn_id'])for l in b['leg_ids']}
 commonpaths=aa&bb;at={t for x in aa for t in x};bt={t for x in bb for t in x}
 assert bool(commonpaths)==bool(r['shared_leg_ids'])and sorted(at&bt)==r['shared_turn_ids']
 all_left=[tm[t]['left_evidence_date']for t in bt];begin=min(all_left)
 assert r['later_source_evidence_start']==begin
 fresh='SHARED_COMPLETED_LEG'if commonpaths else'NO_SHARED_LEG_BUT_SOURCE_PERIOD_REUSED'if begin<=a['known_on_saved_bar']else'ALL_LATER_SOURCE_AFTER_OLDER_KNOWN'
 assert r['freshness']==fresh
 def independent_relation(lo,hi,newlo,newhi):
  if newlo>hi:return'LATER_RANGE_STRICTLY_ABOVE'
  if newhi<lo:return'LATER_RANGE_STRICTLY_BELOW'
  if newlo==hi or newhi==lo:return'TOUCH_ONLY'
  return'POSITIVE_PRICE_OVERLAP'
 oldlo,oldhi=D(a['common_close_low']),D(a['common_close_high']);newlo,newhi=D(b['common_close_low']),D(b['common_close_high'])
 assert r['common_price_relation']==independent_relation(oldlo,oldhi,newlo,newhi)
 assert r['raw_price_relation']==independent_relation(*frames[a['zone_id']],*frames[b['zone_id']])
 actual=[{'date':bar['date'],'close':bar['close']}for bar in s['bars']if b['path_start']<=bar['date']<=b['path_end']and oldlo<=D(bar['close'])<=oldhi]
 assert actual==r['actual_later_path_close_visits_older_core']
 assert r['listed_gaps_between_confirmations']==[d for d in s['source_gaps']['known_calendar_missing_dates']if a['known_on_saved_bar']<d<=b['known_on_saved_bar']]
 assert uid({k:v for k,v in r.items()if k!='comparison_id'})==r['comparison_id']
 assert compare(s,a,b,tm,lm,b['known_on_saved_bar'])==r
 counts['independent_full_comparison_reconstructions']+=1

seen=set()
for group,sp in specs.items():
 a,b=zm[sp['older_zone_id']],zm[sp['later_zone_id']];s=src[a['code']]
 final=observe(s,a,b,tm,lm,sp['cutoffs'][-1]);born=b['known_on_saved_bar']
 for cut in sp['cutoffs']:
  r=observe(s,a,b,tm,lm,cut);assert selected[group+'-'+cut]==r;counts['selected_reconstructions']+=1
  poison=copy.deepcopy(s);pt=copy.deepcopy(tm)
  for bar in poison['bars']:
   if bar['date']>cut:bar.update(close='999999',high='9999999',low='-999999',open='888888')
  poison['source_gaps']['known_calendar_missing_dates']+=['2099-01-01']
  for t in pt.values():
   if t['known_on_saved_bar']>cut:t['close']='777777';t['left_evidence_date']='2099-01-01'
  pb=copy.deepcopy(b)
  if born>cut:pb['common_close_low']='-999999';pb['common_close_high']='999999';pb['raw_path_frame'].update(observed_low='-999999',observed_high='999999')
  assert observe(poison,a,pb,pt,lm,cut)==r;counts['future_bar_turn_zone_gap_poison_checks']+=1
  if cut<born:assert r['comparison']is None and b['zone_id']not in json.dumps(r);counts['unavailable_candidate_metadata_not_exposed']+=1
  else:assert r['comparison']==final['comparison']
 # All saved cutoffs; no later comparison metadata or visits leak into prefixes.
 for bar in s['bars']:
  cut=bar['date'];key=(a['zone_id'],b['zone_id'],cut)
  if not a['known_on_saved_bar']<=cut<=sp['cutoffs'][-1]or key in seen:continue
  seen.add(key);v=observe(s,a,b,tm,lm,cut);short=copy.deepcopy(s);short['bars']=[q for q in short['bars']if q['date']<=cut]
  assert observe(short,a,b,tm,lm,cut)==v
  if v['comparison']is not None:assert v['comparison']==final['comparison']
  counts['prefix_truncation_and_immutable_birth_checks']+=1
 # Synthetic positive affine prices preserve relation and actual visit dates.
 ts=copy.deepcopy(s);ta=copy.deepcopy(a);tb=copy.deepcopy(b)
 for bar in ts['bars']:
  for field in ['open','high','low','close']:bar[field]=str(D(bar[field])*3+7)
 for z in [ta,tb]:
  for field in ['common_close_low','common_close_high']:z[field]=str(D(z[field])*3+7)
  for field in ['observed_low','observed_high']:z['raw_path_frame'][field]=str(D(z['raw_path_frame'][field])*3+7)
 r1=compare(s,a,b,tm,lm,born);r2=compare(ts,ta,tb,tm,lm,born)
 for field in ['freshness','common_price_relation','raw_price_relation','role_candidate','later_source_evidence_start']:assert r1[field]==r2[field]
 assert [v['date']for v in r1['actual_later_path_close_visits_older_core']]==[v['date']for v in r2['actual_later_path_close_visits_older_core']]
 counts['positive_affine_comparison_checks']+=1

# Synthetic endpoint-domain overlap does not mean any saved close visited that domain.
turns={k:{'left_evidence_date':d}for k,d in [('a','2040-01-01'),('b','2040-01-01'),('c','2040-01-02'),('d','2040-01-04'),('e','2040-01-05'),('f','2040-01-06')]}
legs={'a1':{'from_turn_id':'a','to_turn_id':'b'},'a2':{'from_turn_id':'b','to_turn_id':'c'},'b1':{'from_turn_id':'d','to_turn_id':'e'},'b2':{'from_turn_id':'e','to_turn_id':'f'}}
old={'code':'SYNTHETIC','zone_id':'old','known_on_saved_bar':'2040-01-03','leg_ids':['a1','a2'],'common_close_low':'10','common_close_high':'11','raw_path_frame':{'observed_low':'9','observed_high':'12'}}
new={'code':'SYNTHETIC','zone_id':'new','known_on_saved_bar':'2040-01-08','path_start':'2040-01-05','path_end':'2040-01-07','leg_ids':['b1','b2'],'common_close_low':'9','common_close_high':'12','raw_path_frame':{'observed_low':'8','observed_high':'13'}}
source={'code':'SYNTHETIC','bars':[{'date':f'2040-01-{i:02}','close':c}for i,c in [(5,'9'),(6,'12'),(7,'9'),(8,'10.5')]],'source_gaps':{'known_calendar_missing_dates':[]}}
r=compare(source,old,new,turns,legs,'2040-01-08');assert r['common_price_relation']=='POSITIVE_PRICE_OVERLAP'and not r['actual_later_path_close_visits_older_core']
touch=copy.deepcopy(new);touch['common_close_low']='11';touch['common_close_high']='12';assert compare(source,old,touch,turns,legs,'2040-01-08')['common_price_relation']=='TOUCH_ONLY'
reused=copy.deepcopy(turns);reused['d']['left_evidence_date']='2040-01-03';assert compare(source,old,new,reused,legs,'2040-01-08')['freshness']=='NO_SHARED_LEG_BUT_SOURCE_PERIOD_REUSED'
shared=copy.deepcopy(new);shared['leg_ids']=['a2','b1'];assert compare(source,old,shared,turns,legs,'2040-01-08')['freshness']=='SHARED_COMPLETED_LEG'
gap=copy.deepcopy(source);gap['source_gaps']['known_calendar_missing_dates']=['2040-01-04'];assert compare(gap,old,new,turns,legs,'2040-01-08')['listed_gaps_between_confirmations']==['2040-01-04']
for mutation in ['same_day','unavailable','different_stock']:
 z=copy.deepcopy(new);cut='2040-01-08'
 if mutation=='same_day':z['known_on_saved_bar']=old['known_on_saved_bar']
 elif mutation=='unavailable':cut='2040-01-07'
 else:z['code']='OTHER'
 try:compare(source,old,z,turns,legs,cut);raise AssertionError('must reject '+mutation)
 except ValueError:pass
counts['synthetic_edge_cases']=8
assert selected['ABC-fresh-lower-2025-05-26']['comparison']['role_candidate']=='FRESH_PRICE_MIGRATION_WITH_OVERLAPPING_WICKS'
assert selected['G2-fresh-overlap-2023-02-10']['comparison']['actual_later_path_close_visits_older_core']
assert selected['B-shared-path-2026-04-28']['comparison']['freshness']=='SHARED_COMPLETED_LEG'
assert selected['A-reused-context-2026-10-12']['comparison']['freshness']=='NO_SHARED_LEG_BUT_SOURCE_PERIOD_REUSED'
counts['selected_semantic_assertions']=4
for path,info in json.loads((ROOT/'source-provenance.json').read_text())['files'].items():assert sha(Path(path).read_bytes())==info['sha256'];counts['unchanged_source_hashes']+=1
assert sha(Path('/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json').read_bytes())=='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
assert sha(Path('/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json').read_bytes())=='184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15'
assert sha(gzip.decompress((ROOT.parent/'common-band-research/pool-common-span-registry.json.gz').read_bytes()))=='f66907bc82be08637f4e15fbf3b2343ce38b869c9aa91bec48d893ffcd52af12'
write(ROOT/'verification.json',{'status':'PASS','checks':dict(counts),'new_driver_runs':1,'storage_reconstruction_conversion_runs':1,'new_verification_runs':1,'prior_driver_or_product_test_reruns':0,'original_core_recomputations':0,'classification':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD','capital_growth_flywheel_effectiveness':'NOT_EVALUATED'})
print(json.dumps(dict(counts)))
