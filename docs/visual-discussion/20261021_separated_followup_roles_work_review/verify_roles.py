"""Independent raw streak reconstruction, source geometry and causal tests."""
import copy,gzip,itertools,json
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
from followup_roles import ROOT,inputs,propose,track,expand_registry,uid,sha,write
src,zones,pools,scopes,prior=inputs();packed=json.loads(gzip.decompress((ROOT/'followup-role-registry.json.gz').read_bytes()));reg=expand_registry(packed)
selected=json.loads(gzip.decompress((ROOT/'selected-role-proposals.json.gz').read_bytes()));events={e['event_id']:e for e in reg['events']};zm={z['zone_id']:z for z in zones};lm={l['link_id']:l for l in reg['links']};counts=Counter()
def independent(source,event,cutoff):
 f=event['frozen_frame'];up=event['direction']=='UP';lo,hi=D(f['lower']),D(f['upper']);start=f['departure_date']
 bs={b['date']:b for b in source['bars']if start<=b['date']<=cutoff};gaps={d for d in source['source_gaps']['known_calendar_missing_dates']if start<=d<=cutoff}
 timeline=sorted(set(bs)|gaps)
 outside=lambda d:d not in gaps and (D(bs[d]['close'])>hi if up else D(bs[d]['close'])<lo)
 eps=[];where={}
 for flag,group in itertools.groupby(timeline,key=outside):
  dates=list(group)
  if not flag:continue
  first,last=dates[0],dates[-1];j=timeline.index(last);end=timeline[j+1]if j+1<len(timeline)else None
  reason=None if end is None else'LISTED_DATA_GAP_NOT_PRICE_RETURN'if end in gaps else'CLOSE_RETURN_INSIDE'if lo<=D(bs[end]['close'])<=hi else'CLOSE_ON_OPPOSITE_SIDE'
  birth={'event_id':event['event_id'],'direction':event['direction'],'start':first,'previous_listed_gap':max((d for d in gaps if d<first),default=None)};eid=uid(birth)
  whole=[d for d in dates if (D(bs[d]['low'])>hi if up else D(bs[d]['high'])<lo)]
  contacts=[d for d in dates if D(bs[d]['low'])<=(hi if up else lo)<=D(bs[d]['high'])]
  e={**birth,'episode_id':eid,'first_whole_bar_on_side':whole[0]if whole else None,'first_boundary_contact':contacts[0]if contacts else None,'last_observed_outside_close':last,'ended_on':end,'end_reason':reason};eps.append(e)
  for d in dates:where[d]=eid
 return eps,where
def check(source,event,cutoff,links,episodes):
 eps,mapping=independent(source,event,cutoff);assert episodes==eps;counts['independent_episode_views']+=len(eps)
 epmap={e['episode_id']:e for e in eps};expected={};f=event['frozen_frame'];up=event['direction']=='UP'
 for z in zones:
  if z['code']!=source['code']or z['known_on_saved_bar']>cutoff or z['path_start']<event['known_on_saved_bar']:continue
  bars=[b for b in source['bars']if z['path_start']<=b['date']<=z['path_end']]
  separated=all(D(b['low'])>D(f['upper'])if up else D(b['high'])<D(f['lower'])for b in bars)
  if not separated:continue
  eid=mapping.get(z['path_start']);e=epmap.get(eid)
  if not e or mapping.get(z['path_end'])!=eid or not e['first_whole_bar_on_side']or e['first_whole_bar_on_side']>z['path_start']:continue
  expected[z['zone_id']]=e
 assert {l['zone_id']for l in links}==set(expected)
 for l in links:
  z=zm[l['zone_id']];e=expected[l['zone_id']];born=z['known_on_saved_bar']
  assert l['episode_id']==e['episode_id']and l['known_on_saved_bar']==born
  assert l['end_known_at_birth']==(e['ended_on']if e['ended_on']is not None and e['ended_on']<=born else None)
  assert (l['status_at_birth']=='EPISODE_ENDED_BY_CONFIRMATION')==(l['end_known_at_birth']is not None)
  assert uid({k:v for k,v in l.items()if k!='link_id'})==l['link_id']
  counts['independent_role_link_occurrences']+=1
 counts['snapshot_queries']+=1
