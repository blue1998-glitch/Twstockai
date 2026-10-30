"""Causal multiscale swing/range evidence, independent of manual case answers."""
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, localcontext
import hashlib
import json

VERSION = 'graph-recognition-research/0.1'
DEFAULT_CONFIG = dict(reversals=['0.03','0.06','0.12'], cluster_spread_fraction='0.35',
    enumeration='LONGEST_COMPATIBLE_RUN_AND_LATEST_FOUR_TURN_SEED',
    minimum_high_turns=2, minimum_low_turns=2,
    status='RESEARCH_SETTINGS_NOT_USER_APPROVED_STRATEGY')


def fingerprint(value):
    raw=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    return 'sha256:'+hashlib.sha256(raw.encode()).hexdigest()


def number(value):
    if not isinstance(value,str):raise ValueError('Exact numeric source string required')
    try:d=Decimal(value)
    except Exception as error:raise ValueError('Invalid numeric source') from error
    if not d.is_finite():raise ValueError('Finite numeric source required')
    return d


def ratio(a,b):
    if a is None or b is None or b==0:return None
    with localcontext() as ctx:
        ctx.prec=50
        return format(a/b,'f')


def relation(value,low,high):
    return 'ABOVE' if value>high else 'BELOW' if value<low else 'INSIDE'


def trace_reference(bars,price,known_index,*,stop_dates=()):
    """Factual close crossings only after reference is known. No breakout rule."""
    p=number(price);events=[];prior=None;up=None;down=None
    for i in range(known_index,len(bars)):
        row=bars[i]
        if row['date'] in stop_dates or row['close'] is None:
            events.append(dict(type='OBSERVATION_STOPPED_AT_DATA_OR_BASIS_GAP',date=row['date'],first_observed_at=row['date']))
            prior='NOT_COMPARABLE_AFTER_GAP';break
        close=number(row['close']);side='ABOVE' if close>p else 'BELOW' if close<p else 'EQUAL'
        if prior is not None and side!=prior:
            kind='CLOSE_CROSS_UP' if side=='ABOVE' else 'CLOSE_CROSS_DOWN' if side=='BELOW' else 'CLOSE_EQUALS_REFERENCE'
            event=dict(type=kind,date=row['date'],first_observed_at=row['date'],close=row['close'],reference_price=price)
            if side=='BELOW' and up is not None:event.update(type='FAILED_UP_RETURN_BELOW',previous_up_at=up)
            if side=='ABOVE' and down is not None:event.update(type='RETURN_ABOVE_AFTER_DOWN',previous_down_at=down)
            events.append(event)
            if side=='ABOVE':up=row['date'];down=None
            if side=='BELOW':down=row['date'];up=None
        prior=side
    return dict(reference_price=price,known_from=bars[known_index]['date'],events=events,last_relation=prior,
                qualification='COMPLETED_CLOSE_FACTS_NOT_CONFIRMED_BREAKOUT_OR_INTRADAY_ORDER')


