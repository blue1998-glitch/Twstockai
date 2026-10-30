"""New RAW history/indicator candidate. No original structure engine or DB writes.
Reuse unchanged SMA/MACD numeric modules; source-unit precision stays explicit.
"""
from copy import deepcopy
from decimal import Decimal
import hashlib,json
from pathlib import Path
from pressure_chart.history import parse_month,STOCKS,ROOT
from product_candidate.macd import macd,VERSION as MACD_VERSION,PARAMETERS
from moving_averages import curves,VERSION as MA_VERSION
from contracts import fingerprint

VERSION='official-raw-indicator-candidate/0.1'


def validate_intake(path):
    path=Path(path);h=json.loads(path.read_text())
    if h['schema_version']!='official-history-candidate/0.1':raise ValueError('Unsupported intake')
    for s in h['series']:
        if s['code'] not in STOCKS or s['exchange']!=STOCKS[s['code']] or s['price_mode']!='RAW_CANDIDATE':raise ValueError('Intake identity mismatch')
        rows=[]
        for m in s['source_records']:
            b=(path.parent/'raw'/f"{s['code']}_{m['month']}.json").read_bytes()
            if hashlib.sha256(b).hexdigest()!=m['sha256']:raise ValueError('Intake raw response SHA mismatch')
            rows.extend(r for r in parse_month(json.loads(b),s['code'],m['month']) if h['target_start']<=r['date']<=h['target_end'])
        rows.sort(key=lambda r:r['date'])
        if rows!=s['candles']:raise ValueError('Intake normalized OHLCV mismatch')
        if fingerprint(dict(code=s['code'],exchange=s['exchange'],candles=rows))!=s['source_id']:raise ValueError('Intake identity fingerprint mismatch')
    return h


def series_from_intake(item,original_series):
    rows=deepcopy(item['candles'])
    if not rows:raise ValueError('Nonempty official candidate required')
    old=next(s for s in original_series if s['code']==item['code'] and s['price_mode']=='RAW_CANDIDATE')
    old_rows=max(old['bases'].values(),key=lambda b:len(b['bars']))['bars']
    # Every existing source day must still match. Revised official responses are
    # evidence conflicts, not authority to overwrite historical price results.
    indexed={r['date']:r for r in rows}
    for r in old_rows:
        n=indexed.get(r['date'])
        if n is None or any(Decimal(n[k])!=Decimal(r[k]) for k in ('open','high','low','close','volume_shares_scaled')):
            raise ValueError('New official history conflicts with original saved day '+r['date'])
    known=[]
    for b in old['bases'].values():
        for event in b['known_events']:
            if event not in known:known.append(deepcopy(event))
    known.sort(key=lambda e:e['effective_date'])
    resets=sorted({next(i for i,r in enumerate(rows) if r['date']>=e['effective_date']) for e in known if e['effective_date']<=rows[-1]['date']})
    ma=curves(rows);momentum=macd([r['close'] for r in rows],resets=resets)
    source=dict(id=item['source_id'],code=item['code'],exchange=item['exchange'],origin='NEW_OFFICIAL_CAPTURE_NOT_OLD_DATABASE_RESULT',
        volume_unit=item['volume_unit'],volume_normalization=item['normalization'],source_records=deepcopy(item['source_records']),
        corporate_action_coverage='ONLY_OLD_RETAINED_SAMPLE_EVENTS_NEW_PERIODS_UNVERIFIED')
    key=fingerprint(dict(producer=VERSION,source_id=item['source_id']));bases={};frames=[];evidence=[]
    for i,r in enumerate(rows):
        events=[e for e in known if e['effective_date']<=r['date']]
        basis=fingerprint(dict(source=source['id'],mode='RAW_CANDIDATE',known_events=events,producer=VERSION))
        if basis not in bases:bases[basis]=dict(bars=rows,moving_averages=ma,macd=momentum,known_events=events,anchor=r['date'],price_basis='NEW_OFFLINE_RAW_OFFICIAL_CANDIDATE_NO_ADJUSTED_PROJECTION')
        f=dict(schema_version='official-raw-frame/0.1',producer_version=VERSION,code=item['code'],exchange=item['exchange'],price_mode='RAW_CANDIDATE',
            as_of=r['date'],index=i,chart_base=basis,close=r['close'],lifecycle=dict(stage='UNKNOWN'),supporting=[],opposing=[],
            missing=['NO_NEW_STRUCTURE_RULE_CALCULATION','ACTIONS_AND_PUBLICATION_TIMING_NOT_FULLY_VERIFIED'],
            data_fingerprint=fingerprint(rows[:i+1]),effective_events_fingerprint=fingerprint(events),
            action_qualification='NOT_EVALUATED',classification_quality='NOT_VALIDATED',
            ma_version=MA_VERSION,macd_version=MACD_VERSION,original_record_id=None,structure_snapshot_id=None)
        f['frame_id']=fingerprint(f);frames.append(f)
        evidence.append(dict(as_of=r['date'],snapshot_id=None,source_candidate_frame_id=f['frame_id'],rule_version='NO_NEW_STRUCTURE_CALCULATION',
            parameters={},adjustment_anchor=r['date'],pivots=[],zones=[],daily_events=[]))
    return dict(key=key,code=item['code'],exchange=item['exchange'],price_mode='RAW_CANDIDATE',source=source,
        store='INDEPENDENT_OFFICIAL_RAW_INDICATOR_CANDIDATE_NOT_SAVED_TO_DB',original_record_id=None,
        original_structure_version=None,available_start=rows[0]['date'],available_end=rows[-1]['date'],coverage='UNVERIFIED_FULL_PERIOD_ACTIONS',
        frames=frames,bases=bases,kind='NEW_OFFICIAL_RAW_HISTORY',macd_parameters=PARAMETERS),evidence


