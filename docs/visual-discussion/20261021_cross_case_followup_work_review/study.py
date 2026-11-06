"""Finite directional follow-up comparison, independent of formal pattern labels."""
from pathlib import Path
from decimal import Decimal as D
import hashlib,json,os

ROOT=Path(__file__).resolve().parent
SOURCES={
 '1101':Path(os.environ.get('FOLLOWUP_SOURCE_1101','/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json')),
 '2884':Path(os.environ.get('FOLLOWUP_SOURCE_2884','/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json'))}
PRIOR_CROSS=Path(os.environ.get('FOLLOWUP_PRIOR_CROSS','/workspace/scratch/e9363d3b9105/cross-case-reading-research/study-inputs.json'))
PRIOR_RETURN=Path(os.environ.get('FOLLOWUP_PRIOR_RETURN','/workspace/scratch/e9363d3b9105/return-path-research/return-paths.json'))
PRIOR_CONTEXT=Path(os.environ.get('FOLLOWUP_PRIOR_CONTEXT','/workspace/scratch/e9363d3b9105/return-context-research/study-inputs.json'))
PRIOR_B=Path(os.environ.get('FOLLOWUP_PRIOR_B','/workspace/scratch/e9363d3b9105/b-followup-holding-research/episode-summaries.json'))
EXPECTED={'1101':'184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15','2884':'ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'}
CASE_CONFIG={
 'G2':{'code':'1101','end':'2023-08-02','cutoffs':['2023-07-10','2023-07-13','2023-07-14','2023-07-24','2023-07-25','2023-07-28','2023-07-31','2023-08-02']},
 'ABC':{'code':'1101','end':'2025-06-12','cutoffs':['2025-06-02','2025-06-03','2025-06-11','2025-06-12']},
 'A':{'code':'2884','end':'2026-10-16','cutoffs':['2026-10-14','2026-10-15','2026-10-16']}}

