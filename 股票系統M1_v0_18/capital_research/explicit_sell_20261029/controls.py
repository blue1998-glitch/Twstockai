"""Create-only receipt, future-prefix, Decimal, legacy and continuation controls."""
from copy import deepcopy
import decimal
from unittest.mock import patch
from .freeze import ROOT, PROJECT, load, save, info


def main():
    from capital_research.cash_action import evaluate
    from capital_research.cash_action_execution import execute
    from capital_research.execution_continuation import resume_orders, _capture_original
    from capital_research.continuity import make_checkpoint
    from capital_research.core import fingerprint
    from capital_research.decimal_context_20261027.reproduce import snapshot
    save(ROOT/'controls/specification.json',dict(partial=dict(final_cash='816.460',final_B='13',final_C='4',remaining='13',
        status='EXPIRED_UNFILLED',tail_fills=0,full_execution_equal=True,every_observation_equal=True),
        future=dict(research_equal=True,integrity_different=True),
        review=dict(qualified_for_new_capital=False,sell_status='CURRENTLY_FEASIBLE'),
        contexts=dict(full_checked_and_execution_equal=True,caller_and_DefaultContext_unchanged=True,input_unchanged=True),
        legacy=dict(saved_hold_buy_and_rejection_equal=True)))
    save(ROOT/'controls/source-versions.json',dict(files=[info(PROJECT/'capital_research'/n) for n in ('cash_action.py','cash_action_execution.py','execution_continuation.py')]))
    partial=load(ROOT/'initial/partial-exit-B20/result.json')['run'];root=deepcopy(partial['execution_job']);root['observed_until']='2026-01-12T16:00:00+08:00'
    save(ROOT/'controls/partial/root-input.json',root)
    path=dict(schema='capital-synthetic-order-path/0.1',version='frozen-synthetic-path/0.1',
        qualification='EXPLICIT_SYNTHETIC_COMPLETE_PATH_NOT_MARKET_PROOF',source_ids=['fixture'],origin_ledger_input_id=fingerprint(root['ledger_input']),
        start_at=root['decision_input']['data_cutoff'],through_at=root['observed_until'],observations=deepcopy(root['tape']),session_coverage=[])
    for r in root['ledger_input']['calendar']:
        if r['trading'] and path['start_at'][:10]<r['date']<=path['through_at'][:10]:
            path['session_coverage'].append(dict(date=r['date'],source_ids=['fixture'],qualification='EXPLICIT_SYNTHETIC_COMPLETE_EXECUTION_OPPORTUNITIES',
                observation_ids=[fingerprint(o) for o in root['tape'] if o['at'][:10]==r['date']],no_other_execution_opportunities=True))
    cp=partial['checkpoint'];r=dict(schema='capital-standing-order-resume-input/0.1',synthetic=True,root_job=root,checkpoint=cp,
        expected_checkpoint_id=cp['checkpoint_id'],expected_latest_decision_id=cp['execution_result']['latest_decision_id'],path=path,
        expected_path_id=fingerprint(path),segment_tape=[],observed_until=root['observed_until'],resume_at='2026-01-09T16:01:00+08:00')
    save(ROOT/'controls/partial/input.json',r)
    a=resume_orders(r);save(ROOT/'controls/partial/actual.json',a)
    whole,trace,_=_capture_original(root);save(ROOT/'controls/partial/one-shot-execution.json',whole)
    save(ROOT/'controls/partial/comparison.json',dict(execution_equal=a['execution']==whole,
        checkpoint_equal=a['checkpoint']==make_checkpoint(root['ledger_input'],whole,through_at=root['observed_until']),
        every_observation_equal=a['prefix_observation_trace']+a['observation_trace']==trace,
        every_daily_row_equal=a['execution']['ledger']['daily']==whole['ledger']['daily']))
    original=load(ROOT/'cases/exit-B7/action-input.json');future=deepcopy(original)
    e=deepcopy(future['decision_template']['assets']['B']['evidence'][0]);e.update(id='future-only',event_id='future-event',formation_id='future-formation',volume_bar_id='future-bar',
        occurred_at='2026-01-09T09:00:00+08:00',available_at='2026-01-09T09:00:00+08:00',value='FUTURE_NOT_AVAILABLE_AT_REVIEW')
    e['validity'].update(valid_from=e['occurred_at'],available_at=e['available_at'])
    future['decision_template']['assets']['B']['evidence'].append(e)
    save(ROOT/'controls/future/input.json',future);f=evaluate(future);save(ROOT/'controls/future/actual.json',f)
    normal=load(ROOT/'initial/exit-B7/checked-action.json')
    save(ROOT/'controls/future/comparison.json',dict(research_equal=f['research']==normal['research'],integrity_different=f['source_integrity_metadata']!=normal['source_integrity_metadata']))
    review=deepcopy(original);review['decision_template']['assets']['B']['capital_eligibility']['status']='NOT_QUALIFIED'
    save(ROOT/'controls/not-new-capital-qualified/input.json',review);save(ROOT/'controls/not-new-capital-qualified/actual.json',evaluate(review))
    context_specs=[dict(prec=3,rounding='ROUND_UP',Emin=-2,Emax=2,capitals=0,clamp=1,traps=['Inexact','Overflow','Clamped'],flags=[]),
        dict(prec=7,rounding='ROUND_DOWN',Emin=-9,Emax=9,capitals=1,clamp=0,traps=['Rounded'],flags=['Inexact'])]
    save(ROOT/'controls/context/specifications.json',context_specs)
    from capital_research.decimal_context_20261027.reproduce import context
    default=snapshot(decimal.DefaultContext);request=load(ROOT/'initial/exit-B7/execution-input.json');before=deepcopy(request);rows=[]
    for i,spec in enumerate(context_specs):
        with decimal.localcontext(context(spec)) as caller:
            initial=snapshot(caller)
            with patch('builtins.open',side_effect=AssertionError('NO_IO_IN_NUMERIC_API')),patch('socket.socket',side_effect=AssertionError('NO_NETWORK')), \
                 patch('capital_research.quantity_candidates.generate',side_effect=AssertionError('NO_QUANTITY')):
                checked=evaluate(original);executed=execute(request)
            unchanged=snapshot(caller)==initial
        row=dict(context=i,checked_equal=checked==normal,execution_equal=executed==load(ROOT/'initial/exit-B7/result.json'),
                 caller_unchanged=unchanged,input_unchanged=request==before,default_unchanged=snapshot(decimal.DefaultContext)==default)
        rows.append(row)
    save(ROOT/'controls/context/actual.json',rows)
    legacy=[]
    prior=PROJECT/'capital_research/settled_resume_action_20261029'
    for name in ('hold','independent-B20','old-trigger'):
        inp=prior/'actual'/name/'execution-input.json';expected=prior/'actual'/name/'result.json'
        save(ROOT/'controls/legacy'/name/'binding.json',dict(input=info(inp),expected=info(expected)))
        a=execute(load(inp));save(ROOT/'controls/legacy'/name/'actual.json',a)
        legacy.append(dict(name=name,complete_saved_result_equal=a==load(expected)))
    save(ROOT/'controls/legacy/summary.json',legacy)
    print('Created partial sell continuation, future, entry-review separation, two contexts, and three exact old0.1 controls')


if __name__=='__main__':main()
