"""Pure preparation/admission for one explicit RAW market research case.

No policy, fill generation, ledger execution, source IO or qualification upgrade.
The latest saved source contract still refuses numeric market accounting.
"""
from copy import deepcopy
from datetime import date,datetime,timedelta,timezone
from decimal import Context,localcontext,InvalidOperation,DivisionByZero,Overflow,ROUND_HALF_EVEN
from graph_core.core import fingerprint,number
from . import subsidiary_proposal
from .subsidiary_proposal_sources import study_input

INPUT='rotation-market-case-input/0.1'
SCHEMA='rotation-market-case-preparation/0.1'
PATHS={'hold':'HOLD_A','reduce':'REDUCE_A','cash':'EXIT_A_TO_CASH'}
POINTS=[('A-reference','1101','2026-03-12','high','25.20'),
    ('A-breakout','1101','2026-04-08','close','25.40'),('A-return','1101','2026-04-09','close','25.10'),
    ('B-reference','2884','2026-02-26','high','35.50'),('B-breakout','2884','2026-06-22','close','35.80')]
DECISIONS={'A-breakout':'2026-04-08','A-return':'2026-04-09','B-opportunity':'2026-06-22'}
TZ=timezone(timedelta(hours=8))


class CaseError(ValueError):pass


def require(ok,reason):
    if not ok:raise CaseError(reason)


def stamp(value):
    t=datetime.fromisoformat(value);require(t.tzinfo is not None,'EXPLICIT_TIMEZONE_REQUIRED');return t


def source_binding(saved):
    return {k:fingerprint(v) for k,v in saved.items()}


def _observations(saved,through=None):
    quotes=saved['quotes'];result=[]
    require(quotes['mode']=='RAW' and set(quotes['assets'])=={'1101','2884'},'EXPLICIT_SAVED_RAW_ASSETS_REQUIRED')
    for k,c,d,field,expected in POINTS:
        if through is not None and d>through:continue
        asset=quotes['assets'][c];rows=[b for b in asset['bars'] if b['date']==d]
        require(len(rows)==1 and rows[0].get(field)==expected,'SPECIFIED_MARKET_OBSERVATION_UNAVAILABLE_OR_CHANGED:'+k)
        result.append(dict(id=k,code=c,date=d,field=field,value=expected,source_id=asset['source_id'],basis_id=asset['basis_id'],
            available_at=None,availability='HISTORICAL_PUBLICATION_NOT_AUTHENTICATED',
            role='EXPLICIT_CASE_REFERENCE_NOT_FORMAL_PRIMARY_PRESSURE' if 'reference' in k else 'SAVED_PRICE_OBSERVATION_NOT_ORDER'))
    return result


def _prefixes(request,saved,facts):
    require(len(request['decisions'])==3 and {d['id'] for d in request['decisions']}==set(DECISIONS),'EXACT_CASE_DECISIONS_REQUIRED')
    return [_one_prefix(d,facts) for d in request['decisions']]


def prepare_decision_prefix(request,saved,decision_id):
    """A current observation prefix never validates a later price observation.

    This is not a decision or historical-availability certification. Full source
    integrity identity is returned separately from the prefix comparison scope.
    """
    with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999,capitals=1,clamp=0,flags=[],
            traps=[InvalidOperation,DivisionByZero,Overflow])):
        _case_header(request,saved)
        require(decision_id in DECISIONS,'UNKNOWN_CASE_DECISION')
        items=[d for d in request['decisions'] if d['id']==decision_id];require(len(items)==1,'EXACT_CASE_DECISIONS_REQUIRED')
        facts=_observations(saved,through=DECISIONS[decision_id])
        prefix=_one_prefix(items[0],facts)
        return dict(source_integrity_metadata=deepcopy(request['source_binding']),prefix=prefix)


