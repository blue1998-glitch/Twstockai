"""Propose distinct later local activity relative to saved frozen frames.

Reuses immutable saved zones/events. This is not formal region selection.
"""
import argparse,gzip,hashlib,json
from pathlib import Path
from decimal import Decimal as D
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent
SOURCE=Path('/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json')
COMPARISON=Path('/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json')
def sha(b):return hashlib.sha256(b).hexdigest()
def uid(x):return 'sha256:'+sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def pack_registry(registry):
 """Lossless table layout; integer indices are storage, never priority."""
 r=registry;events=r['events'];zones=r['zones'];births=r['episode_births'];links=r['links']
 ei={e['event_id']:i for i,e in enumerate(events)};zi={z['zone_id']:i for i,z in enumerate(zones)};bi={b['episode_id']:i for i,b in enumerate(births)};li={l['link_id']:i for i,l in enumerate(links)}
 compact=[[ei[l['event_id']],bi[l['episode_id']],zi[l['zone_id']],l['status_at_birth'],l['end_known_at_birth'],l['end_reason_known_at_birth'],l['first_whole_bar_on_side'],l['link_id']]for l in links]
 snapshots={}
 for key,o in r['snapshots'].items():
  snapshots[key]={k:v for k,v in o.items()if k not in ['link_ids','episode_views']}
  snapshots[key]['link_indices']=[li[i]for i in o['link_ids']]
  snapshots[key]['episode_views']=[[bi[b['episode_id']],b['first_whole_bar_on_side'],b['first_boundary_contact'],b['last_observed_outside_close'],b['ended_on'],b['end_reason']]for b in o['episode_views']]
 return {'layout':'IMMUTABLE_TABLES_PLUS_CUTOFF_VIEWS_NO_VOTES','events':events,'zones':zones,'episode_births':births,'links':compact,'snapshots':snapshots,'qualification':r['qualification']}
def expand_registry(p):
 links=[]
 for ei,bi,zi,status,end,reason,whole,lid in p['links']:
  e=p['events'][ei];ep=p['episode_births'][bi];z=p['zones'][zi]
  l={'event_id':e['event_id'],'episode_id':ep['episode_id'],'zone_id':z['zone_id'],'known_on_saved_bar':z['known_on_saved_bar'],'direction':e['direction'],
     'role_candidate':'SEPARATED_LATER_LOCAL_TWO_WAY_ACTIVITY_NOT_FORMAL_REGION','status_at_birth':status,'end_known_at_birth':end,'end_reason_known_at_birth':reason,
     'first_whole_bar_on_side':whole,'path_start':z['path_start'],'path_end':z['path_end'],'raw_path_low':z['raw_path_frame']['observed_low'],'raw_path_high':z['raw_path_frame']['observed_high'],
     'common_close_low':z['common_close_low'],'common_close_high':z['common_close_high'],'raw_path_fingerprint':z['raw_path_frame']['bars_fingerprint'],
     'formal_new_region':None,'formal_old_region_end':None,'formal_parent':None,'selected_role':None,'link_id':lid};links.append(l)
 snapshots={}
 for key,o in p['snapshots'].items():
  snapshots[key]={k:v for k,v in o.items()if k not in ['link_indices','episode_views']}
  snapshots[key]['link_ids']=[links[i]['link_id']for i in o['link_indices']]
  snapshots[key]['episode_views']=[{**p['episode_births'][bi],'first_whole_bar_on_side':whole,'first_boundary_contact':contact,'last_observed_outside_close':last,'ended_on':end,'end_reason':reason}for bi,whole,contact,last,end,reason in o['episode_views']]
 return {'events':p['events'],'zones':p['zones'],'episode_births':p['episode_births'],'links':links,'snapshots':snapshots,'qualification':p['qualification']}
def inputs():
 a=json.loads(SOURCE.read_text());b=json.loads(COMPARISON.read_text())
 roles=json.loads(gzip.decompress((BASE/'source-role-research/source-role-registry.json.gz').read_bytes()))
 pools=json.loads(gzip.decompress((BASE/'stop-branch-research/candidate-pools.json.gz').read_bytes()))
 scopes=json.loads((BASE/'stop-branch-research/reviewed-scope-tests.json').read_text())
 selected=json.loads((BASE/'common-band-research/selected-common-spans.json').read_text())
 return {'2884':a,'1101':b},roles['zones'],pools,scopes,selected
