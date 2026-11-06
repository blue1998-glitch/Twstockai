"""Create-only inputs, independent expectations and legacy controls before change."""
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
def info(p):
    b=p.read_bytes();return dict(path=str(p.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def main():
    from capital_research.quantity_candidates import generate
    from capital_research.core import fingerprint
    sources=[];cases=[]
    def read(p):sources.append(info(p));return load(p)
    old=PROJECT/'capital_research/quantity_candidates_v02_20261026/cases'
    domain=PROJECT/'capital_research/quantity_domain_20261029'
    base=read(domain/'cases/full-unit-mismatch/input.json')
    def convert(r,ua=None,ub=None):
        r=deepcopy(r);r['schema']='capital-quantity-candidates-input/0.4';d=r['decision_input']
        if 'quantity_domain' not in r:
            r['quantity_domain']=deepcopy(base['quantity_domain']);r['quantity_domain']['account_id']=fingerprint(d['account'])
            r['quantity_domain']['available_at']=d['data_cutoff']
            for c in ('A','B'):
                row=r['quantity_domain']['assets'][c]
                for k in ('source_id','basis_id','adjustment_version'):row[k]=d['assets'][c][k]
                row['available_at']=d['data_cutoff'];row['unit_shares']='1'
        for c,u in (('A',ua),('B',ub)):
            if u:r['quantity_domain']['assets'][c]['unit_shares']=u
        r['full_search']=dict(schema='capital-full-unit-search/0.1',version='FROZEN_SYNTHETIC_RESOURCE_BOUND/0.1',
            parameter_source='EXPLICIT_RESEARCH_COMPUTATION_LIMIT_NOT_TRADING_POLICY',available_at=d['data_cutoff'],max_probes='128')
        return r
    def add(name,r,status='COMPLETE',**e):
        save(ROOT/'cases'/name/'input.json',r);save(ROOT/'cases'/name/'expected.json',dict(status=status,**e));cases.append(name)
    add('manual-93',convert(base),target_B='93',full_status='FOUND',classification='WAIT_SETTLEMENT_REASSESSMENT',
        probes=['111','108','105','102','99','96','93'],legal_count=38,
        manual=dict(settled_available='900',sale_net='995',joint_available_after_sale='1895',buy_93='1863.86',buy_96='1923.92'))
    add('unit-one',convert(base,'1','1'),target_B='94',classification='WAIT_SETTLEMENT_REASSESSMENT',full_status='FOUND')
    non=convert(base,'1','1');d=non['decision_input'];d['scenario_set']['scenarios']=[dict(id='explicit-hedge',prices=dict(A='11',B='30',C='15'))]
    d['risk_limits']['single_name_value']['B']='45';d['risk_limits']['group_value']['new']='45';d['risk_limits']['account_stress_loss']='5'
    non['bounds']=dict(sell_A=dict(minimum='100',maximum='100'),additional_B=dict(minimum='0',maximum='3'))
    add('non-monotone',non,target_B='2',full_status='FOUND',classification='CURRENTLY_FEASIBLE',grid_classes={'0':'REJECTED','1':'CURRENTLY_FEASIBLE','2':'CURRENTLY_FEASIBLE','3':'REJECTED'})
    bad=deepcopy(non);bad['batch_context']['phase']='UNKNOWN';add('outer-unknown',bad,full_status='NO_FEASIBLE_TARGET',new_buy_reason='BATCH_PHASE_UNKNOWN')
    for name in ('additional-independent','additional-old-trigger','first-old-fact-reviewed'):
        r=convert(read(old/name/'input.json'),'1','3')
        add(name,r,full_status='FOUND_ZERO_ADDITION' if name=='additional-old-trigger' else 'FOUND',
            new_buy_reason='NO_NEW_INDEPENDENT_TRIGGER' if name=='additional-old-trigger' else None,
            preserve_continuation=True)
    r=convert(read(domain/'corrections/existing-B3-add2-declared-opening/input.json'),'2','2')
    add('existing-B3',r,target_B='97',full_status='FOUND',classification='WAIT_SETTLEMENT_REASSESSMENT',delta_unit=2)
    for name in ('liquidity-limit','common-risk-limit','cost-cannot-be-free'):
        add(name,convert(read(old/name/'input.json'),'1','1'),all_probes_use_gate=True)
    bad=convert(base,'3','3');add('full-A-unit-mismatch',bad,full_status='REJECTED_DOMAIN',probe_count=0)
    bad=convert(base);bad['decision_input']['account']['holdings']['A']['sellable']='90'
    bad['batch_context']['account_id']=fingerprint(bad['decision_input']['account']);bad['quantity_domain']['account_id']=bad['batch_context']['account_id']
    add('not-fully-sellable',bad,full_status='REJECTED_PRECONDITION',probe_count=0)
    bad=convert(base);bad['full_search']['max_probes']='1';add('search-limit',bad,'REFUSED_SEARCH_LIMIT',full_status='REFUSED_SEARCH_LIMIT',probe_count=0)
    for name in ('zero-cap','future-policy','missing-policy-source','unknown-policy-time','wrong-unit-source'):
        bad=convert(base)
        if name=='zero-cap':bad['full_search']['max_probes']='0'
        if name=='future-policy':bad['full_search']['available_at']='2026-01-06T16:00:00+08:00'
        if name=='missing-policy-source':bad['full_search']['parameter_source']=''
        if name=='unknown-policy-time':bad['full_search']['available_at']=None
        if name=='wrong-unit-source':bad['quantity_domain']['assets']['B']['source_id']='foreign'
        add(name,bad,'VALUE_ERROR',core_calls=0)
    for name in ('future-A-wins','future-B-wins','future-both-fall'):
        r=convert(read(old/name/'input.json'),'2','3');r['bounds']=deepcopy(base['bounds'])
        add(name,r,same_research_as='manual-93')
    # Exact pre-change controls, not historical actuals computed with older sources.
    for version in ('0.1','0.2','0.3'):
        r=deepcopy(base);r['schema']='capital-quantity-candidates-input/'+version
        if version in ('0.1','0.2'):del r['quantity_domain']
        if version=='0.1':
            del r['batch_context'];r['bounds']=dict(retained_A=dict(minimum='96',maximum='100'),additional_B=dict(minimum='0',maximum='4'))
        save(ROOT/'legacy'/version/'input.json',r)
        save(ROOT/'legacy'/version/'before.json',generate(r))
    changing=[]
    for name in ('allocation.py','quantity_candidates.py'):
        p=PROJECT/'capital_research'/name;q=ROOT/'baseline'/name;q.parent.mkdir(parents=True,exist_ok=True)
        with q.open('xb') as f:f.write(p.read_bytes())
        changing.append(info(p))
    protected=[PROJECT/'capital_research'/n for n in ('core.py','quantity_domain.py','execution.py','continuity.py','eligibility.py','fact_lineage.py','quantity_replay.py')]
    protected+=[PROJECT/'rotation_research/action_ledger.py',domain/'CHANGE_MANIFEST.json',domain/'final/source-versions.json']
    save(ROOT/'case-index.json',dict(cases=cases,original_market_samples=0))
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),changing_sources=changing,
        protected=[info(p) for p in protected if p.exists()],source_originals=list({m['path']:m for m in sources}.values())))
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]))
    print('Frozen',len(cases),'cases and three legacy controls before implementation')

if __name__=='__main__':main()
