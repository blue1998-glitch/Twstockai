"""Freeze source-bound import inputs; never run a numerical producer."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,subprocess
from capital_research.lifecycle import _fp

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent.parent
REPO=PROJECT.parent
def load(p):return json.loads(p.read_text())
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False);f.write('\n')
def info(p):
    b=p.read_bytes();return dict(path=str(p.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def resign(e):e['evaluation_id']=_fp({k:v for k,v in e.items() if k!='evaluation_id'})

def main():
    prior=PROJECT/'capital_research/action_metrics_20261029';sources=[];cases=[]
    originals=[]
    p=PROJECT/'capital_research/action_account_metrics.py';q=ROOT/'baseline/action_account_metrics.py';q.parent.mkdir(parents=True,exist_ok=True)
    with q.open('x') as f:f.write(p.read_text())
    originals.append(dict(current=info(p),archived=info(q)))
    def add(name,r,status,**expected):
        save(ROOT/'cases'/name/'input.json',r);save(ROOT/'cases'/name/'expected.json',dict(storage_status=status,**expected));cases.append(name)
    valid={}
    for name in ('exit-B7','reduce-B3','continued-partial','partial-prefix','stopped-action'):
        a=prior/'cases'/name/'input.json';b=prior/'final-corrected'/name/'actual.json';sources.extend([info(a),info(b)])
        inp=load(a);e=load(b);r=dict(schema='capital-action-evaluation-import-input/0.1',synthetic=True,evaluation_input=inp,evaluation=e,
            expected_evaluation_input_id=_fp(inp),expected_evaluation_id=e['evaluation_id'])
        add(name,r,'SAVED_AND_READ_BACK',evaluation_status=e['status']);valid[name]=r
    base=valid['exit-B7']
    for name in ('missing-source','wrong-input-id','wrong-evaluation-id','cross-source','wrong-time','wrong-latest','missing-token','wrong-reserve','qualified','unknown-schema','refusal-with-metrics'):
        r=deepcopy(base)
        if name=='missing-source':del r['evaluation_input']['saved_result']['action_request']
        elif name=='wrong-input-id':r['expected_evaluation_input_id']='wrong'
        elif name=='wrong-evaluation-id':r['expected_evaluation_id']='wrong'
        elif name=='cross-source':r['evaluation_input']=deepcopy(valid['reduce-B3']['evaluation_input'])
        elif name=='wrong-time':r['evaluation_input']['evaluation_at']='2026-01-12T15:59:59+08:00'
        elif name=='wrong-latest':r['evaluation']['account']['latest_decision_id']='wrong'
        elif name=='missing-token':r['evaluation']['account']['reviewed_evidence_tokens'].pop()
        elif name=='wrong-reserve':r['evaluation']['account']['general_reserved_cash']='0'
        elif name=='qualified':r['evaluation']['data_qualified']=True
        elif name=='unknown-schema':r['evaluation']['schema']='capital-action-account-metrics/99'
        elif name=='refusal-with-metrics':r['evaluation']['status']='REFUSED'
        if name not in ('wrong-input-id','wrong-evaluation-id'):
            r['expected_evaluation_input_id']=_fp(r['evaluation_input']);resign(r['evaluation']);r['expected_evaluation_id']=r['evaluation']['evaluation_id']
        add(name,r,'NOT_SAVED')
    save(ROOT/'case-index.json',dict(cases=cases,synthetic_only=True))
    names=('account_metrics.py','account_metrics_read.py','lifecycle.py','core.py','execution.py','continuity.py','execution_continuation.py','cash_action.py','cash_action_execution.py','fact_lineage.py','reassessment_history.py','research_operation.py','research_choice_workflow.py')
    protected=[PROJECT/'capital_research'/n for n in names]+[PROJECT/'rotation_research/store.py',PROJECT/'rotation_research/action_ledger.py',prior/'CHANGE_MANIFEST.json',prior/'tests-corrected.log']
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        changing_sources=originals,source_originals=sources,protected=[info(p) for p in protected],new_evaluations=0,accounting_replay_calls=0))
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]))
    print('Frozen',len(cases),'explicit import cases; no evaluation or replay')

if __name__=='__main__':main()
