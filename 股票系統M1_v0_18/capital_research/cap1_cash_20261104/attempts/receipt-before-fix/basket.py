"""Minimal explicit multi-asset sell gate over the ORIGINAL decision/execution.

No financial formulas, ledger posting or trading policy. Original single-asset
cash_action remains unchanged. READ never calls evaluate/resume/simulate.
"""
from copy import deepcopy
from decimal import Context, ROUND_HALF_EVEN, localcontext, InvalidOperation, DivisionByZero, Overflow
from ..cash_action import evaluate as single_evaluate
from ..cash_action_execution import _job as single_job, ORDER_FIELDS, FLAGS
from ..core import resume_decision, fingerprint, quantity
from ..execution import simulate
from ..continuity import make_checkpoint
from ..saved_action_source import _pair, _account_binding, _research
from ..lifecycle import _chain, _account, _signed
from ..fact_lineage import source_snapshot
from ..account_metrics import _evaluate_snapshots

INPUT='cap1-explicit-full-exit-input/0.1'
RESULT='cap1-explicit-full-exit-result/0.1'

def require(ok,reason):
    if not ok:raise ValueError(reason)

def scope(request,seed):
    require(set(request)=={'schema','synthetic','id','seed_action_input','sales'} and request['schema']==INPUT
        and request['synthetic'] is True and isinstance(request['id'],str) and request['id'], 'EXPLICIT_FULL_EXIT_REQUIRED')
    i=request['seed_action_input'];c=seed['research'];data=deepcopy(seed['source_integrity_metadata']['derived_decision_input'])
    require(i['schema']=='capital-cash-action-input/0.2' and i['synthetic'] is True
        and i['action']['kind']=='EXIT_SELLABLE_HOLDING','ORIGINAL_SINGLE_EXIT_SEED_REQUIRED')
    require(c['status']=='CURRENTLY_FEASIBLE' and c['intent']['feasible_for_research'] is True,'SINGLE_EXIT_GATE_REFUSED')
    _research(c);require(seed['source_integrity_metadata']['full_request_id']==fingerprint(i),'SEED_INPUT_BINDING_CONFLICT')
    for key,value in i['decision_template'].items():require(data[key]==value,'SEED_INFORMATION_CONFLICT:'+key)
    binding,parent=_account_binding(i['account_source'],data)
    require(parent is not None and c['account_binding']==binding,'EXACT_COMMON_CHECKPOINT_REQUIRED')
    require(not any(quantity(n) for n in parent['state']['opening_unavailable_shares'].values()),'SELLABILITY_RELEASE_NOT_SUPPORTED')
    prior=parent['execution_result'];identities={r['identity']['code']:r['identity'] for r in prior['fact_sources'][prior['latest_decision_id']]['records']}
    require(set(i['decision_template']['assets'])==set(identities) and all(i['decision_template']['assets'][c][k]==identities[c][k] for c in identities for k in ('source_id','basis_id','adjustment_version')),'FULL_EXIT_ASSET_SOURCE_BASIS_CONFLICT')
    a=data['account'];holdings=a['holdings']
    require(isinstance(a['share_claims'],list) and not a['share_claims'],'PENDING_OR_UNKNOWN_SHARE_RIGHTS_PREVENT_FULL_EXIT')
    require(isinstance(a['cash_claims'],list) and not a['payables'] and not a['pending_orders'],'UNKNOWN_RIGHTS_OR_OPEN_TRANSACTIONS')
    expected={code:str(quantity(row['shares'])) for code,row in holdings.items() if quantity(row['shares'])>0}
    require(expected and request['sales']==expected,'EXACT_ALL_HOLDINGS_SALE_SCOPE_REQUIRED')
    require(all(quantity(row['shares'])==quantity(row['sellable']) for row in holdings.values()),'ALL_HELD_SHARES_MUST_BE_TRADABLE')
    require(sorted(data['consumed_evidence_tokens'])==binding['reviewed_evidence_tokens'],'INHERITED_TOKEN_CONFLICT')
    plan=deepcopy(c['intent']['plan']);plan.update(id=request['id'],targets={code:'0' for code in holdings})
    plan['conditions']=['EXPLICIT_ALL_ASSET_SELL_NOT_STRATEGY','VERIFY_ACTUAL_FILLS_RIGHTS_AND_SETTLEMENT_BEFORE_CASH_CLAIM']
    data['plans']=[plan]
    return data,parent


