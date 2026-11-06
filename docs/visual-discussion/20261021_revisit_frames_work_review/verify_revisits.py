"""Independent anchor-by-anchor witness enumeration; not classifier acceptance."""
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
from copy import deepcopy
import argparse,json,gzip,hashlib
from revisit_research import discover,digest,norm

ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--prior-dir',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
p=Path(a.out);prior=Path(a.prior_dir);source_paths=[Path(a.source),Path(a.comparison)];hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest()for f in source_paths+[prior/'candidate-pools.json.gz']}
s,t=[json.loads(f.read_text())for f in source_paths];packed=(p/'pool-revisit-registry.json.gz').read_bytes();raw=gzip.decompress(packed);registry=json.loads(raw);summary=json.loads((p/'summary.json').read_text());selected=json.loads((p/'selected-revisits.json').read_text())
assert hashlib.sha256(raw).hexdigest()==summary['registry_raw_sha256']
def signature(e,frame):
 return(e['anchor_price'],e['anchor_known_on_in_seed'],tuple(e['anchor_birth_roles']),tuple((v['side'],v['date'],v['close'])for v in e['strict_side_visits']),e['known_on_saved_bar'],frame['observed_start'],frame['observed_end'],frame['observed_low'],frame['observed_high'],e['return_close_relation_to_prior_frame'],e['return_bar_inside_prior_frame'])

def independent(src,start,cutoff):
 rows=[b for b in src['bars']if start<=b['date']<=cutoff];gaps=src['source_gaps']['known_calendar_missing_dates'];bounds=[0]
 for i in range(1,len(rows)):
  if any(rows[i-1]['date']<=g<=rows[i]['date']for g in gaps):bounds.append(i)
 bounds.append(len(rows));expected=[]
 for left,right in zip(bounds,bounds[1:]):
  segment=rows[left:right];prices={D(b[field])for b in segment for field in ['low','high','close']}
  for price in prices:
   born=next(i for i,b in enumerate(segment)if any(D(b[field])==price for field in ['low','high','close']))
   birth=segment[born];roles=tuple(field for field in ['low','high','close']if D(birth[field])==price)
   strict=[]
   for i in range(born,len(segment)):
    b=segment[i];c=D(b['close']);side=(c>price)-(c<price)
    if side:strict.append((side,i))
   runs=[]
   for side,i in strict:
    if not runs or side!=runs[-1][0]:runs.append((side,i))
   for j in range(2,len(runs)):
    visits=runs[j-2:j+1];begin=visits[0][1];end=visits[-1][1];old=segment[begin:end];bar=segment[end]
    lo=min(D(b['low'])for b in old);hi=max(D(b['high'])for b in old);close=D(bar['close'])
    expected.append((str(price.normalize()),birth['date'],roles,tuple((side,segment[k]['date'],segment[k]['close'])for side,k in visits),bar['date'],old[0]['date'],old[-1]['date'],str(lo),str(hi),'INSIDE_INCLUSIVE'if lo<=close<=hi else'BELOW'if close<lo else'ABOVE',D(bar['low'])>=lo and D(bar['high'])<=hi))
 return Counter(expected)

observations=witness_checks=current_view_checks=0;seen_events=set();seen_frames=set()
for obs in registry['observations'].values():
 src=s if obs['code']=='2884'else t;r=discover(src,obs['seed_start'],obs['cutoff']);observations+=1
 stored=[registry['episode_table'][index]for index in obs['episode_indices']]
 assert stored==r['episodes']and obs['latest_bar']==next(b for b in src['bars']if b['date']==obs['cutoff'])
 assert Counter(signature(e,r['frames'][e['frame_id']])for e in r['episodes'])==independent(src,obs['seed_start'],obs['cutoff'])
 for e in stored:
  f=registry['frames'][e['frame_id']];assert f==r['frames'][e['frame_id']]
  assert digest({k:v for k,v in e.items()if k!='episode_id'})==e['episode_id']and digest(f)==e['frame_id']
  rows=[b for b in src['bars']if f['observed_start']<=b['date']<=f['observed_end']]
  assert digest(rows)==f['bars_fingerprint']and len(rows)==f['records']
  assert f['observed_end']<e['known_on_saved_bar']and e['anchor_known_on_in_seed']<=e['strict_side_visits'][0]['date']
  seen_events.add(e['episode_id']);seen_frames.add(e['frame_id']);witness_checks+=1
 # Reconstruct every omitted view from the normalized snapshot, losslessly.
 views=[];bar=obs['latest_bar'];c,l,h=[D(bar[k])for k in ['close','low','high']]
 for e in stored:
  f=registry['frames'][e['frame_id']];lo,hi=D(f['observed_low']),D(f['observed_high']);gaps=[g for g in obs['listed_missing_dates_in_observation']if f['observed_start']<=g<=obs['cutoff']]
  views.append({'episode_id':e['episode_id'],'frame_id':e['frame_id'],'latest_close_relation':'INSIDE_INCLUSIVE'if lo<=c<=hi else'BELOW'if c<lo else'ABOVE','latest_bar_relation':'WHOLE_BELOW'if h<lo else'WHOLE_ABOVE'if l>hi else'INSIDE_INCLUSIVE'if l>=lo and h<=hi else'OVERLAPS_OR_TOUCHES','crossed_listed_missing_dates':gaps,'current_relation_source_qualified':False if gaps else None,'formal_stopped':None});current_view_checks+=1
 assert views==r['current_views']
assert len(seen_events)==len(registry['episode_table'])==937 and len(seen_frames)==len(registry['frames'])==430

