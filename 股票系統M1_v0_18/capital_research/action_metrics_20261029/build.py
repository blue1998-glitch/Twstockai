"""Read frozen JSON only; save evaluation actuals, never regenerate accounts."""
import argparse
from copy import deepcopy
from .freeze import ROOT,PROJECT,load,save,info


def main(stage):
    from capital_research.action_account_metrics import evaluate_saved
    dest=ROOT/stage
    save(dest/'source-versions.json',dict(files=[info(PROJECT/'capital_research'/n) for n in
        ('account_metrics.py','action_account_metrics.py','account_metrics_read.py','lifecycle.py','fact_lineage.py','reassessment_history.py')]))
    rows=[]
    for name in load(ROOT/'case-index.json')['cases']:
        request=load(ROOT/'cases'/name/'input.json');old=deepcopy(request)
        actual=evaluate_saved(request);save(dest/name/'actual.json',actual)
        expected=load(ROOT/'cases'/name/'expected.json')
        row=dict(name=name,status=actual['status'],reasons=actual['reasons'],expected_status=expected['status'],
            matched=actual['status']==expected['status'],input_unchanged=request==old,readback_equal=load(dest/name/'actual.json')==actual)
        rows.append(row);print(name,row['status'],row['matched'],row['reasons'],flush=True)
    save(dest/'summary.json',dict(cases=rows,all_statuses_matched=all(r['matched'] for r in rows),
        all_inputs_unchanged=all(r['input_unchanged'] for r in rows),all_readbacks_equal=all(r['readback_equal'] for r in rows),
        accounting_replay_calls=0,new_market_data=0))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',required=True);main(p.parse_args().stage)
