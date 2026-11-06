"""Pure retrospective graph/market-summary journal. No analysis, IO or trading.

Full inputs/results may reconstruct restricted quotes; keep them outside Git.
Only public_summary() is an allowlisted, non-quote acceptance projection.
"""
from copy import deepcopy
from datetime import date, datetime
from decimal import Context, localcontext
import re
from urllib.parse import parse_qs, urlsplit

from .core import _validate, fingerprint, number

VERSION = 'graph-market-research-diary/0.1'
FLAGS = ('data_qualified', 'execution_model_qualified', 'historical_signal_eligible',
         'policy_authorized', 'live_execution_authorized')
FAILURES = ('FAILED_UP_RETURN_IN_RANGE', 'FAILED_UP_AND_CROSSED_BELOW_RANGE')
STOP = 'OBSERVATION_STOPPED_AT_DATA_OR_BASIS_GAP'


class DiaryError(ValueError): pass


def _day(value):
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat()!=value: raise ValueError
    except (TypeError, ValueError): raise DiaryError('INVALID_DATE') from None
    return value


def _no_promotion(value):
    if any(value.get(k) is True for k in FLAGS) or value.get('primary_pressure_id') is not None:
        raise DiaryError('FORMAL_QUALIFICATION_PROMOTION_REFUSED')


def _core(snapshot):
    p, r = snapshot['input'], snapshot['result']; day = _day(r['as_of'])
    if r.get('schema_version')!='graph-recognition-research/0.2': raise DiaryError('CORE_VERSION')
    if r.get('result_id')!=fingerprint({k:v for k,v in r.items() if k!='result_id'}):
        raise DiaryError('CORE_RESULT_FINGERPRINT')
    if 'manual_cases' in p or 'references' in p: raise DiaryError('MANUAL_CORE_INPUT_REFUSED')
    try: context, rows, resets, missing, gaps, cfg = _validate(p, day, r['parameters'])
    except (KeyError, ValueError): raise DiaryError('CORE_INPUT_INVALID') from None
    if (context!=r['context'] or r['source_prefix_fingerprint']!=fingerprint(rows) or
            r['source_records']!=len(rows) or r['anchor']['date']!=day or r['anchor']['close']!=rows[-1]['close'] or
            r['anchor']['index']!=len(rows)-1 or r['anchor']['price_mode']!=context['price_mode'] or
            r['anchor']['price_basis_id']!=context['price_basis_id'] or r['parameters']!=cfg or
            r['data_gaps']!=dict(missing_expected_dates=missing,missing_price_rows=gaps,
                                 basis_resets=sorted(d for d in resets if d<=day))):
        raise DiaryError('CORE_SOURCE_BINDING')
    source_kind=context.get('source_kind')
    expected_role=('SYNTHETIC_TEST_ONLY' if source_kind=='SYNTHETIC_TEST_ONLY' else
                   'RETAINED_FINMIND_LOCAL_INTAKE' if source_kind=='FINMIND_TAIWAN_STOCK_PRICE_RETROSPECTIVE' else None)
    if expected_role is None or snapshot.get('stock_source_role')!=expected_role:
        raise DiaryError('STOCK_SOURCE_ROLE')
    _no_promotion(r); _no_promotion(r['comparison'])
    if r['formal_strategy_parameters']!={}: raise DiaryError('FORMAL_QUALIFICATION_PROMOTION_REFUSED')
    for pivot in r['pivots']:
        if not _day(pivot['occurred_at'])<=_day(pivot['first_observed_at'])<=_day(pivot['confirmed_at'])<=day:
            raise DiaryError('FUTURE_OR_CONTRADICTORY_EVENT')
    for box in r['boxes']:
        if not box['usable_at_anchor'] and (
                box['anchor_relation']!='NOT_COMPARABLE_AFTER_GAP' or
                box['pressure_distance_fraction'] is not None or box['relative_width_to_anchor'] is not None or
                box['anchor_comparison_reason']!=STOP): raise DiaryError('F01_INCOMPARABLE_NUMBERS')
        for event in box['path']['events']:
            if not _day(event['date'])<=_day(event['first_observed_at'])<=day:
                raise DiaryError('FUTURE_OR_CONTRADICTORY_EVENT')
    for ref in r['reference_candidates']:
        if ref['path']['last_relation']=='NOT_COMPARABLE_AFTER_GAP' and (
                ref['distance_to_anchor'] is not None or ref['anchor_comparison_reason']!=STOP):
            raise DiaryError('F01_INCOMPARABLE_NUMBERS')
    return rows


