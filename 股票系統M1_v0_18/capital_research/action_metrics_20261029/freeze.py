"""Create-only source copies, complete new inputs and independent expectations."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from capital_research.lifecycle import _fp

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent.parent
REPO=PROJECT.parent

def load(p):return json.loads(p.read_text())
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False);f.write('\n')
def info(p):
    b=p.read_bytes();return dict(path=str(p.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def resign(bundle):
    """Explicit structural counterexamples, not newly produced ledger results."""
    r=bundle['action_result']['run'];e=r['execution'];cp=r['checkpoint']
    e['result_id']=_fp({k:v for k,v in e.items() if k!='result_id'})
    cp['execution_result']=deepcopy(e);cp['state']['row']=deepcopy(e['ledger']['daily'][-1])
    cp['state_id']=_fp(cp['state']);cp['checkpoint_id']=_fp(dict(schema=cp['schema'],state_id=cp['state_id']))
    cp['integrity']['execution_result_id']=e['result_id']
    if r['numeric_result'] is not None:
        n=r['numeric_result']
        for k,v in [('fills','fills'),('new_fill_ids','new_fill_ids'),('events','execution_events'),('order_states','order_states'),('risk_observations','risk_observations'),('ledger','ledger')]:n[k]=deepcopy(e[v])
        n['checkpoint_state']=deepcopy(cp['state'])

def main():
    original=PROJECT/'capital_research/explicit_sell_20261029'
    protected=[PROJECT/'capital_research'/n for n in ('lifecycle.py','core.py','execution.py','continuity.py','execution_continuation.py','cash_action.py','cash_action_execution.py','fact_lineage.py','eligibility.py','reassessment_history.py')]
    protected += [PROJECT/'rotation_research/action_ledger.py',original/'CHANGE_MANIFEST.json',original/'frozen.json',original/'tests-final.log']
    versions=[]
    for n in ('account_metrics.py','account_metrics_read.py'):
        q=PROJECT/'capital_research'/n;copy=ROOT/'baseline'/n;copy.parent.mkdir(parents=True,exist_ok=True)
        with copy.open('x') as f:f.write(q.read_text())
        versions.append(dict(current=info(q),archived=info(copy)))
    sources=[];names=[]
    def bundle(folder):
        a=original/folder/'execution-input.json';b=original/folder/'result.json';sources.extend([info(a),info(b)])
        return dict(schema='capital-saved-action-source/0.1',action_request=load(a),action_result=load(b),continuation=None)
    def add(name,b,status='REFUSED',at='2026-01-12T16:00:00+08:00',**expected):
        request=dict(schema='capital-action-account-metrics-input/0.1',synthetic=True,evaluation_at=at,saved_result=b)
        save(ROOT/'cases'/name/'input.json',request);save(ROOT/'cases'/name/'expected.json',dict(status=status,**expected));names.append(name)
    reduce=bundle('initial/reduce-B3');exit=bundle('initial/exit-B7');split=bundle('initial/split-exit');partial=bundle('initial/partial-exit-B20')
    for name,b,loss,last,fees in [('reduce-B3',reduce,'3.20','1176.80','3'),('exit-B7',exit,'3.28','1176.72','3'),('split-exit',split,'5.28','1174.72','5')]:
        add(name,b,'EVALUATED',numerator='-'+loss,denominator='1180',last_equity=last,fees=fees,duration=7,rows=8,recovery_date=None)
    continued=deepcopy(partial)
    for n in ('input.json','actual.json'):sources.append(info(original/'controls/partial'/n))
    continued['continuation']=dict(request=load(original/'controls/partial/input.json'),result=load(original/'controls/partial/actual.json'))
    add('continued-partial',continued,'EVALUATED',numerator='-3.54',denominator='1180',last_equity='1176.46',fees='3',duration=7,rows=8,recovery_date=None)
    prior=PROJECT/'capital_research/settled_resume_action_20261029/actual'
    for name in ('hold','independent-B20'):
        a=prior/name/'execution-input.json';b=prior/name/'result.json';sources.extend([info(a),info(b)])
        add('v01-'+name,dict(schema='capital-saved-action-source/0.1',action_request=load(a),action_result=load(b),continuation=None),'EVALUATED')
    add('partial-prefix',partial)
    add('early',exit,at='2026-01-12T15:59:59+08:00')
    add('equivalent-utc',exit,'EVALUATED',at='2026-01-12T08:00:00Z',numerator='-3.28',denominator='1180',last_equity='1176.72',fees='3',duration=7,rows=8,recovery_date=None)
    b=deepcopy(exit);del b['action_request'];add('missing-request',b)
    b=deepcopy(exit);b['action_result']=deepcopy(reduce['action_result']);add('cross-result',b)
    b=deepcopy(exit);b['action_request']['execution_spec']['orders'][0]['shares']='6';add('changed-external-order',b)
    b=deepcopy(exit);b['action_result']['run']['data_qualified']=True;add('qualification-upgrade',b)
    b=deepcopy(exit);b['action_request']['action_input']['account_source']['expected_latest_decision_id']='wrong';add('wrong-latest-request',b)
    for name in ('missing-day','missing-mark','future-mark','unknown-rights','changed-prefix','missing-token','wrong-reserve','wrong-latest-state','external-flow','lost-fact-history'):
        b=deepcopy(exit);r=b['action_result']['run'];e=r['execution'];cp=r['checkpoint'];rows=e['ledger']['daily']
        if name=='missing-day':rows.pop(5)
        elif name=='missing-mark':rows[5]['marks']['C']['value']=None
        elif name=='future-mark':rows[5]['marks']['C']['source_date']='2026-01-13'
        elif name=='unknown-rights':rows[5]['cash_claims']=None
        elif name=='changed-prefix':rows[1]['net_accrual_equity']='1170'
        elif name=='missing-token':e['reviewed_evidence_tokens'].pop();cp['state']['reviewed_evidence_tokens']=deepcopy(e['reviewed_evidence_tokens'])
        elif name=='wrong-reserve':cp['state']['general_reserved_cash']='0'
        elif name=='wrong-latest-state':cp['state']['latest_decision_id']='wrong'
        elif name=='external-flow':cp['state']['external_flow']='1'
        elif name=='lost-fact-history':cp['state']['fact_history']={}
        resign(b);add(name,b)
    b=deepcopy(exit);b['action_result']['run']['checkpoint']['origin_ledger_input']['opening']['cash']='999';resign(b);add('changed-origin',b)
    b=deepcopy(continued);b['continuation']['request']['checkpoint']['state']['accepted_fills']=[];add('missing-resume-history',b)
    b=deepcopy(continued);b['continuation']['result']['integrity']['root_job_id']='wrong';add('wrong-resume-root',b)
    b=deepcopy(exit);b['action_result']['run']['checkpoint']['origin_ledger_input']['sources']['fixture']['kind']='OFFICIAL_RAW';resign(b);add('real-relabel',b)
    a=prior/'old-trigger/execution-input.json';b=prior/'old-trigger/result.json';sources.extend([info(a),info(b)])
    add('stopped-action',dict(schema='capital-saved-action-source/0.1',action_request=load(a),action_result=load(b),continuation=None))
    # Existing quantity result is replayed nowhere: this is the necessary exact-output regression.
    old=load(PROJECT/'capital_research/decimal_context_20261027/input.json')
    for key in ('saved_source','baseline_expected'):sources.append(info(PROJECT/old[key]['path']))
    save(ROOT/'legacy.json',old)
    save(ROOT/'case-index.json',dict(cases=names,original_market_samples=0))
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        changing_sources=versions,protected=[info(q) for q in protected],source_originals=list({m['path']:m for m in sources}.values()),
        accounting_replay_calls=0,new_quotes=0,new_source_fetches=0))
    save(ROOT/'frozen.json',dict(files=[info(q) for q in sorted(ROOT.rglob('*')) if q.is_file()]))
    print('Frozen',len(names),'cases before implementation; originals unchanged')

if __name__=='__main__':main()
