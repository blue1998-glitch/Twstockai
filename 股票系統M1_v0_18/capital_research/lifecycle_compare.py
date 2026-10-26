"""Read-only common-condition gate for saved lifecycle projections."""
from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation

from .lifecycle import summarize_saved, _fp, _time

INPUT='capital-lifecycle-comparison-input/0.1'
SCHEMA='capital-lifecycle-comparison/0.1'
MAX_ITEMS=8
DIAGNOSTIC_LIMIT=64
MODELS=('cost_model','execution_model','risk_limits','scenario_set')


class ComparisonError(ValueError):
    def __init__(self,reason,path):
        super().__init__(reason);self.path=path


def _require(condition,reason,path):
    if not condition:raise ComparisonError(reason,path)


def _jobs(saved):
    if 'review' in saved:
        r=saved['review'];j=r['execution_job']
        _require('continuation' not in j,'CONDITIONAL_PREDECESSOR_MARKET_NOT_SAVED','/review/execution_job/continuation')
        return [(j,r['execution'],'/review/execution_job')]
    jobs=[]
    for i,r in enumerate(saved['replay']['rounds']):
        _require(r['execution_job'] is not None and r['execution'] is not None,'MISSING_COMPARISON_PROVENANCE','/replay/rounds/'+str(i))
        jobs.append((r['execution_job'],r['execution'],'/replay/rounds/'+str(i)+'/execution_job'))
    return jobs


def _prepare(saved):
    summary=summarize_saved(saved)
    _require(summary['status']=='READABLE' and summary['source']['view']=='LATEST_SAVED_SNAPSHOT',
        'HISTORICAL_OR_UNREADABLE_RESULT','/saved_result')
    jobs=_jobs(saved);first=jobs[0][0];origin=first['ledger_input']
    initial=jobs[0][1]['decision_records'][jobs[0][1]['decision_id']]
    start=initial['data_cutoff'][:10];until=summary['account']['as_of'];end=until[:10]
    _require(origin['start']==start and origin['end']>=end,'ORIGIN_WINDOW_CONFLICT','/ledger_input')
    _require(first['decision_input']['account']['as_of']==initial['data_cutoff'],'JOB_DECISION_CONTEXT_CONFLICT','/decision_input/account/as_of')
    previous=None;tape=[];prior_at=None
    for j,e,path in jobs:
        _require(j['schema']=='capital-execution-input/0.1','UNSUPPORTED_JOB_SCHEMA',path+'/schema')
        _require(_fp(j['ledger_input'])==e['origin_ledger_input_id'] and j['ledger_input']==origin,
            'ORIGIN_LEDGER_FINGERPRINT_CONFLICT',path+'/ledger_input')
        d=e['decision_records'][e['decision_id']];data=j['decision_input']
        for k in ('decision_at','data_cutoff','synthetic','policy_version','parameter_source')+MODELS:
            _require(data[k]==d[k],'JOB_DECISION_CONTEXT_CONFLICT',path+'/decision_input/'+k)
        _require(_fp(data['account'])==d['common_account_id'],'JOB_ACCOUNT_FINGERPRINT_CONFLICT',path+'/decision_input/account')
        _require(j['orders']==e['orders'] and j['observed_until']==e['observed_until'],'JOB_EXECUTION_BINDING_CONFLICT',path)
        _require(j['ledger_close_proof']==e['ledger_close_proof'],'JOB_CLOSE_PROOF_CONFLICT',path+'/ledger_close_proof')
        _require(j['ledger_close_proof']==first['ledger_close_proof'],
            'COMMON_CLOSE_PROOF_CHANGED_WITHIN_RESULT',path+'/ledger_close_proof')
        if previous is None:
            _require('continuation' not in j,'INITIAL_PREDECESSOR_MARKET_NOT_SAVED',path+'/continuation')
        else:
            c=j['continuation']['checkpoint']
            _require(c['execution_result']==previous and c['state']['through_at']==data['data_cutoff'],
                'PREDECESSOR_JOB_CHAIN_CONFLICT',path+'/continuation/checkpoint')
        for record in list(e['decision_records'].values())+[a['decision'] for a in e['reassessment_attempts']]:
            for key in MODELS:
                _require(record[key]==initial[key],'COMMON_MODEL_CHANGED_WITHIN_RESULT',path+'/decisions/'+key)
        for i,row in enumerate(j['tape']):
            p=path+'/tape/'+str(i)
            for key in ('at','available_at','code','price','capacity_shares','market_state','settlement_date',
                        'source_id','basis_id','version','qualification'):
                _require(row[key] is not None,'UNKNOWN_REQUIRED_TAPE_FIELD',p+'/'+key)
            at=_time(row['at'])
            _require((prior_at is None or prior_at<at) and _time(data['decision_at'])<at<=_time(e['observed_until']),
                'DUPLICATE_OR_OUT_OF_WINDOW_TAPE',p+'/at')
            _require(_time(row['available_at'])<=at,'INVALID_SAVED_TAPE_AVAILABILITY',p+'/available_at')
            try:
                price=Decimal(row['price']);capacity=row['capacity_shares']
                valid=(price.is_finite() and price>0 and isinstance(capacity,str) and capacity.isascii() and capacity.isdigit()
                    and row['market_state'] in ('OPEN','LIMIT_UP_NO_BUY','LIMIT_DOWN_NO_SELL','HALTED')
                    and date.fromisoformat(row['settlement_date'])>=date.fromisoformat(row['at'][:10]))
            except (InvalidOperation,ValueError,TypeError):valid=False
            _require(valid,'INVALID_SAVED_TAPE_VALUE',p)
            a=origin['assets'][row['code']]
            _require(all(row[k]==a[k] for k in ('source_id','basis_id')),'TAPE_SOURCE_BASIS_CONFLICT',p)
            _require(row['version']=='synthetic-tape/0.1' and row['qualification']=='EXPLICIT_SYNTHETIC_OBSERVATION',
                'UNSUPPORTED_TAPE_QUALIFICATION',p)
            tape.append(deepcopy(row));prior_at=at
        previous=e
    _require(bool(tape),'MISSING_COMPARISON_PROVENANCE','/market/tape')
    assets={}
    for code,a in origin['assets'].items():
        assets[code]={k:deepcopy(v) for k,v in a.items() if k!='quotes'}
        assets[code]['quotes']={day:deepcopy(value) for day,value in a['quotes'].items() if start<=day<=end}
    proof=first['ledger_close_proof']
    market=dict(tape=tape,assets=assets,calendar=[deepcopy(r) for r in origin['calendar'] if start<=r['date']<=end],
        events=[deepcopy(e) for e in origin['events'] if start<=e['ex_date']<=end],
        ledger_metadata={k:deepcopy(v) for k,v in origin.items() if k not in ('opening','assets','calendar','events','fills','start','end')},
        close_proof={k:deepcopy(v) for k,v in proof.items() if k!='closes'})
    market['close_proof']['closes']={day:deepcopy(row) for day,row in proof['closes'].items() if start<=day<=end}
    identity=dict(opening=dict(account=deepcopy(first['decision_input']['account']),ledger_opening=deepcopy(origin['opening']),
            initial_capital=summary['account']['origin_initial_capital']),
        window=dict(decision_at=initial['decision_at'],data_cutoff=initial['data_cutoff'],observed_until=until,
            ledger_available_at=summary['account']['available_at']),
        environment={k:deepcopy(initial[k]) for k in MODELS+('layer1','layer2','fact_history','reviewed_evidence_tokens')},market=market)
    identity['environment']['asset_bindings']={c:{k:a[k] for k in ('source_id','basis_id','adjustment_version')}
        for c,a in first['decision_input']['assets'].items()}
    return summary,identity,dict(document_id=summary['source']['document_id'],source_schema=summary['source']['schema'],
        source_status=summary['source']['status'],origin_ledger_input_id=jobs[-1][1]['origin_ledger_input_id'],
        execution_result_id=jobs[-1][1]['result_id'],saved_job_ids=[_fp(j) for j,e,p in jobs],
        identity_ids={k:_fp(v) for k,v in identity.items()})


