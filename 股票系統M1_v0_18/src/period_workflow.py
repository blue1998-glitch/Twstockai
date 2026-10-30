"""Independent headless period RUN/save/read. Only explicit RUN imports an engine."""
from copy import deepcopy
import re
from contracts import DataError, fingerprint, iso_date
from period_store import PeriodStore, StoreFailure
from period_store_contracts import canonical, validate_bundle

SCHEMA = 'period-workflow/1.0'
VERSION = 'period-workflow-0.1'
HASH = re.compile(r'^sha256:[0-9a-f]{64}$')


class WorkflowError(DataError):
    def __init__(self, code, path, detail, *, stage, operation=None,
                 commit_status='NOT_SAVED', identities=None):
        super().__init__(code, path, detail)
        self.stage, self.operation, self.commit_status = stage, operation, commit_status
        self.identities = identities or {}

    def as_dict(self):
        out = super().as_dict()
        out.update(schema_version=SCHEMA, workflow_version=VERSION, status='WORKFLOW_ERROR',
                   operation=self.operation, stage=self.stage, commit_status=self.commit_status, **self.identities)
        out['recovery_operation'] = ('READ' if out.get('analysis_id') else
                                     'LOOKUP' if self.commit_status == 'UNKNOWN' else None)
        return out


def require(ok, path, detail):
    if not ok: raise DataError('PERIOD_WORKFLOW_REQUEST', path, detail)


def _preflight(request, create):
    canonical(request)
    require(isinstance(request, dict), 'request', 'Versioned object required')
    require(request.get('schema_version') == SCHEMA, 'schema_version', 'Use period-workflow/1.0')
    op = request.get('operation')
    required = {'RUN': {'job','reason'}, 'READ': {'analysis_id'}, 'LOOKUP': {'filters'}}
    require(isinstance(op, str) and op in required, 'operation', 'Use RUN, READ or LOOKUP')
    fields = {'schema_version','operation'} | required[op]
    allowed = fields | ({'include_bundle'} if op != 'LOOKUP' else set())
    require(fields <= set(request) <= allowed, 'request.fields', 'Fixed operation fields; unknown fields rejected')
    require(type(create) is bool and (not create or op == 'RUN'), 'create_if_missing', 'Only RUN can initialize a store')
    if 'include_bundle' in request:
        require(type(request['include_bundle']) is bool, 'include_bundle', 'Boolean required')
    if op == 'RUN':
        q = request['job']
        require(isinstance(q, dict) and q.get('schema_version') == 'stock-period-analysis/1.0',
                'job', 'Existing standalone period job required')
        require(isinstance(request['reason'], str) and bool(request['reason'].strip()) and len(request['reason']) <= 2000,
                'reason', 'Immutable reason of 1 to 2000 characters required')
    elif op == 'READ':
        require(isinstance(request['analysis_id'], str) and HASH.fullmatch(request['analysis_id']),
                'analysis_id', 'Exact full analysis ID required')
    else:
        f = request['filters']; needed = {'code','exchange','price_mode','as_of'}
        optional = {'rule_version','aggregation_version','adapter_version','parameters_fingerprint','source_id','request_fingerprint'}
        require(isinstance(f, dict) and needed <= set(f) <= needed | optional,
                'filters', 'Exact stock/exchange/mode/as_of required; no latest fallback')
        require(all(isinstance(v, str) and bool(v.strip()) for v in f.values()), 'filters', 'Nonempty strings required')
        require(f['exchange'] in ('TWSE','TPEX') and f['price_mode'] in ('RAW_CANDIDATE','ADJUSTED_CANDIDATE'),
                'filters.scope', 'Explicit exchange and price mode required')
        iso_date(f['as_of'], 'filters.as_of')
        for k in ('request_fingerprint','parameters_fingerprint'):
            if k in f: require(HASH.fullmatch(f[k]), 'filters.' + k, 'Full sha256 fingerprint required')
    return op