def _one_prefix(d,facts):
    require(set(d)=={'id','market_date','decision_at','data_cutoff','evidence_ids'} and d['id'] in DECISIONS and
        d['market_date']==DECISIONS[d['id']],'CASE_DECISION_FIELDS_OR_DATE_MISMATCH')
    cutoff=d['market_date']
    if d['data_cutoff'] is not None:
        t=stamp(d['data_cutoff']);require(t.astimezone(TZ).date().isoformat()==cutoff,'CASE_CUTOFF_DATE_MISMATCH')
    if d['decision_at'] is not None:
        require(d['data_cutoff'] is not None and stamp(d['decision_at'])>=stamp(d['data_cutoff']),'DECISION_BEFORE_CUTOFF')
    ids=d['evidence_ids'];require(len(ids)==len(set(ids)),'DUPLICATE_EVIDENCE_REFERENCE')
    for eid in ids:
        definitions=[f for f in POINTS if f[0]==eid];require(len(definitions)==1,'UNKNOWN_CASE_EVIDENCE')
        require(definitions[0][2]<=cutoff,'FUTURE_EVIDENCE_REFERENCE')
    prefix=dict(decision_id=d['id'],market_date=cutoff,decision_at=d['decision_at'],data_cutoff=d['data_cutoff'],
        observations=[deepcopy(f) for f in facts if f['date']<=cutoff],referenced_evidence_ids=deepcopy(ids),
        usable_historical_signal_ids=[],historical_availability='UNKNOWN_NOT_BACKFILLED_FROM_CAPTURE',
        reassessment_required=d['id']=='A-return',automatic_exit_or_transfer=False)
    prefix['prefix_id']=fingerprint(prefix);return prefix


def _gaps(request):
    c=request['common'];g=[]
    for key in ('period','execution_model','market_observations'):
        if c.get(key) is None:g.append('common.'+key)
    for key in ('account_id','cash'):
        if c['account'].get(key) is None:g.append('common.account.'+key)
    if request['common_entry'] is None:g.append('common_entry')
    for d in request['decisions']:
        for key in ('decision_at','data_cutoff'):
            if d[key] is None:g.append(d['id']+'.'+key)
    for p in request['paths']:
        for key in ('common','fills','b_intent'):
            if p[key] is None:g.append('paths.'+p['id']+'.'+key)
    return g


