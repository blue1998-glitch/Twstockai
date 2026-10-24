"""Versioned descriptive facts; no decay, anomaly threshold, zone or trade score.
Calendar-month source slices are navigation containers, NOT consolidation rules.
All inputs must be a selected analysis prefix on one explicit price basis.
"""
from calendar import monthrange
from datetime import date
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from copy import deepcopy
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from contracts import fingerprint, validate_candles

VERSION='left-pressure-source-facts/0.1'
UNKNOWN=dict(time_decay=None,anomalous_volume_threshold=None,anomalous_price_threshold=None,
    consolidation_boundaries=None,automatic_wall_selection=None,automatic_boss_selection=None,
    decline_speed_classification=None,remaining_trapped_ownership=None,volume_expansion_baseline=None,
    volume_expansion_threshold=None,volume_expansion_duration=None,action_qualification='NOT_EVALUATED')
D=Decimal


def relation(value,reference):
    if value is None or reference is None:return 'UNKNOWN'
    return 'ABOVE' if D(value)>D(reference) else 'BELOW' if D(value)<D(reference) else 'AT'


def volume_facts(rows):
    known=[r for r in rows if r.get('volume_shares_scaled') is not None]
    missing=[r['date'] for r in rows if r.get('volume_shares_scaled') is None]
    total=sum((D(r['volume_shares_scaled']) for r in known),D(0))
    peak=max((D(r['volume_shares_scaled']) for r in known),default=None)
    return dict(total_shares=None if missing else format(total,'f'),known_volume_subtotal_shares=format(total,'f'),
        max_single_day_shares=None if missing or peak is None else format(peak,'f'),
        max_single_day_dates=[] if missing else [r['date'] for r in known if D(r['volume_shares_scaled'])==peak],missing_volume_dates=missing,
        known_volume_max_single_day_shares=None if peak is None else format(peak,'f'),
        interpretation='SUPPLIED_DAILY_TURNOVER_NOT_CERTIFIED_FULL_INTERVAL_NOT_REMAINING_OWNERSHIP_OR_PRICE_DISTRIBUTION')


def _interval_facts(rows,start,end,*,code,mode,basis_id,as_of,spec_id=None):
    """Explicit inclusive source-date range. Never infer a formal region boundary."""
    if not rows or rows[-1]['date']!=as_of or any(r['date']>as_of for r in rows):raise ValueError('Exact nonfuture analysis prefix required')
    if start>end or start>as_of:raise ValueError('Invalid/future source interval')
    chosen=[(i,r) for i,r in enumerate(rows) if start<=r['date']<=min(end,as_of)]
    if not chosen:raise ValueError('Interval has no actual source bars')
    indexes=[i for i,_ in chosen];part=[r for _,r in chosen]
    high=max(D(r['high']) for r in part);low=min(D(r['low']) for r in part)
    last=indexes[-1];tail=rows[last+1:];observed_end=part[-1]['date']
    low_after=min((D(r['low']) for r in tail),default=None)
    low_after_index=next((i for i in range(last+1,len(rows)) if D(rows[i]['low'])==low_after),None)
    changes=[]
    for i in range(last+1,len(rows)):
        a,b=rows[i-1],rows[i]
        if D(a['close'])>0:changes.append((i,(D(b['close'])/D(a['close'])-1)*100))
    largest=min(changes,key=lambda x:x[1],default=None)
    frozen=end<=as_of
    events=[];prior=relation(part[-1]['close'],str(high))
    # Facts use an already fully observed, caller-selected interval high. Never
    # freeze a still-growing month or attach a retrospectively higher threshold.
    if frozen:
        for r in tail:
            now=relation(r['close'],str(high))
            kind='CLOSE_ABOVE_SELECTED_SOURCE_HIGH' if now=='ABOVE' and prior!='ABOVE' else 'CLOSE_RETURNED_TO_OR_BELOW_SELECTED_SOURCE_HIGH' if now!='ABOVE' and prior=='ABOVE' else None
            if kind:
                event=dict(date=r['date'],type=kind,close=r['close'],reference_high=format(high,'f'),source_from=start,source_to=end,
                    basis_id=basis_id,code=code,price_mode=mode,rule_version=VERSION)
                event['event_id']=fingerprint(event);events.append(event)
            prior=now
    result=dict(schema_version='pressure-source-interval/0.1',producer_version=VERSION,code=code,price_mode=mode,basis_id=basis_id,
        analysis_as_of=as_of,spec_id=spec_id or fingerprint(dict(code=code,mode=mode,start=start,end=end)),
        requested_start=start,requested_end=end,actual_start=part[0]['date'],actual_end=observed_end,
        from_index=indexes[0],to_index=last,bars=len(part),source_prefix_fingerprint=fingerprint(part),
        high=format(high,'f'),high_dates=[r['date'] for r in part if D(r['high'])==high],
        low=format(low,'f'),low_dates=[r['date'] for r in part if D(r['low'])==low],
        close_relation_to_high=relation(rows[-1]['close'],str(high)),volume=volume_facts(part),
        boundary_status='EXPLICIT_SOURCE_DATE_SLICE_NOT_FORMAL_CONSOLIDATION',
        frozen_reference='OBSERVED_THROUGH_REQUESTED_END' if frozen else 'OPEN_SLICE_NO_FIXED_THRESHOLD_EVENTS',
        elapsed_calendar_days=(date.fromisoformat(as_of)-date.fromisoformat(observed_end)).days,
        elapsed_supplied_bars=len(tail),after_interval=dict(path_from_index=last+1,path_to_index=len(rows)-1,
            lowest_low=None if low_after is None else format(low_after,'f'),lowest_low_date=None if low_after_index is None else rows[low_after_index]['date'],
            calendar_days_to_low=None if low_after_index is None else (date.fromisoformat(rows[low_after_index]['date'])-date.fromisoformat(observed_end)).days,
            supplied_bars_to_low=None if low_after_index is None else low_after_index-last,
            biggest_supplied_close_to_close_decline_pct=None if largest is None or largest[1]>=0 else format(largest[1],'f'),
            biggest_decline_date=None if largest is None or largest[1]>=0 else rows[largest[0]]['date'],
            speed_classification='UNKNOWN_NO_RAPID_OR_GRADUAL_THRESHOLD',path_is='DAILY_SOURCE_BARS_NOT_INTRADAY_PATH'),
        close_events=events,unknown=deepcopy(UNKNOWN))
    result['interval_snapshot_id']=fingerprint(result)
    return result


