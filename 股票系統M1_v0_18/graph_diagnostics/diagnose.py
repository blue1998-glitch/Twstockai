"""Trace original enumeration, date semantics and exact source relationships.

No manual answers, thresholds, file I/O, UI, storage or new recognition rules.
The original core remains the authority. Any divergence fails closed.
"""
from collections import Counter
from copy import deepcopy
from decimal import Decimal, localcontext

from graph_core.core import VERSION as CORE_VERSION, _validate, _pivots, _range
from graph_core.core import fingerprint, number, ratio

VERSION = 'graph-recognition-diagnostics/0.1'


def range_checks(points, tolerance):
    """All applicable checks, signed margins and exact extreme witnesses."""
    highs = [p for p in points if p['kind'] == 'HIGH']
    lows = [p for p in points if p['kind'] == 'LOW']
    reasons = []
    metrics = dict(high_count=len(highs), low_count=len(lows),
                   high_count_margin=len(highs)-2, low_count_margin=len(lows)-2)
    if len(highs) < 2: reasons.append('FEWER_THAN_TWO_HIGHS')
    if len(lows) < 2: reasons.append('FEWER_THAN_TWO_LOWS')
    witnesses = {}
    if highs and lows:
        hh = max(number(p['price']) for p in highs)
        lh = min(number(p['price']) for p in highs)
        hl = max(number(p['price']) for p in lows)
        ll = min(number(p['price']) for p in lows)
        span = hh-ll
        allowed = span*tolerance
        metrics.update({k:format(v,'f') for k,v in dict(
            span=span, allowed_cluster_spread=allowed,
            high_cluster_spread=hh-lh, low_cluster_spread=hl-ll,
            high_spread_margin=allowed-(hh-lh), low_spread_margin=allowed-(hl-ll),
            common_corridor_margin=lh-hl).items()})
        metrics.update(high_spread_to_span=ratio(hh-lh,span), low_spread_to_span=ratio(hl-ll,span))
        for name, pool, value in [('highest_high',highs,hh),('lowest_high',highs,lh),
                                 ('highest_low',lows,hl),('lowest_low',lows,ll)]:
            witnesses[name] = [p['id'] for p in pool if number(p['price']) == value]
        if span <= 0: reasons.append('NONPOSITIVE_SPAN')
        if hh-lh > allowed: reasons.append('HIGH_CLUSTER_SPREAD_EXCEEDS_RESEARCH_LIMIT')
        if hl-ll > allowed: reasons.append('LOW_CLUSTER_SPREAD_EXCEEDS_RESEARCH_LIMIT')
        if lh <= hl: reasons.append('NO_POSITIVE_COMMON_CORRIDOR')
    # Check against the untouched implementation, not merely a mirrored formula.
    if (not reasons) != (_range(points,tolerance) is not None):
        raise ValueError('Diagnostic range checks diverged from original core')
    return dict(passed=not reasons, first_failed_check=reasons[0] if reasons else None,
                failed_checks=reasons, metrics=metrics, witnesses=witnesses)


def enumeration_trace(result):
    traces=[]; emitted=[]; no_valid_endpoints=0
    tolerance=number(result['parameters']['cluster_spread_fraction'])
    for scale in result['parameters']['reversals']:
        points=[p for p in result['pivots'] if p['scale']==scale]
        seen=set()
        for end in range(3,len(points)):
            group=[p for p in points[:end+1] if p['segment']==points[end]['segment']]
            if len(group)<4: continue
            evaluated=[range_checks(group[start:],tolerance) for start in range(len(group)-3)]
            valid=[i for i,e in enumerate(evaluated) if e['passed']]
            chosen=([valid[0]] if valid else [])
            seed=len(group)-4
            if seed in valid and seed not in chosen: chosen.append(seed)
            if not valid: no_valid_endpoints+=1
            chosen_ids=[]
            for start in chosen:
                turns=group[start:]; bounds=_range(turns,tolerance)
                chosen_ids.append(fingerprint(dict(scale=scale,turns=[p['id'] for p in turns],bounds=bounds)))
            for start,checks in enumerate(evaluated):
                turns=group[start:]; key=(turns[0]['occurred_index'],turns[-1]['occurred_index'],scale)
                role=[]; box_id=None
                if chosen and start==chosen[0]: role.append('LONGEST_COMPATIBLE_RUN')
                if start==seed and start in chosen: role.append('LATEST_FOUR_TURN_SEED')
                if not checks['passed']: decision='REJECTED_GEOMETRY'
                elif start not in chosen: decision='VALID_NOT_SELECTED_BY_LONGEST_OR_FOUR_TURN_POLICY'
                elif key in seen: decision='DEDUPLICATED_EXISTING_SOURCE_ENDPOINTS'
                else:
                    decision='EMITTED'; seen.add(key)
                    box_id=chosen_ids[chosen.index(start)]; emitted.append(box_id)
                trace=dict(scale=scale,segment=turns[-1]['segment'],
                    first_turn_id=turns[0]['id'],last_turn_id=turns[-1]['id'],
                    source_turn_slice=dict(scale=scale,segment=turns[-1]['segment'],start=start,end=len(group)-1),source_start=turns[0]['occurred_at'],
                    source_last_turn=turns[-1]['occurred_at'],observed_at=turns[-1]['confirmed_at'],
                    first_index=turns[0]['occurred_index'],last_index=turns[-1]['occurred_index'],
                    checks=checks,decision=decision,selection_roles=role,box_id=box_id,
                    selected_alternative_ids=chosen_ids)
                trace['id']=fingerprint(dict(scale=scale,segment=turns[-1]['segment'],first=trace['first_turn_id'],last=trace['last_turn_id']))
                traces.append(trace)
    if emitted != [b['id'] for b in result['boxes']]:
        raise ValueError('Enumeration trace differs from frozen original box list')
    if no_valid_endpoints != result['rejected_geometry_runs']:
        raise ValueError('Original rejected_geometry_runs means endpoints without any valid suffix')
    return traces


