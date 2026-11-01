"""Read retained M-G3 results into complete, explicitly projected research evidence."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

from graph_core.core import fingerprint
from graph_core_chart.build import ROOT, input_for, PARENT_SHA256
from graph_core_chart.evidence import bind_input, input_binding, validate_source_spec
from candle_region_chart.build import load_parent
from technical_chart.build import unpack
from product_candidate.build import publish_immutable

HERE = Path(__file__).parent/'mc2_20261101'
MG3 = Path(__file__).parent/'output/mg3_20261101'
CODES = ('1101','2884','6488','8069')
DAY = '2026-10-16'
EVENT_FIELDS = ('type','date','first_observed_at','previous','location')
BOX_FIELDS = ('id','scale','segment','start','source_end','duration_records','confirmed_at','first_observed_at',
              'source_turn_ids','research_bounds','display_extent','usable_at_anchor','anchor_relation',
              'anchor_comparison_reason','pressure_distance_fraction','relative_width_to_anchor','parent_ids',
              'successor_after_breakdown_ids','volume','interpretation')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def null_reasons(value, pointer=''):
    """Every omitted value remains null, with a field-specific reason class."""
    out = {}
    if isinstance(value, dict):
        for key, item in value.items():
            path = pointer+'/'+key.replace('~','~0').replace('/','~1')
            if item is None:
                if key in ('first_breakdown_at','maximum_downside_date','first_departure_range_end'):
                    reason = 'NOT_OBSERVED_IN_SUPPLIED_COMPARABLE_PREFIX_NOT_PROOF_OF_FUTURE_ABSENCE'
                elif key == 'anchor_comparison_reason': reason = 'NO_COMPARISON_STOP_RECORDED_NOT_SOURCE_CERTIFICATION'
                elif 'distance' in key or 'width_to_anchor' in key: reason = 'NOT_COMPARABLE_OR_NO_COMPARABLE_CANDIDATE'
                elif key in ('previous','location'): reason = 'INITIAL_STATE_OR_STOP_EVENT_HAS_NO_LOCATION'
                elif key == 'primary_pressure_id': reason = 'NO_FORMAL_PRIMARY_PRESSURE_AUTHORIZED'
                else: reason = 'SOURCE_OR_REQUIRED_BASELINE_NOT_AVAILABLE_SEE_ORIGINAL_QUALIFICATION'
                out[path] = reason
            else: out.update(null_reasons(item,path))
    elif isinstance(value,list):
        for i,item in enumerate(value):
            if item is None: out[pointer+'/'+str(i)] = 'ORIGINAL_OPTIONAL_EVENT_FIELD_NOT_SUPPLIED'
            else: out.update(null_reasons(item,pointer+'/'+str(i)))
    return out


def project(result, series, parent, spec, ledger, original):
    """No recognition call. Validate identities before projecting all candidates."""
    code = series['code']
    if code not in CODES or result['context']['code'] != code or result['as_of'] != DAY:
        raise ValueError('Common stock/date mismatch')
    if result['schema_version'] != 'graph-recognition-research/0.2': raise ValueError('Core version mismatch')
    if result != next(r for r in series['results'] if r['as_of']==DAY): raise ValueError('Full M-G3 result mismatch')
    if result['result_id'] != fingerprint({k:v for k,v in result.items() if k!='result_id'}): raise ValueError('Result fingerprint mismatch')
    source = series['source']
    if (ledger['source_id'] != source['id'] or ledger['source_records'] != source['source_records']
            or ledger['normalization'] != source['volume_normalization'] or ledger['volume_unit'] != source['volume_unit']
            or result['context']['source_id'] != source['id'] or parent['source'] != source):
        raise ValueError('Source ledger mismatch')
    frame = parent['frames'][-1]; base = parent['bases'][frame['chart_base']]
    for key in ('bars','macd','moving_averages'):
        if series[key] != base[key]: raise ValueError('Numeric parent mismatch: '+key)
    payload = bind_input(input_for(parent, frame),spec,code)
    binding = input_binding(payload,spec,code,DAY)
    if binding != series['input_bindings'][DAY] or result['data_gaps']['basis_resets'] != binding['basis_break_dates']:
        raise ValueError('Source basis interruptions missing or changed')
    if result['context']['price_basis_id'] != frame['chart_base']: raise ValueError('Price basis mismatch')
    if result['source_records'] != len(series['bars']) or series['bars'][-1]['date'] != DAY:
        raise ValueError('Incomplete or wrong completed prefix')
    if result['source_prefix_fingerprint'] != fingerprint(series['bars']): raise ValueError('Price prefix mismatch')
    if result['comparison']['primary_pressure_id'] is not None or result['classification_quality']!='NOT_VALIDATED':
        raise ValueError('Qualification promotion refused')
    units = sorted({r['source_volume_field'] for r in source['source_records']})
    expected_units = {'成交股數'} if source['exchange']=='TWSE' else {'成交仟股','成交張數'}
    if not set(units)<=expected_units: raise ValueError('Unknown reported volume unit')
    normalized = source['exchange']=='TPEX'
    if normalized and 'TIMES1000' not in source['volume_normalization']: raise ValueError('Missing explicit volume normalization')
    latest = {}
    for scale in result['parameters']['reversals']:
        latest[scale] = {}
        for kind in ('HIGH','LOW'):
            pool=[p for p in result['pivots'] if p['scale']==scale and p['kind']==kind]
            day=max((p['confirmed_at'] for p in pool),default=None)
            latest[scale][kind]=[deepcopy(p) for p in pool if p['confirmed_at']==day]
    pool=[b for b in result['boxes'] if b['usable_at_anchor'] and b['anchor_relation']=='BELOW']
    nearest=min((Decimal(b['pressure_distance_fraction']) for b in pool),default=None)
    tied=[b['id'] for b in pool if Decimal(b['pressure_distance_fraction'])==nearest]
    boxes=[]
    for b in result['boxes']:
        item={k:deepcopy(b[k]) for k in BOX_FIELDS}
        item['whole_range_location']=b['path']['last_close_location'] if b['usable_at_anchor'] else 'NOT_COMPARABLE_AFTER_GAP'
        item['path_summary']={k:deepcopy(v) for k,v in b['path'].items() if k!='events'}
        # Identity is original result_id + box_id + row index. No core event ID is invented.
        item['event_columns']=list(EVENT_FIELDS)
        item['events']=[[e.get(k) for k in EVENT_FIELDS] for e in b['path']['events']]
        item['null_reasons']=null_reasons(item)
        boxes.append(item)
    value=dict(code=code,as_of=DAY,completed_records=result['source_records'],original=original,
        source_id=source['id'],price_basis_id=result['context']['price_basis_id'],result_id=result['result_id'],
        source_prefix_fingerprint=result['source_prefix_fingerprint'],source_input_binding=binding,
        source_gaps=deepcopy(series['source_gaps']),corporate_action_coverage=source['corporate_action_coverage'],
        volume_provenance=dict(source_volume_fields=units,source_ledger_unit=source['volume_unit'],
            core_internal_unit=result['context']['volume_unit'],normalization=source['volume_normalization'],
            multiplier='1000' if normalized else '1',precision='INTEGER_LOTS_OR_THOUSAND_SHARES_ONLY_NOT_NATIVE_EXACT_SHARES' if normalized else 'NATIVE_REPORTED_SHARE_COUNT',
            native_exact_share_count_certified=not normalized,finmind_exact_volume_verified=False),
        anchor=deepcopy(result['anchor']),anchor_volume=deepcopy(result['anchor_volume']),
        latest_confirmed_by_scale=latest,pending_extrema=deepcopy(result['pending_extrema']),
        latest_confirmed_scope='ALL_TIES_PER_SCALE_AND_KIND_NOT_ALL_HISTORICAL_PIVOTS',
        comparable_candidate_ids=deepcopy(result['comparison']['relevant_pressure_ids']),
        pareto_candidate_ids=deepcopy(result['comparison']['pareto_frontier_ids']),
        nearest_above=dict(distance_fraction=None if nearest is None else str(nearest),candidate_ids=tied,role='DISPLAY_DISTANCE_ONLY_ALL_TIES_NOT_PRIMARY_OR_STOCK_RANKING'),
        manual_audit=deepcopy(series['manual_audits'].get(DAY)),
        coverage=dict(box_candidates='COMPLETE',events='ALL_EVENTS_ALL_BOXES_SELECTED_COLUMNS',pending='COMPLETE',
            omitted_fields=['RAW_CANDLES','EVENT_CLOSE_AND_VOLUME','ALL_HISTORICAL_PIVOTS','FULL_REFERENCE_CANDIDATES','PER_BAR_OBSERVATION_TABLE','MACD_SMA_CURVES'],
            omitted_fields_location='Original full result and M-G3 HTML pinned by SHA; not claimed exported'),
        unknown_reasons=dict(historical_available_at='NO_AUTHENTICATED_HISTORICAL_PUBLICATION_TIME',corporate_actions='INCOMPLETE_ACTION_COVERAGE_NO_CROSS_BASIS_CERTIFICATION',
            calendar='RETAINED_GAPS_AND_PLANNED_EXCEPTIONS_NOT_COMPLETE_AUTHENTICATION',lifecycle='NO_APPROVED_FORMAL_INVALIDATION_OR_REACTIVATION_RULE',
            other_original_UNKNOWN='Retained original qualification/missing_evidence; no imputation'),
        primary_pressure_id=None,classification_quality='NOT_VALIDATED',action_qualification=result['action_qualification'],
        policy_authorized=False,live_execution_authorized=False)
    value['null_reasons']=null_reasons(value)
    return value, boxes


def run():
    frozen=json.loads((HERE/'frozen.json').read_text());readback={}
    for row in frozen['files']:
        raw=(ROOT.parent/row['path']).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']: raise ValueError('Frozen original mismatch: '+row['path'])
        readback[row['path']]=row
    html=(MG3/'M1_v019_graph_recognition_v02.html').read_text()
    bundle=unpack(json.loads(re.search(r'id="payload"[^>]*>(.*?)</script>',html,re.S)[1]))
    if fingerprint({k:v for k,v in bundle.items() if k!='artifact_id'})!=bundle['artifact_id']: raise ValueError('Bundle fingerprint mismatch')
    parent=load_parent();spec=json.loads((HERE.parent/'mg3_20261101/source-input-spec.json').read_text())
    validate_source_spec(spec,ROOT,PARENT_SHA256)
    ledger_path=ROOT/'pressure_chart/data/history-20261018/history-candidate.json'
    ledger=json.loads(ledger_path.read_text());outputs={};stocks=[]
    for code in CODES:
        s=next(s for s in bundle['series'] if s['code']==code)
        p=next(s for s in parent['history_series'] if s['code']==code)
        l=next(s for s in ledger['series'] if s['code']==code)
        file=MG3/f'core-{code}-latest.json';raw=file.read_bytes();r=json.loads(raw)
        # Independently read each retained monthly response: source hashes and original unit fields.
        for record in s['source']['source_records']:
            month=record['month'];path=ROOT/f'pressure_chart/data/history-20261018/raw/{code}_{month}.json'
            response=path.read_bytes()
            if sha(response)!=record['sha256'] or record['source_volume_field'] not in response.decode(): raise ValueError('Monthly source/volume provenance mismatch')
        value,boxes=project(r,s,p,spec,l,dict(path=str(file.relative_to(ROOT.parent)),bytes=len(raw),sha256=sha(raw)))
        value['source_ledger_sha256']=sha(ledger_path.read_bytes());value['numeric_parent_sha256']=PARENT_SHA256
        value['full_MG3_html_sha256']=sha(html.encode())
        # Explicit ordered shards; never truncate a candidate or its events.
        chunks=[];current=[]
        for box in boxes:
            if current and len(dumps(current+[box]))>850000: chunks.append(current);current=[]
            current.append(box)
        if current:chunks.append(current)
        value['box_shards']=[]
        for i,chunk in enumerate(chunks):
            name=f'{code}-boxes-{i+1}.json';data=dumps(dict(code=code,as_of=DAY,result_id=r['result_id'],boxes=chunk))
            if len(data)>=1000000: raise ValueError('Individual complete shard exceeds budget; explicit further design required')
            outputs[name]=data;value['box_shards'].append(dict(path=name,bytes=len(data),sha256=sha(data),count=len(chunk)))
        value['box_count']=len(boxes);value['event_count']=sum(len(b['events']) for b in boxes)
        stocks.append(value)
    index=dict(schema_version='same-day-graph-evidence/0.1',as_of=DAY,stocks=stocks,
        use='RETROSPECTIVE_RESEARCH_ONLY_NOT_STOCK_RANKING_OR_TRADE_AUTHORIZATION',work_mc1_originals='NOT_OBTAINED_NOT_READ')
    outputs['index.json']=dumps(index)
    if len(outputs['index.json'])>=1000000: raise ValueError('Index exceeds budget')
    lines=['# 2026-10-16同期四股研究證據','', '完整候選按下列JSON分片提供；沒有跨股總分、排名或買賣建議。數量只表示證據覆蓋，不是強度。','',
        '|股票|完成K|箱／事件完整數|可比候選|最近上方帶／全部並列|申報量精度|中斷|','|---|---:|---:|---:|---|---|---|']
    for s in stocks:
        tied=s['nearest_above']['candidate_ids'];boxes=[b for info in s['box_shards'] for b in json.loads(outputs[info['path']])['boxes']]
        bands=sorted({tuple(b['research_bounds']['pressure_band']) for b in boxes if b['id'] in tied})
        lines.append(f"|{s['code']}|{s['completed_records']}|{s['box_count']}／{s['event_count']}|{len(s['comparable_candidate_ids'])}|{bands or 'NULL：無可比上方箱'}／{len(tied)}並列|{s['volume_provenance']['source_volume_fields']}；×{s['volume_provenance']['multiplier']}|{s['source_input_binding']['basis_break_dates']}|")
    lines+=['','## 各股證據（同日，不排名）']
    for s in stocks:
        lines+=['',f"### {s['code']}",f"完整原件SHA：`{s['original']['sha256']}`；result_id：`{s['result_id']}`。",
            '最新已確認（發生→確認）：'+ '；'.join(f"{scale} {kind} "+','.join(f"{p['price']}／{p['occurred_at']}→{p['confirmed_at']}" for p in ps) for scale,kinds in s['latest_confirmed_by_scale'].items() for kind,ps in kinds.items()),
            'pending（全部；尚未確認，不當成新轉折）：`'+json.dumps(s['pending_extrema'],ensure_ascii=False)+'`',
            f"當日量觀察：`{json.dumps(s['anchor_volume'],ensure_ascii=False)}`；僅原描述統計，不是放量／勝率認證。",
            '完整箱形成、整箱／壓力帶位置、原父子／反證／回箱／停止及量統計：'+ '、'.join(f"[{i['path']}]({i['path']})（{i['count']}箱）" for i in s['box_shards']),
            '最近上方全部並列IDs：'+ ('、'.join('`'+i+'`' for i in s['nearest_above']['candidate_ids']) or 'NULL；無可比候選，不補0。')]
    lines+=['','1101自動4/8～5/13／25筆與晚來人工4/7～6/2／39筆分離；完整箱集合包含近期小箱與歷史大帶。2884全部32箱已停止比較，不能當成目前可比壓力。6488上方977八並列不任選主要壓力。',
        '', '所有來源歷史available_at／完整公司行動／日曆與辨識用途仍未認證。TPEx成交仟股／張×1000只是換算，core的SHARES_REPORTED不認證原生精確股數；未核FinMind股數。正式false、NOT_VALIDATED、主壓力null及原1101拒算保持。',
        '', '完整性及每一null原因見[index.json](index.json)。全部箱及事件投影均保留；原始K棒／事件價量／全歷史轉折等明列未匯出，不把精簡投影冒稱完整核心原件。Work M-C1 Library未取得／未讀；可繼續人工跨股機會研究，不能產生已驗證優勢或正式採用。']
    outputs['COMPARISON.md']=('\n'.join(lines)+'\n').encode()
    for name,raw in outputs.items():publish_immutable(HERE/name,raw)
    return index


if __name__=='__main__':
    value=run();print(json.dumps({s['code']:dict(boxes=s['box_count'],events=s['event_count'],shards=len(s['box_shards'])) for s in value['stocks']}))
