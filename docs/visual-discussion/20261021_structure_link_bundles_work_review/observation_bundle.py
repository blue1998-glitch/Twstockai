"""Compose saved research evidence into cutoff-qualified observation bundles.

No new seed/turn/box/classifier; manual review is a separate display overlay.
"""
import copy,gzip,hashlib,json,sys
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent
SOURCE=Path('/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json')
COMPARISON=Path('/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json')
sys.path.insert(0,str(BASE/'overlap-role-research'))
from overlap_roles import expand_pair
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def pack_snapshots(snapshots,catalog):
 result=copy.deepcopy(snapshots);pi={p['comparison_id']:i for i,p in enumerate(catalog['pairs'])}
 for r in result.values():
  r['archived_pair_role_indices']={k:[pi[i]for i in ids]for k,ids in r.pop('archived_pair_role_buckets').items()}
 return {'layout':'SNAPSHOTS_WITH_VERSION_BOUND_PRIOR_PAIR_ROW_INDICES_NO_RANKING','snapshots':result,
         'pair_registry_git_path':'docs/visual-discussion/20261021_overlap_fresh_evidence_work_review/overlap-role-registry.json.gz',
         'pair_registry_raw_sha256':'ab016b7c32ac0c80674d5235d4c23b76a75da345b9fe5a356b8f297ed03e953c',
         'supplemental_pair_origin':'evidence-extensions.json.gz appended after prior pair rows'if (ROOT/'evidence-extensions.json.gz').exists()else None}
def unpack_snapshots(packed,catalog):
 result=copy.deepcopy(packed['snapshots'])
 for r in result.values():r['archived_pair_role_buckets']={k:[catalog['pairs'][i]['comparison_id']for i in ids]for k,ids in r.pop('archived_pair_role_indices').items()}
 return result
def location(price,lo,hi):
 c,a,b=map(D,[price,lo,hi]);return'BELOW'if c<a else'ABOVE'if c>b else'AT_LOW'if c==a else'AT_HIGH'if c==b else'INSIDE'
def load_inputs(apply_extensions=True):
 sources={code:json.loads(p.read_text())for code,p in [('2884',SOURCE),('1101',COMPARISON)]}
 op=json.loads(gzip.decompress((BASE/'overlap-role-research/overlap-role-registry.json.gz').read_bytes()))
 fp=json.loads(gzip.decompress((BASE/'followup-role-research/followup-role-registry.json.gz').read_bytes()))
 original=json.loads(gzip.decompress((BASE/'source-role-research/source-role-registry.json.gz').read_bytes()))
 fs=json.loads(gzip.decompress((BASE/'followup-role-research/selected-role-proposals.json.gz').read_bytes()))
 assert op['zones']==original['zones']==fp['zones']
 histories={}
 for snap in fp['snapshots'].values():
  eps=[{**fp['episode_births'][bi],'first_whole_bar_on_side':whole,'first_boundary_contact':contact,'last_observed_outside_close':last,'ended_on':end,'end_reason':reason}for bi,whole,contact,last,end,reason in snap['episode_views']]
  h={'event_id':snap['event_id'],'archive_observed_through':snap['cutoff'],'episodes':eps}
  if h['event_id']not in histories or h['archive_observed_through']>histories[h['event_id']]['archive_observed_through']:histories[h['event_id']]=h
 for snap in fs.values():
  h={'event_id':snap['event_id'],'archive_observed_through':snap['cutoff'],'episodes':snap['episodes']}
  if h['event_id']not in histories or h['archive_observed_through']>histories[h['event_id']]['archive_observed_through']:histories[h['event_id']]=h
 links=[]
 for ei,bi,zi,status,end,reason,whole,lid in fp['links']:
  links.append({'event_id':fp['events'][ei]['event_id'],'episode_id':fp['episode_births'][bi]['episode_id'],'zone_id':fp['zones'][zi]['zone_id'],
                'known_on':fp['zones'][zi]['known_on_saved_bar'],'status_at_birth':status,'end_known_at_birth':end,'link_id':lid})
 catalog={'zones':op['zones'],'turns':{t['turn_id']:t for t in op['turns']},'legs':{l['leg_id']:l for l in op['legs']},
                 'pairs':[expand_pair(op,row)for row in op['pairs']],'events':fp['events'],'histories':histories,'followup_links':links,
                 'pivots':original['pivots'],'contexts':original['contexts']}
 catalog['archive_histories']=copy.deepcopy(histories)
 if apply_extensions and (ROOT/'evidence-extensions.json.gz').exists():
  x=json.loads(gzip.decompress((ROOT/'evidence-extensions.json.gz').read_bytes()));catalog['pairs']+=x['new_comparisons'];catalog['followup_links']+=x['new_followup_links']
  catalog['histories'].update(x['extended_histories']);catalog['extension_summary']=x['summary']
 return sources,catalog
