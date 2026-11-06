"""Run only frozen new-version synthetic inputs, preserving all old artifacts."""
from pathlib import Path
import hashlib
import json
from capital_research.quantity_candidates import generate

HERE=Path(__file__).parent
ROOT=HERE.parents[2]


def dump_new(path,value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def assess(actual,expected,request,previous):
    if 'error_type' in expected:
        return dict(error=actual.get('error_type')==expected['error_type'] and expected['error_contains'] in actual.get('error',''),
                    no_fake_research=actual.get('research') is None)
    if actual.get('research') is None:return {'unexpected_error':False}
    r=actual['research'];checks=dict(status=r['status']==expected['status'])
    candidates=r['candidates'];a=request['incumbent'];b=request['destination']
    if 'manual_grid' in expected:
        actual_grid={(x['plan']['targets'][a],x['plan']['targets'][b]) for x in candidates if x['plan']}
        checks['manual_grid']=all(tuple(pair) in actual_grid for pair in expected['manual_grid']) and r['grid_points']==len(expected['manual_grid'])
    if 'grid_points' in expected:checks['grid_points']=r['grid_points']==expected['grid_points']
    if 'candidate_count' in expected:checks['candidate_count']=len(candidates)==expected['candidate_count']
    if 'probe' in expected:
        p=expected['probe'];matches=[x for x in candidates if x['plan'] and x['plan']['targets'][a]==p['A'] and x['plan']['targets'][b]==p['B']]
        checks['probe']=len(matches)==1 and matches[0]['classification']==p['classification']
    buys=[x for x in candidates if int(x.get('additional_B') or '0')>0]
    if 'all_buys' in expected:checks['all_buys']=bool(buys) and all(x['classification']==expected['all_buys'] for x in buys)
    if 'reason' in expected:checks['reason']=any(expected['reason'] in x['reasons'] for x in candidates)
    if 'buy_family' in expected:checks['buy_family']=bool(buys) and all(x['plan']['family']==expected['buy_family'] for x in buys)
    if 'capital_qualified' in expected:checks['capital_qualified']=r['baseline']['layer2'][b]['capital_eligibility']['qualified_for_synthetic_proposal']==expected['capital_qualified']
    if 'preserve_C' in expected:checks['preserve_C']=all(x['plan']['targets']['C']==expected['preserve_C'] for x in candidates if x['plan'])
    if 'available' in expected:checks['available']=all(x['core_evaluation']['available_settled_cash']==expected['available'] for x in candidates if x['core_evaluation'])
    if 'B_feasibility' in expected:
        checks['non_monotone']={x['plan']['targets'][b]:x['classification'] for x in candidates if x['plan'] and x['plan']['targets'][a]=='100'}==expected['B_feasibility']
    if 'same_research_as' in expected:checks['future_isolation']=r==previous[expected['same_research_as']]['research']
    checks['no_winner']=r['selected_id'] is None and r['ranking'] is None
    checks['formal_false']=all(r[k] is False for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'))
    return checks


def build():
    intake=json.loads((HERE/'intake.json').read_text())
    if (HERE/'summary.json').exists() or any((HERE/'cases'/name/'actual.json').exists() for name in intake['case_names']):
        raise ValueError('Existing actuals are immutable: READ, never regenerate')
    for row in intake['input_expected_fingerprints']:
        payload=(ROOT/row['path']).read_bytes()
        if len(payload)!=row['bytes'] or hashlib.sha256(payload).hexdigest()!=row['sha256']:
            raise ValueError('Frozen input/oracle changed')
    results=[];earlier={}
    for name in intake['case_names']:
        p=HERE/'cases'/name;request=json.loads((p/'input.json').read_text());expected=json.loads((p/'expected.json').read_text())
        try:actual=generate(request)
        except Exception as exc:actual=dict(status='ERROR',error_type=type(exc).__name__,error=str(exc),research=None)
        dump_new(p/'actual.json',actual)
        checks=assess(actual,expected,request,earlier)
        results.append(dict(case=name,checks=checks,matched=all(checks.values())))
        earlier[name]=actual
    dump_new(HERE/'summary.json',dict(schema='quantity-candidates-v02-synthetic-summary/0.1',cases=results,
        all_matched=all(x['matched'] for x in results),independent_market_samples=0,qualification_upgrades=0))
    failed=[x['case'] for x in results if not x['matched']]
    if failed:raise AssertionError('Preserve mismatches; do not edit oracle: '+repr(failed))
    print(f'{len(results)} new frozen cases matched; no old producer, new orders or fills')


if __name__=='__main__':build()
