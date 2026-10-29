"""Create-only exact saved-source inputs; never call a numerical producer."""
from copy import deepcopy
import hashlib,json,subprocess
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

def declared_binding(source):
    q=source['quantity_request'];g=source['generation'];r=g['research'];data=q['decision_input'];base=r.get('baseline') or {}
    continuation=q['continuation'];cp=continuation['checkpoint'] if continuation else None
    e=cp['execution_result'] if cp else None;s=cp['state'] if cp else None
    return dict(source_document_id=fp(source),generation_document_id=fp(g),quantity_request_id=fp(q),source_input_id=fp(q),
        baseline_document_id=fp(base),account_id=fp(data['account']),account_snapshot=deepcopy(data['account']),
        source_kind='CHECKPOINT_EPISODE' if cp else 'DECLARED_SYNTHETIC_OPENING',
        checkpoint_id=cp['checkpoint_id'] if cp else None,state_id=cp['state_id'] if cp else None,
        execution_result_id=e['result_id'] if e else None,origin_ledger_input_id=e['origin_ledger_input_id'] if e else None,
        origin_initial_capital=s['origin_initial_capital'] if s else None,
        latest_decision_id=e['latest_decision_id'] if e else None,latest_common_account_id=e['latest_common_account_id'] if e else None,
        data_cutoff=data['data_cutoff'],decision_at=data['decision_at'],historical_reviewed_tokens=deepcopy(s['reviewed_evidence_tokens']) if s else [],
        decision_reviewed_tokens=deepcopy(base.get('reviewed_evidence_tokens',[])),received_attempt_ids=[a['attempt_id'] for a in e['reassessment_attempts']] if e else [],
        fact_history_id=fp(base.get('fact_history')),quantity_domain=deepcopy(q['quantity_domain']),quantity_domain_id=fp(q['quantity_domain']),
        asset_identities={c:{k:v[k] for k in ('source_id','basis_id','adjustment_version')} for c,v in data['assets'].items()},
        full_search_policy=deepcopy(q['full_search']),full_search_receipt=deepcopy(r['full_search_receipt']),full_proposal_status=r['full_proposal_status'],
        versions=dict(source_wrapper=source['schema'],generation=r['schema'],checkpoint=cp['schema'] if cp else None,decision=base.get('schema')))