def _validate(payload,as_of,config):
    if payload.get('schema_version')!='graph-recognition-input/0.1':raise ValueError('Unsupported graph input schema')
    date.fromisoformat(as_of)
    c=deepcopy(payload['context'])
    for key in ('code','source_id','price_basis_id'):
        if not isinstance(c.get(key),str) or not c[key]:raise ValueError('Explicit source/basis/code required')
    if c.get('price_mode') not in ('RAW_CANDIDATE','ADJUSTED_CANDIDATE'):raise ValueError('Explicit price mode required')
    if c.get('volume_unit')!='SHARES_REPORTED':raise ValueError('Reported shares required; no rescaling')
    if c['price_mode']=='ADJUSTED_CANDIDATE' and c.get('adjustment_anchor')!=as_of:raise ValueError('Adjusted anchor must match selected as_of')
    rows=deepcopy([r for r in payload['bars'] if r['date']<=as_of])
    if not rows or rows[-1]['date']!=as_of:raise ValueError('Exact supplied analysis day required')
    if any(a['date']>=b['date'] for a,b in zip(rows,rows[1:])):raise ValueError('Unique increasing source dates required')
    resets=set(payload.get('basis_break_dates',[]));expected=payload.get('expected_dates');missing=[]
    if expected is not None:
        dates={r['date'] for r in rows};missing=[d for d in expected if rows[0]['date']<=d<=as_of and d not in dates]
        for absent in missing:
            following=next((r['date'] for r in rows if r['date']>absent),None)
            if following:resets.add(following)
    gaps=[]
    for i,row in enumerate(rows):
        if any(k not in row for k in ('date','open','high','low','close','volume_shares_scaled')):raise ValueError('Explicit OHLCV fields required; unknown volume must be null')
        date.fromisoformat(row['date'])
        if row.get('price_basis_id',c['price_basis_id'])!=c['price_basis_id']:raise ValueError('Mixed row price basis refused')
        vals=[row.get(k) for k in ('open','high','low','close')]
        if any(v is None for v in vals):
            if not all(v is None for v in vals):raise ValueError('Partially missing OHLC is contradictory')
            gaps.append(row['date'])
        else:
            o,h,l,cl=map(number,vals)
            if min(o,h,l,cl)<=0 or not l<=min(o,cl)<=max(o,cl)<=h:raise ValueError('Invalid source OHLC')
        v=row.get('volume_shares_scaled')
        if v is not None and number(v)<0:raise ValueError('Negative source volume')
        if row.get('complete',True) is not True:raise ValueError('Incomplete daily candle refused')
        if row.get('available_at') is not None:
            available=datetime.fromisoformat(row['available_at'])
            if available.tzinfo is None:raise ValueError('Publication timestamp requires timezone')
            if available.date().isoformat()>as_of:raise ValueError('Source not available at selected date')
    if rows[-1]['close'] is None:raise ValueError('Missing analysis anchor close')
    cfg=deepcopy(config or DEFAULT_CONFIG)
    if cfg.get('status')!='RESEARCH_SETTINGS_NOT_USER_APPROVED_STRATEGY':raise ValueError('Research qualification cannot be promoted')
    rev=cfg['reversals']
    if not rev or len(set(rev))!=len(rev) or any(not 0<number(x)<1 for x in rev):raise ValueError('Distinct fractional reversal settings required')
    if not 0<number(cfg['cluster_spread_fraction'])<1:raise ValueError('Fractional cluster tolerance required')
    if cfg.get('minimum_high_turns')!=2 or cfg.get('minimum_low_turns')!=2 or cfg.get('enumeration')!=DEFAULT_CONFIG['enumeration']:raise ValueError('Unsupported range research algorithm')
    return c,rows,resets,missing,gaps,cfg


def _pivots(rows,reversal,resets):
    r=number(reversal);points=[];ambiguous=[];pending=[];direction=None;hi=lo=None;segment=0
    def extreme(i,key):return dict(index=i,price=rows[i][key],source_dates=[rows[i]['date']])
    def update(p,i,key,greater):
        value=number(rows[i][key]);old=number(p['price'])
        if (value>old if greater else value<old):return extreme(i,key)
        if value==old and rows[i]['date'] not in p['source_dates']:p['source_dates'].append(rows[i]['date'])
        return p
    for i,row in enumerate(rows):
        if row['date'] in resets or row['close'] is None:
            direction=None;hi=lo=None;segment+=1
            if row['close'] is None:continue
        if hi is None:hi=extreme(i,'high');lo=extreme(i,'low');continue
        close=number(row['close']);high=number(row['high']);low=number(row['low'])
        side='HIGH' if direction=='UP' else 'LOW' if direction=='DOWN' else None
        down=close<=number(hi['price'])*(1-r);up=close>=number(lo['price'])*(1+r)
        if direction is None:
            if up and down:
                ambiguous.append(dict(date=row['date'],reason='INITIAL_DIRECTION_CONFLICT',scale=reversal));hi=update(hi,i,'high',True);lo=update(lo,i,'low',False);continue
            if up:direction='UP';hi=update(hi,i,'high',True)
            elif down:direction='DOWN';lo=update(lo,i,'low',False)
            else:hi=update(hi,i,'high',True);lo=update(lo,i,'low',False)
            continue
        trigger=down if direction=='UP' else up
        p=hi if direction=='UP' else lo
        if (high if direction=='UP' else low)==number(p['price']) and row['date'] not in p['source_dates']:p['source_dates'].append(row['date'])
        stronger=high>number(hi['price']) if direction=='UP' else low<number(lo['price'])
        if trigger and stronger:
            ambiguous.append(dict(date=row['date'],reason='SAME_BAR_NEW_EXTREME_AND_REVERSAL_ORDER_UNKNOWN',scale=reversal))
        elif trigger and p['index']<i:
            point=dict(kind=side,price=p['price'],occurred_index=p['index'],occurred_at=rows[p['index']]['date'],
                source_dates=list(p['source_dates']),confirmed_index=i,confirmed_at=row['date'],first_observed_at=row['date'],
                scale=reversal,segment=segment,confirmation='LATER_COMPLETED_CLOSE_REVERSAL_RESEARCH')
            point['id']=fingerprint({k:point[k] for k in ('kind','price','occurred_at','confirmed_at','scale','segment')})
            points.append(point);direction='DOWN' if direction=='UP' else 'UP';hi=extreme(i,'high');lo=extreme(i,'low');continue
        hi=update(hi,i,'high',True) if direction=='UP' else hi
        lo=update(lo,i,'low',False) if direction=='DOWN' else lo
    if hi is not None:pending=[dict(direction=direction,high=hi,low=lo,qualification='UNCONFIRMED_NOT_A_PIVOT')]
    return points,ambiguous,pending