def _market(item, *, day, market, synthetic):
    if item.get('date')!=day or item.get('market')!=market: raise DiaryError('MARKET_DATE_OR_IDENTITY')
    if not isinstance(item.get('provenance'),dict) or not isinstance(item.get('values'),dict):
        raise DiaryError('MARKET_FIELDS_MISSING_OR_UNSUPPORTED')
    p, v = item['provenance'], item['values']; _no_promotion(item); _no_promotion(p)
    role='SYNTHETIC_TEST_ONLY' if synthetic else 'DIRECTOR_READBACK_RESEARCH_SUMMARY'
    if p.get('role')!=role: raise DiaryError('MARKET_SOURCE_ROLE')
    if (p.get('original_read_by_codex') is not False or p.get('official_reverification')!='NOT_PERFORMED' or
            any(p.get(k)!='UNKNOWN' for k in ('historical_available_at','strict_common_stock_universe','redistribution_permission'))):
        raise DiaryError('MARKET_ORIGINAL_OR_QUALIFICATION_CLAIM')
    if not re.fullmatch('[0-9a-f]{64}', p.get('reported_original_sha256','')):
        raise DiaryError('REPORTED_EVIDENCE_ID_REQUIRED')
    try:
        stamp=datetime.fromisoformat(p['received_at'])
        if stamp.tzinfo is None: raise ValueError
    except (KeyError, ValueError, TypeError): raise DiaryError('SUMMARY_RECEIPT_TIME_REQUIRED') from None
    u=urlsplit(p.get('source_url','')); q=parse_qs(u.query)
    if not synthetic:
        valid=(u.scheme=='https' and
            ((market=='TWSE' and u.netloc=='www.twse.com.tw' and u.path=='/rwd/zh/afterTrading/MI_INDEX'
              and q.get('date')==[day.replace('-','')] and q.get('type')==['MS']) or
             (market=='TPEX' and u.netloc=='www.tpex.org.tw' and u.path=='/www/zh-tw/afterTrading/highlight'
              and q.get('date')==[day.replace('-','/')])))
        if not valid: raise DiaryError('REPORTED_SOURCE_URL_DATE_OR_MARKET')
    elif u.netloc!='example.invalid': raise DiaryError('SYNTHETIC_SOURCE_URL')
    fields=('up','down','flat','non_comparable','untraded') if market=='TWSE' else (
            'up','down','flat','unmatched_or_suspended')
    if set(v)!={'index_close',*fields}: raise DiaryError('MARKET_FIELDS_MISSING_OR_UNSUPPORTED')
    if not isinstance(v['index_close'],str) or number(v['index_close'])<=0:
        raise DiaryError('MARKET_INDEX_PRICE')
    if any(type(v[k]) is not int or v[k]<0 for k in fields): raise DiaryError('MARKET_COUNT_UNKNOWN_OR_INVALID')
    return deepcopy(item)


