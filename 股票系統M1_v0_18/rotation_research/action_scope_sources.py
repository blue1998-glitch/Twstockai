"""Offline source-review integration; writes only independent v0.3 artifacts."""
from copy import deepcopy
from datetime import date, datetime, timezone, timedelta
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from .action_sources import HERE, ROOT, dump
from .official_actions import build as build_v02
from .action_scope import SCHEMA, identify, per_old_share, admit_and_replay, required_inventory
from .action_study import verified_quotes, candidate_input
from .source_qualification import build_calendar, bind_observed_calendar

REVIEW = HERE / 'source_review_20261022'
OUT = HERE / 'action_scope_20261023'
ORIGINS = {'esun-direct-2025-ratio': 'www.esunbank.com',
           'esun-mna-20251105': 'www.esunbank.com', 'esun-mna-20260713': 'www.esunbank.com',
           'esun-mna-index': 'www.esunfhc.com', 'esun-mna-qa': 'www.esunbank.com',
           'tcc-capital-surplus-2026': 'www.tccgroupholdings.com'}


def compact(text):
    return re.sub(r'\s+', '', text)


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip = 0; self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def load_review(review=REVIEW):
    """Validate all archived bytes, metadata, derived text and actual links."""
    review = Path(review)
    manifest = json.loads((review / 'source-manifest.json').read_text())
    sources, texts, originals = {}, {}, {}
    for sid, origin in ORIGINS.items():
        m = manifest[sid]
        meta = json.loads((review / 'raw' / (sid + '.meta.json')).read_text())
        for key in ('url', 'captured_at', 'status', 'http', 'sha256', 'bytes', 'final_url'):
            if m[key] != meta[key]:
                raise ValueError('Source manifest/meta mismatch: ' + sid)
        if m['status'] != 'CAPTURED' or m['http'] != 200:
            raise ValueError('Failed source is not usable: ' + sid)
        if any(urlsplit(m[k]).scheme != 'https' or urlsplit(m[k]).netloc != origin for k in ('url', 'final_url')):
            raise ValueError('Wrong official source origin: ' + sid)
        body = (review / 'raw' / (sid + '.response')).read_bytes()
        text = (review / 'raw' / (sid + '.txt')).read_bytes()
        extraction = json.loads((review / 'raw' / (sid + '.extraction.json')).read_text())
        if (len(body) != m['bytes'] or hashlib.sha256(body).hexdigest() != m['sha256']
                or hashlib.sha256(text).hexdigest() != m['derived_text_sha256']
                or extraction['text_sha256'] != m['derived_text_sha256']
                or extraction.get('pdf_sha256', extraction.get('source_sha256')) != m['sha256']):
            raise ValueError('Source/text fingerprint mismatch: ' + sid)
        if 'pdf' in m['content_type']:
            if not body.startswith(b'%PDF-'):
                raise ValueError('Invalid source PDF')
        else:
            parser = VisibleText(); parser.feed(body.decode('utf-8-sig'))
            # HTMLParser layout may vary, but all visible non-space content must agree.
            if compact(''.join(parser.parts)) != compact(text.decode('utf-8-sig')):
                raise ValueError('HTML visible-text/source mismatch: ' + sid)
        sources[sid] = dict(path=str((REVIEW / 'raw' / (sid + '.response')).relative_to(ROOT)),
            url=m['url'], captured_at=m['captured_at'], sha256=m['sha256'], kind='OFFICIAL_ARCHIVE',
            derived_text_path=str((REVIEW / 'raw' / (sid + '.txt')).relative_to(ROOT)),
            derived_text_sha256=m['derived_text_sha256'], historical_publication_time='NOT_AUTHENTICATED')
        texts[sid] = text.decode('utf-8-sig'); originals[sid] = body
    for sid in ('esun-mna-20251105', 'esun-mna-20260713', 'esun-mna-qa'):
        if sources[sid]['url'].encode() not in originals['esun-mna-index']:
            raise ValueError('PDF not linked by official MNA index: ' + sid)
    failed = manifest['nhi-capital-surplus']
    if failed['status'] != 'FAILED' or failed['http'] != 403:
        raise ValueError('Failed NHI source changed; inspect before use')
    return texts, sources, dict(status='FAILED_HTTP_403_NOT_USABLE_NOT_RETRIED', url=failed['url'])


