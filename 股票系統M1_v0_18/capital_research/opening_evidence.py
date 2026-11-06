"""Pure synthetic opening-evidence diagnostics: no IO, accounting or admission."""
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

INPUT_SCHEMA = 'opening-entitlement-evidence-input/0.1'
SCHEMA = 'opening-entitlement-evidence-diagnostic/0.1'
SOURCE_KIND = 'ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET'


def _time(value):
    if not isinstance(value, str) or 'T' not in value:
        raise ValueError('Explicit timezone-aware timestamp required')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise ValueError('Explicit timezone-aware timestamp required')
    return result


def _number(value, *, whole=False):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError('Explicit decimal string required')
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('Finite nonnegative decimal string required') from exc
    if not result.is_finite() or result < 0 or (whole and result != result.to_integral_value()):
        raise ValueError('Finite nonnegative quantity required')
    return result


def _date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Explicit ISO date required')
    return date.fromisoformat(value)


def _required(data):
    binding = data['binding']
    if set(binding) != {'account_id', 'scenario_id', 'currency'} or any(not isinstance(v, str) or not v for v in binding.values()):
        raise ValueError('Explicit account/scenario/currency binding required')
    if not isinstance(data['assets'], dict) or not data['assets']:
        raise ValueError('Explicit asset scopes required')
    fields = {p: ('list' if p in ('payables', 'pending_orders') else 'number', deepcopy(binding))
              for p in ('settled_cash', 'reserved_cash', 'payables', 'pending_orders')}
    for code, asset in data['assets'].items():
        if not isinstance(code, str) or not code or set(asset) != {'price_source_id', 'basis_id', 'adjustment_version'}:
            raise ValueError('Explicit code/price source/basis/adjustment scope required')
        if any(not isinstance(v, str) or not v for v in asset.values()):
            raise ValueError('Unknown asset scope cannot be filled')
        scope = dict(binding, code=code, **asset)
        for name in ('shares', 'sellable'):
            fields[f'holdings.{code}.{name}'] = ('whole', scope)
        for name in ('cash_claims', 'share_claims'):
            fields[f'entitlements.{code}.{name}'] = (name, scope)
    return fields


