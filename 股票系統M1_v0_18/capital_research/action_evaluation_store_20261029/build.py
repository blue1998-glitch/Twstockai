"""Import frozen original evaluations and read them back, never calculate them."""
from copy import deepcopy
from .freeze import ROOT,PROJECT,load,save,info

def main():
    from capital_research.action_evaluation_store import import_evaluation,read_evaluation
    save(ROOT/'actual/source-versions.json',dict(files=[info(PROJECT/'capital_research'/n) for n in
        ('action_evaluation_store.py','action_evaluation_store_cli.py','saved_action_source.py','action_account_metrics.py','research_operation.py')]))
    rows=[];store=ROOT/'actual/records'
    for name in load(ROOT/'case-index.json')['cases']:
        request=load(ROOT/'cases'/name/'input.json');old=deepcopy(request);expected=load(ROOT/'cases'/name/'expected.json')
        receipt=import_evaluation(store,name,request);save(ROOT/'actual'/name/'import.json',receipt)
        read=read_evaluation(store,name);save(ROOT/'actual'/name/'read.json',read)
        ok=receipt['storage_status']==expected['storage_status']
        if expected.get('evaluation_status'):ok=ok and receipt['evaluation_status']==expected['evaluation_status']
        if expected['storage_status']=='SAVED_AND_READ_BACK':ok=ok and read['storage_status']=='READ_ONLY' and read['record']==receipt['record']
        else:ok=ok and read['storage_status']=='NOT_FOUND'
        row=dict(name=name,storage_status=receipt['storage_status'],evaluation_status=receipt['evaluation_status'],read_status=read['storage_status'],
            reasons=receipt['reasons'],matched=ok,input_unchanged=request==old)
        rows.append(row);print(row,flush=True)
    save(ROOT/'actual/summary.json',dict(cases=rows,all_expected_matched=all(r['matched'] for r in rows),all_inputs_unchanged=all(r['input_unchanged'] for r in rows),
        new_evaluations=0,accounting_replay_calls=0))

if __name__=='__main__':main()
