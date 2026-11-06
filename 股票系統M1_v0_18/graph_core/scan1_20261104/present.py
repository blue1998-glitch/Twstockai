"""Adapter from saved original core result to the ORIGINAL viewer contract.
No core calls, history joining, new numeric formula or persisted chart output.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
from graph_core.core import fingerprint
from graph_core.lite1_20261103.decision import project
from product_candidate.macd import macd,PARAMETERS
from moving_averages import curves

def present(f,v):
    r=v["result"];dt=f["as_of"];context=r["context"];bars=[f["bar"]]
    if r["source_prefix_fingerprint"]!=fingerprint(bars):raise ValueError("SAVED_CORE_INPUT_PREFIX_CONFLICT")
    payload=dict(schema_version="graph-recognition-input/0.1",context=context,bars=bars,basis_break_dates=[dt],expected_dates=[dt])
    d=project(dict(identity=f["identity"],code=f["code"],market=f["market"],as_of=dt,status="INSUFFICIENT_HISTORY"),r)
    series=dict(code=f["code"],exchange=f["market"],source=dict(id=context["source_id"],name=f["name"],role=context["source_kind"],historical_available_at="UNKNOWN"),price_basis_id=context["price_basis_id"],bars=bars,macd=macd([f["bar"]["close"]],resets=[0]),moving_averages=curves(bars),results=[r],presentations={dt:dict(ids=[],reasons={},qualification="NO_FORMED_CANDIDATES_IN_SINGLE_SOURCE_BAR")},manual_audits={},numeric_frame_ids={dt:fingerprint(payload)},source_gaps=dict(calendar_status="SINGLE_VERIFIED_SOURCE_DAY_NOT_COMPLETE_CALENDAR",actions_coverage="UNKNOWN",historical_publication_timing="UNKNOWN"),macd_parameters=PARAMETERS,input_bindings={dt:dict(source_id=context["source_id"],price_basis_id=context["price_basis_id"],basis_break_dates=[dt],historical_available_at="UNKNOWN",core_input_fingerprint=fingerprint(payload))},box_evidence={dt:{}})
    return dict(schema="lazy-segment-analysis/0.1",identity=f["identity"],as_of=dt,fact_source=f["source"],series=series,decision=d,status="INSUFFICIENT_COMPARABLE_HISTORY",core_calls=0,scan_core_calls=v["core_calls"],meaningful_structure=False,history_joined=False,primary_pressure_id=None,execution_qualified=False,historical_signal_eligible=False,policy_authorized=False,metrics=dict(worker_seconds=None,peak_RSS_KiB=None),saved_scan_profile=v.get("profile"))
