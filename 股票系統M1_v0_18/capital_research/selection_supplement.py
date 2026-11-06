"""Append an explicit research choice to a saved waiting parent, never generate."""
from copy import deepcopy
from pathlib import Path
from rotation_research.store import Journal
from .lifecycle import FLAGS, _fp, _signed, _time
from .research_choice import bind_saved_source
from .research_operation import read_operation, _keys as operation_keys, _read_header, _validate_generation, _validate_choice, _persist

INPUT='capital-selection-supplement-input/0.1'
REQUEST='capital-selection-supplement-request/0.1'
RESULT='capital-selection-supplement-result/0.1'
STAGES=('request','choice','result')


def _require(condition,reason):
    if not condition:raise ValueError(reason)


def _keys(identity):
    return {k:v for k,v in operation_keys(identity).items() if k in STAGES}


def _request(request):
    _require(set(request)=={'schema','synthetic','parent_binding','selection','recorded_at'} and
        request['schema']==INPUT and request['synthetic'] is True,'EXPLICIT_SYNTHETIC_SUPPLEMENT_REQUIRED')
    _require(isinstance(request['selection'],dict) and isinstance(request['recorded_at'],str),
        'EXPLICIT_SELECTION_AND_RECORD_TIME_REQUIRED')
    _time(request['recorded_at'])


def _parent(root,identity):
    view=read_operation(root,identity)
    _require(view['workflow_status']=='READ_ONLY','PARENT_NOT_COMPLETE')
    result=view['operation']
    _require(result['outcome']=='AWAITING_EXPLICIT_SELECTION','PARENT_NOT_AWAITING_EXPLICIT_SELECTION')
    keys=view['keys'];store=Journal(root)
    header=store.read(keys['request'])['value'];generation=store.read(keys['generation'])['value']
    request=_read_header(header,identity,keys)
    _validate_generation(request,generation)
    _require(header['header_id']==result['header_id'] and header['request_id']==result['request_id'] and
        _fp(generation)==result['generation_id'] and request['selection'] is None and
        generation['adapter']['status']=='GENERATED' and result['choice_record_id'] is None,
        'PARENT_SAVED_CHAIN_CONFLICT')
    binding=dict(parent_operation_id=identity,parent_header_id=header['header_id'],
        parent_request_id=header['request_id'],parent_result_id=result['result_id'],
        generation_id=_fp(generation),source_binding=bind_saved_source(generation))
    return binding,generation


def _no_overlap(parent_root,parent_id,root,keys):
    parent=Journal(parent_root);child=Journal(root)
    old={parent.path(k).resolve() for k in operation_keys(parent_id).values()}
    _require(not any(child.path(k).resolve() in old for k in keys.values()),'PARENT_CHILD_KEY_OVERLAP')


def _receipt(mode,identity):
    return dict(schema='capital-selection-supplement-receipt/0.1',mode=mode,supplement_id=identity,
        workflow_status='PENDING',reasons=[],failed_stage=None,keys=None,parent_binding=None,
        storage={k:'NOT_PERFORMED' if mode=='SELECT' else 'NOT_READ' for k in STAGES},
        observed=dict(choice_status=None,check_status=None),supplement=None,saved_files_preserved=True,
        generation='NOT_PERFORMED_REUSED_SAVED_PARENT',order_generation='NOT_PERFORMED',
        execution='NOT_PERFORMED',execution_authorized=False,primary_pressure_id=None,**{k:False for k in FLAGS})


def _read_header_child(value,identity,keys,binding):
    _require(value['schema']==REQUEST and value['synthetic'] is True and
        value['supplement_id']==identity and value['keys']==keys,'CHILD_HEADER_CONFLICT')
    _signed(value,'header_id');request=value['request'];_request(request)
    _require(value['request_id']==_fp(request),'CHILD_REQUEST_FINGERPRINT_CONFLICT')
    _require(request['parent_binding']==binding,'PARENT_BINDING_MISMATCH')
    return request


def _choice_request(request,generation):
    return dict(schema='capital-research-choice-input/0.1',synthetic=True,saved_result=deepcopy(generation),
        source_binding=bind_saved_source(generation),selection=deepcopy(request['selection']),recorded_at=request['recorded_at'])


def _choose(root,key,request):
    from .research_choice_workflow import select_and_save
    return select_and_save(root,key,request)


def _check(choice,generation):
    from .research_choice_source import check_saved
    return check_saved(choice,generation)