def match(pattern, text):
    m = re.search(pattern, text)
    if not m:
        raise ValueError('Required source wording absent: ' + pattern)
    return m


def proof(sid, text, pattern):
    m = match(pattern, compact(text))
    # Compact text is a deterministic locator into a SHA-bound derivative.
    return [dict(source_id=sid, locator='derived text without whitespace, chars ' + str(m.start()) + ':' + str(m.end()),
                 raw_value=m[0])]


def field(value, unit, role, proofs, qualification='SOURCE_FACT_NOT_FINAL_LEDGER'):
    return dict(value=value, unit=unit, date_role=role, proofs=proofs, qualification=qualification)


def parse_direct(text):
    s = compact(text)
    year = int(match(r'玉山金控(\d{4})年股利發放訊息', s)[1])
    displayed = match(r'(\d{4})/(\d{2})/(\d{2})', s)
    ex = match(r'除權息交易日為(\d+)/(\d+)', s)
    ratio = match(r'每[仟千]股配發股票股利([\d.]+)股', s)
    pay = match(r'暫訂發放日為(\d+)/(\d+)', s)
    return dict(year=year, issuer_display_date=date(*map(int, displayed.groups())).isoformat(),
                ex_date=date(year, int(ex[1]), int(ex[2])).isoformat(),
                ratio_per_thousand=ratio[1], ratio=per_old_share(ratio[1], '1000'),
                tentative_pay_date=date(year, int(pay[1]), int(pay[2])).isoformat())


def statement_time(text):
    s = compact(text)
    d = match(r'發言日期(\d+)/(\d+)/(\d+)', s)
    t = match(r'發言時間(\d{2}):(\d{2}):(\d{2})', s)
    return datetime(int(d[1]) + 1911, int(d[2]), int(d[3]), *map(int, t.groups()),
                    tzinfo=timezone(timedelta(hours=8))).isoformat()


def parse_exchange(text, scheduled):
    s = compact(text)
    if '三商美邦人壽' not in s or '2884玉山金' not in s:
        raise ValueError('Wrong issuer/target document')
    pattern = (r'三商美邦人壽每1股普通股換發本公司([\d.]+)股普通股' if scheduled
               else r'每1股三商美邦人壽普通股可換發本公司([\d.]+)股普通股')
    ratio = match(pattern, s)[1]
    effective = None
    if scheduled:
        d = match(r'基準日為(\d+)年(\d+)月(\d+)日', s)
        effective = date(int(d[1]) + 1911, int(d[2]), int(d[3])).isoformat()
    return dict(ratio=ratio, document_claimed_statement_at=statement_time(text),
                scheduled_effective_date=effective)


def parse_qa(text):
    s = compact(text)
    listing = match(r'玉山金股份轉換以新股權利證書上市日[：:](\d+)年(\d+)月(\d+)日', s)
    ratio = match(r'三商美邦人壽每1股普通股股份換發本公司([\d.]+)股普通股', s)
    fee = match(r'免扣匯費(\d+)元', s)
    if '不足1元部分四捨五入' not in s or '三商美邦人壽最後交易日' not in s:
        raise ValueError('Missing case-specific fractions wording')
    return dict(listing=date(int(listing[1]) + 1911, int(listing[2]), int(listing[3])).isoformat(),
                ratio=ratio[1], conditional_fee=fee[1])


