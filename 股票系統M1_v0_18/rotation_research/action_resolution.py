"""Pure, explicit resolution diagnostics. No ledger replay or source IO.

The approved ratio can be previewed for a named hypothetical entitlement.
It is never a final payout, tax calculation, opening balance or investor return.
"""
from copy import deepcopy
from decimal import Decimal, ROUND_DOWN, localcontext
import re

from .action_scope import identify, verify, resolve_field, scope_findings
from .action_ledger import qualify

SCHEMA = 'rotation-resolution-catalog/0.4'
ROUNDING = 'PER_ORDINARY_SHAREHOLDER_TOTAL_CASH_DROP_SUB_TWD'


def validate(catalog):
    verify(catalog)
    if catalog['schema'] != SCHEMA:
        raise ValueError('Explicit resolution catalog 0.4 required')
    parent = catalog['parent_catalog']
    verify(parent)
    if parent['schema'] != 'rotation-scoped-action-catalog/0.3':
        raise ValueError('Exact parent catalog 0.3 required')
    if catalog['parent_catalog_id'] != parent['id']:
        raise ValueError('Parent identity mismatch')
    if catalog['events'] != parent['events']:
        raise ValueError('Original ledger components must remain exact')
    if catalog['inventory'][:len(parent['inventory'])] != parent['inventory']:
        raise ValueError('Original source versions must remain exact')
    if len({v['id'] for v in catalog['inventory']}) != len(catalog['inventory']):
        raise ValueError('Duplicate inventory identity')
    for v in catalog['inventory']:
        verify(v)
        for f in v['fields'].values():
            for proof in f['proofs']:
                if proof['source_id'] not in v['source_ids'] or proof['source_id'] not in catalog['sources']:
                    raise ValueError('Field proof outside bound source')
    for code in parent['coverage']:
        if catalog['coverage'][code]['status'] != 'INCOMPLETE':
            raise ValueError('Resolution evidence does not prove complete coverage')
        if catalog['coverage'][code]['known_company_action_ids'] != required_inventory(catalog, code):
            raise ValueError('Known inventory omitted')


def required_inventory(catalog, code):
    return sorted(v['id'] for v in catalog['inventory'] if code in v['company_codes'])


def explicit_version(catalog, version_id):
    validate(catalog)
    versions = [v for v in catalog['inventory'] if v['id'] == version_id]
    if len(versions) != 1:
        raise ValueError('One explicit source version required; no latest selection')
    return versions[0]


def resolve(catalog, field, request):
    return resolve_field(explicit_version(catalog, request.get('version_id')), field, request)


