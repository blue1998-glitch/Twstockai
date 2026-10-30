"""Save new actuals once; never rewrite frozen inputs or historical evidence."""
from copy import deepcopy
import os
from unittest.mock import patch
from capital_research import quantity_candidates as qc
from .freeze import ROOT,PROJECT,load,save,info

def main():
    stage=os.environ.get('UNIT_FULL_STAGE','actual');summary=[]
    for name in load(ROOT/'case-index.json')['cases']:
        request=load(ROOT/'cases'/name/'input.json');original=deepcopy(request)
        with patch.object(qc,'_evaluate',wraps=qc._evaluate) as evaluate,patch.object(qc.allocation,'full_transfer',side_effect=AssertionError('Legacy endpoint not permitted for 0.4')):
            try:output=dict(status='RETURNED',result=qc.generate(request))
            except ValueError as exc:output=dict(status='VALUE_ERROR',message=str(exc))
        output['core_evaluations']=evaluate.call_count;output['input_unchanged']=request==original
        save(ROOT/stage/name/'actual.json',output)
        result=output.get('result',{}).get('research',{})
        summary.append(dict(case=name,status=result.get('status',output['status']),full_status=result.get('full_proposal_status'),
            selected_target=(result.get('full_search_receipt') or {}).get('selected_target'),input_unchanged=output['input_unchanged']))
    for version in ('0.1','0.2','0.3'):
        save(ROOT/stage/'legacy'/version/'actual.json',qc.generate(load(ROOT/'legacy'/version/'input.json')))
    save(ROOT/stage/'summary.json',dict(cases=summary,market_samples=0,ranking=None,execution='NOT_PERFORMED'))
    save(ROOT/stage/'source-versions.json',dict(files=[info(PROJECT/'capital_research'/n) for n in
        ('quantity_candidates.py','allocation.py','quantity_domain.py','core.py','continuity.py','eligibility.py','fact_lineage.py')]))
    print('Saved',len(summary),'new actuals and three exact legacy controls in',stage)

if __name__=='__main__':main()
