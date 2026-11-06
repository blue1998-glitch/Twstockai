"""Pure point-in-time fact history. No file IO, market inference or accounting.

Raw declarations may contain future revocations. Only visible projections enter
the numeric history; the raw declarations belong to execution integrity data.
"""
from copy import deepcopy
from graph_core.core import fingerprint
from .eligibility import _time, known_fact, validity_status

SCHEMA = 'capital-fact-history/0.1'
BINDING = ('source_id', 'basis_id', 'adjustment_version')


def identity(code, asset, kind, fact):
    key = fact.get('id')
    if not key and kind != 'EVIDENCE':
        # A scoped declared snapshot, NOT a certified permanent source fact ID.
        key = kind + '@' + fact['available_at'] + '|' + fact.get('occurred_at', '')
    if not isinstance(key, str) or not key:
        raise ValueError('FACT_IDENTITY_REQUIRED')
    return dict(code=code, kind=kind, id=key, **{k: asset[k] for k in BINDING})


def key_of(value):
    return fingerprint(value)


def records(data):
    result = []
    for code, asset in sorted(data['assets'].items()):
        entry = deepcopy(asset['entry_context']); ref = entry.pop('formal_reference')
        rows = [('EVIDENCE', e) for e in asset['evidence']] + [('ENTRY', entry)]
        if ref is not None: rows.append(('REFERENCE', ref))
        for kind, fact in rows:
            occurred = fact.get('occurred_at', fact['available_at'])
            if _time(occurred) > _time(data['data_cutoff']) or _time(fact['available_at']) > _time(data['decision_at']):
                continue
            if any(fact[k] != asset[k] for k in BINDING):
                raise ValueError('Fact history source/basis/adjustment mismatch')
            result.append(dict(identity=identity(code, asset, kind, fact), fact=deepcopy(fact)))
    return sorted(result, key=lambda r: key_of(r['identity']))


def source_snapshot(data):
    return dict(schema='capital-fact-declarations/0.1', decision_at=data['decision_at'],
                data_cutoff=data['data_cutoff'], records=records(data))


def visible(fact, cutoff, at):
    result = known_fact(fact, cutoff, at)
    for field in ('fact_link', 'fact_correction'):
        if field in result and _time(result[field]['available_at']) > _time(at):
            result.pop(field)
    return result


def body(fact):
    return {k: v for k, v in fact.items()
            if k not in ('id', 'validity', 'validity_visibility', 'fact_link', 'fact_correction')}


def compatible_validity(old, new):
    """Only additional knowledge or tighter restrictions; never silent revival."""
    a, b = old.get('validity'), new.get('validity')
    if a is None: return True
    if b is None: return False
    if a['valid_from'] != b['valid_from']: return False
    if a['valid_until'] is not None:
        if b['valid_until'] is None or _time(b['valid_until']) > _time(a['valid_until']): return False
    if a['invalidation'] is not None and a['invalidation'] != b['invalidation']: return False
    return True


