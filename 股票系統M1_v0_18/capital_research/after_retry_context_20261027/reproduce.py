"""Direct outer-bridge calls only; no old retry or market replay execution."""
import argparse
from decimal import localcontext
import json
from capital_research.quantity_after_retry import generate_after_retry
from capital_research.lifecycle import _fp
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from capital_research.quantity_after_retry_20261027.fixtures import materialize
from .prepare import ROOT,PROJECT,PRIMARY,load,save,info


def case(name):
    spec=next(c for c in load(ROOT/'input.json')['cases'] if c['name']==name)
    for k in ('input_spec','expected_spec','original_actual'):assert info(PROJECT/spec[k]['path'])==spec[k]
    data=materialize(load(PROJECT/spec['input_spec']['path']));expected=load(PROJECT/spec['original_actual']['path'])
    assert _fp(data)==spec['materialized_input_id'] and _fp(expected)==spec['expected_result_id']
    return data,expected,spec


def controls():
    ref=load(ROOT/'input.json')['controls_reference'];assert info(PROJECT/ref['path'])==ref
    return load(PROJECT/ref['path'])


def preset():
    ref=load(ROOT/'input.json')['preset_reference'];assert info(PROJECT/ref['path'])==ref
    return load(PROJECT/ref['path'])['preset']


def stored_actual(value,spec,expected):
    if value==expected:return dict(kind='EXACT_EXISTING_ACTUAL',source=spec['original_actual'],id=_fp(value))
    p=ROOT/'objects'/(_fp(value).split(':')[1]+'.json');p.parent.mkdir(exist_ok=True)
    body=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n'
    if p.exists():assert p.read_text()==body
    else:
        with p.open('x') as f:f.write(body)
    return dict(kind='NEW_COMPLETE_DIFFERING_OUTPUT',path=str(p.relative_to(ROOT)),id=_fp(value))


def actual_value(record):
    a=record['actual']
    if a is None:return None
    if a['kind']=='EXACT_EXISTING_ACTUAL':
        assert info(PROJECT/a['source']['path'])==a['source'];value=load(PROJECT/a['source']['path'])
    else:value=load(ROOT/a['path'])
    assert _fp(value)==a['id'];return value


def probe(data,setting):
    original=_fp(data)
    with localcontext(context(setting)) as ctx:
        before=snapshot(ctx)
        try:value=generate_after_retry(data);error=None
        except Exception as exc:value=None;error=dict(type=type(exc).__name__,detail=str(exc))
        after=snapshot(ctx)
    return value,dict(error=error,caller_before=before,caller_after=after,input_id=original,
        input_unchanged=_fp(data)==original,caller_context_unchanged=before==after,
        source_version=info(ROOT.parent/'quantity_after_retry.py'))


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('before','after'));a=p.parse_args();rows=[]
    for name in PRIMARY:
        data,expected,spec=case(name)
        for c in controls():
            value,record=probe(data,c['context']);record['actual']=stored_actual(value,spec,expected) if value is not None else None
            record['equal_original']=value==expected;save(ROOT/a.stage/name/c['name']/'actual.json',record)
            rows.append(dict(case=name,context=c['name'],equal_original=value==expected,error=record['error'],
                caller_context_unchanged=record['caller_context_unchanged'],input_unchanged=record['input_unchanged']))
            print(name,c['name'],value==expected,record['error'],flush=True)
    save(ROOT/a.stage/'summary.json',rows)


if __name__=='__main__':main()
