"""One qualified current segment, original core/MA/MACD, subprocess resource caps.
The current source contract proves ONLY ONE new comparable bar. Never read or
join historical data in this worker; a source bridge needs separate evidence.
"""
import json,sys,resource,time
if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(3,3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
from decimal import localcontext,ROUND_HALF_EVEN
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from graph_core.core import analyze,fingerprint
from product_candidate.macd import macd,PARAMETERS
from moving_averages import curves
from graph_core.lite1_20261103.decision import project

def run(f):
    if f['source_status']!='SOURCE_BAR_AVAILABLE' or not f['bar'] or f['bar']['date']!=f['as_of']:raise ValueError('QUALIFIED_CURRENT_BAR_REQUIRED')
    if f['source']['price_mode']!='RAW_CANDIDATE' or f['source']['volume_unit']!='SHARES_REPORTED' or f['continuity']!='NOT_CERTIFIED_NO_HISTORY_APPENDED':raise ValueError('UNSUPPORTED_SOURCE_ROLE')
    t=time.monotonic();dt=f['as_of'];bars=[f['bar']]
    context=dict(code=f['code'],exchange=f['market'],source_id='sha256:'+f['source']['daily_sha256'],price_basis_id=f['source']['price_basis_id'],price_mode='RAW_CANDIDATE',volume_unit='SHARES_REPORTED',source_kind='OFFICIAL_SINGLE_DAILY_SEGMENT_NO_CERTIFIED_HISTORY_BRIDGE',corporate_action_comparability='UNKNOWN_RESET_AT_NEW_OFFICIAL_DATE',historical_publication_timing='UNKNOWN')
    payload=dict(schema_version='graph-recognition-input/0.1',context=context,bars=bars,basis_break_dates=[dt],expected_dates=[dt])
    with localcontext() as c:c.prec=50;c.rounding=ROUND_HALF_EVEN;r=analyze(payload,as_of=dt)
    if r['boxes'] or r['reference_candidates'] or r['source_records']!=1:raise ValueError('UNEXPECTED_SINGLE_SEGMENT_RESULT')
    stock=dict(identity=f['identity'],code=f['code'],market=f['market'],as_of=dt,status='INSUFFICIENT_HISTORY');decision=project(stock,r)
    indicators=macd([b['close'] for b in bars],resets=[0]);ma=curves(bars)
    series=dict(code=f['code'],exchange=f['market'],source=dict(id=context['source_id'],name=f['name'],role=context['source_kind'],historical_available_at='UNKNOWN'),price_basis_id=context['price_basis_id'],bars=bars,macd=indicators,moving_averages=ma,results=[r],presentations={dt:dict(ids=[],reasons={},qualification='NO_FORMED_CANDIDATES_IN_SINGLE_SOURCE_BAR')},manual_audits={},numeric_frame_ids={dt:fingerprint(payload)},source_gaps=dict(calendar_status='SINGLE_VERIFIED_SOURCE_DAY_NOT_COMPLETE_CALENDAR',actions_coverage='UNKNOWN',historical_publication_timing='UNKNOWN'),macd_parameters=PARAMETERS,input_bindings={dt:dict(source_id=context['source_id'],price_basis_id=context['price_basis_id'],basis_break_dates=[dt],historical_available_at='UNKNOWN',core_input_fingerprint=fingerprint(payload))},box_evidence={dt:{}})
    return dict(schema='lazy-segment-analysis/0.1',identity=f['identity'],as_of=dt,fact_source=f['source'],series=series,decision=decision,status='INSUFFICIENT_COMPARABLE_HISTORY',core_calls=1,meaningful_structure=False,history_joined=False,primary_pressure_id=None,execution_qualified=False,historical_signal_eligible=False,policy_authorized=False,metrics=dict(worker_seconds=time.monotonic()-t,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
if __name__=='__main__':
    raw=sys.stdin.buffer.read(65537)
    if len(raw)>65536:raise ValueError('FACT_INPUT_BOUND')
    value=run(json.loads(raw));body=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    if len(body)>262144:raise ValueError('RESULT_BOUND')
    sys.stdout.buffer.write(body)
