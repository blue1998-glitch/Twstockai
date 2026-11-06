"""Pure evidence binding and fail-closed ledger admission; no IO or policy.

Issuer, entitled old instrument, event version, field role and observation time
are independent. A target-holder exchange cannot credit acquirer old holders.
"""
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation, localcontext
from graph_core.core import fingerprint
from .action_ledger import qualify, replay

SCHEMA = 'rotation-scoped-action-catalog/0.3'


def identify(value):
    result = deepcopy(value)
    result.pop('id', None)
    result['id'] = fingerprint(result)
    return result


def verify(value):
    if value.get('id') != fingerprint({k: v for k, v in value.items() if k != 'id'}):
        raise ValueError('Evidence fingerprint mismatch')


def per_old_share(value, denominator):
    if not isinstance(value, str) or not isinstance(denominator, str):
        raise ValueError('Explicit decimal strings required')
    try:
        a, b = Decimal(value), Decimal(denominator)
        if not a.is_finite() or not b.is_finite() or a < 0 or b <= 0:
            raise ValueError('Invalid published share unit')
        with localcontext() as context:
            context.prec = 60
            return format(a / b, 'f')
    except InvalidOperation as exc:
        raise ValueError('Invalid decimal share unit') from exc


def resolve_field(version, field, request):
    """One explicit version only; never select latest or borrow another case.

    This returns sourced facts for diagnostics. FINAL_LEDGER usage additionally
    requires final-field qualification, which these partial archives lack.
    """
    verify(version)
    if field not in version['fields']:
        raise ValueError('Unknown evidence field')
    bound = version['fields'][field]
    expected = {k: version[k] for k in ('family', 'issuer_code', 'entitled_old_code', 'action_type', 'old_instrument')}
    expected.update(version_id=version['id'], field=field,
                    date_role=bound['date_role'], unit=bound['unit'])
    if any(request.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong holder/event/version/instrument/date role/unit')
    as_of = request.get('observed_as_of')
    if not as_of:
        raise ValueError('Explicit observation cutoff required')
    cutoff = datetime.fromisoformat(as_of)
    if cutoff.tzinfo is None:
        raise ValueError('Observation cutoff needs an explicit timezone')
    if cutoff < datetime.fromisoformat(version['observed_at']):
        raise ValueError('Evidence not yet observed at requested cutoff')
    if request.get('historical_signal') or version['historical_signal_eligible']:
        raise ValueError('Historical availability not authenticated')
    purpose = request.get('purpose')
    if purpose not in ('SOURCE_DIAGNOSTIC', 'FINAL_LEDGER'):
        raise ValueError('Explicit evidence purpose required')
    if purpose == 'FINAL_LEDGER' and bound['qualification'] != 'VERIFIED_FINAL_LEDGER_FIELD':
        raise ValueError('Proposal/schedule/published precision is not final ledger qualification')
    if bound['value'] is None:
        raise ValueError('Unknown field cannot be defaulted to zero')
    if not bound['proofs']:
        raise ValueError('Unbound field source')
    return deepcopy(bound)


def required_inventory(catalog, code):
    return sorted(v['id'] for v in catalog['inventory'] if code in v['company_codes'])


def scope_findings(data, catalog):
    verify(catalog)
    if catalog['schema'] != SCHEMA:
        raise ValueError('Explicit scoped catalog version required')
    for v in catalog['inventory']:
        verify(v)
    if data['events'] != catalog['events']:
        raise ValueError('Ledger event components must bind exact catalog version')
    findings = []
    def add(reason, **evidence):
        findings.append(dict(reason=reason, **evidence))
    for code in data['assets']:
        if code not in catalog['coverage']:
            raise ValueError('Unknown code outside source coverage')
        coverage = data['coverage'].get(code, {})
        ids = required_inventory(catalog, code)
        if coverage.get('known_company_action_ids') != ids:
            add('KNOWN_COMPANY_ACTION_INVENTORY_MISSING:' + code, required_ids=ids)
        if catalog['coverage'][code]['status'] != 'VERIFIED_COMPLETE':
            add('SOURCE_ACTION_COVERAGE_INCOMPLETE:' + code,
                gaps=deepcopy(catalog['coverage'][code]['gaps']))
    for v in catalog['inventory']:
        when = v['fields'].get('scheduled_effective_date', {}).get('value')
        if (v['action_type'] == 'SHARE_EXCHANGE' and when
                and data['start'] <= when <= data['end']
                and set(v['company_codes']) & set(data['assets'])):
            add('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED', inventory_id=v['id'],
                issuer_code=v['issuer_code'], entitled_old_code=v['entitled_old_code'],
                ledger_supported=False, existing_acquirer_share_grant=None,
                scope='TARGET_HOLDER_EXCHANGE_NOT_ACQUIRER_STOCK_DIVIDEND',
                source_ids=v['source_ids'])
    for e in data['events']:
        if not data['start'] < e['ex_date'] <= data['end']:
            continue
        if e['type'] == 'CASH_DIVIDEND':
            add('FINAL_CASH_DISTRIBUTION_NATURE_UNVERIFIED:' + e['id'],
                legacy_component_type=e['type'], final_funding_source=None,
                net_tax_fee_model=None, code=e['code'])
        if e['type'] == 'STOCK_DIVIDEND':
            add('FINAL_ALLOTMENT_AND_FRACTION_DISPOSITION_UNKNOWN:' + e['id'])
    return findings


def admit_and_replay(data, catalog):
    """Check catalog evidence in addition to the unchanged numeric contract.

    Incomplete company inventories cannot be promoted by changing input flags.
    Missing-account evidence blocks all daily/net calculations.
    """
    findings = scope_findings(data, catalog)
    reasons = sorted(set(qualify(data) + [x['reason'] for x in findings]))
    if not reasons:
        result = replay(data)
        return dict(result, scope_catalog_id=catalog['id'], scope_findings=findings,
                    source_admission='QUALIFIED_WITH_EXPLICIT_SCOPE')
    return dict(schema='rotation-scope-ledger-result/0.1', input_id=fingerprint(data),
                scope_catalog_id=catalog['id'], status='REFUSED_INCOMPLETE_EVENT_ACCOUNTING',
                start=data['start'], end=data['end'], refusal_reasons=reasons,
                scope_findings=findings, daily=[], journal=[], total_net_return=None,
                scenario_net_return=None, actual_realized_investor_return=None,
                original_numeric_replay_called=False, policy_authorized=False,
                historical_signal_eligible=False, primary_pressure_id=None)
