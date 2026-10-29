"""Save actuals only after the frozen sell inputs and independent oracles."""
import argparse
from copy import deepcopy
from unittest.mock import patch
from .freeze import ROOT, PROJECT, load, save, info


def main(stage):
    from capital_research.cash_action import evaluate
    from capital_research.cash_action_execution import execute
    from capital_research.execution import simulate
    from capital_research.core import fingerprint
    out=ROOT/stage
    save(out/'source-versions.json',dict(files=[info(PROJECT/'capital_research'/n) for n in
        ('cash_action.py','cash_action_execution.py','core.py','execution.py','continuity.py','execution_continuation.py')]))
    rows=[]
    with patch('capital_research.cash_action_execution.simulate',wraps=simulate) as engine, \
         patch('capital_research.quantity_candidates.generate',side_effect=AssertionError('NO_QUANTITY_PRODUCER')), \
         patch('capital_research.quantity_replay.replay_sequence',side_effect=AssertionError('NO_REPLAY_COORDINATOR')):
        for name in load(ROOT/'case-index.json')['cases']:
            action=load(ROOT/'cases'/name/'action-input.json');before=deepcopy(action);calls=engine.call_count
            checked=evaluate(action);save(out/name/'checked-action.json',checked)
            submitted=deepcopy(checked);version='0.1' if action['schema']=='capital-cash-action-input/0.1' else '0.2'
            edit_path=ROOT/'cases'/name/'execution-edit.json'
            if edit_path.exists():
                edit=load(edit_path)
                if edit['kind']=='TAMPER_CHECKED_REHASH':submitted['research']['intent']['plan']['targets']['B']='1'
                elif edit['kind']=='EXECUTE_AS_V01':version='0.1'
            request=dict(schema='capital-cash-action-execution-input/'+version,synthetic=True,
                action_input=action,checked_action=submitted,expected_checked_action_id=fingerprint(submitted),
                execution_spec=load(ROOT/'cases'/name/'execution-spec.json'))
            save(out/name/'execution-input.json',request);saved=deepcopy(request)
            result=execute(request);save(out/name/'result.json',result)
            e=load(ROOT/'cases'/name/'expected.json');run=result['run'];gate=checked['research']
            count=engine.call_count-calls
            matched=gate['status']==e['checked_status'] and run['status']==e['run_status'] and count==e['simulate_calls']
            if e.get('reason'):matched=matched and e['reason'] in gate['reasons']
            if e.get('run_reason'):matched=matched and e['run_reason'] in run['reasons']
            row=dict(name=name,checked_status=gate['status'],checked_reasons=gate['reasons'],run_status=run['status'],run_reasons=run['reasons'],
                simulate_calls=count,expected_status_reason_calls_matched=matched,action_unchanged=action==before,
                execution_input_unchanged=request==saved,saved_readback_equal=load(out/name/'result.json')==result)
            rows.append(row);print(row)
    save(out/'summary.json',dict(cases=rows,all_expected_status_reason_calls_matched=all(r['expected_status_reason_calls_matched'] for r in rows),
        all_inputs_unchanged=all(r['action_unchanged'] and r['execution_input_unchanged'] for r in rows),
        all_saved_readbacks_equal=all(r['saved_readback_equal'] for r in rows),new_action_simulate_calls=engine.call_count,
        old_suite_runs=0,market_samples=0))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',required=True);main(p.parse_args().stage)