def earliest(z,c):return c['turns'][c['legs'][z['leg_ids'][0]]['from_turn_id']]['left_evidence_date']
def project_history(source,history,cutoff):
 covered=min(cutoff,history['archive_observed_through']);episodes=[]
 for e in history['episodes']:
  if e['start']>covered:continue
  ending=e['ended_on']if e['ended_on']is not None and e['ended_on']<=covered else None
  last=max(b['date']for b in source['bars']if e['start']<=b['date']<=min(covered,e['last_observed_outside_close']))
  episodes.append({'episode_id':e['episode_id'],'start':e['start'],'previous_listed_gap':e['previous_listed_gap'],
    'first_whole_bar_on_side':e['first_whole_bar_on_side']if e['first_whole_bar_on_side']is not None and e['first_whole_bar_on_side']<=covered else None,
    'first_boundary_contact':e['first_boundary_contact']if e['first_boundary_contact']is not None and e['first_boundary_contact']<=covered else None,
    'last_observed_outside_close':last,'ended_on':ending,'end_reason':e['end_reason']if ending is not None else None,
    'current_evidence_status':'ENDED_AT_SAVED_EVENT'if ending is not None else'OPEN_THROUGH_REQUESTED_CUTOFF'if history['archive_observed_through']>=cutoff else'OPEN_AT_ARCHIVE_END_CURRENT_CONTINUITY_UNKNOWN'})
 return {'observed_through':covered,'covers_requested_cutoff':history['archive_observed_through']>=cutoff,'episodes':episodes}
