"""Independent signed-change turns, exhaustive shared spans and normalized joins."""
from pathlib import Path
from decimal import Decimal as D
from copy import deepcopy
from itertools import combinations
import argparse,json,gzip,hashlib
from common_research import common,digest

ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--prior-dir',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
p=Path(a.out);prior=Path(a.prior_dir);inputs=[Path(a.source),Path(a.comparison),prior/'pool-revisit-registry.json.gz',prior/'selected-revisits.json'];hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest()for f in inputs}
s,t=[json.loads(f.read_text())for f in inputs[:2]];old=json.loads(gzip.decompress(inputs[2].read_bytes()));old_episodes={e['episode_id']:e for e in old['episode_table']};selected=json.loads((p/'selected-common-spans.json').read_text());reg_raw=gzip.decompress((p/'pool-common-span-registry.json.gz').read_bytes());reg=json.loads(reg_raw);summary=json.loads((p/'summary.json').read_text());assert hashlib.sha256(reg_raw).hexdigest()==summary['registry_raw_sha256']

def independent_turns(source,start,cut):
 rows=[b for b in source['bars']if start<=b['date']<=cut];gaps=source['source_gaps']['known_calendar_missing_dates'];segments=[[]]
 for b in rows:
  if segments[-1]and any(segments[-1][-1]['date']<=g<=b['date']for g in gaps):segments.append([])
  segments[-1].append(b)
 result=[]
 for seg in segments:
  changes=[]
  for i in range(1,len(seg)):
   delta=D(seg[i]['close'])-D(seg[i-1]['close'])
   if delta:changes.append((i,1 if delta>0 else-1))
  for(prev_i,prev_sign),(i,sign)in zip(changes,changes[1:]):
   if sign!=prev_sign:result.append(('HIGH'if prev_sign>0 else'LOW',seg[prev_i]['date'],seg[i-1]['date'],seg[prev_i]['close'],seg[prev_i-1]['date'],seg[i]['date']))
 return result

def check_objects(src,r):
 assert [(v['kind'],v['plateau_start'],v['plateau_end'],v['close'],v['left_evidence_date'],v['known_on_saved_bar'])for v in r['turns']]==independent_turns(src,r['seed_start'],r['cutoff'])
 turns={x['turn_id']:x for x in r['turns']};leg_map={x['leg_id']:x for x in r['legs']};expected=set();checks=0
 for turn in r['turns']:assert turn['turn_id']==digest({k:v for k,v in turn.items()if k!='turn_id'})
 for leg in r['legs']:
  assert leg['leg_id']==digest({k:v for k,v in leg.items()if k!='leg_id'})
  left,right=[turns[leg[k]]for k in ['from_turn_id','to_turn_id']]
  assert left['kind']!=right['kind']and left['known_on_saved_bar']<=right['known_on_saved_bar']
  assert D(leg['close_low'])==min(D(left['close']),D(right['close']))and D(leg['close_high'])==max(D(left['close']),D(right['close']))
 for i in range(len(r['legs'])):
  for j in range(i+1,len(r['legs'])):
   used=r['legs'][i:j+1]
   if any(a['to_turn_id']!=b['from_turn_id']for a,b in zip(used,used[1:])):continue
   lo=max(D(x['close_low'])for x in used);hi=min(D(x['close_high'])for x in used)
   if lo<hi:expected.add(tuple(x['leg_id']for x in used))
 assert {tuple(z['leg_ids'])for z in r['zones']}==expected
 for z in r['zones']:
  assert z['zone_id']==digest({k:v for k,v in z.items()if k!='zone_id'})
  used=[leg_map[x]for x in z['leg_ids']];assert z['leg_count']==len(used)>=2
  assert D(z['common_close_low'])==max(D(x['close_low'])for x in used)and D(z['common_close_high'])==min(D(x['close_high'])for x in used)
  assert z['path_start']==used[0]['path_start']and z['path_end']==used[-1]['path_end']and z['known_on_saved_bar']==used[-1]['known_on_saved_bar']
  assert z['path_end']<z['known_on_saved_bar']<=r['cutoff']
  raw=[b for b in src['bars']if z['path_start']<=b['date']<=z['path_end']];f=z['raw_path_frame'];assert len(raw)==f['records']and digest(raw)==f['bars_fingerprint']
  assert min(D(b['low'])for b in raw)==D(f['observed_low'])and max(D(b['high'])for b in raw)==D(f['observed_high'])
  assert z['right_evidence_bar']==next(b for b in src['bars']if b['date']==z['known_on_saved_bar'])
  assert not any(z['path_start']<=g<=z['known_on_saved_bar']for g in src['source_gaps']['known_calendar_missing_dates'])
  assert z['formal_interval']is None and z['formal_price_bounds']is None;checks+=1
 return checks

