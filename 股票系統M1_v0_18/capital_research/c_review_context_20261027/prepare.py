"""Pin original complete review/retry requests and their exact saved results."""
from pathlib import Path
from capital_research.lifecycle import _fp
from capital_research.decimal_context_20261027.prepare import load,save,info

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
PRIMARY=('review','retry')
SELECTION=[('review','review','c_order_review_20261026','valid-C-same-order','after-checkpoint-fix'),
    ('retry','retry','c_order_retry_20261027','qualification-restored','initial'),
    ('review-unknown','review','c_order_review_20261026','unknown-current-eligibility','after-checkpoint-fix'),
    ('review-partial-cancel','review','c_order_review_20261026','future-revocation-known-after-partial','after-checkpoint-fix'),
    ('review-wrong-order','review','c_order_review_20261026','wrong-order-id','after-checkpoint-fix'),
    ('retry-unknown','retry','c_order_retry_20261027','still-unknown','initial'),
    ('retry-partial','retry','c_order_retry_20261027','partial-seven','initial'),
    ('retry-wrong-predecessor','retry','c_order_retry_20261027','wrong-predecessor','initial')]


def main():
    originals={};cases=[]
    def pin(p):
        m=info(p);originals[m['path']]=m;return m
    for label,entry,folder,name,stage in SELECTION:
        base=ROOT.parent/folder;p=base/'cases'/name/'input.json';e=base/'cases'/name/'expected.json';a=base/stage/name/'actual.json'
        cases.append(dict(name=label,entry=entry,role='primary' if label in PRIMARY else 'necessary_regression',
            input=pin(p),expected=pin(e),original_actual=pin(a),input_id=_fp(load(p)),expected_result_id=_fp(load(a))))
    controls=pin(ROOT.parent/'quantity_context_20261027/contexts.json');preset=pin(ROOT.parent/'quantity_context_20261027/test-controls.json')
    save(ROOT/'input.json',dict(schema='capital-c-review-context-probe/0.1',synthetic=True,cases=cases,
        controls_reference=controls,preset_reference=preset))
    save(ROOT/'expected.json',dict(all_complete_outputs_equal_original_actual=True,caller_and_input_unchanged=True,
        original_capital='1430',general_reserve='100',order_id='r1-B',original_and_remaining_quantity='20',
        family='C',trigger_ids=['B-event'],new_evidence_tokens=[],retry_attempts=['REJECTED','ACCEPTED'],
        retry_final_cash='275.100',retry_final_shares=dict(A='60',B='25',C='2'),partial_fill='7',partial_remaining='13',
        review_partial_status='CANCELLED_EVIDENCE',retry_partial_status='EXPIRED_UNFILLED',
        policy='Two independent outer scopes; retry fix requires after-review-only countercheck'))
    (ROOT/'before/source').mkdir(parents=True)
    before={}
    for name in ('conditional_quantity_review.py','conditional_retry.py'):
        p=ROOT.parent/name;before[name]=info(p)
        with (ROOT/'before/source'/name).open('x') as f:f.write(p.read_text())
    for name in ('core.py','execution.py','continuity.py','allocation.py','quantity_candidates.py','quantity_replay.py','quantity_after_retry.py',
            'eligibility.py','fact_lineage.py','reassessment_history.py','order_review.py','transition_risk.py','close_clock.py','lifecycle.py'):
        pin(ROOT.parent/name)
    for p in (PROJECT/'rotation_research/action_ledger.py',PROJECT/'rotation_research/core.py',
            ROOT.parent/'decimal_context_20261027/prepare.py',ROOT.parent/'decimal_context_20261027/reproduce.py',
            ROOT.parent/'c_order_review_20261026/verify.py',ROOT.parent/'c_order_retry_20261027/verify.py'):pin(p)
    save(ROOT/'intake.json',dict(baseline='c8d95bca07057b05f038ca1c906635331ba2e0df',sources_before=before,originals=list(originals.values()),
        input_expected_saved_before_execution=True,no_new_prices_or_parameters=True,no_old_suite_or_standalone_producer=True))


if __name__=='__main__':main()