def compose(source,seed_start,cutoff,catalog):
 if cutoff<seed_start:raise ValueError('Cutoff before observation seed')
 prefix=[b for b in source['bars']if b['date']<=cutoff]
 if not prefix:raise ValueError('No saved source prefix')
 last=prefix[-1];code=source['code'];rows=[b for b in prefix if b['date']>=seed_start]
 if not rows:raise ValueError('No saved rows in observation')
 zs=[z for z in catalog['zones']if z['code']==code and z['known_on_saved_bar']<=cutoff and earliest(z,catalog)>=seed_start]
 zid={z['zone_id']for z in zs};pairs=[p for p in catalog['pairs']if p['older_zone_id']in zid and p['later_zone_id']in zid and p['known_on_saved_bar']<=cutoff]
 buckets={}
 for p in pairs:buckets.setdefault(p['role_candidate'],[]).append(p['comparison_id'])
 for ids in buckets.values():ids.sort()
 zviews=[]
 for z in zs:
  legs=set(z['leg_ids']);maximal=not any(legs<set(t['leg_ids'])for t in zs)
  zviews.append({'zone_id':z['zone_id'],'current_close_vs_common':location(last['close'],z['common_close_low'],z['common_close_high']),
                 'current_close_vs_raw_path':location(last['close'],z['raw_path_frame']['observed_low'],z['raw_path_frame']['observed_high']),
                 'maximal_available_saved_path_view':maximal})
 events=[e for e in catalog['events']if e['code']==code and e['known_on_saved_bar']<=cutoff and e['frozen_frame']['frame_start']>=seed_start]
 eventviews=[];episode_status={}
 for e in events:
  h=project_history(source,catalog['histories'][e['event_id']],cutoff);f=e['frozen_frame']
  archived=catalog.get('archive_histories',catalog['histories'])[e['event_id']]
  eventviews.append({'event_id':e['event_id'],'history':h,'current_close_vs_frozen_frame':location(last['close'],f['lower'],f['upper']),
    'prior_archive_covers_requested_cutoff':archived['archive_observed_through']>=cutoff,
    'trace_source_at_cutoff':'ARCHIVED_RESEARCH_TRACE'if archived['archive_observed_through']>=cutoff else'NEW_EXTENSION_FROM_SAVED_BARS'if h['covers_requested_cutoff']else'ARCHIVE_NOT_COVERING_CUTOFF'})
  episode_status.update({ep['episode_id']:ep['current_evidence_status']for ep in h['episodes']})
 eventids={e['event_id']for e in events};followups=[]
 for l in catalog['followup_links']:
  if l['event_id']in eventids and l['zone_id']in zid and l['known_on']<=cutoff:
   followups.append({'link_id':l['link_id'],'event_id':l['event_id'],'zone_id':l['zone_id'],'status_at_birth':l['status_at_birth'],
                     'current_episode_evidence':episode_status.get(l['episode_id'],'NO_PROJECTED_ARCHIVE_EPISODE_CURRENT_UNKNOWN')})
 pivots=[]
 for p in catalog['pivots']:
  if p['code']!=code or p['known_on']>cutoff:continue
  field='FIRST_SAVED_CLOSE_STRICTLY_ABOVE_HIGH'if p['kind']=='HIGH'else'FIRST_SAVED_CLOSE_STRICTLY_BELOW_LOW'
  hit=next(({'date':b['date'],'close':b['close']}for b in prefix if b['date']>=p['known_on']and(D(b['close'])>D(p['price'])if p['kind']=='HIGH'else D(b['close'])<D(p['price']))),None)
  pivots.append({'pivot_id':p['id'],'current_close_relation':location(last['close'],p['price'],p['price']),
                 'crossing_measure':field,'first_saved_crossing_from_availability':hit})
 contexts=[{'context_id':c['context_id'],'current_close_vs_research_bounds':location(last['close'],c['low'],c['high'])}for c in catalog['contexts']if c['code']==code and c['known_on']<=cutoff]
 out={'schema':'m1-observation-evidence-bundle-research/0.1','code':code,'requested_seed_start':seed_start,'requested_cutoff':cutoff,
      'source_observed_through':last['date'],'last_bar':last,'observation_records':len(rows),
      'observation_raw_extent':{'low':str(min(D(b['low'])for b in rows)),'high':str(max(D(b['high'])for b in rows)),'formal_bounds':None},
      'source_qualification':{'listed_missing_dates_in_observation':[d for d in source['source_gaps']['known_calendar_missing_dates']if seed_start<=d<=cutoff],
        'calendar_status':source['source_gaps'].get('calendar_status','UNVERIFIED'),'actions_coverage':source['source_gaps'].get('actions_coverage','UNVERIFIED'),
        'historical_publication_timing':source['source_gaps'].get('historical_publication_timing','UNVERIFIED'),
        'price_mode':'RAW_CANDIDATE','no_new_calendar_action_or_publication_authentication':True},
      'local_activity_views':sorted(zviews,key=lambda x:x['zone_id']),'archived_pair_role_buckets':buckets,
      'known_zone_pairs_without_archived_comparison':sum(a['known_on_saved_bar']!=b['known_on_saved_bar']for i,a in enumerate(zs)for b in zs[i+1:])-len(pairs),
      'departure_return_views':sorted(eventviews,key=lambda x:x['event_id']),'separated_followup_views':sorted(followups,key=lambda x:x['link_id']),
      'retained_original_pivot_views':sorted(pivots,key=lambda x:x['pivot_id']),'retained_original_context_views':sorted(contexts,key=lambda x:x['context_id']),
      'classification':'NOT_VALIDATED','core_usefulness':'NOT_ESTABLISHED','actions':'NOT_EVALUATED','capital_growth_flywheel_effectiveness':'NOT_EVALUATED','Android':'NOT_TESTED_NEW_BUILD',
      'formal_interval':None,'formal_start':None,'formal_end':None,'formal_membership':None,'formal_parent':None,'formal_merge':None,'selected_role':None,'primary_pressure_id':None,
      'historical_selection_time':None,'historical_signal_eligible':False,'original_core_snapshot_2026_10_07':None,'numeric_frame_2026_10_07':None,
      'qualification':'SAVED_RESEARCH_EVIDENCE_COMPOSITION_NOT_NEW_CLASSIFIER_OR_HISTORICAL_CORE_REPLAY; manual review excluded; archived missing relationships are unknown, not false.'}
 return out