def close_side(bar,frame):
 c=D(bar['close']);lo=D(frame['lower']);hi=D(frame['upper'])
 return 'DOWN'if c<lo else 'UP'if c>hi else 'INSIDE_INCLUSIVE'
def whole_side(bar,frame):
 return 'DOWN'if D(bar['high'])<D(frame['lower'])else'UP'if D(bar['low'])>D(frame['upper'])else'TOUCH_OR_OVERLAP'
def location(price,lo,hi):
 c=D(price);l=D(lo);h=D(hi)
 return 'BELOW'if c<l else 'ABOVE'if c>h else 'AT_LOW'if c==l else 'AT_HIGH'if c==h else'INSIDE'
def track(source,event,cutoff):
 """Current episode views; birth IDs omit future end/contact/status."""
 if cutoff<event['known_on_saved_bar']:raise ValueError('Event not yet available')
 frame=event['frozen_frame'];direction=event['direction'];start=frame['departure_date']
 bars={b['date']:b for b in source['bars']if start<=b['date']<=cutoff}
 gaps={d for d in source['source_gaps']['known_calendar_missing_dates']if start<=d<=cutoff}
 episodes=[];active=None;day_to_episode={};last_gap=None
 for day in sorted(set(bars)|gaps):
  if day in gaps:
   if active is not None:active['ended_on']=day;active['end_reason']='LISTED_DATA_GAP_NOT_PRICE_RETURN';active=None
   last_gap=day;continue
  b=bars[day];side=close_side(b,frame)
  if side==direction:
   if active is None:
    birth={'event_id':event['event_id'],'direction':direction,'start':day,'previous_listed_gap':last_gap}
    active={**birth,'episode_id':uid(birth),'first_whole_bar_on_side':None,'first_boundary_contact':None,'last_observed_outside_close':day,'ended_on':None,'end_reason':None};episodes.append(active)
   active['last_observed_outside_close']=day
   if whole_side(b,frame)==direction and active['first_whole_bar_on_side']is None:active['first_whole_bar_on_side']=day
   boundary=D(frame['upper']if direction=='UP'else frame['lower'])
   if D(b['low'])<=boundary<=D(b['high'])and active['first_boundary_contact']is None:active['first_boundary_contact']=day
   day_to_episode[day]=active['episode_id']
  elif active is not None:
   active['ended_on']=day;active['end_reason']='CLOSE_RETURN_INSIDE'if side=='INSIDE_INCLUSIVE'else'CLOSE_ON_OPPOSITE_SIDE';active=None
 return episodes,day_to_episode
