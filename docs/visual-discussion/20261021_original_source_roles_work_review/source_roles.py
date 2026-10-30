"""Read frozen original metadata; attach research relations to saved close zones.

No core recomputation, ranking, parent selection or historical snapshot claim.
"""
import argparse, gzip, hashlib, json
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=Path('/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json')
COMPARISON=Path('/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json')
CORE=Path('/workspace/scratch/54685b8dac93/independent-level-review/input/core-2884-latest.json')
PRIOR=ROOT.parent/'common-band-research'
def digest(b): return hashlib.sha256(b).hexdigest()
def uid(x): return 'sha256:'+digest(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def load_inputs(source=SOURCE,comparison=COMPARISON,core=CORE,prior=PRIOR):
 s=json.loads(source.read_text());t=json.loads(comparison.read_text())
 c=json.loads(core.read_text());r=json.loads(gzip.decompress((prior/'pool-common-span-registry.json.gz').read_bytes()))
 return {'2884':s,'1101':t},{'2884':c,'1101':t['core']},r,json.loads((prior/'selected-common-spans.json').read_text())

def catalog(core,source,cutoff):
 """Project allowed static fields ONLY. Never return future or current-asof fields."""
 code=source['code']; available={};groups=defaultdict(list)
 for p in core['pivots']:
  # Preserve original consecutive order before availability filtering.
  groups[(p['scale'],p['segment'])].append(p)
  known=max(p['confirmed_at'],p['first_observed_at'],max(p['source_dates']))
  if known>cutoff: continue
  available[p['id']]={k:p[k] for k in ('id','kind','price','occurred_at','source_dates','confirmed_at','first_observed_at','scale','segment')}
  available[p['id']].update(code=code,known_on=known)
 contexts=[]
 def finish(obj):
  obj['code']=code
  obj['listed_gap_dates']=[d for d in source['source_gaps']['known_calendar_missing_dates'] if obj['start']<=d<=obj['known_on']]
  obj['calendar_qualification']='LISTED_GAPS_ONLY_NOT_EXHAUSTIVE'
  obj['formal_parent']=None;obj['formal_membership']=None
  contexts.append(obj)
 for (scale,segment),ps in groups.items():
  ps.sort(key=lambda p:(p['occurred_index'],p['id']))
  for a,b in zip(ps,ps[1:]):
   if a['id'] not in available or b['id'] not in available or a['kind']==b['kind']:continue
   known=max(available[a['id']]['known_on'],available[b['id']]['known_on'])
   lo,hi=sorted([a['price'],b['price']],key=D)
   obj={'kind':'ADJACENT_ORIGINAL_PIVOT_PRICE_BRACKET_NOT_BOX','scale':scale,'segment':segment,
        'start':a['occurred_at'],'source_end':b['occurred_at'],'known_on':known,
        'low':lo,'high':hi,'source_turn_ids':[a['id'],b['id']]}
   obj['context_id']=uid({'code':code,'pair_ids':obj['source_turn_ids']});finish(obj)
 for b in core['boxes']:
  if max(b['confirmed_at'],b['first_observed_at'])>cutoff or not all(i in available for i in b['source_turn_ids']):continue
  known=max(b['confirmed_at'],b['first_observed_at'],*[available[i]['known_on']for i in b['source_turn_ids']])
  if known>cutoff:continue
  finish({'kind':'SAVED_ORIGINAL_RESEARCH_BOX_NOT_FORMAL_PARENT','context_id':b['id'],
          'scale':b['scale'],'segment':b['segment'],'start':b['start'],'source_end':b['source_end'],
          'known_on':known,'low':b['research_bounds']['low'],'high':b['research_bounds']['high'],
          'source_turn_ids':b['source_turn_ids']})
 return {'pivots':sorted(available.values(),key=lambda x:x['id']),'contexts':sorted(contexts,key=lambda x:x['context_id'])}

def time_relation(a,b,c,d):
 if a<=c and d<=b:return 'CONTEXT_ENCLOSES_ZONE_PATH'
 if c<=a and b<=d:return 'ZONE_PATH_ENCLOSES_CONTEXT'
 if b<c:return 'CONTEXT_SOURCE_BEFORE_ZONE_PATH'
 if d<a:return 'CONTEXT_SOURCE_AFTER_ZONE_PATH'
 return 'TIME_OVERLAP_ONLY'
def price_relation(lo,hi,zlo,zhi):
 if hi<zlo or zhi<lo:return 'DISJOINT'
 if lo<=zlo and zhi<=hi:return 'CONTEXT_PRICE_CONTAINS_CORE'
 if zlo<=lo and hi<=zhi:return 'CORE_CONTAINS_CONTEXT_PRICE'
 if max(lo,zlo)==min(hi,zhi):return 'TOUCH_ONLY'
 return 'PRICE_OVERLAP_ONLY'
def relation(z,c,pivots):
 if z['code']!=c['code']:return None
 pr=price_relation(D(c['low']),D(c['high']),D(z['common_close_low']),D(z['common_close_high']))
 if pr=='DISJOINT':return None
 known=max(z['known_on_saved_bar'],c['known_on'])
 return {'zone_id':z['zone_id'],'context_id':c['context_id'],'known_on':known,
         'context_timing':'AVAILABLE_AT_ZONE_BIRTH' if c['known_on']<=z['known_on_saved_bar']else 'LATER_CONTEXT_ADDED_WITHOUT_BACKFILL',
         'price_relation':pr,'path_time_relation':time_relation(c['start'],c['source_end'],z['path_start'],z['path_end']),
         'encloses_right_evidence_window':c['start']<=z['path_start'] and z['known_on_saved_bar']<=c['source_end'],
         'original_point_dates_in_zone_evidence':sorted({d for i in c['source_turn_ids'] for d in pivots[i]['source_dates'] if z['path_start']<=d<=z['known_on_saved_bar']}),
         'formal_parent':None,'formal_membership':None}
def location(price,lo,hi):
 v=D(price);lo=D(lo);hi=D(hi)
 return 'BELOW'if v<lo else 'ABOVE'if v>hi else 'AT_LOW'if v==lo else 'AT_HIGH'if v==hi else 'INSIDE'
def view(source,core,zones,cutoff):
 cat=catalog(core,source,cutoff);pm={p['id']:p for p in cat['pivots']}
 zs=[z for z in zones if z['known_on_saved_bar']<=cutoff]
 links=[r for z in zs for c in cat['contexts'] if (r:=relation(z,c,pm)) is not None]
 bars=[b for b in source['bars'] if b['date']<=cutoff];last=bars[-1]
 return {'cutoff':cutoff,'last_bar':last,'zone_ids':[z['zone_id']for z in zs],
         'available_original_pivot_ids':[p['id']for p in cat['pivots']],
         'available_context_ids':[c['context_id']for c in cat['contexts']],
         'links':links,'current_context_close_relations':{c['context_id']:location(last['close'],c['low'],c['high'])for c in cat['contexts']},
         'current_zone_close_relations':{z['zone_id']:location(last['close'],z['common_close_low'],z['common_close_high'])for z in zs},
         'qualification':'RETROSPECTIVE_SAVED_METADATA_FILTER_NOT_HISTORICAL_CORE_REPLAY',
         'formal_parent':None,'selected_context':None,'primary_pressure_id':None,'historical_selection_time':None,
         'historical_signal_eligible':False,'classification':'NOT_VALIDATED','core_usefulness':'NOT_ESTABLISHED',
         'actions':'NOT_EVALUATED','capital_growth_flywheel_effectiveness':'NOT_EVALUATED','Android':'NOT_TESTED_NEW_BUILD'}

def main(a):
 src,cores,prior,selected=load_inputs(a.source,a.comparison,a.core,a.prior)
 zones={z['zone_id']:z for z in prior['zones']}
 for r in selected.values():
  for z in r['zones']:
   if z['zone_id']in zones:assert zones[z['zone_id']]==z
   zones[z['zone_id']]=z
 cats={code:catalog(cores[code],s,s['as_of'])for code,s in src.items()}
 pivots=[p for x in cats.values()for p in x['pivots']];contexts=[c for x in cats.values()for c in x['contexts']]
 pm={p['id']:p for p in pivots};zlist=list(zones.values());zi={z['zone_id']:i for i,z in enumerate(zlist)};ci={c['context_id']:i for i,c in enumerate(contexts)}
 links=[r for z in zlist for c in contexts if (r:=relation(z,c,pm))is not None]
 pr=sorted({r['price_relation']for r in links});tr=sorted({r['path_time_relation']for r in links})
 packed=[[zi[r['zone_id']],ci[r['context_id']],r['known_on'],0 if r['context_timing']=='AVAILABLE_AT_ZONE_BIRTH'else 1,pr.index(r['price_relation']),tr.index(r['path_time_relation']),r['encloses_right_evidence_window'],r['original_point_dates_in_zone_evidence']]for r in links]
 observations={}
 for oid,o in prior['observations'].items():
  observations[oid]={k:o[k]for k in ('code','seed_start','cutoff')}
  observations[oid]['zone_indices']=[zi[prior['zones'][i]['zone_id']]for i in o['zone_indices']]
 # Reuse immutable prior candidates only. Later cutoffs observe their relationships, no new common driver.
 selections={name:(r['code'],r['cutoff'],r['zones'])for name,r in selected.items()}
 for date in ['2026-10-14','2026-10-15','2026-10-16']:
  selections['A-fixed-core-'+date]=('2884',date,selected['A-Oct7']['zones'])
 for date in ['2025-05-14','2025-05-26','2025-05-27']:
  selections['ABC-fixed-May13-core-'+date]=('1101',date,selected['ABC-May13']['zones'])
 details={name:view(src[code],cores[code],zs,cutoff)for name,(code,cutoff,zs)in selections.items()}
 registry={'schema':'m1-original-source-role-links/0.1','pivots':pivots,'contexts':contexts,'zones':zlist,
           'link_columns':['zone_index','context_index','known_on','timing_0_at_birth_1_later','price_code','time_code','encloses_evidence','point_source_dates_in_evidence'],
           'price_codes':pr,'time_codes':tr,'links':packed,'observations':observations,
           'current_view_recipe':'Filter contexts and links by known_on <= cutoff. Current close relations calculated once per reference; no votes or ranking.',
           'historical_qualification':'RETROSPECTIVE_METADATA_PROJECTION_NOT_SAVED_HISTORICAL_CORE_SNAPSHOT',
           'formal_parent':None,'selected_context':None}
 raw=json.dumps(registry,ensure_ascii=False,separators=(',',':')).encode();gz=gzip.compress(raw,mtime=0)
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-role-registry.json.gz').write_bytes(gz)
 selected_bytes=(json.dumps(details,ensure_ascii=False,indent=2)+'\n').encode()
 (a.out/'selected-source-roles.json.gz').write_bytes(gzip.compress(selected_bytes,mtime=0))
 summary={'prior_observations':len(observations),'unique_zones_including_external_manual_scopes':len(zlist),'original_pivots':len(pivots),
          'context_sources':len(contexts),'original_boxes':sum('BOX_NOT' in c['kind']for c in contexts),
          'adjacent_same_scale_segment_brackets':sum('BRACKET' in c['kind']for c in contexts),'price_intersecting_links':len(links),
          'birth_links':sum(r['context_timing']=='AVAILABLE_AT_ZONE_BIRTH'for r in links),'later_added_links':sum(r['context_timing'].startswith('LATER')for r in links),
          'registry_gzip_bytes':len(gz),'registry_raw_sha256':digest(raw),'selected_views':len(details),
          'qualification':'Source relations only, overlapping research observations are not independent market samples.',
          'classification':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD','capital_growth_flywheel_effectiveness':'NOT_EVALUATED'}
 write(a.out/'summary.json',summary)
 write(a.out/'source-provenance.json',{'files':{str(p):{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size}for p in [a.source,a.comparison,a.core,a.prior/'pool-common-span-registry.json.gz',a.prior/'selected-common-spans.json']},
       '2884_core_result_id':cores['2884']['result_id'],'1101_core_result_id':cores['1101']['result_id'],
       'core_origin_commit':'4c8d483afc7bb052b01cb6a9b99db92dfbd95612','2884_core_git_path':'股票系統M1_v0_18/graph_core_chart/generated/core-2884-latest.json',
       'prior_commit':'abe82e5cc7c1825da662a058a222c69a392160bb','unavailable_historical_core_snapshot_2026_10_07':None})
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=SOURCE);ap.add_argument('--comparison',type=Path,default=COMPARISON);ap.add_argument('--core',type=Path,default=CORE);ap.add_argument('--prior',type=Path,default=PRIOR);ap.add_argument('--out',type=Path,default=ROOT);main(ap.parse_args())
