"""Fill finite composition gaps with the existing research definitions only."""
import copy,gzip,json,sys
from pathlib import Path
from observation_bundle import ROOT,BASE,load_inputs,earliest,project_history,sha,write
from overlap_roles import compare
sys.path.insert(0,str(BASE/'followup-role-research'))
from followup_roles import propose
if any((ROOT/name).exists()for name in ['evidence-extensions.json.gz','baseline-observation-bundles.json.gz','baseline-verification.json','baseline-summary.json']):
 raise SystemExit('PRESERVE_CHECKPOINT: extension or baseline already exists; use a separate fresh research output directory, never overwrite archived baseline.')
src,c=load_inputs(False);spec=json.loads((ROOT/'query-specs.json').read_text())
for filename in ['observation-bundles.json.gz','verification.json','summary.json']:
 (ROOT/('baseline-'+filename)).write_bytes((ROOT/filename).read_bytes())
existing={(p['older_zone_id'],p['later_zone_id'])for p in c['pairs']};missing={};targets={}
for group,sp in spec.items():
 code,start=sp['code'],sp['research_seed_start']
 for cut in sp['cutoffs']:
  zs=[z for z in c['zones']if z['code']==code and z['known_on_saved_bar']<=cut and earliest(z,c)>=start]
  for i,a in enumerate(zs):
   for b in zs[i+1:]:
    if a['known_on_saved_bar']==b['known_on_saved_bar']:continue
    old,new=(a,b)if a['known_on_saved_bar']<b['known_on_saved_bar']else(b,a)
    key=(old['zone_id'],new['zone_id'])
    if key not in existing:missing[key]=(old,new)
  for e in c['events']:
   if e['code']==code and e['known_on_saved_bar']<=cut and e['frozen_frame']['frame_start']>=start and c['histories'][e['event_id']]['archive_observed_through']<cut:
    targets[e['event_id']]=max(cut,targets.get(e['event_id'],cut))
newpairs=[compare(src[a['code']],a,b,c['turns'],c['legs'],b['known_on_saved_bar'])for a,b in missing.values()]
em={e['event_id']:e for e in c['events']};oldlinks={l['link_id']for l in c['followup_links']};newlinks={};histories={};checks=[]
for eid,cut in targets.items():
 e=em[eid];r=propose(src[e['code']],e,c['zones'],cut);old=c['histories'][eid]
 h={'event_id':eid,'archive_observed_through':cut,'episodes':r['episodes'],'derivation':'NEW_TRACE_FROM_SAVED_BARS_NOT_ORIGINAL_HISTORICAL_SNAPSHOT'}
 assert project_history(src[e['code']],h,old['archive_observed_through'])==project_history(src[e['code']],old,old['archive_observed_through'])
 histories[eid]=h;checks.append({'event_id':eid,'prior_observed_through':old['archive_observed_through'],'extended_through':cut,'prior_prefix_exactly_preserved':True})
 for l in r['links']:
  if l['link_id']not in oldlinks:
   newlinks[l['link_id']]={'event_id':eid,'episode_id':l['episode_id'],'zone_id':l['zone_id'],'known_on':l['known_on_saved_bar'],'status_at_birth':l['status_at_birth'],'end_known_at_birth':l['end_known_at_birth'],'link_id':l['link_id']}
summary={'new_comparisons':len(newpairs),'extended_event_traces':len(histories),'new_followup_links':len(newlinks),'prior_trace_prefixes_preserved':len(checks),'extension_generator_runs':1,'new_seed_turn_or_original_core_generation':0}
x={'summary':summary,'new_comparisons':newpairs,'extended_histories':histories,'new_followup_links':list(newlinks.values()),'trace_extension_receipts':checks,
   'qualification':'Supplemental research computed now from saved source bars; not backfilled into prior files and not proof of historical availability or selection.'}
raw=json.dumps(x,ensure_ascii=False,separators=(',',':')).encode();(ROOT/'evidence-extensions.json.gz').write_bytes(gzip.compress(raw,mtime=0));write(ROOT/'extension-summary.json',{**summary,'extension_raw_sha256':sha(raw)})
print(json.dumps(summary))