def propose(source,event,zones,cutoff):
 episodes,mapping=track(source,event,cutoff);em={e['episode_id']:e for e in episodes};f=event['frozen_frame'];direction=event['direction']
 available=[z for z in zones if z['code']==source['code']and z['known_on_saved_bar']<=cutoff and z['path_start']>=event['known_on_saved_bar']]
 links=[];rejections={'raw_path_not_wholly_on_departure_side':0,'no_same_episode_or_whole_bar_before_path':0}
 for z in available:
  lo,hi=D(z['raw_path_frame']['observed_low']),D(z['raw_path_frame']['observed_high'])
  outside=lo>D(f['upper'])if direction=='UP'else hi<D(f['lower'])
  if not outside:rejections['raw_path_not_wholly_on_departure_side']+=1;continue
  eid=mapping.get(z['path_start']);e=em.get(eid)
  if not e or mapping.get(z['path_end'])!=eid or e['first_whole_bar_on_side']is None or e['first_whole_bar_on_side']>z['path_start']:
   rejections['no_same_episode_or_whole_bar_before_path']+=1;continue
  born=z['known_on_saved_bar'];ended_by_birth=e['ended_on']is not None and e['ended_on']<=born
  # No future episode end is included in the immutable link.
  link={'event_id':event['event_id'],'episode_id':eid,'zone_id':z['zone_id'],'known_on_saved_bar':born,'direction':direction,
        'role_candidate':'SEPARATED_LATER_LOCAL_TWO_WAY_ACTIVITY_NOT_FORMAL_REGION',
        'status_at_birth':'EPISODE_ENDED_BY_CONFIRMATION'if ended_by_birth else'OUTSIDE_CLOSE_EPISODE_STILL_OPEN',
        'end_known_at_birth':e['ended_on']if ended_by_birth else None,
        'end_reason_known_at_birth':e['end_reason']if ended_by_birth else None,
        'first_whole_bar_on_side':e['first_whole_bar_on_side'],
        'path_start':z['path_start'],'path_end':z['path_end'],
        'raw_path_low':z['raw_path_frame']['observed_low'],'raw_path_high':z['raw_path_frame']['observed_high'],
        'common_close_low':z['common_close_low'],'common_close_high':z['common_close_high'],
        'raw_path_fingerprint':z['raw_path_frame']['bars_fingerprint'],
        'formal_new_region':None,'formal_old_region_end':None,'formal_parent':None,'selected_role':None}
  link['link_id']=uid(link);links.append(link)
 last=next(b for b in reversed(source['bars'])if b['date']<=cutoff)
 views=[]
 for link in links:
  e=em[link['episode_id']];ended=e['ended_on']is not None
  same_episode=[q for q in links if q['episode_id']==link['episode_id']]
  z=next(z for z in available if z['zone_id']==link['zone_id']);legs=set(z['leg_ids'])
  maximal=not any(legs<set(next(z for z in available if z['zone_id']==q['zone_id'])['leg_ids'])for q in same_episode)
  views.append({'link_id':link['link_id'],'episode_ended_on':e['ended_on'],'episode_end_reason':e['end_reason'],
    'current_role_evidence':'REFERENCE_AFTER_PRICE_RETURN'if ended and e['end_reason']!='LISTED_DATA_GAP_NOT_PRICE_RETURN'else'CONTINUITY_UNVERIFIED_AFTER_GAP'if ended else'SEPARATED_ACTIVITY_WITH_OPEN_OUTSIDE_CLOSE_EPISODE',
    'current_close_vs_old_frame':location(last['close'],f['lower'],f['upper']),
    'current_close_vs_new_raw_path':location(last['close'],link['raw_path_low'],link['raw_path_high']),
    'current_close_vs_common_core':location(last['close'],link['common_close_low'],link['common_close_high']),
    'maximal_available_saved_path_view':maximal})
 return {'schema':'m1-separated-followup-role-proposal/0.1','event_id':event['event_id'],'code':source['code'],'cutoff':cutoff,
         'last_bar':last,'frozen_frame':f,'original_whole_event_known_on':event['known_on_saved_bar'],'episodes':episodes,'links':links,'views':views,
         'comparison_rejections':rejections,'qualification':'RESEARCH_ROLE_PROPOSAL_NOT_CLASSIFIER_OR_FORMAL_REGION_TERMINATION',
         'formal_new_region':None,'formal_old_region_end':None,'formal_parent':None,'selected_role':None,'primary_pressure_id':None,
         'historical_selection_time':None,'historical_signal_eligible':False,'classification':'NOT_VALIDATED','core_usefulness':'NOT_ESTABLISHED',
         'actions':'NOT_EVALUATED','capital_growth_flywheel_effectiveness':'NOT_EVALUATED','Android':'NOT_TESTED_NEW_BUILD'}
