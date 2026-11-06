"""Completed-close common-span research. Never selects formal intervals.

All adjacent spans with positive shared close-price width remain as evidence.
Available maximal spans are views, not immutable selection or formal parents.
"""
from pathlib import Path
from decimal import Decimal as D
from itertools import combinations
import argparse,json,gzip,hashlib

canon=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
digest=lambda x:'sha256:'+hashlib.sha256(canon(x)).hexdigest()

def common(source,start,cutoff,revisit_episodes=None):
 rows=[b for b in source['bars']if start<=b['date']<=cutoff]
 if not rows or rows[0]['date']!=start or rows[-1]['date']!=cutoff:raise ValueError('saved scope dates required')
 declared=source['source_gaps']['known_calendar_missing_dates'];segments=[];segment=[]
 for b in rows:
  if segment and any(segment[-1]['date']<=g<=b['date']for g in declared):segments.append(segment);segment=[]
  segment.append(b)
 if segment:segments.append(segment)
 turns=[];legs=[];zones=[];zone_views=[];segment_leg_lists=[]
 for segment in segments:
  runs=[]
  for b in segment:
   if runs and D(b['close'])==D(runs[-1][-1]['close']):runs[-1].append(b)
   else:runs.append([b])
  local_turns=[]
  for prev,cur,nxt in zip(runs,runs[1:],runs[2:]):
   a,b,c=[D(run[0]['close'])for run in [prev,cur,nxt]]
   if not(a<b>c or a>b<c):continue
   turn={'code':source['code'],'kind':'HIGH'if a<b else'LOW','plateau_start':cur[0]['date'],'plateau_end':cur[-1]['date'],
      'close':cur[0]['close'],'left_evidence_date':prev[-1]['date'],'known_on_saved_bar':nxt[0]['date'],
      'qualification':'NEW_COMPLETED_CLOSE_TURN_NOT_ORIGINAL_PIVOT'}
   turn['turn_id']=digest(turn);local_turns.append(turn);turns.append(turn)
  local_legs=[]
  for left,right in zip(local_turns,local_turns[1:]):
   low,high=sorted([D(left['close']),D(right['close'])])
   leg={'code':source['code'],'from_turn_id':left['turn_id'],'to_turn_id':right['turn_id'],
       'path_start':left['plateau_start'],'path_end':right['plateau_end'],'known_on_saved_bar':right['known_on_saved_bar'],
       'close_low':str(low),'close_high':str(high),'direction':'UP'if D(right['close'])>D(left['close'])else'DOWN',
       'qualification':'COMPLETED_CLOSE_ENDPOINT_SPAN_NOT_INTRADAY_TRADE_PATH'}
   leg['leg_id']=digest(leg);local_legs.append(leg);legs.append(leg)
  segment_leg_lists.append(local_legs)
  for i in range(len(local_legs)-1):
   lo,hi=D(local_legs[i]['close_low']),D(local_legs[i]['close_high'])
   for j in range(i+1,len(local_legs)):
    lo,hi=max(lo,D(local_legs[j]['close_low'])),min(hi,D(local_legs[j]['close_high']))
    if lo>=hi:break
    used=local_legs[i:j+1];path_start=used[0]['path_start'];path_end=used[-1]['path_end'];known=used[-1]['known_on_saved_bar']
    raw=[b for b in rows if path_start<=b['date']<=path_end];low=min(D(b['low'])for b in raw);high=max(D(b['high'])for b in raw)
    z={'code':source['code'],'leg_ids':[leg['leg_id']for leg in used],'leg_count':len(used),'path_start':path_start,'path_end':path_end,
       'known_on_saved_bar':known,'common_close_low':str(lo),'common_close_high':str(hi),
       'raw_path_frame':{'observed_low':str(low),'observed_high':str(high),'records':len(raw),'bars_fingerprint':digest(raw),
          'low_origin_dates':[b['date']for b in raw if D(b['low'])==low],'high_origin_dates':[b['date']for b in raw if D(b['high'])==high]},
       'right_evidence_bar':next(b for b in rows if b['date']==known),
       'formal_price_bounds':None,'formal_interval':None,'formal_membership':None,
       'qualification':'SHARED_COMPLETED_CLOSE_SPAN_RESEARCH_ONLY_NOT_TRADE_DENSITY_OR_FORMAL_BOX'}
    z['zone_id']=digest(z);zones.append(z)
    canleft=i>0 and max(lo,D(local_legs[i-1]['close_low']))<min(hi,D(local_legs[i-1]['close_high']))
    canright=j+1<len(local_legs)and max(lo,D(local_legs[j+1]['close_low']))<min(hi,D(local_legs[j+1]['close_high']))
    last=rows[-1];c,l,h=[D(last[k])for k in ['close','low','high']];crossed=[g for g in declared if path_start<=g<=cutoff]
    zone_views.append({'zone_id':z['zone_id'],'available_maximal_contiguous_span':not canleft and not canright,
       'latest_close_to_common_span':'INSIDE_INCLUSIVE'if lo<=c<=hi else'BELOW'if c<lo else'ABOVE',
       'latest_bar_to_common_span':'WHOLE_BELOW'if h<lo else'WHOLE_ABOVE'if l>hi else'OVERLAPS_OR_TOUCHES',
       'crossed_listed_missing_dates':crossed,'source_qualified_for_current_relation':False if crossed else None,'selected':None})
 maximal_ids={v['zone_id']for v in zone_views if v['available_maximal_contiguous_span']}
 maximal=[z for z in zones if z['zone_id']in maximal_ids];relations=[]
 for left,right in combinations(maximal,2):
  shared=sorted(set(left['leg_ids'])&set(right['leg_ids']))
  if not shared:continue
  lo=max(D(left['common_close_low']),D(right['common_close_low']));hi=min(D(left['common_close_high']),D(right['common_close_high']))
  rel={'left_zone_id':left['zone_id'],'right_zone_id':right['zone_id'],'shared_leg_ids':shared,
       'common_span_relation':'POSITIVE_OVERLAP'if lo<hi else'TOUCH_ONLY'if lo==hi else'DISJOINT',
       'direction_of_disjoint_shift':('DOWN'if D(right['common_close_high'])<D(left['common_close_low'])else'UP')if lo>hi else None,
       'known_on_saved_bar':max(left['known_on_saved_bar'],right['known_on_saved_bar']),
       'formal_merge':None,'qualification':'SHARED_PATH_IS_NOT_SHARED_PRICE_CORE_OR_FORMAL_PARENTAGE'}
  rel['relation_id']=digest(rel);relations.append(rel)
 # Join only already-saved revisit witnesses available at the zone's birth.
 # Three side visits must be within its path+right-evidence window; price in core.
 links=[]
 if revisit_episodes is not None:
  for z in zones:
   matches=[e['episode_id']for e in revisit_episodes if e['code']==source['code']and
       D(z['common_close_low'])<=D(e['anchor_price'])<=D(z['common_close_high'])and
       z['path_start']<=e['strict_side_visits'][0]['date']and e['known_on_saved_bar']<=z['known_on_saved_bar']]
   links.append({'zone_id':z['zone_id'],'revisit_episode_ids':sorted(matches),'qualification':'SAVED_SOURCE_PROVENANCE_LINK_NOT_INDEPENDENT_VOTES'})
 return {'schema':'m1-common-close-span-research/0.1','code':source['code'],'seed_start':start,'cutoff':cutoff,'source_records':len(rows),
    'source_bars_fingerprint':digest(rows),'source_segments':[[seg[0]['date'],seg[-1]['date']]for seg in segments],
    'turns':turns,'legs':legs,'zones':zones,'zone_views':zone_views,'maximal_shared_path_relations':relations,'saved_revisit_links':links,
    'revisit_link_input_status':'PROVIDED_SAVED_WITNESSES_ONLY'if revisit_episodes is not None else'NOT_PROVIDED_NOT_ZERO_WITNESSES',
    'source_observation_frame':{'observed_low':str(min(D(b['low'])for b in rows)),'observed_high':str(max(D(b['high'])for b in rows)),
                              'qualification':'WHOLE_REQUESTED_OBSERVATION_ONLY_NOT_FORMAL_PARENT_BOUNDS'},
    'formal_interval':None,'formal_start':None,'formal_end':None,'formal_membership':None,'selected_zone':None,
    'primary_pressure_id':None,'historical_selection_time':None,'historical_signal_eligible':False,
    'classification':'NOT_VALIDATED','core_usefulness':'NOT_ESTABLISHED','actions':'NOT_EVALUATED'}

