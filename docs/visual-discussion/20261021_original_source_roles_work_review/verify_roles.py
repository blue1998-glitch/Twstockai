"""Independent geometry/source checks and new projection-isolation tests only."""
import copy,gzip,json
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path
from source_roles import ROOT,load_inputs,catalog,view,write,digest

src,cores,prior,sel=load_inputs();r=json.loads(gzip.decompress((ROOT/'source-role-registry.json.gz').read_bytes()));saved=json.loads(gzip.decompress((ROOT/'selected-source-roles.json.gz').read_bytes()))
pm={p['id']:p for p in r['pivots']};cm={c['context_id']:c for c in r['contexts']};zm={z['zone_id']:z for z in r['zones']}
checks=defaultdict(int)
for code,c in cores.items():
 bars={b['date']:b for b in src[code]['bars']}
 for p in c['pivots']:
  field='high'if p['kind']=='HIGH'else'low'
  assert all(D(bars[d][field])==D(p['price'])for d in p['source_dates'])
  assert p['occurred_at']in p['source_dates']
  checks['original_pivots_raw_price_and_dates']+=1
 groups=defaultdict(list)
 for p in c['pivots']:groups[(p['scale'],p['segment'])].append(p)
 adjacency=set()
 for ps in groups.values():
  ps.sort(key=lambda p:(p['occurred_index'],p['id']))
  adjacency.update((a['id'],b['id'])for a,b in zip(ps,ps[1:])if a['kind']!=b['kind'])
 original_boxes={b['id']:b for b in c['boxes']}
 for x in [q for q in r['contexts']if q['code']==code]:
  ps=[pm[i]for i in x['source_turn_ids']]
  assert all(p['scale']==x['scale']and p['segment']==x['segment']for p in ps)
  assert min(D(p['price'])for p in ps)==D(x['low'])and max(D(p['price'])for p in ps)==D(x['high'])
  if 'BRACKET'in x['kind']:assert tuple(x['source_turn_ids'])in adjacency
  else:
   b=original_boxes[x['context_id']];assert x['low']==b['research_bounds']['low']and x['high']==b['research_bounds']['high']
  assert x['start']==ps[0]['occurred_at']and x['source_end']==ps[-1]['occurred_at']
  assert x['known_on']>=max(p['confirmed_at']for p in ps)
  assert x['listed_gap_dates']==[d for d in src[code]['source_gaps']['known_calendar_missing_dates']if x['start']<=d<=x['known_on']]
  checks['original_context_bounds_adjacency_scale_segment_and_gaps']+=1

# Independent all-pair enumeration, including omission of disjoint prices.
expected={}
for iz,z in enumerate(r['zones']):
 for ic,c in enumerate(r['contexts']):
  if z['code']!=c['code']:continue
  lo,hi=D(c['low']),D(c['high']);zl,zh=D(z['common_close_low']),D(z['common_close_high'])
  if hi<zl or zh<lo:continue
  price='CONTEXT_PRICE_CONTAINS_CORE'if lo<=zl and zh<=hi else 'CORE_CONTAINS_CONTEXT_PRICE'if zl<=lo and hi<=zh else 'TOUCH_ONLY'if hi==zl or zh==lo else 'PRICE_OVERLAP_ONLY'
  a,b,c0,d=c['start'],c['source_end'],z['path_start'],z['path_end']
  time='CONTEXT_ENCLOSES_ZONE_PATH'if a<=c0 and d<=b else 'ZONE_PATH_ENCLOSES_CONTEXT'if c0<=a and b<=d else 'CONTEXT_SOURCE_BEFORE_ZONE_PATH'if b<c0 else 'CONTEXT_SOURCE_AFTER_ZONE_PATH'if d<a else 'TIME_OVERLAP_ONLY'
  dates=sorted({date for p in c['source_turn_ids']for date in pm[p]['source_dates']if c0<=date<=z['known_on_saved_bar']})
  expected[iz,ic]=[iz,ic,max(z['known_on_saved_bar'],c['known_on']),int(c['known_on']>z['known_on_saved_bar']),r['price_codes'].index(price),r['time_codes'].index(time),a<=c0 and z['known_on_saved_bar']<=b,dates]
assert {(q[0],q[1]):q for q in r['links']}==expected
checks['independent_link_reconstructions']=len(expected)
for o in r['observations'].values():
 zindices=set(o['zone_indices']);code=o['code'];cut=o['cutoff']
 projected={tuple(q[:3])for q in r['links']if q[0]in zindices and q[2]<=cut}
 v=view(src[code],cores[code],[r['zones'][i]for i in o['zone_indices']],cut)
 got={(next(i for i in zindices if r['zones'][i]['zone_id']==q['zone_id']),next(i for i,c in enumerate(r['contexts'])if c['context_id']==q['context_id']),q['known_on'])for q in v['links']}
 assert projected==got;checks['prior_pool_observation_projections']+=1

