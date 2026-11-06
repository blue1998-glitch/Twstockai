"""Explicit II-track context projection; never decisions, fills or accounting.

Dates, prices and statement roles belong to the external case definition.
Historical availability and every trading authorization remain unqualified.
"""
from copy import deepcopy
from datetime import date
from decimal import Context,localcontext,ROUND_HALF_EVEN,InvalidOperation,DivisionByZero,Overflow
from graph_core.core import fingerprint,number
from .market_case import CaseError,require,source_binding
from . import subsidiary_proposal

INPUT='rotation-market-case-context-input/0.2'
SCHEMA='rotation-market-case-context/0.2'
FACT_ROLES={'PULLBACK_CATCH_OPPORTUNITY','GRAPH_OPPORTUNITY','DEEPER_LOSS',
    'FOLLOWUP_NEW_LOW_NOT_COMPLETED','RECOVERY_NOT_RECLAIMED_AND_LOWER_THAN_IV','LOCAL_GRAPH_ENTRY_OPPORTUNITY'}
REFERENCE_ROLES={'IMPORTANT_PULLBACK_LEVEL','ORIGINAL_UPPER_REFERENCE','LOCAL_ENTRY_REFERENCE'}
PARAMETERS={'opening_cash','N','shares','reduction_ratio','reserved_cash','common_period','risk_thresholds','probability_model','ranking_model','execution_model'}
KEYS={'schema','case_id','data_kind','source_binding','work_summary_id','track','facts','references','entry_materials',
    'excluded_contexts','selected_entry_material_id','as_of_dates','research_parameters','research_controls'}


def _date(value):
    require(isinstance(value,str) and date.fromisoformat(value).isoformat()==value,'EXPLICIT_CANONICAL_CASE_DATE_REQUIRED')
    return value


def _context():
    return localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999,capitals=1,clamp=0,flags=[],
        traps=[InvalidOperation,DivisionByZero,Overflow]))


def _header(request,saved,summary):
    require(set(request)==KEYS and request['schema']==INPUT,'EXACT_V2_CONTEXT_FIELDS_REQUIRED')
    require(request['data_kind']=='SAVED_REAL_RAW_WITH_WORK_CASE_CONTEXT_NOT_SYNTHETIC','EXPLICIT_REAL_CASE_CONTEXT_REQUIRED')
    require(set(saved)=={'quotes','quote_manifest','catalog','calendar'} and request['source_binding']==source_binding(saved),'SOURCE_BINDING_MISMATCH')
    require(saved['quotes']['mode']=='RAW' and set(saved['quotes']['assets'])=={'1101','2884'},'ONLY_ORIGINAL_1101_2884_CASE_SUPPORTED')
    require(summary['schema']=='work-summary-testimony/0.1' and request['work_summary_id']==fingerprint(summary),'EXPLICIT_WORK_SUMMARY_BINDING_REQUIRED')
    require(all(x['read_by_codex'] is False for x in summary['originals']),'ORIGINAL_RESEARCH_FILE_NOT_AUTHENTICATED_BY_THIS_ADAPTER')
    require(set(request['track'])=={'id','opportunity_id'} and request['track']['id']=='II','EXPLICIT_II_TRACK_REQUIRED')
    require(set(request['research_parameters'])==PARAMETERS,'EXPLICIT_UNKNOWN_OR_DECLARED_RESEARCH_PARAMETERS_REQUIRED')
    require(set(request['research_controls'])=={'K','X4','R4_X5','X5'} and all(x=='UNAPPROVED' for x in request['research_controls'].values()),'RESEARCH_CONTROL_NOT_AUTHORIZED')
    for c in request['excluded_contexts']:
        require(set(c)=={'track_id','ordinary_open_on','ordinary_open','adopted_for_main_track'} and
            c['track_id']!=request['track']['id'] and c['adopted_for_main_track'] is False,'EXCLUDED_CONTEXT_CANNOT_BECOME_MAIN_ENTRY')
    ids=[x['id'] for name in ('facts','references','entry_materials') for x in request[name]]
    require(len(ids)==len(set(ids)),'UNIQUE_CASE_IDENTITIES_REQUIRED')
    opportunities=[f for f in request['facts'] if f['id']==request['track']['opportunity_id']]
    require(len(opportunities)==1 and opportunities[0]['code']=='1101' and opportunities[0]['role']=='PULLBACK_CATCH_OPPORTUNITY','MAIN_TRACK_OPPORTUNITY_BINDING_REQUIRED')
    selected=request['selected_entry_material_id'];known={m['id'] for m in request['entry_materials']}
    require(selected is None or (isinstance(selected,str) and selected in known),'EXPLICIT_SINGLE_KNOWN_MATERIAL_REQUIRED')
    require(len(request['entry_materials'])==2 and {m['channel'] for m in request['entry_materials']}=={'REGULAR_OPEN','ODD_LOT_FIRST_PRINT'},'EXPLICIT_SEPARATE_CHANNEL_MATERIALS_REQUIRED')
    dates=request['as_of_dates'];require(dates and dates==sorted(set(dates)),'EXPLICIT_ORDERED_CONTEXT_DATES_REQUIRED')
    for d in dates:_date(d)
    return opportunities[0]


