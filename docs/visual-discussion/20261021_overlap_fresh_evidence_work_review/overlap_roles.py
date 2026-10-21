"""Compare saved common-price candidates by source reuse and fresh later evidence.

Pure research relations, not formal region merging or an interval classifier.
"""
import gzip,hashlib,json
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent
SOURCE=Path('/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json')
COMPARISON=Path('/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json')
def sha(b):return hashlib.sha256(b).hexdigest()
def uid(x):return 'sha256:'+sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def inputs():
 s=json.loads(SOURCE.read_text());t=json.loads(COMPARISON.read_text())
 r=json.loads(gzip.decompress((BASE/'source-role-research/source-role-registry.json.gz').read_bytes()))
 c=json.loads(gzip.decompress((BASE/'common-band-research/pool-common-span-registry.json.gz').read_bytes()))
 selected=json.loads((BASE/'common-band-research/selected-common-spans.json').read_text())
 turns={x['turn_id']:x for x in c['turns']};legs={x['leg_id']:x for x in c['legs']}
 for obs in selected.values():
  for x in obs['turns']:
   if x['turn_id']in turns:assert turns[x['turn_id']]==x
   turns[x['turn_id']]=x
  for x in obs['legs']:
   if x['leg_id']in legs:assert legs[x['leg_id']]==x
   legs[x['leg_id']]=x
 scopes={key:{'code':o['code'],'cutoff':o['cutoff'],'zone_ids':[c['zones'][i]['zone_id']for i in o['zone_indices']]}for key,o in c['observations'].items()}
 scopes.update({'selected:'+name:{'code':o['code'],'cutoff':o['cutoff'],'zone_ids':[z['zone_id']for z in o['zones']]}for name,o in selected.items()})
 return {'2884':s,'1101':t},r['zones'],turns,legs,scopes,selected
def evidence_start(z,turns,legs):return turns[legs[z['leg_ids'][0]]['from_turn_id']]['left_evidence_date']
def turn_ids(z,legs):return set(i for lid in z['leg_ids']for i in [legs[lid]['from_turn_id'],legs[lid]['to_turn_id']])
def price_relation(al,ah,bl,bh):
 a,b,c,d=map(D,[al,ah,bl,bh])
 return 'LATER_RANGE_STRICTLY_ABOVE'if c>b else'LATER_RANGE_STRICTLY_BELOW'if d<a else'TOUCH_ONLY'if max(a,c)==min(b,d)else'POSITIVE_PRICE_OVERLAP'
def fields(older,later,turns,legs,visits,gaps):
 shared_legs=sorted(set(older['leg_ids'])&set(later['leg_ids']))
 shared_turns=sorted(turn_ids(older,legs)&turn_ids(later,legs));begin=evidence_start(later,turns,legs)
 freshness='SHARED_COMPLETED_LEG'if shared_legs else'NO_SHARED_LEG_BUT_SOURCE_PERIOD_REUSED'if begin<=older['known_on_saved_bar']else'ALL_LATER_SOURCE_AFTER_OLDER_KNOWN'
 common=price_relation(older['common_close_low'],older['common_close_high'],later['common_close_low'],later['common_close_high'])
 raw=price_relation(older['raw_path_frame']['observed_low'],older['raw_path_frame']['observed_high'],later['raw_path_frame']['observed_low'],later['raw_path_frame']['observed_high'])
 if freshness=='SHARED_COMPLETED_LEG':role='LINKED_EXISTING_PATH_NOT_FRESH_CORROBORATION'
 elif freshness=='NO_SHARED_LEG_BUT_SOURCE_PERIOD_REUSED':role='ADDITIONAL_LEGS_WITH_REUSED_SOURCE_CONTEXT'
 elif common=='POSITIVE_PRICE_OVERLAP':role='FRESH_TWO_WAY_PATH_WITH_COMMON_PRICES'
 elif common=='TOUCH_ONLY':role='FRESH_TWO_WAY_PATH_AT_PRICE_CONTACT'
 elif raw=='POSITIVE_PRICE_OVERLAP':role='FRESH_PRICE_MIGRATION_WITH_OVERLAPPING_WICKS'
 elif raw=='TOUCH_ONLY':role='FRESH_PRICE_MIGRATION_WITH_WICK_CONTACT'
 else:role='FRESH_PATH_WITH_SEPARATED_RAW_RANGE_NOT_FORMAL_REGION'
 r={'code':older['code'],'older_zone_id':older['zone_id'],'later_zone_id':later['zone_id'],'known_on_saved_bar':later['known_on_saved_bar'],
    'later_source_evidence_start':begin,'freshness':freshness,'shared_leg_ids':shared_legs,'shared_turn_ids':shared_turns,
    'common_price_relation':common,'raw_price_relation':raw,'role_candidate':role,'actual_later_path_close_visits_older_core':visits,
    'listed_gaps_between_confirmations':gaps,
    'formal_interval':None,'formal_merge':None,'formal_split':None,'formal_parent':None,'selected_role':None,'primary_pressure_id':None}
 r['comparison_id']=uid(r);return r