def _bind_complete(request,saved):
    c=request['common'];period=c['period'];account=c['account'];model=c['execution_model']
    require(set(c)=={'period','account','execution_model','market_observations'},'EXACT_COMMON_FIELDS_REQUIRED')
    require(set(period)=={'start','end'} and date.fromisoformat(period['start'])<date.fromisoformat(period['end']),'EXPLICIT_COMMON_PERIOD_REQUIRED')
    require(period['start']<'2026-04-08' and period['end']>='2026-06-22','PERIOD_MUST_COVER_CASH_START_AND_B_OPPORTUNITY')
    require(set(account)=={'kind','account_id','cash','shares','cash_claims','share_claims','rights_basis'} and
        account['kind']=='NEW_HYPOTHETICAL_CASH_NOT_USER_ACCOUNT' and bool(account['account_id']) and
        account['shares']=={'1101':'0','2884':'0'} and account['cash_claims']==[] and account['share_claims']==[] and
        account['rights_basis']=='EXPLICIT_NEW_ACCOUNT_ASSUMPTION_NOT_PRIVATE_EVIDENCE','EXPLICIT_NEW_CASH_ACCOUNT_ASSUMPTION_REQUIRED')
    require(isinstance(account['cash'],str) and number(account['cash'])>0,'EXPLICIT_POSITIVE_OPENING_CASH_REQUIRED')
    require(set(model)=={'id','description','parameter_source','declared_at','fill_role','settlement','terminal_costs'} and
        all(isinstance(model[k],str) and model[k].strip() for k in ('id','description','parameter_source','settlement')) and
        model['fill_role']=='HYPOTHETICAL_EXPLICIT_NOT_ACTUAL','EXPLICIT_EXECUTION_MODEL_REQUIRED')
    stamp(model['declared_at'])
    require(set(model['terminal_costs'])=={'fee_rate','minimum_fee','sell_tax','slippage_bps'},'EXPLICIT_TERMINAL_COSTS_REQUIRED')
    require(all(isinstance(v,str) and number(v)>=0 for v in model['terminal_costs'].values()),'INVALID_EXPLICIT_COST')
    require(isinstance(c['market_observations'],list) and bool(c['market_observations']),'EXPLICIT_COMMON_MARKET_OBSERVATIONS_REQUIRED')
    for m in c['market_observations']:
        require(set(m)=={'code','at','available_at','price','capacity','market_state','source_id','basis_id','qualification'},'COMPLETE_EXTERNAL_MARKET_BINDING_REQUIRED')
        require(m['code'] in saved['quotes']['assets'] and m['basis_id']==saved['quotes']['assets'][m['code']]['basis_id'] and
            bool(m['source_id']) and bool(m['market_state']) and bool(m['qualification']),'MARKET_SOURCE_OR_BASIS_MISMATCH')
        stamp(m['at']);stamp(m['available_at']);require(isinstance(m['price'],str) and number(m['price'])>0 and
            isinstance(m['capacity'],str) and number(m['capacity'])>=0,'INVALID_EXTERNAL_MARKET_OBSERVATION')
    entry=request['common_entry']
    require(entry['code']=='1101' and entry['side']=='BUY' and entry['decision_date']=='2026-04-08','EXPLICIT_COMMON_A_ENTRY_REQUIRED')
    require(entry['date']<='2026-04-09','NOT_IMPLEMENTED_ENTRY_NOT_ESTABLISHED_BY_RETURN_REVIEW')
    for p in request['paths']:
        require(p['common']==c,'COMMON_CONDITIONS_MISMATCH')
        require(isinstance(p['b_intent'],str) and p['b_intent'].strip(),'EXPLICIT_B_INTENT_REQUIRED')
        require(isinstance(p['fills'],list) and len(p['fills'])>0 and p['fills'][0]==entry,'COMMON_A_ENTRY_MISMATCH')
        require(len({f['id'] for f in p['fills']})==len(p['fills']),'DUPLICATE_EXPLICIT_FILL_ID')
        require(p['fills']==sorted(p['fills'],key=lambda f:f['date']),'CHRONOLOGICAL_FULL_FILL_HISTORY_REQUIRED')
        for f in p['fills']:
            require(f['code'] in ('1101','2884') and f['side'] in ('BUY','SELL'),'EXPLICIT_SUPPORTED_FILL_REQUIRED')
            require(period['start']<f['date']<=period['end'] and f['decision_date']<f['date'] and f['settlement_date']>=f['date'],'EXPLICIT_FILL_TIMING_REQUIRED')
            if f['code']=='2884':require(f['decision_date']>='2026-06-22','B_FILL_BEFORE_EXPLICIT_OPPORTUNITY')
            require(all(isinstance(f[k],str) and number(f[k])>=0 for k in ('shares','price','fee','tax')) and number(f['shares'])>0 and
                number(f['shares'])==number(f['shares']).to_integral_value() and number(f['price'])>0,'INVALID_EXPLICIT_FILL_VALUES')
            require(f.get('source_ids') and all(s.startswith('quote-') and s[6:].isdigit() and int(s[6:])<len(saved['quote_manifest']) and
                saved['quote_manifest'][int(s[6:])]['path'].endswith(f['code']+'_'+f['date'][:7]+'.json') for s in f['source_ids']),
                'FILL_QUOTE_SOURCE_OUT_OF_PERIOD')
    return fingerprint(dict(source_binding=request['source_binding'],common=c,common_entry=entry))


def prepare_case(request,saved):
    """Bind only; return existing source refusals instead of numeric results."""
    with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999,capitals=1,clamp=0,flags=[],
            traps=[InvalidOperation,DivisionByZero,Overflow])):
        return _prepare(request,saved)


def _prepare(request,saved):
    _case_header(request,saved)
    subsidiary_proposal.validate(saved['catalog'])
    require(len(request['paths'])==3 and {p['id'] for p in request['paths']}==set(PATHS),'EXACT_CASE_PATHS_REQUIRED')
    for p in request['paths']:
        require(set(p)=={'id','intent','common','fills','b_intent'},'EXACT_PATH_FIELDS_REQUIRED')
        require(p['intent']==PATHS[p['id']],'CASE_PATH_INTENT_MISMATCH')
    return _prepare_bound(request,saved)