def preview_shareholder_cash(catalog, request, entitlement):
    """Hypothetical gross amount only, using the approved (adjustable) ratio.

    Quantity is a decimal string of whole entitled shares, not a trade size or
    a current holding. No investor identifiers or private documents are needed.
    """
    version = explicit_version(catalog, request.get('version_id'))
    if (version['action_type'] != 'CASH_DISTRIBUTION_RESOLUTION'
            or version['stage'] != 'SHAREHOLDER_APPROVED_ADJUSTABLE'
            or request.get('purpose') != 'SOURCE_DIAGNOSTIC'):
        raise ValueError('Approved resolution diagnostic only')
    ratio = resolve(catalog, 'approved_cash_per_share', request)
    rounding_request = dict(request, field='rounding_scope', unit='POLICY', date_role='PER_HOLDER_TOTAL_CASH')
    rounding = resolve(catalog, 'rounding_scope', rounding_request)
    if rounding['value'] != ROUNDING:
        raise ValueError('Unsupported per-holder rounding policy')
    if (entitlement.get('kind') != 'HYPOTHETICAL_ENTITLED_SHARES'
            or not isinstance(entitlement.get('assumption'), str)
            or not entitlement['assumption'].strip()
            or entitlement.get('issuer_code') != version['issuer_code']
            or entitlement.get('old_instrument') != version['old_instrument']
            or entitlement.get('version_id') != version['id']):
        raise ValueError('Explicit version-bound hypothetical entitlement required')
    quantity = entitlement.get('shares')
    if not isinstance(quantity, str) or not re.fullmatch(r'\d{1,30}', quantity):
        raise ValueError('Whole entitled shares required as a decimal string (max 30 digits)')
    rate = ratio['value']
    if not isinstance(rate, str) or not re.fullmatch(r'\d{1,30}(?:\.\d{1,30})?', rate):
        raise ValueError('Finite nonnegative approved decimal rate required')
    with localcontext() as ctx:
        ctx.prec = 100
        gross = Decimal(quantity) * Decimal(rate)
        rounded = gross.quantize(Decimal('1'), rounding=ROUND_DOWN)
        result = dict(schema='rotation-resolution-gross-preview/0.1',
            source_version_id=version['id'], status='HYPOTHETICAL_APPROVED_RATIO_GROSS_ONLY',
            entitlement=deepcopy(entitlement), approved_ratio=rate,
            unrounded_shareholder_gross_twd=format(gross, 'f'),
            rounded_shareholder_gross_twd=format(rounded, 'f'),
            rounding_remainder_twd=format(gross - rounded, 'f'),
            rounding_scope=ROUNDING, final_after_adjustments_verified=False,
            tax_twd=None, fees_twd=None, net_cash_twd=None, net_cash_per_share=None,
            actual_investor_receipt=None, record_date=None, pay_date=None,
            opening_entitlement_verified=False, total_net_return=None,
            historical_signal_eligible=False, primary_pressure_id=None, policy_authorized=False)
    return identify(result)


def refuse_accounting(data, catalog):
    """Source qualification only. This adapter deliberately has no replay path."""
    validate(catalog)
    if data.get('resolution_catalog_id') != catalog['id']:
        raise ValueError('Input must bind explicit resolution catalog')
    parent_data = deepcopy(data)
    findings = []
    for code in data['assets']:
        required = required_inventory(catalog, code)
        if data['coverage'].get(code, {}).get('known_company_action_ids') != required:
            findings.append(dict(reason='RESOLUTION_INVENTORY_MISSING:' + code, required_ids=required))
        # The unchanged 0.3 validator sees its exact historical inventory. The
        # new inventory was independently checked above; no new item is hidden.
        parent_data['coverage'][code]['known_company_action_ids'] = required_inventory(catalog['parent_catalog'], code)
    findings.extend(scope_findings(parent_data, catalog['parent_catalog']))
    findings.append(dict(reason='RESOLUTION_GROSS_PREVIEW_NOT_FINAL_NET_LEDGER_INPUT',
        approved_resolution_not_final_ratio=True, holder_rounding_not_net_per_share=True,
        tax_fee_model=None, investor_receipt=None, opening_entitlements=None))
    for v in catalog['inventory'][len(catalog['parent_catalog']['inventory']):]:
        if v['action_type'] == 'TREASURY_REPURCHASE_REPORT':
            findings.append(dict(reason='TREASURY_TRANCHE_NOT_HOLDER_CAPITAL_REDUCTION',
                inventory_id=v['id'], cancellation_effective_date=None,
                holder_conversion_ratio=None, holder_cashflow=None,
                scope='OBSERVED_COMPANY_REPORT_NOT_EXHAUSTIVE_COVERAGE'))
    reasons = sorted(set(qualify(parent_data) + [f['reason'] for f in findings]))
    return dict(schema='rotation-resolution-qualification/0.1', status='REFUSED_INCOMPLETE_EVENT_ACCOUNTING',
        input_id=identify(data)['id'], resolution_catalog_id=catalog['id'],
        start=data['start'], end=data['end'], refusal_reasons=reasons, source_findings=findings,
        daily=[], journal=[], total_net_return=None, scenario_net_return=None,
        actual_realized_investor_return=None, original_numeric_replay_called=False,
        historical_signal_eligible=False, primary_pressure_id=None, policy_authorized=False)
