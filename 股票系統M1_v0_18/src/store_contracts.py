"""Persistence boundary validation; no calculation, UI or database calls."""
import json
from contracts import DataError,fingerprint,validate_candles,validate_events,validate_output


def canonical(value):
    def walk(v):
        if isinstance(v,dict):
            if any(not isinstance(k,str) for k in v):raise ValueError('JSON keys must be strings')
            for x in v.values():walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
        elif v is not None and not isinstance(v,(str,int,float,bool)):raise ValueError('JSON types required')
    try:
        walk(value)
        s=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False);s.encode('utf-8')
        return s
    except (ValueError,TypeError,UnicodeError) as e:raise DataError('STORE_JSON','payload',str(e)) from None


def _require(ok,path,detail):
    if not ok:raise DataError('STORE_BUNDLE_MISMATCH',path,detail)


def validate_bundle(request,result,evidence):
    # Canonical JSON is retained exactly in meaning, including unknown statuses.
    for v in [request,result,evidence]:canonical(v)
    try:return _validate(request,result,evidence)
    except (KeyError,TypeError,IndexError,AttributeError) as e:
        raise DataError('STORE_BUNDLE_FIELDS','bundle','Incomplete or malformed bundle: '+type(e).__name__) from None


def _validate(q,r,e):
    _require(q['schema_version']=='stock-analysis/1.0','request.schema_version','Unsupported request contract')
    _require(r['schema_version']=='stock-analysis-result/1.0','result.schema_version','Unsupported result contract')
    _require(q['exchange'] in ('TWSE','TPEX') and q['timeframe']=='daily' and q['price_mode'] in ('RAW_CANDIDATE','ADJUSTED_CANDIDATE'),'request.scope','Unsupported market/timeframe/mode')
    _require(q['corporate_actions']['coverage_status'] in ('UNVERIFIED','CASH_ONLY_VERIFIED_SAMPLE'),'request.coverage','Explicit limited coverage required')
    _require(q['source']['volume_unit'] in ('SHARES_REPORTED','SHARES_SCALED_FROM_LOTS') and bool(q['source']['id']),'request.source','Explicit source identity and volume unit required')
    validate_candles(q['candles']);validate_events(q['corporate_actions']['records'])
    _require(e['schema_version']=='analysis-evidence/1.0' and e['code']==q['code'],'evidence','Evidence identity/schema differs')
    _require(isinstance(e['records'],list) and e['coverage_status'] in ('UNVERIFIED','CASH_ONLY_VERIFIED_SAMPLE'),'evidence','Explicit limited coverage required')
    _require(r['request_fingerprint']==fingerprint(q),'request_fingerprint','Result belongs to another request')
    shared=r['shared_input']
    for key in ['code','exchange','timeframe','price_mode','source']:
        _require(shared[key]==q[key],'shared_input.'+key,'Result input identity differs')
    _require(q['source']['code']==q['code'] and q['source']['exchange']==q['exchange'],'source','Source identity differs')
    _require(shared['corporate_action_coverage']==q['corporate_actions']['coverage_status'],'coverage','Coverage cannot change during saving')
    data_fp=fingerprint(q['candles']);events_fp=fingerprint(q['corporate_actions']['records'])
    _require(shared['data_fingerprint']==data_fp and shared['events_fingerprint']==events_fp,'shared_input','Data/event fingerprint differs')
    comps=r['components'];_require(set(comps)=={'structure','daily_ma'},'components','Exactly two supported engines required')
    structure=comps['structure'];ma=comps['daily_ma'];validate_output(structure)
    explicit_volume=structure['rule_version']=='structure-0.3-research' or 'volume_unit' in structure
    if explicit_volume:
        _require(structure.get('volume_unit')==q['source']['volume_unit'],'structure.volume_unit','Structure volume origin differs from request')
    _require(shared['data_quality']==structure['data_quality'],'shared_input.data_quality','Quality metadata differs')
    params={k:v['parameters_fingerprint'] for k,v in comps.items()}
    versions={k:v['rule_version'] for k,v in comps.items()}
    _require(r['component_versions']==versions,'versions','Component version metadata differs')
    expected=fingerprint(dict(request=fingerprint(q),versions=versions,parameters=params,adapter=r['adapter_version']))
    _require(r['analysis_id']==expected,'analysis_id','Run identity must include request, versions and parameters')
    _require(r['action_qualification']=='NOT_EVALUATED' and ma['action_qualification']=='NOT_EVALUATED','qualification','Trading qualification is not supported')
    _require(len(r['aligned_snapshots'])==len(q['candles']),'aligned_snapshots','Snapshot count differs')
    for name,c in comps.items():
        _require(c['code']==q['code'] and c['price_mode']==q['price_mode'],'components.'+name,'Stock/mode mismatch')
        _require(c['data_fingerprint']==data_fp and c['events_fingerprint']==events_fp,'components.'+name,'Data/event mismatch')
        _require(len(c['snapshots'])==len(q['candles']),'components.'+name,'Snapshot count differs')
    for i,candle in enumerate(q['candles']):
        a=structure['snapshots'][i];b=ma['snapshots'][i];joined=r['aligned_snapshots'][i];dt=candle['date']
        _require(a['as_of']==b['as_of']==joined['as_of']==dt,'snapshots.date','Snapshot dates differ')
        _require(a['rule_version']==versions['structure'] and b['rule_version']==versions['daily_ma'],'snapshots.version','Rule version differs')
        _require(a['source_id']==q['source']['id'],'snapshots.source_id','Source identity differs')
        if explicit_volume:
            _require(a.get('volume_unit')==q['source']['volume_unit'],'snapshots.volume_unit','Snapshot volume origin differs from request')
        _require(joined['structure_snapshot_id']==a['snapshot_id'] and joined['daily_ma_snapshot_id']==b['snapshot_id'],'snapshots.id','Joined snapshot IDs differ')
        _require(a['data_fingerprint']==b['data_fingerprint']==joined['data_fingerprint'],'snapshots.data','Prefix identity differs')
        _require(a['effective_events_fingerprint']==b['events_fingerprint']==joined['effective_events_fingerprint'],'snapshots.events','Effective-event identity differs')
        _require(joined['data_quality']==a['data_quality'] and joined['input_quality_fingerprint']==fingerprint(a['data_quality']),'snapshots.quality','Quality metadata differs')
    _require(ma['parameters_fingerprint']==fingerprint(ma['parameters']),'parameters','MA parameter metadata differs')
    config=structure['snapshots'][0]['parameters'] if structure['snapshots'] else None
    if config is not None:_require(fingerprint(config)==params['structure'],'parameters','Structure parameter metadata differs')
    return dict(schema_version='stored-analysis-rules/1.0',adapter_version=r['adapter_version'],component_versions=versions,
                parameters_fingerprints=params,structure_parameters=config,daily_ma_parameters=ma['parameters'])
