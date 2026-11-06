"""Pure source adapter for explicit semantic roles, not automatic box selection."""
from copy import deepcopy
from graph_core.core import fingerprint, number
from reaction_facts.source import make_input


def prepare(data, choice):
    if choice.get('schema_version') != 'p03-source-role-selection/0.1':
        raise ValueError('Explicit semantic source-role selection required')
    if choice['comparison_artifact_id'] != data['artifact_id']:
        raise ValueError('Role selection original comparison artifact differs')
    query = dict(schema_version='explicit-reaction-reference-selection/0.1',
                 binding=choice['binding'], selected_at=choice['selected_at'],
                 references=choice['references'])
    payload = make_input(data, query)
    payload['context']['adjustment_version'] = choice['adjustment_version']
    if payload['context']['price_mode'] == 'RAW_CANDIDATE' and choice['adjustment_version'] != 'NOT_APPLICABLE_RAW':
        raise ValueError('Raw source adjustment-version mismatch')
    roles = {}
    for name, description in choice['roles'].items():
        ref = payload['references'][description['reference_index']]
        role = deepcopy(description)
        role.pop('reference_index')
        role.update(role=name, reference_id=ref['id'], selected_at=choice['selected_at'])
        roles[name] = role
    # A candidate must be explicitly the same original research box, not any two
    # convenient points, and must remain labelled as research, not human approval.
    bottom = roles.get('ORIGINAL_BOX_FLOOR'); top = roles.get('ORIGINAL_BOX_UPPER')
    if bottom and top:
        b = next(r for r in payload['references'] if r['id'] == bottom['reference_id'])
        t = next(r for r in payload['references'] if r['id'] == top['reference_id'])
        if b['source_kind'] == 'RESEARCH_BOUND' or t['source_kind'] == 'RESEARCH_BOUND':
            if b['origin_id'] != t['origin_id']:
                raise ValueError('Different original research box sources')
            if bottom['qualification'] != 'RESEARCH_CANDIDATE' or top['qualification'] != 'RESEARCH_CANDIDATE':
                raise ValueError('Research bounds cannot masquerade as human-confirmed box')
            box = next(x for x in data['core']['boxes'] if x['id'] == b['origin_id'])
            if choice['post_breakout_return']['context_start_on'] != box['start']:
                raise ValueError('Original box context cannot skip earlier source interruptions')
            for role, ref in [(bottom, b), (top, t)]:
                if (role['evidence'].get('candidate_id') != box['id'] or
                    role['evidence'].get('source_start') != box['start'] or
                    role['evidence'].get('source_end') != box['source_end']):
                    raise ValueError('Original box role provenance differs from saved candidate')
                witnesses = [row['date'] for row in data['bars']
                             if box['start'] <= row['date'] <= box['source_end']
                             and row[ref['source_field']] is not None
                             and number(row[ref['source_field']]) == number(ref['price'])]
                if not witnesses or role['evidence'].get('source_k_dates') != witnesses:
                    raise ValueError('Research bound original K witnesses missing or mismatched')
    high = roles.get('PULLBACK_HIGH')
    if high:
        evidence = high['evidence']
        dates = evidence['source_member_dates']
        rows = [r for r in data['bars'] if r['date'] in dates]
        if not dates or [r['date'] for r in rows] != dates:
            raise ValueError('Explicit pullback member dates missing or unordered')
        if evidence['phase_start'] != dates[0] or evidence['phase_end'] != dates[-1]:
            raise ValueError('Pullback phase/source member mismatch')
        expected = [r['date'] for r in data['bars'] if dates[0] <= r['date'] <= dates[-1]]
        if dates != expected or high['known_on'] < dates[-1]:
            raise ValueError('Pullback phase incomplete or known too early')
        high_ref = next(r for r in payload['references'] if r['id'] == high['reference_id'])
        if any(r['high'] is None for r in rows):
            raise ValueError('Missing pullback source high')
        maximum = max(number(r['high']) for r in rows)
        witnesses = [r['date'] for r in rows if number(r['high']) == maximum]
        if (high_ref['source_kind'] != 'BAR_FIELD' or high_ref['source_field'] != 'high'
            or high_ref['occurred_at'] not in witnesses or number(high_ref['price']) != maximum
            or evidence['all_equal_high_source_dates'] != witnesses):
            raise ValueError('Explicit pullback-high source is not supported by its phase')
        if dates[0] < choice['post_breakout_return']['return_on']:
            raise ValueError('Pullback high is outside declared return context')
    scenario = dict(schema_version='p03-explicit-roles/0.1',
                    scenario_id=choice['scenario_id'],
                    binding={k: deepcopy(payload['context'][k]) for k in
                             (*choice['binding'].keys(), 'price_mode', 'adjustment_version')},
                    roles=roles, post_breakout_return=deepcopy(choice['post_breakout_return']))
    return payload, scenario
