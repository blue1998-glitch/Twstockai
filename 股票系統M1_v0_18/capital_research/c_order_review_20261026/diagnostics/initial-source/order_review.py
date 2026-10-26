"""Narrow proof of already-approved C order use, never a new-batch approval."""
from copy import deepcopy
from .core import fingerprint, quantity, timestamp, evidence_tokens, BINDING
from .fact_lineage import body, issues
from .eligibility import validity_status

SCHEMA='capital-same-order-scope/0.1'
DECISION='capital-decision/0.9'


def _require(condition,reason):
    if not condition:raise ValueError(reason)


def _original(execution,order):
    rows=[d for d in execution['decision_records'].values() if d['decision_at']==order['decision_at']]
    _require(len(rows)==1,'SAME_ORDER_ORIGINAL_DECISION_REQUIRED')
    return rows[0]


def _trigger_bindings(execution,original,plan,code,asset):
    result=[]
    rows=execution['fact_sources'][original['decision_id']]['records']
    for key in plan['trigger_ids']:
        facts=[r for r in rows if r['identity']['code']==code and r['identity']['kind']=='EVIDENCE' and r['identity']['id']==key]
        _require(len(facts)==1,'SAME_ORDER_ORIGINAL_TRIGGER_NOT_OWNED')
        r=facts[0];_require(all(r['identity'][k]==asset[k] for k in BINDING),'SAME_ORDER_SOURCE_BASIS_CHANGED')
        tokens=evidence_tokens(r['fact'])
        _require(tokens<=set(original['new_evidence_tokens']),'SAME_ORDER_TRIGGER_WAS_NOT_NEW_AT_APPROVAL')
        result.append(dict(identity=deepcopy(r['identity']),tokens=sorted(tokens),body_id=fingerprint(body(r['fact']))))
    return result


def build_scope(previous,data,checkpoint,order_id):
    # resume_decision has already validated the exact latest account/checkpoint.
    e=checkpoint['execution_result'];orders=e['order_history']
    order=next((o for o in orders if o['id']==order_id),None)
    _require(order is not None and order['side']=='BUY','SAME_ORDER_CONDITIONAL_BUY_REQUIRED')
    st=e['order_states'][order_id]
    _require(st['requires_reassessment'] is True and quantity(st['remaining'])>0 and not st['status'].startswith(('CANCELLED','EXPIRED')),
        'SAME_ORDER_CONDITIONAL_BUY_REQUIRED')
    _require([x['order']['id'] for x in checkpoint['state']['unfilled_orders']]==[order_id],
        'SAME_ORDER_SINGLE_LIVE_ORDER_REQUIRED')
    _require(timestamp(data['decision_at'])<timestamp(order['expires_at']),'SAME_ORDER_EXPIRED')
    _require(len(data['plans'])==1,'SAME_ORDER_ONLY_ONE_PLAN_ALLOWED')
    fresh=data['plans'][0];original=_original(e,order)
    p=next((p for p in original['layer3']['alternatives'] if p['id']==fresh['id']),None)
    _require(p is not None and p['feasible'] and p['family']=='C' and p['route']=='R1' and p['trigger_ids'] and len(set(p['trigger_ids']))==len(p['trigger_ids']),
        'SAME_ORDER_ORIGINAL_C_APPROVAL_REQUIRED')
    _require(all(fresh[k]==p[k] for k in ('id','family','route','trigger_ids','conditions')),'SAME_ORDER_PLAN_OR_TRIGGER_CHANGED')
    code=order['code'];target={c:quantity(v['shares']) for c,v in data['account']['holdings'].items()}
    target[code]+=quantity(st['remaining'])
    _require({c:quantity(n) for c,n in fresh['targets'].items()}==target,'SAME_ORDER_TARGET_OR_QUANTITY_CHANGED')
    opening=next(p for p in original['layer3']['alternatives'] if p['id']=='A-zero')['targets']
    _require(quantity(st['remaining'])<=quantity(order['shares'])<=quantity(p['targets'][code])-quantity(opening[code]),
        'SAME_ORDER_ORIGINAL_QUANTITY_CONFLICT')
    bindings=_trigger_bindings(e,original,p,code,data['assets'][code])
    tokens=sorted(set().union(*(set(b['tokens']) for b in bindings)))
    _require(set(tokens)<=set(checkpoint['state']['reviewed_evidence_tokens']),'SAME_ORDER_APPROVAL_TOKEN_HISTORY_LOST')
    scope=dict(schema=SCHEMA,order_id=order_id,order_fingerprint=fingerprint(order),code=code,
        original_decision_id=original['decision_id'],plan_id=p['id'],trigger_ids=deepcopy(p['trigger_ids']),
        trigger_bindings=bindings,original_trigger_tokens=tokens,original_order_quantity=order['shares'],
        remaining=st['remaining'],fill_ids_at_review=[f['id'] for f in e['fills'] if e['fill_order_ids'][f['id']]==order_id],
        checkpoint_id=checkpoint['checkpoint_id'],latest_predecessor_id=previous['decision']['decision_id'],
        account_id=fingerprint(data['account']),origin_ledger_input_id=e['origin_ledger_input_id'],
        use='SAME_ORIGINAL_ORDER_ONLY_NOT_NEW_BATCH')
    scope['scope_id']=fingerprint(scope)
    return scope