def evaluate(request):
    out=dict(schema='cap1-explicit-full-exit-check/0.1',synthetic=True,status='REFUSED',reasons=[],
             request_id=fingerprint(request),seed_checked=None,decision_input=None,decision=None,
             **{k:False for k in FLAGS},primary_pressure_id=None)
    try:
        seed=single_evaluate(request['seed_action_input']);data,parent=scope(request,seed)
        prior=parent['execution_result'];previous=dict(decision=deepcopy(prior['decision_records'][prior['latest_decision_id']]))
        result=resume_decision(previous,data,checkpoint=parent,cancelled_order_ids=[])
        d=result['decision'];plan=next(x for x in d['layer3']['alternatives'] if x['id']==request['id'])
        require(plan['feasible'],'ORIGINAL_FULL_PLAN_FEASIBILITY_REFUSED:'+str(plan['reasons']))
        out.update(status='FEASIBLE_EXPLICIT_FULL_EXIT_INTENT',seed_checked=seed,decision_input=data,decision=d)
    except (ValueError,KeyError,TypeError,AttributeError,IndexError,StopIteration) as e:out['reasons']=[str(e)]
    out['check_id']=fingerprint(out);return out


def job_for(request,checked,spec):
    require(checked['request_id']==fingerprint(request),'FULL_EXIT_REQUEST_BINDING_CONFLICT')
    require(checked['check_id']==fingerprint({k:v for k,v in checked.items() if k!='check_id'}),'FULL_EXIT_CHECK_FINGERPRINT_CONFLICT')
    require(checked['status']=='FEASIBLE_EXPLICIT_FULL_EXIT_INTENT','FULL_EXIT_CHECK_NOT_FEASIBLE')
    _research(checked);data,parent=scope(request,checked['seed_checked'])
    require(data==checked['decision_input'],'FULL_EXIT_DERIVED_INPUT_CONFLICT')
    require(isinstance(spec['orders'],list),'EXPLICIT_ORDERS_REQUIRED');totals={code:0 for code in request['sales']}
    for order in spec['orders']:
        require(set(order)==ORDER_FIELDS and order['side']=='SELL' and order['code'] in totals,'ORDER_OUTSIDE_FULL_EXIT_SCOPE')
        n=int(quantity(order['shares']));require(n>0,'POSITIVE_SELL_SHARES_REQUIRED');totals[order['code']]+=n
    require({c:str(n) for c,n in totals.items()}==request['sales'],'ORDERS_MUST_COVER_EXACT_ALL_HELD_SHARES')
    seed_spec=deepcopy(spec);code=request['seed_action_input']['action']['code']
    seed_spec['orders']=[o for o in seed_spec['orders'] if o['code']==code]
    job=single_job(request['seed_action_input'],checked['seed_checked'],seed_spec)
    job.update(decision_input=deepcopy(data),plan_id=request['id'],orders=deepcopy(spec['orders']))
    return job