for snap in reg['snapshots'].values():
 e=events[snap['event_id']];check(src[e['code']],e,snap['cutoff'],[lm[i]for i in snap['link_ids']],snap['episode_views'])

for z in zones:
 bs=[b for b in src[z['code']]['bars']if z['path_start']<=b['date']<=z['path_end']]
 assert min(D(b['low'])for b in bs)==D(z['raw_path_frame']['observed_low'])
 assert max(D(b['high'])for b in bs)==D(z['raw_path_frame']['observed_high'])
 assert len(bs)==z['raw_path_frame']['records'];counts['saved_zone_raw_frames']+=1
seen=set()
for name,r in selected.items():
 e=events[r['event_id']];s=src[e['code']];cut=r['cutoff'];check(s,e,cut,r['links'],r['episodes'])
 assert propose(s,e,zones,cut)==r;counts['selected_exact_reconstructions']+=1
 final={l['link_id']:l for l in r['links']}
 for b in s['bars']:
  day=b['date'];key=(e['event_id'],day)
  if not(e['known_on_saved_bar']<=day<=cut)or key in seen:continue
  seen.add(key);v=propose(s,e,zones,day)
  short=copy.deepcopy(s);short['bars']=[b for b in short['bars']if b['date']<=day]
  short['source_gaps']['known_calendar_missing_dates']=[d for d in short['source_gaps']['known_calendar_missing_dates']if d<=day]
  zs=[z for z in zones if z['known_on_saved_bar']<=day]
  assert propose(short,e,zs,day)==v
  assert all(final[l['link_id']]==l for l in v['links']);counts['prefix_truncation_and_immutable_links']+=1
 poison=copy.deepcopy(s);futurezones=copy.deepcopy(zones)
 for b in poison['bars']:
  if b['date']>cut:b.update(close='99999',open='9999',high='999999',low='-99999')
 poison['source_gaps']['known_calendar_missing_dates'] += ['2099-01-01']
 for z in futurezones:
  if z['known_on_saved_bar']>cut:z['raw_path_frame'].update(observed_low='-99999',observed_high='999999')
 assert propose(poison,e,futurezones,cut)==r;counts['future_price_zone_gap_poison']+=1
 # Positive affine price transformation checks role geometry only (synthetic fixture).
 ts=copy.deepcopy(s);te=copy.deepcopy(e);tz=copy.deepcopy(zones)
 for b in ts['bars']:
  for field in ['open','high','low','close']:b[field]=str(D(b[field])*D('3')+D('7'))
 for field in ['lower','upper']:te['frozen_frame'][field]=str(D(te['frozen_frame'][field])*3+7)
 for z in tz:
  if z['code']!=s['code']:continue
  for field in ['observed_low','observed_high']:z['raw_path_frame'][field]=str(D(z['raw_path_frame'][field])*3+7)
  for field in ['common_close_low','common_close_high']:z[field]=str(D(z[field])*3+7)
 transformed=propose(ts,te,tz,cut)
 assert [(l['zone_id'],l['status_at_birth'],l['first_whole_bar_on_side'])for l in transformed['links']]==[(l['zone_id'],l['status_at_birth'],l['first_whole_bar_on_side'])for l in r['links']]
 assert [(ep['start'],ep['ended_on'],ep['end_reason'])for ep in transformed['episodes']]==[(ep['start'],ep['ended_on'],ep['end_reason'])for ep in r['episodes']]
 counts['positive_affine_role_geometry']+=1

