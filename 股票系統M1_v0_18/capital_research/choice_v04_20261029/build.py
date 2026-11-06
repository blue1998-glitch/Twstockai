"""Persist choices and their original sources via the unchanged Journal."""
from copy import deepcopy
import os
from .freeze import ROOT,PROJECT,load,save,info
from capital_research.research_choice_workflow import select_and_save,read_choice
from capital_research.research_choice_source import check_saved

def main():
    stage=os.environ.get('CHOICE_V04_STAGE','actual');rows=[]
    for name in load(ROOT/'case-index.json')['cases']:
        req=load(ROOT/'cases'/name/'input.json');before=deepcopy(req)
        receipt=select_and_save(ROOT/stage/'journal',name,req)
        save(ROOT/stage/name/'receipt.json',receipt)
        if receipt['record'] is None:raise ValueError('Unexpected save failure '+name)
        record=read_choice(ROOT/stage/'journal',name)
        save(ROOT/stage/name/'read.json',record)
        check=check_saved(record['record']['value'],req['saved_result'])
        save(ROOT/stage/name/'source-check.json',check)
        c=record['record']['value']['choice'];rows.append(dict(case=name,status=c['status'],reasons=c['reasons'],
            storage_status=receipt['storage_status'],source_check=check['check_status'],input_unchanged=req==before))
    for name in ('grid-new-trigger','exit-A-cash','unknown-refused'):
        from capital_research.research_choice import choose_saved
        save(ROOT/stage/'legacy'/name/'actual.json',choose_saved(load(ROOT/'legacy'/name/'input.json')))
    save(ROOT/stage/'summary.json',dict(cases=rows,original_market_samples=0,ranking=None,execution='NOT_PERFORMED'))
    save(ROOT/stage/'source-versions.json',dict(files=[info(PROJECT/'capital_research'/n) for n in
        ('research_choice.py','research_choice_source.py','research_quantity_source.py','research_choice_workflow.py','quantity_choice_rules.py','lifecycle.py')]))
    print('Saved',len(rows),'Journal choices/readbacks and source checks in',stage)

if __name__=='__main__':main()
