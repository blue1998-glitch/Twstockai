"""Write new synthetic actuals only; existing outputs are never regenerated."""
from pathlib import Path
import hashlib
import json
from capital_research.quantity_candidates import generate

HERE=Path(__file__).parent
ROOT=HERE.parents[2]


def dump_new(path,data):
    with path.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def assess(actual,expected,request,earlier):
    r=actual['research'];checks={'status':r['status']==expected['status']}
    candidates=r['candidates'];a=request['incumbent'];b=request['destination']
    if 'grid_points' in expected:checks['grid_points']=r['grid_points']==expected['grid_points']
    if 'candidate_count' in expected:checks['candidate_count']=len(candidates)==expected['candidate_count']
    if 'probe' in expected:
        p=expected['probe'];matches=[x for x in candidates if x['plan'] and x['plan']['targets'][a]==p['A'] and x['plan']['targets'][b]==p['B']]
        checks['probe']=len(matches)==1 and matches[0]['classification']==p['classification']
    if expected.get('all_buys_rejected'):
        buys=[x for x in candidates if x.get('additional_B') and int(x['additional_B'])>0]
        checks['all_buys_rejected']=bool(buys) and all(x['classification']=='REJECTED' for x in buys)
    if 'required_reason' in expected:checks['reason']=any(expected['required_reason'] in x['reasons'] for x in candidates)
    if 'capital_qualified' in expected:checks['capital_qualified']=r['baseline']['layer2'][b]['capital_eligibility']['qualified_for_synthetic_proposal']==expected['capital_qualified']
    if 'full_classification' in expected:checks['full_classification']=any('FULL_TRANSFER' in x['kinds'] and x['classification']==expected['full_classification'] for x in candidates)
    if 'B_feasibility' in expected:
        matches={x['plan']['targets'][b]:x['classification'] for x in candidates if x['plan'] and x['plan']['targets'][a]==expected['fixed_A']}
        checks['non_monotone']=matches==expected['B_feasibility']
    if 'same_research_as' in expected:checks['same_research']=r==earlier[expected['same_research_as']]['research']
    if 'settled_cash' in expected:checks['settled_cash']=request['decision_input']['account']['settled_cash']==expected['settled_cash']
    if expected.get('prefix_nonempty_fills'):checks['prefix_nonempty_fills']=bool(request['continuation']['checkpoint']['state']['accepted_fills'])
    checks['not_selected']=r['selected_id'] is None and r['ranking'] is None
    checks['formal_false']=all(r[k] is False for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'))
    return checks


def build():
    intake=json.loads((HERE/'intake.json').read_text())
    if (HERE/'summary.json').exists() or any((HERE/'cases'/name/'actual.json').exists() for name in intake['case_names']):
        raise ValueError('Saved actual already exists; READ it, never overwrite or regenerate')
    for row in intake['input_expected_fingerprints']:
        payload=(ROOT/row['path']).read_bytes()
        if len(payload)!=row['bytes'] or hashlib.sha256(payload).hexdigest()!=row['sha256']:
            raise ValueError('Frozen input/oracle changed')
    earlier={};summary=[]
    for name in intake['case_names']:
        p=HERE/'cases'/name;request=json.loads((p/'input.json').read_text());expected=json.loads((p/'expected.json').read_text())
        try:
            actual=generate(request)
            dump_new(p/'actual.json',actual)
            checks=assess(actual,expected,request,earlier)
        except Exception as exc:
            if not (p/'actual.json').exists():dump_new(p/'actual.json',dict(error_type=type(exc).__name__,error=str(exc)))
            checks={'no_exception':False}
            actual=None
        if actual is not None:earlier[name]=actual
        summary.append(dict(case=name,checks=checks,matched=all(checks.values())))
    dump_new(HERE/'summary.json',dict(schema='quantity-candidates-synthetic-summary/0.1',cases=summary,
        all_matched=all(x['matched'] for x in summary),independent_market_samples=0,winner=None,
        note='Saved synthetic proposal diagnostics; not trades, market samples, strategy returns or test-method count'))
    failures=[x['case'] for x in summary if not x['matched']]
    if failures:raise AssertionError('Preserve mismatch actuals; do not edit oracle: '+repr(failures))
    print(f'{len(summary)} frozen synthetic cases match the original expectations; no winner/orders produced')


if __name__=='__main__':build()