def history_selection(payload,series,frame):
    b=series['bases'][frame['chart_base']];n=frame['index']+1
    return deepcopy(dict(schema_version='official-raw-indicator-selection/0.1',producer_version=VERSION,source=series['source'],frame=frame,
        bars=b['bars'][:n],moving_averages={k:v[:n] for k,v in b['moving_averages'].items()},macd=b['macd'][:n],
        known_sample_events=b['known_events'],price_basis=b['price_basis'],original_record_id=None,
        structure='NOT_CALCULATED_NO_AUTOMATIC_PATTERN_OR_WALL_SELECTION',action_qualification='NOT_EVALUATED',classification_quality='NOT_VALIDATED'))


def followup(case,series,frame,rows,old_series):
    if series['code']!='1101' or series['price_mode']!='RAW_CANDIDATE' or frame['as_of']<case['analysis_as_of']:return None
    old=next(s for s in old_series if s['code']=='1101' and s['price_mode']=='RAW_CANDIDATE')
    # Prefix equality has been checked in series_from_intake; the original case
    # stays intact and is linked as a later review, not relabelled as this source.
    if old['source']['id']!=case['source_id']:raise ValueError('Case source binding mismatch')
    original_frame=next(f for f in old['frames'] if f['as_of']==case['analysis_as_of'])
    if original_frame['structure_snapshot_id']!=case['structure_snapshot_id']:raise ValueError('Case snapshot binding mismatch')
    original=case['confirmed_for_this_case'];refs=[]
    for ref in (original['breakout_reference'],original['next_primary_pressure_reference']):
        level=Decimal(ref['price']);state='UNKNOWN';events=[]
        for r in rows:
            if r['date']<ref['confirmed_at']:continue
            now='ABOVE' if Decimal(r['close'])>level else 'BELOW' if Decimal(r['close'])<level else 'AT'
            if now=='ABOVE' and state!='ABOVE' or now!='ABOVE' and state=='ABOVE':
                e=dict(reference_id=ref['id'],reference_price=ref['price'],date=r['date'],close=r['close'],relation=now,
                    type='CLOSE_ABOVE_REVIEWED_POINT' if now=='ABOVE' else 'CLOSE_RETURNED_TO_OR_BELOW_REVIEWED_POINT',
                    source_id=series['source']['id'],price_mode='RAW_CANDIDATE',rule_version='reviewed-point-close-facts/0.1')
                e['event_id']=fingerprint(e);events.append(e)
            state=now
        refs.append(dict(reference=deepcopy(ref),current_close_relation=state,close_events=events))
    return dict(case_id=case['case_id'],reviewed_at=case['reviewed_at'],original_analysis_as_of=case['analysis_as_of'],
        original_source_id=case['source_id'],current_source_id=series['source']['id'],binding='ORIGINAL_SOURCE_DAYS_NUMERICALLY_EQUAL_NO_REVIEW_REASSIGNMENT',
        original_structure_snapshot_id=case['structure_snapshot_id'],
        status='RETROSPECTIVE_REVIEW_FOLLOWUP_NOT_ASOF_AUTOMATIC_SIGNAL',references=refs,
        post_breakout_bars=[deepcopy(r) for r in rows if r['date']>case['analysis_as_of']],
        volume_expansion=dict(status='UNKNOWN',baseline=None,threshold=None,duration=None),
        left_region_boundaries='UNKNOWN_POINT_PRICES_NOT_REGION_UPPER_EDGES',user_quote=case['user_quote'])
