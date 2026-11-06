"""Single headless calculate/save/read workflow. Engines remain independent.

No UI, network, paid service, automatic event promotion or numeric rules here.
A missing response is resolved by LOOKUP, never by deleting stored history.
"""
from copy import deepcopy
from pathlib import Path
from contracts import DataError,fingerprint,iso_date
from store_contracts import canonical,validate_bundle
from analysis_jobs import run_analysis_job
from analysis_store import AnalysisStore

SCHEMA='analysis-workflow/1.0'


class WorkflowError(DataError):
    def __init__(self,code,path,detail,*,stage,commit_status='NOT_SAVED',record_id=None,identities=None):
        super().__init__(code,path,detail)
        self.stage=stage;self.commit_status=commit_status;self.record_id=record_id;self.identities=identities or {}
    def as_dict(self):
        out=super().as_dict();out.update(schema_version=SCHEMA,status='WORKFLOW_ERROR',stage=self.stage,commit_status=self.commit_status,**self.identities)
        if self.record_id:out['record_id']=self.record_id
        out['recovery_operation']='READ' if self.record_id else 'LOOKUP' if self.commit_status=='UNKNOWN' else None
        return out


def _require(ok,path,detail):
    if not ok:raise DataError('WORKFLOW_REQUEST',path,detail)


def _preflight(request):
    canonical(request)
    _require(isinstance(request,dict),'request','Object required')
    op=request.get('operation')
    allowed=dict(RUN={'schema_version','operation','job','evidence','reason','as_of','include_bundle'},
                 READ={'schema_version','operation','record_id','as_of','include_bundle'},
                 LOOKUP={'schema_version','operation','job','evidence'})
    _require(request.get('schema_version')==SCHEMA,'schema_version','Unsupported workflow contract')
    _require(isinstance(op,str) and op in allowed,'operation','Use RUN, READ or LOOKUP')
    _require(set(request)<=allowed[op],'request','Unknown workflow field')
    if 'include_bundle' in request:_require(isinstance(request['include_bundle'],bool),'include_bundle','Boolean required')
    if 'as_of' in request:iso_date(request['as_of'],'as_of')
    if op in ['RUN','LOOKUP']:
        q=request.get('job');e=request.get('evidence')
        _require(isinstance(q,dict) and q.get('schema_version')=='stock-analysis/1.0' and isinstance(q.get('code'),str) and bool(q['code']),'job','Versioned analysis job required')
        _require(isinstance(e,dict) and e.get('schema_version')=='analysis-evidence/1.0' and e.get('code')==q['code'],'evidence','Matching versioned evidence required')
        _require(e.get('coverage_status') in ('UNVERIFIED','CASH_ONLY_VERIFIED_SAMPLE') and isinstance(e.get('records'),list),'evidence','Explicit limited coverage required')
    else:_require(isinstance(request.get('record_id'),str) and bool(request['record_id']),'record_id','Exact record ID required')
    if op=='RUN':
        _require(isinstance(request.get('reason'),str) and bool(request['reason'].strip()),'reason','Import/change reason required')
        if 'as_of' in request:
            _require(isinstance(q.get('candles'),list) and request['as_of'] in [c.get('date') for c in q['candles'] if isinstance(c,dict)],'as_of','Requested snapshot date is absent; no nearest-date substitution')
    return op


def _open_store(path,*,create=False):
    path=Path(path)
    if create and not path.exists():
        try:store=AnalysisStore.create(path)
        except DataError as e:
            if e.code!='STORE_EXISTS':raise
            store=AnalysisStore(path)  # Another worker may have initialized it.
    else:store=AnalysisStore(path)
    store.recover()  # Includes unknown-format rejection; never reset or migrate.
    return store