def _validate_result(value,header,binding,choice):
    _require(value['schema']==RESULT and value['synthetic'] is True,'UNSUPPORTED_SUPPLEMENT_RESULT')
    _signed(value,'result_id')
    _require(value['supplement_id']==header['supplement_id'] and value['header_id']==header['header_id'] and
        value['request_id']==header['request_id'] and value['parent_binding']==binding and
        value['choice_record_id']==choice['choice']['record_id'],'CHILD_RESULT_CHAIN_CONFLICT')
    _require(all(value[k] is False for k in FLAGS) and value['primary_pressure_id'] is None and
        value['execution_authorized'] is False and value['order_generation']==value['execution']=='NOT_PERFORMED',
        'SUPPLEMENT_QUALIFICATION_CONFLICT')
    c=choice['choice'];request=header['request'];check=value['source_check']
    _require(value['requested_selection']==request['selection'] and value['recorded_at']==request['recorded_at'] and
        value['choice_status']==c['status'] and value['selected_targets']==(c['selected']['plan']['targets'] if c['selected'] else None),
        'SUPPLEMENT_CHOICE_SUMMARY_CONFLICT')
    if c['status']=='REFUSED':
        expected='SUPPLEMENT_CHOICE_REFUSED';_require(check is None,'REFUSED_SUPPLEMENT_ADVANCED')
    else:
        _require(check is not None and check['schema']=='capital-research-choice-source-check/0.1' and
            check['record_id']==c['record_id'] and check['choice_status']==c['status'] and
            all(check[k] is False for k in FLAGS) and check['primary_pressure_id'] is None and
            check['execution_authorized'] is False and check['order_generation']==check['execution']=='NOT_PERFORMED',
            'SUPPLEMENT_SOURCE_CHECK_LINK_CONFLICT')
        if check['check_status']=='MATCHED':
            _require(check['candidate_check']=='EXACT_UNIQUE_MEMBER' and len(check['columns'])==2 and
                all(row['candidate']==c['selected'] and row['binding']==binding['source_binding'] for row in check['columns']),
                'SUPPLEMENT_SOURCE_CHECK_CONTENT_CONFLICT')
            expected='COMPLETED_SUPPLEMENT_CONDITIONAL_INTENT' if c['status']=='RECORDED_CONDITIONAL_RESEARCH_INTENT' else 'COMPLETED_SUPPLEMENT_INTENT'
        else:
            _require(check['check_status']=='REFUSED' and not check['columns'],'SUPPLEMENT_SOURCE_CHECK_STATUS_CONFLICT')
            expected='SUPPLEMENT_SOURCE_CHECK_REFUSED'
    _require(value['outcome']==expected,'SUPPLEMENT_OUTCOME_CONFLICT')


def _finish(store,receipt,header,binding,choice,check):
    c=choice['choice']
    outcome='SUPPLEMENT_CHOICE_REFUSED' if c['status']=='REFUSED' else (
        'SUPPLEMENT_SOURCE_CHECK_REFUSED' if check['check_status']!='MATCHED' else
        'COMPLETED_SUPPLEMENT_CONDITIONAL_INTENT' if c['status']=='RECORDED_CONDITIONAL_RESEARCH_INTENT' else 'COMPLETED_SUPPLEMENT_INTENT')
    request=header['request']
    value=dict(schema=RESULT,synthetic=True,supplement_id=header['supplement_id'],header_id=header['header_id'],
        request_id=header['request_id'],parent_binding=deepcopy(binding),choice_record_id=c['record_id'],
        choice_status=c['status'],source_check=deepcopy(check),outcome=outcome,
        requested_selection=deepcopy(request['selection']),recorded_at=request['recorded_at'],
        selected_targets=deepcopy(c['selected']['plan']['targets']) if c['selected'] else None,
        reasons=deepcopy(c['reasons'] if c['status']=='REFUSED' else check['reasons']),
        order_generation='NOT_PERFORMED',execution='NOT_PERFORMED',execution_authorized=False,
        primary_pressure_id=None,**{k:False for k in FLAGS})
    value['result_id']=_fp(value);_validate_result(value,header,binding,choice)
    status,saved,errors=_persist(store,receipt['keys']['result'],value);receipt['storage']['result']=status
    if status!='SAVED_AND_READ_BACK':
        receipt.update(workflow_status='STOPPED_STORAGE',failed_stage='result',reasons=errors,computed_outcome=outcome)
    else:
        receipt.update(workflow_status=outcome,supplement=saved,failed_stage=None,reasons=deepcopy(value['reasons']))
    return receipt


