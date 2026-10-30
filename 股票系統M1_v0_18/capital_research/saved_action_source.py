"""Pure saved-action source binding, shared by evaluation and immutable READ.

No metrics, decision, accounting, execution or file IO imports/calls.
Functions are moved unchanged from action_account_metrics/0.1.
"""
from copy import deepcopy
from .lifecycle import _fp, _time, _snapshot, _chain, _account, _signed, _require, FLAGS, TERMINAL
from .fact_lineage import history_at, source_snapshot
from .reassessment_history import declaration_sources, validate_request_binding

SOURCE='capital-saved-action-source/0.1'


def _research(value):
    _require(value['synthetic'] is True and all(value[k] is False for k in FLAGS)
        and value.get('primary_pressure_id') is None,'SAVED_ACTION_NOT_RESEARCH_ONLY')


def _close(origin,proof,at):
    """Read the explicit close proof without importing the execution/ledger core."""
    _require(proof['schema']=='synthetic-ledger-close-clock/0.1' and
        proof['qualification']=='DECLARED_SYNTHETIC_DAY_END_NOT_REAL_MARKET_OR_BROKER_PROOF','EXPLICIT_SAVED_CLOSE_REQUIRED')
    row=proof['closes'][at[:10]]
    _require(at[:10] in {r['date'] for r in origin['calendar']} and row['as_of']==at
        and _time(row['available_at'])>=_time(at),'SAVED_CLOSE_WATERMARK_CONFLICT')
    _require(bool(row['source_ids']) and all(origin['sources'][k]['kind']=='ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET'
        for k in row['source_ids']),'NON_SYNTHETIC_CLOSE_SOURCE')
    return row


def _pair(execution,checkpoint,pointer):
    frame=_snapshot(execution,checkpoint,pointer);e=execution;s=checkpoint['state'];origin=checkpoint['origin_ledger_input']
    _require(checkpoint['execution_result']==e and e['origin_ledger_input_id']==_fp(origin),'ORIGIN_EXECUTION_BINDING_CONFLICT')
    _require(s['ledger_close']==_close(origin,e['ledger_close_proof'],e['observed_until']),'SAVED_CLOSE_PROOF_CONFLICT')
    _require(s['opening_unavailable_shares']==e['opening_unavailable_shares'],'SAVED_SELLABILITY_CONFLICT')
    active=[dict(order=deepcopy(o),state=deepcopy(e['order_states'][o['id']])) for o in e['order_history']
        if int(e['order_states'][o['id']]['remaining']) and e['order_states'][o['id']]['status'] not in TERMINAL]
    _require(s['unfilled_orders']==active,'SAVED_ACTIVE_ORDER_CONFLICT')
    ids=e['decision_ids'];sources=e['fact_sources'];attempts=e['reassessment_attempts']
    _require(set(sources)==set(ids),'SAVED_FACT_SOURCE_HISTORY_INCOMPLETE')
    _require(s['fact_history']==history_at(declaration_sources(e),s['through_at']),'SAVED_FACT_HISTORY_CONFLICT')
    for i,key in enumerate(ids):
        d=e['decision_records'][key];source=sources[key]
        _require(all(source[k]==d[k] for k in ('decision_at','data_cutoff')),'SAVED_FACT_DECISION_TIME_CONFLICT')
        own=next((j for j,a in enumerate(attempts) if a['outcome']=='ACCEPTED' and a['decision']['decision_id']==key),None)
        _require(d['fact_history']==history_at(declaration_sources(e,decision_ids=ids[:i+1],attempt_limit=own),d['decision_at']),
            'SAVED_DECISION_FACT_HISTORY_CONFLICT')
        _require(_time(d['decision_at'])<=_time(e['observed_until']),'FUTURE_SAVED_DECISION')
    for a in attempts:validate_request_binding(a)
    return frame


