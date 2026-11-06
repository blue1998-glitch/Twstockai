"""Offline producer for source diagnostics 0.5; no new requests or old writes."""
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from .action_sources import HERE, ROOT, dump
from .action_scope import identify
from .action_scope_sources import field
from .action_resolution_sources import build_catalog as parent_build, input_for
from .action_study import verified_quotes
from .source_qualification import build_calendar
from .source_diagnostics import SCHEMA, QUALIFICATION, validate, quote_diagnostic, qualify

OUT = HERE / 'source_diagnostics_20261023'
# Pin original AND derivative. A changed live source is a new version, not an overwrite.
PINNED = {
    'tcc-resume-20250814': ('https://www.twse.com.tw/staticFiles/news/news/tsecnews/8a8216d697fc438f0198a36441f702b8.pdf',
        '5064b1af3ddee6437f049d378409b4405f96c0956a854000f5c13d40eb26bc68',
        '83016586a4abb9486385866f641ab3f3f50530ed7b45cba2edb73d16e6148a74', 1),
    'esun-prospectus-20260722': ('https://www.esunbank.com/zh-tw/-/media/ESUNFHC/Files/Investor-Relations/mna/mna08_2026Prospectus.pdf',
        '926f1f871a294702d3e4f5e4d89cf5aeb5e64808593efa2d99b95ed7375388fa',
        '6bb2eab5c6f23cff537051807ae98bee47c3f0d121af33b91f07715c8e2f38cf', 765),
    'esun-meeting-followup-2026': ('https://www.esunbank.com/zh-tw/-/media/ESUNFHC/Files/Investor-Relations/Shareholders/Shareholder-Meeting/2026_notes.pdf',
        '285d03487b512460a67875abba5dee38343ed6b1d0c92f5b01aa50dad2cd666c',
        'a58b6b2eb4905621f9088a778bca6d50530ff0a54fd7271141ae9709da1ea7e2', 1),
}
FAILED = {
    'tcc-suspend-20250813': 'https://wwwc.twse.com.tw/staticFiles/news/news/tsecnews/8a8216d697fc438f01989dd5fa3502a6.pdf',
    'esun-suspend-20251105': 'https://investoredu.twse.com.tw/Mobile_pages/..%2FFileSystem%2FFileUpload%2Fdae59521-69e0-4856-90fc-d349fb6013eb.pdf',
    'mof-interpretation-143802': 'https://ttc.mof.gov.tw/FB/FB120/143802',
}


def compact(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text))


def load_sources(directory=OUT):
    directory = Path(directory)
    manifest = json.loads((directory / 'source-manifest.json').read_text())
    if set(manifest) != set(PINNED) | set(FAILED):
        raise ValueError('Explicit capture inventory required')
    texts, sources = {}, {}
    for sid, (url, raw_sha, txt_sha, pages) in PINNED.items():
        m = manifest[sid]
        meta = json.loads((directory / 'raw' / (sid + '.meta.json')).read_text())
        if m != meta or m['url'] != url or m['final_url'] != url or m['http'] != 200 or m['status'] != 'CAPTURED':
            raise ValueError('Capture metadata/origin mismatch: ' + sid)
        for key in ('requested_at', 'completed_at'):
            if datetime.fromisoformat(m[key]).tzinfo is None:
                raise ValueError('Capture timestamp needs timezone')
        if m['requested_at'] > m['completed_at'] or m['retries'] != 0 or m['redirects_followed']:
            raise ValueError('Capture time/retry/redirect mismatch')
        raw = (directory / 'raw' / (sid + '.response')).read_bytes()
        txt = (directory / 'raw' / (sid + '.txt')).read_bytes()
        e = json.loads((directory / 'raw' / (sid + '.extraction.json')).read_text())
        if (not raw.startswith(b'%PDF-') or len(raw) != m['bytes']
                or hashlib.sha256(raw).hexdigest() != raw_sha or m['sha256'] != raw_sha
                or hashlib.sha256(txt).hexdigest() != txt_sha or m['derived_text_sha256'] != txt_sha
                or e['pdf_sha256'] != raw_sha or e['text_sha256'] != txt_sha or e['returncode'] != 0
                or txt.count(b'\f') != pages or e['pages'] != pages or m['pdf_pages'] != pages):
            raise ValueError('Original/derived fingerprint or page mismatch: ' + sid)
        texts[sid] = txt.decode('utf-8')
        sources[sid] = dict(url=url, sha256=raw_sha, captured_at=m['completed_at'],
            derived_text_sha256=txt_sha, historical_publication_time='NOT_AUTHENTICATED',
            path=str((OUT / 'raw' / (sid + '.response')).relative_to(ROOT)), kind='OFFICIAL_ARCHIVE')
    failures = {}
    for sid, url in FAILED.items():
        m = manifest[sid]
        if (m != json.loads((directory / 'raw' / (sid + '.meta.json')).read_text())
                or m['url'] != url or m['status'] != 'REQUEST_FAILED' or m['retries'] != 0
                or m['redirects_followed'] or '403 Forbidden' not in m['error']):
            raise ValueError('Failed source history changed; use a new version')
        failures[sid] = deepcopy(m)
    return texts, sources, failures