def interval_facts(*args,**kwargs):
    with localcontext() as ctx:
        ctx.prec=50;ctx.rounding=ROUND_HALF_EVEN
        return _interval_facts(*args,**kwargs)


def frame_facts(rows,*,code,mode,basis_id,as_of,regions=(),details=True):
    with localcontext() as ctx:
        ctx.prec=50;ctx.rounding=ROUND_HALF_EVEN
        if not rows or rows[-1]['date']!=as_of:raise ValueError('Exact prefix required')
        validate_candles(rows)
        left=rows[:-1];highest=max((D(r['high']) for r in left),default=None)
        hv=volume_facts(left);slices=[]
        for month in sorted({r['date'][:7] for r in rows}) if details else ():
            year,mon=map(int,month.split('-'));start=month+'-01';end=f'{month}-{monthrange(year,mon)[1]:02d}'
            slices.append(interval_facts(rows,start,end,code=code,mode=mode,basis_id=basis_id,as_of=as_of,spec_id='calendar-source:'+month))
        selected=[]
        for spec in regions:
            if spec['code']==code and spec['price_mode']==mode and spec['start']<=as_of:
                if spec['basis_id']!=basis_id:continue  # No cross-action projection of supplied ranges.
                selected.append(interval_facts(rows,spec['start'],spec['end'],code=code,mode=mode,basis_id=basis_id,as_of=as_of,spec_id=spec['id']))
        return dict(schema_version='left-pressure-frame/0.1',producer_version=VERSION,analysis_as_of=as_of,code=code,price_mode=mode,basis_id=basis_id,
            current_close=rows[-1]['close'],all_supplied_prefix_bars=len(rows),left_start=None if not left else left[0]['date'],left_end=None if not left else left[-1]['date'],
            price_wall_evidence=dict(highest_supplied_left_high=None if highest is None else format(highest,'f'),
                dates=[r['date'] for r in left if D(r['high'])==highest],close_relation=relation(rows[-1]['close'],None if highest is None else str(highest)),
                scope='SUPPLIED_LEFT_PREFIX_ONLY_NOT_LIFETIME_HIGH',wall_classification='UNKNOWN_NOT_AUTOMATIC_BOSS'),
            volume_wall_evidence={**hv,'wall_classification':'UNKNOWN_MAX_DAY_NOT_INTERVAL_TOTAL'},
            monthly_source_slices=slices,explicit_source_intervals=selected,unknown=deepcopy(UNKNOWN),
            interval_detail_status='EXPORTED_FOR_THIS_EXACT_DATE' if details else 'NOT_EXPORTED_FOR_THIS_DATE_NO_FUTURE_DETAIL_FALLBACK',
            older_pressure='CANNOT_EXCLUDE_BEFORE_AVAILABLE_START',price_distribution='NOT_AVAILABLE_FROM_DAILY_OHLCV')


def reviewed_layer(case,series,frame,evidence,rows):
    """A later manual review is a separate visible annotation, never an as-of signal."""
    exact=(series['code']==case['code'] and series['price_mode']==case['price_mode'] and frame['as_of']==case['analysis_as_of']
        and series['source']['id']==case['source_id'] and evidence['snapshot_id']==case['structure_snapshot_id'])
    if not exact:return None
    known={p['id']:p for p in evidence['pivots']}
    selected=case['confirmed_for_this_case'];refs=[selected['breakout_reference'],selected['next_primary_pressure_reference'],*selected['secondary_references']]
    for r in refs:
        p=known.get(r['id'])
        if not p or any(p[a]!=r[b] for a,b in [('occurred_at','date'),('price','price'),('confirmed_at','confirmed_at')]):raise ValueError('Reviewed reference/source mismatch')
        if p['confirmed_at']>frame['as_of']:raise ValueError('Future reference in review')
        if rows[p['occurred_index']]['high']!=p['price']:raise ValueError('Reviewed pivot is not original high')
    for row in case['source_observations']['volume_bars']:
        source=next((r for r in rows if r['date']==row[0]),None)
        if source is None or [source[k] for k in ('open','high','low','close','volume_shares_scaled')]!=row[1:]:raise ValueError('Reviewed source OHLCV mismatch')
    high=case['source_observations']['earlier_cluster_high'];source=next(r for r in rows if r['date']==high['date'])
    if source['high']!=high['price']:raise ValueError('Original wick mismatch')
    r=deepcopy(case);r['annotation_status']='RETROSPECTIVE_MANUAL_REVIEW_NOT_AN_ASOF_AUTOMATIC_RESULT'
    r['focus_reference_states']=[dict(reference=deepcopy(ref),close_relation=relation(frame['close'],ref['price'])) for ref in refs[:2]]
    r['bound_frame_id']=frame['frame_id'];r['post_breakout_data_status']='NOT_PROVIDED' if rows[-1]['date']<=case['analysis_as_of'] else 'REQUIRES_SEPARATE_BOUND_SOURCE'
    return r