def _account_binding(source,data):
    if source['kind']=='CHECKPOINT':
        _require(set(source)=={'kind','checkpoint','expected_checkpoint_id','expected_latest_decision_id'},'EXACT_SAVED_ACCOUNT_SOURCE_REQUIRED')
        cp=source['checkpoint'];e=cp['execution_result'];s=cp['state'];row=s['row'];latest=e['latest_decision_id']
        _require(source['expected_checkpoint_id']==cp['checkpoint_id'] and source['expected_latest_decision_id']==latest,'EXACT_SAVED_LATEST_PREDECESSOR_REQUIRED')
        _require(not s['unfilled_orders'] and row['purchase_payable']=='0','SAVED_ACTION_START_NOT_SETTLED')
        _require(_time(data['decision_at'])>=_time(s['ledger_close']['available_at']) and data['data_cutoff']==s['through_at'],
            'SAVED_ACTION_START_NOT_YET_KNOWN')
        account=data['account']
        _require(account['as_of']==s['through_at'] and account['settled_cash']==row['settled_cash']
            and account['reserved_cash']==s['general_reserved_cash'] and account['cash_claims']==row['cash_claims']
            and account['share_claims']==row['share_receivables'] and not account['pending_orders'] and not account['payables'],
            'SAVED_ACCOUNT_RIGHTS_OR_RESERVE_CONFLICT')
        _require(set(account['holdings'])==set(row['shares']) and all(account['holdings'][c]['shares']==n for c,n in row['shares'].items()),
            'SAVED_HOLDINGS_CONFLICT')
        binding=dict(kind='CHECKPOINT',qualification='ORIGINAL_SYNTHETIC_CHECKPOINT_NOT_INVESTOR_AUTHORITY',checkpoint_id=cp['checkpoint_id'],
            origin_ledger_input_id=cp['integrity']['origin_ledger_input_id'],origin_initial_capital=s['origin_initial_capital'],latest_predecessor_id=latest,
            latest_common_account_id=e['latest_common_account_id'],accepted_fill_ids=[f['id'] for f in s['accepted_fills']],
            closed_order_states=deepcopy(s['order_states']),reviewed_evidence_tokens=sorted(set(s['reviewed_evidence_tokens']) |
                set(e['decision_records'][latest]['reviewed_evidence_tokens'])))
        return binding,cp
    _require(source['kind']=='DECLARED_SYNTHETIC_OPENING' and set(source)=={'kind','account','consumed_evidence_tokens'},'SUPPORTED_SAVED_ACCOUNT_SOURCE_REQUIRED')
    _require(data['account']==source['account'] and data['consumed_evidence_tokens']==source['consumed_evidence_tokens'],'SAVED_DECLARED_ACCOUNT_CONFLICT')
    return dict(kind=source['kind'],qualification='DECLARED_SYNTHETIC_OPENING_NOT_A_CONTINUOUS_CHAIN',checkpoint_id=None,
        origin_ledger_input_id=None,origin_initial_capital=None,latest_predecessor_id=None,accepted_fill_ids=[],closed_order_states={},
        reviewed_evidence_tokens=sorted(source['consumed_evidence_tokens'])),None