def _events(result):
    """Preserve original IDs/bodies; missing box event IDs/timestamps stay null."""
    events=[]; day=result['as_of']; binding=deepcopy(result['context'])
    for pivot in result['pivots']:
        if pivot['confirmed_at']!=day: continue
        events.append(dict(event_key=pivot['id'], kind='PIVOT', original_event_type=pivot['kind'],
            original_event_id=pivot['id'], origin_object_id=pivot['id'], origin_index=None,
            original_event=deepcopy(pivot), original_reference=deepcopy(pivot), binding=binding,
            occurred_at=pivot['occurred_at'], first_observed_at=pivot['first_observed_at'],
            confirmed_at=pivot['confirmed_at'], event_id_role='ORIGINAL_CORE_PIVOT_ID'))
    for box in result['boxes']:
        for index, event in enumerate(box['path']['events']):
            if event['date']!=day: continue
            key=fingerprint(dict(box_id=box['id'],event=event,context=binding))
            events.append(dict(event_key=key,kind='BOX_EVENT',original_event_type=event['type'],
                original_event_id=event.get('id'),origin_object_id=box['id'],origin_index=index,
                original_event=deepcopy(event), original_reference=deepcopy(box['research_bounds']),binding=binding,
                occurred_at=event.get('occurred_at',event['date']),first_observed_at=event['first_observed_at'],
                confirmed_at=event.get('confirmed_at'),event_id_role='DERIVED_DIARY_KEY_NOT_ORIGINAL_EVENT_ID',
                timing_note='COMPLETED_BAR_DATE; ORIGINAL_CONFIRMED_AT_MISSING_STAYS_NULL'))
    return events


def _followup(event, latest, window, *, as_of):
    r, p=latest['result'],latest['input']; start=event['first_observed_at']
    bars={b['date']:b for b in p['bars'] if b['date']<=as_of}
    after=sum(d>start for d in bars)
    result=dict(event_key=event['event_key'],evaluated_at=as_of,status='UNKNOWN',maturity='UNKNOWN',
                known_failure=None,original_failure_events=[],window_dates=None,window_source=None,
                definition='EXISTING_CORE_BOX_FAILURE_FACTS_ONLY_NOT_TRADING_SUCCESS')
    box=next((b for b in r['boxes'] if b['id']==event['origin_object_id']),None) if event['kind']=='BOX_EVENT' else None
    if box is not None:
        known=[deepcopy(e) for e in box['path']['events']
               if e['type'] in FAILURES and start<e['first_observed_at']<=as_of]
        if event['original_event_type'] in FAILURES: known.insert(0,deepcopy(event['original_event']))
        result.update(known_failure=bool(known),original_failure_events=known)
        if not box['usable_at_anchor']:
            result['reason']='NOT_COMPARABLE_AFTER_DATA_OR_BASIS_GAP'; return result
    if window is None:
        result.update(status='UNKNOWN' if result['known_failure'] else 'IMMATURE' if after==0 else 'UNKNOWN',
                      maturity='IMMATURE' if after==0 else 'UNKNOWN',
                      reason='KNOWN_FAILURE_WITH_UNSPECIFIED_WINDOW' if result['known_failure'] else
                             'WINDOW_AND_OR_FAILURE_DEFINITION_NOT_SUPPLIED')
        return result
    if (window.get('purpose')!='EXPLICIT_RESEARCH_SETTING_NOT_STRATEGY' or not window.get('source_id')):
        raise DiaryError('EXPLICIT_RESEARCH_WINDOW_SOURCE_REQUIRED')
    days=window.get('dates')
    if not isinstance(days,list) or not days or days!=sorted(set(days)) or any(_day(d)<=start for d in days):
        raise DiaryError('INVALID_RESEARCH_WINDOW')
    result.update(window_dates=deepcopy(days),window_source=window['source_id'])
    if event['kind']!='BOX_EVENT' or event['original_event_type']!='CLOSE_ABOVE_RESEARCH_RANGE':
        result['reason']='NO_APPROVED_FAILURE_DEFINITION_FOR_THIS_EVENT'; return result
    if box is None: result['reason']='ORIGINAL_BOX_NOT_AVAILABLE'; return result
    failures=[deepcopy(e) for e in box['path']['events']
              if e['type'] in FAILURES and start<e['first_observed_at']<=min(as_of,days[-1])]
    result['in_window_failure_events']=failures
    expected=p.get('expected_dates')
    missing=(expected is None or any(d not in days for d in expected if start<d<=min(days[-1],as_of)) or
             any(d<=as_of and (d not in bars or any(bars[d][k] is None for k in ('open','high','low','close')))
                 for d in days))
    complete=as_of>=days[-1] and not missing
    result['maturity']='COMPLETE_SUPPLIED_RESEARCH_WINDOW' if complete else 'UNKNOWN' if missing else 'IMMATURE'
    if failures:
        result.update(status='FAILURE_IN_COMPLETE_WINDOW' if complete else 'KNOWN_EARLY_FAILURE',
                      reason='ORIGINAL_CORE_FAILURE_OBSERVED_NO_INFERRED_FILL')
    elif missing: result['reason']='MISSING_FOLLOWUP_DATE_PRICE_OR_CALENDAR'
    elif not complete: result.update(status='IMMATURE',reason='OBSERVATION_WINDOW_NOT_COMPLETE')
    else: result.update(status='NO_FAILURE_IN_COMPLETE_WINDOW',reason='NO_FAILURE_OBSERVED_NOT_SUCCESS_OR_RETURN')
    return result


