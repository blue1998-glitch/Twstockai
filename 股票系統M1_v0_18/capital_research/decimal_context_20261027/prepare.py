"""Freeze exact original references, four contexts and expected normal output."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]


def load(p):return json.loads(p.read_text())


def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def info(p):
    raw=p.read_bytes();return dict(path=str(p.relative_to(PROJECT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def main():
    source=ROOT.parent/'quantity_replay_20261026/cases/partial-then-independent/actual.json'
    expected=ROOT.parent/'account_metrics_20261027/final/saved/complete-partial-chain/result.json'
    normal=dict(prec=28,rounding='ROUND_HALF_EVEN',Emin=-999999,Emax=999999,capitals=1,clamp=0,
        traps=['InvalidOperation','DivisionByZero','Overflow'],flags=[])
    contexts=[dict(name='normal',context=normal),dict(name='different-rounding',context={**normal,'prec':7,'rounding':'ROUND_UP'}),
        dict(name='inexact-trap',context={**normal,'traps':normal['traps']+['Inexact']}),
        dict(name='narrow-exponents',context={**normal,'Emin':-2,'Emax':2,'traps':normal['traps']+['Underflow']})]
    save(ROOT/'input.json',dict(schema='account-metrics-decimal-probe/0.1',synthetic=True,
        saved_source=info(source),baseline_expected=info(expected),evaluation_at='2026-01-12T16:00:00+08:00',contexts=contexts))
    save(ROOT/'expected.json',dict(status='EVALUATED',all_contexts_equal_original_normal_evaluation=True,
        caller_context_unchanged=True,input_unchanged=True,required_error=None,
        baseline_evaluation_id=load(expected)['evaluation_id'],meaning='DETERMINISM_NOT_STRATEGY_VALIDATION'))
    old=ROOT.parent/'account_metrics.py';(ROOT/'before/source').mkdir(parents=True)
    with (ROOT/'before/source/account_metrics.py').open('x') as f:f.write(old.read_text())
    originals=[info(p) for p in (source,expected,ROOT.parent/'evaluated_replay.py',ROOT.parent/'quantity_replay.py',
        PROJECT/'rotation_research/action_ledger.py',ROOT.parent/'lifecycle.py')]
    save(ROOT/'intake.json',dict(baseline='829fd4af25e12f061e49e0c77446ed2ac4528119',
        originals=originals,source_before=info(old),input_expected_written_before_reproduction=True,
        other_project_progress_read=['PROJECT_VISION','REQUIREMENTS_TRACE','GRAPH_CORE','STRUCTURE_STATE','REACTION_FACTS',
          'VOLUME_PEAK_RESEARCH','SOURCE_AND_OPENING_RIGHTS','PERSISTENCE_AND_WORKFLOW','CAPITAL_RESEARCH'],
        no_old_suite_or_source_refetch=True))


if __name__=='__main__':main()
