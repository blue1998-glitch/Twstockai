"""Pure projection of saved batch/order histories. Standard library only.

No producer import, ledger reconstruction, source authentication or new approval.
"""
from copy import deepcopy
from datetime import datetime, date
import hashlib
import json

SCHEMA='capital-batch-lifecycle/0.1'
FLAGS=('data_qualified','execution_model_qualified','historical_signal_eligible',
       'policy_authorized','live_execution_authorized')
LIVE={'WAITING','WAITING_REASSESSMENT','WAITING_SETTLED_CASH','OPEN','PARTIAL','RISK_BLOCKED'}
CANCELLED={'CANCELLED_EVIDENCE','CANCELLED_REASSESSMENT','CANCELLED_AT_REVIEW'}
TERMINAL=CANCELLED|{'EXPIRED_UNFILLED','FILLED'}


def _fp(value):
    raw=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    return 'sha256:'+hashlib.sha256(raw.encode()).hexdigest()


def _require(condition,reason):
    if not condition:raise ValueError(reason)


def _integer(value):
    _require(isinstance(value,str) and value.isascii() and value.isdigit(),'EXPLICIT_WHOLE_SHARE_STRING_REQUIRED')
    return int(value)


def _time(value):
    t=datetime.fromisoformat(value.replace('Z','+00:00'))
    _require(t.utcoffset() is not None,'EXPLICIT_TIMEZONE_REQUIRED')
    return t


def _signed(value,key):
    _require(value[key]==_fp({k:v for k,v in value.items() if k!=key}),key.upper()+'_FINGERPRINT_CONFLICT')


