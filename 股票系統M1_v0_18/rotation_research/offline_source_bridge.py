"""Pure source bridge 0.6. Exact parent 0.5; no IO or accounting replay."""
from copy import deepcopy
from datetime import date, datetime
import hashlib
import re

from .action_scope import identify, verify, resolve_field
from . import source_diagnostics as parent

SCHEMA = 'rotation-offline-source-bridge/0.6'
QUALIFICATION = parent.QUALIFICATION
TAX_TITLE = '一51公司將資本公積以現金方式發給股東之課稅規定'


def parse_suspension(text, issuer_code, instrument):
    """Extract document date and explicit START; no end-date inference."""
    if instrument != issuer_code + '_ORDINARY_OLD_SHARES':
        raise ValueError('Explicit ordinary-share instrument required')
    s = re.sub(r'\s+', '', text).replace('：', ':')
    codes = set(re.findall(r'公司代號:([0-9]+)', s))
    ordinary = set(re.findall(r'上市普通股自(\d+)年(\d+)月(\d+)日起暫停交易', s))
    dates = set(re.findall(r'自(\d+)年(\d+)月(\d+)日起暫停交易', s))
    doc = re.match(r'中華民國(\d+)年(\d+)月(\d+)日', s)
    if codes != {issuer_code} or len(dates) != 1 or ordinary != dates or not doc:
        raise ValueError('Wrong issuer or missing/unambiguous suspension-start/date wording')
    def iso(parts):
        y, m, d = map(int, parts)
        return date(y + 1911, m, d).isoformat()
    start, document = iso(next(iter(dates))), iso(doc.groups())
    if document > start:
        raise ValueError('Document date after stated suspension start')
    return dict(issuer_code=issuer_code, old_instrument=instrument,
        document_date=document, suspension_start_date=start, suspension_end_date=None,
        announced_at=None, historical_signal_eligible=False)


def parse_mof_api(payload, expected_content_sha256):
    """Actual API's slash-form citation; old synthetic parser stays unchanged.

    The semantic projection excludes ViewCount; archived response bytes are
    independently pinned by the external reader. New captures are new versions.
    """
    if payload.get('Code') != '1' or len(payload.get('Data', {}).get('Table', [])) != 1:
        raise ValueError('One successful official interpretation row required')
    row = payload['Data']['Table'][0]
    expected = dict(TaxAct='所得稅法', TaxVer='一一四年版', Title=TAX_TITLE,
        Article='第十四條（各類所得之計算）', Terms=1, Subsection=51)
    if any(row.get(k) != v or type(row.get(k)) is not type(v) for k, v in expected.items()):
        raise ValueError('Wrong tax act/edition/title/article/terms/subsection')
    content = row.get('Content')
    if (not isinstance(content, str) or '財政部101/08/17台財稅字第10100097670號令' not in content
            or hashlib.sha256(content.encode()).hexdigest() != expected_content_sha256):
        raise ValueError('Interpretation content/citation does not match this source version')
    return dict(expected, Content=content, Content_sha256=expected_content_sha256,
        qualification='GENERAL_LAW_CONTEXT_NOT_PERSONAL_NET', issuer_funding_subtype=None,
        personal_tax_residency=None, personal_tax=None, nhi=None, fees=None,
        personal_net_cash=None, actual_receipt=None, historical_signal_eligible=False)