def parse_resume(text):
    s = compact(text)
    m = re.search(r'公司代號:([0-9]+)', s)
    d = re.search(r'上市普通股自(\d+)年(\d+)月(\d+)日起恢復交易', s)
    if not m or not d:
        raise ValueError('Resumption security/date wording missing')
    y, mo, da = map(int, d.groups())
    return dict(code=m[1], resume_date=f'{y+1911:04d}-{mo:02d}-{da:02d}')


def parse_prospectus(text):
    p = text.split('\f')
    if len(p) != 766:
        raise ValueError('Expected 765 source pages')
    a, b = compact(p[0]), compact(p[54])
    if not all(x in a for x in ['股票代碼:2884', '三商美邦人壽', '預計發行普通股',
            '實際發行新股之數額', '股份轉換基準日實際已發行之股份', '中華民國一一五年七月二十二日刊印']):
        raise ValueError('Expected-issuance/target/date scope missing')
    qty = re.search(r'預計發行普通股([\d,]+)股', a)
    rate = re.search(r'調整為每1股三商美邦人壽普通股股份換發本公司([\d.]+)股普通股', a)
    ordinary = re.search(r'普通股([\d,]+)3,808,000,00020,000,000,000', b)
    if not qty or not rate or not ordinary or not all(x in b for x in [
            '115年7月3日;單位:股', '115.06.30(註7)', '員工酬勞',
            '註7:經濟部115年06月30日經授商字第11530087080號函核准變更登記在案']):
        raise ValueError('Share quantity/employee registration scope missing')
    return dict(expected_issue_shares=qty[1].replace(',', ''), target_holder_ratio=rate[1],
        ordinary_outstanding_shares=ordinary[1].replace(',', ''),
        share_snapshot_date='2026-07-03', employee_registration_date='2026-06-30',
        printed_date='2026-07-22')


def parse_followup(text):
    s = compact(text)
    # pdftotext -layout interleaves the left-column agenda title into this
    # right-column record-date sentence. Accept only that exact intervening row.
    record = re.search(r'已訂(\d{4}\.\d{2}\.\d{2})為盈餘分派除息基準日暨員工酬勞轉增資發行新股之(?:二、承認114年度盈餘分派案。)?增資基準日', s)
    paid = re.search(r'並已於(\d{4}\.\d{2}\.\d{2})發放完畢。\(每股分配現金股利([\d.]+)元', s)
    if not record or not paid or '2026年股東常會議案後續執行情形及檢討' not in s:
        raise ValueError('Issuer completion/record/employee scopes missing')
    return dict(record_date=record[1].replace('.', '-'), issuer_completed_pay_date=paid[1].replace('.', '-'),
        issuer_reported_gross_per_share=paid[2])


def parse_mof_api(payload):
    """Scoped API contract for future archived originals, NOT a live capture.

    ViewCount is deliberately irrelevant. No net/tax-exemption inference.
    Actual catalog does not use this parser until official originals are saved.
    """
    row = payload['Data']['Table'][0]
    if not all(isinstance(row.get(k), str) and row[k].strip() for k in ('TaxVer', 'Title', 'Content')):
        raise ValueError('Official TaxVer/Title/Content required')
    s = compact(row['Title'] + row['Content'])
    if not all(x in s for x in ['10100097670', '101年8月17日']):
        raise ValueError('Wrong interpretation identity')
    if '114' not in compact(row['TaxVer']) and '一一四' not in row['TaxVer']:
        raise ValueError('Wrong tax edition')
    return dict(TaxVer=row['TaxVer'], Title=row['Title'], Content=row['Content'],
        qualification='GENERAL_LAW_CONTEXT_NOT_PERSONAL_NET', personal_net=None,
        personal_tax=None, nhi=None, fees=None, historical_signal_eligible=False)