def _snapshot(e,cp,pointer):
    _require(e['schema'] in ('capital-execution/0.8','capital-execution/0.9') and e['status']=='SYNTHETIC_EXECUTION_REPLAY','UNSUPPORTED_SAVED_EXECUTION')
    _require(all(e[k] is False for k in FLAGS),'SOURCE_QUALIFICATION_NOT_RESEARCH_ONLY')
    _require(e['result_id']==_fp({k:v for k,v in e.items() if k!='result_id'}),'EXECUTION_FINGERPRINT_CONFLICT')
    expected_cp='capital-account-checkpoint/0.8' if e['schema']=='capital-execution/0.9' else 'capital-account-checkpoint/0.7'
    _require(cp['schema']==expected_cp,'UNSUPPORTED_SAVED_CHECKPOINT')
    s=cp['state'];_require(cp['state_id']==_fp(s),'CHECKPOINT_STATE_FINGERPRINT_CONFLICT')
    _require(cp['checkpoint_id']==_fp(dict(schema=cp['schema'],state_id=cp['state_id'])),'CHECKPOINT_ID_CONFLICT')
    _require(s['through_at']==e['observed_until'] and s['ledger_close']['as_of']==s['through_at'],'SAVED_WATERMARK_CONFLICT')
    _require(_time(s['ledger_close']['available_at'])>=_time(s['through_at']),'SAVED_CLOSE_AVAILABILITY_CONFLICT')
    for a,b in [('accepted_fills','fills'),('order_states','order_states'),('latest_decision_id','latest_decision_id'),
                ('latest_common_account_id','latest_common_account_id'),('reviewed_evidence_tokens','reviewed_evidence_tokens')]:
        _require(s[a]==e[b],'CHECKPOINT_EXECUTION_CONFLICT:'+a)
    row=e['ledger']['daily'][-1]
    _require(s['row']==row and row['date']==s['through_at'][:10],'CHECKPOINT_LEDGER_ROW_CONFLICT')
    for key in ('settled_cash','available_cash_strict','cash_receivable','purchase_payable','shares','cash_claims','share_receivables'):
        _require(row[key] is not None,'UNKNOWN_REQUIRED_ACCOUNT_FIELD:'+key)
    orders={o['id']:o for o in e['order_history']};fills={f['id']:f for f in e['fills']}
    _require(len(orders)==len(e['order_history']) and set(orders)==set(e['order_states']),'ORDER_HISTORY_CONFLICT')
    _require(len(fills)==len(e['fills']) and set(fills)==set(e['fill_order_ids']),'FILL_IDENTITY_CONFLICT')
    ids=e['decision_ids'];records=e['decision_records']
    _require(len(ids)==len(set(ids)) and set(ids)==set(records) and ids[-1]==e['latest_decision_id'],'DECISION_HISTORY_CONFLICT')
    for key,d in records.items():
        _signed(d,'decision_id');_require(key==d['decision_id'] and d['schema'] in ('capital-decision/0.8','capital-decision/0.9'),'DECISION_ID_CONFLICT')
        _read_scope(d,e)
    _require(records[e['latest_decision_id']]['common_account_id']==e['latest_common_account_id'],'LATEST_ACCOUNT_CONFLICT')
    _require(s['general_reserved_cash']==records[e['latest_decision_id']]['reserved_cash'],'GENERAL_RESERVE_CONFLICT')
    attempts=e['reassessment_attempts'];_require(len({a['id'] for a in attempts})==len(attempts),'REVIEW_ID_COLLISION')
    scoped=any(d['schema']=='capital-decision/0.9' for d in list(records.values())+[a['decision'] for a in attempts])
    _require((e['schema']=='capital-execution/0.9')==scoped,'SAVED_SCOPE_EXECUTION_VERSION_CONFLICT')
    for a in attempts:
        _require(a['schema']=='capital-reassessment-attempt/0.2','UNSUPPORTED_REVIEW_ATTEMPT')
        _signed(a,'attempt_id');_signed(a['decision'],'decision_id');_read_scope(a['decision'],e)
        _require(a['request_content_id']==_fp(a['request']),'REVIEW_REQUEST_CONTENT_CONFLICT')
        _require(a['order_id'] in orders and a['outcome'] in ('ACCEPTED','REJECTED'),'REVIEW_ORDER_OR_OUTCOME_CONFLICT')
        _require(_time(a['decision']['decision_at'])<=_time(a['observed_at'])<=_time(s['through_at']),'REVIEW_OUTSIDE_WATERMARK')
    tokens=set().union(*(set(d['reviewed_evidence_tokens']) for d in list(records.values())+[a['decision'] for a in attempts]))
    _require(tokens==set(e['reviewed_evidence_tokens']),'REVIEWED_TOKEN_HISTORY_CONFLICT')
    for f in fills.values():
        o=orders[e['fill_order_ids'][f['id']]]
        _require(all(f[k]==o[k] for k in ('code','side')),'FILL_ORDER_BINDING_CONFLICT')
        _require(_integer(f['shares'])>0 and f['date']<=row['date'],'FILL_QUANTITY_OR_WATERMARK_CONFLICT')
        date.fromisoformat(f['settlement_date'])
    for key,o in orders.items():
        st=e['order_states'][key];n=sum(_integer(f['shares']) for f in fills.values() if e['fill_order_ids'][f['id']]==key)
        _require(st['status'] in LIVE|TERMINAL,'UNKNOWN_SAVED_ORDER_STATUS')
        _require(_integer(o['shares'])==n+_integer(st['remaining']),'ORDER_QUANTITY_CONFLICT')
        _require(st['active_decision_id'] in records,'ACTIVE_DECISION_NOT_SAVED')
        _require(st['status']!='FILLED' or _integer(st['remaining'])==0,'FILLED_WITH_UNFILLED_QUANTITY')
        _require(st['status'] not in TERMINAL or st['reserved_cash']=='0','CLOSED_ORDER_RESERVATION_CONFLICT')
    _require(all(j['date']<=row['date'] for j in e['ledger']['journal']),'FUTURE_JOURNAL_IN_SNAPSHOT')
    return dict(execution=e,checkpoint=cp,pointer=pointer)


