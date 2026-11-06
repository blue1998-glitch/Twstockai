"""Pure source-only 0.7 facts. No network, prices, ledger replay or policy."""
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from html.parser import HTMLParser
import hashlib
import json
import re
import unicodedata

from .action_scope import identify, verify, resolve_field
from . import offline_source_bridge as parent

SCHEMA = 'rotation-source-followup/0.7'
PARENT_ID = 'sha256:ffc954ac915889a4fbd8b2d2e71b219cb38fbfe192d7cc08823abe2f04d3b6eb'
QUALIFICATION = 'SOURCE_FACT_NOT_FINAL_LEDGER'
TAIFEX = 'taifex-esun-resumption-20251106'
ESUN = 'esun-issuer-closing-completed-20260902'
TCC = 'tcc-2026-q2-consolidated-report'
EVIDENCE_SHA = {
    TAIFEX:'d8e6d98c04d876b2b22bb00c2909c41fa48c8eba2cba09a5c6f43a771844e62d',
    ESUN:'afef2d9aadf88b98cbddce7807a2b9c5301c375f272850078dba3215f7fcf92a',
    TCC:'54327224bcffb6765a0a2077cf9e0a9ad6df11aa48cb6f0ef473d38558521927',
}


def evidence_sha(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def field(value, unit, role, proofs, qualification):
    return dict(value=value,unit=unit,date_role=role,proofs=proofs,qualification=qualification)


def compact(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text))


def one(pattern, text):
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        raise ValueError('Exactly one source statement required: ' + pattern)
    return matches[0]


def roc(parts):
    y, m, d = map(int, parts)
    return date(y + 1911, m, d).isoformat()


def parse_taifex(text, issuer_code, instrument):
    s = compact(text)
    if (issuer_code != '2884' or instrument != '2884_ORDINARY_OLD_SHARES'
            or set(re.findall(r'證券代號[:：](\d+)', s)) != {issuer_code}
            or '臺灣期貨交易所股份有限公司函' not in s):
        raise ValueError('TAIFEX issuer/instrument mismatch')
    document = roc(one(r'發文日期[:：]中華民國(\d+)年(\d+)月(\d+)日', s).groups())
    number = one(r'發文字號[:：](台期交字第\d+號)', s)[1]
    primary = one(r'主旨[:：]公告玉山金期貨及選擇權\(契約代號[:：](\w+)\)自(\d+)年(\d+)月(\d+)日起恢復交易', s)
    underlying = one(r'因玉山金融控股股份有限公司\(證券代號[:：](\d+)\)自(\d+)年(\d+)月(\d+)日起恢復交易', s)
    dates = {roc(m) for m in re.findall(r'自(\d+)年(\d+)月(\d+)日起恢復交易', s)}
    resume = roc(underlying.groups()[1:])
    if primary[1] != 'DN' or dates != {resume} or document > resume:
        raise ValueError('Conflicting contract/stock resumption/document dates')
    return dict(document_date=document, document_number=number, stock_resumption_date=resume,
                derivatives_resumption_date=roc(primary.groups()[1:]), contract_code=primary[1])


class Article(HTMLParser):
    """Read just the article section, excluding scripts, navigation and related news."""
    def __init__(self):
        super().__init__(); self.stack = []; self.sections = 0
        self.parts = {k: [] for k in ('title', 'date', 'body')}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs); classes = a.get('class', '').split()
        active = self.stack[-1][1] if self.stack else False
        if tag == 'section' and 'l-news' in classes:
            self.sections += 1; active = True
        role = self.stack[-1][2] if self.stack else None
        if active:
            if a.get('id') == 'news-title': role = 'title'
            elif 'newsDate' in classes: role = 'date'
            elif 'l-news__content' in classes: role = 'body'
        skip = tag in ('script', 'style') or (self.stack and self.stack[-1][3])
        if tag not in ('img', 'hr', 'br', 'input', 'meta', 'link', 'source', 'wbr'):
            self.stack.append((tag, active, role, bool(skip)))

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]; break

    def handle_data(self, data):
        if self.stack:
            _, active, role, skip = self.stack[-1]
            if active and role and not skip: self.parts[role].append(data)


def article_text(html):
    p = Article(); p.feed(html)
    if p.sections != 1 or not all(p.parts.values()):
        raise ValueError('One complete issuer article required')
    return {k: ''.join(v).strip() for k, v in p.parts.items()}


