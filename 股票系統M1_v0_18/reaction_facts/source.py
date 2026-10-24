"""Read the existing comparison contract; resolve only explicit source selectors."""
from copy import deepcopy
from .core import BINDING, PRICES, timestamp, day
from graph_core.core import fingerprint


def make_input(data, selection):
    if data.get('schema_version') != 'cross-scale-real-chart/0.1':
        raise ValueError('Existing comparison contract required')
    if fingerprint({k: v for k, v in data.items() if k != 'artifact_id'}) != data['artifact_id']:
        raise ValueError('Comparison artifact fingerprint mismatch')
    core = data['core']; c = core['context']
    if fingerprint({k: v for k, v in core.items() if k != 'result_id'}) != core['result_id']:
        raise ValueError('Saved core fingerprint mismatch')
    if (data['code'] != c['code'] or data['source']['id'] != c['source_id'] or
        data['price_basis_id'] != c['price_basis_id'] or data['as_of'] != core['as_of'] or
        data['source_prefix_fingerprint'] != core['source_prefix_fingerprint'] or
        fingerprint(data['bars']) != core['source_prefix_fingerprint']):
        raise ValueError('Source/core/basis/prefix mismatch')
    context = dict(code=data['code'], source_id=data['source']['id'], price_basis_id=data['price_basis_id'],
                   source_frame_id=data['source_frame_id'], source_prefix_fingerprint=data['source_prefix_fingerprint'],
                   volume_unit=c['volume_unit'], price_mode=c['price_mode'],
                   corporate_action_comparability=c.get('corporate_action_comparability', 'UNVERIFIED'),
                   historical_publication_timing='UNVERIFIED', original_core_result_id=core['result_id'],
                   original_comparison_artifact_id=data['artifact_id'])
    if selection.get('schema_version') != 'explicit-reaction-reference-selection/0.1':
        raise ValueError('Explicit reference selection contract required')
    if any(selection['binding'].get(k) != context[k] for k in BINDING):
        raise ValueError('Selection code/source/basis/frame/prefix mismatch')
    selected_at = timestamp(selection['selected_at'])
    bars = {r['date']: r for r in data['bars']}; boxes = {b['id']: b for b in core['boxes']}
    refs = []; evidence = {}
    for selector in selection['references']:
        kind = selector['kind']; field = selector['field']
        if kind == 'BAR_FIELD':
            if field not in PRICES:
                raise ValueError('Explicit original OHLC field required')
            row = bars[day(selector['date'])]
            price = row[field]; origin_id = fingerprint(row)
            occurred = row['date']; known = row.get('known_on', occurred)
            qualification = 'EXPLICIT_RESEARCH_QUERY'
        elif kind == 'RESEARCH_BOUND':
            if field not in ('high', 'low'):
                raise ValueError('Explicit saved research high/low required')
            box = boxes[selector['box_id']]
            price = box['research_bounds'][field]; origin_id = box['id']
            occurred = box['source_end']; known = box['confirmed_at']
            qualification = 'CONFIRMED_RESEARCH_BOUND'
            evidence[origin_id] = dict(id=origin_id, source_end=occurred, confirmed_at=known,
                                       research_bounds=deepcopy(box['research_bounds']))
        else:
            raise ValueError('No automatic or manual-audit reference selection supported')
        if price is None:
            raise ValueError('Cannot select missing source value')
        refs.append(dict(id=fingerprint(dict(binding=context, selector=selector)), binding={k: context[k] for k in BINDING},
                         price=price, origin_id=origin_id, source_kind=kind, source_field=field,
                         occurred_at=occurred, known_on=known, selected_at=selected_at,
                         historical_selection_time=None, historical_signal_eligible=False,
                         qualification=qualification, explicit_selector=deepcopy(selector)))
    return dict(schema_version='reaction-facts-input/0.1', context=context,
                bars=deepcopy(data['bars']), macd=deepcopy(data['macd']), references=refs,
                research_reference_evidence=evidence,
                known_gap_dates=deepcopy(data['source_gaps']['known_calendar_missing_dates']),
                basis_break_dates=deepcopy(core.get('data_gaps', {}).get('basis_resets', [])),
                limits=dict(source_gaps=deepcopy(data['source_gaps']),
                            corporate_action_comparability=c.get('corporate_action_comparability', 'UNVERIFIED'),
                            adjusted_five_year_history='NOT_AVAILABLE', historical_publication_timing='UNVERIFIED',
                            calendar_completeness='NOT_EXHAUSTIVE_NO_SYNTHETIC_RECORDS',
                            known_gap_handling='CONSERVATIVE_SEGMENT_BREAK_NOT_PROOF_OF_MISSING_TRADING_DAY',
                            formal_boundaries_volume_weights_decay_importance_merge_succession_lifecycle='UNKNOWN',
                            darvas_full_text='NOT_FULLY_VERIFIED', sqlite_root_cause='NOT_ESTABLISHED',
                            reference_selection='EXTERNAL_EXPLICIT_SELECTORS_NOT_AUTOMATIC_PRESSURE_SELECTION'))