def _windows(rows,box,resets):
    a=box['first_index']; b=box['last_index']; formed=box['formed_index']
    end=next((i for i in range(formed,len(rows)) if rows[i]['date'] in resets or rows[i]['close'] is None),len(rows))
    observed=rows[formed:end]
    first_out=next((r for r in observed if number(r['close'])<number(box['research_bounds']['low']) or number(r['close'])>number(box['research_bounds']['high'])),None)
    exit_index=next((i for i in range(formed,end) if rows[i] is first_out),None)
    # The legacy field clamps to formed_index when already outside on formation.
    prior_exit=rows[exit_index-1]['date'] if exit_index is not None and exit_index>formed else None
    return dict(source_turn_span=dict(start=rows[a]['date'],end=rows[b]['date'],records=b-a+1,
                    meaning='FIRST_TO_LAST_TURN_OCCURRENCE_NOT_FORMAL_MEMBERSHIP'),
        confirmation_lag_records=formed-b,
        path_observation=dict(start=observed[0]['date'] if observed else None,
            end=observed[-1]['date'] if observed else None,records=len(observed),
            stopped_at=rows[end]['date'] if end<len(rows) else None,
            qualification='FROM_CONFIRMATION_INCLUSIVE_UNEQUAL_FOLLOWUP_NOT_NORMALIZED_IMPORTANCE'),
        decline_measurement=dict(start=observed[0]['date'] if observed else None,
            end=observed[-1]['date'] if observed else None,records=len(observed),
            maximum_date=box['path']['maximum_downside_date'],
            records_after_formation_to_maximum=box['path']['records_from_formation_to_maximum_low'],
            qualification='MAXIMUM_OVER_THIS_WINDOW_NOT_ONLY_UNTIL_MINIMUM_OR_FAST_SLOW_RULE'),
        source_volume_window=dict(start=rows[a]['date'],end=rows[b]['date'],records=b-a+1,
            missing_dates=deepcopy(box['volume']['missing_dates'])),
        prior_volume_window=deepcopy(box['volume']['prior_equal_record_window']),
        date_semantics=dict(source_last_turn=box['source_end'],confirmed_at=box['confirmed_at'],
            first_outside_close_at=first_out['date'] if first_out else None,
            previous_observed_inside_record=prior_exit,
            outside_on_formation=bool(first_out and first_out is observed[0]),
            legacy_first_departure_range_end=box['path']['first_departure_range_end'],
            legacy_clamps_to_formation_when_already_outside=True,
            first_below_close_at=box['path']['first_breakdown_at'],
            formal_whole_box_end=None,formal_membership=None))


def _volume_windows(rows,index,resets):
    floor=max([0]+[i+(1 if r['close'] is None else 0) for i,r in enumerate(rows[:index+1])
                     if r['date'] in resets or r['close'] is None])
    windows={}
    for count in (1,5,20):
        previous=rows[max(floor,index-count):index]
        windows[str(count)]=dict(start=previous[0]['date'] if previous else None,
            end=previous[-1]['date'] if previous else None,requested_records=count,records=len(previous),
            missing_volume_dates=[r['date'] for r in previous if r['volume_shares_scaled'] is None],
            complete=len(previous)==count and all(r['volume_shares_scaled'] is not None for r in previous),
            includes_observed_day=False)
    return dict(observed_at=rows[index]['date'],current_volume_known=rows[index]['volume_shares_scaled'] is not None,
        previous_windows=windows,qualification='DESCRIPTIVE_NO_VOLUME_EXPANSION_OR_OWNERSHIP_THRESHOLD')


