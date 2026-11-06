"""Pure decision-time feasibility. Evidence, entry and transfer stay separate.

No market forecasts, implicit reference selection, file IO or trading authority.
All numeric inputs are decimal strings; quantities are explicit integer shares.
"""
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, localcontext
from graph_core.core import fingerprint, number as source_number
from rotation_research.core import fees

VERSION = 'capital-decision/0.2'
FEATURES = ('price_volume', 'box', 'key_position', 'momentum', 'cross_scale')
BINDING = ('source_id', 'basis_id', 'adjustment_version')


def number(value):
    # graph_core correctly requires source strings; internal arithmetic is Decimal.
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError('Non-finite internal arithmetic')
        return value
    return source_number(value)


def timestamp(value):
    t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.utcoffset() is None:
        raise ValueError('Timezone required')
    return t


def nonnegative(value):
    n = number(value)
    if n < 0:
        raise ValueError('Negative account/model input')
    return n


def quantity(value):
    n = nonnegative(value)
    if n != n.to_integral_value():
        raise ValueError('Explicit whole share quantity required')
    return n


def costs(shares, mark, cfg, side):
    n = nonnegative(shares)
    if not n:
        return dict(notional=Decimal(0), fee=Decimal(0), tax=Decimal(0), slippage=Decimal(0), cash=Decimal(0))
    raw = n * number(mark)
    slip = raw * nonnegative(cfg['slippage_bps']) / 10000
    effective = raw + (slip if side == 'BUY' else -slip)
    fee, tax = fees(effective, cfg, side == 'SELL')
    flow = effective + fee + tax if side == 'BUY' else effective - fee - tax
    if flow < 0:
        raise ValueError('Negative net sale proceeds')
    return dict(notional=effective, fee=fee, tax=tax, slippage=slip, cash=flow)


def validate_costs(cfg):
    for key in ('fee_rate', 'minimum_fee', 'sell_tax', 'slippage_bps'):
        nonnegative(cfg[key])
    if number(cfg['slippage_bps']) >= 10000 or cfg['version'] != 'synthetic-costs/0.1':
        raise ValueError('Unsupported cost model')


def _known(record, cutoff, decision):
    return timestamp(record['occurred_at']) <= cutoff and timestamp(record['available_at']) <= decision


def _binding(row, asset):
    if any(not asset[k] or row[k] != asset[k] for k in BINDING):
        raise ValueError('Source/basis/adjustment mismatch')


def _account(data, marks):
    a = data['account']
    if timestamp(a['available_at']) > timestamp(data['decision_at']):
        raise ValueError('Account snapshot not available at decision')
    if timestamp(a['as_of']) > timestamp(data['data_cutoff']):
        raise ValueError('Account after data cutoff')
    if set(a['holdings']) != set(marks):
        raise ValueError('Explicit quantities including zero required for every asset')
    q = {c: quantity(x['shares']) for c, x in a['holdings'].items()}
    for c, x in a['holdings'].items():
        if quantity(x['sellable']) > q[c]:
            raise ValueError('Sellable exceeds holding')
    cash = nonnegative(a['settled_cash'])
    reserve = nonnegative(a['reserved_cash'])
    payable = sum((nonnegative(x['amount']) for x in a['payables']), Decimal(0))
    receivable = sum((nonnegative(x['amount']) for x in a['cash_claims']), Decimal(0))
    rights = sum((quantity(x['shares']) * marks[x['code']] for x in a['share_claims']), Decimal(0))
    ids = [x['id'] for k in ('payables', 'cash_claims', 'share_claims', 'pending_orders') for x in a[k]]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate account claim/order identity')
    pending = Decimal(0)
    locked = {c: Decimal(0) for c in q}
    for o in a['pending_orders']:
        n = quantity(o['remaining_shares'])
        if o['side'] == 'BUY':
            # Reservation must cover the explicitly bounded order, including costs.
            limit = number(o['limit_price'])
            if limit <= 0 or nonnegative(o['reserved_cash']) < costs(n, limit, data['cost_model'], 'BUY')['cash']:
                raise ValueError('Under-reserved pending buy')
            pending += number(o['reserved_cash'])
        elif o['side'] == 'SELL':
            locked[o['code']] += n
        else:
            raise ValueError('Unsupported pending order side')
    if cash - reserve - payable - pending < 0:
        raise ValueError('Existing reservations exceed settled cash')
    for c in q:
        if locked[c] > quantity(a['holdings'][c]['sellable']):
            raise ValueError('Pending sell exceeds sellable shares')
    nav = cash + receivable + rights - payable + sum((q[c] * marks[c] for c in q), Decimal(0))
    if nav <= 0:
        raise ValueError('Opening capital cannot be established')
    return q, nav, cash - reserve - payable - pending, locked