def build(request, *, as_of):
    """Assemble supplied validated snapshots; never computes graph recognition."""
    with localcontext(Context(prec=50)):
        _day(as_of); _no_promotion(request)
        if request.get('schema_version')!='graph-market-diary-input/0.1' or request.get('mode')!='RETROSPECTIVE_RESEARCH_ONLY':
            raise DiaryError('DIARY_INPUT_SCHEMA_OR_MODE')
        all_snapshots=request['snapshots']; axis=[_day(s['result']['as_of']) for s in all_snapshots]
        if axis!=sorted(set(axis)): raise DiaryError('SNAPSHOT_DATE_ORDER_OR_DUPLICATE')
        snapshots=[s for s in all_snapshots if s['result']['as_of']<=as_of]
        if not snapshots or snapshots[-1]['result']['as_of']!=as_of: raise DiaryError('EXACT_AS_OF_REQUIRED')
        summaries={}
        for item in request['market_summaries']:
            d=_day(item['date'])
            if d>as_of: continue
            key=(d,item['market'])
            if key in summaries: raise DiaryError('DUPLICATE_MARKET_SUMMARY')
            summaries[key]=item
        windows={}
        for window in request.get('followup_windows',[]):
            key=window['event_key']
            if key in windows: raise DiaryError('DUPLICATE_FOLLOWUP_WINDOW')
            windows[key]=window
        daily=[]; origins=[]; context=None; source_kind=None; previous_markets=None
        for snapshot in snapshots:
            _core(snapshot); r=snapshot['result']; day=r['as_of']
            binding={k:r['context'][k] for k in ('code','source_id','price_basis_id','price_mode','volume_unit')}
            if context is not None and context!=binding: raise DiaryError('CROSS_SNAPSHOT_SOURCE_OR_BASIS')
            if source_kind is not None and source_kind!=r['context']['source_kind']:
                raise DiaryError('CROSS_SNAPSHOT_SOURCE_ROLE')
            source_kind=r['context']['source_kind']
            context=binding; synthetic=snapshot['stock_source_role']=='SYNTHETIC_TEST_ONLY'
            markets={}
            for market in ('TWSE','TPEX'):
                if (day,market) not in summaries: raise DiaryError('SAME_DAY_BOTH_MARKETS_REQUIRED')
                markets[market]=_market(summaries[(day,market)],day=day,market=market,synthetic=synthetic)
            market_states={}
            for name, item in markets.items():
                v=item['values']; prev=previous_markets[name]['values'] if previous_markets else None
                market_states[name]=dict(breadth_relation='MORE_UP_THAN_DOWN' if v['up']>v['down'] else
                    'MORE_DOWN_THAN_UP' if v['up']<v['down'] else 'EQUAL_COUNTS',
                    index_relation_to_previous_supplied_day=('UNKNOWN_NO_PREVIOUS_SUPPLIED_CLOSE' if prev is None else
                        'UP' if number(v['index_close'])>number(prev['index_close']) else
                        'DOWN' if number(v['index_close'])<number(prev['index_close']) else 'EQUAL'),
                    previous_supplied_day=daily[-1]['analysis_date'] if daily else None,
                    market_regime='UNKNOWN_NO_APPROVED_RULE')
            events=_events(r); origins.extend(events)
            daily.append(dict(code=context['code'],analysis_date=day,source_binding=deepcopy(binding),
                original_graph_result=deepcopy(r),events=events,markets=markets,market_states=market_states,
                market_join_status='RETROSPECTIVE_RESEARCH_SUMMARIES_JOINED_NOT_ORIGINAL_REVERIFICATION',
                knowledge_axis='COMPLETED_DAILY_PREFIX_NOT_AUTHENTICATED_HISTORICAL_PUBLICATION',
                initial_followup=[_followup(e,snapshot,windows.get(e['event_key']),as_of=day) for e in events],
                historical_available_at='UNKNOWN',corporate_action_type='UNKNOWN',
                universe='UNKNOWN_STRICT_HISTORICAL_COMMON_STOCK',
                qualification={k:False for k in FLAGS},primary_pressure_id=None))
            previous_markets=markets
        updates=[_followup(e,snapshots[-1],windows.get(e['event_key']),as_of=as_of) for e in origins]
        result=dict(schema_version=VERSION,as_of=as_of,real_research_connection='PARTIAL',
                    purpose='LIMITED_RETROSPECTIVE_RESEARCH_NOT_TRADING',daily_entries=daily,
                    followup_updates=updates,official_market_reverification='NOT_PERFORMED',
                    original_market_reports_read_by_codex=False,all_market_success_rate=None,
                    all_market_failure_rate=None,real_net_performance=None,
                    aggregate_refusal='HISTORICAL_COMMON_STOCK_UNIVERSE_AND_QUALIFIED_LEDGER_UNAVAILABLE',
                    qualification={k:False for k in FLAGS},primary_pressure_id=None)
        if source_kind=='SYNTHETIC_TEST_ONLY':
            result['real_research_connection']='NOT_APPLICABLE_SYNTHETIC'
            result['synthetic_test_only']=True
        result['result_id']=fingerprint(result); return result


