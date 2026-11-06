"""Read saved source relationships; does not run recognition or infer membership."""
import argparse
import hashlib
import json
from collections import Counter, deque
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


def audit(payload, pivot_id, context_layer, focus_layer):
    boxes = payload['core']['boxes']
    pivots = {p['id']: p for p in payload['core']['pivots']}
    layers = {l['id']: l for l in payload['layers']}
    context, focus = layers[context_layer], layers[focus_layer]
    start, end = context['source_start'], context['source_end']
    pivot = pivots[pivot_id]
    assert start <= pivot['occurred_at'] <= end
    assert payload['bars'][pivot['occurred_index']]['high' if pivot['kind'] == 'HIGH' else 'low'] == pivot['price']
    box_by_id = {b['id']: b for b in boxes}
    focus_id, = focus['box_ids']

    def brief(b):
        return {
            'original_box_ordinal': boxes.index(b) + 1,
            **{k: b[k] for k in ['id', 'start', 'source_end', 'confirmed_at', 'scale', 'source_turn_ids']},
            'research_low': b['research_bounds']['low'],
            'research_high': b['research_bounds']['high'],
            'entire_source_interval_within_display_context': start <= b['start'] <= b['source_end'] <= end,
            'source_interval_intersects_display_context': max(start, b['start']) <= min(end, b['source_end']),
            'source_pivots_outside_display_context': [pivots[t] for t in b['source_turn_ids'] if not start <= pivots[t]['occurred_at'] <= end],
            'formal_membership': None,
        }

    source_boxes = [b for b in boxes if pivot_id in b['source_turn_ids']]
    focus_sources = sorted((pivots[t] for t in box_by_id[focus_id]['source_turn_ids']), key=lambda p: p['occurred_index'])
    trace_end = max(pivot['occurred_index'], focus_sources[min(1, len(focus_sources) - 1)]['occurred_index'])
    trace = sorted((p for p in pivots.values() if p['scale'] == pivot['scale'] and p['segment'] == pivot['segment']
                    and pivot['occurred_index'] <= p['occurred_index'] <= trace_end), key=lambda p: p['occurred_index'])
    coordinate = lambda p: (p['kind'], p['occurred_at'], p['price'])
    trace_coordinates = {coordinate(p) for p in trace}
    aliases = [{'focus_original_pivot': p, 'trace_original_pivots': [t for t in trace if coordinate(t) == coordinate(p)]}
               for p in focus_sources if coordinate(p) in trace_coordinates]
    inventory = [brief(b) for b in boxes]
    by_id = {b['id']: b for b in inventory}
    contained = [b for b in boxes if by_id[b['id']]['entire_source_interval_within_display_context']]
    intersecting = [b for b in boxes if by_id[b['id']]['source_interval_intersects_display_context']]
    geometries = {
        tuple((pivots[t]['kind'], pivots[t]['occurred_at'], pivots[t]['price']) for t in b['source_turn_ids'])
        for b in boxes
    }
    assert len(geometries) == payload['diagnostics']['summary']['exact_source_geometry_groups']

    adjacency = {b['id']: [] for b in boxes}
    pair_counts = Counter()
    for i, b in enumerate(boxes):
        for c in boxes[:i]:
            lo = max(Decimal(b['research_bounds']['low']), Decimal(c['research_bounds']['low']))
            hi = min(Decimal(b['research_bounds']['high']), Decimal(c['research_bounds']['high']))
            relation = 'POSITIVE_OVERLAP' if lo < hi else 'EQUAL_TOUCH' if lo == hi else 'DISJOINT'
            pair_counts[relation] += 1
            if relation == 'POSITIVE_OVERLAP':
                adjacency[b['id']].append(c['id'])
                adjacency[c['id']].append(b['id'])
    assert sum(pair_counts.values()) == len(boxes) * (len(boxes) - 1) // 2
    queue = deque([focus_id])
    previous = {focus_id: None}
    while queue:
        current = queue.popleft()
        for other in adjacency[current]:
            if other not in previous:
                previous[other] = current
                queue.append(other)

    # Independent fixed-point set expansion verifies BFS, rather than mirroring it.
    component = {focus_id}
    while True:
        expanded = component | {j for i in component for j in adjacency[i]}
        if expanded == component:
            break
        component = expanded
    assert component == set(previous)
    earliest = min(component, key=lambda x: (box_by_id[x]['start'], x))
    path = []
    current = earliest
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    edges = []
    for a, b in zip(path, path[1:]):
        left, right = box_by_id[a], box_by_id[b]
        lo = max(Decimal(left['research_bounds']['low']), Decimal(right['research_bounds']['low']))
        hi = min(Decimal(left['research_bounds']['high']), Decimal(right['research_bounds']['high']))
        assert lo < hi
        edges.append({'left_id': a, 'right_id': b, 'overlap_low': str(lo), 'overlap_high': str(hi),
                      'source_intervals_overlap': max(left['start'], right['start']) <= min(left['source_end'], right['source_end']),
                      'shared_original_turn_ids': sorted(set(left['source_turn_ids']) & set(right['source_turn_ids'])),
                      'not_before_both_original_confirmations': max(left['confirmed_at'], right['confirmed_at']),
                      'formal_membership': None})
    return {
        'scope': 'READ_ONLY_COUNTEREXAMPLE_AUDIT_NOT_NEW_CORE_OR_MEMBERSHIP_RULE',
        'as_of': payload['as_of'],
        'core_result_id': payload['core']['result_id'],
        'query_selected_at_utc': datetime.now(timezone.utc).isoformat(),
        'selection_actor': 'ASSISTANT_LATER_RESEARCH',
        'historical_selection_time': None,
        'historical_signal_eligible': False,
        'context': context,
        'context_qualification': 'EXISTING_MONTH_DISPLAY_LENS_NOT_EXACT_MEMBERSHIP_OR_PRODUCTION_INPUT',
        'queried_original_pivot': pivot,
        'original_same_scale_chronological_trace': {
            'pivots': trace,
            'focus_source_coordinate_correspondences': aliases,
            'original_confirmation_times_preserved': True,
            'known_unresolved_calendar_dates_in_window': [d for d in payload['source_gaps']['known_calendar_missing_dates']
                                                          if trace[0]['occurred_at'] <= d <= trace[-1]['occurred_at']],
            'qualification': 'ORDERED_SAVED_SOURCES_AND_COORDINATE_MATCHES_NOT_FORMAL_MERGE_DIRECT_SUCCESSION_OR_HOLDER_IDENTITY'},
        'pivot_source_box_memberships': [by_id[b['id']] for b in source_boxes],
        'whole_box_containment_filter': {
            'candidate_versions_selected': len(contained),
            'queried_pivot_retained_by_selected_box_sources': any(pivot_id in b['source_turn_ids'] for b in contained),
            'qualification': 'COUNTERFACTUAL_FILTER_AUDIT_NOT_ADOPTED_RULE'},
        'any_time_overlap_filter': {
            'candidate_versions_selected': len(intersecting),
            'queried_pivot_retained_by_selected_box_sources': any(pivot_id in b['source_turn_ids'] for b in intersecting),
            'qualification': 'COUNTERFACTUAL_FILTER_AUDIT_NOT_ADOPTED_RULE'},
        'price_only_positive_overlap_probe': {
            'candidate_versions': len(boxes),
            'original_exact_geometry_groups': len(geometries),
            'pair_counts': dict(pair_counts),
            'focus_box_id': focus_id,
            'connected_candidate_versions': len(component),
            'connected_box_ids': sorted(component),
            'component_source_start': min(box_by_id[i]['start'] for i in component),
            'component_source_end': max(box_by_id[i]['source_end'] for i in component),
            'witness_path_box_ids': path,
            'witness_edges': edges,
            'qualification': 'STATIC_SAVED_INTERVAL_GRAPH_ONLY_NOT_MERGE_LIFECYCLE_INDEPENDENT_PATTERNS_OR_HISTORICAL_SIGNAL'},
        'candidate_inventory': inventory,
        'primary_pressure_id': None,
        'verification': {'original_pivot_matches_bar': True, 'all_candidate_pairs_partitioned': len(boxes) * (len(boxes) - 1) // 2,
                         'bfs_equals_independent_fixed_point': True, 'original_geometry_count_reproduced': True},
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--source-id', required=True)
    parser.add_argument('--context-layer', required=True)
    parser.add_argument('--focus-layer', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    source = Path(args.input)
    before = source.read_bytes()
    report = audit(json.loads(before), args.source_id, args.context_layer, args.focus_layer)
    report['source_sha256'] = hashlib.sha256(before).hexdigest()
    assert source.read_bytes() == before
    report['verification']['source_bytes_unchanged'] = True
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output': args.output, 'source_boxes': len(report['pivot_source_box_memberships']),
                      'containment_retains_pivot': report['whole_box_containment_filter']['queried_pivot_retained_by_selected_box_sources'],
                      'connected_versions': report['price_only_positive_overlap_probe']['connected_candidate_versions'],
                      'verification': report['verification']}, ensure_ascii=False))
