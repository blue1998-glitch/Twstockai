"""Pure P0-3 descriptions over existing reaction facts; no I/O or thresholds."""
from copy import deepcopy

from graph_core.core import fingerprint, number
from reaction_facts.core import evaluate as reaction, BINDING, day, timestamp

VERSION = 'p03-structure-state/0.1'
REQUIRED = ('PULLBACK_HIGH', 'ORIGINAL_BOX_FLOOR', 'ORIGINAL_BOX_UPPER')
ROLES = REQUIRED + ('SHALLOW_OBSERVATION',)
QUALIFICATIONS = ('HUMAN_CONFIRMED', 'RESEARCH_CANDIDATE', 'ENGINEERING_FIXTURE')
LABELS = dict(STRENGTHENING='轉強', CONSOLIDATING='整理', WEAKENING='轉弱',
              INSUFFICIENT='證據不足／不可判定')


def _errors(facts_input, scenario):
    errors = []
    refs = {r['id']: r for r in facts_input['references']}
    c = facts_input['context']
    if c.get('price_mode') not in ('RAW_CANDIDATE', 'ADJUSTED_CANDIDATE') or not c.get('adjustment_version'):
        errors.append('MISSING_OR_UNSUPPORTED_PRICE_MODE_VERSION')
    if scenario.get('schema_version') != 'p03-explicit-roles/0.1':
        errors.append('UNSUPPORTED_SCENARIO')
    if any(scenario.get('binding', {}).get(k) != c.get(k) for k in (*BINDING, 'price_mode', 'adjustment_version')):
        errors.append('SCENARIO_SOURCE_BASIS_VERSION_MISMATCH')
    roles = scenario.get('roles', {})
    for name in REQUIRED:
        if name not in roles:
            errors.append('MISSING_ROLE:' + name)
    for name, role in roles.items():
        if name not in ROLES or role.get('role') != name:
            errors.append('WRONG_SEMANTIC_ROLE:' + name)
        ref = refs.get(role.get('reference_id'))
        if ref is None:
            errors.append('MISSING_ROLE_REFERENCE:' + name)
            continue
        if role.get('qualification') not in QUALIFICATIONS or not role.get('evidence'):
            errors.append('UNQUALIFIED_ROLE:' + name)
        if timestamp(role.get('selected_at')) is None:
            errors.append('UNKNOWN_ROLE_SELECTION_TIME:' + name)
        known = day(role['known_on']); valid = day(role['valid_from'])
        if known < ref['known_on'] or valid < known:
            errors.append('ROLE_AVAILABILITY_CONFLICT:' + name)
        for key in ('valid_until', 'invalidated_on'):
            if role.get(key) is not None:
                day(role[key])
        if role.get('valid_until') and role['valid_until'] < valid:
            errors.append('ROLE_VALIDITY_CONFLICT:' + name)
        expected = {'PULLBACK_HIGH': 'high', 'ORIGINAL_BOX_FLOOR': 'low', 'ORIGINAL_BOX_UPPER': 'high'}
        if name in expected and ref['source_field'] != expected[name]:
            errors.append('WRONG_SOURCE_FIELD:' + name)
    phase = scenario.get('post_breakout_return', {})
    if phase.get('qualification') not in QUALIFICATIONS or not phase.get('evidence'):
        errors.append('MISSING_POST_BREAKOUT_RETURN_EVIDENCE')
    for key in ('breakout_on', 'return_on', 'known_on', 'context_start_on'):
        day(phase[key])
    if not phase['context_start_on'] <= phase['breakout_on'] < phase['return_on'] <= phase['known_on']:
        errors.append('POST_BREAKOUT_RETURN_DATE_CONFLICT')
    # The caller supplies a semantic hypothesis, never an automatic box choice.
    return errors


def _role_identity(role, ref, context):
    return fingerprint(dict(role=role['role'], origin_id=ref['origin_id'],
                            source_kind=ref['source_kind'], source_field=ref['source_field'],
                            source={k: ref['binding'][k] for k in ('code', 'source_id', 'price_basis_id')},
                            price_mode=context['price_mode'], adjustment_version=context['adjustment_version'],
                            role_evidence=role['evidence'], selected_at=role['selected_at']))