def compare(source,older,later,turns,legs,cutoff):
 if source['code']!=older['code']or older['code']!=later['code']:raise ValueError('Same source code required')
 if older['known_on_saved_bar']>=later['known_on_saved_bar']:raise ValueError('Strictly later confirmation required; same-day candidates are not ordered')
 if later['known_on_saved_bar']>cutoff:raise ValueError('Later candidate not available')
 visits=[{'date':b['date'],'close':b['close']}for b in source['bars']if later['path_start']<=b['date']<=later['path_end']and D(older['common_close_low'])<=D(b['close'])<=D(older['common_close_high'])]
 gaps=[d for d in source['source_gaps']['known_calendar_missing_dates']if older['known_on_saved_bar']<d<=later['known_on_saved_bar']]
 return fields(older,later,turns,legs,visits,gaps)
def pack(zones,turns,legs,records,scopes):
 zi={z['zone_id']:i for i,z in enumerate(zones)};visits=[];gaps=[];vi={};gi={};rows=[]
 for r in records:
  v=json.dumps(r['actual_later_path_close_visits_older_core'],sort_keys=True,separators=(',',':'));g=tuple(r['listed_gaps_between_confirmations'])
  if v not in vi:vi[v]=len(visits);visits.append(r['actual_later_path_close_visits_older_core'])
  if g not in gi:gi[g]=len(gaps);gaps.append(list(g))
  rows.append([zi[r['older_zone_id']],zi[r['later_zone_id']],vi[v],gi[g]])
 return {'layout':'SAVED_ZONE_PAIRS_FULLY_RECONSTRUCTABLE_WITHOUT_EXTERNAL_OHLC_NO_RANKING','zones':zones,'turns':list(turns.values()),'legs':list(legs.values()),
         'pair_columns':['older_zone_index','later_zone_index','actual_close_visit_set_index','listed_gap_set_index'],'pairs':rows,
         'actual_close_visit_sets':visits,'listed_gap_sets':gaps,'scopes':scopes,
         'reconstruction':'expand_pair() restores every immutable comparison and its content-derived ID from these tables; zero-based indices are storage only.'}
def expand_pair(p,row):
 a,b,v,g=row;tm={t['turn_id']:t for t in p['turns']};lm={l['leg_id']:l for l in p['legs']}
 return fields(p['zones'][a],p['zones'][b],tm,lm,p['actual_close_visit_sets'][v],p['listed_gap_sets'][g])
def location(c,lo,hi):
 p,a,b=map(D,[c,lo,hi]);return'BELOW'if p<a else'ABOVE'if p>b else'AT_LOW'if p==a else'AT_HIGH'if p==b else'INSIDE'
def observe(source,older,later,turns,legs,cutoff):
 last=next(b for b in reversed(source['bars'])if b['date']<=cutoff)
 out={'cutoff':cutoff,'last_bar':last,'comparison':None,'current_close_vs_older_core':None,'current_close_vs_later_core':None,
      'first_post_comparison_close_visit_older_core':None,'qualification':'RETROSPECTIVE_SAVED_CANDIDATE_COMPARISON_NOT_BLIND_SCAN',
      'historical_selection_time':None,'historical_signal_eligible':False,'classification':'NOT_VALIDATED','core_usefulness':'NOT_ESTABLISHED',
      'actions':'NOT_EVALUATED','capital_growth_flywheel_effectiveness':'NOT_EVALUATED','Android':'NOT_TESTED_NEW_BUILD'}
 if older['known_on_saved_bar']<=cutoff:out['current_close_vs_older_core']=location(last['close'],older['common_close_low'],older['common_close_high'])
 if later['known_on_saved_bar']>cutoff:return out
 out['comparison']=compare(source,older,later,turns,legs,cutoff)
 out['current_close_vs_later_core']=location(last['close'],later['common_close_low'],later['common_close_high'])
 out['first_post_comparison_close_visit_older_core']=next(({'date':b['date'],'close':b['close']}for b in source['bars']if later['known_on_saved_bar']<b['date']<=cutoff and D(older['common_close_low'])<=D(b['close'])<=D(older['common_close_high'])),None)
 return out