def _read_scope(d,e):
    """Only saved structural links. Never import the numerical scope validator."""
    if d['schema']=='capital-decision/0.8':
        _require('same_order_continuation' not in d,'UNEXPECTED_SCOPE_IN_LEGACY_DECISION');return
    _require(d['schema']=='capital-decision/0.9','UNSUPPORTED_SAVED_DECISION')
    s=d['same_order_continuation'];_require(s['schema']=='capital-same-order-scope/0.1','UNSUPPORTED_ORDER_SCOPE')
    _require(s['use']=='SAME_ORIGINAL_ORDER_ONLY_NOT_NEW_BATCH','UNSUPPORTED_ORDER_SCOPE_USE')
    _signed(s,'scope_id')
    order=next((o for o in e['order_history'] if o['id']==s['order_id']),None)
    _require(order is not None,'SAVED_ORDER_SCOPE_ORDER_MISSING')
    _require(_fp(order)==s['order_fingerprint'] and s['account_id']==d['common_account_id'] and
        s['checkpoint_id']==d['continuity']['checkpoint_id'] and s['latest_predecessor_id']==d['continuity']['latest_predecessor_id'],
        'SAVED_ORDER_SCOPE_BINDING_CONFLICT')
    original=e['decision_records'][s['original_decision_id']]
    p=next((p for p in original['layer3']['alternatives'] if p['id']==s['plan_id']),None)
    _require(p is not None and original['decision_at']==order['decision_at'] and p['family']=='C' and p['trigger_ids']==s['trigger_ids'],
        'SAVED_ORDER_SCOPE_ORIGINAL_CONFLICT')


def _collect(saved):
    snapshots=[];approvals={}
    if 'review' in saved and saved['review']['schema'] in ('capital-conditional-quantity-review/0.1','capital-conditional-quantity-review/0.2','capital-conditional-quantity-review/0.3'):
        r=saved['review'];kind='conditional';status=r['status']
        _require(status in {'REPLAYED_ACCEPTED_REVIEW','REPLAYED_REJECTED_REVIEW','STOPPED_ORIGINAL_GATE',
            'STOPPED_INPUT_ERROR','STOPPED_NOT_IMPLEMENTED','STOPPED_EXECUTION_REFUSAL','REPLAYED_RETRY_NOT_ACTIVATED'},'UNSUPPORTED_SAVED_STATUS')
        for key,ck in [('prefix_execution','prefix_checkpoint'),('execution','checkpoint')]:
            if r[key] is not None and r[ck] is not None:
                snapshots.append(_snapshot(r[key],r[ck],'/review/'+key))
        a=r['original_approval']
        if a is not None:
            approvals[a['original_decision_id']]=dict(plan=deepcopy(a['original_plan']),classification=a['classification'],
                pointer='/review/original_approval',original_order=deepcopy(a['order']))
        complete=status.startswith('REPLAYED_')
    elif 'replay' in saved and saved['replay']['schema']=='capital-quantity-replay/0.1':
        r=saved['replay'];kind='quantity';status=r['status']
        _require(status in {'COMPLETED_PROVIDED_ROUNDS','REFUSED_ROUND_LIMIT','STOPPED_CANDIDATE_GATE',
            'STOPPED_NOT_IMPLEMENTED','STOPPED_INPUT_ERROR','STOPPED_EXECUTION_REFUSAL'},'UNSUPPORTED_SAVED_STATUS')
        for i,frame in enumerate(r['rounds']):
            e=frame['execution'];cp=frame['checkpoint']
            if e is None or cp is None:continue
            p=frame['selected_candidate']
            _require(p['feasible_for_research'] is True and p['classification'] in ('CURRENTLY_FEASIBLE','WAIT_SETTLEMENT_REASSESSMENT'),'ORIGINAL_APPROVAL_NOT_FEASIBLE')
            _require(p['core_decision_id']==e['decision_id'],'ORIGINAL_APPROVAL_DECISION_CONFLICT')
            snapshots.append(_snapshot(e,cp,'/replay/rounds/'+str(i)+'/execution'))
            if p['plan'] is not None:
                approvals[e['decision_id']]=dict(plan=deepcopy(p['plan']),classification=p['classification'],
                    pointer='/replay/rounds/'+str(i)+'/selected_candidate',original_order=None)
        if snapshots:_require(r['last_execution']==snapshots[-1]['execution'],'LAST_EXECUTION_CONFLICT')
        complete=status=='COMPLETED_PROVIDED_ROUNDS'
    else:raise ValueError('UNSUPPORTED_SAVED_SCHEMA')
    _require(r['synthetic'] is True and all(r[k] is False for k in FLAGS),'SOURCE_QUALIFICATION_NOT_RESEARCH_ONLY')
    return snapshots,approvals,dict(kind=kind,schema=r['schema'],status=status,saved_reasons=deepcopy(r['reasons']),
        view='LATEST_SAVED_SNAPSHOT' if complete else 'HISTORICAL_BEFORE_STOP')