def write(name,data):
 (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def price(b):return {k:b[k]for k in ('date','open','high','low','close')}
def side(value,p):return 'ABOVE'if D(value)>p else 'BELOW'if D(value)<p else 'EQUAL'

def inputs():
 cross=json.loads(PRIOR_CROSS.read_text());ret=json.loads(PRIOR_RETURN.read_text());ctx=json.loads(PRIOR_CONTEXT.read_text())
 gref=ret['earlier-down-wick-then-close-return@2023-07-10']['original_reference']
 queries=[
  {'id':'G2-down-37.15','case':'G2','direction':'DOWN','origin':'2023-07-10','reference':gref},
  {'id':'G2-reclaim-37.15','case':'G2','direction':'UP','origin':'2023-07-25','reference':gref},
  {'id':'ABC-down-28.45','case':'ABC','direction':'DOWN','origin':'2025-06-02','reference':cross['cases']['ABC']['points']['low']},
  {'id':'A-up-47.35','case':'A','direction':'UP','origin':'2026-10-15','reference':cross['cases']['A']['points']['high']}]
 return {'selection':'FIXED_PREVIOUSLY_REVIEWED_EVENTS_NOT_NEW_CROSSING_SCAN_OR_HISTORICAL_SELECTION',
  'queries':queries,'case_config':CASE_CONFIG,'G2_earlier_zones':ctx['zones'],
  'ABC_earlier_zone':cross['cases']['ABC']['zones']['earlier'],
  'A_earlier_zone':cross['cases']['A']['zones']['earlier'],
  'B_previous_summaries_unchanged':json.loads(PRIOR_B.read_text())}

def view(bars,query,cutoff):
 """Only supplied bars at/before cutoff; no volume or manual shape input."""
 cfg=CASE_CONFIG[query['case']];end=min(cutoff,cfg['end'])
 known=[b for b in bars if b['date']<=end];by={b['date']:b for b in known}
 if query['origin']>end or query['reference']['known_on']>end:return None
 if query['origin']not in by:return None
 p=D(query['reference']['price']);origin=by[query['origin']]
 i=next(i for i,b in enumerate(known)if b['date']==query['origin']);assert i>0
 previous=known[i-1];up=query['direction']=='UP';same='ABOVE'if up else'BELOW';opposite='BELOW'if up else'ABOVE'
 assert side(previous['close'],p)==opposite and side(origin['close'],p)==same
 birth={'query_id':query['id'],'reference_id':query['reference']['id'],'reference_price':str(p),'reference_available_on':query['reference']['known_on'],'origin':price(origin),'previous':price(previous),'direction':query['direction'],'selection_is_retrospective':True}
 facts=[]
 for b in known:
  if b['date']<=query['origin']:continue
  c,h,l=map(D,[b['close'],b['high'],b['low']]);s=side(c,p)
  facts.append({'date':b['date'],'bar':price(b),'close_side':s,'relative_to_origin_direction':'SAME'if s==same else'OPPOSITE'if s==opposite else'EQUAL',
   'strict_intraday_return_close_same_side':(l<p<c)if up else(c<p<h),
   'equal_boundary_touch_close_same_side':(l==p<c)if up else(c<p==h),
   'whole_bar_same_side':l>p if up else h<p,
   'whole_bar_opposite_side':h<p if up else l>p,
   'range_contains_reference':l<=p<=h})
 opp=[f['date']for f in facts if f['close_side']==opposite]
 first_opp=opp[0]if opp else None
 back=next((f['date']for f in facts if first_opp and f['date']>first_opp and f['close_side']==same),None)
 summary={'cutoff':end,'followup_bars_excluding_origin':len(facts),'above_count':sum(f['close_side']=='ABOVE'for f in facts),'below_count':sum(f['close_side']=='BELOW'for f in facts),'equal_count':sum(f['close_side']=='EQUAL'for f in facts),
  'first_opposite_close':first_opp,'first_return_to_origin_side_after_opposite':back,
  'strict_intraday_return_close_same_side_dates':[f['date']for f in facts if f['strict_intraday_return_close_same_side']],
  'equal_boundary_touch_close_same_side_dates':[f['date']for f in facts if f['equal_boundary_touch_close_same_side']],
  'current_close_side':side((facts[-1]['bar']if facts else origin)['close'],p),
  'highest_followup_high':max((f['bar']['high']for f in facts),key=D)if facts else None,
  'lowest_followup_low':min((f['bar']['low']for f in facts),key=D)if facts else None,
  'observation_ends_without_lifetime_result':True,'formal_standing_or_breakdown_confirmed':None,'formal_success_or_failure':None,'confirmation_date':None,'volume_veto':False,'historical_signal_eligible':False}
 return {'birth':birth,'facts':facts,'summary':summary}

def run():
 for code,path in SOURCES.items():assert sha(path)==EXPECTED[code]
 data=inputs();sources={k:json.loads(p.read_text())for k,p in SOURCES.items()}
 snapshots={};final={}
 for case,cfg in CASE_CONFIG.items():
  bars=sources[cfg['code']]['bars'];assert len(bars)==len({b['date']for b in bars})==1213
  assert bars==sorted(bars,key=lambda b:b['date'])
  snapshots[case]={cut:[v for q in data['queries']if q['case']==case if (v:=view(bars,q,cut))is not None]for cut in cfg['cutoffs']}
  final[case]=snapshots[case][cfg['end']]
 write('study-inputs.json',data);write('cutoff-views.json',snapshots);write('followup-results.json',final)
 write('source-provenance.json',{'base_commit':'8e2260dc9d146244976b8bd4b1b8a87ed70f97ae','inputs':[{'local':str(p),'sha256':sha(p)}for p in [*SOURCES.values(),PRIOR_CROSS,PRIOR_RETURN,PRIOR_CONTEXT,PRIOR_B]],'source_gaps':{k:s['source_gaps']for k,s in sources.items()},'price_basis_id':{k:s['price_basis_id']for k,s in sources.items()},'old_driver_verifier_crossing_or_volume_study_rerun':0,'new_downloads':0,'method':'Four fixed previous crossings, later-only raw price views. Previous B summaries copied, not recomputed. No formal bands, holding thresholds, event scan or source qualification changes.'})
 print(json.dumps({k:[x['summary']for x in v]for k,v in final.items()},ensure_ascii=False,indent=2))
if __name__=='__main__':run()