def execute(request,checked,spec):
    out=dict(schema=RESULT,synthetic=True,status='REFUSED',reasons=[],request=deepcopy(request),checked=deepcopy(checked),
        execution_spec=deepcopy(spec),execution_job=None,execution=None,checkpoint=None,execution_calls=0,
        **{k:False for k in FLAGS},primary_pressure_id=None)
    try:
        require(evaluate(request)==checked,'FULL_EXIT_CHECK_CHANGED')
        job=job_for(request,checked,spec);out['execution_job']=deepcopy(job)
        out['execution_calls']=1;e=simulate(job);out['execution']=e
        require(e['status']=='SYNTHETIC_EXECUTION_REPLAY','ORIGINAL_EXECUTION_REFUSED:'+str(e['refusal_reasons']))
        require(e['decision_records'][e['decision_id']]==checked['decision'],'FULL_EXIT_EXECUTED_DECISION_CONFLICT')
        out.update(checkpoint=make_checkpoint(job['ledger_input'],e,through_at=job['observed_until']),status='REPLAYED_EXPLICIT_FULL_EXIT')
    except (ValueError,KeyError,TypeError,AttributeError,IndexError,StopIteration) as e:out['reasons']=[str(e)]
    out['receipt_id']=fingerprint(out);return out


def read_frames(receipt):
    require(receipt['schema']==RESULT and receipt['status']=='REPLAYED_EXPLICIT_FULL_EXIT'
        and receipt['execution_calls']==1,'COMPLETE_FULL_EXIT_RECEIPT_REQUIRED')
    _research(receipt)
    require(receipt['receipt_id']==fingerprint({k:v for k,v in receipt.items() if k!='receipt_id'}),'FULL_EXIT_RECEIPT_FINGERPRINT_CONFLICT')
    request=receipt['request'];checked=receipt['checked'];job=job_for(request,checked,receipt['execution_spec'])
    require(job==receipt['execution_job'],'FULL_EXIT_EXECUTION_JOB_CONFLICT')
    d=checked['decision'];_signed(d,'decision_id')
    require(d['common_account_id']==fingerprint(job['decision_input']['account']),'FULL_EXIT_DECISION_ACCOUNT_CONFLICT')
    require(all(d[k]==job['decision_input'][k] for k in ('decision_at','data_cutoff')),'FULL_EXIT_DECISION_CLOCK_CONFLICT')
    plan=next(x for x in d['layer3']['alternatives'] if x['id']==request['id'])
    require(plan['targets']==job['decision_input']['plans'][0]['targets'] and plan['feasible'],'FULL_EXIT_SAVED_PLAN_CONFLICT')
    parent=request['seed_action_input']['account_source']['checkpoint'];e=receipt['execution']
    require(e['decision_records'][d['decision_id']]==d and e['decision_id']==d['decision_id'],'FULL_EXIT_SAVED_DECISION_CONFLICT')
    require(e['fact_sources'][d['decision_id']]==source_snapshot(job['decision_input']),'FULL_EXIT_SOURCE_BINDING_CONFLICT')
    frames=[_pair(parent['execution_result'],parent,'/request/seed_action_input/account_source/checkpoint/execution_result'),
            _pair(e,receipt['checkpoint'],'/execution')]
    _chain(frames)
    return frames


def metrics(receipt,evaluation_at):
    out=dict(schema='cap1-full-exit-account-metrics/0.1',synthetic=True,status='REFUSED',reasons=[],
        statistics=None,costs=None,account=None,initial_capital=None,terminal_accrual_equity=None,
        ranking=None,primary_pressure_id=None,**{k:False for k in FLAGS})
    try:
        with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999,capitals=1,clamp=0,flags=[],traps=[InvalidOperation,DivisionByZero,Overflow])):
            frames=read_frames(receipt)
            summary=dict(account=_account(frames[-1]),source=dict(schema=RESULT))
            pairs=[(x['execution'],x['checkpoint']) for x in frames]
            request=dict(evaluation_at=evaluation_at,saved_result=receipt)
            out.update(_evaluate_snapshots(request,pairs,summary));out['status']='EVALUATED'
    except (ValueError,KeyError,TypeError,AttributeError,IndexError,StopIteration) as e:out['reasons']=[str(e)]
    out['evaluation_id']=fingerprint(out);return out