def _chain(snapshots):
    for old,new in zip(snapshots,snapshots[1:]):
        p=old['execution'];n=new['execution']
        _require(_time(p['observed_until'])<=_time(n['observed_until']),'SNAPSHOT_TIME_REVERSED')
        _require(p['origin_ledger_input_id']==n['origin_ledger_input_id'] and p['origin_common_account_id']==n['origin_common_account_id'],'ORIGIN_ACCOUNT_CHANGED')
        for field in ('fills','order_history','reassessment_attempts'):
            _require(n[field][:len(p[field])]==p[field],'SNAPSHOT_HISTORY_CHANGED:'+field)
        _require(all(n['decision_records'].get(k)==v for k,v in p['decision_records'].items()),'SAVED_DECISION_CHANGED')
        _require(set(p['reviewed_evidence_tokens'])<=set(n['reviewed_evidence_tokens']),'TOKEN_HISTORY_DROPPED')
        for k,st in p['order_states'].items():
            _require(st['status'] not in TERMINAL or n['order_states'][k]==st,'CLOSED_ORDER_REVIVED_OR_CHANGED')
        _require(old['checkpoint']['state']['origin_initial_capital']==new['checkpoint']['state']['origin_initial_capital'],'ORIGIN_CAPITAL_CHANGED')


def _account(snapshot):
    cp=snapshot['checkpoint'];s=cp['state'];e=snapshot['execution'];row=s['row']
    return dict(as_of=s['through_at'],available_at=s['ledger_close']['available_at'],ledger_close=deepcopy(s['ledger_close']),
        saved_row=deepcopy(row),general_reserved_cash=s['general_reserved_cash'],
        origin_initial_capital=s['origin_initial_capital'],external_flow=s['external_flow'],
        opening_unavailable_shares=deepcopy(s['opening_unavailable_shares']),
        origin_ledger_input_id=e['origin_ledger_input_id'],origin_common_account_id=e['origin_common_account_id'],
        latest_decision_id=e['latest_decision_id'],latest_common_account_id=e['latest_common_account_id'],
        reviewed_evidence_tokens=deepcopy(e['reviewed_evidence_tokens']),
        source_pointer=snapshot['pointer']+'/ledger/daily/'+str(len(e['ledger']['daily'])-1))


def _settlement(fill,e,pointer):
    match=[]
    for i,j in enumerate(e['ledger']['journal']):
        if (fill['side']=='BUY' and j['type']=='PURCHASE_SETTLED' and j.get('fill_id')==fill['id'] or
            fill['side']=='SELL' and j['type']=='CASH_RECEIVED' and j.get('kind')=='SALE' and j.get('claim_id')==fill['id']):
            match.append(dict(record=deepcopy(j),source_pointer=pointer+'/ledger/journal/'+str(i)))
    _require(len(match)<=1,'DUPLICATE_SETTLEMENT_RECORD')
    if match:
        _require(match[0]['record']['date']==fill['settlement_date'],'SETTLEMENT_DATE_CONFLICT')
        status='SETTLED_SAVED_JOURNAL'
    elif fill['settlement_date']>e['ledger']['daily'][-1]['date']:status='PENDING_SAVED_SCHEDULE'
    else:status='UNKNOWN_MISSING_SETTLEMENT_PROOF'
    return dict(status=status,records=match,pending_amount=None,
        pending_amount_reason='NOT_RECONSTRUCTED_FROM_PRICE_OR_ACCOUNT_AGGREGATE')


