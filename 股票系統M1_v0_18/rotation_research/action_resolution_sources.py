"""Offline 0.4 producer; no requests, no mutation of prior outputs or engines."""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urljoin

from .action_sources import HERE, ROOT, dump
from .action_scope import identify
from .action_scope_sources import compact, match, field, build_catalog as parent_build, scoped_input
from .action_resolution import SCHEMA, ROUNDING, validate, required_inventory, refuse_accounting, preview_shareholder_cash
from .action_study import verified_quotes
from .source_qualification import build_calendar

REVIEW = HERE / 'final_distribution_review_20261023'
OUT = HERE / 'action_resolution_20261023'
PINNED = {
    'tcc-meeting-index': ('https://www.tccgroupholdings.com/shareholder-meetings',
        'd995a10409cebd07942fad51aceb26de1db726936715af36376f4aa68d2f5098',
        '0e3d9a1bd7bc63115366d93da9e8b2976c85e32f7c36759aab82923d63eb60a4'),
    'tcc-2026-agm-minutes': ('https://media.taiwancement.com/web_tcc/comm/pdf/AGM/2026/TCC%20115%E5%B9%B4%E8%82%A1%E6%9D%B1%E6%9C%83%E8%AD%B0%E4%BA%8B%E9%8C%84.pdf',
        'ec3bf135a859a611a2851b744294af8312e829be192d86995fd9203d63472d14',
        'bba966826f91d050ac4ff3c3227caab487b73d57220d902517fa08ccd2f5c08f')}


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs).get('href', ''))


def load_review(review=REVIEW):
    review = Path(review)
    manifest = json.loads((review / 'source-manifest.json').read_text())
    originals, texts, sources = {}, {}, {}
    for sid, (url, raw_hash, text_hash) in PINNED.items():
        m = manifest[sid]
        meta = json.loads((review / 'raw' / (sid + '.meta.json')).read_text())
        for key in ('url', 'captured_at', 'http', 'status', 'final_url', 'bytes', 'sha256', 'retries', 'redirects_followed'):
            if meta[key] != m[key]:
                raise ValueError('Source manifest/meta mismatch: ' + sid)
        if (m['url'] != url or m['final_url'] != url or m['status'] != 'CAPTURED'
                or m['http'] != 200 or m['retries'] != 0 or m['redirects_followed']):
            raise ValueError('Pinned official source metadata mismatch: ' + sid)
        raw = (review / 'raw' / (sid + '.response')).read_bytes()
        text = (review / 'raw' / (sid + '.txt')).read_bytes()
        extraction = json.loads((review / 'raw' / (sid + '.extraction.json')).read_text())
        if (hashlib.sha256(raw).hexdigest() != raw_hash or m['sha256'] != raw_hash
                or len(raw) != m['bytes'] or hashlib.sha256(text).hexdigest() != text_hash
                or m['derived_text_sha256'] != text_hash or extraction['text_sha256'] != text_hash
                or extraction.get('pdf_sha256', extraction.get('source_sha256')) != raw_hash):
            raise ValueError('Pinned original/derived fingerprint mismatch: ' + sid)
        originals[sid], texts[sid] = raw, text.decode('utf-8-sig')
        sources[sid] = dict(url=url, sha256=raw_hash, captured_at=m['captured_at'],
            path=str((REVIEW / 'raw' / (sid + '.response')).relative_to(ROOT)),
            derived_text_sha256=text_hash, kind='OFFICIAL_ARCHIVE',
            historical_publication_time='NOT_AUTHENTICATED')
    parser = Links(); parser.feed(originals['tcc-meeting-index'].decode('utf-8-sig'))
    pdf_url = PINNED['tcc-2026-agm-minutes'][0]
    if unquote(pdf_url) not in [unquote(urljoin(PINNED['tcc-meeting-index'][0], link)) for link in parser.links]:
        raise ValueError('PDF is not an actual official-index anchor')
    if not originals['tcc-2026-agm-minutes'].startswith(b'%PDF-'):
        raise ValueError('Invalid PDF magic')
    if texts['tcc-2026-agm-minutes'].count('\f') != 57:
        raise ValueError('Unexpected page-delimited derivative')
    if '2026股東常會日期2026.05.22' not in compact(texts['tcc-meeting-index']):
        raise ValueError('Meeting date anchor missing')
    return texts, sources


