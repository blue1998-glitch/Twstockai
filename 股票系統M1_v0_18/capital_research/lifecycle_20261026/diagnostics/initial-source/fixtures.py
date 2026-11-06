"""Read exact saved inputs by fingerprint; explicit structural JSON variants.

Variants are reader diagnostics, never new engine or market results.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]


def fp(value):
    return 'sha256:'+hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def materialize(spec):
    source=spec['source'];raw=(REPO/source['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==source['sha256'] and len(raw)==source['bytes']
    saved=json.loads(raw);mutation=spec['mutation']
    if mutation is None:return saved
    if mutation=='schema':saved['review']['schema']='capital-conditional-quantity-review/unknown';return saved
    r=saved['review'];e=r['execution'];cp=r['checkpoint']
    if mutation=='corrupt':e['order_states']['r1-B']['reserved_cash']='9999';return saved
    if mutation=='missing-payable':
        del e['ledger']['daily'][-1]['purchase_payable'];del cp['state']['row']['purchase_payable']
    elif mutation=='quantity':
        e['order_states']['r1-B']['remaining']='12';cp['state']['order_states']['r1-B']['remaining']='12'
    elif mutation=='missing-proof':
        for f in e['fills']:
            if f['code']=='B':f['settlement_date']='2026-01-09'
        for j in e['ledger']['journal']:
            if j['type']=='FILL' and j['fill']['code']=='B':j['fill']['settlement_date']='2026-01-09'
        for f in cp['state']['accepted_fills']:
            if f['code']=='B':f['settlement_date']='2026-01-09'
    else:raise ValueError(mutation)
    # Re-sign this explicit structural variant so it exercises field/link checks,
    # rather than stopping only at the outer byte fingerprint. No engine is used.
    e['result_id']=fp({k:v for k,v in e.items() if k!='result_id'})
    cp['state_id']=fp(cp['state']);cp['checkpoint_id']=fp(dict(schema=cp['schema'],state_id=cp['state_id']))
    return saved


def load(name):
    return materialize(json.loads((ROOT/'cases'/name/'input.json').read_text()))