def public_summary(result):
    """No market numbers, report SHA claims, source/event IDs or graph values."""
    rows=[]
    for row in result['daily_entries']:
        rows.append(dict(code=row['code'],analysis_date=row['analysis_date'],
            market_join_status=row['market_join_status'],market_observation_dates={k:v['date'] for k,v in row['markets'].items()},
            market_source_roles={k:v['provenance']['role'] for k,v in row['markets'].items()},
            event_count=len(row['events']),original_event_types=[e['original_event_type'] for e in row['events']],
            occurred_at=[e['occurred_at'] for e in row['events']],
            first_observed_at=[e['first_observed_at'] for e in row['events']],
            confirmed_at=[e['confirmed_at'] for e in row['events']],
            initial_followup_statuses=[f['status'] for f in row['initial_followup']],
            basis_break_dates=row['original_graph_result']['data_gaps']['basis_resets'],
            original_events_and_graph_preserved=True,historical_available_at='UNKNOWN'))
    return dict(schema_version='graph-market-diary-public-summary/0.1',producer_version=VERSION,
                as_of=result['as_of'],real_research_connection=result['real_research_connection'],joined_research_dates=len(rows),
                daily_entries=rows,official_market_reverification='NOT_PERFORMED',
                original_market_reports_read_by_codex=False,historical_available_at='UNKNOWN',
                strict_common_stock_universe='UNKNOWN',redistribution_permission='UNKNOWN',
                all_market_success_rate=None,all_market_failure_rate=None,real_net_performance=None,
                qualification={k:False for k in FLAGS},primary_pressure_id=None)
