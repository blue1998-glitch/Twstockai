"""Link six frozen activities with reviewed price paths; no formal band merging."""
from pathlib import Path
from decimal import Decimal as D
from itertools import combinations
import json,gzip,hashlib,os

ROOT=Path(__file__).resolve().parent
SOURCE_PATHS={'2884':Path(os.environ.get('BRIDGE_2884','/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json')),'1101':Path(os.environ.get('BRIDGE_1101','/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json'))}
REGISTRY=Path(os.environ.get('BRIDGE_OVERLAP','/workspace/scratch/89f271ea68f4/overlap-role-research/overlap-role-registry.json.gz'))
SOURCE_REGISTRY=Path(os.environ.get('BRIDGE_SOURCE_REGISTRY','/workspace/scratch/89f271ea68f4/source-role-research/source-role-registry.json.gz'))
CONTEXT=Path(os.environ.get('BRIDGE_G2_CONTEXT','/workspace/scratch/e9363d3b9105/return-context-research/study-inputs.json'))
B_PATH=Path(os.environ.get('BRIDGE_B_PATH','/workspace/scratch/e9363d3b9105/b-breakout-path-research/path-evidence.json'))
CROSS_FOLLOWUP=Path(os.environ.get('BRIDGE_PRIOR_FOLLOWUP','/workspace/scratch/e9363d3b9105/cross-case-followup-research/followup-results.json'))
EXPECTED={'2884':'ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901','1101':'184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15'}
CUTS={'B':['2026-06-17','2026-06-18','2026-06-22','2026-06-24','2026-06-26','2026-06-30'],'G2':['2023-07-06','2023-07-07','2023-07-18','2023-07-19','2023-07-25','2023-07-28','2023-07-31','2023-08-02']}
CODE={'B':'2884','G2':'1101'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,d):(ROOT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def price(b):return {k:b[k]for k in ('date','open','high','low','close')}
def side(v,p):return 'ABOVE'if D(v)>p else'BELOW'if D(v)<p else'EQUAL'
def interval(lo,hi,reflo,refhi):
 lo,hi,reflo,refhi=map(D,(lo,hi,reflo,refhi))
 if hi<reflo:return 'STRICTLY_BELOW'
 if lo>refhi:return 'STRICTLY_ABOVE'
 if lo==hi==reflo==refhi:return 'EQUAL'
 if hi==reflo or lo==refhi:return 'BOUNDARY_TOUCH'
 if reflo==refhi:return 'STRADDLES_REFERENCE'
 if lo==hi:return 'INSIDE_REFERENCE_RANGE'
 return 'POSITIVE_OVERLAP'

def select():
 reg=json.loads(gzip.decompress(REGISTRY.read_bytes()));sr=json.loads(gzip.decompress(SOURCE_REGISTRY.read_bytes()));ctx=json.loads(CONTEXT.read_text())
 names=[('B_advance','2884','2026-06-09','2026-06-17'),('B_high','2884','2026-06-17','2026-06-23'),('B_return','2884','2026-06-22','2026-06-25')]
 zones={}
 for name,code,start,end in names:
  found=[z for z in reg['zones']if z['code']==code and z['path_start']==start and z['path_end']==end];assert len(found)==1
  zones[name]=found[0]
 for name,key in [('G_earlier','earlier-local'),('G_lower','lower-local'),('G_rebound','rebound-local')]:zones[name]=ctx['zones'][key]
 rzm={z['zone_id']:z for z in reg['zones']};szm={z['zone_id']:z for z in sr['zones']}
 for z in zones.values():assert z==rzm[z['zone_id']]==szm[z['zone_id']]
 lm={x['leg_id']:x for x in reg['legs']};tm={x['turn_id']:x for x in reg['turns']}
 lids={i for z in zones.values()for i in z['leg_ids']};tids={lm[i][k]for i in lids for k in ('from_turn_id','to_turn_id')}
 bpath=json.loads(B_PATH.read_text());gpath=json.loads(CROSS_FOLLOWUP.read_text())['G2'];gref=ctx['pivots']['later-low']
 events={'B':[{k:e[k]for k in ('date','bar','references')}for e in bpath['events']if e['date']in ['2026-06-04','2026-06-09','2026-06-22','2026-06-24']],
 'G2':[{'date':e['birth']['origin']['date'],'bar':e['birth']['origin'],'direction':e['birth']['direction'],'reference_id':e['birth']['reference_id'],'reference_price':e['birth']['reference_price']}for e in gpath]}
 earlier=zones['G_earlier']
 refs={'B':[{'name':'small_raw_high_proxy','low':'33.20','high':'33.20','known_on':'2026-04-16','qualification':'RAW_HIGH_REFERENCE_NOT_CONFIRMED_FORMAL_BAND_EDGE'}, {'name':'broader_raw_high_proxy','low':'35.50','high':'35.50','known_on':'2026-02-26','qualification':'RAW_HIGH_REFERENCE_NOT_CONFIRMED_FORMAL_BAND_EDGE'}],
 'G2':[{'name':'local_original_low','low':gref['price'],'high':gref['price'],'known_on':gref['known_on'],'reference_id':gref['id']},{'name':'earlier_common','low':earlier['common_close_low'],'high':earlier['common_close_high'],'known_on':earlier['known_on_saved_bar'],'zone_id':earlier['zone_id'],'qualification':'SOURCE_COMMON_SPAN_NOT_FORMAL_LARGE_BAND'}]}
 return {'selection':'SIX_FIXED_REVIEWED_ACTIVITY_SOURCES_NOT_NEW_ZONE_SCAN_OR_PATTERN_SELECTION','zones':zones,'legs':{k:lm[k]for k in sorted(lids)},'turns':{k:tm[k]for k in sorted(tids)},'references':refs,'prior_price_events':events,'case_code':CODE,'cutoffs':CUTS,'formal_merge':None,'formal_parent':None}

def source_fact(source,z,refs):
 bs=[b for b in source['bars']if z['path_start']<=b['date']<=z['path_end']]
 raw=z['raw_path_frame'];assert len(bs)==raw['records']
 assert min(D(b['low'])for b in bs)==D(raw['observed_low'])and max(D(b['high'])for b in bs)==D(raw['observed_high'])
 right=next(b for b in source['bars']if b['date']==z['known_on_saved_bar'])
 assert price(right)==price(z['right_evidence_bar'])
 against={}
 for r in refs:
  row={'common_relation':interval(z['common_close_low'],z['common_close_high'],r['low'],r['high']),'raw_relation':interval(raw['observed_low'],raw['observed_high'],r['low'],r['high'])}
  if r['low']==r['high']:
   p=D(r['low']);row.update(source_close_counts={s:sum(side(b['close'],p)==s for b in bs)for s in ('ABOVE','EQUAL','BELOW')},source_range_contains_reference_dates=[b['date']for b in bs if D(b['low'])<=p<=D(b['high'])])
  against[r['name']]=row
 return {'zone_id':z['zone_id'],'source_period':[z['path_start'],z['path_end']],'available_on':z['known_on_saved_bar'],'common':[z['common_close_low'],z['common_close_high']],'raw':[raw['observed_low'],raw['observed_high']],'source_rows':len(bs),'right_price_bar':price(right),'against_references':against,'formal_bounds':None,'formal_membership':None,'response_confirmed':None}

def relation(source,a,b,data):
 def tids(z):return {data['legs'][i][k]for i in z['leg_ids']for k in ('from_turn_id','to_turn_id')}
 ta,tb=tids(a),tids(b);left=min(data['turns'][i]['left_evidence_date']for i in tb)
 common_legs=sorted(set(a['leg_ids'])&set(b['leg_ids']));common_turns=sorted(ta&tb)
 dates=[x['date']for x in source['bars']if max(a['path_start'],b['path_start'])<=x['date']<=min(a['path_end'],b['path_end'])]
 later=[x for x in source['bars']if b['path_start']<=x['date']<=b['path_end']]
 clo,chi=map(D,[a['common_close_low'],a['common_close_high']]);rlo,rhi=map(D,[a['raw_path_frame']['observed_low'],a['raw_path_frame']['observed_high']])
 visits={'later_source_close_in_earlier_common_dates':[x['date']for x in later if clo<=D(x['close'])<=chi],'later_source_close_in_earlier_raw_dates':[x['date']for x in later if rlo<=D(x['close'])<=rhi],'later_source_range_intersects_earlier_common_dates':[x['date']for x in later if D(x['low'])<=chi and D(x['high'])>=clo],'later_source_range_intersects_earlier_raw_dates':[x['date']for x in later if D(x['low'])<=rhi and D(x['high'])>=rlo]}
 return {'available_on':max(a['known_on_saved_bar'],b['known_on_saved_bar']),'zone_ids':[a['zone_id'],b['zone_id']],'common_relation_later_vs_earlier':interval(b['common_close_low'],b['common_close_high'],a['common_close_low'],a['common_close_high']),'raw_relation_later_vs_earlier':interval(b['raw_path_frame']['observed_low'],b['raw_path_frame']['observed_high'],a['raw_path_frame']['observed_low'],a['raw_path_frame']['observed_high']),
 'shared_leg_ids':common_legs,'shared_turn_ids':common_turns,'shared_source_bar_dates':dates,'later_earliest_left_evidence':left,'all_later_left_evidence_after_older_known':left>a['known_on_saved_bar'],'actual_later_source_visits':visits,'statistical_independence_inferred':False,'formal_merge':None,'formal_parent':None}

def observe(sources,data,case,cutoff):
 source=sources[CODE[case]];known=[b for b in source['bars']if b['date']<=cutoff];last=known[-1]
 refs=[r for r in data['references'][case]if r['known_on']<=cutoff]
 # Gate availability before reading geometry, IDs of dependent legs, or raw values.
 zs={name:z for name,z in data['zones'].items()if z['code']==CODE[case]and z['known_on_saved_bar']<=cutoff}
 facts={name:source_fact({'bars':known},z,refs)for name,z in zs.items()}
 pairs={a+'_'+b:relation({'bars':known},zs[a],zs[b],data)for a,b in combinations(zs,2)}
 current={r['name']:{'close_relation':interval(last['close'],last['close'],r['low'],r['high']),'reference':[r['low'],r['high']]}for r in refs}
 current_activities={name:{'common_location':interval(last['close'],last['close'],z['common_close_low'],z['common_close_high']),'raw_location':interval(last['close'],last['close'],z['raw_path_frame']['observed_low'],z['raw_path_frame']['observed_high'])}for name,z in zs.items()}
 return {'case':case,'cutoff':cutoff,'current_price_bar':price(last),'available_activities':facts,'available_pairs':pairs,'current_reference_locations':current,'current_activity_locations':current_activities,'previous_price_anchors':[e for e in data['prior_price_events'][case]if e['date']<=cutoff],'formal_larger_structure_change':None,'formal_merge':None,'primary_pressure_id':None,'historical_signal_eligible':False,'selection_is_retrospective':True}

def run():
 for k,p in SOURCE_PATHS.items():assert sha(p)==EXPECTED[k]
 assert sha(REGISTRY)=='270a0b20ae2ac5e8e258c79b4170988f4b63d1272ab4c96c90bc6ace6740ef82'
 assert sha(SOURCE_REGISTRY)=='173127538c11ff01594ac566e644404bbb8624674f0951e2a3d6931f1c436895'
 data=select();sources={k:json.loads(p.read_text())for k,p in SOURCE_PATHS.items()}
 for z in data['zones'].values():
  assert next(b for b in sources[z['code']]['bars']if b['date']==z['known_on_saved_bar'])==z['right_evidence_bar']
 snapshots={case:{c:observe(sources,data,case,c)for c in cuts}for case,cuts in CUTS.items()}
 final={case:v[CUTS[case][-1]]for case,v in snapshots.items()}
 write('study-inputs.json',data);write('cutoff-views.json',snapshots);write('activity-evidence.json',final)
 write('source-provenance.json',{'base_commit':'2f7bf898a615a45507d110f6b6e9a7e11c09a16a','inputs':[{'local':str(p),'sha256':sha(p)}for p in [*SOURCE_PATHS.values(),REGISTRY,SOURCE_REGISTRY,CONTEXT,B_PATH,CROSS_FOLLOWUP]],'source_gaps':{k:s['source_gaps']for k,s in sources.items()},'price_basis_id':{k:s['price_basis_id']for k,s in sources.items()},'method':'Copy 6 original activities, all dependent legs/turns and 6 existing crossing anchors; new cutoff projection and pair/source audit only. No original classifier, price-cross or volume study rerun.'})
 print(json.dumps({k:{'activities':{n:{'common':f['common'],'raw':f['raw'],'source_rows':f['source_rows'],'against':f['against_references']}for n,f in v['available_activities'].items()},'pairs':v['available_pairs']}for k,v in final.items()},ensure_ascii=False,indent=2))
if __name__=='__main__':run()
