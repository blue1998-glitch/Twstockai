"""Explicit IMPORT/READ of an existing evaluation, with no numerical producer.

Journal owns persistence. These checks bind saved fields and projections;
they do not recalculate metrics or authenticate the source/producer.
"""
from copy import deepcopy
import re
from rotation_research.store import Journal
from .lifecycle import _fp, _signed, _require, _time, FLAGS
from .research_operation import _persist, _keys as _identity_keys
from .saved_action_source import _snapshots

INPUT='capital-action-evaluation-import-input/0.1'
RECORD='capital-action-evaluation-record/0.1'
RECEIPT='capital-action-evaluation-storage-receipt/0.1'
FIELDS={'schema','synthetic','evaluation_input','evaluation','expected_evaluation_input_id','expected_evaluation_id'}
NULL_METRICS=('statistics','source','account','costs','initial_capital','terminal_accrual_equity','terminal_net_equity','terminal_net_growth')
CHECKED='SAVED_SOURCE_BINDING_CHECKED_NOT_REEVALUATED'
DECLARED='EXPLICIT_REFUSAL_ASSOCIATION_NOT_REEVALUATED'


def _decimal_text(v):
    return isinstance(v,str) and re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?',v) is not None


def _validate_input(request):
    _require(isinstance(request,dict) and set(request)==FIELDS and request['schema']==INPUT and request['synthetic'] is True,
        'EXACT_EXPLICIT_ACTION_EVALUATION_IMPORT_REQUIRED')
    q=request['evaluation_input'];e=request['evaluation']
    _require(isinstance(q,dict) and set(q)=={'schema','synthetic','evaluation_at','saved_result'}
        and q['schema']=='capital-action-account-metrics-input/0.1' and q['synthetic'] is True,'FULL_EVALUATION_INPUT_REQUIRED')
    _time(q['evaluation_at']);source=q['saved_result']
    _require(isinstance(source,dict) and set(source)=={'schema','action_request','action_result','continuation'}
        and source['schema']=='capital-saved-action-source/0.1' and isinstance(source['action_request'],dict)
        and isinstance(source['action_result'],dict) and (source['continuation'] is None or
            isinstance(source['continuation'],dict) and set(source['continuation'])=={'request','result'}),'FULL_SAVED_ACTION_SOURCE_REQUIRED')
    a=source['action_request'];_require(a['schema'] in ('capital-cash-action-execution-input/0.1','capital-cash-action-execution-input/0.2')
        and a['synthetic'] is True and a['action_input']['synthetic'] is True,'EXPLICIT_SYNTHETIC_SOURCE_REQUIRED')
    sources=a['execution_spec']['origin_ledger']['sources']
    _require(bool(sources) and all(v['kind']=='ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET' for v in sources.values()),'NON_SYNTHETIC_IMPORT_SOURCE')
    _require(request['expected_evaluation_input_id']==_fp(q),'EXPECTED_EVALUATION_INPUT_ID_CONFLICT')
    _require(isinstance(e,dict) and e['schema']=='capital-action-account-metrics/0.1','SUPPORTED_SAVED_ACTION_EVALUATION_REQUIRED')
    _signed(e,'evaluation_id')
    _require(request['expected_evaluation_id']==e['evaluation_id'],'EXPECTED_EVALUATION_ID_CONFLICT')
    _require(e['synthetic'] is True and all(e[k] is False for k in FLAGS) and e['primary_pressure_id'] is None
        and e['ranking'] is None and e['selected_strategy'] is None and e['strategy_validated'] is False,'EVALUATION_NOT_RESEARCH_ONLY')
    _require(e['valuation_basis']=='SAVED_NET_ACCRUAL_AFTER_RECORDED_COSTS_BEFORE_HYPOTHETICAL_EXIT' and
        e['validation_scope']=='SAVED_ACTION_BINDINGS_AND_CURVE_CHECKS_NOT_REPLAY_OR_SOURCE_AUTHENTICATION','UNSUPPORTED_EVALUATION_SCOPE')
    _require(e['status'] in ('EVALUATED','REFUSED'),'SUPPORTED_SAVED_EVALUATION_STATUS_REQUIRED')
    if e['status']=='REFUSED':
        _require(isinstance(e['reasons'],list) and bool(e['reasons']) and all(e[k] is None for k in NULL_METRICS),
            'REFUSED_EVALUATION_MUST_NOT_HAVE_METRICS')
        return DECLARED
    _require(e['reasons']==[],'EVALUATED_RESULT_HAS_REFUSALS')
    frames,summary=_snapshots(source);last,cp=frames[-1];ledger=last['ledger'];s=cp['state']
    _require(ledger['status']=='QUALIFIED_ACCOUNTING_SCENARIO_NOT_STRATEGY_VALIDATION' and ledger['refusal_reasons']==[]
        and ledger['quote_gaps']==[],'COMPLETE_SAVED_LEDGER_REQUIRED')
    expected=dict(document_id=_fp(source),execution_result_id=last['result_id'],ledger_input_id=ledger['input_id'],
        origin_ledger_input_id=last['origin_ledger_input_id'],checkpoint_id=cp['checkpoint_id'],source_schema=summary['source']['schema'],
        start=ledger['start'],end=ledger['end'],evaluation_at=q['evaluation_at'],ledger_available_at=summary['account']['available_at'],
        snapshot_count=len(frames),rows_used_once=len(ledger['daily']))
    _require(e['source']==expected,'IMPORTED_METRICS_SOURCE_CONFLICT')
    _require(_time(last['observed_until'])<=_time(q['evaluation_at']) and _time(summary['account']['available_at'])<=_time(q['evaluation_at']),
        'IMPORTED_EVALUATION_BEFORE_CLOSE_AVAILABLE')
    _require(e['account']==summary['account'],'IMPORTED_METRICS_ACCOUNT_CONFLICT')
    _require(e['initial_capital']==s['origin_initial_capital'] and e['terminal_accrual_equity']==ledger['daily'][-1]['net_accrual_equity']
        and e['terminal_net_equity']==ledger['end_net_equity'] and e['terminal_net_growth']==ledger['scenario_net_return'],
        'IMPORTED_TERMINAL_VALUES_CONFLICT')
    _require(e['costs']==dict(recorded_fill_fee_tax=ledger['fees_and_tax_on_fills'],terminal_estimated_exit_cost=ledger['terminal_estimated_exit_cost'],
        cost_treatment='ALREADY_RECORDED_FEES_NOT_DEDUCTED_AGAIN_TERMINAL_EXIT_SEPARATE'),'IMPORTED_COST_VALUES_CONFLICT')
    stats=e['statistics'];_require(isinstance(stats,dict) and set(stats)=={'period_accrual_growth','maximum_drawdown','maximum_drawdown_episode',
        'maximum_drawdown_duration_calendar_days','recovery_censored','ongoing_underwater_calendar_days','episodes','curve'},'SAVED_STATISTICS_SHAPE_REQUIRED')
    _require(_decimal_text(stats['period_accrual_growth']) and _decimal_text(stats['maximum_drawdown']) and isinstance(stats['episodes'],list)
        and type(stats['recovery_censored']) is bool and (stats['maximum_drawdown_episode'] is None or isinstance(stats['maximum_drawdown_episode'],dict))
        and all(type(stats[k]) is int and stats[k]>=0 for k in ('maximum_drawdown_duration_calendar_days','ongoing_underwater_calendar_days')),
        'SAVED_STATISTICS_TYPES_REQUIRED')
    curve=stats['curve'];_require(isinstance(curve,list) and len(curve)==len(ledger['daily']),'SAVED_CURVE_LENGTH_CONFLICT')
    for i,(row,original) in enumerate(zip(curve,ledger['daily'])):
        _require(set(row)=={'date','equity','running_peak','drawdown','source_index'} and row['date']==original['date']
            and row['equity']==original['net_accrual_equity'] and type(row['source_index']) is int and row['source_index']==i
            and all(_decimal_text(row[k]) for k in ('equity','running_peak','drawdown')),'SAVED_CURVE_SOURCE_CONFLICT')
    return CHECKED


