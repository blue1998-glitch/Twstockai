"""Create-only RUN evidence; expected files were frozen before implementation."""
import argparse
from .freeze import ROOT, PROJECT, load, save, info
from capital_research.execution_continuation import resume_orders, _capture_original
from capital_research.continuity import make_checkpoint


def main(out):
    out=ROOT/out
    sources=[PROJECT/'capital_research'/n for n in ('execution.py','execution_continuation.py','continuity.py','core.py','fact_lineage.py','reassessment_history.py')]
    save(out/'source-versions.json',dict(files=[info(p) for p in sources]))
    index=load(ROOT/'case-index.json');summary={}
    for name in index['all']:
        r=load(ROOT/'cases'/name/'input.json');actual=resume_orders(r)
        save(out/name/'actual.json',actual)
        expected=load(ROOT/'cases'/name/'expected.json')
        row=dict(status=actual['status'],expected_status=expected['status'],reasons=actual.get('refusal_reasons',[]))
        if name in index['positive'] and actual['execution'] is not None:
            whole,trace,_=_capture_original(r['root_job'])
            cp=make_checkpoint(r['root_job']['ledger_input'],whole,through_at=r['observed_until'])
            comparison=dict(original_full_control_equal=whole==load(ROOT/'before'/name/'full-execution.json'),
                execution_equal=actual['execution']==whole,checkpoint_equal=actual['checkpoint']==cp,
                every_common_observation_equal=actual['prefix_observation_trace']+actual['observation_trace']==trace,
                every_daily_ledger_row_equal=actual['execution']['ledger']['daily']==whole['ledger']['daily'])
            save(out/name/'one-shot-observation-trace.json',trace)
            save(out/name/'comparison.json',comparison);row.update(comparison)
        summary[name]=row
        print(name,row)
    save(out/'summary.json',summary)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);main(p.parse_args().out)
