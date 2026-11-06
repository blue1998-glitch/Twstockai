from pathlib import Path
import json,hashlib,collections,re,datetime,os
from graph_core.market_daily import Journal,encode
from graph_core.market_finmind import capture_key
from technical_chart.build import unpack
base=Path('/workspace/twstockai-local-data/fm3_20261101');root=base/'runtime';state=json.loads((root/'fm3-continuation.json').read_text());assert state['status']=='FINISHED_COHORT_WITH_EXPLICIT_QUALIFICATIONS',state['status']
batch=Journal(root/'runs').read(state['result']['id'])['value'];rows=batch['stocks'];reference=Journal(root/'runs').read(batch['reference_current_run'])['value'];assert len(rows)==1986 and {s['identity'] for s in rows}=={s['identity'] for s in reference['stocks']};assert not any(s['status']=='RATE_OR_PROVIDER_DEFERRED' for s in rows)
html=Path(state['preview']['path']);raw=html.read_bytes();assert hashlib.sha256(raw).hexdigest()==state['preview']['sha256'];text=raw.decode();m=re.search(r'<script id="market-state" type="application/json">(.*?)</script>',text,re.S);visible=json.loads(m[1]);assert [{k:v for k,v in x.items() if k!='preview_series'} for x in visible['stocks']]==rows
checks=collections.Counter();errors=[]
for stock in rows:
 try:
  params=dict(dataset='TaiwanStockPrice',data_id=stock['code'],start_date=max('2021-10-18',stock['listed_at']),end_date=batch['as_of'])
  receipt=Journal(root/'source-receipts').read(capture_key(params))['value'];assert receipt['parameters']==params
  original=(root/'source-raw'/receipt['sha256']).read_bytes();assert hashlib.sha256(original).hexdigest()==receipt['sha256'];checks['stock_source_raw_verified']+=1
  if not stock.get('result_key'):continue
  saved=Journal(root/'results').read(stock['result_key'])['value'];assert stock['result_key']=='fm3-result-'+hashlib.sha256(encode(saved)).hexdigest();assert saved['acquisition']==receipt
  h=Journal(root/'histories').read(stock['history_key'])['value'];assert h['bars']==saved['input']['bars'];assert saved['result']['as_of']==batch['as_of'];assert saved['result']['context']['code']==stock['code'];assert saved['official_comparison']['matched']
  item=next(s for s in visible['stocks'] if s['identity']==stock['identity']);desc=item['preview_series'];chunk=(html.parent/desc['path']).read_bytes();assert len(chunk)==desc['bytes'] and hashlib.sha256(chunk).hexdigest()==desc['sha256'];series=unpack(json.loads(chunk));assert series['bars']==saved['input']['bars'];assert series['results']==[saved['result']];assert series['macd']==saved['indicators']['macd'];assert series['moving_averages']==saved['indicators']['moving_averages'];checks['complete_result_history_and_chart_verified']+=1
 except Exception as e:errors.append(dict(identity=stock['identity'],error_type=type(e).__name__))
slots=sorted(json.loads(p.read_text())['value']['epoch'] for p in (root/'source-slots').glob('*.json'));left=maximum=0
for i,t in enumerate(slots):
 while slots[left]<=t-3600:left+=1
 maximum=max(maximum,i-left+1)
assert maximum<=240
stats=dict(status='COHORT_ALL_TERMINALS_AUDITED' if not errors else 'AUDIT_BLOCKED',as_of=batch['as_of'],reference_count=len(rows),reference_by_market=reference['summary']['expected_by_market'],reference_source_dates={k:v['observed_at'] for k,v in reference['markets'].items()},terminal_counts=dict(collections.Counter(s['status'] for s in rows)),analysis_by_market=dict(collections.Counter(s['market'] for s in rows if s['status']=='ANALYZED_FINMIND_HISTORY')),searchable_charts=sum(bool(s.get('result_key')) for s in rows),new_searchable_excluding_original_four=sum(bool(s.get('result_key')) and s['code'] not in ['1101','2884','6488','8069'] for s in rows),new_multiday_excluding_original_four=sum(s['status']=='ANALYZED_FINMIND_HISTORY' and s['code'] not in ['1101','2884','6488','8069'] for s in rows),remaining=0,checks=dict(checks),errors=errors,api_request_slots=len(slots),maximum_observed_rolling_3600_requests=maximum,private_data_outside_git=True,persistence='UNKNOWN_OVERLAY_ONLY',android_fixed_entry='NOT_DEPLOYED',daily_scheduler='NOT_ENABLED',new_core_or_source_requests=0)
Path('/workspace/Twstockai-private/fm3_20261101/final-audit.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));print(json.dumps(stats,ensure_ascii=False),flush=True)