def _volume(rows,a,b,resets):
    selected=rows[a:b+1];known=[r for r in selected if r['volume_shares_scaled'] is not None]
    values=[number(r['volume_shares_scaled']) for r in known];floor=max([0]+[i+(1 if row['close'] is None else 0) for i,row in enumerate(rows[:a+1]) if row['date'] in resets or row['close'] is None]);baseline=rows[max(floor,a-len(selected)):a]
    baseline_complete=len(baseline)==len(selected) and all(r['volume_shares_scaled'] is not None for r in baseline)
    total=sum(values,Decimal(0));mean=total/len(selected) if len(known)==len(selected) else None
    previous_mean=sum((number(r['volume_shares_scaled']) for r in baseline),Decimal(0))/len(baseline) if baseline_complete else None
    maximum=max(values) if values else None
    return dict(unit='SHARES_REPORTED',records=len(selected),known_records=len(known),missing_dates=[r['date'] for r in selected if r['volume_shares_scaled'] is None],
        supplied_interval_total=format(total,'f') if len(known)==len(selected) else None,
        known_partial_sum=format(total,'f'),mean=format(mean,'f') if mean is not None else None,
        maximum=format(maximum,'f') if maximum is not None else None,
        maximum_dates=[r['date'] for r in known if number(r['volume_shares_scaled'])==maximum],
        prior_equal_record_window=dict(first_date=baseline[0]['date'] if baseline else None,last_date=baseline[-1]['date'] if baseline else None,complete=baseline_complete,includes_selected=False),
        mean_to_prior_ratio=ratio(mean,previous_mean),
        qualification='DESCRIPTIVE_RESEARCH_INTERVAL_VOLUME_NOT_APPROVED_REGION_MEASURE_OR_REMAINING_SHARES')


def _range(points,tolerance):
    highs=[number(p['price']) for p in points if p['kind']=='HIGH'];lows=[number(p['price']) for p in points if p['kind']=='LOW']
    if len(highs)<2 or len(lows)<2:return None
    span=max(highs)-min(lows)
    if span<=0:return None
    hs=max(highs)-min(highs);ls=max(lows)-min(lows)
    if hs>span*tolerance or ls>span*tolerance:return None
    # Repeated alternating turns must share a nonempty common vertical corridor.
    if min(highs)<=max(lows):return None
    return dict(low=format(min(lows),'f'),high=format(max(highs),'f'),
        pressure_band=[format(min(highs),'f'),format(max(highs),'f')],support_band=[format(min(lows),'f'),format(max(lows),'f')],
        high_cluster_spread_to_span=ratio(hs,span),low_cluster_spread_to_span=ratio(ls,span))