def build_catalog(directory=OUT):
    texts, sources, failures = load_sources(directory)
    parent = parent_build()
    if parent != json.loads((HERE / 'action_resolution_20261023/events-v04.json').read_text()):
        raise ValueError('Formal parent 0.4 changed; preserve and inspect')
    result = dict(schema=SCHEMA, parent_catalog_id=parent['id'], parent_catalog=deepcopy(parent),
        coverage=deepcopy(parent['coverage']), sources=sources, failed_sources=failures, observations=[],
        gaps=['COMPLETE_1101_2884_ACTION_AND_REDUCTION_COVERAGE', 'POST_20260725_ACTION_COVERAGE',
            'DIRECT_SUSPENSION_STARTS_AND_ESUN_RESUMPTION', '2884_2025_TRADABILITY_UNROUNDED_ALLOTMENT_FRACTIONS',
            '2884_EXISTING_HOLDER_EXCHANGE_IMPACT', '1101_FINAL_ADJUSTMENT_AND_TAX_SUBTYPE',
            'DIRECT_TAX_ORIGINAL_UNAVAILABLE_IN_THIS_ENVIRONMENT', 'INVESTOR_NET_RECEIPTS_AND_NINE_OPENING_ENTITLEMENTS'],
        historical_signal_eligible=False, primary_pressure_id=None, policy_authorized=False)
    def bound(sid, pages, value, unit, role, literal):
        scoped = compact(''.join(texts[sid].split('\f')[i-1] for i in pages))
        if value is not None and compact(literal) not in scoped:
            raise ValueError('Missing field proof in scoped pages: ' + literal)
        proofs = [] if value is None else [dict(source_id=sid, pdf_pages=pages,
            locator='PDF pages ' + ','.join(map(str, pages)), raw_value=literal)]
        return field(value, unit, role, proofs, QUALIFICATION)
    def add(sid, kind, holder, instrument, fields):
        obs = identify(dict(family=sid + ':' + kind, issuer_code='1101' if sid.startswith('tcc-') else '2884',
            entitled_old_code=holder, old_instrument=instrument, action_type=kind,
            source_ids=[sid], observed_at=sources[sid]['captured_at'], announced_at=None,
            accounting_eligible=False, historical_signal_eligible=False, fields=fields))
        result['observations'].append(obs)
    sid = 'tcc-resume-20250814'; r = parse_resume(texts[sid])
    if r['code'] != '1101':
        raise ValueError('Wrong resumption issuer')
    add(sid, 'SECURITY_RESUMPTION_NOTICE', r['code'], '1101_ORDINARY_OLD_SHARES', dict(
        resume_date=bound(sid, [1], r['resume_date'], 'ISO_DATE', 'SECURITY_RESUMPTION_NOT_SUSPENSION_START', '上市普通股自114年8月14日起恢復交易'),
        suspension_date=bound(sid, [1], None, 'ISO_DATE', 'SECURITY_SUSPENSION_START_UNVERIFIED', '')))
    sid = 'esun-prospectus-20260722'; p = parse_prospectus(texts[sid])
    add(sid, 'SHARE_EXCHANGE_EXPECTED_ISSUANCE', '2867', '2867_ORDINARY_OLD_SHARES', dict(
        expected_issue_shares=bound(sid, [1], p['expected_issue_shares'], 'NEW_2884_SHARES_FOR_OLD_2867_HOLDERS', 'EXPECTED_NOT_ACTUAL_ISSUE', '預計發行普通股1,531,510,471股'),
        target_holder_ratio=bound(sid, [1], p['target_holder_ratio'], 'NEW_2884_PER_OLD_2867', 'TARGET_HOLDER_EXCHANGE_NOT_2884_STOCK_DIVIDEND', '本公司0.2596股普通股'),
        actual_issued_shares=bound(sid, [1], None, 'SHARES', 'ACTUAL_ISSUE_NOT_AUTHENTICATED', ''),
        existing_2884_share_grant=bound(sid, [1], None, 'NEW_2884_PER_OLD_2884', 'EXISTING_ACQUIRER_IMPACT_UNRESOLVED', '')))
    add(sid, 'EMPLOYEE_CAPITAL_REGISTRATION', 'EMPLOYEE_RECIPIENTS', 'EMPLOYEE_REMUNERATION_RIGHTS', dict(
        registration_date=bound(sid, [55], p['employee_registration_date'], 'ISO_DATE', 'CORPORATE_REGISTRATION_NOT_LISTING_OR_RECORD', '115年06月30日經授商字第11530087080號函核准變更登記在案'),
        ordinary_outstanding_shares=bound(sid, [55], p['ordinary_outstanding_shares'], 'ISSUER_ORDINARY_SHARES', 'AS_OF_SHARE_SNAPSHOT_NOT_ALLOTMENT', '16,192,000,000'),
        share_snapshot_date=bound(sid, [55], p['share_snapshot_date'], 'ISO_DATE', 'SHARE_CAPITAL_AS_OF_NOT_REGISTRATION_OR_LISTING', '115年7月3日'),
        listing_date=bound(sid, [55], None, 'ISO_DATE', 'ACTUAL_SECURITY_LISTING_NOT_AUTHENTICATED', '')))
    sid = 'esun-meeting-followup-2026'; p = parse_followup(texts[sid])
    add(sid, 'ISSUER_DISTRIBUTION_COMPLETION_REPORT', '2884', '2884_ORDINARY_OLD_SHARES', dict(
        dividend_record_date=bound(sid, [1], p['record_date'], 'ISO_DATE', 'DIVIDEND_RECORD_NOT_EX_TRADING', '2026.07.07為盈餘分派除息基準日'),
        issuer_completed_pay_date=bound(sid, [1], p['issuer_completed_pay_date'], 'ISO_DATE', 'ISSUER_REPORTED_COMPLETION_NOT_PERSONAL_RECEIPT', '2026.07.27發放完畢'),
        issuer_reported_gross_per_share=bound(sid, [1], p['issuer_reported_gross_per_share'], 'TWD_PER_OLD_2884_SHARE', 'ISSUER_GROSS_NOT_PERSONAL_NET', '每股分配現金股利1.40元'),
        investor_net_cash=bound(sid, [1], None, 'TWD', 'PERSONAL_NET_UNKNOWN', ''),
        actual_investor_receipt=bound(sid, [1], None, 'TWD', 'PERSONAL_RECEIPT_UNKNOWN', '')))
    add(sid, 'EMPLOYEE_CAPITAL_REGISTRATION', 'EMPLOYEE_RECIPIENTS', 'EMPLOYEE_REMUNERATION_RIGHTS', dict(
        employee_capital_record_date=bound(sid, [1], p['record_date'], 'ISO_DATE', 'EMPLOYEE_CAPITAL_RECORD_NOT_REGISTRATION_OR_LISTING', '已訂2026.07.07為盈餘分派除息基準日暨員工酬勞轉增資發行新股之'),
        listing_date=bound(sid, [1], None, 'ISO_DATE', 'ACTUAL_SECURITY_LISTING_NOT_AUTHENTICATED', '')))
    return validate(identify(result))


