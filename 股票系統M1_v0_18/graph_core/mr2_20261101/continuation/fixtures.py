"""Synthetic-only fixtures; no real market summaries or file/network producer."""
from copy import deepcopy
import json
from pathlib import Path
from graph_core.core import analyze

HERE=Path(__file__).resolve().parent


def frozen(): return json.loads((HERE/'synthetic-input-expected.json').read_text())


def request_for(variant='failure', *, no_window=False):
    f=frozen(); p=deepcopy(f['variants'][variant]); snapshots=[]; markets=[]
    for day in f['observation_dates']:
        if not any(b['date']==day and b['close'] is not None for b in p['bars']):continue
        snapshots.append(dict(input=deepcopy(p),result=analyze(p,as_of=day),stock_source_role='SYNTHETIC_TEST_ONLY'))
        for name in ('TWSE','TPEX'):
            values=dict(index_close='300.25',up=10,down=5,flat=0)
            values.update(dict(non_comparable=0,untraded=0) if name=='TWSE' else dict(unmatched_or_suspended=0))
            markets.append(dict(date=day,market=name,values=values,provenance=dict(role='SYNTHETIC_TEST_ONLY',
                source_url='https://example.invalid/'+name+'/'+day,reported_original_sha256='1'*64,
                received_at='2026-11-01T00:00:00+00:00',original_read_by_codex=False,
                official_reverification='NOT_PERFORMED',historical_available_at='UNKNOWN',
                strict_common_stock_universe='UNKNOWN',redistribution_permission='UNKNOWN')))
    return dict(schema_version='graph-market-diary-input/0.1',mode='RETROSPECTIVE_RESEARCH_ONLY',
                snapshots=snapshots,market_summaries=markets,
                followup_windows=[] if no_window else [deepcopy(f['window'])])