def _differences(left,right,path=''):
    if type(left) is not type(right):
        yield dict(path=path,left=left,right=right);return
    if isinstance(left,dict):
        for key in sorted(set(left)|set(right)):
            p=path+'/'+str(key).replace('~','~0').replace('/','~1')
            if key not in left:yield dict(path=p,left_missing=True,right=right[key])
            elif key not in right:yield dict(path=p,left=left[key],right_missing=True)
            else:yield from _differences(left[key],right[key],p)
    elif isinstance(left,list):
        for i in range(max(len(left),len(right))):
            p=path+'/'+str(i)
            if i>=len(left):yield dict(path=p,left_missing=True,right=right[i])
            elif i>=len(right):yield dict(path=p,left=left[i],right_missing=True)
            else:yield from _differences(left[i],right[i],p)
    elif left!=right:yield dict(path=path,left=left,right=right)


def compare_saved(request):
    """Equality of declared saved conditions, never a performance/strategy rank."""
    out=dict(schema=SCHEMA,status='REFUSED',comparable=False,refusals=[],differences=[],total_mismatches=0,
        diagnostic_limit=DIAGNOSTIC_LIMIT,details_truncated=False,provenance=[],common_identity_ids=None,columns=[],
        comparison_scope='SAVED_SYNTHETIC_EPISODE_AND_DECLARED_MARKET_PATH_NOT_POLICY_PERFORMANCE',
        job_to_execution_causality='NOT_REPLAYED_OR_AUTHENTICATED',ranking=None,selected_label=None,
        data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,
        policy_authorized=False,live_execution_authorized=False,primary_pressure_id=None)
    try:
        _require(set(request)=={'schema','synthetic','items'} and request['schema']==INPUT and request['synthetic'] is True,
            'EXPLICIT_SYNTHETIC_COMPARISON_REQUIRED','/request')
        items=request['items']
        _require(isinstance(items,list) and 2<=len(items)<=MAX_ITEMS,'COMPARISON_RESOURCE_LIMIT_EXCEEDED','/items')
        labels=[]
        for item in items:
            _require(set(item)=={'label','saved_result'},'EXACT_LABEL_AND_SAVED_RESULT_REQUIRED','/items')
            label=item['label']
            _require(isinstance(label,str) and label.strip() and not any(x in label for x in '\n\r|') and label not in labels,
                'UNIQUE_SINGLE_LINE_LABEL_REQUIRED','/items/label')
            labels.append(label)
        prepared=[]
        for item in items:
            try:
                summary,identity,provenance=_prepare(item['saved_result'])
                provenance['label']=item['label'];out['provenance'].append(provenance)
                prepared.append((item['label'],summary,identity))
            except (ValueError,KeyError,TypeError,IndexError,AttributeError) as exc:
                reason='MISSING_COMPARISON_PROVENANCE:'+str(exc) if isinstance(exc,KeyError) else str(exc)
                out['refusals'].append(dict(label=item['label'],reason=reason,path=getattr(exc,'path','/saved_result')))
        if out['refusals']:return out
        reference=prepared[0]
        for label,summary,identity in prepared[1:]:
            for diff in _differences(reference[2],identity):
                out['total_mismatches']+=1
                if len(out['differences'])<DIAGNOSTIC_LIMIT:
                    out['differences'].append(dict(reference_label=reference[0],label=label,**diff))
        out['details_truncated']=out['total_mismatches']>len(out['differences'])
        if out['total_mismatches']:
            out['refusals']=[dict(reason='COMMON_CONDITIONS_MISMATCH',path='/identities')];return out
        out.update(status='COMPARABLE',comparable=True,common_identity_ids=deepcopy(out['provenance'][0]['identity_ids']),
            columns=[dict(label=label,summary=summary) for label,summary,identity in prepared])
        return out
    except (ValueError,KeyError,TypeError,IndexError,AttributeError) as exc:
        out['refusals'].append(dict(reason=str(exc),path=getattr(exc,'path','/request')));return out


