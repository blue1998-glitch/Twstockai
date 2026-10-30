"""Use the original public APIs; save each exact input before its RUN."""
from copy import deepcopy
from unittest.mock import patch
from .freeze import ROOT, PROJECT, load, save, info


def main():
    from capital_research.cash_action_execution import execute
    from capital_research.execution_continuation import resume_orders, _capture_original
    from capital_research.continuity import make_checkpoint
    from capital_research.core import fingerprint, timestamp
    save(ROOT/'source-versions.json',dict(files=[info(PROJECT/'capital_research'/n) for n in (
        'cash_action.py','cash_action_execution.py','core.py','execution.py','execution_continuation.py','continuity.py')]))
    root=load(ROOT/'root-input.json');path=load(ROOT/'path.json');cut='2026-01-09T16:00:00+08:00'
    with patch('capital_research.quantity_candidates.generate',side_effect=AssertionError('NO_NEW_QUANTITY')), \
         patch('capital_research.quantity_replay.replay_sequence',side_effect=AssertionError('NO_REPLAY_COORDINATOR')):
        prefix_input=load(ROOT/'prefix-action-input.json');before=deepcopy(prefix_input)
        prefix=execute(prefix_input);save(ROOT/'actual/prefix-action-result.json',prefix)
        if prefix['run']['status']!='REPLAYED_EXPLICIT_ACTION':raise ValueError(prefix['run'])
        save(ROOT/'actual/prefix-input-check.json',dict(input_unchanged=prefix_input==before,
            exact_frozen_job=prefix['run']['execution_job']==load(ROOT/'prefix-input.json')))
        cp=prefix['run']['checkpoint']
        whole,trace,_=_capture_original(root)
        save(ROOT/'control/one-shot-execution.json',whole);save(ROOT/'control/one-shot-observation-trace.json',trace)
        whole_cp=make_checkpoint(root['ledger_input'],whole,through_at=root['observed_until'])
        save(ROOT/'control/one-shot-checkpoint.json',whole_cp)
        request=dict(schema='capital-standing-order-resume-input/0.1',synthetic=True,root_job=root,checkpoint=cp,
            expected_checkpoint_id=cp['checkpoint_id'],expected_latest_decision_id=cp['execution_result']['latest_decision_id'],
            path=path,expected_path_id=fingerprint(path),segment_tape=[],observed_until=root['observed_until'],
            resume_at='2026-01-09T16:01:00+08:00')
        rows=[]
        def run(name,r,expected):
            save(ROOT/'cases'/name/'input.json',r);save(ROOT/'cases'/name/'expected.json',expected)
            before=deepcopy(r);a=resume_orders(r);save(ROOT/'actual'/name/'result.json',a)
            status_match=a['status']==expected['status']
            if 'reason' in expected:status_match=status_match and expected['reason'] in a.get('refusal_reasons',[])
            row=dict(name=name,status=a['status'],reasons=a.get('refusal_reasons',[]),expected_status_reason_match=status_match,input_unchanged=r==before,
                saved_readback_equal=load(ROOT/'actual'/name/'result.json')==a,tail_observations_processed=a['tail_observations_processed'])
            rows.append(row);print(row)
            return a
        main=run('direct',request,dict(status='CONTINUED_ORIGINAL_ORDERS',full_execution_equal=True,segment_fills=0))
        if main['execution'] is not None:
            save(ROOT/'actual/direct/comparison.json',dict(execution_equal=main['execution']==whole,checkpoint_equal=main['checkpoint']==whole_cp,
                every_observation_equal=main['prefix_observation_trace']+main['observation_trace']==trace,
                every_daily_row_equal=main['execution']['ledger']['daily']==whole['ledger']['daily']))
        mid_request=deepcopy(request);mid_request['observed_until']='2026-01-10T16:00:00+08:00'
        middle=run('to-Jan10',mid_request,dict(status='CONTINUED_ORIGINAL_ORDERS',payable='141.140',reserved='261.65039',segment_fills=0))
        if middle['checkpoint'] is None:raise ValueError(middle)
        tail=deepcopy(request);tail.update(checkpoint=middle['checkpoint'],expected_checkpoint_id=middle['checkpoint']['checkpoint_id'],
            expected_latest_decision_id=middle['checkpoint']['execution_result']['latest_decision_id'],resume_at='2026-01-10T16:01:00+08:00')
        end=run('Jan10-to-Jan12',tail,dict(status='CONTINUED_ORIGINAL_ORDERS',full_execution_equal=True,segment_fills=0))
        if end['execution'] is not None:
            save(ROOT/'actual/Jan10-to-Jan12/comparison.json',dict(execution_equal=end['execution']==whole,checkpoint_equal=end['checkpoint']==whole_cp,
                every_daily_row_equal=end['execution']['ledger']['daily']==whole['ledger']['daily']))
        negatives=load(ROOT/'negative-specifications.json')
        for name,reason in negatives.items():
            x=deepcopy(request)
            if name=='wrong_latest':
                x['expected_latest_decision_id']=root['continuation']['checkpoint']['execution_result']['latest_decision_id']
            elif name=='dropped_parent':x['root_job'].pop('continuation')
            elif name=='different_capacity_path':
                original=load(PROJECT/'capital_research/settled_resume_action_20261029/actual/independent-B20/result.json')['run']['execution_job']
                x['root_job']=deepcopy(original);x['path']['observations']=deepcopy(original['tape'])
                for s in x['path']['session_coverage']:s['observation_ids']=[fingerprint(o) for o in original['tape'] if o['at'][:10]==s['date']]
                x['expected_path_id']=fingerprint(x['path'])
            elif name=='duplicate_fill':
                fills=x['checkpoint']['execution_result']['fills'];fills.append(deepcopy(fills[-1]))
            elif name=='missing_empty_session':
                x['path']['session_coverage']=[s for s in x['path']['session_coverage'] if s['date']!='2026-01-12']
                x['expected_path_id']=fingerprint(x['path'])
            run(name,x,dict(status='REFUSED',reason=reason,tail_processing_started=False,tail_observations=0))
        save(ROOT/'summary.json',dict(cases=rows,all_expected_status_reason_match=all(r['expected_status_reason_match'] for r in rows),
            all_inputs_unchanged=all(r['input_unchanged'] for r in rows),all_saved_readbacks_equal=all(r['saved_readback_equal'] for r in rows),
            original_saved_resume_runs=0,new_partial_action_runs=1,one_shot_control_runs=1,new_quotes=0,new_calendar_rows=0,
            product_module_changes=0,old_suites_run=0,market_samples=0))


if __name__=='__main__':main()
