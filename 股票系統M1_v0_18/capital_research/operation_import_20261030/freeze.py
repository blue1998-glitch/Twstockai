"""Create-only saved-result inputs and independent expectations, before code."""
from copy import deepcopy
import json,hashlib,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent.parent
REPO=PROJECT.parent
def load(p):return json.loads(p.read_text())
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False);f.write('\n')
def fp(x):return 'sha256:'+hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def info(p):
    b=p.read_bytes();return dict(path=str(p.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def main():
    from capital_research.research_operation import read_operation
    prior=PROJECT/'capital_research/choice_v04_20261029';sources=[];names=[];positive_ids=set();negative_ids=set()
    def read(p):sources.append(info(p));return load(p)
    def original(name):
        q=read(prior/'cases'/name/'input.json');c=read(prior/'final'/name/'read.json')['record']['value']
        return dict(schema='capital-research-operation-import-input/0.1',synthetic=True,saved_source=q['saved_result'],choice=c)
    def add(name,x,status,**e):
        save(ROOT/'cases'/name/'input.json',x);save(ROOT/'cases'/name/'expected.json',dict(workflow_status=status,**e));names.append(name)
        (negative_ids if status=='INPUT_REFUSED' else positive_ids).add(fp(x))
    for name,status in [('general-full','COMPLETED_RESEARCH_INTENT'),('conditional-full','COMPLETED_CONDITIONAL_INTENT'),
            ('checkpoint-new-trigger','COMPLETED_CONDITIONAL_INTENT'),('zero-addition','COMPLETED_RESEARCH_INTENT'),
            ('hold','COMPLETED_RESEARCH_INTENT'),('outer-unknown','CHOICE_REFUSED')]:
        add(name,original(name),status,choice_status='REFUSED' if status=='CHOICE_REFUSED' else
            'RECORDED_CONDITIONAL_RESEARCH_INTENT' if status=='COMPLETED_CONDITIONAL_INTENT' else 'RECORDED_RESEARCH_INTENT',
            source_check_calls=0 if status=='CHOICE_REFUSED' else 1)
    base=original('conditional-full')
    bad=deepcopy(base);bad['saved_source']=original('general-full')['saved_source'];add('cross-source',bad,'INPUT_REFUSED')
    for name in ('missing-source','missing-choice','null-choice','wrong-request-id','missing-token','wrong-role','changed-account','changed-unit','changed-search','incomplete-generation','missing-choice-binding'):
        bad=deepcopy(base);s=bad['saved_source'];c=bad['choice']['choice']
        if name=='missing-source':del bad['saved_source']
        if name=='missing-choice':del bad['choice']
        if name=='null-choice':bad['choice']=None
        if name=='wrong-request-id':c['request_id']='wrong'
        if name=='missing-token':
            bad=original('checkpoint-new-trigger');c=bad['choice']['choice'];c['source_binding']['decision_reviewed_tokens']=c['source_binding']['decision_reviewed_tokens'][1:]
        if name=='wrong-role':c['source_roles']=dict(incumbent='B',destination='A')
        if name=='changed-account':s['quantity_request']['decision_input']['account']['reserved_cash']='0'
        if name=='changed-unit':s['quantity_request']['quantity_domain']['assets']['B']['unit_shares']='4'
        if name=='changed-search':s['quantity_request']['full_search']['max_probes']='1'
        if name=='incomplete-generation':s['generation']['research']['enumeration_complete']=False
        if name=='missing-choice-binding':c['source_binding']=None
        if name in ('wrong-request-id','missing-token','wrong-role','missing-choice-binding'):c['record_id']=fp({k:v for k,v in c.items() if k!='record_id'})
        add(name,bad,'INPUT_REFUSED')
    legacy=read(prior/'legacy/grid-new-trigger/before.json');bad=deepcopy(base);bad['choice']=legacy;add('legacy-choice',bad,'INPUT_REFUSED')
    assert not positive_ids & negative_ids,'A frozen negative has no material difference from a positive'
    # Capture established READ routes only. No generate, select, engine or replay.
    old=PROJECT/'capital_research/research_operation_20261027/initial/runs'
    controls=[]
    for name in ('general','conditional','old-trigger','no-selection','search-limit'):
        store=old/name;identity='demo-'+name
        result=read_operation(store,identity);assert result['workflow_status']=='READ_ONLY',(name,result)
        save(ROOT/'legacy'/name/'before.json',result);controls.append(dict(name=name,store=str(store.relative_to(REPO)),identity=identity))
        sources.extend(info(p) for p in sorted(store.rglob('*')) if p.is_file())
    for name in ('research_operation.py','research_operation_cli.py'):
        p=PROJECT/'capital_research'/name;q=ROOT/'baseline'/name;q.parent.mkdir(parents=True,exist_ok=True)
        with q.open('xb') as f:f.write(p.read_bytes())
    protected=[PROJECT/'capital_research'/n for n in ('research_choice.py','research_choice_source.py','research_quantity_source.py','research_choice_workflow.py','quantity_choice_rules.py','lifecycle.py','quantity_candidates.py','core.py','execution.py','continuity.py','quantity_after_retry.py')]
    protected += [PROJECT/'rotation_research/store.py',PROJECT/'rotation_research/action_ledger.py',prior/'CHANGE_MANIFEST.json']
    save(ROOT/'case-index.json',dict(cases=names,legacy=controls,market_samples=0,negative_positive_overlap=0))
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),protected=[info(p) for p in protected],
        source_originals=list({x['path']:x for x in sources}.values())))
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]))
    print('Frozen',len(names),'import cases and five existing READ controls; numeric producer runs 0')

if __name__=='__main__':main()