def parse_minutes(text):
    pages = text.split('\f')
    section = compact(pages[5] + pages[6]).split('四、討論事項', 1)[1].split('第二案', 1)[0]
    funding = match(r'二、本公司擬以(.+?)之資本公積提撥新台幣', section)[1]
    total = match(r'提撥新台幣\(以下同\)([\d,]+)元', section)[1].replace(',', '')
    rate = match(r'每股發放([\d.]+)元', section)[1]
    vote_patterns = {'attending': r'表決時出席股東表決權數：([\d,]+)權',
        'yes': r'贊成權數：([\d,]+)權', 'no': r'反對權數：([\d,]+)權',
        'invalid': r'無效權數：([\d,]+)權', 'abstain': r'棄權與未投票權數：([\d,]+)權'}
    vote = {k: match(p, section)[1].replace(',', '') for k, p in vote_patterns.items()}
    if sum(int(vote[k]) for k in ('yes', 'no', 'invalid', 'abstain')) != int(vote['attending']):
        raise ValueError('Resolution vote arithmetic mismatch')
    percent = match(r'贊成權數：[\d,]+權([\d.]+)%', section)[1]
    if format((Decimal(vote['yes']) * 100 / Decimal(vote['attending'])).quantize(Decimal('.01'), rounding=ROUND_HALF_UP), 'f') != percent:
        raise ValueError('Resolution displayed vote percent mismatch')
    required = ['本案依表決結果，照案通過', '授權董事長全權處理', '授權董事長另行訂定發放現金基準日及發放日',
        '每位普通股股東發放現金總額至元為止(元以下捨去)', '其畸零款合計數計入本公司之其他收入']
    if not all(s in section for s in required):
        raise ValueError('Resolution/authority/per-holder rounding clause missing')
    tranche = compact(pages[3])
    if '買回期次第七次' not in tranche or '已辦理銷除之股份數量28,000張' not in tranche:
        raise ValueError('Seventh treasury cancellation scope missing')
    return dict(funding=funding, total=total, rate=rate, vote=vote, percent=percent, section=section)


