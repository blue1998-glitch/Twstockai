"""Explicit synthetic hold/cash-buy adapter, including zero-incumbent accounts.

No candidate search, orders, fills, account posting, market replay or policy.
Financial feasibility and original account continuity remain in the old engines.
"""
from copy import deepcopy
from decimal import Context, InvalidOperation, DivisionByZero, Overflow, ROUND_HALF_EVEN, localcontext

from .core import decide, resume_decision, fingerprint, quantity, nonnegative, timestamp, evidence_tokens
from .continuity import validate_checkpoint, account_at_checkpoint
from .quantity_candidates import _validate_batch_context, _first_entry_reasons

INPUT='capital-cash-action-input/0.1'
SCHEMA='capital-cash-action/0.1'
INPUT_V2='capital-cash-action-input/0.2'
SCHEMA_V2='capital-cash-action/0.2'


def evaluate(request):
    """Check one external intent against an exact opening or ledger checkpoint."""
    with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999,
            capitals=1,clamp=0,flags=[],traps=[InvalidOperation,DivisionByZero,Overflow])):
        return _evaluate(request)


def _account_source(source, template):
    kind=source['kind'];previous=None;cp=None
    if kind=='DECLARED_SYNTHETIC_OPENING':
        if set(source)!={'kind','account','consumed_evidence_tokens'}:
            raise ValueError('EXACT_DECLARED_OPENING_REQUIRED')
        account=deepcopy(source['account']);tokens=deepcopy(source['consumed_evidence_tokens'])
        if not isinstance(tokens,list) or any(not isinstance(t,str) or not t for t in tokens) or len(set(tokens))!=len(tokens):
            raise ValueError('EXPLICIT_UNIQUE_OPENING_TOKENS_REQUIRED')
        binding=dict(kind=kind,qualification='DECLARED_SYNTHETIC_OPENING_NOT_A_CONTINUOUS_CHAIN',
            checkpoint_id=None,origin_ledger_input_id=None,origin_initial_capital=None,latest_predecessor_id=None,
            accepted_fill_ids=[],closed_order_states={},reviewed_evidence_tokens=sorted(tokens))
    elif kind=='CHECKPOINT':
        if set(source)!={'kind','checkpoint','expected_checkpoint_id','expected_latest_decision_id'}:
            raise ValueError('EXACT_CHECKPOINT_SOURCE_REQUIRED')
        cp=source['checkpoint']
        if source['expected_checkpoint_id']!=cp['checkpoint_id']:
            raise ValueError('EXACT_CHECKPOINT_REQUIRED')
        validate_checkpoint(cp)
        execution=cp['execution_result'];latest=execution['latest_decision_id']
        if source['expected_latest_decision_id']!=latest:
            raise ValueError('EXACT_LATEST_PREDECESSOR_REQUIRED')
        if cp['state']['unfilled_orders']:
            raise ValueError('ACTIVE_ORDER_CONTINUATION_NOT_IMPLEMENTED')
        account=account_at_checkpoint(cp,decision_at=template['decision_at'])
        previous=dict(decision=deepcopy(execution['decision_records'][latest]))
        # Every existing asset and reference identity stays on the original book.
        prior={r['identity']['code']:r['identity'] for r in execution['fact_sources'][latest]['records']}
        if set(template['assets'])!=set(prior) or any(
                template['assets'][c][k]!=prior[c][k]
                for c in prior for k in ('source_id','basis_id','adjustment_version')):
            raise ValueError('CHECKPOINT_ASSET_SOURCE_BASIS_CHANGED')
        tokens=sorted(set(cp['state']['reviewed_evidence_tokens']) | set(previous['decision']['reviewed_evidence_tokens']))
        binding=dict(kind=kind,qualification='ORIGINAL_SYNTHETIC_CHECKPOINT_NOT_INVESTOR_AUTHORITY',
            checkpoint_id=cp['checkpoint_id'],origin_ledger_input_id=cp['integrity']['origin_ledger_input_id'],
            origin_initial_capital=cp['state']['origin_initial_capital'],latest_predecessor_id=latest,
            latest_common_account_id=execution['latest_common_account_id'],
            accepted_fill_ids=[f['id'] for f in cp['state']['accepted_fills']],
            closed_order_states=deepcopy(cp['state']['order_states']),reviewed_evidence_tokens=tokens)
    else:
        raise ValueError('SUPPORTED_EXPLICIT_ACCOUNT_SOURCE_REQUIRED')
    if account['as_of']!=template['data_cutoff']:
        raise ValueError('ACCOUNT_CUTOFF_MUST_MATCH_ORIGINAL_SNAPSHOT')
    if account['payables']:
        raise ValueError('OPENING_PAYABLE_CONTINUATION_NOT_IMPLEMENTED')
    if account['pending_orders']:
        raise ValueError('EXTERNAL_PENDING_ORDER_CONTINUATION_NOT_IMPLEMENTED')
    return account,tokens,previous,cp,binding