observations=zone_checks=view_checks=link_checks=relation_checks=0
for obs_id,obs in reg['observations'].items():
 src=s if obs['code']=='2884'else t;episodes=[old_episodes[reg['revisit_episode_id_table'][i]]for i in obs['revisit_episode_indices']];r=common(src,obs['seed_start'],obs['cutoff'],episodes);observations+=1;zone_checks+=check_objects(src,r)
 for kind,key in [('turns','turn_indices'),('legs','leg_indices'),('zones','zone_indices')]:assert [reg[kind][i]for i in obs[key]]==r[kind]
 maximal={z['zone_id']for z in r['zones']if not any(set(z['leg_ids'])<set(other['leg_ids'])for other in r['zones'])}
 assert maximal=={reg['zones'][i]['zone_id']for i in obs['maximal_zone_indices']}
 bar=obs['latest_bar'];c,l,h=[D(bar[k])for k in ['close','low','high']];views=[]
 for z in r['zones']:
  lo,hi=D(z['common_close_low']),D(z['common_close_high']);gaps=[g for g in obs['listed_missing_dates_in_observation']if z['path_start']<=g<=obs['cutoff']]
  views.append({'zone_id':z['zone_id'],'available_maximal_contiguous_span':z['zone_id']in maximal,'latest_close_to_common_span':'INSIDE_INCLUSIVE'if lo<=c<=hi else'BELOW'if c<lo else'ABOVE','latest_bar_to_common_span':'WHOLE_BELOW'if h<lo else'WHOLE_ABOVE'if l>hi else'OVERLAPS_OR_TOUCHES','crossed_listed_missing_dates':gaps,'source_qualified_for_current_relation':False if gaps else None,'selected':None});view_checks+=1
 assert views==r['zone_views']
 links=[]
 for z in r['zones']:
  ids=[]
  for e in episodes:
   if e['code']!=src['code']or e['known_on_saved_bar']>z['known_on_saved_bar']:continue
   if min(v['date']for v in e['strict_side_visits'])<z['path_start']:continue
   if D(z['common_close_low'])<=D(e['anchor_price'])<=D(z['common_close_high']):ids.append(e['episode_id'])
  links.append({'zone_id':z['zone_id'],'revisit_episode_ids':sorted(ids),'qualification':'SAVED_SOURCE_PROVENANCE_LINK_NOT_INDEPENDENT_VOTES'});link_checks+=len(ids)
 assert links==r['saved_revisit_links']
 pair_keys=set()
 for a,b in combinations([z for z in r['zones']if z['zone_id']in maximal],2):
  shared=set(a['leg_ids'])&set(b['leg_ids'])
  if shared:
   lo=max(D(a['common_close_low']),D(b['common_close_low']));hi=min(D(a['common_close_high']),D(b['common_close_high']))
   pair_keys.add((a['zone_id'],b['zone_id'],tuple(sorted(shared)),'POSITIVE_OVERLAP'if lo<hi else'TOUCH_ONLY'if lo==hi else'DISJOINT'))
 assert pair_keys=={(x['left_zone_id'],x['right_zone_id'],tuple(x['shared_leg_ids']),x['common_span_relation'])for x in r['maximal_shared_path_relations']};relation_checks+=len(pair_keys)

prefix_seen=set();prefixes=0;selected_zone_checks=0
old_selected=json.loads(inputs[3].read_text())
for name,r in selected.items():
 src=s if r['code']=='2884'else t;previous=next((v for v in old_selected.values()if v['code']==r['code']and v['seed_start']==r['seed_start']and v['cutoff']>=r['cutoff']),None)
 saved=previous['episodes']if r['revisit_link_input_status'].startswith('PROVIDED')else None
 assert saved is None or previous is not None
 assert common(src,r['seed_start'],r['cutoff'],saved)==r;selected_zone_checks+=check_objects(src,r)
 for b in [b for b in src['bars']if r['seed_start']<=b['date']<=r['cutoff']]:
  cut=b['date'];key=(r['code'],r['seed_start'],cut)
  if key in prefix_seen:continue
  prefix_seen.add(key);original=common(src,r['seed_start'],cut,saved);truncated={**src,'bars':[b for b in src['bars']if b['date']<=cut]}
  assert original==common(truncated,r['seed_start'],cut,saved)
  for kind in ['turns','legs','zones']:assert original[kind]==[v for v in r[kind]if v['known_on_saved_bar']<=cut]
  expected_links=[x for x in r['saved_revisit_links']if x['zone_id']in{z['zone_id']for z in original['zones']}]
  assert original['saved_revisit_links']==expected_links;prefixes+=1
 poison=deepcopy(src)
 for b in poison['bars']:
  if b['date']>r['cutoff']:
   for f in ['open','high','low','close']:b[f]='999999999'
 poison['source_gaps']['known_calendar_missing_dates'].append('2222-01-01');assert common(poison,r['seed_start'],r['cutoff'],saved)==r
 affine=deepcopy(src)
 for b in affine['bars']:
  for f in ['open','high','low','close']:b[f]=str(D(b[f])*10+7)
 ar=common(affine,r['seed_start'],r['cutoff'])
 assert [(z['path_start'],z['path_end'],z['known_on_saved_bar'],z['leg_count'])for z in ar['zones']]==[(z['path_start'],z['path_end'],z['known_on_saved_bar'],z['leg_count'])for z in r['zones']]
 assert [(v['available_maximal_contiguous_span'],v['latest_close_to_common_span'],v['latest_bar_to_common_span'])for v in ar['zone_views']]==[(v['available_maximal_contiguous_span'],v['latest_close_to_common_span'],v['latest_bar_to_common_span'])for v in r['zone_views']]

