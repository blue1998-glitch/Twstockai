"""Pure, additive source diagnostics. No IO, price filling or ledger replay.

New observations never rewrite a parent's UNKNOWN, coverage or source version.
All values are retrospective document facts, not investor accounting inputs.
"""
from copy import deepcopy
from datetime import date

from .action_scope import identify, verify, resolve_field
from .action_resolution import validate as validate_parent, refuse_accounting

SCHEMA = 'rotation-source-diagnostics/0.5'
QUALIFICATION = 'SOURCE_DIAGNOSTIC_ONLY_NOT_LEDGER'
SCOPES = {
    'SECURITY_RESUMPTION_NOTICE': ('1101', '1101', '1101_ORDINARY_OLD_SHARES'),
    'SECURITY_SUSPENSION_NOTICE': None,  # Explicit security identity, no market-wide closure.
    'SHARE_EXCHANGE_EXPECTED_ISSUANCE': ('2884', '2867', '2867_ORDINARY_OLD_SHARES'),
    'EMPLOYEE_CAPITAL_REGISTRATION': ('2884', 'EMPLOYEE_RECIPIENTS', 'EMPLOYEE_REMUNERATION_RIGHTS'),
    'ISSUER_DISTRIBUTION_COMPLETION_REPORT': ('2884', '2884', '2884_ORDINARY_OLD_SHARES'),
    'GENERAL_TAX_INTERPRETATION': ('GENERAL', 'NOT_INVESTOR_SPECIFIC', 'NOT_AN_ENTITLEMENT'),
}
NULL_ONLY_FIELDS = {
    'net_cash_per_share', 'investor_net_cash', 'actual_investor_receipt', 'investor_tax',
    'investor_nhi', 'investor_fees', 'actual_issued_shares', 'listing_date',
    'opening_entitlement', 'final_cash_per_share', 'existing_2884_share_grant',
}


def validate(catalog):
    verify(catalog)
    if catalog['schema'] != SCHEMA:
        raise ValueError('Explicit source diagnostics version 0.5 required')
    parent = catalog['parent_catalog']
    validate_parent(parent)
    if catalog['parent_catalog_id'] != parent['id'] or catalog['coverage'] != parent['coverage']:
        raise ValueError('Exact parent identity and incomplete coverage must remain')
    if (catalog['historical_signal_eligible'] is not False
            or catalog['primary_pressure_id'] is not None or catalog['policy_authorized'] is not False):
        raise ValueError('Research qualifications must remain unknown/unauthorized')
    ids = set()
    for obs in catalog['observations']:
        verify(obs)
        if obs['id'] in ids:
            raise ValueError('Duplicate observation identity')
        ids.add(obs['id'])
        kind = obs['action_type']
        if kind not in SCOPES:
            raise ValueError('Unknown document scope')
        expected = SCOPES[kind]
        if expected and tuple(obs[k] for k in ('issuer_code', 'entitled_old_code', 'old_instrument')) != expected:
            raise ValueError('Wrong recipient/instrument for document scope')
        if kind == 'SECURITY_SUSPENSION_NOTICE':
            if (obs['issuer_code'] != obs['entitled_old_code']
                    or obs['old_instrument'] != obs['issuer_code'] + '_ORDINARY_OLD_SHARES'):
                raise ValueError('Suspension is security-specific')
        if obs['historical_signal_eligible'] is not False or obs['accounting_eligible'] is not False:
            raise ValueError('Document observation cannot authorize accounting/history')
        if obs['announced_at'] is not None:
            raise ValueError('Historical public availability not authenticated')
        for name, field in obs['fields'].items():
            if field['qualification'] != QUALIFICATION:
                raise ValueError('Source diagnostics cannot become final ledger fields')
            if name in NULL_ONLY_FIELDS and field['value'] is not None:
                raise ValueError('Personal net/final allotment/listing still unknown')
            if field['value'] is not None and not field['proofs']:
                raise ValueError('Known fact requires bound proof')
            for proof in field['proofs']:
                sid = proof['source_id']
                if sid not in obs['source_ids'] or sid not in catalog['sources']:
                    raise ValueError('Proof outside bound usable source')
    return catalog