def parse_esun(article):
    title, body = compact(article['title']), compact(article['body'])
    if '玉山金控完成合意併購三商美邦人壽' not in title:
        raise ValueError('Wrong issuer article')
    displayed = one(r'(\d{4})/(\d{2})/(\d{2})', article['date'])
    page_date = date(*map(int, displayed.groups())).isoformat()
    closing = one(r'玉山金控今\((\d+)\)日完成與三商壽之股權交割程序', body)
    if not 1 <= int(closing[1]) <= 31 or '三商壽自即日起正式成為玉山金控子公司' not in body:
        raise ValueError('Issuer closing completion wording absent')
    approved = one(r'今日金控董事會也通過參與三商壽([\d.]+)億元現金增資', body)
    if '三商壽既有保戶之權益將獲得百分之百保障' not in body:
        raise ValueError('Policyholder scope missing')
    return dict(page_display_date=page_date, body_day_text=closing[0], body_day=closing[1],
                date_conflict=displayed[3] != closing[1].zfill(2),
                closing_stage='ISSUER_REPORTED_CLOSING_COMPLETED',
                board_participation_amount=approved[1], board_participation_unit='HUNDRED_MILLION_TWD',
                capital_increase_stage='BOARD_APPROVED_PARTICIPATION_ONLY')


def parse_tcc(pages):
    if set(pages) != {'7', '52', '54', '55', '57'}:
        raise ValueError('Explicit selected report pages required')
    s52, s54, s55, s57 = (compact(pages[str(n)]) for n in (52, 54, 55, 57))
    cancelled = one(r'本公司於(\d+)年(\d+)月辦理註銷庫藏股([\d,]+)仟股', s52)
    year, month = int(cancelled[1])+1911, int(cancelled[2])
    date(year, month, 1)  # validate the month; never output an invented day
    quantity = cancelled[3].replace(',', '')
    treasury = s57.split('(七)庫藏股', 1)
    if len(treasury) != 2 or '單位:仟股數' not in treasury[1]:
        raise ValueError('Treasury table/unit missing')
    # Column separation is retained in the native text. Do not join two years' numbers.
    table = pages['57'].split('庫 藏 股', 1)
    if len(table) != 2: raise ValueError('Native treasury heading absent')
    a = one(r'期初股數\s+([\d,]+)\s+([\d,]+)', table[1])
    b = one(r'本期註銷\s+\(\s*([\d,]+)\s*\)\s+-', table[1])
    c = one(r'期末股數\s+([\d,]+)\s+([\d,]+)', table[1])
    start, cancel, end = (m[1].replace(',', '') for m in (a, b, c))
    if cancel != quantity or int(start)-int(cancel) != int(end):
        raise ValueError('Treasury reconciliation/cancellation mismatch')
    approved = one(r'本公司於(\d+)年(\d+)月股東常會決議以資本公積發放現金,每股配發新台幣([\d.]+)元,共計配發([\d,]+)仟元', s55)
    if '股票發行溢價' not in s54 or '資本公積' not in s54:
        raise ValueError('Capital-surplus balance table missing')
    return dict(cancellation_month=f'{year:04d}-{month:02d}', cancellation_quantity=quantity,
                treasury_opening=start, treasury_cancelled=cancel, treasury_closing=end,
                quantity_unit='THOUSAND_SHARES', approved_cash_per_share=approved[3],
                approved_total=approved[4].replace(',', ''), total_unit='THOUSAND_TWD',
                native_page7_text_empty=not pages['7'].strip())