def build_catalog():
    texts, sources = load_review()
    parsed = parse_minutes(texts['tcc-2026-agm-minutes'])
    parent = json.loads((HERE / 'action_scope_20261023/events-v03.json').read_text())
    if parent_build() != parent:
        raise ValueError('Parent source catalog drift; do not overwrite')
    facts = json.loads((REVIEW / 'facts.json').read_text())
    reviewed = facts['distribution_resolution']
    for key, value in [('approved_cash_per_share', parsed['rate']), ('approved_total_twd', parsed['total']),
            ('approved_capital_surplus_label_raw', parsed['funding'])]:
        if reviewed[key] != value:
            raise ValueError('Work facts disagree with exact resolution section: ' + key)
    for key, value in parsed['vote'].items():
        target = 'vote_' + ('abstain_or_not_voted' if key == 'abstain' else key) + '_rights'
        if reviewed[target] != value:
            raise ValueError('Work vote facts disagree: ' + key)
    catalog = dict(schema=SCHEMA, parent_catalog_id=parent['id'], parent_catalog=deepcopy(parent),
        events=deepcopy(parent['events']), inventory=deepcopy(parent['inventory']),
        coverage=deepcopy(parent['coverage']), sources={**parent['sources'], **sources},
        version_relations=deepcopy(parent['version_relations']),
        supplement_scope='APPROVED_RESOLUTION_AND_TRANCHE_REPORT_NOT_COMPLETE_COVERAGE',
        historical_signal_eligible=False, primary_pressure_id=None, policy_authorized=False)
    sid = 'tcc-2026-agm-minutes'
    def bound(value, unit, role, literal, pages):
        proofs = []
        if value is not None:
            scoped = compact(''.join(texts[sid].split('\f')[p-1] for p in pages))
            if literal not in scoped:
                raise ValueError('Field proof absent in specified PDF pages: ' + literal)
            proofs = [dict(source_id=sid, pdf_pages=pages, locator='PDF pages ' + ','.join(map(str, pages)), raw_value=literal)]
        return field(value, unit, role, proofs, 'RESOLUTION_DIAGNOSTIC_NOT_FINAL_LEDGER')
    def add(family, action_type, stage, fields):
        v = identify(dict(family=family, issuer_code='1101', entitled_old_code='1101',
            old_instrument='1101_ORDINARY_OLD_SHARES', action_type=action_type,
            company_codes=['1101'], source_ids=['tcc-meeting-index', sid], stage=stage,
            observed_at=max(s['captured_at'] for s in sources.values()), announced_at=None,
            historical_signal_eligible=False, fields=fields))
        catalog['inventory'].append(v); return v
    v = add('1101-capital-surplus-2026-approved', 'CASH_DISTRIBUTION_RESOLUTION', 'SHAREHOLDER_APPROVED_ADJUSTABLE', dict(
        meeting_date=field('2026-05-22', 'ISO_DATE', 'SHAREHOLDER_MEETING_NOT_EX_RECORD_PAY_DATE',
            [dict(source_id='tcc-meeting-index', locator='visible text 2026 annual meeting date', raw_value='2026股東常會日期2026.05.22')],
            'RESOLUTION_DIAGNOSTIC_NOT_FINAL_LEDGER'),
        approved_cash_per_share=bound(parsed['rate'], 'TWD_PER_OLD_1101_SHARE', 'NOT_A_DATE', '每股發放0.8元', [6]),
        approved_total_twd=bound(parsed['total'], 'TWD', 'APPROVED_ISSUER_TOTAL_NOT_INVESTOR_CASH', '5,994,545,394元', [6]),
        approved_funding_label=bound(parsed['funding'], 'SOURCE_LABEL_AS_STATED', 'APPROVED_RESOLUTION_NOT_TAX_SUBTYPE', parsed['funding'], [6]),
        rounding_scope=bound(ROUNDING, 'POLICY', 'PER_HOLDER_TOTAL_CASH', required_rounding_literal(), [6, 7]),
        ratio_adjustment_authority=bound('CHAIR_AUTHORIZED_IF_OUTSTANDING_SHARES_CHANGE', 'AUTHORITY', 'NOT_FINAL_ADJUSTED_RATIO', '授權董事長全權處理', [6]),
        date_setting_authority=bound('CHAIR_TO_SET_RECORD_AND_PAY_DATES', 'AUTHORITY', 'NOT_ACTUAL_DATES', '另行訂定發放現金基準日及發放日', [6]),
        final_cash_per_share=bound(None, 'TWD_PER_OLD_1101_SHARE', 'FINAL_AFTER_ADJUSTMENTS', '', [6]),
        tax_origin_subtype=bound(None, 'TAX_CATEGORY', 'AUTHENTICATED_TAX_ORIGIN', '', [6]),
        net_cash_per_share=bound(None, 'TWD_PER_OLD_1101_SHARE', 'INVESTOR_NET', '', [6]),
        record_date=bound(None, 'ISO_DATE', 'ACTUAL_RECORD_DATE', '', [6]),
        pay_date=bound(None, 'ISO_DATE', 'ACTUAL_PAY_DATE', '', [6]),
        actual_investor_receipt=bound(None, 'TWD', 'ACTUAL_INVESTOR_RECEIPT', '', [6])))
    proposal = next(x for x in parent['inventory'] if x['action_type'] == 'CASH_DISTRIBUTION_PROPOSAL')
    catalog['version_relations'].append(dict(earlier_document_version=proposal['id'], later_document_version=v['id'],
        role='PROPOSAL_TO_APPROVED_DOCUMENT_STAGE_NOT_AUTOMATIC_FINAL_SELECTION', same_action_identity_authenticated=False))
    for i, quantity in [(6, '10000'), (7, '28000')]:
        page = i - 3
        observation = facts['capital_action_inventory_observations'][i-6]
        raw_quantity = '10,000張' if i == 6 else '28,000張'
        add(observation['family'], 'TREASURY_REPURCHASE_REPORT', 'TRANCHE_REPORT_NOT_HOLDER_CAPITAL_REDUCTION', dict(
            actual_repurchase_quantity=bound(quantity, '張_AS_PUBLISHED', 'ISSUER_TREASURY_TRANCHE', '實際買回股份之數量' + raw_quantity, [page]),
            reported_cancellation=bound('NONE_REPORTED_THIS_TRANCHE' if i == 6 else quantity, 'TRANCHE_REPORT_AS_STATED', 'NOT_HOLDER_CONVERSION_OR_CASHFLOW', '已辦理銷除之股份數量' + ('無' if i == 6 else raw_quantity), [page]),
            cancellation_effective_date=bound(None, 'ISO_DATE', 'CANCELLATION_EFFECTIVE_NOT_BUYBACK_END', '', [page]),
            holder_conversion_ratio=bound(None, 'NEW_PER_OLD_SHARE', 'HOLDER_CAPITAL_REDUCTION_NOT_AUTHENTICATED', '', [page]),
            holder_cashflow=bound(None, 'TWD', 'HOLDER_CAPITAL_RETURN_NOT_AUTHENTICATED', '', [page])))
    for code, c in catalog['coverage'].items():
        c['known_company_action_ids'] = required_inventory(catalog, code)
        c['gaps'].append('RESOLUTION_NOT_FINAL_RATIO_NET_PAYMENT_OR_EXHAUSTIVE_ACTION_REGISTER')
        c['status'] = 'INCOMPLETE'
    catalog = identify(catalog); validate(catalog)
    return catalog


