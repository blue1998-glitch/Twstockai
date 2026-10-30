"""Execute only frozen new bridge fixtures; never regenerate old evidence."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from capital_research.quantity_replay import replay_sequence

HERE=Path(__file__).parent
ROOT=HERE.parents[2]


def dump_new(path,value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def assess(actual,expected,earlier):
    r=actual['replay'];last=r['last_execution'];checks=dict(status=r['status']==expected['status'],execution_calls=r['execution_calls']==expected['execution_calls'])
    if 'total_fills' in expected:checks['fills']=last is not None and len(last['fills'])==expected['total_fills']
    if last is not None:
        row=last['ledger']['daily'][-1]
        for key,field in [('final_cash','settled_cash'),('final_nav','net_accrual_equity')]:
            if key in expected:checks[key]=Decimal(row[field])==Decimal(expected[key])
        if 'final_shares' in expected:checks['final_shares']=row['shares']==expected['final_shares']
        if 'waiting_order' in expected:
            st=last['order_states'][expected['waiting_order']]
            checks['waiting']=st['requires_reassessment'] is True and st['status']=='WAITING_REASSESSMENT'
        if 'cancelled_order' in expected:checks['cancelled']=last['order_states'][expected['cancelled_order']]['status']=='CANCELLED_AT_REVIEW'
        if 'pending_payable' in expected:checks['payable_preserved']=Decimal(row['purchase_payable'])==Decimal(expected['pending_payable'])
    if 'first_cash' in expected:
        row=r['rounds'][0]['execution']['ledger']['daily'][-1]
        checks['first_cash']=Decimal(row['settled_cash'])==Decimal(expected['first_cash'])
        checks['first_nav']=Decimal(row['net_accrual_equity'])==Decimal(expected['first_nav'])
        checks['first_shares']=row['shares']==expected['first_shares']
    if 'origin_capital' in expected:checks['origin_capital']=Decimal(r['historical_checkpoint']['state']['origin_initial_capital'])==Decimal(expected['origin_capital'])
    if 'reason' in expected:
        reasons=list(r['reasons'])
        for record in r['rounds']:
            reasons+=record['reasons']
            if record['execution']:reasons += [e.get('reason','') for e in record['execution'].get('execution_events',[])]
        checks['reason']=any(expected['reason'] in x for x in reasons)
    if 'same_numeric_prefix_as' in expected:
        checks['numeric_prefix']=r['rounds'][0]['numeric_prefix']==earlier[expected['same_numeric_prefix_as']]['replay']['rounds'][0]['numeric_prefix']
    checks['formal_false']=all(r[k] is False for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'))
    checks['no_strategy_winner']=r['ranking'] is None and r['selected_strategy'] is None
    return checks


def build(stage='after-final'):
    intake=json.loads((HERE/'intake.json').read_text())
    output=HERE/stage
    if output.exists():
        raise ValueError('Existing bridge actuals are immutable: READ only')
    for row in intake['input_expected_fingerprints']:
        b=(ROOT/row['path']).read_bytes()
        if len(b)!=row['bytes'] or hashlib.sha256(b).hexdigest()!=row['sha256']:raise ValueError('Frozen input/oracle changed')
    output.mkdir();results=[];earlier={}
    for name in intake['case_names']:
        p=HERE/'cases'/name;request=json.loads((p/'input.json').read_text());expected=json.loads((p/'expected.json').read_text())
        try:
            actual=replay_sequence(request);checks=assess(actual,expected,earlier)
        except Exception as exc:
            actual=dict(error_type=type(exc).__name__,error=str(exc));checks={'unexpected_exception':False}
        target=output/name;target.mkdir();dump_new(target/'actual.json',actual);earlier[name]=actual
        results.append(dict(case=name,checks=checks,matched=all(checks.values())))
    dump_new(output/'summary.json',dict(schema='quantity-replay-synthetic-summary/0.1',cases=results,all_matched=all(x['matched'] for x in results),
        independent_market_samples=0,strategy_ranking=None,qualification_upgrades=0))
    failed=[x['case'] for x in results if not x['matched']]
    if failed:raise AssertionError('Preserve actuals and frozen oracle; diagnose: '+repr(failed))
    print(f'{len(results)} explicit synthetic bridge fixtures matched frozen expectations; no policy selection')


if __name__=='__main__':build()