def _view(saved,request,*,receipt=None):
    r=saved['result'];q=saved['request'];dates=[s['as_of'] for s in r['aligned_snapshots']]
    dt=request.get('as_of',dates[-1] if dates else None);snapshot=None
    if dt is not None:
        if dt not in dates:raise DataError('STORE_NOT_FOUND','as_of','Exact saved date required; no nearest-date substitution')
        i=dates.index(dt)
        snapshot=dict(as_of=dt,aligned=r['aligned_snapshots'][i],structure=r['components']['structure']['snapshots'][i],daily_ma=r['components']['daily_ma']['snapshots'][i])
    out=dict(schema_version=SCHEMA,operation=request['operation'],status='COMPLETED',record_id=saved['record_id'],analysis_id=saved['analysis_id'],
             request_fingerprint=fingerprint(q),result_fingerprint=fingerprint(r),evidence_fingerprint=fingerprint(saved['evidence']),
             code=q['code'],price_mode=q['price_mode'],bars=len(q['candles']),computation_status=r['status'],component_versions=r['component_versions'],
             evidence_coverage=saved['evidence']['coverage_status'],corporate_action_coverage=r['shared_input']['corporate_action_coverage'],
             data_quality=r['shared_input']['data_quality'],snapshot=snapshot,classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED',
             limitations=deepcopy(r['limitations']))
    if receipt is not None:out.update(store_status=receipt['status'],commit_status='COMMITTED')
    if request.get('include_bundle',False):out['saved_bundle']=saved
    return out


def execute_workflow(request,database,*,create_if_missing=False):
    stage='VALIDATE';commit='NOT_SAVED';receipt=None;identities={}
    try:
        request=deepcopy(request);op=_preflight(request)
        _require(isinstance(create_if_missing,bool),'create_if_missing','Boolean required')
        _require(not create_if_missing or op=='RUN','create_if_missing','Only RUN can initialize a new database')
        if op in ['RUN','LOOKUP']:
            identities=dict(request_fingerprint=fingerprint(request['job']),evidence_fingerprint=fingerprint(request['evidence']))
        if op=='RUN':
            stage='CALCULATE';result=run_analysis_job(request['job'])
            stage='VALIDATE_RESULT';validate_bundle(request['job'],result,request['evidence'])
            stage='PREPARE_STORE';store=_open_store(database,create=create_if_missing)
            stage='SAVE';commit='UNKNOWN'
            receipt=store.save(request['job'],result,request['evidence'],reason=request['reason']);commit='COMMITTED'
            stage='READ_BACK';saved=store.load(receipt['record_id'])
            return _view(saved,request,receipt=receipt)
        stage='PREPARE_STORE';store=_open_store(database)
        if op=='READ':
            stage='READ';return _view(store.load(request['record_id']),request)
        stage='LOOKUP';matches=[]
        for record in store.list_records(request['job']['code']):
            saved=store.load(record['record_id'])
            if fingerprint(saved['request'])==identities['request_fingerprint'] and fingerprint(saved['evidence'])==identities['evidence_fingerprint']:
                matches.append(dict(record_id=saved['record_id'],analysis_id=saved['analysis_id'],component_versions=saved['result']['component_versions'],
                                    evidence_coverage=saved['evidence']['coverage_status'],action_qualification='NOT_EVALUATED'))
        status='FOUND' if len(matches)==1 else 'NOT_FOUND' if not matches else 'MULTIPLE_VERSION_MATCHES'
        return dict(schema_version=SCHEMA,operation=op,status=status,matches=matches,**identities,action_qualification='NOT_EVALUATED')
    except WorkflowError:raise
    except DataError as e:
        raise WorkflowError(e.code,e.path,e.detail,stage=stage,commit_status=commit,
                            record_id=receipt['record_id'] if receipt else None,identities=identities) from None
    except Exception as e:
        raise WorkflowError('WORKFLOW_INTERNAL','workflow',type(e).__name__,stage=stage,commit_status=commit,
                            record_id=receipt['record_id'] if receipt else None,identities=identities) from None
