"""Read saved source identities and explicit paths, without recognition/replay."""
from collections import defaultdict
from copy import deepcopy
from datetime import date, datetime

from graph_core.core import VERSION as CORE_VERSION, fingerprint, number

VERSION = 'graph-source-query/0.1'
QUERY_VERSION = 'graph-source-query-request/0.1'


def _day(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError('Canonical original date required')
    return value


def _index(value, length):
    if type(value) is not int or not 0 <= value < length:
        raise ValueError('Original source index out of prefix')
    return value


def _identity(value, key):
    if fingerprint({k: v for k, v in value.items() if k != key}) != value[key]:
        raise ValueError('Saved fingerprint differs: ' + key)


def binding_for(result):
    return dict(result_id=result['result_id'], source_prefix_fingerprint=result['source_prefix_fingerprint'],
                context=deepcopy(result['context']))


def validate_result(result):
    """Validate saved IDs, references and index/time coherence; never detect turns."""
    if result.get('schema_version') != CORE_VERSION:
        raise ValueError('Saved original core schema required')
    _identity(result, 'result_id')
    as_of = _day(result['as_of']); n = result['source_records']; c = result['context']
    if type(n) is not int or n < 1:
        raise ValueError('Original prefix length required')
    if any(not isinstance(c.get(k), str) or not c[k] for k in ('code', 'source_id', 'price_basis_id')):
        raise ValueError('Explicit original source context required')
    if c.get('volume_unit') != 'SHARES_REPORTED' or c.get('price_mode') not in ('RAW_CANDIDATE', 'ADJUSTED_CANDIDATE'):
        raise ValueError('Original price mode/reported share qualification required')
    if not result.get('source_prefix_fingerprint'):
        raise ValueError('Original prefix identity required')
    anchor = result['anchor']
    if (anchor['date'] != as_of or anchor['index'] != n - 1 or
        anchor['price_basis_id'] != c['price_basis_id'] or anchor['price_mode'] != c['price_mode']):
        raise ValueError('Anchor/source prefix identity differs')
    by_id = {}; groups = defaultdict(list); all_dates = {n - 1: as_of}
    def bind_date(index, day):
        _index(index, n); _day(day)
        if index in all_dates and all_dates[index] != day:
            raise ValueError('Original index/date contradiction')
        all_dates[index] = day
    for p in result['pivots']:
        if p['id'] in by_id:
            raise ValueError('Duplicate original pivot ID')
        if p.get('confirmation') != 'LATER_COMPLETED_CLOSE_REVERSAL_RESEARCH':
            raise ValueError('Unconfirmed or unsupported pivot qualification')
        if p['kind'] not in ('HIGH', 'LOW') or number(p['price']) <= 0:
            raise ValueError('Invalid original pivot')
        if p['scale'] not in result['parameters']['reversals'] or type(p['segment']) is not int or p['segment'] < 0:
            raise ValueError('Unknown scale or segment')
        if not 0 < number(p['scale']) < 1:
            raise ValueError('Invalid saved scale')
        bind_date(p['occurred_index'], p['occurred_at']); bind_date(p['confirmed_index'], p['confirmed_at'])
        if (p['occurred_index'] >= p['confirmed_index'] or p['occurred_at'] >= p['confirmed_at'] or
            p['confirmed_at'] > as_of or p['first_observed_at'] != p['confirmed_at']):
            raise ValueError('Unconfirmed/future or contradictory pivot times')
        expected = fingerprint({k: p[k] for k in ('kind', 'price', 'occurred_at', 'confirmed_at', 'scale', 'segment')})
        if p['id'] != expected:
            raise ValueError('Original pivot ID differs')
        dates = p['source_dates']
        if (not dates or dates[0] != p['occurred_at'] or dates != sorted(set(dates)) or
            any(not p['occurred_at'] <= _day(d) <= p['confirmed_at'] for d in dates)):
            raise ValueError('Complete ordered source_dates required')
        by_id[p['id']] = p; groups[(p['scale'], p['segment'])].append(p)
    ordered_dates = sorted(all_dates.items())
    if any(a[1] >= b[1] for a, b in zip(ordered_dates, ordered_dates[1:])):
        raise ValueError('Inconsistent source index chronology')
    for points in groups.values():
        if any(a['occurred_index'] >= b['occurred_index'] or a['confirmed_index'] >= b['confirmed_index']
               for a, b in zip(points, points[1:])):
            raise ValueError('Original source sequence must remain ordered')
    boxes = {}; positions = {key: {p['id']: i for i, p in enumerate(points)} for key, points in groups.items()}
    for b in result['boxes']:
        ids = b['source_turn_ids']
        if b['id'] in boxes or not ids or len(set(ids)) != len(ids) or any(i not in by_id for i in ids):
            raise ValueError('Broken original box source references')
        if b['id'] != fingerprint(dict(scale=b['scale'], turns=ids, bounds=b['research_bounds'])):
            raise ValueError('Original box ID differs')
        key = (b['scale'], b['segment']); points = groups.get(key, []); pos = positions.get(key, {})
        if any(i not in pos for i in ids):
            raise ValueError('Box mixes scale/segment sources')
        start = pos[ids[0]]
        if [p['id'] for p in points[start:start + len(ids)]] != ids:
            raise ValueError('Box references are not its original ordered contiguous sequence')
        first, last = by_id[ids[0]], by_id[ids[-1]]
        if (b['first_index'] != first['occurred_index'] or b['last_index'] != last['occurred_index'] or
            b['formed_index'] != last['confirmed_index'] or b['start'] != first['occurred_at'] or
            b['source_end'] != last['occurred_at'] or b['confirmed_at'] != last['confirmed_at'] or
            b['first_observed_at'] != b['confirmed_at'] or b['turns'] != len(ids) or
            b['duration_records'] != b['last_index'] - b['first_index'] + 1):
            raise ValueError('Original box times/index/source count differ')
        if max(by_id[i]['confirmed_at'] for i in ids) > b['confirmed_at'] or b['confirmed_at'] > as_of:
            raise ValueError('Box sources not confirmed at saved box time')
        boxes[b['id']] = b
    # Validate old reference IDs without interpreting/expanding their relationships.
    for b in boxes.values():
        for key in ('parent_ids', 'successor_after_breakdown_ids'):
            if any(i not in boxes for i in b.get(key, [])):
                raise ValueError('Broken saved box relationship reference')
    comparison = result['comparison']
    for key in ('pareto_frontier_ids', 'relevant_pressure_ids'):
        if any(i not in boxes for i in comparison[key]):
            raise ValueError('Broken saved comparison box reference')
    if any(e[k] not in boxes for e in comparison['parent_child_comparisons'] for k in ('parent_id', 'child_id')):
        raise ValueError('Broken saved comparison relationship reference')
    for ref in result['reference_candidates']:
        if ref['pivot_id'] not in by_id:
            raise ValueError('Broken saved pivot reference candidate')
        p = by_id[ref['pivot_id']]
        if any(ref[k] != p[k] for k in ('scale', 'price', 'occurred_at', 'confirmed_at', 'first_observed_at', 'source_dates')):
            raise ValueError('Saved reference candidate source differs')
    return by_id, groups, boxes


def inspect_sources(result, query):
    """Pure deterministic read-only lookup, limited to explicit IDs and endpoints."""
    pivots, groups, boxes = validate_result(result)
    if query.get('schema_version') != QUERY_VERSION or set(query) != {'schema_version', 'binding', 'pivot_ids', 'path_requests', 'selected_at'}:
        raise ValueError('Explicit source-query request only; no manual answers or implicit endpoints')
    if query['binding'] != binding_for(result):
        raise ValueError('Query mixes saved result/source/basis/context/prefix')
    if not isinstance(query['selected_at'], str):
        raise ValueError('Actual query timestamp required')
    selected = datetime.fromisoformat(query['selected_at'])
    if selected.tzinfo is None:
        raise ValueError('Actual query timestamp requires timezone')
    requested = query['pivot_ids']
    if not isinstance(requested, list) or len(set(requested)) != len(requested):
        raise ValueError('Distinct explicit pivot IDs required')
    if any(i not in pivots for i in requested):
        raise ValueError('Unknown/unconfirmed pivot ID outside saved prefix')
    if not isinstance(query['path_requests'], list):
        raise ValueError('Explicit path list required')
    reverse = defaultdict(list)
    for ordinal, b in enumerate(result['boxes'], 1):
        for position, pivot_id in enumerate(b['source_turn_ids']):
            reverse[pivot_id].append(dict(box_id=b['id'], original_box_ordinal_1based=ordinal,
                                         source_turn_position_0based=position,
                                         not_before_original_confirmations=max(b['confirmed_at'], pivots[pivot_id]['confirmed_at'])))
    needed = set(); returned_boxes = {}; sources = []; paths = []
    def coordinate(p):
        # Decimal equality preserves long precision and ignores spelling zeros.
        return (p['segment'], p['kind'], p['occurred_at'], number(p['price']), tuple(p['source_dates']))
    for pivot_id in requested:
        p = pivots[pivot_id]; needed.add(pivot_id); aliases = []
        for other in result['pivots']:
            if other['id'] != pivot_id and coordinate(other) == coordinate(p):
                needed.add(other['id'])
                aliases.append(dict(pivot_id=other['id'], not_before_original_confirmations=max(p['confirmed_at'], other['confirmed_at']),
                                    qualification='EXACT_SOURCE_COORDINATE_NOT_MERGE_OR_INDEPENDENT_VOTE'))
        refs = deepcopy(reverse[pivot_id])
        for ref in refs:
            b = boxes[ref['box_id']]; needed.update(b['source_turn_ids'])
            returned_boxes[b['id']] = {k: deepcopy(b[k]) for k in
                                      ('id', 'scale', 'segment', 'start', 'source_end', 'confirmed_at', 'first_observed_at',
                                       'first_index', 'last_index', 'formed_index', 'source_turn_ids', 'research_bounds')}
        sources.append(dict(pivot_id=pivot_id, original_box_references=refs, coordinate_correspondences=aliases,
                            qualification='ORIGINAL_BOX_REFERENCE_NOT_FORMAL_WHOLE_STRUCTURE_MEMBERSHIP'))
    for request in query['path_requests']:
        if not isinstance(request, dict) or set(request) != {'from_id', 'to_id'}:
            raise ValueError('Both explicit path endpoints required; no guessed stop')
        if any(request[k] not in pivots for k in ('from_id', 'to_id')):
            raise ValueError('Unknown/unconfirmed path endpoint')
        first, last = pivots[request['from_id']], pivots[request['to_id']]
        key = (first['scale'], first['segment'])
        if key != (last['scale'], last['segment']):
            raise ValueError('Cross-scale/segment path refused; coordinate lookup is separate')
        points = groups[key]; start = points.index(first); end = points.index(last)
        if start > end:
            raise ValueError('Reverse chronological path refused')
        route = points[start:end + 1]; needed.update(p['id'] for p in route)
        paths.append(dict(**deepcopy(request), scale=key[0], segment=key[1], turn_ids=[p['id'] for p in route],
                          records=len(route), sequence_records=len(points), records_before=start, records_after=len(points) - end - 1,
                          not_before_original_confirmations=max(p['confirmed_at'] for p in route),
                          qualification='EXPLICIT_SAVED_SUBSEQUENCE_NOT_FORMAL_WHOLE_START_STOP_OR_SUCCESSION'))
    report = dict(schema_version=VERSION, query=deepcopy(query), original_result_id=result['result_id'],
                  as_of=result['as_of'], context=deepcopy(result['context']),
                  source_prefix_fingerprint=result['source_prefix_fingerprint'],
                  original_parameters=deepcopy(result['parameters']),
                  pivots={p['id']:deepcopy(p) for p in result['pivots'] if p['id'] in needed},
                  boxes=returned_boxes, requested_sources=sources, paths=paths,
                  original_qualifications={k:deepcopy(result[k]) for k in
                      ('data_gaps', 'ambiguities', 'historical_information_availability', 'corporate_action_comparability',
                       'intraday_order', 'qualified_interpretation', 'classification_quality', 'action_qualification')},
                  historical_selection_time=None, historical_signal_eligible=False,
                  public_information_availability='UNVERIFIED_ORIGINAL_CONFIRMATIONS_ARE_LOWER_BOUNDS_ONLY',
                  lookup_scope='REVERSE_BOX_LOOKUP_ONLY_FOR_EXPLICIT_PIVOT_IDS_NO_RECURSIVE_EXPANSION',
                  primary_pressure_id=None, formal_structure_membership=None, formal_merge=None,
                  formal_representative=None, direct_successor_id=None, whole_pressure_clearance=None,
                  importance='UNKNOWN', lifecycle='UNKNOWN', core_usefulness='NOT_ESTABLISHED',
                  physical_android='NOT_TESTED_NEW_BUILD')
    report['report_id'] = fingerprint(report)
    return report
