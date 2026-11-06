"""Pin exact existing jobs/executions before directly probing simulate."""
from pathlib import Path
from capital_research.lifecycle import _fp
from capital_research.decimal_context_20261027.prepare import load,save,info

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
CASES=('initial','continuation')


def main():
    reference=ROOT.parent/'decision_context_20261027/input.json';ref=load(reference);p=PROJECT/ref['source']['path']
    assert info(p)==ref['source'];source=load(p);assert _fp(source)==ref['source_id']
    specs=[]
    for index,name in enumerate(CASES):
        frame=source['replay']['rounds'][index]
        specs.append(dict(name=name,round_index=index,job_id=_fp(frame['execution_job']),
            expected_execution_id=_fp(frame['execution']),result_id=frame['execution']['result_id'],
            expected_checkpoint_id=frame['checkpoint']['checkpoint_id']))
    controls=ROOT.parent/'quantity_context_20261027/contexts.json';preset=ROOT.parent/'quantity_context_20261027/test-controls.json'
    save(ROOT/'input.json',dict(schema='capital-execution-context-probe/0.1',synthetic=True,source=info(p),
        source_id=_fp(source),source_reference=info(reference),cases=specs,controls_reference=info(controls),preset_reference=info(preset)))
    save(ROOT/'expected.json',dict(all_complete_outputs_equal_exact_original_execution=True,input_unchanged=True,caller_unchanged=True,
        initial_capital='2230',general_reserve='100',first_cash='1056.660',first_shares=dict(A='80',B='7',C='2'),
        final_cash='1115.640',final_shares=dict(A='90',B='8',C='2'),final_nav='2225.640',final_fill_fees_and_tax='4',
        first_fill_ids=['r1-A-fill-0','r1-B-fill-1'],all_fill_ids=['r1-A-fill-0','r1-B-fill-1','r2-B-fill-2'],
        original_unfilled_remaining=dict(A='30',B='13'),opening_cash_claim='80',opening_share_claim='10',
        cash_and_share_claims_each_received_once=True,source_qualifications_not_promoted=True))
    save(ROOT/'regression-specs.json',[
        dict(name='cost-mismatch',source_case='initial',change='Only ledger_input.terminal_costs.fee_rate=0',error='Decision/execution/terminal cost model mismatch'),
        dict(name='opening-right-drop',source_case='initial',change='Only ledger_input.opening.cash_claims=[]',error='Unequal opening holdings/cash/rights'),
        dict(name='wrong-latest',source_case='continuation',change='Only continuation.previous_decision uses the valid saved first baseline',error='LATEST_PREDECESSOR_REQUIRED')])
    target=ROOT.parent/'execution.py';(ROOT/'before/source').mkdir(parents=True)
    with (ROOT/'before/source/execution.py').open('x') as f:f.write(target.read_text())
    originals=[info(x) for x in (p,reference,controls,preset)]
    for name in ('core.py','continuity.py','allocation.py','quantity_candidates.py','quantity_replay.py','quantity_after_retry.py',
            'conditional_quantity_review.py','conditional_retry.py','eligibility.py','fact_lineage.py','reassessment_history.py',
            'order_review.py','transition_risk.py','close_clock.py','lifecycle.py'):
        originals.append(info(ROOT.parent/name))
    originals.extend(info(x) for x in (PROJECT/'rotation_research/action_ledger.py',PROJECT/'rotation_research/core.py',
        ROOT.parent/'decimal_context_20261027/prepare.py',ROOT.parent/'decimal_context_20261027/reproduce.py'))
    save(ROOT/'intake.json',dict(baseline='cef4d09f08d9d0850adb4c03a9eac651146cded3',source_before=info(target),originals=originals,
        input_expected_saved_before_execution=True,old_suites_or_quantity_replay_producer_run=False,new_prices_or_sources=False))


if __name__=='__main__':main()