def _proof_gaps(data, path, declaration, scope, is_list):
    gaps = []
    ids = declaration.get('evidence_ids', [])
    if not isinstance(ids, list) or not ids:
        return ['SOURCE_EVIDENCE_REQUIRED']
    if any(not isinstance(eid, str) for eid in ids) or len(set(ids)) != len(ids):
        return ['INVALID_OR_DUPLICATE_EVIDENCE_REFERENCE']
    for eid in ids:
        evidence = data['evidence'].get(eid)
        if not isinstance(evidence, dict):
            gaps.append('EVIDENCE_REFERENCE_NOT_FOUND')
            continue
        if evidence.get('field') != path or evidence.get('scope') != scope:
            gaps.append('EVIDENCE_SCOPE_MISMATCH')
        if evidence.get('declared_value') != declaration.get('value'):
            gaps.append('EVIDENCE_VALUE_MISMATCH')
        if not evidence.get('locator'):
            gaps.append('EVIDENCE_LOCATOR_REQUIRED')
        if is_list and evidence.get('complete_outstanding_inventory') is not True:
            gaps.append('OUTSTANDING_INVENTORY_NOT_DECLARED_COMPLETE')
        try:
            if _time(evidence.get('as_of')) != _time(data['as_of']):
                gaps.append('EVIDENCE_AS_OF_MISMATCH')
        except (ValueError, TypeError):
            gaps.append('EVIDENCE_AS_OF_MISSING_OR_INVALID')
        try:
            if _time(evidence.get('available_at')) > _time(data['decision_at']):
                gaps.append('EVIDENCE_NOT_YET_AVAILABLE')
        except (ValueError, TypeError):
            gaps.append('EVIDENCE_AVAILABILITY_UNKNOWN')
        source = data['sources'].get(evidence.get('source_id'))
        if not isinstance(source, dict):
            gaps.append('SOURCE_REFERENCE_NOT_FOUND')
            continue
        if source.get('kind') != SOURCE_KIND:
            gaps.append('REAL_SOURCE_INTAKE_NOT_IMPLEMENTED')
        if not isinstance(source.get('sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', source['sha256']):
            gaps.append('SOURCE_FINGERPRINT_MISSING_OR_INVALID')
        try:
            if _time(source.get('available_at')) > _time(data['decision_at']):
                gaps.append('SOURCE_NOT_YET_AVAILABLE')
            if _time(evidence.get('available_at')) < _time(source.get('available_at')):
                gaps.append('EVIDENCE_PRECEDES_DECLARED_SOURCE_AVAILABILITY')
        except (ValueError, TypeError):
            gaps.append('SOURCE_OR_EVIDENCE_AVAILABILITY_UNKNOWN')
        try:
            _time(source.get('captured_at'))
        except (ValueError, TypeError):
            gaps.append('SOURCE_CAPTURE_TIME_UNKNOWN')
    return sorted(set(gaps))


def _value_gaps(data, kind, value):
    gaps, unsupported = [], []
    if kind in ('number', 'whole'):
        try:
            _number(value, whole=kind == 'whole')
        except ValueError:
            gaps.append('EXPLICIT_FINITE_NONNEGATIVE_VALUE_REQUIRED')
        return gaps, unsupported
    if not isinstance(value, list):
        return ['EXPLICIT_LIST_REQUIRED'], unsupported
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id']:
            gaps.append('ACCOUNT_ITEM_ID_REQUIRED')
            continue
        if kind == 'list':
            # Opaque legacy orders/payables are retained, never replayed here.
            continue
        if not item.get('event_id'):
            gaps.append('ENTITLEMENT_EVENT_ID_REQUIRED')
        try:
            if _time(item.get('entitlement_at')) > _time(data['as_of']):
                gaps.append('CLAIM_AFTER_OPENING_CUTOFF')
        except (ValueError, TypeError):
            gaps.append('ENTITLEMENT_TIME_UNKNOWN')
        if kind == 'cash_claims':
            if item.get('currency') != data['binding']['currency']:
                gaps.append('CLAIM_CURRENCY_MISMATCH')
            if item.get('payment_status') != 'OUTSTANDING':
                gaps.append('OUTSTANDING_PAYMENT_STATUS_REQUIRED')
            amount = item.get('amount_net')
            quantity_reason = 'NET_AMOUNT_UNKNOWN'
            date_fields = (('pay_date', 'PAYMENT_DATE_UNKNOWN'),)
        else:
            if item.get('delivery_status') != 'PENDING':
                gaps.append('PENDING_DELIVERY_STATUS_REQUIRED')
            amount = item.get('shares')
            quantity_reason = 'SHARE_QUANTITY_UNKNOWN'
            date_fields = (('delivery_date', 'DELIVERY_DATE_UNKNOWN'), ('tradable_date', 'TRADABLE_DATE_UNKNOWN'))
        try:
            number = _number(amount)
            if number == 0:
                gaps.append('NONPOSITIVE_OUTSTANDING_CLAIM')
            if kind == 'share_claims' and number != number.to_integral_value():
                unsupported.append('FRACTIONAL_SHARE_RIGHT_REPLAY_NOT_IMPLEMENTED')
        except ValueError:
            gaps.append(quantity_reason)
        parsed_dates = {}
        for field, reason in date_fields:
            try:
                parsed_dates[field] = _date(item.get(field))
            except (ValueError, TypeError):
                gaps.append(reason)
        if kind == 'share_claims' and len(parsed_dates) == 2 and parsed_dates['tradable_date'] < parsed_dates['delivery_date']:
            gaps.append('TRADABLE_BEFORE_DELIVERY')
    return sorted(set(gaps)), sorted(set(unsupported))


def check(data):
    """Diagnose declared synthetic evidence; never authenticate or mutate it."""
    if data.get('schema') != INPUT_SCHEMA or data.get('synthetic') is not True:
        raise ValueError('Only explicit synthetic opening-evidence input is supported')
    if data.get('clock_qualification') != 'EXPLICIT_SYNTHETIC_NOT_REAL_CLOSE':
        raise ValueError('Real opening/availability times are not inferred')
    if not _time(data['as_of']) <= _time(data['data_cutoff']) <= _time(data['decision_at']):
        raise ValueError('Require as_of <= data_cutoff <= decision_at')
    for name in ('declarations', 'evidence', 'sources'):
        if not isinstance(data.get(name), dict):
            raise ValueError('Explicit declarations/evidence/sources maps required')
    fields = _required(data)
    if set(data['declarations']) - set(fields):
        raise ValueError('Unknown declaration field; no implicit scope or schema migration')
    results, gaps, unsupported, item_paths = {}, [], [], {}
    for path, (kind, scope) in fields.items():
        declaration = data['declarations'].get(path)
        row = dict(classification='UNKNOWN', declared_value=None, diagnostic_value=None, evidence_ids=[], gaps=[])
        if declaration is None:
            row['gaps'] = ['MISSING_DECLARATION']
            results[path] = row
            continue
        if not isinstance(declaration, dict):
            raise ValueError('Declaration must be an explicit object')
        state, value = declaration.get('state'), declaration.get('value')
        row.update(declared_value=deepcopy(value), evidence_ids=deepcopy(declaration.get('evidence_ids', [])))
        if state == 'UNKNOWN' or state is None:
            row['gaps'] = ['UNKNOWN_DECLARATION']
        elif state not in ('SOURCE_DECLARED', 'HYPOTHETICAL_ASSUMPTION'):
            raise ValueError('Only UNKNOWN, SOURCE_DECLARED or HYPOTHETICAL_ASSUMPTION is allowed')
        else:
            row['gaps'], missing = _value_gaps(data, kind, value)
            unsupported.extend(dict(field=path, reason=reason) for reason in missing)
            if state == 'HYPOTHETICAL_ASSUMPTION':
                if not declaration.get('assumption_reason'):
                    row['gaps'].append('EXPLICIT_ASSUMPTION_REASON_REQUIRED')
                if declaration.get('evidence_ids'):
                    row['gaps'].append('ASSUMPTION_MUST_NOT_CLAIM_SOURCE_PROOF')
                if not row['gaps']:
                    row['classification'] = 'HYPOTHETICAL_ASSUMPTION'
            else:
                row['gaps'].extend(_proof_gaps(data, path, declaration, scope, kind not in ('number', 'whole')))
                if not row['gaps']:
                    zero = value == [] if isinstance(value, list) else _number(value) == 0
                    row['classification'] = 'SOURCED_ZERO_DECLARATION' if zero else 'SOURCED_NONZERO_DECLARATION'
                    row['diagnostic_value'] = deepcopy(value)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and isinstance(item.get('id'), str) and item['id']:
                    item_paths.setdefault(item['id'], []).append(path)
            if value and path in ('payables', 'pending_orders'):
                reason = 'OPENING_PAYABLE_REPLAY_NOT_IMPLEMENTED' if path == 'payables' else 'EXTERNAL_EXISTING_ORDER_REPLAY_NOT_IMPLEMENTED'
                unsupported.append(dict(field=path, reason=reason))
        results[path] = row
    for paths in item_paths.values():
        if len(paths) > 1:
            for path in paths:
                results[path]['gaps'].append('DUPLICATE_ACCOUNT_ITEM_ID')
    for code in data['assets']:
        physical, sellable = (results[f'holdings.{code}.{name}'] for name in ('shares', 'sellable'))
        if physical['diagnostic_value'] is not None and sellable['diagnostic_value'] is not None:
            if _number(sellable['diagnostic_value']) > _number(physical['diagnostic_value']):
                sellable['gaps'].append('SELLABLE_EXCEEDS_PHYSICAL_HOLDING')
    for path, row in results.items():
        row['gaps'] = sorted(set(row['gaps']))
        if row['gaps']:
            row.update(classification='UNKNOWN', diagnostic_value=None)
        gaps.extend(dict(field=path, reason=reason) for reason in row['gaps'])
    status = ('GAPS_PRESENT' if gaps else 'ASSUMPTIONS_PRESENT' if any(
        r['classification'] == 'HYPOTHETICAL_ASSUMPTION' for r in results.values()) else 'STRUCTURALLY_COMPLETE_NOT_AUTHENTICATED')
    serialized = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return dict(schema=SCHEMA, synthetic=True, research_only=True, status=status,
        input_id='sha256:'+hashlib.sha256(serialized.encode()).hexdigest(), binding=deepcopy(data['binding']),
        as_of=data['as_of'], data_cutoff=data['data_cutoff'], decision_at=data['decision_at'],
        fields=results, gaps=gaps, unsupported_capabilities=unsupported,
        authenticity_verified=False, opening_entitlements_verified=False,
        data_qualified=False, execution_model_qualified=False, historical_signal_eligible=False,
        policy_authorized=False, live_execution_authorized=False, primary_pressure_id=None,
        ledger_called=False, legacy_qualification_updates={}, cash_or_share_postings=[],
        usable_cash='NOT_COMPUTED_NO_LEDGER_CALL')
