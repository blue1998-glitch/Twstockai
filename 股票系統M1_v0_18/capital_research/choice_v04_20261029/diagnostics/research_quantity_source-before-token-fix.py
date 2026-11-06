"""Standard-library saved 0.4 source binding. No numeric producer or IO imports."""
from copy import deepcopy
from decimal import Decimal
from .lifecycle import FLAGS,_fp,_integer,_time,_snapshot,_signed

SOURCE='capital-saved-quantity-source/0.1'
FOUND={'FOUND','FOUND_ZERO_ADDITION'}
ELIGIBLE={'CURRENTLY_FEASIBLE','WAIT_SETTLEMENT_REASSESSMENT'}

def _require(ok,reason):
    if not ok:raise ValueError(reason)

def _whole(value):
    return _integer(value)

def validate_binding(binding):
    """Validate only saved components; never recreate a decision or candidate."""
    a=binding['account_snapshot'];d=binding['quantity_domain'];identities=binding['asset_identities']
    _require(_fp(a)==binding['account_id'],'SAVED_ACCOUNT_BINDING_CONFLICT')
    _require(binding['versions']['source_wrapper']==SOURCE and binding['versions']['generation']=='capital-quantity-candidates/0.4',
        'SAVED_V04_SOURCE_VERSION_REQUIRED')
    _require(d['schema']=='capital-quantity-domain/0.1' and _fp(d)==binding['quantity_domain_id'] and d['account_id']==binding['account_id'],
        'SAVED_QUANTITY_DOMAIN_BINDING_CONFLICT')
    _require(bool(d['version']) and bool(d['parameter_source']) and _time(d['available_at'])<=_time(binding['decision_at']),
        'SAVED_QUANTITY_DOMAIN_PROVENANCE_CONFLICT')
    _require(set(identities)==set(a['holdings']) and len(d['assets'])==2 and set(d['assets'])<=set(identities),
        'SAVED_UNIT_ASSETS_CONFLICT')
    for c,row in d['assets'].items():
        _require(row['code']==c and all(row[k]==identities[c][k] for k in ('source_id','basis_id','adjustment_version')),
            'SAVED_UNIT_SOURCE_CONFLICT')
        _require(bool(row['channel_id']) and _whole(row['unit_shares'])>0 and _time(row['available_at'])<=_time(binding['decision_at']),
            'SAVED_UNIT_PROVENANCE_CONFLICT')
    policy=binding['full_search_policy'];receipt=binding['full_search_receipt'];status=binding['full_proposal_status']
    _require(policy['schema']=='capital-full-unit-search/0.1' and bool(policy['version']) and bool(policy['parameter_source']) and
        _time(policy['available_at'])<=_time(binding['decision_at']) and _whole(policy['max_probes'])>0,
        'SAVED_FULL_SEARCH_POLICY_CONFLICT')
    _require(status==receipt['status'] and receipt['configured_max_probes']==_whole(policy['max_probes']) and
        receipt['implementation_max_probes']==20000,'SAVED_FULL_SEARCH_RECEIPT_CONFLICT')
    _require(status in FOUND|{'NO_FEASIBLE_TARGET','NOT_IMPLEMENTED','REJECTED_DOMAIN','REJECTED_PRECONDITION'},
        'COMPLETE_SAVED_FULL_SEARCH_REQUIRED')
    trace=receipt['probe_trace'];count=receipt['probe_count'];limit=receipt['legal_candidate_count']
    _require(type(count) is int and count==len(trace) and 0<=count<=min(_whole(policy['max_probes']),20000),
        'SAVED_FULL_SEARCH_COUNT_CONFLICT')
    if trace:
        _require(type(limit) is int and 0<count<=limit<=min(_whole(policy['max_probes']),20000),
            'SAVED_FULL_SEARCH_BOUND_CONFLICT')
        unit=_whole(receipt['unit_B']);original=_whole(receipt['original_B']);upper=_whole(receipt['upper_total_B'])
        _require(unit>0 and limit==(upper-original)//unit+1,'SAVED_FULL_SEARCH_DOMAIN_CONFLICT')
        for i,p in enumerate(trace):
            _require(_whole(p['additional_B'])==(limit-1-i)*unit and
                any(_whole(p['targets'][c])==original+_whole(p['additional_B']) for c in d['assets']),
                'SAVED_FULL_SEARCH_SEQUENCE_CONFLICT')
            _require(p['feasible_for_research'] is (p['classification'] in ELIGIBLE) and
                (not p['feasible_for_research'] or not p['reasons']), 'SAVED_FULL_SEARCH_TRACE_QUALIFICATION_CONFLICT')
        _require(all(p['feasible_for_research'] is False for p in trace[:-1]),'SAVED_FULL_SEARCH_EARLY_ENDPOINT_CONFLICT')
    if status in FOUND:
        _require(bool(trace) and trace[-1]['feasible_for_research'] is True and receipt['selected_target']==trace[-1]['targets'],
            'SAVED_FULL_SEARCH_ENDPOINT_CONFLICT')
        _require((_whole(trace[-1]['additional_B'])==0)==(status=='FOUND_ZERO_ADDITION'),'SAVED_FULL_SEARCH_ZERO_ADDITION_CONFLICT')
    else:
        _require(receipt['selected_target'] is None and all(p['feasible_for_research'] is False for p in trace),
            'SAVED_FULL_SEARCH_REFUSAL_CONFLICT')
        if status=='NO_FEASIBLE_TARGET':_require(count==limit,'INCOMPLETE_SAVED_FULL_SEARCH')
    _require(binding['source_kind'] in ('CHECKPOINT_EPISODE','DECLARED_SYNTHETIC_OPENING'),'EXPLICIT_SAVED_ACCOUNT_ORIGIN_REQUIRED')
    if binding['source_kind']=='DECLARED_SYNTHETIC_OPENING':
        _require(all(binding[k] is None for k in ('checkpoint_id','state_id','execution_result_id','origin_ledger_input_id',
            'origin_initial_capital','latest_decision_id','latest_common_account_id')) and
            binding['historical_reviewed_tokens']==[] and binding['received_attempt_ids']==[],'FAKE_OPENING_PREDECESSOR_CONFLICT')
    else:
        _require(all(binding[k] is not None for k in ('checkpoint_id','state_id','execution_result_id','origin_ledger_input_id',
            'origin_initial_capital','latest_decision_id','latest_common_account_id')) and
            set(binding['historical_reviewed_tokens'])<=set(binding['decision_reviewed_tokens']),'SAVED_TOKEN_HISTORY_CONFLICT')
    return binding

def validate_selected(candidate,binding,*,roles):
    """Retain unit/receipt semantics on SELECT and READ; not a financial replay."""
    validate_binding(binding)
    _require(candidate['unit_gate_reasons']==[],'SAVED_UNIT_QUALIFICATION_CONFLICT')
    account=binding['account_snapshot'];targets=candidate['plan']['targets'];domain=binding['quantity_domain']['assets']
    _require(set(targets)==set(account['holdings']),'SAVED_TARGET_ASSETS_CONFLICT')
    for c,n in targets.items():
        _whole(n)
        if c not in domain:_require(n==account['holdings'][c]['shares'],'OTHER_ASSET_TARGET_CHANGED')
    # Roles are explicit producer fields, never inferred from a matching quantity.
    a,b=roles['incumbent'],roles['destination']
    _require(a!=b and set(domain)=={a,b},'SAVED_UNIT_ASSETS_CONFLICT')
    sold=_whole(account['holdings'][a]['shares'])-_whole(targets[a]);added=_whole(targets[b])-_whole(account['holdings'][b]['shares'])
    _require(sold>=0 and added>=0 and sold%_whole(domain[a]['unit_shares'])==0 and added%_whole(domain[b]['unit_shares'])==0,
        'SAVED_TARGET_OUTSIDE_DECLARED_UNIT')
    _require(_whole(candidate['sold_A'])==sold and _whole(candidate['additional_B'])==added,'SAVED_TARGET_DELTA_CONFLICT')
    _require(candidate['core_evaluation']['common_account_id']==binding['account_id'],'SELECTED_ACCOUNT_CONFLICT')
    if 'FULL_TRANSFER' in candidate['kinds']:
        receipt=binding['full_search_receipt']
        _require(binding['full_proposal_status'] in FOUND and targets==receipt['selected_target'] and
            candidate['classification']==receipt['probe_trace'][-1]['classification'] and
            candidate['core_decision_id']==receipt['probe_trace'][-1]['core_decision_id'], 'SAVED_FULL_CANDIDATE_CONFLICT')
    receipt=binding['full_search_receipt']
    if receipt['probe_trace']:
        _require(receipt['original_B']==account['holdings'][b]['shares'] and receipt['sell_A']==account['holdings'][a]['shares'] and
            receipt['unit_B']==domain[b]['unit_shares'],'SAVED_FULL_SEARCH_ROLES_CONFLICT')
        for point in receipt['probe_trace']:
            _require(point['targets']=={c:'0' if c==a else str(_whole(account['holdings'][b]['shares'])+_whole(point['additional_B'])) if c==b else
                v['shares'] for c,v in account['holdings'].items()},'SAVED_FULL_SEARCH_TARGET_CONFLICT')
    return candidate

def bind_source(saved):
    _require(set(saved)=={'schema','synthetic','quantity_request','generation'} and saved['schema']==SOURCE and saved['synthetic'] is True,
        'COMPLETE_EXPLICIT_V04_SOURCE_REQUIRED')
    q=saved['quantity_request'];g=saved['generation'];r=g['research'];data=q['decision_input'];base=r['baseline'];account=data['account']
    _require(q['schema']=='capital-quantity-candidates-input/0.4' and q['synthetic'] is True and data['synthetic'] is True and
        r['schema']=='capital-quantity-candidates/0.4' and r['synthetic'] is True and r['status']=='COMPLETE' and r['enumeration_complete'] is True,
        'COMPLETE_SAVED_V04_GENERATION_REQUIRED')
    _require(g['source_integrity_metadata']['full_request_id']==_fp(q) and g['source_integrity_metadata']['original']==data['source_integrity_metadata'],
        'SAVED_QUANTITY_REQUEST_CONFLICT')
    _require(all(r[k] is False and base[k] is False for k in FLAGS) and r['primary_pressure_id'] is None and base['primary_pressure_id'] is None and
        r['ranking'] is None and r['selected_id'] is None and r['order_generation']==r['execution']=='NOT_PERFORMED','RESEARCH_ONLY_SOURCE_REQUIRED')
    _signed(base,'decision_id')
    _require(_fp(account)==r['common_account_id']==base['common_account_id'] and base['reserved_cash']==account['reserved_cash'],
        'SAVED_ACCOUNT_BINDING_CONFLICT')
    _require(base['data_cutoff']==data['data_cutoff'] and base['decision_at']==data['decision_at'] and
        _time(account['as_of'])<=_time(data['data_cutoff'])<=_time(data['decision_at']) and
        _time(account['available_at'])<=_time(data['decision_at']),'SAVED_CUTOFF_BINDING_CONFLICT')
    _require(r['quantity_domain']==q['quantity_domain'] and r['quantity_domain_id']==_fp(q['quantity_domain']) and
        r['full_search_policy']==q['full_search'],'SAVED_DOMAIN_OR_SEARCH_POLICY_CONFLICT')
    a,b=q['incumbent'],q['destination']
    _require(a!=b and set(q['quantity_domain']['assets'])=={a,b},'SAVED_UNIT_ASSETS_CONFLICT')
    cs=r['candidates'];_require(len({c['id'] for c in cs})==len(cs),'CANDIDATE_ID_NOT_UNIQUE')
    continuation=q['continuation'];cp=continuation['checkpoint'] if continuation is not None else None
    e=cp['execution_result'] if cp else None;s=cp['state'] if cp else None
    kind='CHECKPOINT_EPISODE' if cp else 'DECLARED_SYNTHETIC_OPENING'
    _require(q['batch_context']['origin']==kind and q['batch_context']['account_id']==_fp(account),'SAVED_BATCH_ORIGIN_CONFLICT')
    if cp:
        _snapshot(e,cp,'/quantity_request/continuation/checkpoint')
        _require(_fp(cp['origin_ledger_input'])==e['origin_ledger_input_id'],'SAVED_ORIGIN_FINGERPRINT_CONFLICT')
        _require(not s['unfilled_orders'] and Decimal(s['row']['purchase_payable']).is_zero() and
            all(_whole(n)==0 for n in s['opening_unavailable_shares'].values()) and continuation['cancelled_order_ids']==[],
            'SAVED_CHECKPOINT_STATE_NOT_SUPPORTED')
        previous=continuation['previous_decision']['decision'];link=base['continuity'];row=s['row']
        _require(previous==e['decision_records'][e['latest_decision_id']] and link['latest_predecessor_id']==e['latest_decision_id'] and
            link['checkpoint_id']==cp['checkpoint_id'] and link['state_id']==cp['state_id'] and
            link['origin_initial_capital']==s['origin_initial_capital'] and link['external_flow']=='0','SAVED_LATEST_BINDING_CONFLICT')
        _require(data['data_cutoff']==s['through_at'] and _time(data['decision_at'])>_time(s['through_at']) and
            _time(data['decision_at'])>=_time(s['ledger_close']['available_at']),'SAVED_CLOSE_NOT_YET_AVAILABLE')
        _require(account['as_of']==s['through_at'] and account['available_at']==data['decision_at'] and
            account['settled_cash']==row['settled_cash'] and account['reserved_cash']==s['general_reserved_cash'] and
            account['cash_claims']==row['cash_claims'] and account['share_claims']==row['share_receivables'] and
            account['holdings']=={c:dict(shares=n,sellable=n) for c,n in row['shares'].items()} and
            account['payables']==account['pending_orders']==[],'SAVED_ACCOUNT_ROW_CONFLICT')
        _require(set(s['reviewed_evidence_tokens'])<=set(data['consumed_evidence_tokens']) and
            set(s['reviewed_evidence_tokens'])<=set(base['reviewed_evidence_tokens']),'SAVED_TOKEN_HISTORY_CONFLICT')
    else:
        _require('continuity' not in base,'FAKE_OPENING_PREDECESSOR_CONFLICT')
    binding=dict(source_document_id=_fp(saved),generation_document_id=_fp(g),quantity_request_id=_fp(q),source_input_id=_fp(q),
        baseline_document_id=_fp(base),account_id=_fp(account),account_snapshot=deepcopy(account),source_kind=kind,
        checkpoint_id=cp['checkpoint_id'] if cp else None,state_id=cp['state_id'] if cp else None,
        execution_result_id=e['result_id'] if e else None,origin_ledger_input_id=e['origin_ledger_input_id'] if e else None,
        origin_initial_capital=s['origin_initial_capital'] if s else None,
        latest_decision_id=e['latest_decision_id'] if e else None,latest_common_account_id=e['latest_common_account_id'] if e else None,
        data_cutoff=data['data_cutoff'],decision_at=data['decision_at'],historical_reviewed_tokens=deepcopy(s['reviewed_evidence_tokens']) if s else [],
        decision_reviewed_tokens=deepcopy(base['reviewed_evidence_tokens']),received_attempt_ids=[a['attempt_id'] for a in e['reassessment_attempts']] if e else [],
        fact_history_id=_fp(base['fact_history']),quantity_domain=deepcopy(q['quantity_domain']),quantity_domain_id=_fp(q['quantity_domain']),
        asset_identities={c:{k:v[k] for k in ('source_id','basis_id','adjustment_version')} for c,v in data['assets'].items()},
        full_search_policy=deepcopy(q['full_search']),full_search_receipt=deepcopy(r['full_search_receipt']),full_proposal_status=r['full_proposal_status'],
        versions=dict(source_wrapper=saved['schema'],generation=r['schema'],checkpoint=cp['schema'] if cp else None,decision=base['schema']))
    validate_binding(binding)
    full=[c for c in cs if 'FULL_TRANSFER' in c['kinds']];_require(len(full)==1,'SAVED_FULL_CANDIDATE_NOT_UNIQUE')
    if binding['full_proposal_status'] in FOUND:validate_selected(full[0],binding,roles=dict(incumbent=a,destination=b))
    else:_require(full[0]['plan'] is None and full[0]['feasible_for_research'] is False,'SAVED_UNAVAILABLE_FULL_CONFLICT')
    return binding
