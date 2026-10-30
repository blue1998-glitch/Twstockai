"""Pure evaluation of complete saved synthetic accounts; no accounting or execution.

Accrual equity already includes recorded costs and priced rights. Terminal
hypothetical liquidation is reported separately, exactly as the original ledger.
"""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal, Context, InvalidOperation, DivisionByZero, Overflow, ROUND_HALF_EVEN, localcontext
from .lifecycle import summarize_saved, _fp, _time, FLAGS

INPUT='capital-account-metrics-input/0.1'
SCHEMA='capital-account-metrics/0.1'
BASIS='SAVED_NET_ACCRUAL_AFTER_RECORDED_COSTS_BEFORE_HYPOTHETICAL_EXIT'
IMPLEMENTATION_REVISION='0.1.1-deterministic-decimal-context'


class MetricsError(ValueError):
    def __init__(self,reason,path=''):
        super().__init__(reason);self.path=path


def _require(condition,reason,path=''):
    if not condition:raise MetricsError(reason,path)


def _number(value,reason,path=''):
    _require(isinstance(value,str) and bool(value.strip()),reason,path)
    try:n=Decimal(value)
    except InvalidOperation:raise MetricsError(reason,path)
    _require(n.is_finite(),reason,path)
    return n


def _curve_statistics(rows):
    """Arithmetic only, no claim to ledger validity. Caller validates full source."""
    _require(isinstance(rows,list) and len(rows)>=2,'COMPLETE_NONEMPTY_PERIOD_REQUIRED')
    curve=[];episodes=[];active=None;peak=None;peak_day=None;previous=None
    for i,row in enumerate(rows):
        day=date.fromisoformat(row['date']);n=_number(row['net_accrual_equity'],'UNKNOWN_EQUITY',str(i))
        _require(n>0,'NONPOSITIVE_EQUITY',str(i))
        _require(previous is None or day==previous+timedelta(days=1),'INCOMPLETE_CALENDAR_CURVE',str(i))
        _require(day.isoformat()==row['date'],'NONCANONICAL_DATE',str(i))
        if peak is None or n>=peak:
            if active is not None:
                active.update(recovery_date=day.isoformat(),observed_through=day.isoformat(),
                    duration_calendar_days=(day-date.fromisoformat(active['peak_date'])).days,recovery_censored=False)
                episodes.append(active);active=None
            peak=n;peak_day=day.isoformat()
        else:
            if active is None:
                active=dict(peak_date=peak_day,peak_equity=str(peak),first_underwater_date=day.isoformat(),
                    trough_date=day.isoformat(),trough_equity=str(n),maximum_drawdown=str(n/peak-1),recovery_date=None)
            elif n<_number(active['trough_equity'],'UNKNOWN_EQUITY'):
                active.update(trough_date=day.isoformat(),trough_equity=str(n),maximum_drawdown=str(n/peak-1))
        curve.append(dict(date=day.isoformat(),equity=str(n),running_peak=str(peak),drawdown=str(n/peak-1),source_index=i))
        previous=day
    if active is not None:
        active.update(observed_through=previous.isoformat(),
            duration_calendar_days=(previous-date.fromisoformat(active['peak_date'])).days,recovery_censored=True)
        episodes.append(active)
    worst=min(episodes,key=lambda e:Decimal(e['maximum_drawdown'])) if episodes else None
    return dict(period_accrual_growth=str(Decimal(curve[-1]['equity'])/Decimal(curve[0]['equity'])-1),
        maximum_drawdown=worst['maximum_drawdown'] if worst else '0',
        maximum_drawdown_episode=deepcopy(worst),
        maximum_drawdown_duration_calendar_days=max((e['duration_calendar_days'] for e in episodes),default=0),
        recovery_censored=bool(episodes and episodes[-1]['recovery_censored']),
        ongoing_underwater_calendar_days=episodes[-1]['duration_calendar_days'] if episodes and episodes[-1]['recovery_censored'] else 0,
        episodes=episodes,curve=curve)