def _boxes(rows,points,tolerance,resets):
    boxes=[];seen=set();rejected=0
    for end in range(3,len(points)):
        group=[p for p in points[:end+1] if p['segment']==points[end]['segment']]
        if len(group)<4:continue
        valid=[]
        for start in range(len(group)-3):
            candidate=_range(group[start:],tolerance)
            if candidate is not None:valid.append((start,candidate))
        if not valid:rejected+=1;continue
        chosen=[valid[0]]
        seed=next((v for v in valid if v[0]==len(group)-4),None)
        if seed and seed!=chosen[0]:chosen.append(seed)
        for start,bounds in chosen:
            turns=group[start:];a=turns[0]['occurred_index'];b=turns[-1]['occurred_index'];known=turns[-1]['confirmed_index']
            key=(a,b,turns[-1]['scale'])
            if key in seen:continue
            seen.add(key)
            raw=rows[a:b+1];low=min(raw,key=lambda r:number(r['low']))['low'];high=max(raw,key=lambda r:number(r['high']))['high']
            box=dict(scale=turns[-1]['scale'],segment=turns[-1]['segment'],first_index=a,last_index=b,formed_index=known,
                start=rows[a]['date'],source_end=rows[b]['date'],first_observed_at=rows[known]['date'],confirmed_at=rows[known]['date'],
                source_turn_ids=[p['id'] for p in turns],turns=len(turns),duration_records=b-a+1,
                research_bounds=bounds,formal_price_bounds=None,formal_region_membership=None,
                display_extent=dict(low=low,high=high,source_rows_fingerprint=fingerprint(raw)),
                volume=_volume(rows,a,b,resets),qualification='AUTOMATIC_REPEATED_SWING_RANGE_CANDIDATE_NOT_APPROVED_BOX')
            box['id']=fingerprint(dict(scale=box['scale'],turns=box['source_turn_ids'],bounds=bounds))
            boxes.append(box)
    return boxes,rejected


def volume_observation(rows,index,resets=()):
    current=rows[index]['volume_shares_scaled'];ratios={}
    floor=max([0]+[i+(1 if r['close'] is None else 0) for i,r in enumerate(rows[:index+1]) if r['date'] in resets or r['close'] is None])
    for length in (1,5,20):
        baseline=rows[max(floor,index-length):index]
        complete=len(baseline)==length and all(r['volume_shares_scaled'] is not None for r in baseline)
        mean=sum((number(r['volume_shares_scaled']) for r in baseline),Decimal(0))/length if complete else None
        ratios[str(length)]=ratio(number(current) if current is not None else None,mean)
    return dict(current_shares=current,ratio_to_previous_means=ratios,baseline_includes_current=False,
                qualification='DESCRIPTIVE_1_5_20_RECORD_COMPARISONS_NOT_VOLUME_EXPANSION_OR_SETTLEMENT_RULE')


def _path(rows,box,resets,volume_cache):
    low=number(box['research_bounds']['low']);high=number(box['research_bounds']['high']);events=[];last=None;last_exit=None;range_end=None
    max_decline=Decimal(0);decline_date=None;first_breakdown=None
    for i in range(box['formed_index'],len(rows)):
        row=rows[i]
        if row['date'] in resets or row['close'] is None:
            events.append(dict(type='OBSERVATION_STOPPED_AT_DATA_OR_BASIS_GAP',date=row['date'],first_observed_at=row['date']))
            break
        cl=number(row['close']);loc=relation(cl,low,high)
        decline=(high-number(row['low']))/high
        if decline>max_decline:max_decline=decline;decline_date=row['date']
        if loc!=last:
            kind='INITIAL_CLOSE_LOCATION' if last is None else 'CLOSE_ABOVE_RESEARCH_RANGE' if loc=='ABOVE' else 'CLOSE_BELOW_RESEARCH_RANGE' if loc=='BELOW' else 'CLOSE_REENTERED_RANGE'
            if i not in volume_cache:volume_cache[i]=volume_observation(rows,i,resets)
            event=dict(type=kind,date=row['date'],first_observed_at=row['date'],previous=last,location=loc,close=row['close'],bounds_id=box['id'],volume=volume_cache[i])
            if loc=='INSIDE' and last_exit is not None:event.update(type='FAILED_UP_RETURN_IN_RANGE' if last_exit=='ABOVE' else 'RETURN_IN_RANGE_AFTER_BREAKDOWN')
            if last=='ABOVE' and loc=='BELOW':event['type']='FAILED_UP_AND_CROSSED_BELOW_RANGE'
            if loc=='BELOW' and first_breakdown is None:first_breakdown=row['date']
            if loc in ('ABOVE','BELOW'):
                last_exit=loc
                if range_end is None:range_end=rows[max(box['formed_index'],i-1)]['date']
            events.append(event)
        last=loc
    return dict(events=events,last_close_location=last,first_breakdown_at=first_breakdown,
        first_departure_range_end=range_end,maximum_observed_downside_fraction=format(max_decline,'f'),maximum_downside_date=decline_date,
        records_from_formation_to_maximum_low=(next((i for i,r in enumerate(rows) if r['date']==decline_date),box['formed_index'])-box['formed_index']) if decline_date else None,
        route_classification='UNKNOWN_NO_APPROVED_FAST_SLOW_DECLINE_RULE',
        qualification='CLOSE_LOCATION_AND_FAILURE_PATH_NOT_PERMANENT_INVALIDATION_OR_TRADING_SIGNAL')


