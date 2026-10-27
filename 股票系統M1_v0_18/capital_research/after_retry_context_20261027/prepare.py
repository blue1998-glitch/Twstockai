"""Pin existing complete inputs/oracles before probing the public bridge."""
from pathlib import Path
from capital_research.lifecycle import _fp
from capital_research.decimal_context_20261027.prepare import load,save,info
from capital_research.quantity_after_retry_20261027.fixtures import materialize

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
REPO=PROJECT.parent
PREVIOUS=ROOT.parent/'quantity_after_retry_20261027'
PRIMARY=('new-independent-trigger','old-trigger','unknown-qualification')
REGRESSIONS=('wrong-latest','tampered-token-history','search-limit')


def main():
    originals={};cases=[]
    def pin(p):
        meta=info(p);originals[meta['path']]=meta;return meta
    for name in PRIMARY+REGRESSIONS:
        p=PREVIOUS/'cases'/name/'input.json';spec=load(p);request=materialize(spec)
        assert _fp(request)==spec['materialized_input_id']
        expected=PREVIOUS/'cases'/name/'expected.json';actual=PREVIOUS/'after-final'/name/'actual.json'
        for key in ('saved_source','checkpoint_source'):pin(REPO/spec[key]['path'])
        cases.append(dict(name=name,role='primary' if name in PRIMARY else 'necessary_regression',
            input_spec=pin(p),expected_spec=pin(expected),original_actual=pin(actual),
            materialized_input_id=_fp(request),expected_result_id=_fp(load(actual))))
    controls=pin(ROOT.parent/'quantity_context_20261027/contexts.json')
    preset=pin(ROOT.parent/'quantity_context_20261027/test-controls.json')
    save(ROOT/'input.json',dict(schema='capital-after-retry-context-probe/0.1',synthetic=True,
        cases=cases,controls_reference=controls,preset_reference=preset))
    save(ROOT/'expected.json',dict(all_complete_outputs_equal_pinned_original=True,
        original_schema='capital-quantity-after-retry/0.1',input_unchanged=True,caller_context_unchanged=True,
        origin_initial_capital='1430',current_account_value='1425.100',settled_cash='275.100',general_reserved_cash='100',
        holdings=dict(A='60',B='25',C='2'),historical_tokens=12,received_attempt_outcomes=['REJECTED','ACCEPTED'],
        buys=dict(new_independent_trigger='FEASIBLE_EXISTS',old_trigger='NO_NEW_INDEPENDENT_TRIGGER',
            unknown_qualification='NEW_CAPITAL_NOT_QUALIFIED:B'),new_order_or_execution='NOT_PERFORMED'))
    target=ROOT.parent/'quantity_after_retry.py';(ROOT/'before/source').mkdir(parents=True)
    with (ROOT/'before/source/quantity_after_retry.py').open('x') as f:f.write(target.read_text())
    for name in ('core.py','continuity.py','execution.py','quantity_candidates.py','quantity_replay.py',
            'allocation.py','conditional_retry.py','conditional_quantity_review.py','order_review.py',
            'fact_lineage.py','reassessment_history.py','eligibility.py','transition_risk.py','lifecycle.py'):
        pin(ROOT.parent/name)
    for p in (PROJECT/'rotation_research/action_ledger.py',PREVIOUS/'fixtures.py',PREVIOUS/'verify.py',
            ROOT.parent/'decimal_context_20261027/prepare.py',ROOT.parent/'decimal_context_20261027/reproduce.py'):
        pin(p)
    save(ROOT/'intake.json',dict(baseline='3b472ae8575f4f4f6c5acaf504f29d0ded078bdd',source_before=info(target),
        originals=list(originals.values()),input_expected_versions_saved_before_execution=True,
        new_prices_or_sources=False,old_suites_replayed=False,original_account_reused=True))


if __name__=='__main__':main()