def _action(saved):
    request=saved['action_request'];receipt=saved['action_result'];r=receipt['run']
    _require(set(request)=={'schema','synthetic','action_input','checked_action','expected_checked_action_id','execution_spec'}
        and request['schema'] in ('capital-cash-action-execution-input/0.1','capital-cash-action-execution-input/0.2')
        and request['synthetic'] is True,'SUPPORTED_FULL_SAVED_ACTION_REQUEST_REQUIRED')
    version=request['schema'].rsplit('/',1)[1];original=request['action_input'];checked=request['checked_action'];c=checked['research']
    _require(original['schema']=='capital-cash-action-input/'+version and c['schema']=='capital-cash-action/'+version
        and r['schema']=='capital-cash-action-execution/'+version,'SAVED_ACTION_VERSION_CONFLICT')
    _research(c);_research(r)
    _require(r['status']=='REPLAYED_EXPLICIT_ACTION' and r['execution_calls']==1 and c['status']=='CURRENTLY_FEASIBLE'
        and c['intent']['feasible_for_research'] is True,'INCOMPLETE_SAVED_ACTION')
    _require(request['expected_checked_action_id']==_fp(checked) and checked['source_integrity_metadata']['full_request_id']==_fp(original),
        'SAVED_CHECKED_ACTION_BINDING_CONFLICT')
    spec=request['execution_spec'];data=checked['source_integrity_metadata']['derived_decision_input'];d=c['core_decision'];intent=c['intent']
    _require(original['synthetic'] is True and data['synthetic'] is True,'EXPLICIT_SYNTHETIC_SAVED_ACTION_REQUIRED')
    _require(intent['external_action']==original['action'] and c['research_recommendation']['candidate_ids']==[intent['evaluated_plan_id']]
        and not intent['batch_gate_reasons'],'SAVED_ACTION_GATE_CONFLICT')
    _require(receipt['source_integrity_metadata']==dict(full_request_id=_fp(request),origin_ledger_input_id=_fp(spec['origin_ledger']),
        external_execution_spec_id=_fp(spec)),'SAVED_FULL_REQUEST_BINDING_CONFLICT')
    account_binding,parent=_account_binding(original['account_source'],data)
    _require(c['account_binding']==account_binding,'SAVED_CHECKED_ACCOUNT_BINDING_CONFLICT')
    _require(sorted(data['consumed_evidence_tokens'])==account_binding['reviewed_evidence_tokens'],'SAVED_INHERITED_TOKEN_CONFLICT')
    _require(r['binding']==dict(checked_action_id=_fp(checked),action_input_id=_fp(original),decision_id=d['decision_id'],
        common_account_id=d['common_account_id'],evaluated_plan_id=intent['evaluated_plan_id'],account=account_binding),'SAVED_RESULT_BINDING_CONFLICT')
    _require(_fp(data['account'])==d['common_account_id'] and all(data[k]==d[k] for k in ('decision_at','data_cutoff')),'SAVED_DECISION_ACCOUNT_CONFLICT')
    p=next((x for x in d['layer3']['alternatives'] if x['id']==intent['evaluated_plan_id']),None)
    _require(p is not None and p==intent['core_evaluation'] and p['feasible'] is True,'SAVED_PLAN_APPROVAL_CONFLICT')
    if intent['plan'] is not None:_require(data['plans']==[intent['plan']] and p['targets']==intent['plan']['targets'],'SAVED_PLAN_TARGET_CONFLICT')
    job=dict(schema='capital-execution-input/0.1',decision_input=deepcopy(data),plan_id=intent['evaluated_plan_id'],
        ledger_input=deepcopy(spec['origin_ledger']),ledger_close_proof=deepcopy(spec['ledger_close_proof']),orders=deepcopy(spec['orders']),
        tape=deepcopy(spec['tape']),observed_until=spec['observed_until'])
    frames=[]
    if parent is not None:
        e=parent['execution_result'];latest=e['latest_decision_id']
        _require(parent['origin_ledger_input']==spec['origin_ledger'] and e['ledger_close_proof']==spec['ledger_close_proof'],
            'SAVED_ORIGINAL_BOOK_CHANGED')
        job['continuation']=dict(previous_decision=dict(decision=deepcopy(e['decision_records'][latest])),checkpoint=deepcopy(parent),cancelled_order_ids=[])
        _require(d['continuity']['checkpoint_id']==parent['checkpoint_id'] and d['continuity']['latest_predecessor_id']==latest,
            'SAVED_DECISION_PREDECESSOR_CONFLICT')
        frames.append(_pair(e,parent,'/action_request/action_input/account_source/checkpoint/execution_result'))
    else:
        a=data['account'];_require(spec['origin_ledger']['opening']==dict(cash=a['settled_cash'],shares={k:v['shares'] for k,v in a['holdings'].items()},
            cash_claims=a['cash_claims'],share_claims=a['share_claims']),'SAVED_OPENING_BOOK_CHANGED')
    _require(job==r['execution_job'],'SAVED_EXECUTION_JOB_CONFLICT')
    e=r['execution'];cp=r['checkpoint']
    try:declared=source_snapshot(data)
    except ValueError as exc:raise ValueError('SAVED_DECLARED_SOURCE_CONFLICT') from exc
    _require(e['fact_sources'][d['decision_id']]==declared,'SAVED_DECLARED_SOURCE_CONFLICT')
    _require(set(data['assets'])==set(spec['origin_ledger']['assets']) and all(
        data['assets'][code][key]==asset[key] for code,asset in spec['origin_ledger']['assets'].items()
        for key in ('source_id','basis_id')),'SAVED_LEDGER_ASSET_SOURCE_CONFLICT')
    _require(e['observed_until']==spec['observed_until'] and e['orders']==spec['orders'] and e['ledger_close_proof']==spec['ledger_close_proof']
        and e['decision_id']==d['decision_id'] and e['common_account_id']==d['common_account_id']
        and e['decision_records'][d['decision_id']]==d,'SAVED_EXECUTION_ACTION_CONFLICT')
    expected=dict(decision=deepcopy(d),fills=deepcopy(e['fills']),new_fill_ids=deepcopy(e['new_fill_ids']),events=deepcopy(e['execution_events']),
        order_states=deepcopy(e['order_states']),risk_observations=deepcopy(e['risk_observations']),ledger=deepcopy(e['ledger']),checkpoint_state=deepcopy(cp['state']))
    _require(r['numeric_result']==expected,'SAVED_NUMERIC_RESULT_CONFLICT')
    frames.append(_pair(e,cp,'/action_result/run/execution'))
    return frames,job


