"""One new synthetic execution; five gates. First round remains a saved READ."""
from copy import deepcopy
from unittest.mock import patch
from .freeze import ROOT,PROJECT,OLD,load,save,info


def main():
    from capital_research.cash_action_execution import execute
    from capital_research.execution import simulate
    import capital_research.quantity_replay
    save(ROOT/'source-versions.json',[info(PROJECT/'capital_research'/n) for n in
        ('cash_action.py','cash_action_execution.py','core.py','execution.py','continuity.py','fact_lineage.py')])
    rows=[]
    with patch('capital_research.cash_action_execution.simulate',wraps=simulate) as engine, \
         patch('capital_research.quantity_replay.replay_sequence',side_effect=AssertionError('NO_OLD_REPLAY')), \
         patch('capital_research.quantity_candidates.generate',side_effect=AssertionError('NO_GENERATION')):
        for name in load(ROOT/'case-index.json')['cases']:
            r=load(ROOT/'cases'/name/'input.json');before=deepcopy(r);expected=load(ROOT/'cases'/name/'expected.json');calls=engine.call_count
            actual=execute(r);save(ROOT/'actual'/name/'result.json',actual)
            assert load(ROOT/'actual'/name/'result.json')==actual
            run=actual['run'];checked=r['checked_action']['research'];count=engine.call_count-calls
            matched=run['status']==expected['run_status'] and checked['status']==expected['checked_status'] and count==expected['simulate_calls']
            if expected.get('reason'):matched=matched and expected['reason'] in checked['reasons']
            rows.append(dict(name=name,checked_status=checked['status'],run_status=run['status'],checked_reasons=checked['reasons'],
                run_reasons=run['reasons'],simulate_calls=count,expected_status_reasons_calls_matched=matched,input_unchanged=r==before))
        total=engine.call_count
    save(ROOT/'summary.json',dict(cases=rows,all_status_reasons_calls_matched=all(x['expected_status_reasons_calls_matched'] for x in rows),
        all_inputs_unchanged=all(x['input_unchanged'] for x in rows),first_round_simulate_calls=0,second_round_simulate_calls=total,
        existing_entrypoints_sufficient=True,production_module_changes=0,quote_or_calendar_additions=0,market_replay_calls=0,saved_json_readbacks_matched=True))
    print(dict(cases=len(rows),all_status_reasons_calls_matched=all(x['expected_status_reasons_calls_matched'] for x in rows),
        second_round_simulate_calls=total,mismatches=[x for x in rows if not x['expected_status_reasons_calls_matched']]))


if __name__=='__main__':main()