def evaluate(facts_input, scenario, *, as_of):
    """Describe explicit roles. Research roles remain conditional, never signals."""
    day(as_of)
    try:
        # Verify the declared original binding, but do not validate/use future K.
        if fingerprint(facts_input['bars']) != facts_input['context']['source_prefix_fingerprint']:
            raise ValueError('Source prefix fingerprint mismatch')
        errors = _errors(facts_input, scenario)
        prefix = deepcopy(facts_input)
        n = sum(r['date'] <= as_of for r in prefix['bars'])
        old_binding = deepcopy(prefix['context'])
        for r in prefix['references']:
            if any(r['binding'].get(k) != old_binding[k] for k in BINDING):
                raise ValueError('Reference source/basis/frame/prefix/code mismatch')
        prefix['bars'] = prefix['bars'][:n]; prefix['macd'] = prefix['macd'][:n]
        prefix['context']['source_prefix_fingerprint'] = fingerprint(prefix['bars'])
        for r in prefix['references']:
            r['binding']['source_prefix_fingerprint'] = prefix['context']['source_prefix_fingerprint']
        facts = reaction(prefix, as_of=as_of)
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        result = dict(schema_version=VERSION, as_of=as_of, records=[dict(
            date=as_of, state='INSUFFICIENT', label=LABELS['INSUFFICIENT'],
            reasons=['INVALID_INPUT:' + str(exc)], state_changed_on=as_of,
            price_facts={}, equal_boundaries=[], evidence={}, role_prices={})],
            events=[], reference_catalog=[], input_refusal=str(exc), source_qualification='INPUT_REFUSED')
        return _finish(result)
    refs = {r['id']: r for r in prefix['references']}
    roles = scenario.get('roles', {})
    phase = scenario['post_breakout_return']
    by_date = {r['date']: r for r in facts['records']}
    upper = roles.get('ORIGINAL_BOX_UPPER', {}).get('reference_id')
    breakout = by_date.get(phase['breakout_on'])
    breakout_fact = breakout and breakout['references'].get(upper)
    breakout_ok = bool(breakout_fact and breakout_fact['fields']['close']['transition']['kind']
                       in ('BELOW_TO_ABOVE', 'EQUAL_TO_ABOVE'))
    original_upper = roles.get('ORIGINAL_BOX_UPPER', {})
    if original_upper:
        bo = phase['breakout_on']
        breakout_ok = bool(breakout_ok and original_upper['known_on'] <= bo and
                           original_upper['valid_from'] <= bo and
                           (not original_upper.get('valid_until') or bo <= original_upper['valid_until']) and
                           (not original_upper.get('invalidated_on') or bo < original_upper['invalidated_on']))
    phase_errors = []
    if not breakout_ok:
        phase_errors.append('INITIAL_BREAKOUT_NOT_SUPPORTED_BY_CONTIGUOUS_CLOSE_FACT')
    if phase['return_on'] not in by_date:
        phase_errors.append('RETURN_SOURCE_RECORD_MISSING')
    records = []; events = []; prior = None; changed_on = None; broken_since = None
    for source in facts['records']:
        d = source['date']; why = list(errors); price_facts = {}; prices = {}; role_ids = {}
        missing = []; support = []; opposite = []
        if d >= phase['context_start_on']:
            row = source['original_bar']
            if source['continuity']['reason'] or any(row[k] is None for k in ('open', 'high', 'low', 'close')):
                broken_since = broken_since or d
        if broken_since:
            why.append('INTERRUPTED_STRUCTURE_CONTEXT_SINCE:' + broken_since)
        if d < phase['known_on']:
            why.append('POST_BREAKOUT_RETURN_NOT_YET_KNOWN')
        else:
            why += phase_errors
        for name, role in roles.items():
            ref = refs.get(role.get('reference_id'))
            if ref is None:
                continue
            valid = (d >= role['known_on'] and d >= role['valid_from'] and
                     (not role.get('valid_until') or d <= role['valid_until']) and
                     (not role.get('invalidated_on') or d < role['invalidated_on']))
            if not valid:
                if name in REQUIRED:
                    why.append('ROLE_UNAVAILABLE_OR_EXPIRED:' + name)
                continue
            role_ids[name] = _role_identity(role, ref, facts_input['context'])
            observed = source['references'][ref['id']]
            price_facts[name] = deepcopy(observed['fields'])
            if observed['fields']['close']['relation'] is None:
                if name in REQUIRED:
                    why.append('REFERENCE_NOT_COMPARABLE:' + name + ':' + observed['fields']['close']['reason'])
            else:
                prices[name] = ref['price']
        if all(k in prices for k in REQUIRED):
            if number(prices['ORIGINAL_BOX_FLOOR']) >= min(number(prices['PULLBACK_HIGH']), number(prices['ORIGINAL_BOX_UPPER'])):
                why.append('CONTRADICTORY_REFERENCE_GEOMETRY')
        elif not why:
            why.append('MISSING_REQUIRED_REFERENCE_VALUES')
        equal = [name for name, v in price_facts.items() if v['close']['relation'] == 'EQUAL']
        if why:
            state = 'INSUFFICIENT'
        elif price_facts['PULLBACK_HIGH']['close']['relation'] == 'ABOVE':
            state = 'STRENGTHENING'; why.append('CLOSE_STRICTLY_ABOVE_PULLBACK_HIGH')
        elif price_facts['ORIGINAL_BOX_FLOOR']['close']['relation'] == 'BELOW':
            state = 'WEAKENING'; why.append('CLOSE_STRICTLY_BELOW_ORIGINAL_BOX_FLOOR')
        else:
            state = 'CONSOLIDATING'; why.append('NOT_ABOVE_PULLBACK_HIGH_AND_NOT_BELOW_ORIGINAL_BOX_FLOOR')
        why += ['EQUAL_' + k + '_IS_NOT_A_STRICT_CROSS' for k in equal]
        # Auxiliary observations never veto the already occurred price facts.
        volume = source['volume']; macd = source['macd']
        if volume['reason'] == 'AVAILABLE':
            rel = source['original_bar']['volume_shares_scaled']
            from reaction_facts.core import compare
            relation = compare(rel, volume['previous_shares'])['relation']
            (support if relation == 'ABOVE' else opposite if relation == 'BELOW' else missing).append(
                'VOLUME_' + relation + '_PREVIOUS_RECORD_DESCRIPTION_ONLY_NOT_BREAKOUT_FILTER')
        else:
            missing.append('VOLUME:' + volume['reason'])
        sign = macd['field_observations']['histogram']['sign']['relation']
        if sign is None:
            missing.append('MACD_HISTOGRAM_UNAVAILABLE')
        elif sign == 'ABOVE':
            support.append('MACD_HISTOGRAM_POSITIVE_DESCRIPTION_ONLY')
        elif sign == 'BELOW':
            opposite.append('MACD_HISTOGRAM_NEGATIVE_DESCRIPTION_ONLY')
        if any(r.get('qualification') == 'RESEARCH_CANDIDATE' for r in roles.values()):
            missing.append('RESEARCH_ROLE_HYPOTHESIS_NOT_FORMAL_ORIGINAL_BOX_APPROVAL')
        missing += ['HISTORICAL_PUBLICATION_UNVERIFIED', 'PERSONAL_ACTION_AND_RETURN_QUALIFICATION_NOT_EVALUATED']
        if breakout_ok and d == phase['breakout_on']:
            events.append(_event(d, 'ORIGINAL_BREAKOUT_CLOSE', None, None,
                                 ['CONTIGUOUS_CLOSE_ABOVE_EXPLICIT_ORIGINAL_UPPER'],
                                 {'ORIGINAL_BOX_UPPER': role_ids.get('ORIGINAL_BOX_UPPER')}, source['original_bar']['close']))
        if state != prior:
            changed_on = d
            events.append(_event(d, 'STATE_CHANGED', prior, state, why, role_ids, source['original_bar']['close']))
        for name, pf in price_facts.items():
            change = pf['close']['transition']
            if change['kind'] not in ('UNCHANGED', 'NOT_AVAILABLE', 'SEGMENT_START'):
                events.append(_event(d, 'CLOSE_REFERENCE_TRANSITION', None, None,
                                     [name, change['kind']], {name: role_ids[name]}, source['original_bar']['close']))
        records.append(dict(date=d, close=source['original_bar']['close'], state=state, label=LABELS[state],
                            reasons=why, state_changed_on=changed_on, price_facts=price_facts,
                            role_prices=prices, equal_boundaries=equal, reference_role_ids=role_ids,
                            evidence=dict(supporting=support, opposing=opposite, missing=missing,
                                          original_volume=deepcopy(volume), original_macd=deepcopy(macd),
                                          body=deepcopy(source['body']), adjacent_close=deepcopy(source['adjacent']['close'])),
                            intraday_sequence='UNKNOWN_FROM_DAILY_OHLC',
                            reference_qualification='CONDITIONAL_EXPLICIT_ROLES_NOT_AUTOMATIC_PATTERN',
                            historical_signal_eligible=False))
        prior = state
    catalogue = []
    for name, role in roles.items():
        ref = refs.get(role.get('reference_id'))
        if ref:
            catalogue.append(dict(role=name, role_id=_role_identity(role, ref, facts_input['context']), semantic=deepcopy(role),
                                  source_reference=deepcopy(ref), available_at_as_of=role['known_on'] <= as_of))
            if role['known_on'] > as_of or ref['known_on'] > as_of:
                catalogue[-1]['source_reference']['price'] = None
    return _finish(dict(schema_version=VERSION, as_of=as_of, context=deepcopy(facts_input['context']),
                        evaluated_prefix_fingerprint=facts['evaluated_prefix_fingerprint'],
                        original_reaction_result_id=facts['result_id'], scenario_id=scenario['scenario_id'],
                        source_qualification='EXPLICIT_RESEARCH_ROLES_NOT_FORMAL_BOX' if any(r['qualification'] == 'RESEARCH_CANDIDATE' for r in roles.values()) else 'EXPLICIT_SOURCE_ROLES',
                        post_breakout_return=deepcopy(phase), reference_catalog=catalogue,
                        records=records, events=events, limits=deepcopy(facts.get('limits', {}))))


def _event(day_, kind, old, new, reasons, roles, close):
    event = dict(date=day_, kind=kind, from_state=old, to_state=new, reasons=deepcopy(reasons),
                 reference_role_ids=deepcopy(roles), close=close,
                 intraday_sequence='UNKNOWN_FROM_DAILY_OHLC', historical_signal_eligible=False)
    event['id'] = fingerprint(event)
    return event


def _finish(result):
    result.update(execution_qualified=False, imputed_close=None, valuation=None,
                  historical_signal_eligible=False, primary_pressure_id=None, policy_authorized=False,
                  classification_quality='NOT_VALIDATED', core_usefulness='NOT_ESTABLISHED',
                  action_qualification='NOT_EVALUATED', physical_android='NOT_TESTED_NEW_BUILD')
    result['result_id'] = fingerprint(result)
    return result
