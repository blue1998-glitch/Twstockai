"""Direct public decision calls with pinned, predeclared expectations."""
import argparse
from copy import deepcopy
from decimal import localcontext
import json
import sys
import traceback
from capital_research.core import decide,resume_decision
from capital_research.lifecycle import _fp
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .prepare import ROOT,PROJECT,CASES,projection,load,save,info


def case(name):
    spec=load(ROOT/'input.json');meta=spec['source'];assert info(PROJECT/meta['path'])==meta
    source=load(PROJECT/meta['path']);assert _fp(source)==spec['source_id']
    entry=next(e for e in spec['cases'] if e['name']==name);args,expected=projection(source,entry['round_index'])
    assert _fp(args)==entry['arguments_id'] and _fp(expected)==entry['expected_wrapper_id']
    return args,expected,entry


def controls():
    ref=load(ROOT/'input.json')['controls_reference'];assert info(PROJECT/ref['path'])==ref
    return load(PROJECT/ref['path'])


def preset():
    ref=load(ROOT/'input.json')['preset_reference'];assert info(PROJECT/ref['path'])==ref
    return load(PROJECT/ref['path'])['preset']


def regression(name):
    args,_,_=case('resume')
    if name=='wrong-latest':
        spec=load(ROOT/'input.json');source=load(PROJECT/spec['source']['path'])
        args['previous']=dict(decision=deepcopy(source['replay']['rounds'][0]['generation']['research']['baseline']))
    elif name=='checkpoint-token-change':args['checkpoint']['state']['reviewed_evidence_tokens'].pop(0)
    elif name=='reserve-drop':args['data']['account']['reserved_cash']='0'
    elif name=='cash-right-drop':args['data']['account']['cash_claims']=[]
    elif name=='missing-checkpoint':args['checkpoint']=None
    else:raise ValueError('Unknown frozen regression')
    return args


def stored_actual(value,spec,expected):
    if value==expected:return dict(kind='EXACT_SAVED_DECISION_AND_METADATA_PROJECTION',case=spec['name'],id=_fp(value))
    p=ROOT/'objects'/(_fp(value).split(':')[1]+'.json');p.parent.mkdir(exist_ok=True)
    body=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n'
    if p.exists():assert p.read_text()==body
    else:
        with p.open('x') as f:f.write(body)
    return dict(kind='NEW_COMPLETE_DIFFERING_OUTPUT',path=str(p.relative_to(ROOT)),id=_fp(value))


def actual_value(record):
    a=record['actual']
    if a is None:return None
    if a['kind']=='EXACT_SAVED_DECISION_AND_METADATA_PROJECTION':_,value,_=case(a['case'])
    else:value=load(ROOT/a['path'])
    assert _fp(value)==a['id'];return value


def probe(args,setting):
    original=_fp(args);counts=dict(decide=0,resume=0,inner_decide=0,bind_resume=0,ledger_replay=0,simulate=0,replay_sequence=0,save=0)
    def profile(frame,event,arg):
        if event!='call':return
        p=frame.f_code.co_filename;n=frame.f_code.co_name
        for k,path,name in [('decide','/capital_research/core.py','decide'),('resume','/capital_research/core.py','resume_decision'),
                ('inner_decide','/capital_research/core.py','_decide'),('bind_resume','/continuity.py','bind_resume'),
                ('ledger_replay','/rotation_research/action_ledger.py','replay'),('simulate','/execution.py','simulate'),
                ('replay_sequence','/quantity_replay.py','replay_sequence'),('save','/rotation_research/store.py','save')]:
            if p.endswith(path) and n==name:counts[k]+=1
    with localcontext(context(setting)) as ctx:
        before=snapshot(ctx);sys.setprofile(profile)
        try:value=(resume_decision if 'previous' in args else decide)(**args);error=None;trace=None
        except Exception as exc:value=None;error=dict(type=type(exc).__name__,detail=str(exc));trace=traceback.format_exc()
        finally:sys.setprofile(None)
        after=snapshot(ctx)
    return value,dict(error=error,traceback=trace,calls=counts,caller_before=before,caller_after=after,input_id=original,
        input_unchanged=_fp(args)==original,caller_context_unchanged=before==after,source_version=info(ROOT.parent/'core.py'))


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('before','after'));a=p.parse_args();rows=[]
    for name in CASES:
        args,expected,spec=case(name)
        for c in controls():
            value,record=probe(args,c['context']);record['actual']=stored_actual(value,spec,expected) if value is not None else None
            record['equal_original']=value==expected;save(ROOT/a.stage/name/c['name']/'actual.json',record)
            rows.append(dict(case=name,context=c['name'],equal_original=value==expected,error=record['error'],calls=record['calls'],
                caller_context_unchanged=record['caller_context_unchanged'],input_unchanged=record['input_unchanged']))
            print(name,c['name'],value==expected,record['error'],record['calls'],flush=True)
    save(ROOT/a.stage/'summary.json',rows)


if __name__=='__main__':main()