def _record(identity,request):
    _identity_keys(identity)
    scope=_validate_input(request);q=request['evaluation_input'];e=request['evaluation']
    value=dict(schema=RECORD,synthetic=True,operation_id=identity,import_input=deepcopy(request),import_input_id=_fp(request),
        evaluation_input_id=_fp(q),source_document_id=_fp(q['saved_result']),evaluation_id=e['evaluation_id'],
        evaluation_at=q['evaluation_at'],evaluation_status=e['status'],association_scope=scope)
    value['record_id']=_fp(value)
    return value


def validate_record(value,identity):
    _require(isinstance(value,dict) and value['schema']==RECORD,'SUPPORTED_ACTION_EVALUATION_RECORD_REQUIRED')
    _signed(value,'record_id')
    _require(value==_record(identity,value['import_input']),'SAVED_IMPORT_RECORD_BINDING_CONFLICT')
    return value


def _receipt(mode,identity):
    return dict(schema=RECEIPT,mode=mode,operation_id=identity,storage_status='NOT_SAVED' if mode=='IMPORT' else 'UNREADABLE',
        evaluation_status=None,association_scope=None,record=None,reasons=[],saved_files_preserved=True,
        validation_scope='SAVED_BINDINGS_NOT_REEVALUATED_OR_AUTHENTICATED',primary_pressure_id=None,**{k:False for k in FLAGS})


def import_evaluation(root,identity,request):
    """Import an explicitly pinned existing evaluation; never calculate one."""
    out=_receipt('IMPORT',identity)
    try:value=_record(identity,request)
    except (ValueError,KeyError,TypeError,AttributeError,IndexError,OverflowError) as exc:
        out['reasons']=[str(exc)];return out
    status,saved,errors=_persist(Journal(root),identity,value)
    out.update(storage_status=status,reasons=errors)
    if status=='SAVED_AND_READ_BACK':
        try:validate_record(saved,identity)
        except (ValueError,KeyError,TypeError,AttributeError,IndexError) as exc:
            out.update(storage_status='UNKNOWN',reasons=[str(exc)]);return out
        out.update(record=saved,evaluation_status=saved['evaluation_status'],association_scope=saved['association_scope'])
    return out


def read_evaluation(root,identity):
    """No source input, evaluation, write, recovery or automatic reconstruction."""
    out=_receipt('READ',identity)
    try:
        _identity_keys(identity);value=Journal(root).read(identity)['value'];validate_record(value,identity)
        out.update(storage_status='READ_ONLY',evaluation_status=value['evaluation_status'],association_scope=value['association_scope'],record=value)
    except FileNotFoundError:out.update(storage_status='NOT_FOUND',reasons=['SAVED_RECORD_MISSING_NO_RECONSTRUCTION'])
    except (OSError,ValueError,KeyError,TypeError,AttributeError,IndexError) as exc:out['reasons']=[str(exc)]
    return out