def select_supplement(parent_root,parent_id,root,identity,request):
    receipt=_receipt('SELECT',identity);stage='input'
    try:
        keys=_keys(identity);receipt['keys']=keys;_request(request)
        _no_overlap(parent_root,parent_id,root,keys)
        stage='parent';binding,generation=_parent(parent_root,parent_id);receipt['parent_binding']=binding
        _require(request['parent_binding']==binding,'PARENT_BINDING_MISMATCH')
        stage='request';store=Journal(root)
        existing=[s for s in STAGES if store.path(keys[s]).exists() or store.path(keys[s]).is_symlink()]
        if existing:
            receipt.update(workflow_status='SUPPLEMENT_EXISTS_READ_REQUIRED',existing_stages=existing,
                reasons=['EXISTING_CHILD_FILES_PRESERVED_USE_READ'])
            if 'request' in existing:
                try:
                    old=store.read(keys['request'])['value'];_read_header_child(old,identity,keys,binding)
                    if old['request_id']!=_fp(request):
                        receipt.update(workflow_status='SUPPLEMENT_ID_CONFLICT',reasons=['DIFFERENT_REQUEST_SAME_CHILD_ID'])
                except (OSError,ValueError,KeyError,TypeError):
                    receipt['reasons'].append('EXISTING_CHILD_HEADER_UNREADABLE_NOT_REPAIRED')
            return receipt
        header=dict(schema=REQUEST,synthetic=True,supplement_id=identity,keys=keys,request_id=_fp(request),request=deepcopy(request))
        header['header_id']=_fp(header)
        status,saved,errors=_persist(store,keys['request'],header);receipt['storage']['request']=status
        if status!='SAVED_AND_READ_BACK':
            receipt.update(workflow_status='STOPPED_STORAGE',failed_stage='request',reasons=errors);return receipt
        header=saved;stage='choice'
        selected=_choose(root,keys['choice'],_choice_request(request,generation));receipt['storage']['choice']=selected['storage_status']
        if selected['storage_status']!='SAVED_AND_READ_BACK':
            receipt.update(workflow_status='STOPPED_STORAGE',failed_stage='choice',reasons=selected['reasons']);return receipt
        choice=selected['record']['value'];_validate_choice(request,generation,choice)
        receipt['observed']['choice_status']=choice['choice']['status']
        stage='source_check';check=None
        if choice['choice']['status']!='REFUSED':
            check=_check(choice,generation);receipt['observed']['check_status']=check['check_status']
        return _finish(store,receipt,header,binding,choice,check)
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        receipt.update(workflow_status='INPUT_REFUSED' if stage=='input' else 'PARENT_REFUSED' if stage=='parent' else 'STOPPED_VALIDATION',
            failed_stage=stage,reasons=[str(exc)])
        return receipt


def read_supplement(parent_root,parent_id,root,identity):
    receipt=_receipt('READ',identity)
    try:
        keys=_keys(identity);receipt['keys']=keys;_no_overlap(parent_root,parent_id,root,keys)
        binding,generation=_parent(parent_root,parent_id);receipt['parent_binding']=binding
        store=Journal(root);values={}
        for stage in STAGES:
            receipt['failed_stage']=stage
            try:
                values[stage]=store.read(keys[stage])['value'];receipt['storage'][stage]='READ_ONLY'
            except FileNotFoundError:
                values[stage]=None;receipt['storage'][stage]='MISSING'
        header=values['request'];_require(header is not None,'SUPPLEMENT_REQUEST_MISSING')
        request=_read_header_child(header,identity,keys,binding);choice=values['choice'];value=values['result']
        if choice is not None:
            _validate_choice(request,generation,choice);receipt['observed']['choice_status']=choice['choice']['status']
        if value is None:
            receipt.update(workflow_status='INCOMPLETE_SUPPLEMENT_PREFIX',failed_stage=None,
                reasons=['NO_SAVED_CHILD_RESULT_NO_AUTOMATIC_RESUME'])
        else:
            _require(choice is not None,'SUPPLEMENT_CHOICE_MISSING')
            _validate_result(value,header,binding,choice)
            receipt['observed']['check_status']=value['source_check']['check_status'] if value['source_check'] else None
            receipt.update(workflow_status='READ_ONLY',supplement=value,failed_stage=None,reasons=[])
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        receipt.update(workflow_status='UNREADABLE',reasons=[str(exc)])
    return receipt