def build_catalog():
    text, sources, failed = load_review()
    review_facts_bytes = (REVIEW / 'facts.json').read_bytes()
    review_facts = json.loads(review_facts_bytes)
    original = json.loads((HERE / 'official_actions_20261022/events-v02.json').read_text())
    if original != build_v02()['catalog']:
        raise ValueError('Original v0.2/source drift; do not rewrite it')
    direct = parse_direct(text['esun-direct-2025-ratio'])
    reviewed_direct = review_facts['esun_2025_stock_dividend']
    if any(reviewed_direct[k] != direct[v] for k, v in [
            ('ex_date', 'ex_date'), ('published_shares_per_share', 'ratio'),
            ('issuer_page_display_date', 'issuer_display_date'),
            ('published_new_shares_per_thousand_old_shares', 'ratio_per_thousand')]):
        raise ValueError('Reviewed direct fields disagree with source extraction')
    if (review_facts['esun_share_exchange']['acquirer_code'], review_facts['esun_share_exchange']['target_code']) != ('2884', '2867'):
        raise ValueError('Reviewed issuer/target identity mapping changed; inspect primary identity evidence')
    old_stock = [e for e in original['events'] if e['code'] == '2884' and e['type'] == 'STOCK_DIVIDEND'
                 and e['ex_date'] == direct['ex_date']]
    if len(old_stock) != 1 or old_stock[0]['shares_per_share'] != direct['ratio']:
        raise ValueError('Direct ratio/date conflicts with saved stock component')
    catalog = deepcopy(original)
    catalog.pop('id', None)
    catalog.update(schema=SCHEMA, supersedes_catalog_id=identify(original)['id'], inventory=[],
                   sources={**catalog['sources'], **sources}, source_failure=failed,
                   review_fact_path=str((REVIEW / 'facts.json').relative_to(ROOT)),
                   review_fact_sha256=hashlib.sha256(review_facts_bytes).hexdigest(),
                   identity_qualification='TWO_SAVED_TWSE_ASSETS_ONLY_TARGET_2867_IDENTITY_FROM_WORK_REVIEW_NOT_FULL_MASTER')
    stock = next(e for e in catalog['events'] if e['id'] == old_stock[0]['id'])
    prior_id = stock.pop('id'); stock['supersedes_event_id'] = prior_id
    stock['prior_observed_at'] = stock['observed_at']
    stock['prior_ratio_role'] = stock['ratio_role']
    stock['prior_ratio_calculation'] = stock.pop('ratio_calculation')
    stock['observed_at'] = max(stock['observed_at'], sources['esun-direct-2025-ratio']['captured_at'])
    stock.update(ratio_role='DIRECT_PUBLISHED_NOT_VERIFIED_UNROUNDED_OR_INVESTOR_ALLOTMENT',
                 ratio_calculation=dict(expression='published_new_shares_per_thousand_old_shares / 1000',
                                        result_unit='NEW_2884_SHARES_PER_OLD_2884_SHARE'),
                 published_new_shares_per_thousand_old_shares=direct['ratio_per_thousand'],
                 issuer_page_display_date=direct['issuer_display_date'])
    stock['source_ids'].append('esun-direct-2025-ratio')
    stock['field_sources']['shares_per_share'] = proof('esun-direct-2025-ratio', text['esun-direct-2025-ratio'], r'每[仟千]股配發股票股利[\d.]+股')
    stock.update(identify(stock))
    for c in catalog['coverage'].values():
        c['event_ids'] = [stock['id'] if i == prior_id else i for i in c['event_ids']]
    inventory = catalog['inventory']
    def version(sid, family, action, entitled, fields, stage, old_instrument, company_codes):
        sids = [sid, 'esun-mna-index'] if sid.startswith('esun-mna-') else [sid]
        v = identify(dict(family=family, issuer_code='2884' if sid.startswith('esun') else '1101',
            entitled_old_code=entitled, action_type=action, old_instrument=old_instrument,
            company_codes=company_codes, source_ids=sids, observed_at=max(sources[s]['captured_at'] for s in sids),
            historical_signal_eligible=False, announced_at=None, stage=stage, fields=fields))
        inventory.append(v); return v
    dp = stock['field_sources']['shares_per_share']
    version('esun-direct-2025-ratio', '2884-stock-dividend-component:' + prior_id,
        'STOCK_DIVIDEND', '2884', dict(
            shares_per_share=field(direct['ratio'], 'NEW_2884_SHARES_PER_OLD_2884_SHARE', 'NOT_A_DATE', dp, 'DIRECT_PUBLISHED'),
            tentative_pay_date=field(direct['tentative_pay_date'], 'ISO_DATE', 'TENTATIVE_STOCK_DIVIDEND_DISTRIBUTION', proof('esun-direct-2025-ratio', text['esun-direct-2025-ratio'], r'暫訂發放日為\d+/\d+')),
            tradable_date=field(None, 'ISO_DATE', 'STOCK_DIVIDEND_ORDINARY_SHARE_TRADABILITY', [])),
        'PUBLISHED_STOCK_DIVIDEND', '2884_ORDINARY_OLD_SHARES', ['2884'])
    exchange_versions = []
    for sid, scheduled in [('esun-mna-20251105', False), ('esun-mna-20260713', True)]:
        f = parse_exchange(text[sid], scheduled)
        exchange_versions.append(version(sid, '2884-acquires-2867', 'SHARE_EXCHANGE', '2867', dict(
            shares_per_share=field(f['ratio'], 'NEW_2884_SHARES_PER_OLD_2867_SHARE', 'NOT_A_DATE', proof(sid, text[sid], r'(?:三商美邦人壽每1股普通股換發本公司|每1股三商美邦人壽普通股可換發本公司)[\d.]+股普通股'), 'DIRECT_PUBLISHED'),
            scheduled_effective_date=field(f['scheduled_effective_date'], 'ISO_DATE', 'SCHEDULED_SHARE_EXCHANGE_EFFECTIVE', proof(sid, text[sid], r'基準日為\d+年\d+月\d+日') if scheduled else []),
            document_claimed_statement_at=field(f['document_claimed_statement_at'], 'DATETIME_OFFSET', 'DOCUMENT_SELF_REPORTED_STATEMENT_NOT_AUTHENTICATED_AVAILABILITY', proof(sid, text[sid], r'發言日期\d+/\d+/\d+'))),
            'ANNOUNCED_SCHEDULE' if scheduled else 'BOARD_PROPOSAL', '2867_ORDINARY_OLD_SHARES', ['2884', '2867']))
    qa = parse_qa(text['esun-mna-qa'])
    if qa['ratio'] != exchange_versions[-1]['fields']['shares_per_share']['value']:
        raise ValueError('Q&A ratio disagrees with announced version')
    catalog['version_relations'] = [dict(family='2884-acquires-2867',
        earlier_document_version=exchange_versions[0]['id'], later_document_version=exchange_versions[1]['id'],
        role='DOCUMENT_CLAIM_SEQUENCE_NOT_AUTHENTICATED_HISTORICAL_AVAILABILITY_OR_AUTOMATIC_SELECTION')]
    version('esun-mna-qa', '2884-acquires-2867', 'SHARE_EXCHANGE', '2867', dict(
        certificate_listing_date=field(qa['listing'], 'ISO_DATE', 'EXCHANGE_NEW_RIGHT_CERTIFICATE_LISTING', proof('esun-mna-qa', text['esun-mna-qa'], r'玉山金股份轉換以新股權利證書上市日[：:]\d+年\d+月\d+日')),
        fractional_rounding=field('ROUND_TO_WHOLE_TWD', 'POLICY', 'THIS_SHARE_EXCHANGE_ONLY', proof('esun-mna-qa', text['esun-mna-qa'], r'不足1元部分四捨五入至新臺幣「元」為止')),
        conditional_remittance_fee=field(qa['conditional_fee'], 'TWD', 'THIS_SHARE_EXCHANGE_CONDITIONAL_FEE_NOT_OTHER_PAYMENTS', proof('esun-mna-qa', text['esun-mna-qa'], r'免扣匯費\d+元'))),
        'CASE_SPECIFIC_QA_NOT_INVESTOR_RECEIPT', '2867_ORDINARY_OLD_SHARES', ['2884', '2867'])
    tcc = text['tcc-capital-surplus-2026']
    if not all(s in tcc for s in ('Board Proposes', 'capital surplus', '2026.03.11')):
        raise ValueError('TCC source no longer an identifiable board proposal')
    amount = match(r'NT\$([\d.]+) per share in cash from capital surplus', tcc)[1]
    version('tcc-capital-surplus-2026', '1101-cash-distribution-board-proposal', 'CASH_DISTRIBUTION_PROPOSAL', '1101', dict(
        proposed_cash_per_share=field(amount, 'TWD_PER_OLD_1101_SHARE', 'NOT_A_DATE', proof('tcc-capital-surplus-2026', tcc, r'NT\$[\d.]+pershareincashfromcapitalsurplus')),
        proposed_funding_source=field('CAPITAL_SURPLUS', 'SOURCE_CATEGORY', 'BOARD_PROPOSAL_NOT_FINAL_RESOLUTION', proof('tcc-capital-surplus-2026', tcc, r'BoardProposesNT\$[\d.]+CashDistributionperSharefromCapitalSurplus')),
        final_funding_source=field(None, 'SOURCE_CATEGORY', 'FINAL_DISTRIBUTION', []),
        capital_surplus_subtype=field(None, 'SOURCE_CATEGORY', 'FINAL_CAPITAL_SURPLUS_SUBTYPE', []),
        net_cash_per_share=field(None, 'TWD_PER_OLD_1101_SHARE', 'INVESTOR_OR_CONTEXTUAL_MODEL_NET_CASH', [])),
        'BOARD_PROPOSAL_NOT_TAX_MODEL', '1101_ORDINARY_OLD_SHARES', ['1101'])
    for code, coverage in catalog['coverage'].items():
        coverage['known_company_action_ids'] = required_inventory(catalog, code)
        coverage['source_ids'] = sorted(set(coverage['source_ids']) | {s for v in inventory if code in v['company_codes'] for s in v['source_ids']})
        coverage['gaps'].append('SCOPED_INVENTORY_NOT_EXHAUSTIVE_REGISTER_OR_SUPPORTED_ACCOUNT_IMPACT')
    catalog['source_supplement_scope'] = 'DIRECT_PUBLISHED_PRECISION_AND_CASE_SCOPES_NOT_COMPLETE_COVERAGE'
    return identify(catalog)


