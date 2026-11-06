"""Presentation-only projection of an unchanged graph 0.2 result.

No recognition, ranking, source retrieval or trading qualification is performed.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from graph_core.core import fingerprint, number, relation


def validate_source_spec(spec, root, parent_sha):
    if spec.get('schema_version') != 'graph-view-source-input/0.2':
        raise ValueError('Explicit graph view source spec 0.2 required')
    if spec.get('core_version') != 'graph-recognition-research/0.2' or spec.get('numeric_parent_sha256') != parent_sha:
        raise ValueError('Source spec version/parent mismatch')
    # Validate retained evidence, never fetch or reinterpret a corporate action.
    from source_audit import parse_twse_month
    for code, warnings in spec.get('basis_warnings', {}).items():
        for warning in warnings:
            path = (root / warning['source_file']).resolve()
            if not path.is_relative_to(root.resolve()):
                raise ValueError('Warning source outside retained project')
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != warning['sha256']:
                raise ValueError('Retained warning source changed')
            year, month, _ = map(int, warning['date'].split('-'))
            payload = json.loads(raw)
            rows = parse_twse_month(payload, code=code, year=year, month=month)
            index = next(i for i, r in enumerate(rows) if r['date'] == warning['date'])
            change = payload['fields'].index('漲跌價差')
            if not str(payload['data'][index][change]).strip().startswith('X'):
                raise ValueError('No retained non-comparable price marker')
            if warning['kind'] != 'NON_COMPARABLE_MARKER_EVENT_TYPE_UNKNOWN' or warning['historical_available_at'] != 'UNKNOWN':
                raise ValueError('Unverified corporate-action/publication qualification')


def bind_input(payload, spec, code):
    value = deepcopy(payload)
    value['basis_break_dates'] = sorted(set(value['basis_break_dates']) | {
        w['date'] for w in spec.get('basis_warnings', {}).get(code, [])})
    return value


def input_binding(payload, spec, code, as_of):
    prefix = deepcopy(payload)
    prefix['bars'] = [r for r in prefix['bars'] if r['date'] <= as_of]
    prefix['basis_break_dates'] = [d for d in prefix['basis_break_dates'] if d <= as_of]
    return dict(schema_version='graph-view-input-binding/0.2', core_input_fingerprint=fingerprint(prefix),
                source_id=payload['context']['source_id'], price_basis_id=payload['context']['price_basis_id'],
                basis_break_dates=prefix['basis_break_dates'],
                retained_warning_evidence=deepcopy([w for w in spec.get('basis_warnings', {}).get(code, []) if w['date'] <= as_of]),
                source_role='RETAINED_OFFICIAL_PARENT_NOT_FINMIND', historical_available_at='UNKNOWN',
                corporate_action_type='UNKNOWN', cross_basis_comparability='NOT_CERTIFIED')


def layers(result, rows):
    """Exact source indices and original events; no new lifecycle verdicts."""
    if result['schema_version'] != 'graph-recognition-research/0.2':
        raise ValueError('View 0.2 requires graph core 0.2')
    rows = rows[:result['source_records']]
    if not rows or rows[-1]['date'] != result['as_of']:
        raise ValueError('Exact completed prefix required')
    pivots = {p['id']: p for p in result['pivots']}
    projected = {}
    for b in result['boxes']:
        events = b['path']['events']
        stops = [e['date'] for e in events if e['type'] == 'OBSERVATION_STOPPED_AT_DATA_OR_BASIS_GAP']
        stop = stops[0] if stops else None
        observations = []
        for i in range(b['formed_index'], len(rows)):
            r = rows[i]
            loc = 'NOT_COMPARABLE_AFTER_GAP' if stop and r['date'] >= stop else (
                'UNKNOWN_MISSING_PRICE' if r['close'] is None else relation(number(r['close']), number(b['research_bounds']['low']), number(b['research_bounds']['high'])))
            observations.append([i, loc])
        projected[b['id']] = dict(schema_version='graph-box-evidence/0.2', box_id=b['id'],
            formation=dict(first_index=b['first_index'], last_index=b['last_index'], start=b['start'], source_end=b['source_end'],
                records=b['duration_records'], source_turns=[deepcopy(pivots[i]) for i in b['source_turn_ids']],
                first_observed_at=b['first_observed_at'], confirmed_at=b['confirmed_at'],
                research_bounds=deepcopy(b['research_bounds']), display_extent=deepcopy(b['display_extent'])),
            observation=dict(start_index=b['formed_index'], as_of=result['as_of'], completed_records=observations,
                whole_range_location=b['path']['last_close_location'] if b['usable_at_anchor'] else 'NOT_COMPARABLE_AFTER_GAP',
                pressure_band_location=b['anchor_relation'], comparison_reason=b['anchor_comparison_reason'],
                pressure_distance_fraction=b['pressure_distance_fraction'], relative_width_to_anchor=b['relative_width_to_anchor'],
                first_breakdown_at=b['path']['first_breakdown_at'], events=deepcopy(events), stopped_at=stop,
                qualification=b['path']['qualification']),
            history=dict(parent_ids=deepcopy(b['parent_ids']), successor_after_breakdown_ids=deepcopy(b['successor_after_breakdown_ids']),
                scale=b['scale'], segment=b['segment'], cross_scale_candidate_ids=[p['id'] for p in result['boxes']
                    if p['scale'] != b['scale'] and p['first_index'] <= b['last_index'] and p['last_index'] >= b['first_index']],
                manual_review_role='LATER_INDEPENDENT_AUDIT_NEVER_AUTOMATIC_FORMATION', primary_pressure_id=None,
                lifecycle='UNKNOWN_RETURN_IS_NOT_FORMAL_REACTIVATION'))
    return projected