def _case_header(request,saved):
    require(set(request)=={'schema','case_id','data_kind','source_binding','common','decisions','common_entry','paths'},'EXACT_CASE_FIELDS_REQUIRED')
    require(request['schema']==INPUT and request['case_id']=='1101-return-then-2884-opportunity' and
        request['data_kind']=='SAVED_REAL_RAW_WITH_EXPLICIT_HYPOTHETICAL_ACCOUNT','EXPLICIT_MARKET_CASE_REQUIRED')
    require(set(saved)=={'quotes','quote_manifest','catalog','calendar'} and request['source_binding']==source_binding(saved),'SOURCE_BINDING_MISMATCH')


def _prepare_bound(request,saved):
    facts=_observations(saved);prefixes=_prefixes(request,saved,facts)
    b=saved['quotes']['assets']['2884']['bars'];window=[x for x in b if '2026-02-26'<x['date']<='2026-06-22']
    sessions={x['date'] for x in saved['calendar']['calendar'] if x['trading'] and '2026-02-26'<x['date']<='2026-06-22'}
    complete={x['date'] for x in window}==sessions and all(x.get('close') is not None for x in window)
    crossing=next((x['date'] for x in window if x.get('close') is not None and number(x['close'])>number('35.50')),None) if complete else None
    require(not complete or crossing=='2026-06-22','SPECIFIED_FIRST_STRICT_BREAKOUT_CHANGED')
    gaps=_gaps(request)
    coverage={c:deepcopy(v) for c,v in saved['catalog']['coverage'].items()}
    result=dict(schema=SCHEMA,case_id=request['case_id'],input_id=fingerprint(request),source_binding=deepcopy(request['source_binding']),
        status='AWAITING_EXPLICIT_INPUT',missing_inputs=gaps,observations=facts,decision_prefixes=prefixes,
        b_first_strict_breakout=dict(status='MATCHED_SAVED_COMPLETE_PREFIX' if complete else 'UNKNOWN_INCOMPLETE_PREFIX',date=crossing),
        source_coverage=coverage,common_binding_id=None,comparison_status='NOT_READY',compiled_accounts=None,
        source_admissions=None,numeric_replay='NOT_PERFORMED',order_generation='NOT_PERFORMED',
        prepared_fills='UNEXECUTED_EXTERNAL_MODEL_INPUT_NOT_VALIDATED_ACCOUNT_BALANCES',
        strategy_validation='NOT_VALIDATED',historical_signal_eligible=False,data_qualified=False,execution_model_qualified=False,
        policy_authorized=False,live_execution_authorized=False,primary_pressure_id=None,
        total_net_return=None,scenario_net_return=None,actual_realized_investor_return=None,ranking=None)
    if gaps:return result
    binding=_bind_complete(request,saved);c=request['common'];period=c['period']
    # Reuse existing input adapter, not its historical opening assumptions/strategy.
    base=study_input(saved['quotes'],saved['catalog'],saved['quote_manifest'],saved['calendar'],period['start'],period['end'],'1101')
    base['opening']=dict(cash=c['account']['cash'],shares=deepcopy(c['account']['shares']),cash_claims=[],share_claims=[])
    base['opening_note']=c['account']['rights_basis'];base['terminal_costs']=deepcopy(c['execution_model']['terminal_costs'])
    base['scope']='EXPLICIT_MARKET_CASE_PREPARATION_ONLY_NO_NUMERIC_DISPATCH'
    accounts={};admissions={}
    for p in request['paths']:
        data=deepcopy(base);data['fills']=deepcopy(p['fills']);accounts[p['id']]=data
        admissions[p['id']]=subsidiary_proposal.qualify(data,saved['catalog'])
        require(bool(admissions[p['id']]['refusal_reasons']),'NOT_IMPLEMENTED_UNREVIEWED_SOURCE_ADMISSION_TRANSITION')
    return dict(result,status='REFUSED_SOURCE_QUALIFICATION',common_binding_id=binding,
        comparison_status='COMMON_CONDITIONS_BOUND_NOT_PERFORMANCE_COMPARISON',compiled_accounts=accounts,source_admissions=admissions)
