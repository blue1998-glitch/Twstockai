"""Read-only projection of saved graph0.2 events. No price/strategy calculations."""
from copy import deepcopy
from datetime import date
from graph_core.core import fingerprint

STOP='OBSERVATION_STOPPED_AT_DATA_OR_BASIS_GAP'

def project(result, stock, *, dates=None):
    """Explicit observed-date coverage, default current batch only (bounded index)."""
    if stock.get('status') not in ('ANALYZED_FINMIND_HISTORY','ANALYZED_RETAINED_HISTORY','ANALYZED_RESEARCH','SEGMENTED_RESEARCH','INSUFFICIENT_HISTORY'):raise ValueError('Source/analysis status not eligible for event projection')
    cutoff=result['as_of'];date.fromisoformat(cutoff)
    if result['schema_version']!='graph-recognition-research/0.2':raise ValueError('Unsupported saved core')
    if result['result_id']!=fingerprint({k:v for k,v in result.items() if k!='result_id'}):raise ValueError('Saved result fingerprint mismatch')
    if stock.get('result_id') and stock['result_id']!=result['result_id']:raise ValueError('Declared result identity mismatch')
    ctx=result['context']
    if ctx['code']!=stock['code'] or ctx.get('exchange')!=stock['market'] or stock['as_of']!=cutoff:
        raise ValueError('Saved event stock/market/cutoff mismatch')
    selected=sorted(set(dates if dates is not None else [cutoff]))
    if any(date.fromisoformat(d)>date.fromisoformat(cutoff) for d in selected):raise ValueError('Future event coverage refused')
    gaps=deepcopy(result['data_gaps']);records=[]
    for collection in ('boxes','reference_candidates'):
        for i,candidate in enumerate(result[collection]):
            cid=candidate.get('id') if collection=='boxes' else candidate.get('pivot_id')
            if not cid:raise ValueError('Missing original candidate identity')
            stopped=False
            for j,event in enumerate(candidate['path']['events']):
                day=event['date'];observed=event['first_observed_at'];date.fromisoformat(day);date.fromisoformat(observed)
                if not day<=observed<=cutoff or candidate['confirmed_at']>observed:
                    raise ValueError('Impossible event/confirmation chronology')
                if stopped:raise ValueError('Event after original observation stopped')
                if event['type']==STOP:stopped=True
                if observed not in selected:continue
                missing=set(gaps['missing_expected_dates'])|set(gaps['missing_price_rows'])|set(gaps['basis_resets'])
                if day in missing and event['type']!=STOP:raise ValueError('Non-stop event on missing/reset date')
                records.append(dict(candidate_id=cid,collection=collection,
                    original_pointer=f'/{collection}/{i}/path/events/{j}',original_event_id=event.get('id'),
                    volume_evidence_available='volume' in event,type=event['type'],date=day,first_observed_at=observed,confirmed_at=candidate['confirmed_at'],
                    candidate_source=deepcopy(candidate.get('source',candidate.get('source_dates',candidate.get('source_turn_ids')))),
                    candidate_qualification=candidate['qualification'],path_qualification=candidate['path']['qualification'],
                    observation_qualification='STOPPED_NOT_COMPARABLE' if event['type']==STOP else
                      'HISTORICAL_ONLY_NOT_CURRENT_COMPARABLE' if any(d>day for d in gaps['basis_resets']) else 'OBSERVED_RESEARCH_FACT_NOT_TRADE_SIGNAL'))
    return dict(version='graph-event-radar/0.1',result_id=result['result_id'],result_fingerprint=fingerprint(result),
        source_prefix_fingerprint=result['source_prefix_fingerprint'],code=stock['code'],market=stock['market'],as_of=cutoff,
        source_id=ctx['source_id'],price_basis_id=ctx['price_basis_id'],historical_available_at='UNKNOWN',
        corporate_action_comparability=result['corporate_action_comparability'],data_gaps=gaps,
        pending_count=len(result['pending_extrema']),pending_are_events=False,coverage=dict(first_observed_dates=selected,complete_for_selected_dates=True,all_history=False),
        events=records,formal_authorized=False,primary_pressure_id=None)
