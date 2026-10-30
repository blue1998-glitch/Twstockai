"""Execute only this milestone's frozen explicit-action decisions, no replay."""
import json
import argparse
from copy import deepcopy
from .freeze import ROOT,PROJECT,load,save,info


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['after-final'],required=True);args=parser.parse_args()
    stage=ROOT/args.stage
    from capital_research.cash_action import evaluate
    from unittest.mock import patch
    versions=[info(PROJECT/'capital_research'/n) for n in
        ('cash_action.py','core.py','continuity.py','quantity_candidates.py','eligibility.py','fact_lineage.py','reassessment_history.py')]
    save(stage/'source-versions.json',versions)
    rows=[]
    with patch('capital_research.execution.simulate',side_effect=AssertionError('NO_EXECUTION')), \
         patch('capital_research.quantity_candidates.generate',side_effect=AssertionError('NO_ENUMERATION')):
        for name in load(ROOT/'case-index.json')['cases']:
            r=load(ROOT/'cases'/name/'input.json');before=deepcopy(r);expected=load(ROOT/'cases'/name/'expected.json')
            actual=evaluate(r);save(stage/'actual'/name/'result.json',actual)
            out=actual['research'];matched=out['status']==expected['status'] and (expected['reason'] is None or expected['reason'] in out['reasons'])
            rows.append(dict(name=name,status=out['status'],reasons=out['reasons'],expected_matched=matched,input_unchanged=r==before,
                candidate_ids=out['research_recommendation']['candidate_ids']))
    save(stage/'summary.json',dict(cases=rows,all_expected=all(r['expected_matched'] and r['input_unchanged'] for r in rows),
        market_replay_calls=0,action_execution_calls=0,quantity_generation_calls=0))
    print(json.dumps(dict(cases=len(rows),all_expected=all(r['expected_matched'] for r in rows),mismatches=[r for r in rows if not r['expected_matched']]),ensure_ascii=False))


if __name__=='__main__':main()
