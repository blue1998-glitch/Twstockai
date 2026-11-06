"""Direct simulate diagnostics; never invoke quantity replay or generation."""
import argparse
from copy import deepcopy
from decimal import localcontext
import json
import sys
import traceback
from capital_research.execution import simulate
from capital_research.lifecycle import _fp
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .prepare import ROOT,PROJECT,CASES,load,save,info


def source():
    s=load(ROOT/'input.json');meta=s['source'];assert info(PROJECT/meta['path'])==meta
    value=load(PROJECT/meta['path']);assert _fp(value)==s['source_id'];return s,value


def case(name):
    s,value=source();spec=next(c for c in s['cases'] if c['name']==name);frame=value['replay']['rounds'][spec['round_index']]
    job=deepcopy(frame['execution_job']);expected=frame['execution']
    assert _fp(job)==spec['job_id'] and _fp(expected)==spec['expected_execution_id'];return job,expected,spec


def controls():
    ref=load(ROOT/'input.json')['controls_reference'];assert info(PROJECT/ref['path'])==ref;return load(PROJECT/ref['path'])


def preset():
    ref=load(ROOT/'input.json')['preset_reference'];assert info(PROJECT/ref['path'])==ref;return load(PROJECT/ref['path'])['preset']


def regression(name):
    spec=next(x for x in load(ROOT/'regression-specs.json') if x['name']==name);job,_,_=case(spec['source_case'])
    if name=='cost-mismatch':job['ledger_input']['terminal_costs']['fee_rate']='0'
    elif name=='opening-right-drop':job['ledger_input']['opening']['cash_claims']=[]
    elif name=='wrong-latest':
        _,value=source();job['continuation']['previous_decision']=dict(decision=deepcopy(value['replay']['rounds'][0]['generation']['research']['baseline']))
    return job


def stored_actual(value,spec,expected):
    if value==expected:return dict(kind='EXACT_EXISTING_EXECUTION',case=spec['name'],id=_fp(value))
    p=ROOT/'objects'/(_fp(value).split(':')[1]+'.json');p.parent.mkdir(exist_ok=True)
    body=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n'
    if p.exists():assert p.read_text()==body
    else:
        with p.open('x') as f:f.write(body)
    return dict(kind='NEW_COMPLETE_DIFFERING_OUTPUT',path=str(p.relative_to(ROOT)),id=_fp(value))


def actual_value(record):
    a=record['actual']
    if a is None:return None
    if a['kind']=='EXACT_EXISTING_EXECUTION':_,value,_=case(a['case'])
    else:value=load(ROOT/a['path'])
    assert _fp(value)==a['id'];return value


def probe(job,setting):
    original=_fp(job);calls=dict(simulate=0,decide=0,resume=0,ledger_replay=0,risk=0,replay_sequence=0,generate=0,save=0)
    def profile(frame,event,arg):
        if event!='call':return
        p=frame.f_code.co_filename;n=frame.f_code.co_name
        for k,path,name in [('simulate','/capital_research/execution.py','simulate'),('decide','/capital_research/core.py','decide'),
                ('resume','/capital_research/core.py','resume_decision'),('ledger_replay','/rotation_research/action_ledger.py','replay'),
                ('risk','/transition_risk.py','inspect_risk'),('replay_sequence','/quantity_replay.py','replay_sequence'),
                ('generate','/quantity_candidates.py','generate'),('save','/rotation_research/store.py','save')]:
            if p.endswith(path) and n==name:calls[k]+=1
    with localcontext(context(setting)) as ctx:
        before=snapshot(ctx);sys.setprofile(profile)
        try:value=simulate(job);error=None;trace=None
        except Exception as exc:value=None;error=dict(type=type(exc).__name__,detail=str(exc));trace=traceback.format_exc()
        finally:sys.setprofile(None)
        after=snapshot(ctx)
    return value,dict(error=error,traceback=trace,calls=calls,caller_before=before,caller_after=after,input_id=original,
        input_unchanged=_fp(job)==original,caller_context_unchanged=before==after,source_version=info(ROOT.parent/'execution.py'))


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('before','after'));p.add_argument('--regressions',action='store_true');a=p.parse_args();rows=[]
    if a.regressions:
        for spec in load(ROOT/'regression-specs.json'):
            job=regression(spec['name'])
            for c in (controls()[0],dict(name='preset',context=preset())):
                value,r=probe(job,c['context']);r['actual']=value
                r['expected_rejection']=bool(r['error'] and r['error']['type']=='ValueError' and spec['error'] in r['error']['detail'])
                save(ROOT/a.stage/'regressions'/spec['name']/c['name']/'actual.json',r)
                rows.append(dict(case=spec['name'],context=c['name'],error=r['error'],expected_rejection=r['expected_rejection']))
                print(spec['name'],c['name'],r['error'],r['expected_rejection'],flush=True)
        save(ROOT/a.stage/'regressions/summary.json',rows);return
    for name in CASES:
        job,expected,spec=case(name)
        for c in controls():
            value,r=probe(job,c['context']);r['actual']=stored_actual(value,spec,expected) if value is not None else None
            r['equal_original']=value==expected;save(ROOT/a.stage/name/c['name']/'actual.json',r)
            rows.append(dict(case=name,context=c['name'],equal_original=value==expected,error=r['error'],calls=r['calls'],
                input_unchanged=r['input_unchanged'],caller_context_unchanged=r['caller_context_unchanged']))
            print(name,c['name'],value==expected,r['error'],r['calls'],flush=True)
    save(ROOT/a.stage/'summary.json',rows)


if __name__=='__main__':main()
