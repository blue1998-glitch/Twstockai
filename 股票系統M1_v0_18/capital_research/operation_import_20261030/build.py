"""Save import/READ evidence once; no numerical RUN or choice creation."""
from copy import deepcopy
import os
from unittest.mock import patch
from .freeze import ROOT,PROJECT,REPO,load,save,info
from capital_research import research_operation as op

def main():
    stage=os.environ.get('OPERATION_IMPORT_STAGE','actual');rows=[]
    for name in load(ROOT/'case-index.json')['cases']:
        request=load(ROOT/'cases'/name/'input.json');before=deepcopy(request)
        with (patch.object(op,'_generation',side_effect=AssertionError('No generation')),
              patch.object(op,'_selection',side_effect=AssertionError('No selection')),
              patch.object(op,'_source_check',wraps=op._source_check) as check):
            result=op.import_operation(ROOT/stage/'runs'/name,'import-'+name,request)
            calls=check.call_count
        save(ROOT/stage/name/'import.json',result)
        with patch.object(op,'_source_check',side_effect=AssertionError('READ must not recompute verdict')):
            read=op.read_operation(ROOT/stage/'runs'/name,'import-'+name)
        save(ROOT/stage/name/'read.json',read)
        rows.append(dict(case=name,workflow_status=result['workflow_status'],reasons=result['reasons'],
            source_check_calls=calls,input_unchanged=request==before,read_status=read['workflow_status']))
    for c in load(ROOT/'case-index.json')['legacy']:
        save(ROOT/stage/'legacy'/c['name']/'read.json',op.read_operation(REPO/c['store'],c['identity']))
    save(ROOT/stage/'summary.json',dict(cases=rows,numeric_producer_runs=0,selection_runs=0,market_samples=0,ranking=None))
    save(ROOT/stage/'source-versions.json',dict(files=[info(PROJECT/'capital_research'/n) for n in
        ('research_operation.py','research_operation_cli.py','research_choice.py','research_choice_source.py','research_quantity_source.py','lifecycle.py')]))
    print('Saved',len(rows),'import/READ cases; no generation or selection')

if __name__=='__main__':main()