def summarize_saved(saved):
    """Read saved facts only. Failure never falls back to a numerical producer."""
    out=dict(schema=SCHEMA,status='UNREADABLE',reasons=[],source=None,account=None,snapshots=[],approvals=[],orders=[],
        validation_scope='SAVED_STRUCTURAL_LINKS_NOT_LEDGER_REPLAY_OR_SOURCE_AUTHENTICATION',
        data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,
        policy_authorized=False,live_execution_authorized=False,primary_pressure_id=None)
    try:
        snapshots,approvals,source=_collect(saved);source['document_id']=_fp(saved);out['source']=source
        if not snapshots:
            out.update(status='NO_SAVED_EXECUTION',reasons=['NO_EXECUTION_AND_CHECKPOINT_PAIR']);return out
        _chain(snapshots);last=snapshots[-1];e=last['execution'];pointer=last['pointer']
        out['account']=_account(last);out['snapshots']=[_account(s) for s in snapshots]
        events=[];seen=set()
        for s in snapshots:
            for i,event in enumerate(s['execution']['execution_events']):
                token=_fp(event)
                if token not in seen:events.append(dict(record=deepcopy(event),source_pointer=s['pointer']+'/execution_events/'+str(i)));seen.add(token)
        for key,a in approvals.items():
            _require(key in e['decision_records'],'APPROVAL_DECISION_NOT_SAVED')
            d=e['decision_records'][key];p=next((p for p in d['layer3']['alternatives'] if p['id']==a['plan']['id']),None)
            _require(p is not None and p['feasible'] is True and p['targets']==a['plan']['targets'],'APPROVAL_PLAN_CONFLICT')
            if a['original_order'] is not None:
                _require(a['original_order'] in e['order_history'] and a['original_order']['decision_at']==d['decision_at'],'APPROVAL_ORDER_CONFLICT')
            out['approvals'].append(dict(origin_decision_id=key,candidate_id=a['plan']['id'],
                classification=a['classification'],saved_plan=a['plan'],source_pointer=a['pointer'],
                shared_order_ids=[o['id'] for o in e['order_history'] if o['decision_at']==d['decision_at']],
                budget_scope='ONE_SHARED_RESEARCH_PROPOSAL_NOT_REUSABLE_PER_ORDER'))
        for i,o in enumerate(e['order_history']):
            key=o['id'];st=e['order_states'][key];origin=[d for d in e['decision_records'].values() if d['decision_at']==o['decision_at']]
            _require(len(origin)==1,'ORIGIN_ORDER_DECISION_AMBIGUOUS')
            origin=origin[0];approved=origin['decision_id'] in approvals
            fills=[]
            for j,f in enumerate(e['fills']):
                if e['fill_order_ids'][f['id']]!=key:continue
                fills.append(dict(record=deepcopy(f),source_pointer=pointer+'/fills/'+str(j),settlement=_settlement(f,e,pointer)))
            filled=sum(_integer(f['record']['shares']) for f in fills);remaining=_integer(st['remaining'])
            by_settlement={k:sum(_integer(f['record']['shares']) for f in fills if f['settlement']['status']==k)
                for k in ('SETTLED_SAVED_JOURNAL','PENDING_SAVED_SCHEDULE','UNKNOWN_MISSING_SETTLEMENT_PROOF')}
            reviews=[]
            for j,a in enumerate(e['reassessment_attempts']):
                if a['order_id']!=key:continue
                d=a['decision'];p=next((p for p in d['layer3']['alternatives'] if p['id']==a['plan_id']),None)
                reviews.append(dict(id=a['id'],decision_at=d['decision_at'],data_cutoff=d['data_cutoff'],observed_at=a['observed_at'],
                    outcome=a['outcome'],decision_id=d['decision_id'],checkpoint_id=a['checkpoint_id'],
                    request_content_id=a['request_content_id'],attempt_id=a['attempt_id'],
                    reasons=None if p is None else deepcopy(p['reasons']),
                    capital_eligibility=deepcopy(d['layer2'][o['code']]['capital_eligibility']),
                    restriction_conflicts=deepcopy(d['fact_history']['restriction_conflicts']),
                    new_evidence_tokens=deepcopy(d['new_evidence_tokens']),
                    source_pointer=pointer+'/reassessment_attempts/'+str(j)))
                if d['schema']=='capital-decision/0.9':reviews[-1]['same_order_continuation']=deepcopy(d['same_order_continuation'])
            out['orders'].append(dict(order_id=key,code=o['code'],side=o['side'],origin_decision_id=origin['decision_id'],
                original_order=deepcopy(o),approval_status='SAVED_RESEARCH_APPROVAL' if approved else 'UNKNOWN',
                approved_order_quantity=o['shares'] if approved else None,
                approval_quantity_scope='ORIGINAL_ORDER_ONLY_NOT_ENTIRE_PLAN_OR_FRESH_BUY_PERMISSION',
                original_order_quantity=o['shares'],filled_quantity=str(filled),
                live_remaining_quantity=str(remaining if st['status'] in LIVE else 0),
                cancelled_unfilled_quantity=str(remaining if st['status'] in CANCELLED else 0),
                expired_unfilled_quantity=str(remaining if st['status']=='EXPIRED_UNFILLED' else 0),
                settled_fill_quantity=str(by_settlement['SETTLED_SAVED_JOURNAL']),
                pending_settlement_quantity=str(by_settlement['PENDING_SAVED_SCHEDULE']),
                unknown_settlement_quantity=str(by_settlement['UNKNOWN_MISSING_SETTLEMENT_PROOF']),
                saved_order_state=deepcopy(st),fills=fills,reviews=reviews,
                events=[x for x in events if x['record']['order_id']==key],source_pointer=pointer+'/order_history/'+str(i)))
        out['status']='READABLE';return out
    except (ValueError,KeyError,TypeError,IndexError,AttributeError) as exc:
        reason='MISSING_SAVED_FIELD:'+str(exc) if isinstance(exc,KeyError) else str(exc)
        out.update(status='UNREADABLE',reasons=[reason],account=None,snapshots=[],approvals=[],orders=[])
        return out


