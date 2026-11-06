"""Pin original input/generation pointers; reuse controls without new prices."""
from pathlib import Path
from capital_research.lifecycle import _fp
from capital_research.decimal_context_20261027.prepare import load,save,info

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
PREVIOUS=ROOT.parent/'quantity_context_20261027'


def main():
    specs=[];originals=[]
    for name,record,number in [('initial',PREVIOUS/'before/normal/actual.json',0),
                             ('old-trigger',PREVIOUS/'test-evidence/old-trigger/normal/actual.json',1)]:
        meta=load(record)['actual'];path=PREVIOUS/meta['path'];wrapper=load(path)
        assert _fp(wrapper)==meta['id'];frame=wrapper['replay']['rounds'][number];q=frame['quantity_request'];g=frame['generation']
        specs.append(dict(name=name,source=info(path),source_record=info(record),source_id=meta['id'],round_index=number,
            request_id=_fp(q),expected_generation_id=_fp(g),selected_candidate_id=frame['selected_candidate']['id']))
        originals.extend([info(path),info(record)])
    controls=info(PREVIOUS/'contexts.json');preset=info(PREVIOUS/'test-controls.json')
    save(ROOT/'input.json',dict(schema='capital-candidate-context-probe/0.1',synthetic=True,cases=specs,
        controls_reference=controls,preset_reference=preset))
    save(ROOT/'expected.json',dict(all_complete_outputs_equal_original_generation=True,input_unchanged=True,caller_context_unchanged=True,
        original_schema='capital-quantity-candidates/0.2',original_initial_capital='2230',selected_id=None,ranking=None,
        initial_targets=[dict(A='100',B='0',C='2'),dict(A='50',B='20',C='2'),dict(A='0',B='0',C='2'),dict(A='0',B='94',C='2')],
        initial_classifications=['CURRENTLY_FEASIBLE','CURRENTLY_FEASIBLE','CURRENTLY_FEASIBLE','WAIT_SETTLEMENT_REASSESSMENT'],
        old_trigger_buy_reasons=['NO_NEW_INDEPENDENT_TRIGGER'],orders_or_simulation='NOT_PERFORMED'))
    save(ROOT/'search-limit-spec.json',dict(source_case='initial',only_change=dict(max_grid_combinations='0'),
        expected_status='REFUSED_SEARCH_LIMIT',expected_reason='EXPLICIT_GRID_ENUMERATION_LIMIT_EXCEEDED',candidates=[],enumeration_complete=False))
    target=ROOT.parent/'quantity_candidates.py';(ROOT/'before/source').mkdir(parents=True)
    with (ROOT/'before/source/quantity_candidates.py').open('x') as f:f.write(target.read_text())
    originals.extend([controls,preset])
    for p in [ROOT.parent/n for n in ('allocation.py','core.py','execution.py','continuity.py','quantity_replay.py','quantity_after_retry.py','evaluated_replay.py','account_metrics.py')]:originals.append(info(p))
    originals.append(info(PROJECT/'rotation_research/action_ledger.py'))
    save(ROOT/'intake.json',dict(baseline='9efc3f34ae46df21411ef738a57d61c2fca7a540',source_before=info(target),
        originals=originals,input_expected_versions_saved_before_execution=True,new_prices_or_sources=False,old_suites_replayed=False))


if __name__=='__main__':main()