def required_rounding_literal():
    return '每位普通股股東發放現金總額至元為止(元以下捨去)'


def input_for(old, catalog, manifest, calendar, start, end, a):
    data = scoped_input(old, catalog['parent_catalog'], manifest, calendar, start, end, a)
    data['resolution_catalog_id'] = catalog['id']
    for code, c in data['coverage'].items():
        c['known_company_action_ids'] = required_inventory(catalog, code)
    return data


def main():
    catalog = build_catalog()
    old, manifest = verified_quotes(); calendar = build_calendar()
    design = json.loads((HERE / 'generated/design.json').read_text())
    dates = [b['date'] for b in old['assets']['1101']['bars']]
    windows = []
    for start in design['cutoffs']:
        for a, b in [('1101', '2884'), ('2884', '1101')]:
            for horizon in design['horizons']:
                i = dates.index(start)
                if i + horizon >= len(dates):
                    windows.append(dict(A=a, B=b, start=start, end=None, horizon=horizon, status='INSUFFICIENT_SAVED_FORWARD_ROWS'))
                else:
                    data = input_for(old, catalog, manifest, calendar, start, dates[i+horizon], a)
                    windows.append(dict(A=a, B=b, horizon=horizon, **refuse_accounting(data, catalog)))
    OUT.mkdir(exist_ok=True)
    dump(OUT / 'events-v04.json', catalog)
    calculated = sum(w['end'] is not None for w in windows)
    dump(OUT / 'window-qualification.json', dict(windows=windows, qualified_windows=0, ranking=None,
        new_admission_calls=calculated, original_numeric_replay_calls=0, six_strategy_replays=0))
    v = next(v for v in catalog['inventory'] if v['action_type'] == 'CASH_DISTRIBUTION_RESOLUTION')
    f = v['fields']['approved_cash_per_share']
    request = {k:v[k] for k in ('family', 'issuer_code', 'entitled_old_code', 'action_type', 'old_instrument')}
    request.update(version_id=v['id'], field='approved_cash_per_share', unit=f['unit'], date_role=f['date_role'],
        observed_as_of=v['observed_at'], historical_signal=False, purpose='SOURCE_DIAGNOSTIC')
    previews = [preview_shareholder_cash(catalog, request, dict(kind='HYPOTHETICAL_ENTITLED_SHARES',
        assumption='工程假想權利股數；非真實帳戶、成交或期初應收證明', shares=n, issuer_code='1101',
        old_instrument=v['old_instrument'], version_id=v['id'])) for n in ['1', '3', '5', '1001']]
    dump(OUT / 'gross-previews.json', dict(scope='SYNTHETIC_ENTITLEMENTS_ONLY_NOT_ACTUAL_ACCOUNT', previews=previews))
    summary = dict(schema=SCHEMA, archived_originals_rechecked=8, old_quote_originals_rechecked=len(manifest),
        source_versions=len(catalog['inventory']), added_source_versions=3, new_qualification_calls=calculated,
        refused_windows=sum(w['end'] is not None for w in windows), insufficient_windows=sum(w['end'] is None for w in windows),
        exchange_unsupported_windows=sum('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED' in w.get('refusal_reasons', []) for w in windows),
        qualified_total_net_return_windows=0, numeric_replay_calls=0, six_strategy_replays=0,
        new_network_requests=0, browser_runs=0, android='NOT_TESTED_NEW_BUILD')
    dump(OUT / 'verification.json', summary); print(json.dumps(summary))


if __name__ == '__main__':
    main()