# Synthetic confirmation-return, strict equality, gap, opposite-side and availability.
bars=[]
for day,o,h,l,c in [(2,11,12,10,11),(3,12,13,11,12),(4,12,12,11,11.5),(5,11.5,13,11,12),(6,12,12,8,9)]:
 bars.append({'date':f'2040-01-{day:02}','open':str(o),'high':str(h),'low':str(l),'close':str(c),'volume_shares_scaled':'1'})
s={'code':'SYNTHETIC','bars':bars,'source_gaps':{'known_calendar_missing_dates':[]}}
e={'event_id':'synthetic-event','known_on_saved_bar':'2040-01-03','direction':'UP','frozen_frame':{'lower':'0','upper':'10','departure_date':'2040-01-02'}}
z={'code':'SYNTHETIC','zone_id':'synthetic-zone','known_on_saved_bar':'2040-01-06','path_start':'2040-01-03','path_end':'2040-01-05','leg_ids':['a','b'],'common_close_low':'11.5','common_close_high':'12','raw_path_frame':{'observed_low':'11','observed_high':'13','bars_fingerprint':'synthetic'}}
v=propose(s,e,[z],'2040-01-06');assert len(v['links'])==1 and v['links'][0]['status_at_birth']=='EPISODE_ENDED_BY_CONFIRMATION';assert v['views'][0]['current_role_evidence']=='REFERENCE_AFTER_PRICE_RETURN'
assert not propose(s,e,[z],'2040-01-05')['links']
touch=copy.deepcopy(z);touch['raw_path_frame']['observed_low']='10';assert not propose(s,e,[touch],'2040-01-06')['links']
gap=copy.deepcopy(s);gap['source_gaps']['known_calendar_missing_dates']=['2040-01-04'];gap['bars']=[b for b in gap['bars']if b['date']!='2040-01-04'];assert not propose(gap,e,[z],'2040-01-06')['links']
gapview=track(gap,e,'2040-01-06')[0];assert gapview[0]['end_reason']=='LISTED_DATA_GAP_NOT_PRICE_RETURN'
opposite=copy.deepcopy(s);opposite['bars'][-1]['close']='-1';assert track(opposite,e,'2040-01-06')[0][0]['end_reason']=='CLOSE_ON_OPPOSITE_SIDE'
try:propose(s,e,[z],'2040-01-02');raise AssertionError('must reject unavailable event')
except ValueError:pass
counts['synthetic_edge_cases']=7
assert not selected['ABC-2025-06-11']['links'];assert len(selected['ABC-2025-06-12']['links'])==1
g=selected['G2-2023-04-27'];assert g['links'][0]['first_whole_bar_on_side']=='2023-04-24';assert next(ep for ep in g['episodes']if ep['episode_id']==g['links'][0]['episode_id'])['start']=='2023-04-21'
assert g['episodes'][0]['ended_on']=='2023-03-01'and g['links'][0]['episode_id']!=g['episodes'][0]['episode_id']
assert not selected['2884-last-bar']['links']
counts['selected_time_role_assertions']=5
for path,info in json.loads((ROOT/'source-provenance.json').read_text())['files'].items():assert sha(Path(path).read_bytes())==info['sha256'];counts['unchanged_input_hashes']+=1
assert sha(Path('/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json').read_bytes())=='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
assert sha(Path('/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json').read_bytes())=='184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15'
assert sha(gzip.decompress((ROOT.parent/'source-role-research/source-role-registry.json.gz').read_bytes()))=='d337e10f56586c493f9cc4d608040181fc5a98bdc37845b0f106dec8da1b9cea'
write(ROOT/'verification.json',{'status':'PASS','checks':dict(counts),'driver_runs':1,'storage_conversion_runs':1,'verification_runs':1,'prior_driver_or_test_reruns':0,'original_core_recomputations':0,'classifier_validation':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD','capital_growth_flywheel_effectiveness':'NOT_EVALUATED'})
print(json.dumps(dict(counts)))