def validate(catalog):
    verify(catalog)
    if catalog['schema'] != SCHEMA:
        raise ValueError('Explicit bridge source version 0.6 required')
    p = parent.validate(catalog['parent_catalog'])
    if catalog['parent_catalog_id'] != p['id'] or catalog['coverage'] != p['coverage']:
        raise ValueError('Exact parent 0.5 and incomplete coverage required')
    if (catalog['historical_signal_eligible'] is not False
            or catalog['primary_pressure_id'] is not None or catalog['policy_authorized'] is not False):
        raise ValueError('Research qualifications cannot be promoted')
    seen = set()
    for obs in catalog['observations']:
        verify(obs)
        if obs['id'] in seen:
            raise ValueError('Duplicate bridge observation')
        seen.add(obs['id'])
        if obs['action_type'] == 'SECURITY_SUSPENSION_START_NOTICE':
            code = obs['issuer_code']
            if (code not in p['coverage'] or obs['entitled_old_code'] != code
                    or obs['old_instrument'] != code + '_ORDINARY_OLD_SHARES'):
                raise ValueError('Suspension identity/instrument mismatch')
            if obs['fields']['suspension_end_date']['value'] is not None:
                raise ValueError('Start notice cannot infer an end date')
            for name, role in [('document_date', 'SOURCE_DOCUMENT_DATE_NOT_PUBLICATION'),
                    ('suspension_start_date', 'SECURITY_SUSPENSION_START_NOT_END'),
                    ('suspension_end_date', 'SUSPENSION_END_NOT_AUTHENTICATED')]:
                if obs['fields'][name]['unit'] != 'ISO_DATE' or obs['fields'][name]['date_role'] != role:
                    raise ValueError('Suspension document/start/end roles cannot be interchanged')
            document = date.fromisoformat(obs['fields']['document_date']['value'])
            start = date.fromisoformat(obs['fields']['suspension_start_date']['value'])
            if document > start:
                raise ValueError('Document date after suspension start')
        elif obs['action_type'] == 'GENERAL_TAX_INTERPRETATION':
            if (obs['issuer_code'], obs['entitled_old_code'], obs['old_instrument']) != (
                    'GENERAL', 'NOT_INVESTOR_SPECIFIC', 'NOT_AN_ENTITLEMENT'):
                raise ValueError('General law cannot become issuer or investor facts')
        else:
            raise ValueError('Unsupported bridge observation')
        if obs['announced_at'] is not None or obs['accounting_eligible'] is not False or obs['historical_signal_eligible'] is not False:
            raise ValueError('No authenticated historical signal or net-account eligibility')
        observed = datetime.fromisoformat(obs['observed_at'])
        if observed.tzinfo is None:
            raise ValueError('Explicit observation timezone required')
        for sid in obs['source_ids']:
            source = catalog['sources'][sid]
            captured = datetime.fromisoformat(source['captured_at'])
            ingested = datetime.fromisoformat(source['ingested_at'])
            if captured.tzinfo is None or ingested.tzinfo is None or not captured <= ingested <= observed:
                raise ValueError('Capture, ingestion and observation times must remain separate/ordered')
        for name, f in obs['fields'].items():
            if f['qualification'] != QUALIFICATION:
                raise ValueError('No bridge field is final-ledger eligible')
            if name in parent.NULL_ONLY_FIELDS | {'issuer_funding_subtype', 'personal_tax_residency',
                    'personal_tax', 'nhi', 'fees', 'personal_net_cash'} and f['value'] is not None:
                raise ValueError('Personal net and issuer tax-source details remain unknown')
            if f['value'] is not None and not f['proofs']:
                raise ValueError('Known value needs source proof')
            for proof in f['proofs']:
                if proof['source_id'] not in obs['source_ids'] or proof['source_id'] not in catalog['sources']:
                    raise ValueError('Proof outside observation source chain')
    return catalog


def resolve(catalog, name, request):
    validate(catalog)
    matches = [o for o in catalog['observations'] if o['id'] == request.get('version_id')]
    if len(matches) != 1:
        raise ValueError('One explicit new source observation required')
    return resolve_field(matches[0], name, request)


def quote_diagnostic(catalog, code, when, raw_close, market_session):
    validate(catalog)
    prior = parent.quote_diagnostic(catalog['parent_catalog'], code, when, raw_close, market_session)
    starts = [o['id'] for o in catalog['observations']
        if o['action_type'] == 'SECURITY_SUSPENSION_START_NOTICE' and o['issuer_code'] == code
        and o['fields']['suspension_start_date']['value'] == when]
    result = dict(deepcopy(prior), schema='rotation-security-quote-diagnostic/0.2',
        parent_diagnostic=prior, bridge_catalog_id=catalog['id'],
        direct_suspension_start_observation_ids=starts, suspension_end_date=None,
        security_tradable=False if starts else prior['security_tradable'])
    if starts:
        result['security_session_status'] = 'OFFICIAL_SECURITY_SUSPENSION_START_DATE_ONLY'
        if raw_close is None:
            result['new_missing_explanation'] = 'DIRECT_OFFICIAL_SUSPENSION_START_ON_DATE'
    return result


def qualify(data, catalog):
    validate(catalog)
    if data.get('bridge_catalog_id') != catalog['id']:
        raise ValueError('Explicit bridge catalog binding required')
    old_input = deepcopy(data); old_input.pop('bridge_catalog_id')
    prior = parent.qualify(old_input, catalog['parent_catalog'])
    return dict(deepcopy(prior), schema='rotation-source-bridge-qualification/0.1',
        input_id=identify(data)['id'], bridge_catalog_id=catalog['id'],
        bridge_parent_qualification=prior,
        bridge_limits=['SUSPENSION_START_NOT_END_VALUATION_OR_EXECUTION_POLICY',
            'DIRECT_LAW_NOT_ISSUER_FUNDING_OR_PERSONAL_NET',
            'SOURCE_ACTION_COVERAGE_NET_RECEIPT_AND_OPENING_ENTITLEMENTS_STILL_MISSING'])
