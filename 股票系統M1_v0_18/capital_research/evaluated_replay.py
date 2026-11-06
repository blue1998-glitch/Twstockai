"""External replay -> immutable save/readback -> evaluation coordinator.

Numerical backends are imported only by an explicit fresh RUN. READ only checks
saved signatures, references and projections; it cannot replay or re-evaluate.
"""
from copy import deepcopy
import json
from rotation_research.store import Journal
from .lifecycle import FLAGS,_fp,_signed,_time
from .research_operation import _persist,_keys as _identity_keys

INPUT='capital-evaluated-replay-input/0.1'
HEADER='capital-evaluated-replay-request/0.1'
EVALUATION_RECORD='capital-evaluated-replay-evaluation/0.1'
RESULT='capital-evaluated-replay-result/0.1'
STAGES=('request','replay','evaluation','result')
OUTCOMES={'EVALUATED':'COMPLETED_EVALUATED','REFUSED':'COMPLETED_EVALUATION_REFUSED'}


def _require(condition,reason):
    if not condition:raise ValueError(reason)


def _keys(identity):
    _identity_keys(identity)  # Reuse the existing explicit identity rule.
    return {s:identity+'--'+s for s in STAGES}


def _request(request):
    _require(set(request)=={'schema','synthetic','replay_input','evaluation_at'} and request['schema']==INPUT
        and request['synthetic'] is True,'EXPLICIT_SYNTHETIC_EVALUATED_REPLAY_REQUIRED')
    _time(request['evaluation_at']);r=request['replay_input']
    _require(isinstance(r,dict) and r.get('schema')=='capital-quantity-replay-input/0.1' and r.get('synthetic') is True,
        'EXPLICIT_QUANTITY_REPLAY_INPUT_REQUIRED')
    sources=r['origin_ledger']['sources']
    _require(bool(sources) and all(s['kind']=='ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET' for s in sources.values()),
        'NON_SYNTHETIC_SOURCE_NOT_SUPPORTED')


def _header(identity,request,keys):
    h=dict(schema=HEADER,synthetic=True,operation_id=identity,keys=keys,request_id=_fp(request),
        request_json=json.dumps(request,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))
    h['header_id']=_fp(h);return h


def _read_header(h,identity,keys):
    _require(h['schema']==HEADER and h['synthetic'] is True and h['operation_id']==identity and h['keys']==keys,
        'SAVED_REQUEST_IDENTITY_CONFLICT')
    _signed(h,'header_id');request=json.loads(h['request_json']);_request(request)
    _require(h['request_id']==_fp(request),'SAVED_REQUEST_CONTENT_CONFLICT')
    return request


def _replay(request):
    from .quantity_replay import replay_sequence
    return replay_sequence(deepcopy(request))


def _evaluation_input(request,replay):
    return dict(schema='capital-account-metrics-input/0.1',synthetic=True,
        evaluation_at=request['evaluation_at'],saved_result=deepcopy(replay))


def _evaluate(request):
    from .account_metrics import evaluate_saved
    return evaluate_saved(request)


def _validate_replay(request,saved):
    r=saved['replay'];i=request['replay_input']
    _require(r['schema']=='capital-quantity-replay/0.1' and r['synthetic'] is True and
        all(r[k] is False for k in FLAGS) and r['ranking'] is None and r['selected_strategy'] is None
        and r['strategy_validated'] is False and r['primary_pressure_id'] is None,'SAVED_REPLAY_SCOPE_CONFLICT')
    _require(saved['source_integrity_metadata']==dict(full_input_id=_fp(i),
        original_ledger_input_id=_fp(i['origin_ledger']),close_proof_id=_fp(i['ledger_close_proof'])),
        'SAVED_REPLAY_INPUT_CONFLICT')
    _require(r['status'] in {'COMPLETED_PROVIDED_ROUNDS','REFUSED_ROUND_LIMIT','STOPPED_CANDIDATE_GATE',
        'STOPPED_NOT_IMPLEMENTED','STOPPED_INPUT_ERROR','STOPPED_EXECUTION_REFUSAL'},'UNSUPPORTED_SAVED_REPLAY_STATUS')
    _require(len(r['rounds'])<=len(i['rounds']) and all(f['index']==n and f['id']==i['rounds'][n]['id']
        for n,f in enumerate(r['rounds'])),'SAVED_REPLAY_ROUND_CHAIN_CONFLICT')
    if r['status']=='COMPLETED_PROVIDED_ROUNDS':
        _require(len(r['rounds'])==len(i['rounds']) and bool(r['rounds']) and
            all(f['status']=='REPLAYED_EXPLICIT_INTENT' and f['execution'] is not None and f['checkpoint'] is not None
                for f in r['rounds']),'SAVED_COMPLETED_REPLAY_INCOMPLETE')


def _evaluation_record(header,request,replay,evaluation):
    v=dict(schema=EVALUATION_RECORD,synthetic=True,operation_id=header['operation_id'],header_id=header['header_id'],
        request_id=header['request_id'],replay_document_id=_fp(replay),evaluation_at=request['evaluation_at'],
        evaluation_input_id=_fp(_evaluation_input(request,replay)),evaluation=deepcopy(evaluation))
    v['record_id']=_fp(v);return v


