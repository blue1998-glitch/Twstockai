"""Read-only source audit for one retrospective rally path; no engine imports."""
from pathlib import Path
from decimal import Decimal as D
import json,hashlib
p=Path('real-review/input/comparison-data.json');raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest();assert sha=='184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15';data=json.loads(raw);bars=data['bars'];by={b['date']:(i,b) for i,b in enumerate(bars)}
idx=[i for i,b in enumerate(bars) if '2025-01-13'<=b['date']<='2025-03-24'];assert idx==list(range(idx[0],idx[-1]+1))
records=[{'source_index':i,'bar':bars[i],'macd':data['macd'][i]} for i in idx]
rs=[r['bar'] for r in records]
maxima={}
for k in ['high','close','volume_shares_scaled']:
 m=max(D(b[k]) for b in rs);maxima[k]={'value':str(m),'dates':[b['date'] for b in rs if D(b[k])==m]}
assert maxima['high']['dates']==['2025-03-12'];assert maxima['close']['dates']==['2025-02-26'];assert maxima['volume_shares_scaled']['dates']==['2025-02-25']
references=[]
for date in ['2023-06-05','2023-11-28','2024-07-26']:
 i,b=by[date];references.append({'bar':b,'original_pivots':[v for v in data['core']['pivots'] if v['occurred_at']==date and v['kind']=='HIGH' and D(v['price'])==D(b['high'])],'qualification':'ASSISTANT_CONTEXT_REFERENCE_NOT_FORMAL_KEYPOINT_OR_WHOLE_REPRESENTATIVE'})
relations={}
for ref in ['35.20','35.50','39.25']:
 relations[ref]={'close_above':[b['date'] for b in rs if D(b['close'])>D(ref)],'close_equal':[b['date'] for b in rs if D(b['close'])==D(ref)],'high_above':[b['date'] for b in rs if D(b['high'])>D(ref)],'high_equal':[b['date'] for b in rs if D(b['high'])==D(ref)],'all_record_close_locations':[{'date':b['date'],'relation':'ABOVE' if D(b['close'])>D(ref) else 'BELOW' if D(b['close'])<D(ref) else 'EQUAL'} for b in rs]}
assert relations['35.20']['close_above']==['2025-02-26'];assert relations['35.50']['high_above']==[] and relations['35.50']['high_equal']==[];assert relations['39.25']['high_above']==[] and relations['39.25']['high_equal']==[]
assert D(by['2025-02-27'][1]['close'])<D('35.20')
focus_dates=['2025-02-25','2025-02-26','2025-02-27','2025-03-12','2025-03-13','2025-03-24']
focus=[{'source_index':by[d][0],'bar':by[d][1],'macd':data['macd'][by[d][0]]} for d in focus_dates]
extra=[bars[i] for i in range(by['2023-11-28'][0],by['2023-11-30'][0]+1)]
assert len(extra)==3 and D(extra[-1]['volume_shares_scaled'])>D(extra[0]['volume_shares_scaled']) and D(extra[-1]['high'])<D(extra[0]['high'])
turns=[v for v in data['core']['pivots'] if v['scale']=='0.06' and v['occurred_at']=='2025-03-12' and v['kind']=='HIGH'];assert len(turns)==1 and turns[0]['confirmed_at']=='2025-03-24'
q=Path('whole-membership-review/input/source-query.json');querysha=hashlib.sha256(q.read_bytes()).hexdigest();assert querysha=='4a43a8c0f03bbffacb86306f064b7c807a7a83bdaf7e737bc76cd654a2c1dbb0'
png=Path('broad-context-review/broad-price-volume-context.png');e={'schema':'m1-rally-path-read-review/1','source_comparison_sha256':sha,'source_query_sha256':querysha,'core_result_id':data['core']['result_id'],'view':'../20261020_broad_context_correction/broad-price-volume-context.png','view_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'context':'Original 597-record broad context, unchanged; 43-row observation is not a replacement narrow chart','observation_window':['2025-01-13','2025-03-24'],'observation_window_selection':'RETROSPECTIVE_ORIGINAL_LOW_TO_ORIGINAL_6PCT_HIGH_CONFIRMATION_NOT_FORMAL_REGION_OR_MOVE_BOUNDARY','record_count':len(records),'records':records,'maxima_in_same_window':maxima,'focus':focus,'references':references,'reference_relations':relations,'nov2023_neighbour_records':extra,'march_6pct_pivot':turns[0],'selection_time_is_historical':False,'historical_selection_time':None,'historical_signal_eligible':False,'primary_pressure_id':None,'classification':'ASSISTANT_RESEARCH_NOT_USER_APPROVED_KEYPOINTS_OR_MEMBERSHIP'}
out=Path('rally-path-review');(out/'evidence.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n');assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
(out/'verification.json').write_text(json.dumps({'source_hashes_unchanged':True,'all_43_original_record_indices_contiguous':True,'original_OHLCV_MACD_string_copy':True,'all_record_reference_relations_decimal':True,'max_price_close_and_volume_dates_distinct':True,'only_close_above_35_20':'2025-02-26','next_saved_record_below_35_20':'2025-02-27','none_high_reach_35_50_or_39_25_in_observation':True,'original_6pct_high_confirmation_verified':True,'nov28_30_2023_price_volume_peaks_differ':True,'image':'REUSED_UNCHANGED_NO_REDRAW','M1_engine_MACD_reaction_query_adapter_CLI':'NOT_RUN','product_tests':'NOT_RUN','bootstrap':'NOT_RUN','browser':'NOT_RUN','Android':'NOT_TESTED_NEW_BUILD'},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'records':len(records),'maxima':maxima,'35.20':{k:v for k,v in relations['35.20'].items() if k!='all_record_close_locations'},'march12_MACD':data['macd'][by['2025-03-12'][0]],'march13_MACD':data['macd'][by['2025-03-13'][0]]},ensure_ascii=False))