def trigger_reasons(scope,data,history,evidence):
    code=scope['code'];asset=data['assets'][code];owned={f['id'] for f in asset['evidence']}
    for row in scope['trigger_bindings']:
        key=row['identity']['id'];f=evidence.get(key)
        if (key not in owned or f is None or any(f[k]!=asset[k] for k in BINDING) or
            fingerprint(body(f))!=row['body_id'] or issues(history,code,asset,'EVIDENCE',f,data['decision_at']) or
            validity_status(f,data['data_cutoff'],data['decision_at']) not in ('WITHIN_DECLARED_INTERVAL','ONGOING_REQUIRES_CURRENT_REVIEW')):
            return ['ORIGINAL_ORDER_TRIGGER_NOT_CURRENTLY_VALID']
    return []


def validate_saved(decision,execution):
    """Check saved proof references without building a second ledger/checkpoint."""
    if decision['schema']!=DECISION:
        _require('same_order_continuation' not in decision,'SAME_ORDER_SCOPE_REQUIRES_VERSION_0_9')
        return
    s=decision.get('same_order_continuation')
    _require(s is not None and s['schema']==SCHEMA,'SAME_ORDER_SCOPE_REQUIRED')
    _require(s['scope_id']==fingerprint({k:v for k,v in s.items() if k!='scope_id'}),'SAME_ORDER_SCOPE_FINGERPRINT_CONFLICT')
    order=next((o for o in execution['order_history'] if o['id']==s['order_id']),None)
    _require(order is not None and fingerprint(order)==s['order_fingerprint'] and order['code']==s['code'],'SAME_ORDER_SCOPE_ORDER_CONFLICT')
    original=_original(execution,order)
    _require(original['decision_id']==s['original_decision_id'],'SAME_ORDER_SCOPE_ORIGINAL_CONFLICT')
    p=next((p for p in original['layer3']['alternatives'] if p['id']==s['plan_id']),None)
    fresh=next((p for p in decision['layer3']['alternatives'] if p['id']==s['plan_id']),None)
    _require(p is not None and fresh is not None and p['family']==fresh['family']=='C' and p['route']==fresh['route']=='R1'
        and p['trigger_ids']==fresh['trigger_ids']==s['trigger_ids'],'SAME_ORDER_SCOPE_PLAN_CONFLICT')
    _require(s['original_order_quantity']==order['shares'] and s['trigger_bindings'],'SAME_ORDER_SCOPE_ORIGINAL_QUANTITY_CONFLICT')
    asset={k:s['trigger_bindings'][0]['identity'][k] for k in BINDING}
    bindings=_trigger_bindings(execution,original,p,order['code'],asset)
    tokens=sorted(set().union(*(set(b['tokens']) for b in bindings)))
    _require(bindings==s['trigger_bindings'] and tokens==s['original_trigger_tokens'],'SAME_ORDER_SCOPE_TRIGGER_CONFLICT')
    _require(s['checkpoint_id']==decision['continuity']['checkpoint_id'] and s['latest_predecessor_id']==decision['continuity']['latest_predecessor_id']
        and s['account_id']==decision['common_account_id'] and s['origin_ledger_input_id']==execution['origin_ledger_input_id'],
        'SAME_ORDER_SCOPE_PREDECESSOR_CONFLICT')
    _require(set(s['original_trigger_tokens'])<=set(decision['reviewed_evidence_tokens']),'SAME_ORDER_SCOPE_TOKENS_LOST')
    prior=[f for f in execution['fills'] if execution['fill_order_ids'][f['id']]==s['order_id'] and f['date']<=decision['data_cutoff'][:10]]
    _require(s['fill_ids_at_review']==[f['id'] for f in prior] and quantity(s['remaining'])+sum((quantity(f['shares']) for f in prior),quantity('0'))==quantity(order['shares']),
        'SAME_ORDER_SCOPE_QUANTITY_CONFLICT')
    q=next(p for p in decision['layer3']['alternatives'] if p['id']=='A-zero')['targets'];target={c:quantity(n) for c,n in q.items()};target[s['code']]+=quantity(s['remaining'])
    _require({c:quantity(n) for c,n in fresh['targets'].items()}==target,'SAME_ORDER_SCOPE_TARGET_CONFLICT')