projections={}
for name,v in saved.items():
 code=zm[v['zone_ids'][0]]['code']if v['zone_ids']else sel[name]['code']
 zs=[zm[i]for i in v['zone_ids']];cut=v['cutoff']
 assert view(src[code],cores[code],zs,cut)==v;checks['selected_view_reconstructions']+=1
 # Every distinct saved-bar cutoff from first zone birth to observation.
 if not zs:continue
 for bar in src[code]['bars']:
  day=bar['date']
  if min(z['known_on_saved_bar']for z in zs)<=day<=cut:
   key=(code,tuple(v['zone_ids']),day)
   if key in projections:continue
   now=view(src[code],cores[code],zs,day)
   shorter=copy.deepcopy(src[code]);shorter['bars']=[b for b in shorter['bars']if b['date']<=day]
   assert view(shorter,cores[code],zs,day)==now
   fullpairs={(q['zone_id'],q['context_id']):q for q in v['links']}
   assert all(fullpairs[(q['zone_id'],q['context_id'])]==q for q in now['links'])
   assert all(q['known_on']<=day for q in now['links'])
   projections[key]=True;checks['unique_prefix_and_immutable_link_checks']+=1
 # Poison every future payload and all asof interpretation fields; no core engine is run.
 poison=copy.deepcopy(cores[code]);poison_src=copy.deepcopy(src[code])
 for p in poison['pivots']:
  if max(p['confirmed_at'],p['first_observed_at'],max(p['source_dates']))>cut:p['price']='999999'
 for b in poison['boxes']:
  if max(b['confirmed_at'],b['first_observed_at'])>cut:b['research_bounds']={'low':'-9999','high':'999999'}
  b['anchor_relation']={'POISON':'FUTURE'};b['path']={'POISON':'FUTURE'};b['interpretation']={'POISON':'FUTURE'}
 for k in list(poison):
  if k not in ['pivots','boxes']:poison[k]={'POISON':'FUTURE'}
 for b in poison_src['bars']:
  if b['date']>cut:b.update(open='99999',high='999999',low='-9999',close='77777')
 assert view(poison_src,poison,zs,cut)==v;checks['future_payload_and_asof_fields_poison_checks']+=1

# Specific boundary cases are consequences, not rules in research generation.
pair=next(c for c in r['contexts']if c['code']=='2884'and c['scale']=='0.03'and c['start']=='2026-09-17'and c['source_end']=='2026-10-01')
assert pair['low']=='44.20'and pair['high']=='47.35'and pair['known_on']=='2026-10-07'
assert pair['context_id']not in saved['A-Oct6']['available_context_ids']
q=next(q for q in saved['A-Oct7']['links']if q['context_id']==pair['context_id'])
assert q['context_timing']=='LATER_CONTEXT_ADDED_WITHOUT_BACKFILL'and q['path_time_relation']=='TIME_OVERLAP_ONLY'
assert q['price_relation']=='CONTEXT_PRICE_CONTAINS_CORE'and not q['encloses_right_evidence_window']
assert saved['A-fixed-core-2026-10-14']['current_context_close_relations'][pair['context_id']]=='INSIDE'
assert all(saved['A-fixed-core-'+d]['current_context_close_relations'][pair['context_id']]=='ABOVE'for d in ['2026-10-15','2026-10-16'])
boxes=[c for c in r['contexts']if c['code']=='1101'and 'BOX_NOT'in c['kind']and c['start']=='2025-04-08'and c['source_end']=='2025-05-13']
assert {(c['scale'],c['known_on'],c['low'],c['high'])for c in boxes}=={('0.03','2025-05-14','28.45','31.40'),('0.06','2025-05-27','28.45','31.40')}
assert all(saved['ABC-Jun2']['current_context_close_relations'][c['context_id']]=='BELOW'for c in boxes)
assert max(D(c['high'])for c in r['contexts']if c['code']=='2884'and 'BOX_NOT'in c['kind'])==D('39.10')
assert any(p['occurred_at']=='2023-05-02'and p['price']=='40.25'and p['confirmed_at']=='2023-05-09'and p['scale']=='0.03'for p in r['pivots'])
checks['specific_availability_and_role_assertions']=12
# Source hashes remain exact; no source writes occurred.
prov=json.loads((ROOT/'source-provenance.json').read_text())
for path,info in prov['files'].items():assert digest(Path(path).read_bytes())==info['sha256']
checks['unchanged_input_fingerprints']=len(prov['files'])
write(ROOT/'verification.json',{'status':'PASS','checks':dict(checks),'driver_runs':1,'verification_runs':1,
 'original_core_recomputations':0,'prior_driver_or_prior_test_reruns':0,'product_classifier_tests':0,'Android':'NOT_TESTED_NEW_BUILD',
 'limits':'Metadata qualification is not historical replay or independent market validation. Source availability/publication and original historical snapshots remain unverified/null.'})
print(json.dumps(dict(checks)))