def render_text(summary):
    """Small plain-text view, with shared money shown once, not allocated twice."""
    lines=['原批次生命週期（保存研究結果，只讀）','讀取狀態：'+summary['status']]
    if summary['status']!='READABLE':return '\n'.join(lines+summary['reasons'])+'\n'
    a=summary['account'];r=a['saved_row'];s=summary['source']
    lines+=['原結果狀態：'+s['status']+'；檢視：'+s['view'],
        '原結果理由：'+json.dumps(s['saved_reasons'],ensure_ascii=False),
        '帳戶截止：'+a['as_of']+'；帳務可得：'+a['available_at'],
        '全帳已結現金 '+r['settled_cash']+'；嚴格可用 '+r['available_cash_strict']+'；一般預留 '+a['general_reserved_cash'],
        '全帳應收 '+r['cash_receivable']+'；應付 '+r['purchase_payable']+'（不重複分配到每張單）',
        '原單 | 股票 | 方向 | 核准原單量 | 已成交 | 活單剩餘 | 已取消 | 已到期 | 待交割 | 交割未知 | 原單預留']
    for o in summary['orders']:
        lines.append(' | '.join([o['order_id'],o['code'],o['side'],o['approved_order_quantity'] or 'UNKNOWN',
            o['filled_quantity'],o['live_remaining_quantity'],o['cancelled_unfilled_quantity'],o['expired_unfilled_quantity'],
            o['pending_settlement_quantity'],o['unknown_settlement_quantity'],o['saved_order_state']['reserved_cash']]))
        for v in o['reviews']:lines.append('  重評 '+v['id']+'：'+v['outcome']+'；理由 '+json.dumps(v['reasons'],ensure_ascii=False))
    return '\n'.join(lines+['嚴格可用是原帳欄位，仍有一般及各單預留，不等於可追加金額。',
        '核准僅指原保存研究提案，不是新批次或正式交易授權。'])+'\n'