def _raw_value(saved,code,bar,value):
    require(isinstance(bar,dict) and set(bar)=={'date','field'} and bar['field'] in ('open','high','low','close'),'EXPLICIT_RAW_BAR_LOCATOR_REQUIRED')
    rows=[r for r in saved['quotes']['assets'][code]['bars'] if r['date']==bar['date']]
    require(len(rows)==1 and rows[0].get(bar['field']) is not None and rows[0][bar['field']]==value,'RAW_MODEL_MATERIAL_VALUE_MISMATCH')
    return dict(source_id=saved['quotes']['assets'][code]['source_id'],basis_id=saved['quotes']['assets'][code]['basis_id'],raw_bar=deepcopy(bar))


def _fact(f,request):
    require(set(f)=={'id','code','case_context_on','role','statement','reference_ids','evidence_kind','historical_available_at'},'EXACT_CASE_FACT_FIELDS_REQUIRED')
    require(f['code'] in ('1101','2884'),'ONLY_ORIGINAL_1101_2884_CASE_SUPPORTED')
    require(f['role'] in FACT_ROLES and f['evidence_kind']=='USER_CONFIRMED_CASE_FROM_WORK_SUMMARY' and f['historical_available_at'] is None,'EXPLICIT_UNAUTHENTICATED_CASE_ROLE_REQUIRED')
    _date(f['case_context_on']);lookup={x['id']:x for name in ('facts','references') for x in request[name]}
    for key in f['reference_ids']:
        require(key in lookup and lookup[key]['code']==f['code'],'SAME_ASSET_CASE_REFERENCE_REQUIRED')
        require(lookup[key]['case_context_on']<=f['case_context_on'],'FUTURE_CASE_REFERENCE')
    # A broad source quote can mention later developments. Only typed, dated
    # case facts enter a prefix; original prose stays in the saved input.
    return {k:deepcopy(f[k]) for k in ('id','code','case_context_on','role','reference_ids','evidence_kind','historical_available_at')}


def _reference(r,saved):
    require(set(r)=={'id','code','case_context_on','role','value','raw_bar','evidence_kind','historical_role_known_at'},'EXACT_CASE_REFERENCE_FIELDS_REQUIRED')
    require(r['code'] in ('1101','2884'),'ONLY_ORIGINAL_1101_2884_CASE_SUPPORTED')
    require(r['role'] in REFERENCE_ROLES and r['evidence_kind']=='USER_CONFIRMED_CASE_FROM_WORK_SUMMARY' and
        r['historical_role_known_at'] is None,'EXPLICIT_UNAUTHENTICATED_REFERENCE_ROLE_REQUIRED')
    _date(r['case_context_on']);require(isinstance(r['value'],str) and number(r['value'])>0,'EXPLICIT_REFERENCE_VALUE_REQUIRED')
    binding=None
    if r['raw_bar'] is not None:
        require(r['raw_bar']['date']<=r['case_context_on'],'FUTURE_CASE_REFERENCE')
        binding=_raw_value(saved,r['code'],r['raw_bar'],r['value'])
    return dict(deepcopy(r),source_binding=binding,automatic_exit=False,formal_primary_pressure=False,
        source_qualification='RAW_VALUE_MATCH_ONLY_ROLE_FROM_WORK' if binding else 'WORK_REPORTED_ROLE_OR_VALUE_NO_ORIGIN_BAR_INFERRED')


