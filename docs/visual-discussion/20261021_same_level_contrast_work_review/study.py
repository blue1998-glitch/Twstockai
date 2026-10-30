"""Matched saved-source contrasts; no approved same-level merge labels exist here."""
from pathlib import Path
from decimal import Decimal as D
from itertools import product
from collections import defaultdict
import gzip,json,hashlib,os

ROOT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('CONTRAST_SOURCE','/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json'))
REGISTRY=Path(os.environ.get('CONTRAST_REGISTRY','/workspace/scratch/89f271ea68f4/overlap-role-research/overlap-role-registry.json.gz'))
NESTED=Path(os.environ.get('CONTRAST_NESTED_DECISION','/workspace/scratch/e9363d3b9105/b-nested-band-decision/decision.json'))
VOLUME=Path(os.environ.get('CONTRAST_VOLUME_DECISION','/workspace/scratch/e9363d3b9105/b-price-hold-decision/decision.json'))
EXPECTED_SOURCE='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
EXPECTED_REGISTRY='270a0b20ae2ac5e8e258c79b4170988f4b63d1272ab4c96c90bc6ace6740ef82'
SELECTED={'reference':('2025-12-22','2025-12-31'),'close_inside':('2026-02-02','2026-02-23'),'sides_crossed':('2026-02-26','2026-03-05')}
CUTS=['2025-12-31','2026-01-02','2026-02-09','2026-02-10','2026-02-23','2026-02-24','2026-03-03','2026-03-04','2026-03-05','2026-03-06','2026-05-29']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):(ROOT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def price(b):return {k:b[k]for k in ('date','open','high','low','close')}
def loc(c,lo,hi):
 c,lo,hi=map(D,(c,lo,hi))
 return 'BELOW'if c<lo else'ABOVE'if c>hi else'AT_LOW'if c==lo else'AT_HIGH'if c==hi else'INSIDE'
def positive_overlap(a,b,c,d):return max(D(a),D(c))<min(D(b),D(d))
def left(z,lm,tm):return tm[lm[z['leg_ids'][0]]['from_turn_id']]['left_evidence_date']
def disjoint(a,b):return a['path_end']<b['path_start']or b['path_end']<a['path_start']

def query_saved_registry(reg):
 """Explicit retrospective B cohort. Counts are overlapping saved combinations."""
 zs=reg['zones'];lm={x['leg_id']:x for x in reg['legs']};tm={x['turn_id']:x for x in reg['turns']}
 eligible=[];strict=defaultdict(list);coarse=defaultdict(list)
 for a,b,vi,gi in reg['pairs']:
  old,new=zs[a],zs[b]
  if old['code']!='2884'or not('2025-11-06'<=old['path_start']<new['path_start']<='2026-05-29')or new['known_on_saved_bar']>'2026-05-29':continue
  if any(z['path_start']<='2026-04-27'and z['path_end']>='2026-04-16'for z in (old,new)):continue
  if reg['listed_gap_sets'][gi]or left(new,lm,tm)<=old['known_on_saved_bar']:continue
  if not positive_overlap(old['common_close_low'],old['common_close_high'],new['common_close_low'],new['common_close_high']):continue
  if not positive_overlap(old['raw_path_frame']['observed_low'],old['raw_path_frame']['observed_high'],new['raw_path_frame']['observed_low'],new['raw_path_frame']['observed_high']):continue
  row={'older_zone_id':old['zone_id'],'later_zone_id':new['zone_id'],'has_saved_source_close_inside_old_common':bool(reg['actual_close_visit_sets'][vi])}
  eligible.append(row);strict[(a,new['common_close_low'],new['common_close_high'])].append((b,row));coarse[a].append((b,row))
 def contrast_count(groups):
  both=total=0
  for rows in groups.values():
   yes=[b for b,r in rows if r['has_saved_source_close_inside_old_common']];no=[b for b,r in rows if not r['has_saved_source_close_inside_old_common']]
   if yes and no:both+=1
   total+=sum(disjoint(zs[a],zs[b])for a,b in product(yes,no))
  return {'groups_with_both_close_visit_states':both,'nonoverlapping_later_source_contrast_combinations':total}
 return {'cohort':'B/2884 frozen pairs, source starts Nov6_2025 onward; later available by May29_2026; full later source after older known; positive common/raw overlap; no listed gap between confirmations; exclude either source intersecting closed April16_27 microperiod','eligible_saved_pairs':len(eligible),'same_later_common_bounds':contrast_count(strict),'same_coarse_relations':contrast_count(coarse),'eligible_pairs':eligible,'not_independent_market_samples':True,'not_success_rates_or_approved_merge_labels':True,'manual_example_selection':'Explicit illustrative IDs after inspection; no nearest-distance or predictive rank'}

def select(reg):
 zones={}
 for name,(a,b)in SELECTED.items():
  found=[z for z in reg['zones']if z['code']=='2884'and z['path_start']==a and z['path_end']==b];assert len(found)==1;zones[name]=found[0]
 lm={x['leg_id']:x for x in reg['legs']};tm={x['turn_id']:x for x in reg['turns']};lids={i for z in zones.values()for i in z['leg_ids']};tids={lm[i][k]for i in lids for k in ('from_turn_id','to_turn_id')}
 return {'selection':'RETROSPECTIVE_FIXED_EXAMPLES_NOT_FORMAL_SMALL_BANDS','zones':zones,'legs':{i:lm[i]for i in sorted(lids)},'turns':{i:tm[i]for i in sorted(tids)},'original_nested_B_answer':json.loads(NESTED.read_text()),'latest_volume_decision':json.loads(VOLUME.read_text()),'cutoffs':CUTS}

def day_fact(bar,previous,lo,hi):
 current=loc(bar['close'],lo,hi);prev=loc(previous['close'],lo,hi)if previous else None
 direction='DOWN_ACROSS_BOTH_BOUNDARIES'if prev=='ABOVE'and current=='BELOW'else'UP_ACROSS_BOTH_BOUNDARIES'if prev=='BELOW'and current=='ABOVE'else None
 return {'bar':price(bar),'previous_price_bar':price(previous)if previous else None,'close_location':current,'close_on_or_inside_reference':D(lo)<=D(bar['close'])<=D(hi),'daily_range_intersects_reference':D(bar['low'])<=D(hi)and D(bar['high'])>=D(lo),'adjacent_saved_close_sides_crossing':direction,'intraday_order_or_continuous_trade_path_inferred':False}

def observe(bars,data,cutoff):
 known=[b for b in bars if b['date']<=cutoff];ref=data['zones']['reference']
 if cutoff<ref['known_on_saved_bar']:return {'cutoff':cutoff,'reference':None,'price_history':[],'activities':{},'formal_merge':None,'historical_signal_eligible':False}
 lo,hi=ref['common_close_low'],ref['common_close_high'];facts=[day_fact(b,known[i-1]if i else None,lo,hi)for i,b in enumerate(known)if b['date']>=ref['known_on_saved_bar']]
 by={f['bar']['date']:f for f in facts};activities={}
 for name,z in data['zones'].items():
  if z['known_on_saved_bar']>cutoff:continue
  bs=[b for b in known if z['path_start']<=b['date']<=z['path_end']];source_facts=[]
  if name!='reference':source_facts=[by[b['date']]for b in bs]
  current=known[-1]
  activities[name]={'birth':{'zone_id':z['zone_id'],'source_period':[z['path_start'],z['path_end']],'known_on':z['known_on_saved_bar'],'common':[z['common_close_low'],z['common_close_high']],'raw':[z['raw_path_frame']['observed_low'],z['raw_path_frame']['observed_high']],'source_records':len(bs),'source_price_bars':[price(b)for b in bs],'later_source_facts_vs_reference':source_facts,'right_price_bar':price(next(b for b in known if b['date']==z['known_on_saved_bar']))},'current_close_vs_activity_common':loc(current['close'],z['common_close_low'],z['common_close_high'])}
 return {'cutoff':cutoff,'reference':{'zone_id':ref['zone_id'],'known_on':ref['known_on_saved_bar'],'common':[lo,hi]},'price_history':facts,'activities':activities,'formal_merge':None,'formal_parent':None,'historical_signal_eligible':False,'holding_confirmation':None}

def run():
 assert sha(SOURCE)==EXPECTED_SOURCE and sha(REGISTRY)==EXPECTED_REGISTRY
 reg=json.loads(gzip.decompress(REGISTRY.read_bytes()));data=select(reg);source=json.loads(SOURCE.read_text());query=query_saved_registry(reg)
 for z in data['zones'].values():
  bs=[b for b in source['bars']if z['path_start']<=b['date']<=z['path_end']];raw=z['raw_path_frame']
  assert len(bs)==raw['records']and min(D(b['low'])for b in bs)==D(raw['observed_low'])and max(D(b['high'])for b in bs)==D(raw['observed_high'])
  assert next(b for b in source['bars']if b['date']==z['known_on_saved_bar'])==z['right_evidence_bar']
 views={cut:observe(source['bars'],data,cut)for cut in CUTS}
 write('study-inputs.json',data);write('registry-query.json',query);write('cutoff-views.json',views);write('contrast-evidence.json',views[CUTS[-1]])
 write('source-provenance.json',{'base_commit':'71dbc062a88efbe21e3b2d360b9156c1d4a14dab','inputs':[{'local':str(p),'sha256':sha(p)}for p in (SOURCE,REGISTRY,NESTED,VOLUME)],'price_basis_id':source['price_basis_id'],'source_gaps':source['source_gaps'],'method':'Query fixed saved pair cohort; copy three exact frozen activities. New interval-side/close-visit projection only. Manual same-level identity remains unanswered.'})
 print(json.dumps({k:v for k,v in query.items()if k!='eligible_pairs'},ensure_ascii=False,indent=2))
 for name,z in views[CUTS[-1]]['activities'].items():
  fs=z['birth']['later_source_facts_vs_reference'];print(name,'source',z['birth']['source_records'],'inside',[f['bar']['date']for f in fs if f['close_on_or_inside_reference']],'contact',[f['bar']['date']for f in fs if f['daily_range_intersects_reference']],'crosses',[(f['bar']['date'],f['adjacent_saved_close_sides_crossing'])for f in fs if f['adjacent_saved_close_sides_crossing']])
if __name__=='__main__':run()
