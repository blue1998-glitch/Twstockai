"""Validate an existing immutable packet; never rebuild diagnostic/analysis results."""
from copy import deepcopy
from graph_core.core import _validate, fingerprint, number
from .source_query import inspect_sources, validate_result


def inspect_packet(packet, query):
    if fingerprint({k:v for k,v in packet.items() if k != 'artifact_id'}) != packet['artifact_id']:
        raise ValueError('Saved packet artifact fingerprint differs')
    wanted = query['binding']['result_id']; schema = packet['schema_version']
    if schema == 'cross-scale-real-chart/0.1':
        series = packet; core = packet['core']; frame = packet['source_frame_id']
        if core['result_id'] != wanted or packet['as_of'] != core['as_of'] or packet['source_prefix_fingerprint'] != core['source_prefix_fingerprint']:
            raise ValueError('Comparison is not the explicitly selected saved result')
        diagnostics_status = 'COMPARISON_SUMMARY_ONLY_NO_FULL_DIAGNOSTIC_ID_VERIFICATION_CLAIMED'
    elif schema in ('graph-recognition-chart-bundle/0.1', 'graph-diagnostic-chart-bundle/0.1'):
        matches = [(s, r) for s in packet['series'] for r in s['results'] if r['result_id'] == wanted]
        if len(matches) != 1:
            raise ValueError('Exactly one explicitly selected saved result required; no latest fallback')
        series, core = matches[0]; frame = series['numeric_frame_ids'][core['as_of']]
        diagnostics_status = 'SAVED_CORE_SOURCE_QUERY_FULL_DIAGNOSTICS_NOT_RECOMPUTED_OR_REVALIDATED'
    else:
        raise ValueError('Unsupported saved packet schema')
    validate_result(core)
    c = core['context']
    if series['code'] != c['code'] or series['source']['id'] != c['source_id'] or series['price_basis_id'] != c['price_basis_id'] or not isinstance(frame, str) or not frame:
        raise ValueError('Packet source/code/basis/frame identity differs')
    payload = dict(schema_version='graph-recognition-input/0.1', context=deepcopy(c), bars=series['bars'],
                   basis_break_dates=core['data_gaps']['basis_resets'])
    context, rows, resets, missing, gaps, config = _validate(payload, core['as_of'], core['parameters'])
    if (context != c or fingerprint(rows) != core['source_prefix_fingerprint'] or len(rows) != core['source_records'] or
        sorted(resets) != core['data_gaps']['basis_resets'] or gaps != core['data_gaps']['missing_price_rows']):
        raise ValueError('Original source prefix/context/gap identity differs')
    if len(series['macd']) != len(series['bars']) or any(m is not None and m.get('date', r['date']) != r['date'] for m,r in zip(series['macd'],series['bars'])):
        raise ValueError('Saved MACD ordinal axis differs; no recalculation permitted')
    by_date = {r['date']:r for r in rows}
    for p in core['pivots']:
        if rows[p['occurred_index']]['date'] != p['occurred_at'] or rows[p['confirmed_index']]['date'] != p['confirmed_at']:
            raise ValueError('Original pivot source index/date differs')
        field = 'high' if p['kind'] == 'HIGH' else 'low'
        observed = [r['date'] for r in rows[p['occurred_index']:p['confirmed_index'] + 1]
                    if r[field] is not None and number(r[field]) == number(p['price'])]
        if p['source_dates'] != observed or any(d not in by_date for d in p['source_dates']):
            raise ValueError('Complete original source_dates/price differ from saved bars')
    for b in core['boxes']:
        if fingerprint(rows[b['first_index']:b['last_index'] + 1]) != b['display_extent']['source_rows_fingerprint']:
            raise ValueError('Original box source row fingerprint differs')
    report = inspect_sources(core, query)
    del report['report_id']
    report['source_validation'] = dict(source_frame_id=frame, packet_contract=schema,
                                       original_source_prefix_verified=True, original_pivot_source_fields_verified=True,
                                       source_gaps=deepcopy(series['source_gaps']), diagnostics=diagnostics_status,
                                       external_market_or_publication_authentication='NOT_ESTABLISHED',
                                       recognition_macd_diagnostics_recomputed=False)
    report['report_id'] = fingerprint(report)
    return report