def observations(facts, sources):
    result = []
    def add(sid, code, holder, instrument, kind, values, page):
        fs = {}
        for name, (value, unit, role) in values.items():
            proof = [] if value is None else [dict(source_id=sid, locator=page,
                native_evidence_sha256=EVIDENCE_SHA[sid], normalized_value=value)]
            fs[name] = field(value, unit, role, proof, QUALIFICATION)
        result.append(identify(dict(family='source-followup:'+kind+':'+code, issuer_code=code,
            entitled_old_code=holder, old_instrument=instrument, action_type=kind, source_ids=[sid],
            observed_at=sources[sid]['readback_at'], source_captured_at=sources[sid]['captured_at'],
            announced_at=None, accounting_eligible=False, historical_signal_eligible=False, fields=fs)))
    def v(value, unit='TEXT', role='SOURCE_ONLY_NOT_ENTITLEMENT'): return (value, unit, role)
    a, b, c = (facts[s] for s in (TAIFEX, ESUN, TCC))
    add(TAIFEX,'2884','NOT_AN_ENTITLEMENT','2884_ORDINARY_OLD_SHARES',
        'TAIFEX_CORROBORATES_UNDERLYING_RESUMPTION', dict(
            document_date=v(a['document_date'],'ISO_DATE','SOURCE_DOCUMENT_DATE_NOT_PUBLICATION'),
            document_number=v(a['document_number']), stock_resumption_date=v(a['stock_resumption_date'],'ISO_DATE','TAIFEX_STATES_STOCK_RESUMPTION_NOT_TWSE_DIRECT'),
            authority=v('TAIFEX_OFFICIAL_CORROBORATION_NOT_TWSE_DIRECT'),
            suspension_end_date=v(None,'ISO_DATE','SUSPENSION_END_NOT_AUTHENTICATED')), 'PDF page 1 explanation 2; heading separate')
    add(TAIFEX,'2884','NOT_AN_ENTITLEMENT','DN_FUTURES_AND_OPTIONS',
        'DERIVATIVES_RESUMPTION', dict(contract_code=v(a['contract_code']),
            derivatives_resumption_date=v(a['derivatives_resumption_date'],'ISO_DATE','DERIVATIVES_RESUMPTION_NOT_STOCK_DIRECT_NOTICE')), 'PDF page 1 subject')
    add(ESUN,'2884','NOT_AN_ENTITLEMENT','ISSUER_MNA_REPORT_NOT_ALLOTMENT',
        'ISSUER_CLOSING_REPORT', dict(
            stage=v(b['closing_stage']),page_display_date=v(b['page_display_date'],'ISO_DATE','PAGE_DISPLAY_DATE_NOT_EFFECTIVE'),
            body_day_text=v(b['body_day_text']),date_conflict=v(b['date_conflict'],'BOOLEAN'),
            canonical_effective_at=v(None,'ISO_DATE','DATE_CONFLICT_UNRESOLVED'),
            actual_issued_shares=v(None,'SHARES'),existing_2884_entitlement=v(None,'SHARES_PER_OLD_SHARE'),
            existing_2884_impact=v(None),board_participation_amount=v(b['board_participation_amount'],b['board_participation_unit'],'BOARD_APPROVAL_NOT_PAYMENT'),
            capital_increase_stage=v(b['capital_increase_stage']), capital_increase_paid=v(None,'TWD'),
            protected_recipient=v('SANSHANG_EXISTING_POLICYHOLDERS_NOT_2884_SHAREHOLDERS')), 'HTML l-news only; date and body paragraphs 1-3')
    add(TCC,'1101','ISSUER_TREASURY_NOT_PRO_RATA_HOLDERS','1101_ISSUER_TREASURY_SHARES',
        'TREASURY_CANCELLATION_MONTH_REPORTED', dict(
            cancellation_month=v(c['cancellation_month'],'ISO_MONTH','CANCELLATION_MONTH_NOT_EXACT_DAY'),
            cancellation_quantity=v(c['cancellation_quantity'],c['quantity_unit']),
            exact_effective_date=v(None,'ISO_DATE'),holder_conversion_ratio=v(None,'SHARES_PER_OLD_SHARE'),holder_cashflow=v(None,'TWD'),
            treasury_opening=v(c['treasury_opening'],c['quantity_unit'],'HALF_YEAR_OPENING_BALANCE_NOT_EVENT'),
            treasury_cancelled=v(c['treasury_cancelled'],c['quantity_unit'],'HALF_YEAR_MOVEMENT_SAME_CANCELLATION_NOT_NEW_EVENT'),
            treasury_closing=v(c['treasury_closing'],c['quantity_unit'],'HALF_YEAR_CLOSING_BALANCE_NOT_EVENT')), 'PDF pages 52 and 57; one cancellation observation')
    add(TCC,'1101','1101','1101_ORDINARY_OLD_SHARES','FINANCIAL_REPORT_RESOLUTION_CORROBORATION', dict(
        approved_cash_per_share=v(c['approved_cash_per_share'],'TWD_PER_SHARE','APPROVED_NOT_FINAL_ADJUSTED'),
        report_total=v(c['approved_total'],c['total_unit'],'PUBLISHED_THOUSAND_TWD_PRECISION_NOT_REPLACEMENT'),
        final_adjusted_per_share=v(None,'TWD_PER_SHARE'),tax_origin_subtype=v(None),personal_net_cash=v(None,'TWD'),
        actual_investor_receipt=v(None,'TWD'),native_page7_text_empty=v(c['native_page7_text_empty'],'BOOLEAN','EXTRACTION_STATUS_NOT_PAGE_ABSENCE')),
        'PDF page 55; p54 balances not granular payout tax source; p7 scanned table viewed')
    return result