def evidence_tokens(e):
    # Shared bars, formation points and event IDs are dependent evidence.
    tokens = [e['source_id'] + ':' + k + ':' + str(e[k]) for k in
              ('formation_id', 'volume_bar_id', 'event_id') if e.get(k) is not None]
    if not tokens:
        raise ValueError('Evidence needs an explicit dependence identity')
    return set(tokens)


def _risk(q, marks, nav, data):
    r = data['risk_limits']
    q = dict(q)
    for claim in data['account']['share_claims']:
        q[claim['code']] += quantity(claim['shares'])
    exposures = {c: q[c] * marks[c] for c in q}
    groups = {}
    for c, x in exposures.items():
        g = data['assets'][c]['group']
        groups[g] = groups.get(g, Decimal(0)) + x
    violations = {('single:' + c): max(Decimal(0), exposures[c] - nonnegative(r['single_name_value'][c])) for c in q}
    violations.update({('group:' + g): max(Decimal(0), x - nonnegative(r['group_value'][g])) for g, x in groups.items()})
    # Common hypothetical stress prices are assumptions, never stop-fill guarantees.
    losses = {}
    for s in data['scenario_set']['scenarios']:
        losses[s['id']] = sum((q[c] * (marks[c] - number(s['prices'][c])) for c in q), Decimal(0))
    worst = max([Decimal(0)] + list(losses.values()))
    violations['account_stress'] = max(Decimal(0), worst - nonnegative(r['account_stress_loss']))
    return violations


def decide(data):
    with localcontext() as ctx:
        ctx.prec = 50
        return _decide(data)