def scoped_input(old, catalog, manifest, calendar, start, end, a):
    return bind_observed_calendar(candidate_input(old, catalog, manifest, start, end, a), calendar)


def main():
    OUT.mkdir(exist_ok=True)
    catalog = build_catalog(); old, manifest = verified_quotes(); calendar = build_calendar()
    design = json.loads((HERE / 'generated/design.json').read_text())
    dates = [b['date'] for b in old['assets']['1101']['bars']]; windows = []
    for start in design['cutoffs']:
        for a, b in [('1101', '2884'), ('2884', '1101')]:
            for horizon in design['horizons']:
                i = dates.index(start)
                if i + horizon >= len(dates):
                    windows.append(dict(A=a, B=b, start=start, end=None, horizon=horizon,
                                        status='INSUFFICIENT_SAVED_FORWARD_ROWS')); continue
                inp = scoped_input(old, catalog, manifest, calendar, start, dates[i + horizon], a)
                result = admit_and_replay(inp, catalog)
                if result['daily'] or result['total_net_return'] is not None:
                    raise ValueError('Incomplete sources were calculated')
                windows.append(dict(A=a, B=b, horizon=horizon, **result))
    probe = scoped_input(old, catalog, manifest, calendar, '2026-08-03', '2026-09-10', '2884')
    probe_result = admit_and_replay(probe, catalog)
    calculated = [w for w in windows if w['end'] is not None]
    numeric_calls = sum(w.get('original_numeric_replay_called', True) for w in calculated)
    if probe_result.get('original_numeric_replay_called', True) or numeric_calls:
        raise ValueError('Unqualified numeric replay unexpectedly executed')
    dump(OUT / 'events-v03.json', catalog)
    dump(OUT / 'window-qualification.json', dict(windows=windows, qualified_windows=0, ranking=None,
        new_admission_calls=len(calculated), original_numeric_replay_calls=numeric_calls, six_strategy_replays=0))
    dump(OUT / 'scope-input-probe.json', probe)
    dump(OUT / 'scope-refusal.json', probe_result)
    summary = dict(scoped_source_versions=len(catalog['inventory']),
        original_ledger_components=len(catalog['events']), official_archives_rechecked=6,
        original_quote_archives_rechecked=len(manifest), admission_windows=len(calculated), separate_probe_calls=1,
        unsupported_exchange_windows=sum('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED' in w['refusal_reasons'] for w in calculated),
        insufficient_windows=sum(w['end'] is None for w in windows), total_net_return_qualified_windows=0,
        original_numeric_replay_calls=0, six_strategy_replays=0, new_network_requests=0,
        browser_runs=0, android='NOT_TESTED_NEW_BUILD', primary_pressure_id=None, policy_authorized=False)
    dump(OUT / 'verification.json', summary); print(json.dumps(summary))


if __name__ == '__main__':
    main()
