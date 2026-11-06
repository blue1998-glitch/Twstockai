"""Reversible continuation research over explicit point-in-time evidence.

Consumes declared P0-3/volume/step/momentum/cross-scale facts. It does not
recognize new chart patterns, select a pressure line or predict a 'ten-bagger'.
"""
from copy import deepcopy
from graph_core.core import fingerprint
from .core import timestamp,number

VERSION='trend-continuation-research/0.1'
FEATURES=('box','dense_volume_peaks','point_line_steps','momentum_repair','dynamic_balance','cross_scale')
PRESSURE=('DATA_MISSING','NO_IDENTIFIABLE_UPPER_PRESSURE_IN_VERIFIED_SCOPE','BROKEN_OLD_REFERENCE','UPPER_PRESSURE_REMAINS')


def evaluate(payload,*,decision_at):
    if payload['schema']!='trend-continuation-input/0.1' or payload['synthetic'] is not True:
        raise ValueError('Explicit synthetic continuation research input required')
    now=timestamp(decision_at);binding=payload['binding'];records=[];events=[];previous=None
    rows=[r for r in payload['records'] if timestamp(r['decision_at'])<=now and timestamp(r['available_at'])<=now]
    times=[timestamp(r['decision_at']) for r in rows]
    if times!=sorted(set(times)):raise ValueError('Unique chronological point-in-time reviews required')
    for row in rows:
        if timestamp(row['data_cutoff'])>timestamp(row['decision_at']) or timestamp(row['available_at'])>timestamp(row['decision_at']):
            raise ValueError('Evidence became available after its claimed decision')
        support=[];opposition=[];missing=[];evidence_ids=[]
        compatible=all(row['binding'][k]==binding[k] for k in ('code','source_id','basis_id','adjustment_version'))
        if not compatible:missing.append('SOURCE_OR_BASIS_CHANGED_REVALIDATION_REQUIRED')
        for f in FEATURES:
            es=row['evidence'].get(f,[])
            if not es:missing.append('MISSING:'+f)
            for e in es:
                if timestamp(e['available_at'])>timestamp(row['decision_at']) or timestamp(e['occurred_at'])>timestamp(row['data_cutoff']):
                    continue
                if not e['id'] or not e['source_id']:raise ValueError('Source and evidence identity required')
                if e['source_id']!=row['binding']['source_id'] or e['binding']!=row['binding']:
                    raise ValueError('Trend evidence source/basis/version mismatch')
                evidence_ids.append(e['id'])
                if e['stance']=='support':support.append(e['id'])
                elif e['stance']=='refutation':opposition.append(e['id'])
                elif e['stance']=='unknown':missing.append(e['id'])
                else:raise ValueError('Unsupported evidence stance')
        price=number(row['price'])
        if price<=0:raise ValueError('Positive known price required')
        pressure=row['pressure'];status=pressure['status']
        if status not in PRESSURE:raise ValueError('Pressure knowledge must be distinguished explicitly')
        if not compatible:status='DATA_MISSING'
        known=[]
        for ref in payload['references']:
            if timestamp(ref['available_at'])>timestamp(row['decision_at']):continue
            if any(ref['binding'][k]!=row['binding'][k] for k in ('code','source_id','basis_id','adjustment_version')):continue
            known.append(ref)
        asserted_crossings=set(pressure['crossed_reference_ids'])
        crossed=asserted_crossings if compatible else set()
        for key in crossed:
            matches=[r for r in known if r['id']==key]
            if len(matches)!=1 or price<=number(matches[0]['price']):
                raise ValueError('Crossing requires a known same-basis reference and strict observed price fact')
        upper=[r['id'] for r in known if number(r['price'])>=price and r['id'] not in crossed]
        if status=='NO_IDENTIFIABLE_UPPER_PRESSURE_IN_VERIFIED_SCOPE':
            scope=pressure['checked_scope']
            if scope['qualification']!='EXPLICIT_SYNTHETIC_VERIFIED_SCOPE' or not scope['source_ids'] or not scope['scope_id']:
                raise ValueError('Absence of identifiable pressure requires bounded checked evidence, not a data gap')
            if upper:raise ValueError('A new small step cannot erase an existing upper pressure')
        if status=='BROKEN_OLD_REFERENCE' and not crossed:raise ValueError('Explicit broken reference evidence required')
        if upper and status!='DATA_MISSING':status='UPPER_PRESSURE_REMAINS'
        if not compatible:status='DATA_MISSING'
        if not compatible or row['structure_state']=='INSUFFICIENT':state='UNKNOWN'
        elif row['structure_state']=='WEAKENING' or row['invalidation_confirmed']:state='CONTINUATION_REFUTED'
        elif support and row['structure_state'] in ('STRENGTHENING','CONSOLIDATING') and not opposition:state='CONTINUATION_SUPPORTED'
        elif not support and not opposition:state='UNKNOWN'
        else:state='REVIEW_REQUIRED'
        risk_breaches=row['hard_risk_breaches']
        hold='CONDITIONAL_RESEARCH_HOLD' if state=='CONTINUATION_SUPPORTED' else ('REFUTED' if state=='CONTINUATION_REFUTED' else 'UNKNOWN_OR_REVIEW')
        if risk_breaches:hold='RISK_REDUCTION_REQUIRED'
        add=(state=='CONTINUATION_SUPPORTED' and not risk_breaches and row['new_capital_evidence_qualified'] is True
             and compatible and status not in ('DATA_MISSING','NO_IDENTIFIABLE_UPPER_PRESSURE_IN_VERIFIED_SCOPE'))
        rec=dict(decision_at=row['decision_at'],data_cutoff=row['data_cutoff'],available_at=row['available_at'],
            binding=deepcopy(row['binding']),state=state,support=support,refutation=opposition,unknown=missing,
            evidence_ids=evidence_ids,pressure_status=status,known_upper_reference_ids=upper,
            crossed_reference_ids=sorted(crossed),reasonable_space=None,guaranteed_target=None,
            asserted_crossing_ids=sorted(asserted_crossings),
            holding_qualification=hold,additional_capital_qualification='CONDITIONAL_RESEARCH_ONLY' if add else 'NOT_QUALIFIED',
            hard_risk_breaches=deepcopy(risk_breaches),alternative_opportunities=deepcopy(row['alternative_opportunities']),
            extension_reasons=deepcopy(row['extension_reasons']),
            reached_original_target=row['reached_original_target'],elapsed_sessions=row['elapsed_sessions'],
            automatic_exit_on_target_or_days=False,permanent_participation_ratio=None,
            retrospective_winner_label_used=False,data_qualified=False,execution_model_qualified=False,
            historical_signal_eligible=False,policy_authorized=False,live_execution_authorized=False)
        if hold=='CONDITIONAL_RESEARCH_HOLD' and not rec['extension_reasons']:
            raise ValueError('Holding extension needs inspectable reasons and alternative opportunity comparison')
        if not rec['alternative_opportunities']:raise ValueError('Cash/holding/alternative comparison must remain explicit')
        rec['record_id']=fingerprint(rec)
        if state!=previous:
            e=dict(at=row['decision_at'],from_state=previous,to_state=state,evidence_ids=evidence_ids)
            e['event_id']=fingerprint(e);events.append(e)
        records.append(rec);previous=state
    result=dict(schema=VERSION,decision_at=decision_at,records=records,events=events,
                definition='Continuing beyond original expectation; no tenfold requirement or unlimited-return claim',
                primary_pressure_id=None,retrospective_winner_label_used=False)
    result['result_id']=fingerprint(result)
    return result


def competing_targets(frame,trend_record,current):
    """Five external synthetic intents. No permanent share/percentage rule."""
    zero={c:'0' for c in current};holding=dict(current)
    permitted=trend_record['state']=='CONTINUATION_SUPPORTED'
    if trend_record['state']=='UNKNOWN':
        # Keep the recorded account observable; unknown evidence is not a new buy.
        return {p:dict(current) for p in ('original_baseline','structure_hold','flexible_participation','adaptive_exit','account_reallocation')}
    structure=dict(zero,A=frame['structure_shares']) if permitted else zero
    return dict(original_baseline=holding,
                structure_hold=structure,
                flexible_participation=dict(zero,A=frame['participation_shares']),
                adaptive_exit=dict(zero,A=frame['adaptive_shares']),
                account_reallocation=deepcopy(frame['account_targets']))
