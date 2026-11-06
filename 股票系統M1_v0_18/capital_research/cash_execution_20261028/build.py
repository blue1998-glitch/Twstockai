"""Only new frozen cases, exclusive writes and exact JSON readback."""
from copy import deepcopy
from .freeze import ROOT,PROJECT,load,save,info


def main():
    from capital_research.cash_action_execution import execute
    save(ROOT/'source-versions.json',[info(PROJECT/'capital_research'/n) for n in
        ('cash_action_execution.py','cash_action.py','core.py','execution.py','continuity.py','fact_lineage.py','transition_risk.py')])
    rows=[]
    for name in load(ROOT/'case-index.json')['cases']:
        r=load(ROOT/'cases'/name/'input.json');before=deepcopy(r);expected=load(ROOT/'cases'/name/'expected.json')
        actual=execute(r);save(ROOT/'actual'/name/'result.json',actual)
        assert load(ROOT/'actual'/name/'result.json')==actual,'SAVED_JSON_READBACK_CONFLICT'
        run=actual['run'];matched=run['status']==expected['status'] and (expected['reason'] is None or expected['reason'] in run['reasons'])
        rows.append(dict(name=name,status=run['status'],reasons=run['reasons'],execution_calls=run['execution_calls'],
            matched_status_and_reason=matched,input_unchanged=r==before))
    save(ROOT/'summary.json',dict(cases=rows,all_status_reasons_matched=all(r['matched_status_and_reason'] for r in rows),
        all_inputs_unchanged=all(r['input_unchanged'] for r in rows),saved_json_readbacks_matched=True,market_replay_calls=0))
    print(dict(cases=len(rows),all_status_reasons_matched=all(r['matched_status_and_reason'] for r in rows),mismatches=[r for r in rows if not r['matched_status_and_reason']]))


if __name__=='__main__':main()
