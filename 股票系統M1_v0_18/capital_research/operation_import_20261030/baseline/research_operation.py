"""External staged IO coordinator. READ never calls generation, selection or checks."""
from copy import deepcopy
import json
import re
from rotation_research.store import Journal
from .lifecycle import FLAGS, _fp, _signed, _time
from .research_choice import bind_saved_source, validate_record

INPUT = 'capital-research-operation-input/0.1'
REQUEST = 'capital-research-operation-request/0.1'
RESULT = 'capital-research-operation-result/0.1'
STAGES = ('request','generation','choice','result')


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _keys(identity):
    _require(isinstance(identity,str) and re.fullmatch('[A-Za-z0-9_-]{1,90}',identity), 'EXPLICIT_OPERATION_ID_REQUIRED')
    return {s:identity+'--'+s for s in STAGES}


def _request(request):
    _require(set(request)=={'schema','synthetic','generation_input','selection','recorded_at'} and
        request['schema']==INPUT and request['synthetic'] is True, 'EXPLICIT_SYNTHETIC_OPERATION_REQUIRED')
    g=request['generation_input']
    _require(isinstance(g,dict) and g.get('schema')=='capital-quantity-after-retry-input/0.1' and
        g.get('synthetic') is True, 'EXPLICIT_AFTER_RETRY_INPUT_REQUIRED')
    if request['selection'] is not None:
        _require(isinstance(request['selection'],dict) and isinstance(request['recorded_at'],str),
            'EXPLICIT_SELECTION_AND_RECORD_TIME_REQUIRED')
        _time(request['recorded_at'])


def _receipt(mode, identity):
    return dict(schema='capital-research-operation-receipt/0.1', mode=mode, operation_id=identity,
        workflow_status='PENDING', reasons=[], failed_stage=None, keys=None,
        storage={s:'NOT_PERFORMED' if mode=='RUN' else 'MISSING' for s in STAGES},
        observed=dict(generation_status=None,choice_status=None,check_status=None), operation=None,
        saved_files_preserved=True, order_generation='NOT_PERFORMED', execution='NOT_PERFORMED',
        execution_authorized=False, primary_pressure_id=None, **{k:False for k in FLAGS})


def _persist(store, key, value):
    try:
        store.save(key,value)
        saved=store.read(key)['value']
        _require(saved==value,'SAVED_READBACK_CONTENT_CONFLICT')
        return 'SAVED_AND_READ_BACK',saved,[]
    except ValueError as exc:
        status='NOT_SAVED' if str(exc).startswith(('Identity conflict:','Invalid identity')) else 'UNKNOWN'
        return status,None,[str(exc)]
    except OSError as exc:
        return 'UNKNOWN',None,[str(exc)]


def _header(identity, request, keys):
    h=dict(schema=REQUEST,synthetic=True,operation_id=identity,keys=keys,request_id=_fp(request),
        request_json=json.dumps(request,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))
    h['header_id']=_fp(h)
    return h


def _read_header(header, identity, keys):
    _require(header['schema']==REQUEST and header['synthetic'] is True and
        header['operation_id']==identity and header['keys']==keys,'SAVED_OPERATION_HEADER_CONFLICT')
    _signed(header,'header_id')
    request=json.loads(header['request_json']);_request(request)
    _require(header['request_id']==_fp(request),'SAVED_OPERATION_REQUEST_CONFLICT')
    return request


def _generation(request):
    # Lazy import only on a new explicit RUN, after its request is saved/read.
    from .quantity_after_retry import generate_after_retry
    return generate_after_retry(deepcopy(request))


def _selection(root, key, request):
    from .research_choice_workflow import select_and_save
    return select_and_save(root,key,request)


def _source_check(choice, generation):
    from .research_choice_source import check_saved
    return check_saved(choice,generation)


def _validate_generation(request, generation):
    a=generation['adapter']
    _require(a['schema']=='capital-quantity-after-retry/0.1' and a['synthetic'] is True and
        generation['source_integrity_metadata']['full_input_id']==_fp(request['generation_input']),
        'SAVED_GENERATION_REQUEST_CONFLICT')
    _require(a['status'] in ('GENERATED','STOPPED_NOT_IMPLEMENTED','STOPPED_INPUT_ERROR','STOPPED_QUANTITY_GATE') and
        all(a[k] is False for k in FLAGS) and a['primary_pressure_id'] is None and
        a['selected_id'] is None and a['ranking'] is None and
        a['order_generation']==a['execution']=='NOT_PERFORMED','SAVED_GENERATION_SCOPE_CONFLICT')
    if a['status']=='GENERATED':
        bind_saved_source(generation)


def _choice_request(request, generation):
    return dict(schema='capital-research-choice-input/0.1',synthetic=True,saved_result=deepcopy(generation),
        source_binding=bind_saved_source(generation),selection=deepcopy(request['selection']),
        recorded_at=request['recorded_at'])