def render_comparison(result):
    lines=['保存生命週期並列（只讀，沒有策略排名）']
    if not result['comparable']:
        lines.append('拒絕同條件並列；未輸出比較欄。')
        lines += [r.get('label','')+'：'+r['reason']+' '+r['path'] for r in result['refusals']]
        lines += [d['label']+' 與 '+d['reference_label']+' 不同：'+d['path'] for d in result['differences']]
        if result['details_truncated']:lines.append('差異共'+str(result['total_mismatches'])+'項，文字及JSON僅列前64項。')
        return '\n'.join(lines)+'\n'
    columns=result['columns'];lines.append('共同期初帳戶、截止與保存市場條件一致；這不是來源認證或策略績效驗收。')
    lines.append('欄位 | '+' | '.join(c['label'] for c in columns))
    for name,key in [('期初原資本','origin_initial_capital'),('觀察截止','as_of')]:
        lines.append(name+' | '+' | '.join(c['summary']['account'][key] for c in columns))
    for name,key in [('已結現金','settled_cash'),('嚴格可用（仍有預留）','available_cash_strict'),('全帳應付','purchase_payable')]:
        lines.append(name+' | '+' | '.join(c['summary']['account']['saved_row'][key] for c in columns))
    lines.append('一般預留 | '+' | '.join(c['summary']['account']['general_reserved_cash'] for c in columns))
    keys=list(dict.fromkeys(o['order_id'] for c in columns for o in c['summary']['orders']))
    for key in keys:
        orders=[next((o for o in c['summary']['orders'] if o['order_id']==key),None) for c in columns]
        lines.append(key+' 股票／方向 | '+' | '.join('無此保存單' if o is None else o['code']+' '+o['side'] for o in orders))
        lines.append(key+' 核准原單量 | '+' | '.join('無此保存單' if o is None else o['approved_order_quantity'] or 'UNKNOWN' for o in orders))
        for name,field in [('已成交','filled_quantity'),('活單剩餘','live_remaining_quantity'),('取消量','cancelled_unfilled_quantity'),
                           ('到期量','expired_unfilled_quantity'),('待交割','pending_settlement_quantity'),('交割未知','unknown_settlement_quantity')]:
            lines.append(key+' '+name+' | '+' | '.join('無此保存單' if o is None else o[field] for o in orders))
        lines.append(key+' 原單預留 | '+' | '.join('無此保存單' if o is None else o['saved_order_state']['reserved_cash'] for o in orders))
        lines.append(key+' 重評 | '+' | '.join('無此保存單' if o is None else
            '；'.join(v['outcome']+' '+str(v['reasons']) for v in o['reviews']) or '無保存重評' for o in orders))
    return '\n'.join(lines+['原提案／各單仍共用原預算，嚴格可用額不是可追加金額；不選勝者。'])+'\n'