def history_at(sources, at):
    """Reconstruct chronological knowledge from explicit prior declarations.

    Earlier decisions are never recalculated. Future declaration bytes do not
    enter observations until both their occurrence and availability are known.
    """
    events = []
    for source in sources:
        if source['schema'] != 'capital-fact-declarations/0.1':
            raise ValueError('Versioned fact declarations required')
        start = _time(source['decision_at'])
        if start > _time(at): continue
        for row in source['records']:
            fact = row['fact']; times = {start}
            v = fact.get('validity')
            if v:
                times.add(max(start, _time(v['available_at'])))
                invalid = v['invalidation']
                if invalid:
                    times.add(max(start, _time(v['available_at']), _time(invalid['occurred_at']), _time(invalid['available_at'])))
            for field in ('fact_link', 'fact_correction'):
                if field in fact: times.add(max(start, _time(fact[field]['available_at'])))
            for when in times:
                if when <= _time(at):
                    f = visible(fact, source['data_cutoff'], when.isoformat())
                    events.append((when, key_of(row['identity']), fingerprint(f), row['identity'], f))
    roots, aliases, unresolved, rejected, observations = {}, {}, {}, {}, []
    seen = set()
    for when, key, content_id, ident, fact in sorted(events, key=lambda e: e[:3]):
        if (key, content_id) in seen:
            prior = roots.get(aliases.get(key))
            # A rejected proposal is not a permanent ban on a still-valid
            # original. Re-observing its exact accepted bytes may clear only
            # that proposal rejection, never a later expiry or revocation.
            if (key not in rejected or prior is None or content_id not in prior['content_ids']
                    or body(prior['fact']) != body(fact)
                    or prior['fact'].get('validity') != fact.get('validity')):
                continue
        seen.add((key, content_id)); reasons = []
        root = aliases.get(key)
        link = fact.get('fact_link')
        if link:
            target_identity = dict(ident, id=link['target_id'])
            target = aliases.get(key_of(target_identity))
            if (link['schema'] != 'capital-fact-alias/0.1'
                    or any(link[k] != ident[k] for k in ('code', *BINDING))
                    or ident['source_id'] not in link['source_ids'] or target is None
                    or link['target_content_id'] not in roots[target]['content_ids']):
                reasons.append('FACT_ALIAS_IDENTITY_UNKNOWN')
            elif root is not None and root != target:
                reasons.append('LATE_ALIAS_MERGE_NOT_IMPLEMENTED')
            else:
                root = target; aliases[key] = target; unresolved.pop(key, None)
        if 'fact_correction' in fact:
            reasons.append('FACT_CORRECTION_NOT_IMPLEMENTED')
        if key in unresolved and not link:
            reasons.append('FACT_IDENTITY_UNRESOLVED')
        if root is None and not reasons:
            # Identical declaration under a different ID is ambiguous. Do not
            # infer identity from a shared volume bar/formation, or call it new.
            for prior in roots.values():
                scope = prior['identity']
                if (all(scope[k] == ident[k] for k in ('code', 'kind', *BINDING))
                        and body(prior['fact']) == body(fact)):
                    reasons.append('FACT_RENAME_LINK_REQUIRED'); break
        if root is not None and not reasons:
            prior = roots[root]['fact']
            if body(prior) != body(fact): reasons.append('FACT_CONTENT_REWRITE_NOT_IMPLEMENTED')
            elif not compatible_validity(prior, fact): reasons.append('FACT_VALIDITY_REWRITE_NOT_IMPLEMENTED')
        if reasons:
            rejected[key] = reasons
            if root is None: unresolved[key] = reasons
        else:
            if root is None:
                root = key; aliases[key] = key
                roots[key] = dict(identity=deepcopy(ident), fact=deepcopy(fact), content_ids=[])
            roots[root]['fact'] = deepcopy(fact)
            if content_id not in roots[root]['content_ids']:
                roots[root]['content_ids'].append(content_id)
            rejected.pop(key, None)
        observations.append(dict(observed_at=when.isoformat(), identity=deepcopy(ident),
            fact=deepcopy(fact), content_id=content_id, reasons=reasons))
    result = dict(schema=SCHEMA, observations=observations, roots=roots,
                  aliases=aliases, unresolved=unresolved, rejected=rejected)
    result['history_id'] = fingerprint(result)
    return result


def issues(history, code, asset, kind, fact, at):
    if fact is None: return ['FACT_IDENTITY_UNKNOWN']
    key = key_of(identity(code, asset, kind, fact))
    reasons = list(history['rejected'].get(key, [])) + list(history['unresolved'].get(key, []))
    root = history['aliases'].get(key)
    if root is None: reasons.append('FACT_IDENTITY_UNKNOWN')
    else:
        status = validity_status(history['roots'][root]['fact'], at, at)
        if status not in ('WITHIN_DECLARED_INTERVAL', 'ONGOING_REQUIRES_CURRENT_REVIEW'):
            reasons.append('FACT_HISTORY_' + status)
    return sorted(set(reasons))


def asset_issues(history, code, asset, at):
    ids = set(asset.get('capital_eligibility', {}).get('evidence_ids', []))
    result = []
    for fact in asset['evidence']:
        if fact['id'] in ids: result += issues(history, code, asset, 'EVIDENCE', fact, at)
    entry = deepcopy(asset['entry_context']); ref = entry.pop('formal_reference')
    result += issues(history, code, asset, 'ENTRY', entry, at)
    result += issues(history, code, asset, 'REFERENCE', ref, at)
    return sorted(set(result))


def first_issue_at(sources, code, asset, *, after, through):
    """First declared known disqualification, separate from processing time."""
    final = history_at(sources, through); candidates = {_time(after)}
    for row in final['observations']:
        if row['identity']['code'] != code: continue
        observed = _time(row['observed_at']); candidates.add(observed)
        v = row['fact'].get('validity')
        if v and v['valid_until'] is not None:
            candidates.add(max(observed, _time(v['valid_until'])))
    for when in sorted(candidates):
        if _time(after) <= when <= _time(through):
            if asset_issues(history_at(sources, when.isoformat()), code, asset, when.isoformat()):
                return when.isoformat()
    return None
