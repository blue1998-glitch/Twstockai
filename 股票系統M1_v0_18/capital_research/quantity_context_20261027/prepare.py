"""Freeze new exact requests/oracles; only provenance labels differ from seeds."""
from copy import deepcopy
from pathlib import Path
from capital_research.decimal_context_20261027.prepare import load,save,info

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]


def main():
    base=ROOT.parent/'quantity_replay_20261026/cases';originals=[]
    for name,seed in [('complete','partial-then-independent'),('old-trigger','old-trigger-blocked')]:
        folder=base/seed;value=deepcopy(load(folder/'input.json'))
        value['run_policy']['parameter_source']='QUANTITY_CONTEXT_PROBE_20261027'
        for f in value['rounds']:f['decision_template']['parameter_source']='QUANTITY_CONTEXT_PROBE_20261027_'+name+'_'+f['id']
        save(ROOT/'cases'/name/'input.json',value)
        expected=deepcopy(load(folder/'expected.json'))
        expected.update(complete_output_equal_new_normal=True,caller_context_unchanged=True,input_unchanged=True,
            schema='capital-quantity-replay/0.1',general_reserved_cash='100',origin_capital='2230')
        save(ROOT/'cases'/name/'expected.json',expected)
        originals.extend([info(folder/'input.json'),info(folder/'expected.json'),info(folder/'actual.json')])
    normal=dict(prec=28,rounding='ROUND_HALF_EVEN',Emin=-999999,Emax=999999,capitals=1,clamp=0,
        traps=['InvalidOperation','DivisionByZero','Overflow'],flags=[])
    controls=[dict(name='normal',context=normal),dict(name='round-up',context={**normal,'prec':7,'rounding':'ROUND_UP'}),
        dict(name='round-down',context={**normal,'prec':7,'rounding':'ROUND_DOWN'}),
        dict(name='inexact-trap',context={**normal,'traps':normal['traps']+['Inexact']}),
        dict(name='narrow-exponents',context={**normal,'Emin':-2,'Emax':2,'traps':normal['traps']+['Underflow']})]
    save(ROOT/'contexts.json',controls)
    preset={**normal,'prec':5,'rounding':'ROUND_FLOOR','Emin':-2,'Emax':2,'capitals':0,'clamp':1,
        'flags':['Inexact','Rounded'],'traps':normal['traps']+['Inexact','Rounded','Underflow','Subnormal','Clamped','FloatOperation']}
    save(ROOT/'test-controls.json',dict(preset=preset,expected_full_output_equal_normal=True,
        expected_old_trigger='STOPPED_CANDIDATE_GATE',expected_reason='NO_NEW_INDEPENDENT_TRIGGER',no_hidden_new_orders=True))
    target=ROOT.parent/'quantity_replay.py';(ROOT/'before/source').mkdir(parents=True)
    with (ROOT/'before/source/quantity_replay.py').open('x') as f:f.write(target.read_text())
    for p in [ROOT.parent/n for n in ('core.py','execution.py','continuity.py','quantity_candidates.py','quantity_choice_rules.py','evaluated_replay.py','account_metrics.py','lifecycle.py')]:originals.append(info(p))
    originals.extend([info(PROJECT/'rotation_research/action_ledger.py'),info(PROJECT/'rotation_research/store.py')])
    save(ROOT/'intake.json',dict(baseline='ea33452d9cc15c626b87748444a4b6377e3d84a3',source_before=info(target),
        originals=originals,exact_inputs_expected_saved_before_reproduction=True,
        old_suites_or_old_actuals_regenerated=False,only_seed_changes='EXPLICIT_PROVENANCE_LABELS',new_quotes_added=False))


if __name__=='__main__':main()