def resolve(catalog, field, request):
    """Reuse the established exact identity/unit/date-role/observation gate."""
    validate(catalog)
    matches = [o for o in catalog['observations'] if o['id'] == request.get('version_id')]
    if len(matches) != 1:
        raise ValueError('One explicit observation required; no latest selection')
    return resolve_field(matches[0], field, request)


def quote_diagnostic(catalog, code, when, raw_close, market_session):
    """A null quote stays null even after a suspension explanation is sourced.

    A resumption notice does not state the start of a suspension. The function
    never extrapolates a one-day source to a full period or from another stock.
    """
    validate(catalog)
    date.fromisoformat(when)
    if code not in catalog['coverage'] or (market_session is not None and type(market_session) is not bool):
        raise ValueError('Explicit covered security and market-session fact required')
    suspended = []
    resumptions = []
    for obs in catalog['observations']:
        if obs['issuer_code'] != code:
            continue
        f = obs['fields']
        if obs['action_type'] == 'SECURITY_SUSPENSION_NOTICE' and f['suspension_date']['value'] == when:
            suspended.append(obs['id'])
        if obs['action_type'] == 'SECURITY_RESUMPTION_NOTICE':
            resumptions.append(dict(observation_id=obs['id'], resume_date=f['resume_date']['value'],
                role='RELATED_NOTICE_NOT_PROOF_OF_MISSING_DAY_SUSPENSION_START'))
    return dict(schema='rotation-security-quote-diagnostic/0.1', code=code, date=when,
        market_session=market_session, raw_close=raw_close,
        old_missing_cause='UNKNOWN' if raw_close is None else None,
        new_missing_explanation=('OFFICIAL_SECURITY_SUSPENSION_ON_DATE' if suspended else 'UNKNOWN') if raw_close is None else None,
        suspension_observation_ids=suspended, related_resumption_notices=resumptions,
        security_session_status='OFFICIAL_SUSPENSION_ON_DATE' if suspended else 'UNKNOWN_NOT_INFERRED_FROM_MARKET_CALENDAR',
        security_tradable=False if suspended else None,
        execution_qualified=False, execution_note='NO_EXECUTION_OR_VALUATION_POLICY_IN_SOURCE_DIAGNOSTICS',
        imputed_close=None, valuation=None, missing_quote_blocks_accounting=raw_close is None,
        historical_signal_eligible=False, primary_pressure_id=None, policy_authorized=False)


def qualify(data, catalog):
    """Delegate unchanged 0.4 refusal and append source boundaries, never replay."""
    validate(catalog)
    if data.get('source_diagnostics_catalog_id') != catalog['id']:
        raise ValueError('Explicit source diagnostics catalog required')
    parent_data = deepcopy(data)
    parent_data.pop('source_diagnostics_catalog_id')
    parent_result = refuse_accounting(parent_data, catalog['parent_catalog'])
    result = deepcopy(parent_result)
    result.update(schema='rotation-source-diagnostics-qualification/0.1',
        input_id=identify(data)['id'], source_diagnostics_catalog_id=catalog['id'],
        parent_qualification=parent_result,
        diagnostic_limits=['SUSPENSION_NOT_MARKET_HOLIDAY_OR_VALUATION_POLICY',
            'EMPLOYEE_AND_TARGET_HOLDER_SHARES_NOT_OLD_2884_ALLOTMENT',
            'REGISTRATION_RECORD_EX_LISTING_AND_PAYMENT_DATES_NOT_INTERCHANGEABLE',
            'EXPECTED_ISSUE_NOT_COMPLETION', 'ISSUER_PAYMENT_NOT_PERSONAL_NET_RECEIPT',
            'GENERAL_TAX_INTERPRETATION_NOT_PERSONAL_EXEMPTION',
            'SOURCE_COVERAGE_REMAINS_INCOMPLETE_NOT_OVERRIDDEN_BY_INPUT_FLAGS'])
    return result