def _decide(data):
    if data['schema'] != 'capital-decision-input/0.1' or data['synthetic'] is not True:
        raise ValueError('Phase 1 accepts explicitly synthetic research only; real-source route remains refused')
    decision, cutoff = timestamp(data['decision_at']), timestamp(data['data_cutoff'])
    if cutoff > decision:
        raise ValueError('Data cutoff after decision')
    validate_costs(data['cost_model'])
    if not data['policy_version'] or not data['parameter_source'] or timestamp(data['policy_available_at']) > decision:
        raise ValueError('Explicit research policy/parameter provenance required')
    for obj in (data['scenario_set'], data['risk_limits'], data['execution_model'],data['cost_model']):
        if timestamp(obj['available_at']) > decision or not obj['version']:
            raise ValueError('Model/limits not available at decision')
    if not data['scenario_set']['scenarios']:
        raise ValueError('Explicit common scenarios required')
    for s in data['scenario_set']['scenarios']:
        if set(s['prices']) != set(data['assets']) or any(number(v) <= 0 for v in s['prices'].values()):
            raise ValueError('Complete positive scenario assumptions required')
    marks, layer1, layer2, evidence, novel = {}, {}, {}, {}, {}
    used = set(data['consumed_evidence_tokens'])
    for code, asset in data['assets'].items():
        rows = [r for r in asset['marks'] if _known(r, cutoff, decision)]
        if not rows:
            raise ValueError('Missing as-of mark; no zero/forward fill: ' + code)
        latest = max(timestamp(r['occurred_at']) for r in rows)
        rows = [r for r in rows if timestamp(r['occurred_at']) == latest]
        if len(rows) != 1 or latest != cutoff:
            raise ValueError('Ambiguous or stale cutoff mark: ' + code)
        row = rows[0]; _binding(row, asset)
        if row['reference_role'] != 'VALUATION_MARK' or number(row['price']) <= 0:
            raise ValueError('Invalid valuation role/price')
        marks[code] = number(row['price'])
        facts = {f: dict(support=[], refutation=[], unknown=[]) for f in FEATURES}
        for e in sorted(asset['evidence'], key=lambda e: (timestamp(e['available_at']), e['id'])):
            if not _known(e, cutoff, decision):
                continue
            _binding(e, asset)
            if e['feature'] not in FEATURES or e['stance'] not in ('support', 'refutation', 'unknown'):
                raise ValueError('Invalid separated evidence category')
            if e['id'] in evidence and evidence[e['id']] != e:
                raise ValueError('Conflicting evidence identity')
            evidence[e['id']] = deepcopy(e)
            facts[e['feature']][e['stance']].append(deepcopy(e))
            tokens = evidence_tokens(e)
            if not tokens & used:
                novel[e['id']] = tokens
            used.update(tokens)
        for f in facts:
            if not any(facts[f].values()):
                facts[f]['unknown'].append({'reason': 'NO_KNOWN_EVIDENCE'})
        layer1[code] = dict(features=facts, strength_probability=None, combined_score=None,
                            conclusion='EVIDENCE_ONLY_NO_STRENGTH_RANKING')
        entry = asset['entry_context']
        if timestamp(entry['available_at']) > decision:
            entry = dict(position=None, formal_reference=None, invalidation_risk=None, liquidity_shares=None)
        else:
            _binding(entry, asset)
            if entry['liquidity_shares'] is not None:
                quantity(entry['liquidity_shares'])
        missing = [k for k in ('position', 'formal_reference', 'invalidation_risk', 'liquidity_shares') if entry[k] is None]
        ref = entry['formal_reference']
        if ref is not None:
            _binding(ref, asset)
            if not _known(ref, cutoff, decision) or ref['reference_role'] != 'FORMAL_RESISTANCE' or number(ref['price']) <= 0:
                raise ValueError('Unknown/wrong formal reference')
        layer2[code] = dict(status='UNKNOWN' if missing else 'CONDITIONAL_RESEARCH_ENTRY',
                            missing=missing, position=deepcopy(entry['position']),
                            invalidation_risk=deepcopy(entry['invalidation_risk']),
                            liquidity_shares=entry['liquidity_shares'],
                            reasonable_space=None if ref is None else str(number(ref['price']) - marks[code]),
                            reference=deepcopy(ref), guaranteed_target=None, data_qualified=False)
    q, nav, available, locked = _account(data, marks)
    baseline_q = dict(q)
    for o in data['account']['pending_orders']:
        if o['side']=='BUY':
            baseline_q[o['code']] += quantity(o['remaining_shares'])
    base_risk = _risk(baseline_q, marks, nav, data)
    cfg = data['cost_model']
    model = data['execution_model']
    credit = Decimal(0)
    if model['buying_power'] == 'BROKER_CREDIT_RESEARCH':
        c = model['broker_credit']
        if (c['qualification'] != 'EXPLICIT_SYNTHETIC_TERMS' or timestamp(c['available_at']) > decision
                or not c['source_id'] or not c['version']):
            raise ValueError('Explicit credit qualification/terms required')
        credit = nonnegative(c['limit'])
    elif model['buying_power'] != 'SETTLED_CASH_ONLY':
        raise ValueError('Unsupported buying power model')
    # Every alternative starts from this exact account, including existing rights.
    common_id = fingerprint(data['account'])
    plans = [dict(id='A-zero', family='A', route='R1', targets={c:str(q[c]) for c in q},
                  trigger_ids=[], edge_budget='0', conditions=['REVIEW_ON_NEW_INDEPENDENT_EVENT'])] + deepcopy(data['plans'])
    if len({p['id'] for p in plans}) != len(plans):
        raise ValueError('Duplicate alternative identity')
    alternatives = []
    for p in plans:
        if p['family'] not in tuple('ABCDEF') or p['route'] not in ('R1', 'R2'):
            raise ValueError('Unsupported candidate family/route')
        out = dict(id=p['id'], family=p['family'], route=p['route'], common_account_id=common_id,
                   initial_capital=str(nav), trigger_ids=p['trigger_ids'], conditions=p['conditions'],
                   cancel_conditions=['EVIDENCE_INVALIDATED', 'BASIS_OR_SOURCE_CHANGED', 'RISK_OR_LIQUIDITY_CHANGED'],
                   next_review_conditions=['NEW_INDEPENDENT_EVENT', 'FILL_OR_SETTLEMENT_UPDATE'],
                   reasons=[], dominated_by=[], indistinguishable_from=[], feasible=False)
        if p['route'] == 'R2' or p['family'] == 'F':
            out.update(status='NOT_IMPLEMENTED', reasons=['ROBUST_MINIMAX_SOLVER_NOT_IMPLEMENTED'])
            alternatives.append(out); continue
        if set(p['targets']) != set(q):
            raise ValueError('Explicit target for every asset required')
        target = {c: quantity(p['targets'][c]) for c in q}
        if p['family'] == 'A' and target != q:
            raise ValueError('Hold must preserve opening shares')
        if p['family'] == 'D' and any(target.values()):
            raise ValueError('Cash alternative must target zero shares')
        reasons = out['reasons']
        if p['family'] == 'C':
            if not p['trigger_ids'] or any(e not in novel for e in p['trigger_ids']) or len(set(p['trigger_ids'])) != len(p['trigger_ids']):
                reasons.append('NO_NEW_INDEPENDENT_TRIGGER')
        buys, sells, friction = Decimal(0), Decimal(0), Decimal(0)
        for c in q:
            change = target[c] - q[c]
            side = 'BUY' if change > 0 else 'SELL'
            x = costs(abs(change), marks[c], cfg, side)
            friction += x['fee'] + x['tax'] + x['slippage']
            if change > 0:
                buys += x['cash']
                if layer2[c]['status'] == 'UNKNOWN':
                    reasons.append('ENTRY_EVIDENCE_UNKNOWN:' + c)
                elif change > quantity(layer2[c]['liquidity_shares']):
                    reasons.append('ENTRY_LIQUIDITY_LIMIT:' + c)
            elif -change > quantity(data['account']['holdings'][c]['sellable']) - locked[c]:
                reasons.append('SELLABLE_SHARES_RESERVED_OR_UNAVAILABLE:' + c)
            else:
                sells += x['cash']
            if abs(change) > quantity(data['risk_limits']['max_trade_shares'][c]):
                reasons.append('LIQUIDITY_REQUIRES_SMALLER_OR_PARTIAL_ORDER:' + c)
        for o in data['account']['pending_orders']:
            # Joint worst case if every outstanding buy fills; no cash reuse.
            if o['side'] == 'BUY':
                target[o['code']] += quantity(o['remaining_shares'])
        after = _risk(target, marks, nav-friction, data)
        reducing = (any(after[k] < base_risk[k] for k in after)
                    and all(after[k] <= base_risk[k] for k in after))
        if any(after.values()) and not reducing:
            reasons.append('RISK_LIMIT_EXCEEDED')
        if nav - friction <= 0:
            reasons.append('COST_EXHAUSTS_CAPITAL')
        funding = 'SETTLED'
        if buys > available + credit:
            if buys <= available + sells + credit:
                funding = 'WAIT_SALE_SETTLEMENT_AND_REEVALUATE'
            else:
                reasons.append('JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS')
        band = nonnegative(p['edge_budget']) <= friction + nonnegative(data['no_trade_buffer'])
        trading = any(quantity(p['targets'][c]) != q[c] for c in q)
        if trading and band and not reducing:
            reasons.append('NO_TRADE_BAND')
        scenario_values = {}
        for s in data['scenario_set']['scenarios']:
            rights = {c:sum((quantity(x['shares']) for x in data['account']['share_claims'] if x['code']==c),Decimal(0)) for c in q}
            scenario_values[s['id']] = str(nav - friction + sum(((quantity(p['targets'][c])+rights[c]) * (number(s['prices'][c])-marks[c]) for c in q), Decimal(0)))
        out.update(status='REJECTED' if reasons else ('CONDITIONAL' if funding != 'SETTLED' else 'FEASIBLE'),
                   feasible=not reasons, targets=deepcopy(p['targets']), risk_reducing=reducing,
                   remaining_risk_violations={k:str(v) for k,v in after.items()},
                   estimated_cost=str(friction), sale_receivable_estimate=str(sells),
                   purchase_payable_estimate=str(buys), available_settled_cash=str(available),
                   broker_credit_separate=str(credit), funding=funding,
                   final_cash_after_all_settlements_estimate=str(number(data['account']['settled_cash']) + sells - buys),
                   scenario_values=scenario_values,
                   scenario_value_qualification='STATIC_TARGET_ATTAINED_STRESS_EXCLUDES_WAITING_AND_NONFILLS',
                   dominance_scope='STATIC_TARGETS_ONLY',policy_dominance='NOT_EVALUATED')
        alternatives.append(out)
    # Pareto comparisons use the same common scenarios and friction, never a score.
    for a in alternatives:
        if not a['feasible']: continue
        for b in alternatives:
            if a is b or not b['feasible']: continue
            av, bv = a['scenario_values'], b['scenario_values']
            if av == bv:
                a['indistinguishable_from'].append(b['id'])
            elif all(number(bv[k]) >= number(av[k]) for k in av):
                a['dominated_by'].append(b['id'])
    decision_result = dict(schema=VERSION, decision_at=data['decision_at'], data_cutoff=data['data_cutoff'],
        policy_version=data['policy_version'], parameter_source=data['parameter_source'], synthetic=True,
        cost_model=deepcopy(cfg), execution_model=deepcopy(model), risk_limits=deepcopy(data['risk_limits']),
        scenario_set=deepcopy(data['scenario_set']),
        common_account_id=common_id, initial_capital=str(nav), layer1=layer1, layer2=layer2,
        layer3=dict(alternatives=alternatives, comparison='STATIC_TARGET_SCENARIO_PARETO_NOT_POLICY_COMPARISON'),
        research_recommendation=dict(status='REVIEW_ALL_FEASIBLE_POLICIES_STATIC_DOMINANCE_IS_DIAGNOSTIC_ONLY',
            candidate_ids=[p['id'] for p in alternatives if p['feasible']]),
        data_qualified=False, execution_model_qualified=False, historical_signal_eligible=False,
        policy_authorized=False, live_execution_authorized=False, primary_pressure_id=None,
        new_evidence_tokens=sorted(set().union(*novel.values())) if novel else [],
        reviewed_evidence_tokens=sorted(used),
        reserved_cash=data['account']['reserved_cash'],
        continuity_qualification='INDEPENDENT_SNAPSHOT_NOT_A_CONTINUOUS_CAPITAL_CHAIN',
        R2_status='NOT_IMPLEMENTED_REQUIRES_OUT_OF_SAMPLE_COMPARISON_WITH_R1')
    decision_result['decision_id'] = fingerprint(decision_result)
    return dict(decision=decision_result, source_integrity_metadata=deepcopy(data['source_integrity_metadata']))