def main():
    from capital_research.research_choice import choose_saved
    prior=PROJECT/'capital_research/unit_full_search_20261029';sources=[];names=[]
    def source(name):
        qp=prior/'cases'/name/'input.json';gp=prior/'actual'/name/'actual.json';sources.extend([info(qp),info(gp)])
        return dict(schema='capital-saved-quantity-source/0.1',synthetic=True,quantity_request=load(qp),generation=load(gp)['result'])
    def choice(s,mode='FULL_TRANSFER',sell=None,buy=None):
        return dict(schema='capital-research-choice-input/0.2',synthetic=True,saved_result=deepcopy(s),source_binding=declared_binding(s),
            selection=dict(mode=mode,sell_A=sell,additional_B=buy,reason='明示合成研究意圖；非最佳量或交易批准'),recorded_at=s['quantity_request']['decision_input']['decision_at'])
    def add(name,x,status='REFUSED',**expected):
        save(ROOT/'cases'/name/'input.json',x);save(ROOT/'cases'/name/'expected.json',dict(status=status,**expected));names.append(name)
    base=source('manual-93');req=choice(base)
    add('conditional-full',req,'RECORDED_CONDITIONAL_RESEARCH_INTENT',target_B='93')
    add('general-full',choice(source('non-monotone')),'RECORDED_RESEARCH_INTENT',target_B='2')
    add('hold',choice(base,'HOLD'),'RECORDED_RESEARCH_INTENT',target_B='0')
    add('grid',choice(base,'GRID','2','3'),'RECORDED_RESEARCH_INTENT',target_B='3')
    add('exit-A',choice(base,'EXIT_A_KEEP_CASH'),'RECORDED_RESEARCH_INTENT',target_B='0')
    add('checkpoint-new-trigger',choice(source('additional-independent')),'RECORDED_CONDITIONAL_RESEARCH_INTENT',target_B='93')
    add('checkpoint-valid-old-fact',choice(source('first-old-fact-reviewed')),'RECORDED_CONDITIONAL_RESEARCH_INTENT',target_B='93')
    old=source('additional-old-trigger');add('zero-addition',choice(old),'RECORDED_RESEARCH_INTENT',target_B='0',additional_B='0')
    add('old-trigger-buy-not-listed',choice(old,'GRID','0','3'))
    for name in ('outer-unknown','full-A-unit-mismatch','search-limit'):add(name,choice(source(name)))
    add('hold-when-full-rejected',choice(source('full-A-unit-mismatch'),'HOLD'),'RECORDED_RESEARCH_INTENT',target_B='0')
    for name in ('wrong-request-fingerprint','wrong-domain','missing-domain','wrong-policy','wrong-receipt','duplicate-id','wrong-account','wrong-cutoff','bad-unit-time','bad-selected-quantity'):
        s=deepcopy(base);q=s['quantity_request'];r=s['generation']['research']
        if name=='wrong-request-fingerprint':s['generation']['source_integrity_metadata']['full_request_id']='wrong'
        if name=='wrong-domain':r['quantity_domain']['assets']['B']['unit_shares']='4'
        if name=='missing-domain':del q['quantity_domain']
        if name=='wrong-policy':r['full_search_policy']['max_probes']='1'
        if name=='wrong-receipt':r['full_search_receipt']['selected_target']['B']='90'
        if name=='duplicate-id':r['candidates'].append(deepcopy(r['candidates'][-1]))
        if name=='wrong-account':q['decision_input']['account']['reserved_cash']='0'
        if name=='wrong-cutoff':q['decision_input']['data_cutoff']='2026-01-04T14:00:00+08:00'
        if name=='bad-unit-time':
            q['quantity_domain']['assets']['B']['available_at']='2026-01-06T15:00:00+08:00';r['quantity_domain']=deepcopy(q['quantity_domain']);r['quantity_domain_id']=fp(q['quantity_domain'])
        if name=='bad-selected-quantity':r['candidates'][-1]['plan']['targets']['B']='90'
        if name not in ('wrong-request-fingerprint','missing-domain'):s['generation']['source_integrity_metadata']['full_request_id']=fp(q)
        if name=='missing-domain':
            x=deepcopy(req);x['saved_result']=s
        else:x=choice(s)
        add(name,x)
    for name in ('wrong-latest','missing-token','wrong-reserve','fake-opening'):
        s=source('additional-independent');q=s['quantity_request'];g=s['generation']
        if name=='wrong-latest':q['continuation']['previous_decision']['decision']['decision_id']='wrong'
        if name=='missing-token':q['decision_input']['consumed_evidence_tokens']=[]
        if name=='wrong-reserve':q['decision_input']['account']['reserved_cash']='0'
        if name=='fake-opening':q['continuation']=None;q['batch_context']['origin']='DECLARED_SYNTHETIC_OPENING'
        g['source_integrity_metadata']['full_request_id']=fp(q);add(name,choice(s))
    bad=deepcopy(req);bad['source_binding']=declared_binding(source('non-monotone'));add('borrow-binding',bad)
    bad=deepcopy(req);bad['selection']['reason']=' ';add('missing-reason',bad)
    bad=deepcopy(req);bad['selection'].update(mode='GRID',sell_A='1',additional_B='1');add('unlisted-quantity',bad)
    bad=deepcopy(req);bad['recorded_at']='2026-01-04T15:00:00+08:00';add('record-before-decision',bad)
    bad=deepcopy(req);bad['schema']='capital-research-choice-input/0.1';add('downgrade',bad)
    # Persist the actual legacy requests and their unchanged pre-change controls.
    for name in ('grid-new-trigger','exit-A-cash','unknown-refused'):
        p=PROJECT/'capital_research/research_choice_20261027/cases'/name/'input.json';sources.append(info(p));x=load(p)
        save(ROOT/'legacy'/name/'input.json',x);save(ROOT/'legacy'/name/'before.json',choose_saved(x))
    changed=[]
    for name in ('research_choice.py','research_choice_source.py'):
        p=PROJECT/'capital_research'/name;q=ROOT/'baseline'/name;q.parent.mkdir(parents=True,exist_ok=True)
        with q.open('xb') as f:f.write(p.read_bytes())
        changed.append(info(p))
    protected=[PROJECT/'capital_research'/n for n in ('quantity_candidates.py','quantity_domain.py','allocation.py','core.py','execution.py','continuity.py','quantity_after_retry.py','quantity_choice_rules.py','research_choice_workflow.py','research_choice_cli.py','research_choice_view.py','research_operation.py','lifecycle.py')]
    protected += [PROJECT/'rotation_research/action_ledger.py',PROJECT/'rotation_research/store.py',prior/'CHANGE_MANIFEST.json']
    save(ROOT/'case-index.json',dict(cases=names,market_samples=0))
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),changing=changed,
        protected=[info(p) for p in protected],source_originals=list({x['path']:x for x in sources}.values())))
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]))
    print('Frozen',len(names),'selection cases and three legacy controls before implementation')

if __name__=='__main__':main()
