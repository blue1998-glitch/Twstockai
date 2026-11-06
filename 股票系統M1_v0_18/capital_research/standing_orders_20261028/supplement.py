"""Freeze remaining receipt and cash-receivable boundaries before RUN."""
from copy import deepcopy
from .freeze import ROOT, PROJECT, load, save, info
from .controls import baseline_simulate
from capital_research.core import fingerprint, timestamp
from capital_research.continuity import make_checkpoint


def freeze():
    save(ROOT/'supplement/source-before.json',dict(files=[info(PROJECT/'capital_research/execution_continuation.py')]))
    source=PROJECT/'capital_research/quantity_replay_20261026/after-final/partial-then-independent/actual.json'
    j=deepcopy(load(source)['replay']['rounds'][0]['execution_job'])
    first=deepcopy(j['tape']);j['tape']+=deepcopy(load(ROOT/'cases/partial-fill/root-input.json')['tape'][3:])
    j['observed_until']='2026-01-12T16:00:00+08:00';cut='2026-01-06T16:00:00+08:00'
    prefix=deepcopy(j);prefix.update(tape=first,observed_until=cut)
    save(ROOT/'supplement/receivable/root-input.json',j);save(ROOT/'supplement/receivable/prefix-input.json',prefix)
    save(ROOT/'supplement/receivable/expected.json',dict(status='CONTINUED_ORIGINAL_ORDERS',
        origin_capital='2230',prefix_cash='1000',prefix_payable='141.140',prefix_receivable='277.800',prefix_available='858.860',
        Jan8_cash='1056.660',Jan8_receivable='80',final_cash='1136.660',final_A='90',final_B='7',final_C='2',
        general_reserve='100',full_execution_equal=True))
    prior=baseline_simulate(prefix);full=baseline_simulate(j)
    save(ROOT/'supplement/receivable/baseline-prefix.json',prior);save(ROOT/'supplement/receivable/baseline-full.json',full)
    cp=make_checkpoint(j['ledger_input'],prior,through_at=cut)
    r=load(ROOT/'cases/partial-fill/input.json');path=r['path']
    path.update(origin_ledger_input_id=fingerprint(j['ledger_input']),observations=deepcopy(j['tape']))
    for row in path['session_coverage']:row['observation_ids']=[fingerprint(o) for o in j['tape'] if o['at'][:10]==row['date']]
    r.update(root_job=j,checkpoint=cp,expected_checkpoint_id=cp['checkpoint_id'],expected_latest_decision_id=prior['latest_decision_id'],
        expected_path_id=fingerprint(path),segment_tape=[o for o in j['tape'] if timestamp(o['at'])>timestamp(cut)])
    save(ROOT/'supplement/receivable/input.json',r)
    r=load(ROOT/'cases/partial-fill/input.json')
    review=deepcopy(load(ROOT/'cases/past-reassessment-current/root-input.json')['reassessments'][0])
    # An unreceived request is not an approved historical receipt, regardless
    # of its claimed decision date. No attempt to authenticate its contents.
    review['decision_input']['decision_at']='2026-01-06T15:30:00+08:00'
    r['root_job']['reassessments']=[review]
    save(ROOT/'supplement/unreceived-review/input.json',r)
    save(ROOT/'supplement/unreceived-review/expected.json',dict(status='REFUSED',reason='UNRECEIVED_REASSESSMENT_NOT_IMPLEMENTED',tail_observations=0))


def run():
    from capital_research.execution_continuation import resume_orders, _capture_original
    for name in ('receivable','unreceived-review'):
        r=load(ROOT/'supplement'/name/'input.json');a=resume_orders(r)
        save(ROOT/'supplement'/name/'actual.json',a)
        if name=='receivable' and a['execution'] is not None:
            ex,trace,_=_capture_original(r['root_job'])
            save(ROOT/'supplement'/name/'one-shot-observation-trace.json',trace)
            save(ROOT/'supplement'/name/'comparison.json',dict(full_execution_equal=ex==a['execution'],
                baseline_full_equal=ex==load(ROOT/'supplement/receivable/baseline-full.json'),
                every_common_observation_equal=trace==a['prefix_observation_trace']+a['observation_trace']))


if __name__=='__main__':
    import sys
    {'freeze':freeze,'run':run}[sys.argv[1]]()