def _snapshots(saved):
    """Require every completed round; lifecycle READ remains the identity gate."""
    _require(isinstance(saved,dict) and isinstance(saved.get('replay'),dict),'UNSUPPORTED_SAVED_RESULT')
    r=saved['replay']
    _require(r.get('schema')=='capital-quantity-replay/0.1','UNSUPPORTED_SAVED_RESULT')
    _require(r.get('status')=='COMPLETED_PROVIDED_ROUNDS','INCOMPLETE_SAVED_RESULT')
    frames=r['rounds'];_require(bool(frames),'COMPLETE_NONEMPTY_PERIOD_REQUIRED')
    _require(all(f['status']=='REPLAYED_EXPLICIT_INTENT' and f['execution'] is not None and f['checkpoint'] is not None
        for f in frames),'INCOMPLETE_ROUND_HISTORY')
    summary=summarize_saved(saved)
    if summary['status']!='READABLE' or summary['source']['view']!='LATEST_SAVED_SNAPSHOT':
        error=MetricsError('SAVED_RESULT_UNREADABLE','/saved_result')
        error.guard_reasons=summary['reasons'];raise error
    _require(r['historical_checkpoint']==frames[-1]['checkpoint'],'LATEST_CHECKPOINT_CONFLICT')
    return [(f['execution'],f['checkpoint']) for f in frames],summary


def _validate_rows(ledger,origin):
    rows=ledger['daily'];start=date.fromisoformat(ledger['start']);end=date.fromisoformat(ledger['end'])
    expected=[(start+timedelta(days=i)).isoformat() for i in range((end-start).days+1)]
    _require(len(expected)>=2 and [r['date'] for r in rows]==expected,'INCOMPLETE_CALENDAR_CURVE')
    _require([r['date'] for r in origin['calendar'] if ledger['start']<=r['date']<=ledger['end']]==expected,
        'INCOMPLETE_SOURCE_CALENDAR')
    for i,row in enumerate(rows):
        path='/ledger/daily/'+str(i)
        _require(_number(row['net_accrual_equity'],'UNKNOWN_EQUITY',path)>0,'NONPOSITIVE_EQUITY',path)
        for key in ('settled_cash','available_cash_strict','cash_receivable','purchase_payable'):
            _require(_number(row[key],'UNKNOWN_ACCOUNT_VALUE',path+'/'+key)>=0,'NEGATIVE_ACCOUNT_VALUE',path+'/'+key)
        claims=row['cash_claims'];_require(isinstance(claims,list),'UNKNOWN_CASH_CLAIMS',path)
        pending=row['share_receivables'];_require(isinstance(pending,list),'UNKNOWN_SHARE_RIGHTS',path)
        _require(isinstance(row['shares'],dict) and set(row['shares'])==set(origin['assets']),'UNKNOWN_HOLDINGS',path)
        held=set()
        for code,value in row['shares'].items():
            n=_number(value,'UNKNOWN_HOLDINGS',path)
            _require(n>=0,'NEGATIVE_HOLDINGS',path+'/'+code)
            if n:held.add(code)
        for claim in claims:
            _require(_number(claim['amount'],'UNKNOWN_CASH_CLAIMS',path)>=0 and bool(claim['id']) and bool(claim['pay_date']),
                'UNKNOWN_CASH_CLAIMS',path)
        for claim in pending:
            _require(_number(claim['shares'],'UNKNOWN_SHARE_RIGHTS',path)>=0 and claim['code'] in origin['assets'],
                'UNKNOWN_SHARE_RIGHTS',path)
            held.add(claim['code'])
        for code in held:
            mark=row['marks'].get(code);asset=origin['assets'][code]
            _require(isinstance(mark,dict),'UNKNOWN_HELD_ASSET_MARK',path+'/'+code)
            _require(_number(mark['value'],'UNKNOWN_HELD_ASSET_MARK',path+'/'+code)>0,'UNKNOWN_HELD_ASSET_MARK',path+'/'+code)
            _require(all(mark[k]==asset[k] for k in ('source_id','basis_id','quote_source_ids')),'MARK_SOURCE_CONFLICT',path+'/'+code)
            source_day=date.fromisoformat(mark['source_date']).isoformat()
            _require(source_day==mark['source_date'] and ledger['start']<=source_day<=row['date'],
                'FUTURE_OR_OUTSIDE_MARK',path+'/'+code)
            _require(_number(asset['quotes'].get(source_day),'MISSING_ORIGINAL_MARK',path+'/'+code)==Decimal(mark['value']),
                'MARK_VALUE_CONFLICT',path+'/'+code)
            _require(bool(asset['quote_source_ids']) and all(k in origin['sources'] for k in asset['quote_source_ids']),
                'MARK_SOURCE_CONFLICT',path+'/'+code)
            trading=next(r['trading'] for r in origin['calendar'] if r['date']==row['date'])
            _require(type(trading) is bool and mark['carried_nontrading_mark']==(source_day!=row['date'])
                and (source_day==row['date'] or not trading),'UNPROVEN_CARRIED_MARK',path+'/'+code)


