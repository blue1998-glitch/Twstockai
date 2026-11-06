"""Pure saved-result projection for 2..4-stock descriptive comparison; no scoring."""
from copy import deepcopy
from graph_core.core import fingerprint
from graph_core.event_radar import project as radar_project
from graph_core_chart.comparison_export import reference_summary,BOX_FIELDS,null_reasons


def project(saved,stock,source):
    r=saved['result'];p=saved['input'];bars=p['bars']
    # Reuse original observed-event eligibility, chronology and result binding.
    events=radar_project(r,stock)
    if p['context']!=r['context'] or len(bars)!=r['source_records'] or fingerprint(bars)!=r['source_prefix_fingerprint']:
        raise ValueError('Saved input/core prefix mismatch')
    if not bars or bars[-1]['date']!=r['as_of'] or r['anchor']['date']!=r['as_of']:
        raise ValueError('Wrong source cutoff; no nearest date substituted')
    if source.get('id')!=r['context']['source_id'] or not r['context']['price_basis_id']:raise ValueError('Comparison source/basis binding missing or different')
    if r['classification_quality']!='NOT_VALIDATED' or r['comparison']['primary_pressure_id'] is not None:raise ValueError('Formal classification/primary-pressure promotion refused')
    latest,nearest,ties=reference_summary(r)
    boxes=[]
    for box in r['boxes']:
        value={k:deepcopy(box[k]) for k in BOX_FIELDS}
        value.update(whole_range_location=box['path']['last_close_location'] if box['usable_at_anchor'] else 'NOT_COMPARABLE_AFTER_GAP',path_summary={k:deepcopy(v) for k,v in box['path'].items() if k!='events'})
        boxes.append(value)
    value=dict(schema='stock-comparison-evidence/0.1',code=stock['code'],market=stock['market'],identity=stock['identity'],status=stock['status'],
        as_of=r['as_of'],source_start=bars[0]['date'],source_end=bars[-1]['date'],records=len(bars),source_id=r['context']['source_id'],
        price_basis_id=r['context']['price_basis_id'],price_mode=r['context']['price_mode'],source_kind=r['context'].get('source_kind','UNKNOWN'),
        source=deepcopy(source),result_id=r['result_id'],source_prefix_fingerprint=r['source_prefix_fingerprint'],
        anchor=deepcopy(r['anchor']),anchor_volume=deepcopy(r['anchor_volume']),latest_confirmed_by_scale=latest,pending_extrema=deepcopy(r['pending_extrema']),
        reference_candidates=[{k:deepcopy(v) for k,v in c.items() if k!='path'}|{'last_relation':c['path']['last_relation']} for c in r['reference_candidates']],
        boxes=boxes,nearest_above=dict(distance_fraction=None if nearest is None else str(nearest),candidate_ids=ties,role='DISPLAY_DISTANCE_ONLY_ALL_TIES_NOT_PRIMARY_OR_STOCK_RANKING'),
        current_events=events['events'],event_coverage=events['coverage'],data_gaps=deepcopy(r['data_gaps']),
        historical_available_at='UNKNOWN',corporate_action_comparability=r['corporate_action_comparability'],
        classification_quality=r['classification_quality'],primary_pressure_id=r['comparison']['primary_pressure_id'],
        policy_authorized=False,live_execution_authorized=False,unvalidated=dict(strength_score=None,buy_point='UNKNOWN',remaining_upside='UNKNOWN',future_return='UNKNOWN',risk_probability='UNKNOWN',capital_efficiency='UNKNOWN'))
    value['null_reasons']=null_reasons(value)
    return value