def main():
 src,zones,turns,legs,scopes,selected=inputs();zi={z['zone_id']:i for i,z in enumerate(zones)};pairs=set();same_day=set()
 for o in scopes.values():
  ids=[zi[i]for i in o['zone_ids']]
  for offset,i in enumerate(ids):
   for j in ids[offset+1:]:
    a,b=zones[i],zones[j]
    if a['known_on_saved_bar']==b['known_on_saved_bar']:same_day.add(tuple(sorted([i,j])));continue
    if a['known_on_saved_bar']<b['known_on_saved_bar']:pairs.add((i,j))
    else:pairs.add((j,i))
 records=[compare(src[zones[i]['code']],zones[i],zones[j],turns,legs,zones[j]['known_on_saved_bar'])for i,j in sorted(pairs)]
 pi={(zi[r['older_zone_id']],zi[r['later_zone_id']]):i for i,r in enumerate(records)}
 snapshots={key:{**o,'zone_indices':[zi[i]for i in o['zone_ids']]}for key,o in scopes.items()}
 for o in snapshots.values():del o['zone_ids']
 # Normalized rows retain only non-derivable provenance/details; read with expand().
 packed=pack(zones,turns,legs,records,snapshots)
 raw=json.dumps(packed,ensure_ascii=False,separators=(',',':')).encode();gz=gzip.compress(raw,mtime=0);(ROOT/'overlap-role-registry.json.gz').write_bytes(gz)
 def choose(name,start,end):return next(z for z in selected[name]['zones']if z['path_start']==start and z['path_end']==end)
 oldabc=max(selected['ABC-May13']['zones'],key=lambda z:z['leg_count']);newabc=choose('ABC-Jun2','2025-05-19','2025-05-23')
 g1=choose('G2-full-manual-scope','2023-01-17','2023-01-31');g2=choose('G2-full-manual-scope','2023-02-06','2023-02-09')
 bs=selected['B-May4'];maxids={v['zone_id']for v in bs['zone_views']if v['available_maximal_contiguous_span']};b1,b2=sorted([z for z in bs['zones']if z['zone_id']in maxids],key=lambda z:z['known_on_saved_bar'])
 a1=selected['A-Oct7']['zones'][0];a2=next(z for z in zones if z['code']=='2884'and z['path_start']=='2026-10-05'and z['path_end']=='2026-10-08')
 query_groups={'ABC-fresh-lower':(oldabc,newabc,['2025-05-23','2025-05-26','2025-06-02']),
               'G2-fresh-overlap':(g1,g2,['2023-02-09','2023-02-10','2023-02-20']),
               'B-shared-path':(b1,b2,['2026-04-27','2026-04-28','2026-05-04']),
               'A-reused-context':(a1,a2,['2026-10-08','2026-10-12','2026-10-16'])}
 details={name+'-'+cut:observe(src[a['code']],a,b,turns,legs,cut)for name,(a,b,cuts)in query_groups.items()for cut in cuts}
 write(ROOT/'selected-comparisons.json',details)
 write(ROOT/'selected-query-specs.json',{name:{'older_zone_id':a['zone_id'],'later_zone_id':b['zone_id'],'cutoffs':cuts,'selection':'EX_POST_ILLUSTRATIVE_NOT_HISTORICAL_CHOICE'}for name,(a,b,cuts)in query_groups.items()})
 summary={'saved_scopes':len(scopes),'unique_saved_zones':len(zones),'unique_saved_turns':len(turns),'unique_saved_legs':len(legs),'directed_comparisons':len(records),
          'same_known_day_pairs_not_ordered':len(same_day),'freshness':dict(Counter(r['freshness']for r in records)),
          'role_candidates':dict(Counter(r['role_candidate']for r in records)),
          'fresh_overlap_without_actual_path_close_visit':sum(r['freshness']=='ALL_LATER_SOURCE_AFTER_OLDER_KNOWN'and r['common_price_relation']=='POSITIVE_PRICE_OVERLAP'and not r['actual_later_path_close_visits_older_core']for r in records),
          'pairs_with_listed_gaps_between_confirmations':sum(bool(r['listed_gaps_between_confirmations'])for r in records),
          'registry_gzip_bytes':len(gz),'registry_raw_sha256':sha(raw),'selected_queries':len(details),'new_driver_runs':1,
          'formal_interval_classifier':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD','capital_growth_flywheel_effectiveness':'NOT_EVALUATED'}
 write(ROOT/'summary.json',summary)
 paths=[SOURCE,COMPARISON,BASE/'source-role-research/source-role-registry.json.gz',BASE/'common-band-research/pool-common-span-registry.json.gz',BASE/'common-band-research/selected-common-spans.json']
 write(ROOT/'source-provenance.json',{'files':{str(p):{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}for p in paths},'original_core_recomputations':0,'prior_driver_reruns':0})
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
