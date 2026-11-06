"""Independent generate probes; reuse exact original requests and expectations."""
import argparse
from copy import deepcopy
from decimal import localcontext
import json
from capital_research.quantity_candidates import generate
from capital_research.lifecycle import _fp
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .prepare import ROOT,PROJECT,load,save,info


def case(name):
    spec=next(c for c in load(ROOT/'input.json')['cases'] if c['name']==name)
    for key in ('source','source_record'):assert info(PROJECT/spec[key]['path'])==spec[key]
    value=load(PROJECT/spec['source']['path']);assert _fp(value)==spec['source_id']
    f=value['replay']['rounds'][spec['round_index']];q=f['quantity_request'];expected=f['generation']
    assert _fp(q)==spec['request_id'] and _fp(expected)==spec['expected_generation_id']
    return deepcopy(q),expected,spec


def controls():
    ref=load(ROOT/'input.json')['controls_reference'];assert info(PROJECT/ref['path'])==ref
    return load(PROJECT/ref['path'])


def preset():
    ref=load(ROOT/'input.json')['preset_reference'];assert info(PROJECT/ref['path'])==ref
    return load(PROJECT/ref['path'])['preset']


def stored_actual(value,spec,expected):
    if value==expected:
        return dict(kind='EXACT_EXISTING_GENERATION',source=spec['source'],round_index=spec['round_index'],id=_fp(value))
    p=ROOT/'objects'/(_fp(value).split(':')[1]+'.json');p.parent.mkdir(exist_ok=True)
    body=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n'
    if p.exists():assert p.read_text()==body
    else:
        with p.open('x') as f:f.write(body)
    return dict(kind='NEW_COMPLETE_DIFFERING_OUTPUT',path=str(p.relative_to(ROOT)),id=_fp(value))


def actual_value(record):
    a=record['actual']
    if a is None:return None
    if a['kind']=='EXACT_EXISTING_GENERATION':value=load(PROJECT/a['source']['path'])['replay']['rounds'][a['round_index']]['generation']
    else:value=load(ROOT/a['path'])
    assert _fp(value)==a['id'];return value


def probe(data,setting):
    before_id=_fp(data)
    with localcontext(context(setting)) as ctx:
        before=snapshot(ctx)
        try:value=generate(data);error=None
        except Exception as exc:value=None;error=dict(type=type(exc).__name__,detail=str(exc))
        after=snapshot(ctx)
    return value,dict(error=error,caller_before=before,caller_after=after,input_id=before_id,input_unchanged=_fp(data)==before_id,
        caller_context_unchanged=before==after,source_version=info(ROOT.parent/'quantity_candidates.py'))


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('before','after'));a=p.parse_args();rows=[]
    for name in ('initial','old-trigger'):
        data,expected,spec=case(name)
        for setting in controls():
            value,record=probe(data,setting['context']);record['actual']=stored_actual(value,spec,expected) if value is not None else None
            record['equal_original']=value==expected;save(ROOT/a.stage/name/setting['name']/'actual.json',record)
            rows.append(dict(case=name,context=setting['name'],equal_original=value==expected,error=record['error'],
                input_unchanged=record['input_unchanged'],caller_context_unchanged=record['caller_context_unchanged']))
            print(name,setting['name'],value==expected,record['error'],flush=True)
    save(ROOT/a.stage/'summary.json',rows)


if __name__=='__main__':main()
