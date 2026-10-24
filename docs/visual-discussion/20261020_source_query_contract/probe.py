"""Audit saved ordered pivot sources only; never establishes economic membership."""
import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def inspect(payload, earlier_audit):
    groups = defaultdict(list)
    for p in payload['core']['pivots']:
        groups[(p['scale'], p['segment'])].append(p)
    source = earlier_audit['queried_original_pivot']
    points = groups[(source['scale'], source['segment'])]
    assert all(a['occurred_index'] < b['occurred_index'] for a, b in zip(points, points[1:]))
    assert points.count(source) == 1
    first = points.index(source)
    trace = earlier_audit['original_same_scale_chronological_trace']['pivots']
    last = points.index(trace[-1])
    assert points[first:last + 1] == trace
    for p in points:
        bar = payload['bars'][p['occurred_index']]
        assert bar['date'] == p['occurred_at']
        assert bar['high' if p['kind'] == 'HIGH' else 'low'] == p['price']
    aliases = []
    for record in earlier_audit['original_same_scale_chronological_trace']['focus_source_coordinate_correspondences']:
        for p in record['trace_original_pivots']:
            other = record['focus_original_pivot']
            assert (p['kind'], p['occurred_at'], p['price'], p['source_dates'], p['segment']) == (
                other['kind'], other['occurred_at'], other['price'], other['source_dates'], other['segment'])
            assert p['id'] != other['id']
            aliases.append({'original_pivot_ids': [p['id'], other['id']],
                            'original_confirmations': [p['confirmed_at'], other['confirmed_at']],
                            'source_dates': p['source_dates'], 'formal_merge': None})
    return {
        'scope': 'READ_ONLY_PATH_STOP_SUFFICIENCY_COUNTEREXAMPLE_NOT_RECOGNITION_OR_QUERY_IMPLEMENTATION',
        'as_of': payload['as_of'], 'core_result_id': payload['core']['result_id'],
        'selected_at_utc': datetime.now(timezone.utc).isoformat(),
        'historical_selection_time': None, 'historical_signal_eligible': False,
        'same_scale_and_segment': {'scale': source['scale'], 'segment': source['segment']},
        'entire_saved_sequence': {'records': len(points), 'first': points[0], 'last': points[-1],
                                 'turn_ids': [p['id'] for p in points]},
        'explicit_preceding_research_route': {
            'from_id': source['id'], 'to_id': trace[-1]['id'], 'records': len(trace),
            'records_before_route': first, 'records_after_route': len(points) - last - 1,
            'original_confirmations_not_before': max(p['confirmed_at'] for p in trace),
            'turns': trace, 'route_endpoint_meaning': 'EXPLICIT_LATER_RESEARCH_QUERY_NOT_FORMAL_START_OR_STOP'},
        'coordinate_correspondences_with_source_dates_preserved': aliases,
        'source_data_gap_notice': payload['source_gaps'],
        'same_segment_does_not_establish_economic_structure': True,
        'formal_structure_stop': None, 'formal_membership': None, 'primary_pressure_id': None,
        'production_source_query_implemented': False,
        'verification': {'all_sequence_pivots_match_original_bars': True,
                         'earlier_explicit_route_is_exact_saved_subsequence': True,
                         'no_source_or_confirmation_recomputed': True},
    }


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--previous-audit', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    source = Path(args.input)
    raw = source.read_bytes()
    earlier = json.loads(Path(args.previous_audit).read_text())
    assert hashlib.sha256(raw).hexdigest() == earlier['source_sha256']
    report = inspect(json.loads(raw), earlier)
    assert source.read_bytes() == raw
    report['source_sha256'] = hashlib.sha256(raw).hexdigest()
    report['verification']['input_bytes_unchanged'] = True
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'sequence_records': report['entire_saved_sequence']['records'],
                      'route_records': report['explicit_preceding_research_route']['records'],
                      'before': report['explicit_preceding_research_route']['records_before_route'],
                      'after': report['explicit_preceding_research_route']['records_after_route'],
                      'production_query_implemented': False}))