prefix_seen=set();prefix_checks=0
for name,r in selected.items():
 src=s if r['code']=='2884'else t
 assert discover(src,r['seed_start'],r['cutoff'])==r
 for b in [b for b in src['bars']if r['seed_start']<=b['date']<=r['cutoff']]:
  cut=b['date'];key=(r['code'],r['seed_start'],cut)
  if key in prefix_seen:continue
  prefix_seen.add(key);old=discover(src,r['seed_start'],cut);trunc={**src,'bars':[b for b in src['bars']if b['date']<=cut]}
  assert old==discover(trunc,r['seed_start'],cut)
  assert old['episodes']==[e for e in r['episodes']if e['known_on_saved_bar']<=cut]
  assert all(r['frames'][key]==v for key,v in old['frames'].items());prefix_checks+=1
 poison=deepcopy(src)
 for b in poison['bars']:
  if b['date']>r['cutoff']:
   for field in ['open','high','low','close']:b[field]='999999999'
 poison['source_gaps']['known_calendar_missing_dates'].append('2222-01-01')
 assert discover(poison,r['seed_start'],r['cutoff'])==r
 affine=deepcopy(src)
 for b in affine['bars']:
  for field in ['open','high','low','close']:b[field]=str(D(b[field])*10+7)
 ar=discover(affine,r['seed_start'],r['cutoff'])
 assert [(e['known_on_saved_bar'],[v['date']for v in e['strict_side_visits']],e['return_close_relation_to_prior_frame'],e['return_bar_inside_prior_frame'])for e in ar['episodes']]==[(e['known_on_saved_bar'],[v['date']for v in e['strict_side_visits']],e['return_close_relation_to_prior_frame'],e['return_bar_inside_prior_frame'])for e in r['episodes']]
 assert [(v['latest_close_relation'],v['latest_bar_relation'])for v in ar['current_views']]==[(v['latest_close_relation'],v['latest_bar_relation'])for v in r['current_views']]

assert selected['ABC-reviewed-Jun2']['last_segment_anchor_registry']['31.4']=={'known_on':'2025-05-13','birth_roles':['high'],'strict_side_runs':1}
assert all(e['anchor_price']!='31.4'for e in selected['ABC-reviewed-Jun2']['episodes'])
assert selected['2884-last-seed']['episodes']==[]
def synthetic(values,gaps=[]):
 return {'code':'SYNTHETIC','source_gaps':{'known_calendar_missing_dates':gaps},'bars':[{'date':f'2000-01-{i+1:02d}','open':str(c),'high':str(h),'low':str(l),'close':str(c),'volume_shares_scaled':'1'}for i,(l,h,c)in enumerate(values)]}
q=synthetic([(9,11,10),(7,10,8),(5,13,12)]);r=discover(q,'2000-01-01','2000-01-03')
assert any(e['anchor_price']=='9'and e['return_close_relation_to_prior_frame']=='ABOVE'for e in r['episodes'])
q=synthetic([(9,11,10),(7,10,8),(1,20,10)]);r=discover(q,'2000-01-01','2000-01-03')
assert any(e['anchor_price']=='9'and e['return_close_relation_to_prior_frame']=='INSIDE_INCLUSIVE'and not e['return_bar_inside_prior_frame']for e in r['episodes'])
q=synthetic([(9,11,10),(7,10,8),(8,10,9),(8,12,10)]);r=discover(q,'2000-01-01','2000-01-04')
assert not any(e['anchor_price']=='9'and e['known_on_saved_bar']=='2000-01-03'for e in r['episodes'])
assert any(e['anchor_price']=='9'and e['known_on_saved_bar']=='2000-01-04'for e in r['episodes'])
for vals in [[(10,10,10)]*5,[(x-1,x+1,x)for x in range(10,15)]]:
 q=synthetic(vals);assert not discover(q,q['bars'][0]['date'],q['bars'][-1]['date'])['episodes']
q=synthetic([(9,11,10),(7,10,8),(8,12,10)],['2000-01-03']);assert not discover(q,'2000-01-01','2000-01-03')['episodes']
assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in hashes.items())
v={'schema':'m1-revisit-frame-verification/1','research_driver_runs':3,'driver_rerun_reason':'Storage normalization only after first numerical run; repeated full views -> shared snapshot -> indexed episode references. Same numerical selected summaries preserved.','verification_runs':1,
   'automatic_seed_observations':observations,'independently_enumerated_witness_occurrences':witness_checks,'unique_episodes':len(seen_events),'unique_frames':len(seen_frames),'losslessly_reconstructed_current_views':current_view_checks,
   'unique_selected_scope_prefix_checks':prefix_checks,'eleven_scope_future_poison_and_positive_affine_checks':'PASS',
   'synthetic_monotonic_constant_equality_overshoot_new_wick_gap_checks':'PASS','wick_31_40_anchor_retained_without_close_crossing_episode':'PASS',
   'append_episode_and_frame_ids_stable':'PASS','registry_raw_sha256':hashlib.sha256(raw).hexdigest(),'registry_gzip_roundtrip':'PASS','registry_gzip_bytes':len(packed),
   'input_sha256_unchanged':hashes,'formal_formation_rule':'NOT_ESTABLISHED','classification':'NOT_VALIDATED','core_usefulness':'NOT_ESTABLISHED','actions':'NOT_EVALUATED','Android':'NOT_TESTED_NEW_BUILD','old_driver_runs':0,'core_recomputations':0,'original_product_tests':'NOT_RUN','PDF_visual_QA':'NOT_YET_CREATED'}
(p/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(json.dumps(v,ensure_ascii=False))