def _evaluate(request):
    selling=isinstance(request,dict) and request.get('schema')==INPUT_V2
    out=dict(schema=SCHEMA_V2 if selling else SCHEMA,synthetic=True,status='PENDING',reasons=[],intent=None,
        core_decision=None,account_binding=None,research_recommendation=dict(candidate_ids=[],selected_id=None,ranking=None),
        order_generation='NOT_PERFORMED',execution='NOT_PERFORMED',account_posting='NOT_PERFORMED',
        strategy_validated=False,data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,
        policy_authorized=False,live_execution_authorized=False,primary_pressure_id=None)
    integrity=dict(full_request_id=fingerprint(request),derived_decision_input=None,core_source_integrity_metadata=None)
    def wrap():
        return dict(research=out,source_integrity_metadata=integrity)
    try:
        if (not isinstance(request,dict) or set(request)!={'schema','synthetic','decision_template','account_source','action','policy'}
                or request['schema'] not in (INPUT,INPUT_V2) or request['synthetic'] is not True
                or any(not isinstance(request[k],dict) for k in ('decision_template','account_source','action','policy'))
                or request['decision_template'].get('synthetic') is not True):
            raise ValueError('EXPLICIT_SYNTHETIC_CASH_ACTION_REQUIRED')
        template=request['decision_template'];action=request['action'];policy=request['policy']
        if {'account','plans','consumed_evidence_tokens'} & set(template):
            raise ValueError('DERIVED_ACCOUNT_PLANS_TOKENS_CANNOT_BE_OVERRIDDEN')
        if {'orders','tape','continuation','ledger_input','reassessments','selected_candidate'} & set(template):
            raise ValueError('DECISION_TEMPLATE_EXECUTION_FIELDS_FORBIDDEN')
        fields={'id','kind','code','sell_shares','reason'} if selling else {'id','kind','code','additional_shares','trigger_ids','batch_context'}
        if set(action)!=fields:
            raise ValueError('EXACT_EXPLICIT_ACTION_REQUIRED')
        if not isinstance(action['id'],str) or not action['id'] or action['id']=='A-zero':
            raise ValueError('EXPLICIT_NONBASELINE_ACTION_ID_REQUIRED')
        if set(policy)!={'version','parameter_source','available_at','edge_budget'} or not policy['version'] or not policy['parameter_source']:
            raise ValueError('EXPLICIT_ACTION_POLICY_REQUIRED')
        if timestamp(policy['available_at'])>timestamp(template['decision_at']):
            raise ValueError('ACTION_POLICY_NOT_YET_AVAILABLE')
        nonnegative(policy['edge_budget'])
        if template['execution_model']['buying_power']!='SETTLED_CASH_ONLY':
            raise ValueError('CREDIT_CONTINUATION_NOT_IMPLEMENTED')
        if selling:
            source=request['account_source']
            if source.get('kind')!='CHECKPOINT':
                raise ValueError('CHECKPOINT_REQUIRED_FOR_SELL')
            sources=source['checkpoint']['origin_ledger_input']['sources']
            if not sources or any(s['kind']!='ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET' for s in sources.values()):
                raise ValueError('EXPLICIT_SYNTHETIC_SELL_CHECKPOINT_REQUIRED')
        account,tokens,previous,cp,binding=_account_source(request['account_source'],template)
        data=deepcopy(template);data.update(account=account,consumed_evidence_tokens=tokens,plans=[])
        continuation=None if cp is None else dict(previous_decision=previous,checkpoint=cp,cancelled_order_ids=[])
        targets={c:str(int(quantity(row['shares']))) for c,row in account['holdings'].items()}
        triggers=[] if selling else action['trigger_ids']
        if not isinstance(triggers,list) or any(not isinstance(t,str) or not t for t in triggers):
            raise ValueError('EXPLICIT_TRIGGER_LIST_REQUIRED')
        first=False;batch=None
        sale_scope=None
        if selling:
            if action['kind'] not in ('REDUCE_HOLDING','EXIT_SELLABLE_HOLDING'):
                raise ValueError('EXPLICIT_SELL_ACTION_KIND_REQUIRED')
            if not isinstance(action['reason'],str) or not action['reason'].strip():
                raise ValueError('EXPLICIT_SELL_REASON_REQUIRED')
            code=action['code']
            if code not in targets:
                raise ValueError('EXPLICIT_HELD_ASSET_REQUIRED')
            n=quantity(action['sell_shares']);held=quantity(account['holdings'][code]['shares']);sellable=quantity(account['holdings'][code]['sellable'])
            if n<=0:
                raise ValueError('POSITIVE_EXPLICIT_SELL_SHARES_REQUIRED')
            if n>sellable:
                raise ValueError('SELL_QUANTITY_EXCEEDS_AVAILABLE_SHARES')
            if action['kind']=='REDUCE_HOLDING' and n>=held:
                raise ValueError('REDUCTION_MUST_LEAVE_SPECIFIED_HOLDING')
            if action['kind']=='EXIT_SELLABLE_HOLDING' and n!=sellable:
                raise ValueError('EXIT_MUST_MATCH_CURRENT_SELLABLE_SHARES')
            targets[code]=str(held-n)
            sale_scope=dict(code=code,authorized_sell_shares=str(n),original_shares=str(held),original_sellable=str(sellable),
                target_remaining_shares=targets[code],completion='INTENT_ONLY_CHECK_ACTUAL_FILLS',account_liquidation_claimed=False)
            plan=dict(id=action['id'],family='E',route='R1',targets=targets,trigger_ids=[],edge_budget=policy['edge_budget'],
                conditions=['EXPLICIT_SELL_INTENT_NOT_STRATEGY_SIGNAL','PRESERVE_OTHER_ASSETS_AND_RIGHTS','SALE_PROCEEDS_WAIT_EXPLICIT_SETTLEMENT'])
            data['plans']=[plan];plan_id=plan['id']
        elif action['kind']=='HOLD':
            if action['code'] is not None or action['batch_context'] is not None or quantity(action['additional_shares']) or triggers:
                raise ValueError('HOLD_MUST_PRESERVE_ALL_SHARES_WITHOUT_BUY_SCOPE')
            plan=None;plan_id='A-zero'
        elif action['kind']=='BUY_FROM_SETTLED_CASH':
            code=action['code']
            if code not in targets or quantity(action['additional_shares'])<=0:
                raise ValueError('EXPLICIT_ASSET_AND_POSITIVE_WHOLE_SHARE_BUY_REQUIRED')
            context=deepcopy(action['batch_context'])
            if not isinstance(context,dict) or {'account_id','origin'} & set(context):
                raise ValueError('BATCH_ACCOUNT_AND_ORIGIN_ARE_DERIVED')
            context.update(account_id=fingerprint(account),origin='CHECKPOINT_EPISODE' if cp else 'DECLARED_SYNTHETIC_OPENING')
            batch=dict(batch_context=context,decision_input=data,destination=code,continuation=continuation)
            _validate_batch_context(batch)
            first=context['phase']=='FIRST_ENTRY'
            if first and triggers:
                raise ValueError('FIRST_ENTRY_CANNOT_SILENTLY_IGNORE_TRIGGER_IDS')
            targets[code]=str(quantity(targets[code])+quantity(action['additional_shares']))
            plan=dict(id=action['id'],family='E' if first else 'C',route='R1',targets=targets,
                trigger_ids=deepcopy(triggers),edge_budget=policy['edge_budget'],
                conditions=['EXPLICIT_RESEARCH_INTENT_ONLY','EXISTING_SETTLED_CASH_NO_ASSUMED_SALE',
                            'NEW_INDEPENDENT_TRIGGER_FOR_ADDITIONAL_BATCH'])
            data['plans']=[plan];plan_id=plan['id']
        else:
            raise ValueError('ONLY_EXPLICIT_HOLD_OR_SETTLED_CASH_BUY_SUPPORTED')
        result=decide(data) if cp is None else resume_decision(previous,data,checkpoint=cp,cancelled_order_ids=[])
        decision=result['decision'];evaluation=deepcopy(next(p for p in decision['layer3']['alternatives'] if p['id']==plan_id))
        gate=[]
        if batch is not None:
            code=action['code']
            known={e['id']:e for feature in decision['layer1'][code]['features'].values()
                   for stance in feature.values() for e in stance if 'id' in e}
            gate.extend(_first_entry_reasons(batch,known))
            if not first:
                if any(t not in known for t in triggers):gate.append('BATCH_TRIGGER_NOT_OWNED_BY_DESTINATION')
                review=decision['layer2'][code]['capital_eligibility']['review']
                review_ids=set(review['evidence_ids']) if review else set()
                if any(evidence_tokens(known[t]) & evidence_tokens(known[old])
                       for t in triggers if t in known for old in review_ids if old in known and old!=t):
                    gate.append('NO_NEW_INDEPENDENT_TRIGGER')
            if evaluation.get('funding')!='SETTLED':gate.append('CASH_ACTION_CANNOT_ASSUME_SALE_SETTLEMENT')
        passed=bool(evaluation['feasible'] and not gate)
        integrity.update(derived_decision_input=deepcopy(data),core_source_integrity_metadata=deepcopy(result['source_integrity_metadata']))
        out.update(status='CURRENTLY_FEASIBLE' if passed else 'REJECTED',
            reasons=sorted(set(evaluation['reasons']+gate)),account_binding=binding,
            core_decision=deepcopy(decision),
            intent=dict(external_action=deepcopy(action),bound_batch_context=deepcopy(batch['batch_context']) if batch else None,
                plan=deepcopy(plan),evaluated_plan_id=plan_id,core_evaluation=evaluation,batch_gate_reasons=gate,
                feasible_for_research=passed,other_asset_targets_preserved=True,
                account_liquidation_claimed=False,purpose='ONE_EXPLICIT_INTENT_NOT_OPTIMIZATION_OR_EXECUTION'))
        out['research_recommendation']['candidate_ids']=[plan_id] if passed else []
        if selling:
            out['intent']['sale_scope']=sale_scope
        return wrap()
    except (ValueError,KeyError,TypeError,IndexError,StopIteration) as exc:
        reason=str(exc);unsupported=reason.split(':',1)[0].endswith('NOT_IMPLEMENTED')
        out.update(status='NOT_IMPLEMENTED' if unsupported else 'INPUT_ERROR',reasons=[reason],error_type=type(exc).__name__)
        return wrap()
