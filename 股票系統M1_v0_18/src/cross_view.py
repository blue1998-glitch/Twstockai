"""Read-only daily/weekly/monthly view model. No numeric engine imports."""
from copy import deepcopy
from itertools import product
from pathlib import Path
from contracts import DataError, fingerprint, iso_date
from store_contracts import canonical
from analysis_store import AnalysisStore
from period_store import PeriodStore
from period_store_contracts import decimal_string

SCHEMA='cross-timeframe-catalog/1.0'
VIEW_SCHEMA='cross-timeframe-view/1.0'
SELECTION_SCHEMA='cross-timeframe-selection/1.0'
VERSION='cross-view-0.1'
DAILY_VERSIONS={'structure-0.2-research','structure-0.3-research'}


def require(ok,path,detail='Invalid or inconsistent cross-timeframe input'):
    if not ok:raise DataError('CROSS_VIEW_CONTRACT',path,detail)


def identity(entry):return tuple(entry[k] for k in ('code','exchange','price_mode','as_of'))


def daily_entry(saved,alias,as_of):
    q=saved['request'];r=saved['result'];versions=r['component_versions']
    require(versions['structure'] in DAILY_VERSIONS and versions['daily_ma']=='daily-sma-0.1' and r['adapter_version']=='analysis-job-0.1',
            'daily.versions','Explicit supported daily producer versions required')
    dates=[s['as_of'] for s in r['aligned_snapshots']]
    if as_of not in dates:return None
    i=dates.index(as_of)
    snap=dict(schema_version='analysis-store/1.0',record_id=saved['record_id'],analysis_id=saved['analysis_id'],as_of=as_of,
              aligned=deepcopy(r['aligned_snapshots'][i]),structure=deepcopy(r['components']['structure']['snapshots'][i]),
              daily_ma=deepcopy(r['components']['daily_ma']['snapshots'][i]),evidence_coverage=saved['evidence']['coverage_status'],
              corporate_action_coverage=q['corporate_actions']['coverage_status'],action_qualification='NOT_EVALUATED')
    ma=snap['daily_ma'];n=i+1
    require(set(ma['curves'])==set(ma['available'])=={'5','20','60','130','260'},'daily.curves')
    for key,values in ma['curves'].items():
        require(isinstance(values,list) and len(values)==n,'daily.curves.alignment')
        for value in values:decimal_string(value,'daily.curve')
        require(ma['available'][key]==(values[-1] is not None),'daily.available')
    entry=dict(key=fingerprint(dict(store=alias,record_id=saved['record_id'],as_of=as_of)),store=alias,
               record_id=saved['record_id'],analysis_id=saved['analysis_id'],code=q['code'],exchange=q['exchange'],
               price_mode=q['price_mode'],as_of=as_of,source=deepcopy(q['source']),versions=deepcopy(versions),
               reason=saved['reason'],created_at_utc=saved['created_at_utc'],snapshot=snap,
               source_candles=deepcopy([c for c in q['candles'] if c['date']<=as_of]),
               effective_actions=deepcopy([e for e in q['corporate_actions']['records'] if e['effective_date']<=as_of]),
               calendar_context=dict(expected_dates=deepcopy([d for d in q.get('expected_dates',[]) or [] if d<=as_of]),
                                     supplied=q.get('expected_dates') is not None),
               lineage=dict(request_fingerprint=fingerprint(q),result_fingerprint=fingerprint(r),evidence_fingerprint=fingerprint(saved['evidence']),
                            selected_snapshot_fingerprint=fingerprint(snap)),limitations=deepcopy(r['limitations']))
    return entry


def period_entry(record,alias):
    s=record['result']['snapshot']
    return dict(key=fingerprint(dict(store=alias,analysis_id=record['analysis_id'])),store=alias,
                analysis_id=record['analysis_id'],code=s['code'],exchange=s['exchange'],price_mode=s['price_mode'],as_of=s['as_of'],
                record=deepcopy(record),snapshot_fingerprint=fingerprint(s))