def main():
 sources,catalog=load_inputs()
 groups={'A':('2884','2026-09-17',['2026-10-05','2026-10-06','2026-10-07','2026-10-12','2026-10-16']),
         'ABC':('1101','2025-04-07',['2025-05-13','2025-05-23','2025-05-26','2025-06-02','2025-06-03','2025-06-11','2025-06-12','2025-06-13']),
         'G2':('1101','2023-01-16',['2023-02-01','2023-02-10','2023-03-01','2023-04-27','2023-05-12','2023-08-16']),
         'B':('2884','2026-04-15',['2026-04-23','2026-04-24','2026-04-28','2026-05-04'])}
 snapshots={name+'-'+cut:compose(sources[code],start,cut,catalog)for name,(code,start,cuts)in groups.items()for cut in cuts}
 raw=json.dumps(pack_snapshots(snapshots,catalog),ensure_ascii=False,separators=(',',':')).encode();(ROOT/'observation-bundles.json.gz').write_bytes(gzip.compress(raw,mtime=0))
 write(ROOT/'query-specs.json',{name:{'code':code,'research_seed_start':start,'cutoffs':cuts,'historical_selection_time':None}for name,(code,start,cuts)in groups.items()})
 overlay={'role':'RETROSPECTIVE_MANUAL_REVIEW_DISPLAY_ONLY_EXCLUDED_FROM_COMPOSE','knowledge_date':'2026-10-21','not_evidence_available_at_historical_cutoff':True,
   'A':{'confirmed':['完整上漲、短暫整理、再漲','截至2026-10-07足夠辨認整理'],'formal_start':None,'earliest_recognition_date':None},
   'ABC':{'confirmed':['自身較弱區間；相對舊主要帶跳空下跌更弱','2025-04-07至06-02人工涵蓋39筆；6/2仍內、6/3在外','5/13 H31.40局部代表已答，非主壓力'],
          'older_major_band_months':['2023-06','2025-04'],'month_precision_only':True,'formal_price_bounds':None,'formal_membership':None,'primary_representative':None},
   'G2':{'confirmed':['人工2023-01-16至08-16共136保存筆','代表2023-05-02 H40.25'],'formal_price_bounds':None,'formal_membership':None},
   'B':{'case_role':'事後方向對照','manual_negative_interval_label':None}}
 write(ROOT/'manual-review-overlay.json',overlay)
 summary={'snapshots':len(snapshots),'groups':len(groups),'selected':{name:{'observed_through':r['source_observed_through'],'rows':r['observation_records'],
   'local_zones':len(r['local_activity_views']),'maximal_saved_path_views':sum(v['maximal_available_saved_path_view']for v in r['local_activity_views']),
   'pair_roles':{k:len(v)for k,v in r['archived_pair_role_buckets'].items()},'uncompared_known_pairs':r['known_zone_pairs_without_archived_comparison'],
   'retained_original_pivots':len(r['retained_original_pivot_views']),'retained_original_contexts':len(r['retained_original_context_views']),
   'departure_return_events':len(r['departure_return_views']),'archive_traces_not_covering_cutoff':sum(not v['history']['covers_requested_cutoff']for v in r['departure_return_views']),
   'separated_followup_links':len(r['separated_followup_views'])}for name,r in snapshots.items()},'bundle_gzip_bytes':(ROOT/'observation-bundles.json.gz').stat().st_size,'bundle_raw_sha256':sha(raw),
   'new_composer_driver_runs':3,'run_history':['Initial composition','Add inherited source qualification','Compose supplemental comparisons and extended traces'],
   'new_seed_or_turn_generation':0,'new_evidence_extensions':catalog.get('extension_summary',{}),'manual_review_used_in_composer':False,'classification':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD','capital_growth_flywheel_effectiveness':'NOT_EVALUATED'}
 write(ROOT/'summary.json',summary)
 paths=[SOURCE,COMPARISON,BASE/'overlap-role-research/overlap-role-registry.json.gz',BASE/'followup-role-research/followup-role-registry.json.gz',BASE/'followup-role-research/selected-role-proposals.json.gz',BASE/'source-role-research/source-role-registry.json.gz']
 if (ROOT/'evidence-extensions.json.gz').exists():paths.append(ROOT/'evidence-extensions.json.gz')
 write(ROOT/'source-provenance.json',{'files':{str(p):{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}for p in paths},'source_indices_are_version_bound_not_strategy_rank':True})
 print(json.dumps({k:v for k,v in summary.items()if k!='selected'},ensure_ascii=False))
if __name__=='__main__':main()
