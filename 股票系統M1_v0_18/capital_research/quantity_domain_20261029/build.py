"""Generate only new frozen synthetic candidates; never call execution."""
from copy import deepcopy
from unittest.mock import patch
from .freeze import ROOT,PROJECT,load,save,info


def main(stage='actual'):
    dest=ROOT/stage
    import capital_research.quantity_candidates as qc
    save(dest/'source-versions.json',dict(files=[info(PROJECT/'capital_research'/n) for n in
        ('quantity_candidates.py','quantity_domain.py','allocation.py','core.py')]))
    rows=[]
    for name in load(ROOT/'case-index.json')['cases']:
        request=load(ROOT/'cases'/name/'input.json');before=deepcopy(request);expected=load(ROOT/'cases'/name/'expected.json')
        with patch.object(qc,'decide',wraps=qc.decide) as decision,patch.object(qc,'resume_decision',wraps=qc.resume_decision) as resume, \
             patch.object(qc.allocation,'decide',wraps=qc.allocation.decide) as full:
            try:a=qc.generate(request);status=a['research']['status']
            except ValueError as e:a=dict(research=None,error_type=type(e).__name__,error=str(e));status='VALUE_ERROR'
            calls=decision.call_count+resume.call_count+full.call_count
        save(dest/name/'actual.json',a)
        same_legacy=None
        if expected.get('compare_legacy'):
            old=deepcopy(request);old['schema']=qc.INPUT_V2;del old['quantity_domain'];legacy=qc.generate(old)
            save(dest/name/'legacy-input.json',old);save(dest/name/'legacy-actual.json',legacy)
            same_legacy=normalize(a)==legacy['research']
        row=dict(name=name,status=status,expected_status=expected['status'],matched=status==expected['status'],decision_entry_calls=calls,
            input_unchanged=request==before,legacy_research_equal=same_legacy,readback_equal=load(dest/name/'actual.json')==a)
        rows.append(row);print(row,flush=True)
    save(dest/'summary.json',dict(cases=rows,all_statuses_matched=all(r['matched'] for r in rows),
        all_inputs_unchanged=all(r['input_unchanged'] for r in rows),all_readbacks_equal=all(r['readback_equal'] for r in rows),
        old_suites=0,market_replays=0,order_generation=0))


def normalize(result):
    r=deepcopy(result['research']);r['schema']='capital-quantity-candidates/0.2'
    for k in ('quantity_domain','quantity_domain_id','domain_axes','raw_integer_grid_points','quantity_domain_diagnostics','domain_reasons','full_proposal_status','enumeration_scope'):r.pop(k)
    for c in r['candidates']:c.pop('unit_gate_reasons',None);c.pop('in_explicit_grid',None)
    return r

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--stage',default='actual');main(p.parse_args().stage)