def _compare(boxes,anchor):
    """Multidimensional Pareto relation; missing dimensions force incomparability."""
    for box in boxes:
        lo,hi=map(number,box['research_bounds']['pressure_band']);cl=number(anchor['close'])
        box['anchor_relation']=relation(cl,lo,hi) if box['usable_at_anchor'] else 'NOT_COMPARABLE_AFTER_GAP'
        box['pressure_distance_fraction']=ratio(max(lo-cl,Decimal(0)),cl)
        box['relative_width_to_anchor']=ratio(number(box['research_bounds']['high'])-number(box['research_bounds']['low']),cl)
        box['parent_ids']=[]
    # Strict interval + geometric containment, never just older/bigger wins.
    for child in boxes:
        parents=[p for p in boxes if p['id']!=child['id'] and p['segment']==child['segment'] and p['first_index']<=child['first_index'] and p['last_index']>=child['last_index']
            and p['duration_records']>child['duration_records'] and number(p['display_extent']['low'])<=number(child['display_extent']['low'])
            and number(p['display_extent']['high'])>=number(child['display_extent']['high'])]
        if parents:
            nearest=min(p['duration_records'] for p in parents);child['parent_ids']=[p['id'] for p in parents if p['duration_records']==nearest]
    frontier=[];comparisons=[]
    relevant=[b for b in boxes if b['usable_at_anchor'] and b['anchor_relation'] in ('BELOW','INSIDE')]
    def dimensions(b):return [Decimal(b['turns']),Decimal(b['duration_records']),number(b['path']['maximum_observed_downside_fraction']),
        number(b['volume']['mean_to_prior_ratio']) if b['volume']['mean_to_prior_ratio'] is not None else None]
    def dominates(a,b):
        x,y=dimensions(a),dimensions(b)
        return None if None in x or None in y else all(i>=j for i,j in zip(x,y)) and any(i>j for i,j in zip(x,y))
    for b in relevant:
        dominant=[a['id'] for a in relevant if a['id']!=b['id'] and dominates(a,b) is True]
        b['research_dominated_by']=dominant
        if not dominant:frontier.append(b['id'])
    # Keep pair evidence for distinct temporal scales instead of a scalar score.
    for child in boxes:
        for pid in child['parent_ids']:
            parent=next(p for p in boxes if p['id']==pid)
            comparisons.append(dict(parent_id=pid,child_id=child['id'],dimensions=['turns','duration_records','following_downside','mean_volume_vs_prior'],
                parent_pareto_dominates=dominates(parent,child),child_pareto_dominates=dominates(child,parent),
                verdict='RESEARCH_PARETO_ONLY_NO_APPROVED_IMPORTANCE_WEIGHT'))
    return dict(relevant_pressure_ids=[b['id'] for b in relevant],pareto_frontier_ids=frontier,parent_child_comparisons=comparisons,
        primary_pressure_id=None,ranking_status='UNRESOLVED_MULTI_OBJECTIVE_NOT_APPROVED_IMPORTANCE',
        missing_evidence='Formal significance/decay/anomaly/ownership rules and historical publication availability are not defined')