def _evaluate(request):
    _require(set(request)=={'schema','synthetic','evaluation_at','saved_result'} and request['schema']==INPUT
        and request['synthetic'] is True,'EXPLICIT_SYNTHETIC_METRICS_INPUT_REQUIRED')
    evaluation_at=_time(request['evaluation_at'])
    snapshots,summary=_snapshots(request['saved_result'])
    return _evaluate_snapshots(request,snapshots,summary)


def _evaluate_snapshots(request,snapshots,summary):
    """Shared checked-source evaluation; callers must validate their own receipts."""
    evaluation_at=_time(request['evaluation_at']);last=snapshots[-1][0]
    origin=snapshots[0][1]['origin_ledger_input'];initial=None;previous=None
    sources=origin['sources']
    _require(bool(sources) and all(v['kind']=='ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET' for v in sources.values()),
        'NON_SYNTHETIC_SOURCE_NOT_SUPPORTED')
    for e,cp in snapshots:
        s=cp['state'];ledger=e['ledger']
        _require(cp['origin_ledger_input']==origin and _fp(origin)==e['origin_ledger_input_id'],'ORIGIN_LEDGER_CONFLICT')
        _require(cp['execution_result']==e,'CHECKPOINT_EXECUTION_CONFLICT')
        _require(cp['integrity']==dict(origin_ledger_input_id=_fp(origin),execution_result_id=e['result_id'],
            ledger_close_proof_id=_fp(e['ledger_close_proof'])),'CHECKPOINT_INTEGRITY_CONFLICT')
        _require(_number(s['external_flow'],'UNKNOWN_EXTERNAL_FLOW')==0,'EXTERNAL_FLOW_NOT_IMPLEMENTED')
        root=_number(ledger['initial_equity'],'UNKNOWN_ORIGINAL_CAPITAL')
        _require(root>0 and _number(s['origin_initial_capital'],'UNKNOWN_ORIGINAL_CAPITAL')==root,'ORIGINAL_CAPITAL_CONFLICT')
        _require(initial is None or root==initial,'ORIGINAL_CAPITAL_CONFLICT');initial=root
        _require(ledger['schema']=='rotation-action-ledger/0.1' and ledger['research_only'] is True,'UNSUPPORTED_LEDGER')
        q=ledger['source_qualification']
        _require(q['calendar']=='VERIFIED_COMPLETE' and q['opening_claims']=='VERIFIED' and q['net_distributions']=='VERIFIED',
            'MISSING_ACCOUNTING_EVIDENCE')
        _require(ledger['total_net_return'] is None and ledger['actual_realized_investor_return'] is None
            and ledger['policy_authorized'] is False and ledger['historical_signal_eligible'] is False,'SOURCE_QUALIFICATION_NOT_RESEARCH_ONLY')
        _require(ledger['start']==origin['start'] and ledger['end']==s['through_at'][:10],'ORIGINAL_WINDOW_CONFLICT')
        _require(_number(ledger['daily'][0]['net_accrual_equity'],'UNKNOWN_EQUITY')==root,'ORIGINAL_CAPITAL_CONFLICT')
        _validate_rows(ledger,origin)
        if previous is not None:
            _require(ledger['daily'][:len(previous['daily'])]==previous['daily'],'LEDGER_PREFIX_CHANGED')
        previous=ledger
    _require(_time(last['observed_until'])<=evaluation_at and _time(summary['account']['available_at'])<=evaluation_at,
        'CLOSE_NOT_YET_AVAILABLE')
    ledger=last['ledger']
    _require(ledger['status']=='QUALIFIED_ACCOUNTING_SCENARIO_NOT_STRATEGY_VALIDATION' and ledger['refusal_reasons']==[]
        and ledger['quote_gaps']==[],'LEDGER_RETURN_REFUSED')
    result=_curve_statistics(ledger['daily'])
    terminal=_number(ledger['end_net_equity'],'UNKNOWN_TERMINAL_VALUE');exit_cost=_number(ledger['terminal_estimated_exit_cost'],'UNKNOWN_TERMINAL_COST')
    saved_growth=_number(ledger['scenario_net_return'],'UNKNOWN_TERMINAL_GROWTH')
    fees=_number(ledger['fees_and_tax_on_fills'],'UNKNOWN_RECORDED_FEES')
    _require(terminal>0 and exit_cost>=0 and fees>=0 and terminal+exit_cost==Decimal(result['curve'][-1]['equity']),
        'TERMINAL_ACCOUNT_VALUE_CONFLICT')
    _require(abs(saved_growth-(terminal/initial-1))<=Decimal('1e-45'),'TERMINAL_GROWTH_CONFLICT')
    _require(not ledger['daily'][-1]['share_receivables'],'TERMINAL_UNTRADABLE_RIGHTS')
    source=dict(document_id=_fp(request['saved_result']),execution_result_id=last['result_id'],ledger_input_id=ledger['input_id'],
        origin_ledger_input_id=last['origin_ledger_input_id'],checkpoint_id=snapshots[-1][1]['checkpoint_id'],
        source_schema=summary['source']['schema'],start=ledger['start'],end=ledger['end'],evaluation_at=request['evaluation_at'],
        ledger_available_at=summary['account']['available_at'],snapshot_count=len(snapshots),rows_used_once=len(ledger['daily']))
    return dict(statistics=result,source=source,account=deepcopy(summary['account']),
        costs=dict(recorded_fill_fee_tax=str(fees),terminal_estimated_exit_cost=str(exit_cost),
            cost_treatment='ALREADY_RECORDED_FEES_NOT_DEDUCTED_AGAIN_TERMINAL_EXIT_SEPARATE'),
        initial_capital=str(initial),terminal_accrual_equity=result['curve'][-1]['equity'],
        terminal_net_equity=ledger['end_net_equity'],terminal_net_growth=ledger['scenario_net_return'])