def validate(catalog):
    verify(catalog)
    if catalog['schema'] != SCHEMA: raise ValueError('Explicit source followup version required')
    parent.validate(catalog['parent_catalog'])
    if (catalog['parent_catalog_id'] != PARENT_ID or catalog['parent_catalog']['id'] != PARENT_ID
            or catalog['coverage'] != catalog['parent_catalog']['coverage']):
        raise ValueError('Exact parent0.6 and unchanged incomplete coverage required')
    if any(catalog[k] != v for k,v in dict(historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False).items()):
        raise ValueError('Research-only flags required')
    sources = catalog['sources']
    if set(sources) != {TAIFEX, ESUN, TCC}: raise ValueError('Explicit three-source version required')
    for s in sources.values():
        times = [datetime.fromisoformat(s[k]) for k in ('requested_at','completed_at','captured_at','readback_at')]
        if any(t.tzinfo is None for t in times) or times != sorted(times) or s['announced_at'] is not None:
            raise ValueError('Separate aware capture/readback times required; no announcement backfill')
    if any(evidence_sha(sources[s]['native_evidence']) != EVIDENCE_SHA.get(s) for s in sources):
        raise ValueError('Archived native evidence fingerprint mismatch')
    parsed = {TAIFEX:parse_taifex(sources[TAIFEX]['native_evidence']['text'],'2884','2884_ORDINARY_OLD_SHARES'),
              ESUN:parse_esun(sources[ESUN]['native_evidence']),TCC:parse_tcc(sources[TCC]['native_evidence'])}
    if catalog['facts'] != parsed:
        raise ValueError('Facts must agree with immutable source-bound native evidence')
    expected = observations(catalog['facts'], sources)
    if catalog['observations'] != expected:
        raise ValueError('Identity, scope, role, precision or unknown field promoted away from parsed evidence')
    return catalog


def resolve(catalog, name, request):
    validate(catalog)
    matches = [o for o in catalog['observations'] if o['id'] == request.get('version_id')]
    if len(matches) != 1: raise ValueError('One explicit new source version required')
    return resolve_field(matches[0], name, request)


def quote_diagnostic(catalog, code, when, raw_close, market_session):
    validate(catalog)
    old = parent.quote_diagnostic(catalog['parent_catalog'], code, when, raw_close, market_session)
    matches = [o for o in catalog['observations'] if o['action_type']=='TAIFEX_CORROBORATES_UNDERLYING_RESUMPTION'
        and o['issuer_code']==code and o['fields']['stock_resumption_date']['value']==when]
    return dict(parent_diagnostic=deepcopy(old), related_resumption_corroboration_ids=[o['id'] for o in matches],
        direct_twse_resumption_acquired=False, suspension_end_date=None, raw_close=raw_close,
        imputed_close=None, valuation=None, execution_qualified=False, missing_quote_blocks_accounting=raw_close is None)


def precision_comparison(catalog):
    validate(catalog)
    formal = catalog['parent_catalog']['parent_catalog']['parent_catalog']
    precise = [o for o in formal['inventory'] if o['issuer_code']=='1101' and o['action_type']=='CASH_DISTRIBUTION_RESOLUTION']
    if len(precise)!=1: raise ValueError('One parent approved-resolution source required')
    original = precise[0]['fields']['approved_total_twd']['value']
    published = catalog['facts'][TCC]['approved_total']
    return dict(parent_resolution_id=precise[0]['id'], parent_approved_total_twd=original,
        new_report_total=published, new_report_unit='THOUSAND_TWD',
        difference_from_scaled_display_twd=str(Decimal(original)-Decimal(published)*1000),
        interpretation='DIFFERENT_PUBLISHED_PRECISION_NOT_EVIDENCE_OF_ADJUSTMENT_OR_CONTRADICTION',
        parent_total_replaced=False, final_adjusted_per_share=None, tax_origin_subtype=None, personal_net_cash=None)


def qualify(data, catalog):
    validate(catalog)
    if data.get('source_followup_catalog_id') != catalog['id']:
        raise ValueError('Exact new source version must be bound')
    old = deepcopy(data); old.pop('source_followup_catalog_id')
    result = parent.qualify(old, catalog['parent_catalog'])
    return dict(deepcopy(result), source_followup_catalog_id=catalog['id'],
        source_followup_parent_qualification=deepcopy(result))
