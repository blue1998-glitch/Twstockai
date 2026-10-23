"""Pure source-only subsidiary IPO proposal binding; never a holder action ledger."""
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
import re

from . import capital_components as parent
from .action_scope import identify, verify, resolve_field
from .source_followup import compact, one, field, evidence_sha, roc, QUALIFICATION

SCHEMA = 'rotation-subsidiary-proposal-research/0.10'
PARENT_ID = 'sha256:673e0815cc9f1372ab187c7aa93c9a5ad1f746a45bf87ea4687d4b2e7be048f3'
MINUTES = 'tcc-egm-minutes-20261013'
VOTING = 'tcc-egm-voting-20261013'
PROVENANCE_SHA = '2e8b5bcd2c61f0ab963558d1fb66d801ae82492697eb8b4699b8da0e6dcaf36f'
NATIVE_SHA = {MINUTES: '009391559b2777d7003b4a8f2ac076416b66eee634361c208c85dae6d174cda0',
              VOTING: '0085499789e79cf719053d3c744f08f509bc7bfb3bbcac7c2d28b377927c0801'}


def parse_voting(text):
    s = compact(text)
    if not s.startswith('臺灣水泥股份有限公司'): raise ValueError('Wrong issuer')
    meeting = one(r'民國(\d+)年(\d+)月(\d+)日股東臨時會行使投票方式及投票表決結果', s)
    proposal = one(r'第一案本公司之子公司(.+?)擬於海外證券交易市場申請首次公開發行股票及掛牌交易案。', s)[1]
    if proposal != 'CimporInternationalHoldings': raise ValueError('Wrong subject entity')
    if '占出席股東表決權數%' not in s or '本案依表決結果,照案通過。' not in s:
        raise ValueError('Explicit voting denominator and approval required')
    votes = {}
    for key, label in [('for', '贊成權數'), ('against', '反對權數'), ('invalid', '無效權數'), ('abstained', '棄權與未投票權數')]:
        m = one(re.escape(label) + r':([\d,]+)權([\d.]+)%', s)
        count, pct = m[1].replace(',', ''), m[2]
        if not 0 <= Decimal(pct) <= 100: raise ValueError('Invalid published voting percentage')
        votes[key] = dict(voting_rights=count, rights_unit='VOTING_RIGHTS', percentage=pct,
                          percentage_unit='PERCENT_OF_ATTENDING_VOTING_RIGHTS_NOT_ALLOCATION')
    return dict(issuer_code='1101', issuer_name='臺灣水泥股份有限公司', meeting_date=roc(meeting.groups()),
        subject_entity='Cimpor International Holdings', instrument='SUBSIDIARY_EQUITY_AND_COMPANY_HOLDING_NOT_1101_HOLDER_GRANT',
        source_proposal_wording='擬於海外證券交易市場申請首次公開發行股票及掛牌交易案',
        phase='ISSUER_REPORTED_SUBSIDIARY_IPO_PROPOSAL_APPROVED', voting_body_meeting_ordinal=None,
        votes=votes, total_voting_rights=str(sum(int(v['voting_rights']) for v in votes.values())),
        percentage_sum=str(sum(Decimal(v['percentage']) for v in votes.values())),
        percentage_normalized=False)


def facts(source):
    v = parse_voting(source['native_evidence'][VOTING])
    manual = source['manifest']['visual_review']['manual_inventory']
    if (manual['p1']['meeting_date'] != v['meeting_date'] or manual['p1']['issuer_name'] != v['issuer_name']
            or manual['p1']['subject_entity'] != v['subject_entity']
            or manual['p4']['attending_voting_rights'] != v['total_voting_rights']
            or manual['p4']['vote_counts'] != {k: x['voting_rights'] for k, x in v['votes'].items()}
            or manual['p4']['for_percentage'] != v['votes']['for']['percentage']):
        raise ValueError('Manually reviewed minutes and native voting case mismatch')
    return dict(voting_native=v, minutes_scanned=dict(
        qualification='MANUAL_VISUAL_INVENTORY_NOT_NATIVE_PARSE', physical_pages=[1, 2, 3, 4],
        title_ordinal=manual['p1']['title_ordinal'], detail_clause_parser='NOT_IMPLEMENTED_INVENTORY_ONLY',
        proposal_locator='p1 第一案；p4 授權、不確定性與照原案表決通過',
        numeric_clause_fields_extracted=False),
        meeting_ordinal=dict(index_path_filename='第一次', minutes_p1='第二次', voting_body=None,
            canonical_meeting_ordinal=None, status='CONFLICT_PRESERVED_NOT_TWO_EVENTS'),
        relationship=dict(qualification='EXPLICIT_SOURCE_CASE_CROSS_REFERENCE_NOT_AUTOMATIC_EVENT_MERGE',
            source_ids=[MINUTES, VOTING], issuer_code=v['issuer_code'], meeting_date=v['meeting_date'],
            subject_entity=v['subject_entity'], numeric_ledger_events_added=0, independent_market_samples_added=0),
        unknown=dict(actual_effective_at=None, announced_at=None, completed_listing_at=None,
            final_issued_quantity=None, final_company_disposal_quantity=None, personal_cash=None,
            personal_shares=None, holder_dilution=None, zero_impact=None, net_cash=None, accounting_effect=None))