def evaluate_saved(request):
    """No IO. Fingerprints prove saved consistency, not source authenticity."""
    out=dict(schema=SCHEMA,synthetic=True,status='REFUSED',reasons=[],statistics=None,account=None,source=None,costs=None,
        initial_capital=None,terminal_accrual_equity=None,terminal_net_equity=None,terminal_net_growth=None,
        valuation_basis=BASIS,validation_scope='SAVED_STRUCTURAL_AND_CURVE_CHECKS_NOT_LEDGER_REPLAY_OR_SOURCE_AUTHENTICATION',
        ranking=None,selected_strategy=None,strategy_validated=False,primary_pressure_id=None,**{k:False for k in FLAGS})
    try:
        # Reproduce the original standard-context results, independently of the
        # caller's rounding, exponent limits, traps, flags or DefaultContext.
        # Creating an explicit local context also leaves the caller untouched.
        with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999,
                capitals=1,clamp=0,flags=[],traps=[InvalidOperation,DivisionByZero,Overflow])):
            out.update(_evaluate(request));out['status']='EVALUATED'
    except (ValueError,KeyError,TypeError,AttributeError,IndexError,InvalidOperation,OverflowError) as exc:
        out['reasons']=[dict(reason=str(exc),path=getattr(exc,'path',''),
            classification='SAVED_RESULT_OR_REQUIRED_VALUE_NOT_SUPPORTED',guard_reasons=getattr(exc,'guard_reasons',[]))]
    out['evaluation_id']=_fp(out)
    return out


def render_text(result):
    lines=['全帳戶合成評估（非市場績效）','評估狀態：'+result['status']]
    if result['status']!='EVALUATED':return '\n'.join(lines+[r['reason'] for r in result['reasons']])+'\n'
    s=result['statistics'];worst=s['maximum_drawdown_episode']
    lines+=['口徑：原帳應計淨值，已含保存成交成本；不是每日可清倉金額。',
        '期間：'+result['source']['start']+'～'+result['source']['end'],
        '原始資本：'+result['initial_capital']+'；期末應計淨值：'+result['terminal_accrual_equity'],
        '期間應計成長（非年化）：'+s['period_accrual_growth'],
        '原帳期末成本後成長：'+result['terminal_net_growth'],
        '最大回撤：'+s['maximum_drawdown']+'；最長峰值下方日曆日：'+str(s['maximum_drawdown_duration_calendar_days']),
        '最深回撤恢復日：'+(worst['recovery_date'] or '截至終點未恢復') if worst else '沒有回撤區間',
        '期末仍未恢復：'+str(s['recovery_censored']),
        '原帳成交費稅：'+result['costs']['recorded_fill_fee_tax']+'（已包含，不再扣）',
        '原帳期末假想退出成本：'+result['costs']['terminal_estimated_exit_cost']+'（另列，非已成交）',
        '不排名；全部正式資格false，主壓力null。']
    return '\n'.join(lines)+'\n'