def _validate_choice(request, generation, choice):
    c=validate_record(choice)['choice']
    expected=_choice_request(request,generation)
    _require(request['selection'] is not None and
        c['request_id']==_fp(expected) and c['source_binding']==expected['source_binding'] and
        c['requested_selection']==request['selection'] and c['recorded_at']==request['recorded_at'],
        'SAVED_CHOICE_OPERATION_CONFLICT')


def _catalog(generation):
    g=generation['adapter']['generation']
    if g is None:
        return None
    return [deepcopy({k:c[k] for k in ('id','classification','feasible_for_research','reasons','plan')})
        for c in g['research']['candidates']]


def _validate_result(value, header, request, generation, choice):
    _require(value['schema']==RESULT and value['synthetic'] is True,'UNSUPPORTED_SAVED_OPERATION_RESULT')
    _signed(value,'result_id')
    _require(value['operation_id']==header['operation_id'] and value['header_id']==header['header_id'] and
        value['request_id']==header['request_id'] and value['generation_id']==_fp(generation) and
        value['choice_record_id']==(choice['choice']['record_id'] if choice else None),
        'SAVED_OPERATION_STAGE_CHAIN_CONFLICT')
    _require(all(value[k] is False for k in FLAGS) and value['primary_pressure_id'] is None and
        value['execution_authorized'] is False and value['order_generation']==value['execution']=='NOT_PERFORMED',
        'SAVED_OPERATION_QUALIFICATION_CONFLICT')
    _require(value['generation_status']==generation['adapter']['status'] and
        value['choice_status']==(choice['choice']['status'] if choice else None) and
        value['candidate_catalog']==_catalog(generation),'SAVED_OPERATION_SUMMARY_CONFLICT')
    check=value['source_check']
    if generation['adapter']['status']!='GENERATED':
        expected='GENERATION_REFUSED';_require(choice is None and check is None,'UNEXPECTED_LATER_STAGE')
    elif request['selection'] is None:
        expected='AWAITING_EXPLICIT_SELECTION';_require(choice is None and check is None,'UNEXPECTED_LATER_STAGE')
    else:
        _require(choice is not None,'SAVED_OPERATION_CHOICE_MISSING')
        c=choice['choice']
        if c['status']=='REFUSED':
            expected='CHOICE_REFUSED';_require(check is None,'REJECTED_CHOICE_ADVANCED')
        else:
            _require(check is not None and check['schema']=='capital-research-choice-source-check/0.1' and
                check['record_id']==c['record_id'] and check['choice_status']==c['status'] and
                all(check[k] is False for k in FLAGS) and check['primary_pressure_id'] is None and
                check['execution_authorized'] is False and check['order_generation']==check['execution']=='NOT_PERFORMED',
                'SAVED_SOURCE_CHECK_LINK_CONFLICT')
            if check['check_status']=='MATCHED':
                _require(len(check['columns'])==2 and check['candidate_check']=='EXACT_UNIQUE_MEMBER' and
                    all(col['binding']==c['source_binding'] and col['candidate']==c['selected'] for col in check['columns']),
                    'SAVED_SOURCE_CHECK_SNAPSHOT_CONFLICT')
                expected='COMPLETED_CONDITIONAL_INTENT' if c['status']=='RECORDED_CONDITIONAL_RESEARCH_INTENT' else 'COMPLETED_RESEARCH_INTENT'
            else:
                _require(check['check_status']=='REFUSED' and not check['columns'],'SAVED_SOURCE_CHECK_STATUS_CONFLICT')
                expected='SOURCE_CHECK_REFUSED'
    _require(value['outcome']==expected,'SAVED_OPERATION_OUTCOME_CONFLICT')


def _finish(store, receipt, header, request, generation, choice, check, outcome, reasons):
    value=dict(schema=RESULT,synthetic=True,operation_id=header['operation_id'],header_id=header['header_id'],
        request_id=header['request_id'],generation_id=_fp(generation),
        choice_record_id=choice['choice']['record_id'] if choice else None,
        generation_status=generation['adapter']['status'],choice_status=choice['choice']['status'] if choice else None,
        source_check=deepcopy(check),outcome=outcome,reasons=deepcopy(reasons),candidate_catalog=_catalog(generation),
        stage_storage={k:receipt['storage'][k] for k in ('request','generation','choice')},
        order_generation='NOT_PERFORMED',execution='NOT_PERFORMED',execution_authorized=False,
        primary_pressure_id=None,**{k:False for k in FLAGS})
    value['result_id']=_fp(value)
    _validate_result(value,header,request,generation,choice)
    status,saved,errors=_persist(store,receipt['keys']['result'],value)
    receipt['storage']['result']=status
    if status!='SAVED_AND_READ_BACK':
        receipt.update(workflow_status='STOPPED_STORAGE',failed_stage='result',reasons=errors,computed_outcome=outcome)
    else:
        receipt.update(workflow_status=outcome,operation=saved,reasons=deepcopy(reasons),failed_stage=None)
    return receipt