def brief(r):
 maximal=[z for z,v in zip(r['zones'],r['zone_views'])if v['available_maximal_contiguous_span']]
 return {'records':r['source_records'],'turns':len(r['turns']),'completed_legs':len(r['legs']),'all_common_span_candidates':len(r['zones']),
    'available_maximal_spans':[{'low':z['common_close_low'],'high':z['common_close_high'],'path_start':z['path_start'],'path_end':z['path_end'],'known_on':z['known_on_saved_bar'],'legs':z['leg_count']}for z in maximal],
    'shared_path_disjoint_cores':sum(x['common_span_relation']=='DISJOINT'for x in r['maximal_shared_path_relations']),
    'formal_formation_rule':'NOT_ESTABLISHED'}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--prior-dir',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
 p=Path(a.out);p.mkdir(parents=True,exist_ok=True);sraw=Path(a.source).read_bytes();traw=Path(a.comparison).read_bytes()
 assert hashlib.sha256(sraw).hexdigest()=='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
 assert hashlib.sha256(traw).hexdigest()=='184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15'
 s,t=map(json.loads,[sraw,traw]);prior=Path(a.prior_dir);prior_packed=(prior/'pool-revisit-registry.json.gz').read_bytes();prior_raw=gzip.decompress(prior_packed)
 assert hashlib.sha256(prior_raw).hexdigest()=='dac09001f9afae5370ae1369d440291464ffac784ad59a64ab888763217e8cc7'
 saved=json.loads(prior_raw);old_selected=json.loads((prior/'selected-revisits.json').read_text())
 registry={'layout':'IMMUTABLE_TABLES_PLUS_CURRENT_SNAPSHOT; views/relations/revisit links reconstructed without loss',
           'turns':{},'legs':{},'zones':{},'revisit_episode_id_table':[e['episode_id']for e in saved['episode_table']],
           'prior_revisit_raw_sha256':hashlib.sha256(prior_raw).hexdigest(),'observations':{}};pool_summary=[]
 for obs_id,obs in saved['observations'].items():
  src=s if obs['code']=='2884'else t;episodes=[saved['episode_table'][i]for i in obs['episode_indices']];r=common(src,obs['seed_start'],obs['cutoff'],episodes)
  for key,kind in [('turn_id','turns'),('leg_id','legs'),('zone_id','zones')]:
   for item in r[kind]:assert registry[kind].setdefault(item[key],item)==item
  registry['observations'][obs_id]={'code':src['code'],'seed_start':obs['seed_start'],'cutoff':obs['cutoff'],
    'turn_ids':[x['turn_id']for x in r['turns']],'leg_ids':[x['leg_id']for x in r['legs']],
    'zone_ids':[x['zone_id']for x in r['zones']],
    'maximal_zone_ids':[v['zone_id']for v in r['zone_views']if v['available_maximal_contiguous_span']],
    'revisit_episode_indices':obs['episode_indices'],'latest_bar':obs['latest_bar'],
    'listed_missing_dates_in_observation':obs['listed_missing_dates_in_observation'],'source_segments':r['source_segments']}
  pool_summary.append({'observation_id':obs_id,'code':src['code'],'seed_start':obs['seed_start'],'cutoff':obs['cutoff'],'turns':len(r['turns']),'legs':len(r['legs']),'zone_count':len(r['zones']),'maximal_count':sum(v['available_maximal_contiguous_span']for v in r['zone_views'])})
 specs=[('A-Oct5',s,'2026-09-17','2026-10-05','2884-Oct7'),('A-Oct6',s,'2026-09-17','2026-10-06','2884-Oct7'),('A-Oct7',s,'2026-09-17','2026-10-07','2884-Oct7'),
  ('B-Apr23',s,'2026-04-15','2026-04-23','2884-control-May4'),('B-Apr24',s,'2026-04-15','2026-04-24','2884-control-May4'),('B-Apr28',s,'2026-04-15','2026-04-28','2884-control-May4'),('B-May4',s,'2026-04-15','2026-05-04','2884-control-May4'),
  ('ABC-May13',t,'2025-04-07','2025-05-13','ABC-reviewed-Jun2'),('ABC-Jun2',t,'2025-04-07','2025-06-02','ABC-reviewed-Jun2'),
  ('ABC-next-Jun11',t,'2025-06-03','2025-06-11','ABC-followup-Jun13'),('ABC-next-Jun12',t,'2025-06-03','2025-06-12','ABC-followup-Jun13'),('ABC-next-Jun13',t,'2025-06-03','2025-06-13','ABC-followup-Jun13'),
  ('G2-Feb20',t,'2023-01-16','2023-02-20','G2-through-Mar3'),('G2-Mar3',t,'2023-01-16','2023-03-03','G2-through-Mar3'),('G2-full-manual-scope',t,'2023-01-16','2023-08-16',None),('A-last-bar',s,'2026-10-16','2026-10-16','2884-last-seed')]
 selected={name:common(src,start,cut,[e for e in old_selected[old]['episodes']if e['known_on_saved_bar']<=cut]if old else None)for name,src,start,cut,old in specs}
 # Index immutable objects and keep only current-view data once per observation.
 for kind,id_key,obs_key in [('turns','turn_id','turn_ids'),('legs','leg_id','leg_ids'),('zones','zone_id','zone_ids')]:
  order=list(registry[kind]);lookup={key:i for i,key in enumerate(order)};registry[kind]=[registry[kind][key]for key in order]
  for obs in registry['observations'].values():
   obs[obs_key.replace('_ids','_indices')]=[lookup[key]for key in obs.pop(obs_key)]
   if kind=='zones':obs['maximal_zone_indices']=[lookup[key]for key in obs.pop('maximal_zone_ids')]
 packed=gzip.compress((json.dumps(registry,ensure_ascii=False,separators=(',',':'))+'\n').encode(),mtime=0)
 (p/'pool-common-span-registry.json.gz').write_bytes(packed)
 summary={'pool_observations':len(registry['observations']),'unique_turns':len(registry['turns']),'unique_legs':len(registry['legs']),'unique_zones':len(registry['zones']),
  'registry_gzip_bytes':len(packed),'registry_raw_sha256':hashlib.sha256(gzip.decompress(packed)).hexdigest(),
  'selected':{name:brief(r)for name,r in selected.items()},'formal_formation_rule':'NOT_ESTABLISHED','capital_growth_flywheel_effectiveness':'NOT_EVALUATED'}
 for name,obj in [('selected-common-spans.json',selected),('pool-summaries.json',pool_summary),('summary.json',summary)]:
  (p/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 assert Path(a.source).read_bytes()==sraw and Path(a.comparison).read_bytes()==traw
 assert (prior/'pool-revisit-registry.json.gz').read_bytes()==prior_packed
 print(json.dumps(summary,ensure_ascii=False))
