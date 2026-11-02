"""Tiny synthetic private collection reusing an already saved public demo core.
No provider requests or numerical analysis, even during fixture preparation.
"""
import json,re,os
from pathlib import Path
from rotation_research import artifact_codec as c
from rotation_research.store import Journal
from rotation_research.private_portability import FINMIND_ENDPOINT,encode,digest
from technical_chart.interned_json import unpack,pack


def make(root):
    root.mkdir(mode=0o700)
    html=(Path(__file__).resolve().parents[1]/'comp1_20261102/Twstockai_COMP1_SYNTHETIC_DEMO.html').read_bytes()
    payload=json.loads(re.search(rb'<script id="payload" type="application/json">(.*?)</script>',html,re.S)[1]);s=unpack(payload)['series'][0]
    result=s['results'][0];bars=s['bars'];as_of=result['as_of'];code=s['code'];market=s['exchange'];start=bars[0]['date']
    params=dict(dataset='TaiwanStockPrice',data_id=code,start_date=start,end_date=as_of)
    original=encode(dict(SYNTHETIC_NOT_PROVIDER_DATA=True,bars=bars));sha=digest(original);(root/'source-raw').mkdir();(root/'source-raw'/sha).write_bytes(original)
    (root/'readonly-aliases').mkdir();os.link(root/'source-raw'/sha,root/'readonly-aliases'/'synthetic-original')
    receipt=dict(parameters=params,endpoint=FINMIND_ENDPOINT,status='RECEIVED',sha256=sha,synthetic=True)
    key=digest(encode(dict(endpoint=FINMIND_ENDPOINT,parameters=params)));Journal(root/'source-receipts').save(key,receipt)
    payload=dict(schema_version='graph-recognition-input/0.1',context=result['context'],bars=bars,basis_break_dates=result['data_gaps']['basis_resets'],expected_dates=[b['date'] for b in bars])
    saved=dict(input=payload,result=result,acquisition=receipt,indicators=dict(macd=s['macd'],moving_averages=s['moving_averages']),official_comparison=dict(matched=True,synthetic=True))
    rk='fm3-result-'+digest(encode(saved));hk='synthetic-history'
    Journal(root/'histories').save(hk,dict(bars=bars,basis_break_dates=payload['basis_break_dates']),compact=True,storage_root=root)
    Journal(root/'results').save(rk,saved,compact=True,storage_root=root)
    row=dict(identity=market+':'+code,code=code,market=market,name='SYNTHETIC',listed_at=start,status='ANALYZED_FINMIND_HISTORY',result_key=rk,history_key=hk,
        data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,policy_authorized=False,live_execution_authorized=False,primary_pressure_id=None)
    run='synthetic-fm3-run';reference='synthetic-reference';summary=dict(expected=1,processed=1,requested_start=start,as_of=as_of)
    Journal(root/'runs').save(reference,dict(stocks=[row],summary=summary))
    Journal(root/'runs').save(run,dict(version='finmind-market-history/0.1',stocks=[row],reference_current_run=reference,summary=summary,as_of=as_of))
    data=encode(pack(s));page_dir=root/'preview'/run;page_dir.mkdir(parents=True)
    anchor=page_dir/'old-chart-anchor.json';anchor.write_bytes(data)
    name='series-'+digest(data)+'.json';c.publish_interned(page_dir/name,data,root=root,bases=[anchor],format='chart')
    state=dict(summary=summary,stocks=[dict(row,preview_series=dict(path=name,sha256=digest(data),bytes=len(data)))])
    page=b'<!doctype html><meta charset="utf-8"><script id="market-state" type="application/json">'+encode(state)+b'</script>'
    page_path=page_dir/'market-fm3-v02.html';c.publish(page_path,page,root=root)
    desc=dict(path=str(page_path),sha256=digest(page),bytes=len(page),charts=1)
    c.immutable(root/'fm3-continuation.json',encode(dict(status='FINISHED_COHORT_WITH_EXPLICIT_QUALIFICATIONS',data_class='SYNTHETIC_ENGINEERING_FIXTURE_NOT_PROVIDER_SAMPLE',result=dict(id=run),preview=desc)))
    catalogue=root/'saved-batches.json';c.immutable(catalogue,encode(dict(schema='private-saved-batches/0.1',batches=[dict(run_id=run,as_of=as_of,**{k:desc[k] for k in ('path','sha256','bytes')})])))
    c.immutable(root/'current-increment-run.json',encode(dict(id=run,private_preview=desc,batch_index=str(catalogue))))
    return root