def run_operation(root, identity, request):
    receipt=_receipt('RUN',identity)
    try:
        keys=_keys(identity);receipt['keys']=keys;_request(request)
        store=Journal(root)
        existing=[s for s in STAGES if store.path(keys[s]).exists() or store.path(keys[s]).is_symlink()]
        if existing:
            receipt.update(workflow_status='OPERATION_EXISTS_READ_REQUIRED',existing_stages=existing,
                reasons=['EXISTING_FILES_PRESERVED_USE_EXPLICIT_READ'])
            if 'request' in existing:
                try:
                    old=store.read(keys['request'])['value'];_read_header(old,identity,keys)
                    if old['request_id']!=_fp(request):
                        receipt.update(workflow_status='OPERATION_ID_CONFLICT',reasons=['DIFFERENT_REQUEST_SAME_OPERATION_ID'])
                except (OSError,ValueError,KeyError,TypeError):
                    receipt['reasons'].append('EXISTING_REQUEST_UNREADABLE_NOT_REPAIRED')
            return receipt
        header=_header(identity,request,keys)
        for stage,value in [('request',header)]:
            status,saved,errors=_persist(store,keys[stage],value);receipt['storage'][stage]=status
            if status!='SAVED_AND_READ_BACK':
                receipt.update(workflow_status='STOPPED_STORAGE',failed_stage=stage,reasons=errors);return receipt
            header=saved
        receipt['failed_stage']='generation'
        generation=_generation(request['generation_input'])
        status,saved,errors=_persist(store,keys['generation'],generation);receipt['storage']['generation']=status
        if status!='SAVED_AND_READ_BACK':
            receipt.update(workflow_status='STOPPED_STORAGE',reasons=errors);return receipt
        generation=saved;_validate_generation(request,generation)
        receipt['observed']['generation_status']=generation['adapter']['status']
        if generation['adapter']['status']!='GENERATED':
            return _finish(store,receipt,header,request,generation,None,None,'GENERATION_REFUSED',generation['adapter']['reasons'])
        if request['selection'] is None:
            return _finish(store,receipt,header,request,generation,None,None,'AWAITING_EXPLICIT_SELECTION',['NO_EXPLICIT_SELECTION'])
        receipt['failed_stage']='choice'
        selected=_selection(root,keys['choice'],_choice_request(request,generation))
        receipt['storage']['choice']=selected['storage_status']
        if selected['storage_status']!='SAVED_AND_READ_BACK':
            receipt.update(workflow_status='STOPPED_STORAGE',reasons=selected['reasons']);return receipt
        choice=selected['record']['value'];_validate_choice(request,generation,choice)
        receipt['observed']['choice_status']=choice['choice']['status']
        if choice['choice']['status']=='REFUSED':
            return _finish(store,receipt,header,request,generation,choice,None,'CHOICE_REFUSED',choice['choice']['reasons'])
        receipt['failed_stage']='source_check'
        check=_source_check(choice,generation);receipt['observed']['check_status']=check['check_status']
        outcome=('COMPLETED_CONDITIONAL_INTENT' if choice['choice']['status']=='RECORDED_CONDITIONAL_RESEARCH_INTENT'
            else 'COMPLETED_RESEARCH_INTENT') if check['check_status']=='MATCHED' else 'SOURCE_CHECK_REFUSED'
        return _finish(store,receipt,header,request,generation,choice,check,outcome,check['reasons'])
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        receipt.update(workflow_status='INPUT_REFUSED' if receipt['storage']['request']=='NOT_PERFORMED' else 'STOPPED_VALIDATION',
            reasons=[str(exc)])
        return receipt


def read_operation(root, identity):
    receipt=_receipt('READ',identity)
    try:
        keys=_keys(identity);receipt['keys']=keys;store=Journal(root);values={}
        for stage in STAGES:
            receipt['failed_stage']=stage
            try:
                values[stage]=store.read(keys[stage])['value'];receipt['storage'][stage]='READ_ONLY'
            except FileNotFoundError:
                values[stage]=None
        header=values['request'];_require(header is not None,'SAVED_REQUEST_MISSING_NO_RECONSTRUCTION')
        request=_read_header(header,identity,keys)
        generation=values['generation'];choice=values['choice'];value=values['result']
        if generation is not None:
            _validate_generation(request,generation)
            receipt['observed']['generation_status']=generation['adapter']['status']
        if choice is not None:
            _require(generation is not None,'SAVED_GENERATION_MISSING')
            _validate_choice(request,generation,choice)
            receipt['observed']['choice_status']=choice['choice']['status']
        if value is None:
            receipt.update(workflow_status='INCOMPLETE_SAVED_PREFIX',failed_stage=None,
                reasons=['NO_SAVED_FINAL_RESULT_NO_AUTOMATIC_RESUME'])
        else:
            _require(generation is not None,'SAVED_GENERATION_MISSING')
            _validate_result(value,header,request,generation,choice)
            receipt['observed']['check_status']=value['source_check']['check_status'] if value['source_check'] else None
            receipt.update(workflow_status='READ_ONLY',operation=value,failed_stage=None,reasons=[])
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        receipt.update(workflow_status='UNREADABLE',reasons=[str(exc)])
    return receipt