assert not selected['A-Oct5']['zones']and len(selected['A-Oct6']['zones'])==1
assert not selected['ABC-next-Jun11']['zones']and len(selected['ABC-next-Jun12']['zones'])==1
assert selected['B-May4']['maximal_shared_path_relations'][0]['common_span_relation']=='DISJOINT'
may=selected['ABC-May13'];assert any(z['right_evidence_bar']['date']=='2025-05-13'and z['right_evidence_bar']['high']=='31.40'for z in may['zones'])
g=selected['G2-full-manual-scope'];assert len(g['source_segments'])==2 and all(not(z['path_start']<='2023-08-03'<=z['known_on_saved_bar'])for z in g['zones'])
def synthetic(closes,gaps=[]):
 return {'code':'SYNTHETIC','source_gaps':{'known_calendar_missing_dates':gaps},'bars':[{'date':f'2000-01-{i+1:02d}','open':str(c),'high':str(D(c)+D('.2')),'low':str(D(c)-D('.2')),'close':str(c),'volume_shares_scaled':'1'}for i,c in enumerate(closes)]}
def run(src):return common(src,src['bars'][0]['date'],src['bars'][-1]['date'])
for values in [[10]*6,[10,11,12,13,14],[10,11,11,11]]:assert not run(synthetic(values))['zones']
touch=run(synthetic([11,12,10,11,9,10,8]));assert any(v['common_span_relation']=='TOUCH_ONLY'for v in touch['maximal_shared_path_relations'])
disjoint=run(synthetic([11,12,10,11,8,9,7]));assert any(v['common_span_relation']=='DISJOINT'for v in disjoint['maximal_shared_path_relations'])
plateau=run(synthetic([10,12,12,8,11,9]));turn=plateau['turns'][0];assert turn['plateau_start']=='2000-01-02'and turn['plateau_end']=='2000-01-03'and turn['known_on_saved_bar']=='2000-01-04'
gap=run(synthetic([11,12,10,11,8,9,7],['2000-01-04']));assert all(not(z['path_start']<='2000-01-04'<=z['known_on_saved_bar'])for z in gap['zones'])
assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in hashes.items())
v={'schema':'m1-common-span-verification/1','research_driver_runs':2,'driver_rerun_reason':'Lossless normalized storage only; same common/turn/leg/zone logic and selected results.','verification_runs':1,
 'automatic_observations':observations,'unique_turns':len(reg['turns']),'unique_legs':len(reg['legs']),'unique_zones':len(reg['zones']),
 'independent_zone_occurrence_checks':zone_checks,'selected_zone_checks':selected_zone_checks,'lossless_current_view_reconstructions':view_checks,'lossless_saved_revisit_provenance_joins':link_checks,'shared_path_relation_checks':relation_checks,
 'unique_selected_prefix_checks':prefixes,'sixteen_scope_future_poison_and_affine_geometry':'PASS','append_immutable_turn_leg_zone_and_birth_join_ids':'PASS_MAXIMAL_VIEWS_MAY_CHANGE',
 'synthetic_constant_monotonic_plateau_touch_disjoint_gap':'PASS','wick_May13_confirmation_bar_31_40_retained':'PASS','G2_gap_segment_boundary_preserved':'PASS',
 'input_sha256_unchanged':hashes,'registry_gzip_bytes':(p/'pool-common-span-registry.json.gz').stat().st_size,'registry_raw_sha256':hashlib.sha256(reg_raw).hexdigest(),
 'formal_formation_rule':'NOT_ESTABLISHED','classification':'NOT_VALIDATED','core_usefulness':'NOT_ESTABLISHED','actions':'NOT_EVALUATED','capital_growth_flywheel_effectiveness':'NOT_EVALUATED','Android':'NOT_TESTED_NEW_BUILD','old_driver_runs':0,'core_recomputations':0,'original_product_tests':'NOT_RUN','PDF_visual_QA':'NOT_YET_CREATED'}
(p/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(json.dumps(v,ensure_ascii=False))