def presentation_trace(result):
    boxes=result['boxes']; byid={b['id']:b for b in boxes}
    front=[byid[i] for i in result['comparison']['pareto_frontier_ids']]
    criteria=[('LONG_CONTEXT_DISPLAY_NOT_PRIMARY_RANK',front,'duration_records',True),
        ('NEAREST_UPPER_BAND_DISPLAY_NOT_SIGNIFICANCE',front,'pressure_distance_fraction',False),
        ('REPEATED_TURNS_DISPLAY',front,'turns',True),
        ('LATEST_FORMED_DISPLAY',boxes,'confirmed_at',True),
        ('CROSSED_RANGE_CONTEXT_DISPLAY',[b for b in boxes if b['usable_at_anchor'] and b['anchor_relation']=='ABOVE'],'duration_records',True)]
    traces=[]; chosen=[]
    for name,pool,key,reverse in criteria:
        ordered=sorted(pool,key=lambda b:number(b[key]) if key=='pressure_distance_fraction' else b[key],reverse=reverse)
        winner=ordered[0]['id'] if ordered else None
        if winner and winner not in chosen: chosen.append(winner)
        traces.append(dict(criterion=name,field=key,direction='DESCENDING' if reverse else 'ASCENDING',
            eligible_ids=[b['id'] for b in pool],winner_id=winner,
            tie_rule='STABLE_ORIGINAL_CANDIDATE_ORDER_NOT_APPROVED_SIGNIFICANCE'))
    return dict(selected_ids=chosen,criteria=traces,qualification='UI_DIVERSITY_NOT_RECOGNITION_REJECTION_OR_IMPORTANCE')