def run():
    catalog = build_catalog()
    old, manifest = verified_quotes(); calendar = build_calendar()
    missing = [quote_diagnostic(catalog, code, b['date'], b['close'], b['date'] in calendar['sessions'])
        for code, a in old['assets'].items() for b in a['bars'] if b.get('missing')]
    design = json.loads((HERE / 'generated/design.json').read_text())
    dates = [b['date'] for b in old['assets']['1101']['bars']]; windows = []
    for start in design['cutoffs']:
        for a, b in [('1101', '2884'), ('2884', '1101')]:
            for horizon in design['horizons']:
                i = dates.index(start)
                if i + horizon >= len(dates):
                    windows.append(dict(A=a, B=b, start=start, end=None, horizon=horizon, status='INSUFFICIENT_SAVED_FORWARD_ROWS'))
                else:
                    data = input_for(old, catalog['parent_catalog'], manifest, calendar, start, dates[i+horizon], a)
                    data['source_diagnostics_catalog_id'] = catalog['id']
                    windows.append(dict(A=a, B=b, horizon=horizon, **qualify(data, catalog)))
    verification = dict(schema=SCHEMA, usable_new_originals=3, failed_captures=3,
        new_source_observations=len(catalog['observations']), not_independent_event_count=True,
        original_quote_archives_rechecked=len(manifest), calendar_reports_rechecked=len(calendar['sources']),
        qualification_calls=sum(w['end'] is not None for w in windows),
        refused_windows=sum(w['end'] is not None for w in windows), insufficient_windows=sum(w['end'] is None for w in windows),
        exchange_unsupported_windows=sum('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED' in w.get('refusal_reasons', []) for w in windows),
        qualified_total_net_return_windows=0, numeric_replay_calls=0, six_strategy_replays=0,
        unknown_missing_causes=sum(d['new_missing_explanation']=='UNKNOWN' for d in missing),
        new_network_requests_by_offline_producer=0, android='NOT_TESTED_NEW_BUILD',
        tax_api_contract='SYNTHETIC_TEST_ONLY_NO_LIVE_ORIGINAL', historical_signal_eligible=False,
        primary_pressure_id=None, policy_authorized=False)
    return {'catalog-v05.json':catalog, 'missing-quotes.json':dict(diagnostics=missing),
        'window-qualification.json':dict(windows=windows, ranking=None), 'verification.json':verification}


def main():
    outputs = run()
    for name, value in outputs.items():
        path = OUT / name
        if path.exists() and json.loads(path.read_text()) != value:
            raise ValueError('Different output already exists; preserve and choose a new version: ' + name)
        if not path.exists():
            dump(path, value)
    print(json.dumps(outputs['verification.json']))


if __name__ == '__main__':
    main()
