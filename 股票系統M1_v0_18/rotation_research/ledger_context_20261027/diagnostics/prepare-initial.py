"""Freeze existing synthetic inputs, exact oracles and source before RUN."""
from copy import deepcopy
from pathlib import Path
from capital_research.decimal_context_20261027.prepare import load,save,info
from capital_research.lifecycle import _fp

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
BASELINE='43bc493fa592ced26202116b22337d66183313f1'


def main():
    r=ROOT.parent;c=PROJECT/'capital_research';old=r/'action_data_20261022'
    examples=load(old/'engineered-examples.json');primary=load(old/'engineered-input.json')
    assert primary==examples['cash-net-withholding']['input']
    controls=c/'quantity_context_20261027/contexts.json';preset=c/'quantity_context_20261027/test-controls.json'
    save(ROOT/'controls.json',dict(contexts=load(controls),preset=load(preset)['preset'],
        references=[info(controls),info(preset)]))
    cases=[]
    for name in ['cash-net-withholding','stock-delivery','capital-reduction']:
        item=examples[name];cases.append(dict(name=name,input=item['input'],expected=item['result'],
            input_id=_fp(item['input']),expected_id=_fp(item['result']),kind='EXACT_SAVED_SYNTHETIC'))
    for name,key,reason in [('opening-unknown','opening_claims','OPENING_ENTITLEMENTS_UNKNOWN'),
            ('net-unknown','net_distributions','NET_DISTRIBUTIONS_TAX_FEES_UNKNOWN')]:
        value=deepcopy(primary);value['qualification'][key]='UNKNOWN'
        cases.append(dict(name=name,input=value,input_id=_fp(value),kind='SYNTHETIC_REFUSAL',
            expected=dict(status='REFUSED_INCOMPLETE_EVENT_ACCOUNTING',refusal_reasons=[reason],
                source_qualification=value['qualification'],daily=[],journal=[],total_net_return=None,
                scenario_net_return=None,actual_realized_investor_return=None,policy_authorized=False,
                historical_signal_eligible=False,primary_pressure_id=None)))
    save(ROOT/'input.json',dict(schema='action-ledger-context-probe/0.1',synthetic=True,cases=cases,
        primary_input=info(old/'engineered-input.json'),original_examples=info(old/'engineered-examples.json'),
        capital_regression=dict(helper='capital_research.execution_context_20261027.reproduce.case',case='continuation')))
    save(ROOT/'expected.json',dict(all_contexts_equal_frozen_oracles=True,caller_context_unchanged=True,
        default_context_unchanged=True,input_unchanged=True,read_without_engine_or_write=True,
        manual_cash_example=dict(initial_equity='1000',dividend_receivable_gross='100',
            dividend_receivable_net='80.0',cash_received='80.0',end_net_equity='980.0',scenario_net_return='-0.02',
            total_net_return=None),no_formula_or_qualification_changes=True))
    integration=c/'execution_context_20261027/input.json'
    paths=[old/'engineered-input.json',old/'engineered-examples.json',old/'CONTRACT.md',
        r/'action_cli.py',r/'store.py',r/'core.py',PROJECT/'graph_core/core.py',controls,preset,
        c/'decimal_context_20261027/prepare.py',c/'decimal_context_20261027/reproduce.py',c/'lifecycle.py',
        c/'core.py',c/'execution.py',c/'continuity.py',integration,
        c/'execution_context_20261027/prepare.py',c/'execution_context_20261027/reproduce.py',
        PROJECT/load(integration)['source']['path']]
    save(ROOT/'intake.json',dict(baseline=BASELINE,source_before=info(r/'action_ledger.py'),
        unchanged_originals=[info(p) for p in paths],effective_docs_before=[info(PROJECT.parent/n) for n in
            ['AGENTS.md','CONTINUE_IN_WORK_MODE.md','PROJECT_VISION.md','M1_V019_GRAPH_CORE_RESUME_HANDOFF.md']],
        frozen_before_reproduction=True))
    (ROOT/'before/source').mkdir(parents=True)
    with (ROOT/'before/source/action_ledger.py').open('x') as f:f.write((r/'action_ledger.py').read_text())
    save(ROOT/'frozen.json',dict(files=[info(ROOT/n) for n in
        ['CONTRACT.md','input.json','expected.json','controls.json','intake.json','prepare.py','reproduce.py','before/source/action_ledger.py']]))


if __name__=='__main__':main()
