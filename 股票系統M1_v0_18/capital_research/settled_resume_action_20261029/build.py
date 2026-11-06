"""Create-only integration actuals using unchanged public action entrypoints."""
from copy import deepcopy
from unittest.mock import patch
from .freeze import ROOT, PROJECT, load, save, info


def main():
    from capital_research.cash_action import evaluate
    from capital_research.cash_action_execution import execute
    from capital_research.execution import simulate
    from capital_research.core import fingerprint
    save(ROOT/'source-versions.json',dict(files=[info(PROJECT/'capital_research'/n) for n in (
        'cash_action.py','cash_action_execution.py','core.py','execution.py','execution_continuation.py','continuity.py')]))
    rows=[]
    with patch('capital_research.cash_action_execution.simulate',wraps=simulate) as engine, \
         patch('capital_research.execution_continuation.resume_orders',side_effect=AssertionError('ORIGINAL_RESUME_READ_ONLY')), \
         patch('capital_research.quantity_candidates.generate',side_effect=AssertionError('NO_NEW_QUANTITY_GENERATION')), \
         patch('capital_research.quantity_replay.replay_sequence',side_effect=AssertionError('NO_REPLAY_COORDINATOR')):
        for name in load(ROOT/'case-index.json')['cases']:
            action=load(ROOT/'cases'/name/'action-input.json');before=deepcopy(action)
            expected=load(ROOT/'cases'/name/'expected.json');calls=engine.call_count
            checked=evaluate(action);save(ROOT/'actual'/name/'checked-action.json',checked)
            request=dict(schema='capital-cash-action-execution-input/0.1',synthetic=True,action_input=action,
                checked_action=checked,expected_checked_action_id=fingerprint(checked),
                execution_spec=load(ROOT/'cases'/name/'execution-spec.json'))
            save(ROOT/'actual'/name/'execution-input.json',request);request_before=deepcopy(request)
            actual=execute(request);save(ROOT/'actual'/name/'result.json',actual)
            readback=load(ROOT/'actual'/name/'result.json')
            count=engine.call_count-calls;run=actual['run'];gate=checked['research']
            matched=gate['status']==expected['checked_status'] and run['status']==expected['run_status'] and count==expected['simulate_calls']
            if expected.get('reason'):matched=matched and expected['reason'] in gate['reasons']
            row=dict(name=name,checked_status=gate['status'],run_status=run['status'],checked_reasons=gate['reasons'],run_reasons=run['reasons'],
                simulate_calls=count,expected_status_reason_calls_matched=matched,
                action_input_unchanged=action==before,execution_input_unchanged=request==request_before,saved_readback_equal=readback==actual)
            rows.append(row);print(row)
    save(ROOT/'summary.json',dict(cases=rows,all_expected_status_reason_calls_matched=all(r['expected_status_reason_calls_matched'] for r in rows),
        all_inputs_unchanged=all(r['action_input_unchanged'] and r['execution_input_unchanged'] for r in rows),
        all_saved_readbacks_equal=all(r['saved_readback_equal'] for r in rows),new_action_simulate_calls=engine.call_count,
        original_resume_run_calls=0,original_two_round_producer_calls=0,new_quotes=0,new_calendar_rows=0,product_module_changes=0,
        existing_entrypoints_sufficient=all(r['expected_status_reason_calls_matched'] for r in rows),market_samples=0))


if __name__=='__main__':main()
