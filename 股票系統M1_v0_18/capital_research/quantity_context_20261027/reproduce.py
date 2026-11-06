"""Only the frozen context probes; content-address large exact outputs once."""
import argparse
import decimal
from pathlib import Path
from capital_research.quantity_replay import replay_sequence
from capital_research.lifecycle import _fp
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .prepare import ROOT,PROJECT,load,save,info


def object_path(value):return ROOT/'objects'/(_fp(value).split(':')[1]+'.json')


def save_object(value):
    import json
    path=object_path(value);path.parent.mkdir(exist_ok=True)
    body=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n'
    if path.exists():assert path.read_text()==body,'OBJECT_CONTENT_CONFLICT'
    else:
        with path.open('x') as f:f.write(body)
    return dict(path=str(path.relative_to(ROOT)),id=_fp(value),bytes=path.stat().st_size)


def probe(data,spec):
    identity=_fp(data)
    with decimal.localcontext(context(spec)) as ctx:
        before=snapshot(ctx)
        try:result=replay_sequence(data);error=None
        except Exception as exc:result=None;error=dict(type=type(exc).__name__,detail=str(exc))
        after=snapshot(ctx)
    return result,dict(error=error,caller_before=before,caller_after=after,caller_context_unchanged=before==after,
        input_id=identity,input_unchanged=_fp(data)==identity,source_version=info(ROOT.parent/'quantity_replay.py'))


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('before','after'));a=p.parse_args();rows=[]
    data=load(ROOT/'cases/complete/input.json')
    for item in load(ROOT/'contexts.json'):
        result,record=probe(data,item['context']);record['actual']=save_object(result) if result is not None else None
        save(ROOT/a.stage/item['name']/'actual.json',record)
        rows.append(dict(name=item['name'],actual_id=record['actual']['id'] if record['actual'] else None,
            error=record['error'],caller_context_unchanged=record['caller_context_unchanged'],input_unchanged=record['input_unchanged']))
        print(item['name'],rows[-1]['actual_id'],record['error'],flush=True)
    normal=load(ROOT/'before/normal/actual.json')['actual']['id']
    for row in rows:row['equal_before_normal']=row['actual_id']==normal
    save(ROOT/a.stage/'summary.json',rows)


if __name__=='__main__':main()
