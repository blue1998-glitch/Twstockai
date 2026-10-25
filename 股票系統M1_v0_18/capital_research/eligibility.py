"""Point-in-time synthetic capital permission, separate from chart strength.

An explicit current review may reuse a valid older fact. It cannot revive an
expired/invalidated fact or create any data, trading or live authorization.
"""
from copy import deepcopy
from datetime import datetime


def _time(value):
    t=datetime.fromisoformat(value.replace('Z','+00:00'))
    if t.utcoffset() is None:raise ValueError('Timezone required for eligibility')
    return t


def validity_status(record, cutoff, decision):
    v=record.get('validity')
    if v is None:return 'UNSPECIFIED'
    now=_time(decision);end=_time(cutoff)
    if _time(v['available_at'])>now:return 'NOT_AVAILABLE'
    if v['schema']!='capital-fact-validity/0.1' or record['source_id'] not in v['source_ids']:
        raise ValueError('Explicit same-source synthetic validity required')
    start=_time(v['valid_from']);until=_time(v['valid_until']) if v['valid_until'] is not None else None
    if until is not None and until<=start:raise ValueError('Invalid declared validity interval')
    invalid=v['invalidation']
    if invalid is not None and _time(invalid['available_at'])<=now and _time(invalid['occurred_at'])<=now:
        if not invalid['evidence_id'] or record['source_id'] not in invalid['source_ids']:
            raise ValueError('Sourced invalidation identity required')
        return 'INVALIDATED'
    if start>end:return 'NOT_YET_VALID'
    if until is not None and now>=until:return 'EXPIRED'
    if until is None:
        if v['qualification']!='EXPLICIT_SYNTHETIC_ONGOING_REQUIRES_REVIEW':
            raise ValueError('Null expiry is not implicit perpetual qualification')
        return 'ONGOING_REQUIRES_CURRENT_REVIEW'
    if v['qualification'] not in ('EXPLICIT_SYNTHETIC_INTERVAL','EXPLICIT_SYNTHETIC_ONGOING_REQUIRES_REVIEW'):
        raise ValueError('Unsupported validity declaration')
    return 'WITHIN_DECLARED_INTERVAL'


def known_fact(record, cutoff, decision):
    """Do not put not-yet-known revocations into a decision's numeric identity."""
    r=deepcopy(record);v=r.get('validity')
    if v is not None:
        if _time(v['available_at'])>_time(decision):
            r.pop('validity');r['validity_visibility']='NOT_AVAILABLE'
        elif v['invalidation'] is not None:
            i=v['invalidation']
            if _time(i['available_at'])>_time(decision) or _time(i['occurred_at'])>_time(decision):v['invalidation']=None
    return r


def entry_review(asset, code, data, evidence):
    r=asset.get('capital_eligibility');reasons=[]
    out=dict(qualified_for_synthetic_proposal=False,reasons=reasons,review=None,
             authority='SYNTHETIC_RESEARCH_ONLY_NOT_DATA_OR_EXECUTION_AUTHORIZATION')
    if r is None:reasons.append('MISSING_CAPITAL_REVIEW');return out
    now=_time(data['decision_at']);cutoff=data['data_cutoff']
    if _time(r['available_at'])>now:reasons.append('CAPITAL_REVIEW_NOT_AVAILABLE');return out
    if r['schema']!='capital-entry-review/0.1' or r['code']!=code or any(r[k]!=asset[k] for k in ('source_id','basis_id','adjustment_version')):
        raise ValueError('Capital review source/basis/asset mismatch')
    if asset['source_id'] not in r['source_ids']:raise ValueError('Capital review source required')
    if not _time(cutoff)<=_time(r['assessed_at'])<=_time(r['available_at'])<=now:
        reasons.append('REVIEW_NOT_CURRENT_AT_DECISION')
    if r['data_cutoff']!=cutoff:reasons.append('REVIEW_CUTOFF_MISMATCH')
    if r['status'] not in ('QUALIFIED_SYNTHETIC_RESEARCH','NOT_QUALIFIED','UNKNOWN'):
        raise ValueError('Unsupported capital-review status')
    if r['status']!='QUALIFIED_SYNTHETIC_RESEARCH':reasons.append('CAPITAL_'+r['status'])
    ids=r['evidence_ids']
    if not ids or len(set(ids))!=len(ids):reasons.append('MISSING_OR_DUPLICATE_REVIEW_EVIDENCE')
    owned_ids={e['id'] for e in asset['evidence']}
    for key in ids:
        fact=evidence.get(key)
        if fact is None:
            reasons.append('REVIEW_EVIDENCE_UNKNOWN:'+key);continue
        if key not in owned_ids or any(fact[k]!=asset[k] for k in ('source_id','basis_id','adjustment_version')):
            reasons.append('REVIEW_EVIDENCE_NOT_OWNED_OR_BINDING_MISMATCH:'+key);continue
        status=validity_status(fact,cutoff,data['decision_at'])
        if status not in ('WITHIN_DECLARED_INTERVAL','ONGOING_REQUIRES_CURRENT_REVIEW'):
            reasons.append('EVIDENCE_'+status+':'+key)
    for label,fact in [('ENTRY',asset['entry_context']),('REFERENCE',asset['entry_context']['formal_reference'])]:
        if fact is None:reasons.append(label+'_UNKNOWN');continue
        status=validity_status(fact,cutoff,data['decision_at'])
        if status not in ('WITHIN_DECLARED_INTERVAL','ONGOING_REQUIRES_CURRENT_REVIEW'):
            reasons.append(label+'_'+status)
    out['review']=deepcopy(r);out['qualified_for_synthetic_proposal']=not reasons
    return out


def expired_entry_reasons(asset, at):
    """Standing orders retain approval, but explicit expiry/revocation cancels."""
    ids=set(asset.get('capital_eligibility',{}).get('evidence_ids',[]))
    facts=[('ENTRY',asset['entry_context']),('REFERENCE',asset['entry_context']['formal_reference'])]
    facts += [(e['id'],e) for e in asset['evidence'] if e['id'] in ids]
    return [label+':'+s for label,f in facts if f is not None
            for s in [validity_status(f,at,at)] if s in ('EXPIRED','INVALIDATED')]