def diagnose(payload,result):
    """Deterministic prefix-only diagnostic sidecar. Original result untouched."""
    if any(k in payload for k in ('manual_cases','references')): raise ValueError('Manual answers refused')
    with localcontext() as ctx:
        ctx.prec=50
        content={k:v for k,v in result.items() if k!='result_id'}
        if result['schema_version']!=CORE_VERSION or fingerprint(content)!=result['result_id']:
            raise ValueError('Original core identity mismatch')
        context,rows,resets,missing,gaps,cfg=_validate(payload,result['as_of'],result['parameters'])
        if fingerprint(rows)!=result['source_prefix_fingerprint'] or context!=result['context']:
            raise ValueError('Diagnostic source/basis/prefix mismatch')
        points=[]
        for scale in cfg['reversals']: points+=_pivots(rows,scale,resets)[0]
        if points!=result['pivots']: raise ValueError('Original confirmed turns differ from source')
        traces=enumeration_trace(result); bypivot={p['id']:p for p in points}; boxes=result['boxes']
        geometry={}; geom_for={}
        for b in boxes:
            signature=[dict(kind=bypivot[i]['kind'],price=format(number(bypivot[i]['price']).normalize(),'f'),
                occurred_at=bypivot[i]['occurred_at'],source_dates=bypivot[i]['source_dates']) for i in b['source_turn_ids']]
            key=fingerprint(dict(segment=b['segment'],turn_geometry=signature))
            geometry.setdefault(key,[]).append(b['id']);geom_for[b['id']]=key
        presentation=presentation_trace(result);details=[];edges=[]
        for b in boxes:
            earlier=[p for p in boxes if p['scale']==b['scale'] and p['segment']==b['segment']
                and p['confirmed_at']<b['confirmed_at'] and len(p['source_turn_ids'])<len(b['source_turn_ids'])
                and b['source_turn_ids'][:len(p['source_turn_ids'])]==p['source_turn_ids']]
            nearest=max((p['turns'] for p in earlier),default=0)
            predecessors=[p['id'] for p in earlier if p['turns']==nearest]
            edges.extend(dict(from_id=i,to_id=b['id'],observed_at=b['confirmed_at'],
                relation='EXACT_SAME_SCALE_SOURCE_ID_PREFIX_EXTENSION_NOT_FORMAL_MERGE') for i in predecessors)
            local_of=[p['id'] for p in boxes if p['id']!=b['id'] and p['scale']==b['scale'] and p['segment']==b['segment']
                and len(p['source_turn_ids'])>len(b['source_turn_ids'])
                and any(p['source_turn_ids'][i:i+b['turns']]==b['source_turn_ids'] for i in range(1,p['turns']-b['turns']+1))]
            later=[dict(id=p['id'],source_start=p['start'],confirmed_at=p['confirmed_at'],
                relation_observed_at=max(b['confirmed_at'],b['path']['first_breakdown_at'],p['confirmed_at']))
                for p in boxes if p['id'] in b['successor_after_breakdown_ids']]
            emitted=next(t for t in traces if t['box_id']==b['id'])
            detail=dict(box_id=b['id'],enumeration_trace_id=emitted['id'],
                same_geometry_group_id=geom_for[b['id']],
                same_geometry_other_ids=[i for i in geometry[geom_for[b['id']]] if i!=b['id']],
                same_geometry_relations=[dict(other_id=p['id'],observed_at=max(b['confirmed_at'],p['confirmed_at']),
                    qualification='EQUAL_ORDERED_SOURCE_GEOMETRY_NOT_EQUAL_CONFIRMATION_OR_INDEPENDENT_VOTE')
                    for p in boxes if p['id']!=b['id'] and geom_for[p['id']]==geom_for[b['id']]],
                immediate_source_prefix_predecessor_ids=predecessors,all_source_prefix_ancestor_ids=[p['id'] for p in earlier],
                local_subsequence_of_ids=local_of,
                relation_qualification='EXACT_SOURCE_RELATIONS_ONLY_NOT_DISTINCT_ECONOMIC_PATTERN_OR_APPROVED_MERGE',
                geometric_parent_ids=deepcopy(b['parent_ids']),
                later_after_breakdown=later,direct_successor_id=None,direct_succession='UNKNOWN_TIME_ORDER_DOES_NOT_ESTABLISH_DIRECT_SUCCESSION',
                windows=_windows(rows,b,resets),
                event_volume_window_dates=[e['date'] for e in b['path']['events'] if 'volume' in e],
                default_display=dict(selected=b['id'] in presentation['selected_ids'],
                    criteria=[dict(criterion=c['criterion'],eligible=b['id'] in c['eligible_ids'],
                        winner_id=c['winner_id'],selected=c['winner_id']==b['id']) for c in presentation['criteria']],
                    original_dominated_by=deepcopy(b.get('research_dominated_by',[])),
                    usable_at_anchor=b['usable_at_anchor'],anchor_relation=b['anchor_relation'],
                    reason='SELECTED_UI_DIVERSITY' if b['id'] in presentation['selected_ids'] else 'NO_UI_CRITERION_WIN_NOT_ENGINE_MISS'))
            details.append(detail)
        volume_dates={result['as_of']}|{day for b in details for day in b['event_volume_window_dates']}
        report=dict(schema_version=VERSION,core_result_id=result['result_id'],as_of=result['as_of'],
            context=deepcopy(context),source_prefix_fingerprint=result['source_prefix_fingerprint'],
            original_parameters=deepcopy(cfg),enumeration=traces,boxes=details,presentation=presentation,
            enumeration_scope=dict(
                starts='ONLY_CONFIRMED_TURN_OCCURRENCES_NOT_ARBITRARY_DAILY_OR_MONTH_ENDPOINTS',
                ends='EVERY_CONFIRMED_TURN_WITH_AT_LEAST_FOUR_TURNS_IN_SEGMENT',
                source_turn_sequences=[dict(scale=scale,segment=segment,turn_ids=[p['id'] for p in points if p['scale']==scale and p['segment']==segment])
                    for scale in cfg['reversals'] for segment in sorted({p['segment'] for p in points if p['scale']==scale})],
                pending_extrema=deepcopy(result['pending_extrema']),ambiguities=deepcopy(result['ambiguities']),
                qualification='NO_TRIAL_FOR_A_NON_TURN_ENDPOINT_NOT_A_GEOMETRY_REJECTION'),
            volume_observation_windows={r['date']:_volume_windows(rows,i,resets) for i,r in enumerate(rows) if r['date'] in volume_dates},
            geometry_groups=[dict(id=k,box_ids=v,independent_pattern_votes=False) for k,v in geometry.items()],
            source_prefix_version_edges=edges,
            summary=dict(candidate_versions=len(boxes),exact_source_geometry_groups=len(geometry),
                independent_pattern_count=None,accuracy=None,
                enumeration_decisions=dict(Counter(t['decision'] for t in traces)),
                original_rejected_geometry_runs_meaning='ENDPOINTS_WITH_NO_VALID_SUFFIX_NOT_REJECTED_TRIAL_COUNT'),
            formal_membership=None,primary_pressure_id=None,core_modified=False,manual_answers_used=False,
            qualified_interpretation='DIAGNOSTICS_ONLY_NOT_RECOGNITION_IMPROVEMENT_OR_APPROVAL',
            historical_information_availability=result['historical_information_availability'],
            core_usefulness='NOT_ESTABLISHED',classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED')
        report['diagnostic_id']=fingerprint(report)
        return report