def alignment(d,p,scope):
    """Compare saved identities, never generate numeric values or structure states."""
    checks=[];warnings=[]
    def check(name,a,b):checks.append(dict(field=name,daily=a,period=b,status='MATCH' if a==b else 'CONFLICT'))
    if d is None or p is None:
        status='MISSING_DAILY' if d is None and p is not None else 'MISSING_PERIOD' if p is None and d is not None else 'MISSING_BOTH'
        e=d if d is not None else p
        if e is not None:
            for k in ('code','exchange','price_mode','as_of'):check('selection.'+k,e[k],scope[k])
            if any(c['status']=='CONFLICT' for c in checks):status='CONFLICT'
    else:
        s=d['snapshot']['structure'];m=d['snapshot']['daily_ma'];a=d['snapshot']['aligned'];ps=p['record']['result']['snapshot'];q=p['record']['request']
        check('structure.supported_version',s['rule_version'] in DAILY_VERSIONS,True)
        check('daily_ma.supported_version',m['rule_version'],'daily-sma-0.1')
        check('structure.version_link',s['rule_version'],d['versions']['structure'])
        for k in ('code','exchange','price_mode','as_of'):
            check(k,d[k],p[k]);check('selection.'+k,d[k],scope[k])
            check('period_snapshot.'+k,ps[k],p[k])
        for key,obj in [('structure',s),('daily_ma',m)]:
            check(key+'.code',obj['code'],d['code']);check(key+'.price_mode',obj['price_mode'],d['price_mode'])
        check('source_id',d['source']['id'],ps['source_id'])
        check('volume_unit',d['source']['volume_unit'],ps['volume_unit'])
        if s['rule_version']=='structure-0.3-research':check('structure.volume_unit',s.get('volume_unit'),d['source']['volume_unit'])
        else:
            warnings.append('歷史 structure-0.2 沒有快照單位欄位，單位依原工作單；不改寫歷史證據文字。')
            if d['source']['volume_unit']=='SHARES_REPORTED':warnings.append('此歷史版本的量能證據可能誤標為張數換算；原生股數沒有再次換算。')
        check('structure.source_id',s['source_id'],d['source']['id'])
        for key,dt in [('structure',s['as_of']),('daily_ma',m['as_of']),('aligned',a['as_of'])]:check(key+'.as_of',dt,scope['as_of'])
        check('structure.adjustment_anchor',s['adjustment_anchor'],ps['adjustment_anchor'])
        check('daily_ma.anchor_by_as_of_contract',m['as_of'],ps['adjustment_anchor'])
        check('period.adjustment_anchor',ps['adjustment_anchor'],scope['as_of'])
        raw_fp=fingerprint(d['source_candles']);event_fp=fingerprint(d['effective_actions'])
        for key,x in [('structure',s['data_fingerprint']),('daily_ma',m['data_fingerprint']),('aligned',a['data_fingerprint']),
                      ('daily_raw_prefix',raw_fp),('period_request_prefix',fingerprint([c for c in q['candles'] if c['date']<=scope['as_of']]))]:
            check(key+'.data_fingerprint',x,ps['data_fingerprint'])
        for key,x in [('structure',s['effective_events_fingerprint']),('daily_ma',m['events_fingerprint']),('aligned',a['effective_events_fingerprint']),
                      ('daily_effective_actions',event_fp),('period_request_actions',fingerprint([e for e in q['corporate_actions']['records'] if e['effective_date']<=scope['as_of']]))]:
            check(key+'.effective_events',x,ps['effective_events_fingerprint'])
        check('daily_records',len(d['source_candles']),ps['daily_records']);check('ma.bars',m['bars'],ps['daily_records'])
        check('last_price_date',d['source_candles'][-1]['date'] if d['source_candles'] else None,ps['last_price_date'])
        check('corporate_action_coverage',d['snapshot']['corporate_action_coverage'],p['record']['result']['corporate_action_coverage'])
        check('daily_snapshot_content',fingerprint(d['snapshot']),d['lineage']['selected_snapshot_fingerprint'])
        check('period_snapshot_content',fingerprint(ps),p['snapshot_fingerprint'])
        status='CONFLICT' if any(c['status']=='CONFLICT' for c in checks) else 'ALIGNED_INPUTS'
    warnings+=['輸入對齊不代表交易日曆、來源、分類品質或策略價值已認證。',
               '日線與週月的日曆／證據涵蓋分別保留，不由對照層提升確定程度。',
               '不產生跨尺度總分、正式型態或買賣資格。']
    payload=dict(schema_version=VIEW_SCHEMA,view_version=VERSION,scope=deepcopy(scope),daily_key=d['key'] if d else None,
                 period_key=p['key'] if p else None,status=status,allow_comparison=status=='ALIGNED_INPUTS',checks=checks,warnings=warnings,
                 classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED')
    return dict(**payload,view_id=fingerprint(payload))


def validate_config(config):
    canonical(config)
    require(isinstance(config,dict) and set(config)=={'schema_version','daily_stores','period_stores','as_of_dates'} and
            config['schema_version']=='cross-timeframe-sources/1.0','config')
    for k in ('daily_stores','period_stores'):
        require(isinstance(config[k],dict) and bool(config[k]) and all(isinstance(a,str) and a.strip() and isinstance(p,str) and p.strip() for a,p in config[k].items()),k)
    dates=config['as_of_dates'];require(isinstance(dates,list) and bool(dates),'as_of_dates')
    for dt in dates:iso_date(dt,'as_of_dates')
    require(len(set(dates))==len(dates),'as_of_dates','Explicit distinct dates required; no latest fallback')


def catalog(config):
    validate_config(config);daily=[];period=[];unavailable=[]
    for alias,path in sorted(config['daily_stores'].items()):
        store=AnalysisStore(path)
        for row in store.list_records():
            saved=store.load(row['record_id'])
            for dt in config['as_of_dates']:
                entry=daily_entry(saved,alias,dt)
                if entry:daily.append(entry)
                else:unavailable.append(dict(store=alias,record_id=row['record_id'],as_of=dt,reason='EXACT_DAILY_SNAPSHOT_NOT_SAVED'))
    for alias,path in sorted(config['period_stores'].items()):
        store=PeriodStore(path)
        for row in store.list():
            if row['as_of'] in config['as_of_dates']:period.append(period_entry(store.load(row['analysis_id']),alias))
    scopes=sorted({identity(e) for e in daily+period});views=[]
    for scope in scopes:
        fields=dict(zip(('code','exchange','price_mode','as_of'),scope))
        ds=[d for d in daily if identity(d)==scope];ps=[p for p in period if identity(p)==scope]
        for d,p in product(ds,ps):views.append(alignment(d,p,fields))
        for d in ds:views.append(alignment(d,None,fields))
        for p in ps:views.append(alignment(None,p,fields))
    return dict(schema_version=SCHEMA,exporter_version=VERSION,as_of_dates=deepcopy(config['as_of_dates']),daily=daily,period=period,views=views,
                unavailable_daily_dates=unavailable,source_aliases=dict(daily=sorted(config['daily_stores']),period=sorted(config['period_stores'])),
                classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED')


def select(payload,selection):
    canonical(selection)
    require(isinstance(selection,dict) and set(selection)=={'schema_version','code','exchange','price_mode','as_of','daily','period'} and
            selection['schema_version']==SELECTION_SCHEMA,'selection')
    scope={k:selection[k] for k in ('code','exchange','price_mode','as_of')};iso_date(scope['as_of'],'selection.as_of')
    require(scope['exchange'] in ('TWSE','TPEX') and scope['price_mode'] in ('RAW_CANDIDATE','ADJUSTED_CANDIDATE') and
            isinstance(scope['code'],str) and scope['code'].strip(),'selection.scope')
    picked={}
    for name,id_field in [('daily','record_id'),('period','analysis_id')]:
        ref=selection[name]
        if ref is None:picked[name]=None;continue
        require(isinstance(ref,dict) and set(ref)=={'store',id_field},'selection.'+name)
        candidates=[e for e in payload[name] if e['store']==ref['store'] and e[id_field]==ref[id_field] and e['as_of']==scope['as_of']]
        require(len(candidates)==1,'selection.'+name,'Exact saved identity/date required; no substitute')
        picked[name]=candidates[0]
    require(picked['daily'] is not None or picked['period'] is not None,'selection','At least one explicit saved record required')
    view=alignment(picked['daily'],picked['period'],scope)
    return dict(schema_version=VIEW_SCHEMA,selection=deepcopy(selection),alignment=view,daily=deepcopy(picked['daily']),period=deepcopy(picked['period']),
                classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED')