def _continuation(saved,frames,original_job):
    item=saved['continuation']
    _require(set(item)=={'request','result'},'EXACT_SAVED_CONTINUATION_PAIR_REQUIRED')
    q=item['request'];r=item['result'];prior=frames[-1];cp=prior['checkpoint'];old=prior['execution']
    _require(set(q)=={'schema','synthetic','root_job','checkpoint','expected_checkpoint_id','expected_latest_decision_id','path',
        'expected_path_id','segment_tape','observed_until','resume_at'} and q['schema']=='capital-standing-order-resume-input/0.1'
        and q['synthetic'] is True and r['schema']=='capital-standing-order-resume/0.1' and r['status']=='CONTINUED_ORIGINAL_ORDERS',
        'SUPPORTED_SAVED_CONTINUATION_REQUIRED')
    _research(r);_signed(r,'result_id')
    _require(q['checkpoint']==cp and q['expected_checkpoint_id']==cp['checkpoint_id'] and q['expected_latest_decision_id']==old['latest_decision_id'],
        'SAVED_CONTINUATION_PREDECESSOR_CONFLICT')
    root=q['root_job'];path=q['path'];cut=cp['state']['through_at'];end=q['observed_until']
    prefix=deepcopy(root);prefix['observed_until']=cut;prefix['tape']=[o for o in root['tape'] if _time(o['at'])<=_time(cut)]
    _require(prefix==original_job,'SAVED_CONTINUATION_ACTION_ROOT_CONFLICT')
    _require(path['schema']=='capital-synthetic-order-path/0.1' and path['version']=='frozen-synthetic-path/0.1'
        and path['qualification']=='EXPLICIT_SYNTHETIC_COMPLETE_PATH_NOT_MARKET_PROOF' and q['expected_path_id']==_fp(path)
        and path['origin_ledger_input_id']==_fp(root['ledger_input']) and path['observations']==root['tape']
        and path['start_at']==root['decision_input']['data_cutoff'] and path['through_at']==root['observed_until'],'SAVED_CONTINUATION_PATH_CONFLICT')
    times=[_time(o['at']) for o in path['observations']]
    _require(times==sorted(set(times)) and all(_time(path['start_at'])<t<=_time(path['through_at']) for t in times),'SAVED_PATH_OBSERVATIONS_CONFLICT')
    days=[x['date'] for x in root['ledger_input']['calendar'] if x['trading'] and path['start_at'][:10]<x['date']<=path['through_at'][:10]]
    _require([x['date'] for x in path['session_coverage']]==days and all(x['qualification']=='EXPLICIT_SYNTHETIC_COMPLETE_EXECUTION_OPPORTUNITIES'
        and x['no_other_execution_opportunities'] is True and bool(x['source_ids']) and x['observation_ids']==[_fp(o) for o in root['tape'] if o['at'][:10]==x['date']]
        for x in path['session_coverage']) and all(o['at'][:10] in days for o in path['observations']),'SAVED_PATH_COVERAGE_INCOMPLETE')
    for source in [path]+path['session_coverage']:
        _require(bool(source['source_ids']) and all(root['ledger_input']['sources'][k]['kind']=='ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET'
            for k in source['source_ids']),'NON_SYNTHETIC_PATH_SOURCE')
    _require(_time(cut)<_time(end)<=_time(path['through_at']) and _time(cp['state']['ledger_close']['available_at'])<=_time(q['resume_at'])<=_time(end),
        'SAVED_CONTINUATION_TIME_CONFLICT')
    tail=[o for o in path['observations'] if _time(cut)<_time(o['at'])<=_time(end)]
    remaining=[o for o in path['observations'] if _time(o['at'])>_time(cut)]
    _require(q['segment_tape']==tail and (not remaining or _time(q['resume_at'])<=_time(remaining[0]['at'])),'SAVED_CONTINUATION_GAP')
    _require(r['integrity']==dict(root_job_id=_fp(root),path_id=_fp(path),predecessor_checkpoint_id=cp['checkpoint_id'],
        predecessor_latest_id=old['latest_decision_id']),'SAVED_CONTINUATION_INTEGRITY_CONFLICT')
    e=r['execution']
    _require(e['ledger_close_proof']==root['ledger_close_proof'],'SAVED_CONTINUATION_ORIGINAL_PROOF_CHANGED')
    for key in ('decision_id','common_account_id','opening_checkpoint_id','opening_unavailable_shares','orders'):
        _require(e[key]==old[key],'SAVED_CONTINUATION_CHANGED_ORIGINAL_IDENTITY:'+key)
    _require(e['observed_until']==end and r['new_fill_ids_this_segment']==[f['id'] for f in e['fills'][len(old['fills']):]],'SAVED_CONTINUATION_END_CONFLICT')
    for key in ('decision_ids','decision_records','latest_decision_id','fact_sources','reassessment_attempts','reviewed_evidence_tokens','order_history'):
        _require(e[key]==old[key],'SAVED_CONTINUATION_CHANGED_ORIGINAL_HISTORY:'+key)
    frames.append(_pair(e,r['checkpoint'],'/continuation/result/execution'))


def _snapshots(saved):
    _require(isinstance(saved,dict) and set(saved)=={'schema','action_request','action_result','continuation'} and saved['schema']==SOURCE,
        'COMPLETE_SAVED_ACTION_SOURCE_REQUIRED')
    frames,job=_action(saved)
    if saved['continuation'] is not None:_continuation(saved,frames,job)
    _chain(frames)
    for old,new in zip(frames,frames[1:]):
        for key,value in old['execution']['fact_sources'].items():
            _require(new['execution']['fact_sources'].get(key)==value,'SAVED_FACT_SOURCE_CHANGED')
    last=frames[-1]
    summary=dict(status='READABLE',source=dict(schema=saved['action_result']['run']['schema'],view='LATEST_SAVED_SNAPSHOT'),account=_account(last))
    return [(f['execution'],f['checkpoint']) for f in frames],summary