def observation(source, f):
    v = f['voting_native']; fs = {}
    def add(key, value, unit='TEXT', role='COMPANY_SUBSIDIARY_PROPOSAL_NOT_PERSONAL_RIGHT', manual=False):
        proofs = [] if value is None else [dict(source_id=MINUTES if manual else VOTING,
            physical_pdf_page=4 if manual else 1, locator='p4 授權事項及決議' if manual else '第一案／表決權數欄',
            evidence_kind='MANUAL_VISUAL_INVENTORY' if manual else 'NATIVE_TEXT',
            source_manifest_sha256=PROVENANCE_SHA, normalized_value=value)]
        fs[key] = field(value, unit, role, proofs, QUALIFICATION)
    add('meeting_date', v['meeting_date'], 'ISO_DATE', 'MEETING_NOT_ANNOUNCEMENT_OR_EFFECTIVE_DATE')
    add('subject_entity', v['subject_entity']); add('phase', v['phase'])
    add('authorization', 'APPROVED_PROPOSAL_CONTAINS_AUTHORIZATION_NOT_COMPLETION', manual=True)
    add('for_voting_rights', v['votes']['for']['voting_rights'], 'VOTING_RIGHTS', 'VOTE_COUNT_NOT_SHARES_GRANTED')
    add('for_percentage', v['votes']['for']['percentage'], v['votes']['for']['percentage_unit'], 'VOTE_PERCENT_NOT_ALLOCATION_DILUTION_OR_RETURN')
    add('canonical_meeting_ordinal', None)
    for name, value in f['unknown'].items():
        add(name, value, 'ISO_DATE' if name.endswith('_at') else 'UNKNOWN_NOT_DEFAULTED', 'UNKNOWN_NOT_INFERRED_FROM_PROPOSAL')
    return identify(dict(family='1101-subsidiary-ipo-20261013-source-case', issuer_code='1101',
        entitled_old_code='COMPANY_HELD_SUBSIDIARY_INTEREST_NOT_PERSONAL_1101',
        old_instrument=v['instrument'], action_type='SUBSIDIARY_IPO_PROPOSAL_SOURCE_RESEARCH',
        subject_entity=v['subject_entity'], source_ids=[MINUTES, VOTING], fields=fs,
        observed_at=source['manifest']['codex_analysis_observed_at'], announced_at=None,
        accounting_eligible=False, historical_signal_eligible=False))


def validate(catalog):
    verify(catalog)
    if catalog['schema'] != SCHEMA: raise ValueError('Explicit new source version required')
    parent.validate(catalog['parent_catalog'])
    if (catalog['parent_catalog_id'] != PARENT_ID or catalog['parent_catalog']['id'] != PARENT_ID
            or catalog['coverage'] != catalog['parent_catalog']['coverage']):
        raise ValueError('Exact complete parent0.9 and original incomplete coverage required')
    if any(catalog[k] != v for k, v in dict(historical_signal_eligible=False, primary_pressure_id=None, policy_authorized=False).items()):
        raise ValueError('Research-only flags required')
    source = catalog['source']; m = source['manifest']
    if evidence_sha(m) != PROVENANCE_SHA: raise ValueError('Actual source/visual/time provenance mismatch')
    for sid, text in source['native_evidence'].items():
        import hashlib
        if hashlib.sha256(text.encode()).hexdigest() != NATIVE_SHA.get(sid): raise ValueError('Native bytes mismatch')
    if set(source['native_evidence']) != {MINUTES, VOTING} or source['native_evidence'][MINUTES] != '\f' * 4:
        raise ValueError('Scanned empty extraction must stay formfeeds, not synthetic text')
    observed = datetime.fromisoformat(m['codex_analysis_observed_at'])
    for meta in m['official_captures'].values():
        times = [datetime.fromisoformat(meta[k]) for k in ['requested_at', 'completed_at', 'captured_at']]
        if any(t.tzinfo is None for t in times) or times != sorted(times) or times[-1] > observed:
            raise ValueError('Capture/read/analysis roles mismatch')
    if m['announced_at'] is not None or m['work_github_readback_at'] is not None:
        raise ValueError('Unavailable publication/Work readback cannot be filled')
    f = facts(source)
    if catalog['facts'] != f or catalog['observations'] != [observation(source, f)]:
        raise ValueError('Source, subject, instrument, stage, percentage, dates or unknowns promoted')
    return catalog


def resolve(catalog, name, request):
    validate(catalog)
    return resolve_field(catalog['observations'][0], name, request)


def qualify(data, catalog):
    validate(catalog)
    if data.get('subsidiary_proposal_catalog_id') != catalog['id']: raise ValueError('Exact new source catalog required')
    old = deepcopy(data); old.pop('subsidiary_proposal_catalog_id')
    return dict(deepcopy(parent.qualify(old, catalog['parent_catalog'])), subsidiary_proposal_catalog_id=catalog['id'])
