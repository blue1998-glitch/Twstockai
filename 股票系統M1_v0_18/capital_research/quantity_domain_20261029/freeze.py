"""Create-only new domain inputs and manual expected sets before implementation."""
from copy import deepcopy
from pathlib import Path
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

def main():
    prior=PROJECT/'capital_research/quantity_candidates_v02_20261026/cases';sources=[];cases=[]
    original=PROJECT/'capital_research/quantity_candidates.py';archive=ROOT/'baseline/quantity_candidates.py';archive.parent.mkdir(parents=True,exist_ok=True)
    with archive.open('x') as f:f.write(original.read_text())
    def old(name):
        p=prior/name/'input.json';sources.append(info(p));return load(p)
    def convert(r,ua='2',ub='2'):
        r=deepcopy(r);r['schema']='capital-quantity-candidates-input/0.3';data=r['decision_input'];a,b=r['incumbent'],r['destination']
        r['quantity_domain']=dict(schema='capital-quantity-domain/0.1',version='EXPLICIT_SYNTHETIC_UNITS/0.1',
            parameter_source='FROZEN_SYNTHETIC_QUANTITY_UNITS_NOT_MARKET_RULE',available_at=data['data_cutoff'],account_id=_fp(data['account']),assets={})
        for c,u in ((a,ua),(b,ub)):
            asset=data['assets'][c];r['quantity_domain']['assets'][c]=dict(code=c,channel_id='DECLARED_SYNTHETIC_'+c,
                unit_shares=u,source_id=asset['source_id'],basis_id=asset['basis_id'],adjustment_version=asset['adjustment_version'],available_at=data['data_cutoff'])
        return r
    def add(name,r,status='COMPLETE',**expected):
        save(ROOT/'cases'/name/'input.json',r);save(ROOT/'cases'/name/'expected.json',dict(status=status,**expected));cases.append(name)
    base=old('first-manual-grid');r=convert(base);r['bounds']=dict(sell_A=dict(minimum='0',maximum='4'),additional_B=dict(minimum='0',maximum='4'))
    manual=[['0','0'],['0','2'],['0','4'],['2','0'],['2','2'],['2','4'],['4','0'],['4','2'],['4','4']]
    add('manual-grid',r,grid=manual,grid_points=9,full_status='LEGACY_ENDPOINT_IN_DECLARED_DOMAIN')
    add('unit-one',convert(base,'1','1'),grid_points=9,legacy_input=info(prior/'first-manual-grid/input.json'))
    bad=deepcopy(r);bad['quantity_domain']['assets']['B']['unit_shares']='3';add('full-unit-mismatch',bad,grid_points=6,full_status='NOT_IMPLEMENTED_IN_DECLARED_DOMAIN')
    bad=deepcopy(r);bad['quantity_domain']['assets']['A']['unit_shares']='3';add('exit-unit-mismatch',bad,grid_points=6,exit_rejected=True)
    odd=convert(base,'100','2');odd['decision_input']['account']['holdings']['A'].update(shares='105',sellable='105')
    odd['batch_context']['account_id']=_fp(odd['decision_input']['account']);odd['quantity_domain']['account_id']=odd['batch_context']['account_id']
    odd['bounds']=dict(sell_A=dict(minimum='100',maximum='100'),additional_B=dict(minimum='0',maximum='0'))
    add('retain-existing-odd-shares',odd,grid=[['100','0']],grid_points=1,retained_A='5')
    odd=convert(old('additional-independent'),'5','2');odd['decision_input']['account']['holdings']['B'].update(shares='3',sellable='3')
    odd['batch_context']['account_id']=_fp(odd['decision_input']['account']);odd['quantity_domain']['account_id']=odd['batch_context']['account_id']
    odd['bounds']=dict(sell_A=dict(minimum='0',maximum='0'),additional_B=dict(minimum='2',maximum='2'))
    add('existing-B3-add2',odd,grid=[['0','2']],grid_points=1,target_B='5')
    large=convert(base,'1000','1000');large['decision_input']['account']['holdings']['A'].update(shares='1000',sellable='1000')
    large['batch_context']['account_id']=_fp(large['decision_input']['account']);large['quantity_domain']['account_id']=large['batch_context']['account_id']
    large['bounds']=dict(sell_A=dict(minimum='0',maximum='1000'),additional_B=dict(minimum='0',maximum='0'));large['max_grid_combinations']='2'
    add('explicit-1000-no-partial',large,grid=[['0','0'],['1000','0']],grid_points=2,raw_points=1001,no_strict_partial_A=True)
    empty=convert(base);empty['bounds']=dict(sell_A=dict(minimum='1',maximum='1'),additional_B=dict(minimum='1',maximum='1'))
    add('empty-grid',empty,grid=[],grid_points=0,grid_empty=True)
    bad=deepcopy(r);bad['max_grid_combinations']='8';add('search-limit',bad,'REFUSED_SEARCH_LIMIT',core_calls=0)
    for name in ('additional-independent','additional-old-trigger','unknown-batch-phase','wait-sale-settlement','non-monotone','common-risk-limit','liquidity-limit','cost-cannot-be-free'):
        add(name,convert(old(name),'1','1'),compare_legacy=True)
    for name in ('future-A-wins','future-B-wins','future-both-fall'):
        f=convert(old(name));f['bounds']=deepcopy(r['bounds']);add(name,f,same_research_as='manual-grid')
    for name in ('missing-domain','zero-unit','unknown-unit','fractional-unit','missing-provenance','future-domain','future-unit','wrong-account','wrong-code','wrong-source','wrong-basis','wrong-adjustment','extra-asset'):
        bad=deepcopy(r);domain=bad['quantity_domain'];asset=domain['assets']['B']
        if name=='missing-domain':del bad['quantity_domain']
        elif name=='zero-unit':asset['unit_shares']='0'
        elif name=='unknown-unit':asset['unit_shares']=None
        elif name=='fractional-unit':asset['unit_shares']='2.5'
        elif name=='missing-provenance':domain['parameter_source']=''
        elif name=='future-domain':domain['available_at']='2026-01-06T16:00:00+08:00'
        elif name=='future-unit':asset['available_at']='2026-01-06T16:00:00+08:00'
        elif name=='wrong-account':domain['account_id']='wrong'
        elif name=='wrong-code':asset['code']='A'
        elif name=='wrong-source':asset['source_id']='foreign'
        elif name=='wrong-basis':asset['basis_id']='foreign'
        elif name=='wrong-adjustment':asset['adjustment_version']='foreign'
        elif name=='extra-asset':domain['assets']['C']=deepcopy(asset)
        add(name,bad,'VALUE_ERROR',core_calls=0)
    protected=[PROJECT/'capital_research'/n for n in ('allocation.py','core.py','continuity.py','execution.py','execution_continuation.py','cash_action.py','cash_action_execution.py','eligibility.py','fact_lineage.py','quantity_replay.py')]
    protected += [PROJECT/'rotation_research/action_ledger.py',prior.parent/'CHANGE_MANIFEST.json']
    save(ROOT/'case-index.json',dict(cases=cases,original_market_samples=0))
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        changing_sources=[dict(current=info(original),archived=info(archive))],protected=[info(p) for p in protected],
        source_originals=list({m['path']:m for m in sources}.values()),quotes_added=0,new_market_rules=0))
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(ROOT.rglob('*')) if p.is_file()]))
    print('Frozen',len(cases),'explicit-domain cases before implementation')

if __name__=='__main__':main()
