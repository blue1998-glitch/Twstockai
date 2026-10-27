"""Freeze original call arguments and saved-decision projections, without RUN."""
from copy import deepcopy
from pathlib import Path
from capital_research.lifecycle import _fp
from capital_research.decimal_context_20261027.prepare import load,save,info

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
CASES=('initial','resume')


def projection(source,index):
    frame=source['replay']['rounds'][index];job=frame['execution_job'];e=frame['execution']
    args=dict(data=deepcopy(job['decision_input']))
    meta=deepcopy(args['data']['source_integrity_metadata'])
    if index:
        c=job['continuation'];args.update(previous=deepcopy(c['previous_decision']),checkpoint=deepcopy(c['checkpoint']),
            cancelled_order_ids=deepcopy(c['cancelled_order_ids']),same_order_id=None)
        meta['continuity']=deepcopy(c['checkpoint']['integrity'])
    expected=dict(decision=deepcopy(e['decision_records'][e['decision_id']]),source_integrity_metadata=meta)
    return args,expected


def main():
    reference=ROOT.parent/'candidate_context_20261027/input.json';ref=load(reference)['cases'][0]
    path=PROJECT/ref['source']['path'];assert info(path)==ref['source'];source=load(path);assert _fp(source)==ref['source_id']
    controls=ROOT.parent/'quantity_context_20261027/contexts.json';preset=ROOT.parent/'quantity_context_20261027/test-controls.json'
    specs=[]
    for i,name in enumerate(CASES):
        args,expected=projection(source,i)
        specs.append(dict(name=name,entry='resume_decision' if i else 'decide',round_index=i,
            arguments_id=_fp(args),expected_wrapper_id=_fp(expected),expected_decision_id=expected['decision']['decision_id']))
    save(ROOT/'input.json',dict(schema='capital-decision-context-probe/0.1',synthetic=True,source=info(path),
        source_id=_fp(source),source_reference=info(reference),cases=specs,controls_reference=info(controls),preset_reference=info(preset)))
    save(ROOT/'expected.json',dict(rule='EXACT_SAVED_DECISION_AND_DECLARED_METADATA_PROJECTION_NOT_A_NEW_RUN',
        all_complete_outputs_equal_projection=True,initial_capital='2230',current_resume_value='2226.660',
        resume_cash='1056.660',reserve='100',resume_holdings=dict(A='80',B='7',C='2'),cash_claim='80',share_claim='10',
        prior_tokens_must_be_retained=True,metadata_rule='Copy exact input metadata; resume also copies checkpoint.integrity',
        input_and_caller_unchanged=True,ranking_or_execution_not_added=True))
    save(ROOT/'regression-specs.json',[
        dict(name='wrong-latest',change='Replace previous with the valid saved first generation baseline decision',error='LATEST_PREDECESSOR_REQUIRED'),
        dict(name='checkpoint-token-change',change='Remove the first checkpoint.state.reviewed_evidence_tokens entry only',error='Checkpoint differs from original ledger/fills/order states'),
        dict(name='reserve-drop',change='Set data.account.reserved_cash to 0 only',error='Next account/cutoff resets or drops authoritative cash, rights, holdings or orders'),
        dict(name='cash-right-drop',change='Set data.account.cash_claims to [] only',error='Next account/cutoff resets or drops authoritative cash, rights, holdings or orders'),
        dict(name='missing-checkpoint',change='Set checkpoint to null only',error='LEDGER_CHECKPOINT_REQUIRED')])
    target=ROOT.parent/'core.py';(ROOT/'before/source').mkdir(parents=True)
    with (ROOT/'before/source/core.py').open('x') as f:f.write(target.read_text())
    originals=[info(p) for p in (path,reference,controls,preset)]
    for name in ('continuity.py','execution.py','allocation.py','quantity_candidates.py','quantity_replay.py',
            'quantity_after_retry.py','conditional_quantity_review.py','conditional_retry.py','eligibility.py',
            'fact_lineage.py','reassessment_history.py','order_review.py','transition_risk.py','lifecycle.py'):
        originals.append(info(ROOT.parent/name))
    originals.extend(info(p) for p in (PROJECT/'rotation_research/action_ledger.py',PROJECT/'rotation_research/core.py',
        ROOT.parent/'decimal_context_20261027/reproduce.py',ROOT.parent/'decimal_context_20261027/prepare.py',
        ROOT.parent/'candidate_context_20261027/reproduce.py'))
    save(ROOT/'intake.json',dict(baseline='5f18238d6b2d2e1dec87da22d23a5bd3e1ff351a',source_before=info(target),
        originals=originals,input_expected_saved_before_execution=True,old_suites_or_market_replay_run=False,new_prices_or_sources=False))


if __name__=='__main__':main()