def resume_decision(previous, data, *, checkpoint=None, cancelled_order_ids=()):
    """Carry tokens only after proving the next account from original ledger fills."""
    old=previous['decision']
    if old['schema'] != VERSION or old['decision_id'] != fingerprint({k:v for k,v in old.items() if k!='decision_id'}):
        raise ValueError('Invalid saved predecessor decision')
    if timestamp(data['decision_at']) <= timestamp(old['decision_at']) or timestamp(data['data_cutoff']) < timestamp(old['data_cutoff']):
        raise ValueError('Resume must advance decision time without moving cutoff backward')
    if checkpoint is None:
        raise ValueError('LEDGER_CHECKPOINT_REQUIRED: token carry does not prove capital continuity')
    from .continuity import bind_resume
    linkage=bind_resume(previous,data,checkpoint,cancelled_order_ids)
    next_input=deepcopy(data)
    next_input['consumed_evidence_tokens']=sorted(set(next_input['consumed_evidence_tokens']) | set(old['reviewed_evidence_tokens']))
    result=decide(next_input)
    d=result['decision'];d.pop('decision_id')
    d['continuity_qualification']=linkage['qualification'];d['continuity']=linkage
    d['decision_id']=fingerprint(d)
    result['source_integrity_metadata']['continuity']=deepcopy(checkpoint['integrity'])
    return result