def _view(saved, op, commit, include_bundle, receipt=None):
    r = saved['result']; s = r['snapshot']
    out = dict(schema_version=SCHEMA, workflow_version=VERSION, operation=op, status='COMPLETED',
               commit_status=commit, analysis_id=saved['analysis_id'], record_fingerprint=saved['record_fingerprint'],
               request_fingerprint=r['request_fingerprint'], result_fingerprint=fingerprint(r),
               metadata=deepcopy(saved['metadata']), computation_status=r['status'], snapshot=deepcopy(s),
               classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED',
               limitations=deepcopy(s['limitations']))
    if receipt is not None: out['store_status'] = receipt['status']
    if include_bundle: out['saved_bundle'] = deepcopy(saved)
    return out


def execute_period_workflow(request, store_path, *, create_if_missing=False):
    stage = 'VALIDATE'; commit = 'NOT_SAVED'; identities = {}; op = None
    if isinstance(request, dict) and isinstance(request.get('operation'), str):
        op = request['operation']
        if op in ('READ','LOOKUP'): commit = 'NOT_APPLICABLE'
    try:
        request = deepcopy(request)
        op = _preflight(request, create_if_missing)
        if op == 'READ': identities['analysis_id'] = request['analysis_id']
        if op == 'RUN':
            identities['request_fingerprint'] = fingerprint(request['job'])
            stage = 'CALCULATE'
            from period_jobs import run_period_job  # Deliberately lazy: no engine on READ/LOOKUP.
            result = run_period_job(request['job'])
            stage = 'VALIDATE_RESULT'
            validate_bundle(request['job'], result)
            identities.update(analysis_id=result['analysis_id'], result_fingerprint=fingerprint(result))
            stage = 'PREPARE_STORE'
            store = PeriodStore.create(store_path) if create_if_missing else PeriodStore(store_path)
            stage = 'SAVE'; commit = 'UNKNOWN'
            receipt = store.save(request['job'], result, reason=request['reason'])
            # A successful supported store receipt is the durable acknowledgment.
            require(receipt.get('commit_status') == 'COMMITTED' and receipt.get('analysis_id') == result['analysis_id'] and
                    receipt.get('status') in ('SAVED','DUPLICATE'), 'save.receipt', 'Invalid save acknowledgment; resolve via READ')
            commit = 'COMMITTED'; stage = 'READ_BACK'
            saved = store.load(result['analysis_id'])
            require(saved['analysis_id'] == result['analysis_id'] and fingerprint(saved['request']) == identities['request_fingerprint'] and
                    fingerprint(saved['result']) == identities['result_fingerprint'] and saved['reason'] == request['reason'],
                    'read_back', 'Saved content differs from calculated request/result/reason')
            return _view(saved, op, commit, request.get('include_bundle', False), receipt)
        stage = 'PREPARE_STORE'; store = PeriodStore(store_path)
        if op == 'READ':
            identities['analysis_id'] = request['analysis_id']; stage = 'READ'
            return _view(store.load(request['analysis_id']), op, commit, request.get('include_bundle', False))
        stage = 'LOOKUP'; f = dict(request['filters']); request_fp = f.pop('request_fingerprint', None)
        matches = store.lookup(**f)
        if request_fp is not None: matches = [x for x in matches if x['request_fingerprint'] == request_fp]
        return dict(schema_version=SCHEMA, workflow_version=VERSION, operation=op,
                    status='NOT_FOUND' if not matches else 'FOUND' if len(matches) == 1 else 'MULTIPLE_MATCHES',
                    commit_status=commit, filters=request['filters'], matches=matches,
                    classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED')
    except WorkflowError: raise
    except StoreFailure as e:
        if stage == 'SAVE': commit = e.commit_status
        if e.analysis_id: identities['analysis_id'] = e.analysis_id
        raise WorkflowError(e.code, 'store', e.detail, stage=stage, operation=op,
                            commit_status=commit, identities=identities) from None
    except DataError as e:
        raise WorkflowError(e.code, e.path, e.detail, stage=stage, operation=op,
                            commit_status=commit, identities=identities) from None
    except Exception as e:
        # An unexpected save exception may occur after the commit point. Never claim NOT_SAVED there.
        raise WorkflowError('PERIOD_WORKFLOW_INTERNAL', 'workflow', type(e).__name__, stage=stage, operation=op,
                            commit_status=commit, identities=identities) from None