def _validate_evaluation(record,header,request,replay):
    _require(record['schema']==EVALUATION_RECORD and record['synthetic'] is True,'UNSUPPORTED_EVALUATION_RECORD')
    _signed(record,'record_id')
    _require(record['operation_id']==header['operation_id'] and record['header_id']==header['header_id'] and
        record['request_id']==header['request_id'] and record['replay_document_id']==_fp(replay) and
        record['evaluation_at']==request['evaluation_at'] and
        record['evaluation_input_id']==_fp(_evaluation_input(request,replay)),'SAVED_EVALUATION_STAGE_CHAIN_CONFLICT')
    e=record['evaluation'];_signed(e,'evaluation_id')
    _require(e['schema']=='capital-account-metrics/0.1' and e['synthetic'] is True and e['status'] in OUTCOMES
        and all(e[k] is False for k in FLAGS) and e['primary_pressure_id'] is None and e['ranking'] is None
        and e['selected_strategy'] is None and e['strategy_validated'] is False,'SAVED_EVALUATION_SCOPE_CONFLICT')
    if e['status']=='REFUSED':
        _require(bool(e['reasons']) and all(e[k] is None for k in ('statistics','source','account','costs','initial_capital',
            'terminal_accrual_equity','terminal_net_equity','terminal_net_growth')),'REFUSED_EVALUATION_HAS_METRICS')
    else:
        r=replay['replay'];cp=r['historical_checkpoint'];last=r['last_execution'];source=e['source'];account=e['account']
        _require(r['status']=='COMPLETED_PROVIDED_ROUNDS' and e['reasons']==[] and
            source['document_id']==_fp(replay) and source['execution_result_id']==last['result_id'] and
            source['checkpoint_id']==cp['checkpoint_id'] and source['evaluation_at']==request['evaluation_at'] and
            source['ledger_input_id']==last['ledger']['input_id'] and source['origin_ledger_input_id']==last['origin_ledger_input_id'],
            'SAVED_METRICS_SOURCE_CONFLICT')
        _require(account['saved_row']==cp['state']['row'] and all(account[k]==cp['state'][k] for k in
            ('general_reserved_cash','origin_initial_capital','external_flow','opening_unavailable_shares',
             'latest_decision_id','latest_common_account_id','reviewed_evidence_tokens')),'SAVED_METRICS_ACCOUNT_CONFLICT')
        _require(_time(source['ledger_available_at'])<=_time(request['evaluation_at']) and
            source['ledger_available_at']==cp['state']['ledger_close']['available_at'],'SAVED_METRICS_AVAILABILITY_CONFLICT')


def _summary(e):
    s=e['statistics']
    return dict(initial_capital=e['initial_capital'],terminal_accrual_equity=e['terminal_accrual_equity'],
        terminal_net_equity=e['terminal_net_equity'],terminal_net_growth=e['terminal_net_growth'],costs=deepcopy(e['costs']),
        statistics=None if s is None else {k:deepcopy(s[k]) for k in ('period_accrual_growth','maximum_drawdown',
            'maximum_drawdown_episode','maximum_drawdown_duration_calendar_days','recovery_censored','ongoing_underwater_calendar_days')})


def _result(header,replay,record):
    e=record['evaluation'];v=dict(schema=RESULT,synthetic=True,operation_id=header['operation_id'],header_id=header['header_id'],
        request_id=header['request_id'],replay_document_id=_fp(replay),replay_status=replay['replay']['status'],
        evaluation_record_id=record['record_id'],evaluation_id=e['evaluation_id'],evaluation_status=e['status'],
        outcome=OUTCOMES[e['status']],reasons=deepcopy(e['reasons']),summary=_summary(e),ranking=None,selected_strategy=None,
        primary_pressure_id=None,**{k:False for k in FLAGS})
    v['result_id']=_fp(v);return v


def _validate_result(value,header,replay,record):
    _signed(value,'result_id')
    _require(value==_result(header,replay,record),'SAVED_RESULT_STAGE_OR_SUMMARY_CONFLICT')


def _receipt(mode,identity):
    return dict(schema='capital-evaluated-replay-receipt/0.1',mode=mode,operation_id=identity,
        workflow_status='PENDING',failed_stage=None,reasons=[],keys=None,
        storage={s:'NOT_PERFORMED' if mode=='RUN' else 'MISSING' for s in STAGES},
        observed=dict(replay_status=None,evaluation_status=None),operation=None,evaluation=None,
        ranking=None,selected_strategy=None,primary_pressure_id=None,**{k:False for k in FLAGS})


