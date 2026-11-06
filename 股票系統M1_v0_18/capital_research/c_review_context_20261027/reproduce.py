"""Direct C review/retry requests; preserve mandatory nested call visibility."""
import argparse
from decimal import localcontext
import json
import sys
import traceback
from capital_research.conditional_quantity_review import reassess_conditional
from capital_research.conditional_retry import retry_rejected
from capital_research.lifecycle import _fp
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .prepare import ROOT,PROJECT,PRIMARY,load,save,info


def case(name):
    s=next(c for c in load(ROOT/'input.json')['cases'] if c['name']==name)
    for k in ('input','expected','original_actual'):assert info(PROJECT/s[k]['path'])==s[k]
    request=load(PROJECT/s['input']['path']);expected=load(PROJECT/s['original_actual']['path'])
    assert _fp(request)==s['input_id'] and _fp(expected)==s['expected_result_id'];return request,expected,s


def controls():
    r=load(ROOT/'input.json')['controls_reference'];assert info(PROJECT/r['path'])==r;return load(PROJECT/r['path'])


def preset():
    r=load(ROOT/'input.json')['preset_reference'];assert info(PROJECT/r['path'])==r;return load(PROJECT/r['path'])['preset']


def source_versions():return {n:info(ROOT.parent/n) for n in ('conditional_quantity_review.py','conditional_retry.py')}


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
        assert info(PROJECT/a['source']['path'])==a['source'];v=load(PROJECT/a['source']['path'])
    else:v=load(ROOT/a['path'])
    assert _fp(v)==a['id'];return v


def probe(request,entry,setting):
    original=_fp(request);calls=dict(review=0,retry=0,quantity_replay=0,simulate=0,ledger_replay=0,generate=0,save=0)
    def profile(frame,event,arg):
        if event!='call':return
        p=frame.f_code.co_filename;n=frame.f_code.co_name
        for k,path,name in [('review','/conditional_quantity_review.py','reassess_conditional'),('retry','/conditional_retry.py','retry_rejected'),
                ('quantity_replay','/quantity_replay.py','replay_sequence'),('simulate','/execution.py','simulate'),
                ('ledger_replay','/rotation_research/action_ledger.py','replay'),('generate','/quantity_candidates.py','generate'),
                ('save','/rotation_research/store.py','save')]:
            if p.endswith(path) and n==name:calls[k]+=1
    with localcontext(context(setting)) as ctx:
        before=snapshot(ctx);sys.setprofile(profile)
        try:value=(reassess_conditional if entry=='review' else retry_rejected)(request);error=None;trace=None
        except Exception as exc:value=None;error=dict(type=type(exc).__name__,detail=str(exc));trace=traceback.format_exc()
        finally:sys.setprofile(None)
        after=snapshot(ctx)
    return value,dict(error=error,traceback=trace,calls=calls,caller_before=before,caller_after=after,input_id=original,
        input_unchanged=_fp(request)==original,caller_context_unchanged=before==after,source_versions=source_versions())


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('before','after-review-only','after'));p.add_argument('--regressions',action='store_true');a=p.parse_args();rows=[]
    specs=load(ROOT/'input.json')['cases']
    if a.stage=='after-review-only':specs=[s for s in specs if s['name']=='retry']
    elif a.regressions:specs=[s for s in specs if s['role']=='necessary_regression']
    else:specs=[s for s in specs if s['name'] in PRIMARY]
    for spec in specs:
        request,expected,s=case(spec['name'])
        selected=(controls()[0],dict(name='preset',context=preset())) if a.regressions else controls()
        for c in selected:
            value,r=probe(request,s['entry'],c['context']);r['actual']=stored_actual(value,s,expected) if value is not None else None
            r['equal_original']=value==expected
            folder=ROOT/a.stage/('regressions' if a.regressions else 'primary')/s['name']/c['name']
            save(folder/'actual.json',r)
            rows.append(dict(case=s['name'],context=c['name'],equal_original=value==expected,error=r['error'],calls=r['calls'],
                caller_context_unchanged=r['caller_context_unchanged'],input_unchanged=r['input_unchanged']))
            print(s['name'],c['name'],value==expected,r['error'],r['calls'],flush=True)
    save(ROOT/a.stage/('regressions' if a.regressions else 'primary')/'summary.json',rows)


if __name__=='__main__':main()