def _material(m,opportunity,saved):
    require(set(m)=={'id','opportunity_id','code','case_context_on','channel','price_role','price','raw_bar','evidence_kind',
        'capacity','trade_at','historical_available_at','fee_model','settlement_date'},'EXACT_ENTRY_MATERIAL_FIELDS_REQUIRED')
    require(m['code']=='1101','ONLY_ORIGINAL_1101_2884_CASE_SUPPORTED')
    require(m['opportunity_id']==opportunity['id'],'MAIN_TRACK_OPPORTUNITY_BINDING_REQUIRED')
    require(_date(m['case_context_on'])>_date(opportunity['case_context_on']),'MODEL_MATERIAL_MUST_FOLLOW_OPPORTUNITY')
    require(all(m[k] is None for k in ('capacity','trade_at','historical_available_at','fee_model','settlement_date')),'CAPACITY_OR_EXECUTION_EVIDENCE_NOT_IMPLEMENTED')
    require(isinstance(m['price'],str) and number(m['price'])>0,'EXPLICIT_MODEL_MATERIAL_PRICE_REQUIRED')
    binding=None
    if m['channel']=='REGULAR_OPEN':
        require(m['price_role']=='SAVED_DAILY_OPEN_MODEL_MATERIAL' and m['evidence_kind']=='SAVED_RAW_BAR_MODEL_MATERIAL_NOT_FILL' and
            isinstance(m['raw_bar'],dict) and m['raw_bar']==dict(date=m['case_context_on'],field='open'),'CHANNEL_ROLE_OR_SOURCE_MISMATCH')
        binding=_raw_value(saved,m['code'],m['raw_bar'],m['price'])
    else:
        require(m['channel']=='ODD_LOT_FIRST_PRINT' and m['price_role']=='WORK_REPORTED_FIRST_PRINT_MODEL_MATERIAL' and
            m['evidence_kind']=='WORK_SUMMARY_ONLY_NO_RETAINED_FIRST_PRINT_OR_CAPACITY' and m['raw_bar'] is None,'CHANNEL_ROLE_OR_SOURCE_MISMATCH')
    return dict(deepcopy(m),source_binding=binding,actual_fill=False,model_authorized=False,
        source_qualification='DAILY_OPEN_VALUE_ONLY_NOT_EXECUTABLE_TAPE' if binding else 'WORK_SUMMARY_PRICE_ONLY_FIRST_PRINT_SOURCE_AND_CAPACITY_UNKNOWN')


def _prefix(request,saved,opportunity,as_of):
    _date(as_of)
    # Filter by case chronology before validating or reading later values.
    facts=[_fact(f,request) for f in request['facts'] if f['case_context_on']<=as_of]
    refs=[_reference(r,saved) for r in request['references'] if r['case_context_on']<=as_of]
    materials=[_material(m,opportunity,saved) for m in request['entry_materials'] if m['case_context_on']<=as_of]
    chosen=next((m for m in materials if m['id']==request['selected_entry_material_id']),None)
    out=dict(as_of_case_date=as_of,track_id=request['track']['id'],facts=facts,references=refs,
        visible_entry_materials=materials,selected_entry_material=deepcopy(chosen),
        usable_historical_signal_ids=[],historical_availability='UNKNOWN_CASE_CONTEXT_IS_NOT_PUBLICATION_TIME',
        automatic_order=False,automatic_add=False,automatic_exit=False)
    out['prefix_id']=fingerprint(out);return out


def prepare_context_prefix(request,saved,work_summary,*,as_of):
    """Pure current-context projection; full source identity stays separate."""
    with _context():
        opportunity=_header(request,saved,work_summary)
        prefix=_prefix(request,saved,opportunity,as_of)
        return dict(schema=SCHEMA,source_integrity_metadata=dict(input_id=fingerprint(request),
            source_binding=deepcopy(request['source_binding']),work_summary_id=request['work_summary_id']),prefix=prefix)


def prepare_context(request,saved,work_summary):
    """Prepare v0.2 context only; never call qualify, ledger or policy engines."""
    with _context():
        opportunity=_header(request,saved,work_summary)
        subsidiary_proposal.validate(saved['catalog'])
        # Validate the complete definition for the full report, independently
        # from current-prefix access which never inspects later observations.
        for f in request['facts']:_fact(f,request)
        for r in request['references']:_reference(r,saved)
        for m in request['entry_materials']:_material(m,opportunity,saved)
        missing=sorted(k for k,v in request['research_parameters'].items() if v is None)
        parent_ids=[];cat=saved['catalog']
        while cat:
            parent_ids.append(dict(schema=cat['schema'],id=cat['id']));cat=cat.get('parent_catalog')
        return dict(schema=SCHEMA,case_id=request['case_id'],track_id=request['track']['id'],
            status='CONTEXT_PREPARED_RESEARCH_INPUTS_PENDING' if missing else 'CONTEXT_ONLY_NUMERIC_DISPATCH_NOT_IMPLEMENTED',
            input_id=fingerprint(request),source_binding=deepcopy(request['source_binding']),work_summary_id=request['work_summary_id'],
            work_originals_read_by_codex=False,main_opportunity_on=opportunity['case_context_on'],
            prefixes=[_prefix(request,saved,opportunity,d) for d in request['as_of_dates']],
            research_parameters=deepcopy(request['research_parameters']),missing_research_parameters=missing,
            research_controls=deepcopy(request['research_controls']),selected_entry_material_id=request['selected_entry_material_id'],
            source_parent_chain=parent_ids,source_coverage=deepcopy(saved['catalog']['coverage']),
            source_admission='SAVED_INCOMPLETE_COVERAGE_NOT_PROMOTED',account_reconstruction='NOT_PERFORMED',
            numeric_replay='NOT_PERFORMED',order_generation='NOT_PERFORMED',fills=None,
            data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,policy_authorized=False,
            live_execution_authorized=False,primary_pressure_id=None,total_net_return=None,scenario_net_return=None,
            actual_realized_investor_return=None,ranking=None,strategy_validated=False)