def analyze(payload,*,as_of,config=None):
    """Read only the supplied completed prefix. No manual references accepted."""
    if 'manual_cases' in payload or 'references' in payload:raise ValueError('Manual answers cannot enter automatic core input')
    with localcontext() as ctx:
        ctx.prec=50
        context,rows,resets,missing,gaps,cfg=_validate(payload,as_of,config)
        points=[];boxes=[];ambiguities=[];pending=[];rejected=0
        for reversal in cfg['reversals']:
            p,a,u=_pivots(rows,reversal,resets);points+=p;ambiguities+=a;pending+=u
            candidates,count=_boxes(rows,p,number(cfg['cluster_spread_fraction']),resets);boxes+=candidates;rejected+=count
        anchor=dict(date=as_of,close=rows[-1]['close'],index=len(rows)-1,price_mode=context['price_mode'],price_basis_id=context['price_basis_id'])
        volume_cache={}
        for box in boxes:
            box['path']=_path(rows,box,resets,volume_cache)
            box['usable_at_anchor']=not any(e['type']=='OBSERVATION_STOPPED_AT_DATA_OR_BASIS_GAP' for e in box['path']['events'])
        comparison=_compare(boxes,anchor)
        for box in boxes:
            box['successor_after_breakdown_ids']=[b['id'] for b in boxes if box['path']['first_breakdown_at'] is not None
                and b['segment']==box['segment'] and b['start']>box['path']['first_breakdown_at']]
            box['interpretation']=dict(settlement='UNKNOWN_NO_APPROVED_VOLUME_OR_OWNERSHIP_RULE',
                strengthening='CLOSE_FACT_ONLY_NOT_TRADE_QUALIFIED',lifecycle='UNKNOWN',
                counterevidence=[e['type'] for e in box['path']['events'] if 'FAILED' in e['type'] or 'BELOW' in e['type']],
                missing_evidence=['FORMAL_PRICE_BOUNDS','IMPORTANCE_WEIGHTS','VOLUME_EXPANSION_THRESHOLD','OWNERSHIP','HISTORICAL_PUBLICATION_TIMES'])
        references=[]
        for p in points:
            if p['kind']!='HIGH':continue
            references.append(dict(pivot_id=p['id'],scale=p['scale'],price=p['price'],source_dates=p['source_dates'],
                occurred_at=p['occurred_at'],first_observed_at=p['first_observed_at'],confirmed_at=p['confirmed_at'],
                distance_to_anchor=ratio(abs(number(anchor['close'])-number(p['price'])),number(anchor['close'])),
                path=trace_reference(rows,p['price'],p['confirmed_index'],stop_dates=resets),
                qualification='AUTOMATIC_SWING_REFERENCE_NOT_UNIQUE_IMPORTANT_REPRESENTATIVE'))
        result=dict(schema_version=VERSION,context=context,as_of=as_of,anchor=anchor,parameters=cfg,source_prefix_fingerprint=fingerprint(rows),
            source_records=len(rows),anchor_volume=volume_observation(rows,len(rows)-1,resets),pivots=points,pending_extrema=pending,boxes=boxes,reference_candidates=references,comparison=comparison,
            ambiguities=ambiguities,data_gaps=dict(missing_expected_dates=missing,missing_price_rows=gaps,basis_resets=sorted(d for d in resets if d<=as_of)),
            rejected_geometry_runs=rejected,qualified_interpretation='ABSTAIN_APPROVED_CORE_USEFULNESS_UNESTABLISHED',
            corporate_action_comparability=context.get('corporate_action_comparability','UNVERIFIED'),
            historical_information_availability='UNVERIFIED_UNLESS_SEPARATELY_SUPPLIED',
            intraday_order='UNKNOWN_FROM_DAILY_OHLCV',classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED',
            formal_strategy_parameters={},manual_case_inputs_used=False)
        result['result_id']=fingerprint(result)
        return result