def main():
 src,zones,pools,scopes,selected=inputs();events={};observations=[]
 for name,pool in pools.items():
  for observation in pool['results']:
   for e in observation['events']:
    if e['kind']!='WHOLE_BAR_OUTSIDE_FROZEN_FRAME':continue
    if e['event_id']in events:assert events[e['event_id']]==e
    events[e['event_id']]=e;observations.append({'pool':name,'event_id':e['event_id'],'cutoff':pool['cutoff']})
 for name,o in scopes.items():
  for e in o['events']:
   if e['kind']!='WHOLE_BAR_OUTSIDE_FROZEN_FRAME':continue
   if e['event_id']in events:assert events[e['event_id']]==e
   events[e['event_id']]=e;observations.append({'pool':'external:'+name,'event_id':e['event_id'],'cutoff':o['data_cutoff']})
 # Normalized immutable link registry, episode birth table, snapshots separately.
 links={};episodes={};snapshots={}
 for o in observations:
  key=uid(o)
  if key in snapshots:continue
  e=events[o['event_id']];r=propose(src[e['code']],e,zones,o['cutoff'])
  for l in r['links']:
   if l['link_id']in links:assert links[l['link_id']]==l
   links[l['link_id']]=l
  for ep in r['episodes']:
   birth={k:ep[k]for k in ['event_id','direction','start','previous_listed_gap','episode_id']}
   if ep['episode_id']in episodes:assert episodes[ep['episode_id']]==birth
   episodes[ep['episode_id']]=birth
  snapshots[key]={**o,'link_ids':[l['link_id']for l in r['links']],'episode_views':r['episodes'],'rejections':r['comparison_rejections'],'last_bar':r['last_bar']}
 abc=next(e for e in scopes['ABC-next-record']['events']if e['kind']=='WHOLE_BAR_OUTSIDE_FROZEN_FRAME')
 g2=next(e for e in scopes['G2-manual-scope-test']['events']if e['kind']=='WHOLE_BAR_OUTSIDE_FROZEN_FRAME')
 aevent=next(e for e in scopes['2884-later-rise']['events']if e['kind']=='WHOLE_BAR_OUTSIDE_FROZEN_FRAME')
 queries={**{'ABC-'+date:(abc,date)for date in ['2025-06-03','2025-06-11','2025-06-12','2025-06-13']},
          **{'G2-'+date:(g2,date)for date in ['2023-02-21','2023-02-22','2023-03-01','2023-03-03','2023-04-26','2023-04-27','2023-05-09','2023-08-16']},
          '2884-last-bar':(aevent,'2026-10-16')}
 details={name:propose(src[e['code']],e,zones,cut)for name,(e,cut)in queries.items()}
 for r in details.values():
  for l in r['links']:
   if l['link_id']in links:assert links[l['link_id']]==l
   links[l['link_id']]=l
 # Source-level view remains immutable input; no new common candidates computed.
 registry={'events':list(events.values()),'zones':zones,'episode_births':list(episodes.values()),'links':list(links.values()),'snapshots':snapshots,
           'qualification':'Repeated/overlapping source-event pairs are not independent samples or votes. Maximal views do not delete shorter evidence.'}
 raw=json.dumps(pack_registry(registry),ensure_ascii=False,separators=(',',':')).encode();packed=gzip.compress(raw,mtime=0)
 (ROOT/'followup-role-registry.json.gz').write_bytes(packed)
 selected_bytes=(json.dumps(details,ensure_ascii=False,indent=2)+'\n').encode();(ROOT/'selected-role-proposals.json.gz').write_bytes(gzip.compress(selected_bytes,mtime=0))
 summary={'input_event_occurrences':len(observations),'distinct_snapshot_queries':len(snapshots),'unique_original_whole_events':len(events),
          'unique_episode_births_in_pool_views':len(episodes),'unique_saved_zones':len(zones),'unique_role_links':len(links),'selected_queries':len(details),
          'registry_gzip_bytes':len(packed),'registry_raw_sha256':sha(raw),'selected_raw_sha256':sha(selected_bytes),
          'selected':{name:{'role_links':len(r['links']),'open_episodes':sum(ep['ended_on']is None for ep in r['episodes']),
            'first_role_known_on':min((l['known_on_saved_bar']for l in r['links']),default=None),
            'current_old_frame_relation':location(r['last_bar']['close'],r['frozen_frame']['lower'],r['frozen_frame']['upper'])}for name,r in details.items()},
          'formal_formation_rule':'NOT_ESTABLISHED','classification':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD','capital_growth_flywheel_effectiveness':'NOT_EVALUATED'}
 write(ROOT/'summary.json',summary)
 paths=[SOURCE,COMPARISON,BASE/'source-role-research/source-role-registry.json.gz',BASE/'stop-branch-research/candidate-pools.json.gz',BASE/'stop-branch-research/reviewed-scope-tests.json',BASE/'common-band-research/selected-common-spans.json']
 write(ROOT/'source-provenance.json',{'files':{str(p):{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}for p in paths},'original_core_recomputations':0,'prior_driver_reruns':0})
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