def run_evaluated_replay(root,identity,request):
    receipt=_receipt('RUN',identity)
    try:
        keys=_keys(identity);receipt['keys']=keys;_request(request);store=Journal(root)
        existing=[s for s in STAGES if store.path(keys[s]).exists() or store.path(keys[s]).is_symlink()]
        if existing:
            receipt.update(workflow_status='OPERATION_EXISTS_READ_REQUIRED',existing_stages=existing,
                reasons=['EXISTING_FILES_PRESERVED_USE_EXPLICIT_READ'])
            if 'request' in existing:
                old=store.read(keys['request'])['value'];_read_header(old,identity,keys)
                if old['request_id']!=_fp(request):receipt.update(workflow_status='OPERATION_ID_CONFLICT',reasons=['DIFFERENT_REQUEST_SAME_ID'])
            return receipt
        header=_header(identity,request,keys);values={}
        for stage in STAGES:
            receipt['failed_stage']=stage
            if stage=='request':value=header
            elif stage=='replay':value=_replay(request['replay_input'])
            elif stage=='evaluation':
                value=_evaluation_record(header,request,values['replay'],_evaluate(_evaluation_input(request,values['replay'])))
            else:value=_result(header,values['replay'],values['evaluation'])
            status,saved,errors=_persist(store,keys[stage],value);receipt['storage'][stage]=status
            if status!='SAVED_AND_READ_BACK':
                receipt.update(workflow_status='STOPPED_STORAGE',reasons=errors);return receipt
            values[stage]=saved
            if stage=='replay':
                _validate_replay(request,saved);receipt['observed']['replay_status']=saved['replay']['status']
            elif stage=='evaluation':
                _validate_evaluation(saved,header,request,values['replay']);receipt['observed']['evaluation_status']=saved['evaluation']['status']
            elif stage=='result':_validate_result(saved,header,values['replay'],values['evaluation'])
        receipt.update(workflow_status=values['result']['outcome'],operation=values['result'],
            evaluation=values['evaluation']['evaluation'],reasons=values['result']['reasons'],failed_stage=None)
    except (OSError,ValueError,KeyError,TypeError,AttributeError,IndexError) as exc:
        receipt.update(workflow_status='INPUT_REFUSED' if receipt['storage']['request']=='NOT_PERFORMED' else 'STOPPED_VALIDATION',reasons=[str(exc)])
    return receipt


def read_evaluated_replay(root,identity):
    receipt=_receipt('READ',identity)
    try:
        keys=_keys(identity);receipt['keys']=keys;store=Journal(root);values={}
        for stage in STAGES:
            receipt['failed_stage']=stage
            try:values[stage]=store.read(keys[stage])['value'];receipt['storage'][stage]='READ_ONLY'
            except FileNotFoundError:values[stage]=None
        header=values['request'];_require(header is not None,'SAVED_REQUEST_MISSING_NO_RECONSTRUCTION')
        request=_read_header(header,identity,keys);replay=values['replay'];record=values['evaluation'];value=values['result']
        if replay is not None:_validate_replay(request,replay);receipt['observed']['replay_status']=replay['replay']['status']
        if record is not None:
            _require(replay is not None,'SAVED_REPLAY_MISSING');_validate_evaluation(record,header,request,replay)
            receipt['observed']['evaluation_status']=record['evaluation']['status']
        if value is None:
            receipt.update(workflow_status='INCOMPLETE_SAVED_PREFIX',failed_stage=None,reasons=['NO_FINAL_RESULT_NO_AUTOMATIC_RESUME'])
        else:
            _require(replay is not None and record is not None,'SAVED_STAGE_MISSING')
            _validate_result(value,header,replay,record)
            receipt.update(workflow_status='READ_ONLY',operation=value,evaluation=record['evaluation'],failed_stage=None,reasons=[])
    except (OSError,ValueError,KeyError,TypeError,AttributeError,IndexError) as exc:
        receipt.update(workflow_status='UNREADABLE',reasons=[str(exc)])
    return receipt


def render_text(receipt):
    lines=['明示合成回放與另存評估（非市場績效）','操作狀態：'+receipt['workflow_status'],
        '分開保存：'+json.dumps(receipt['storage'],ensure_ascii=False),
        '回放狀態：'+str(receipt['observed']['replay_status'])+'；評估狀態：'+str(receipt['observed']['evaluation_status'])]
    if receipt['operation']:
        v=receipt['operation'];lines.append('保存結果：'+v['outcome'])
        if v['evaluation_status']=='EVALUATED':
            s=v['summary'];m=s['statistics']
            lines+=['原始資本：'+s['initial_capital']+'；期末應計淨值：'+s['terminal_accrual_equity'],
                '期間應計成長：'+m['period_accrual_growth']+'；最大回撤：'+m['maximum_drawdown'],
                '截至終點仍未恢復：'+str(m['recovery_censored']),
                '原帳期末假想退出後成長：'+s['terminal_net_growth']+'（非已清倉）']
        else:lines.append('拒算：統計保持null，不把停止前帳戶當完成結果。')
    if receipt['reasons']:lines.append('理由：'+json.dumps(receipt['reasons'],ensure_ascii=False))
    lines+=['READ只讀已保存評估，不重播、不重算或補行情。','不排名；全部正式資格false、主壓力null。']
    return '\n'.join(lines)+'\n'
