"""Offline archive verification only; no imports/calls into the stock product or network."""
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import re

SOURCE_URL = 'https://ecorp.ctbcbank.com/cts/static/ag_dividend_printer.jsp'
SOURCE_SHA = 'ac8340b658018958e500f576bdc7605475cea0f48dac010e2c5251a1750aa310'
HEADERS = ['證券代號', '公司名稱', '每股現金股利（元）', '除息交易日', '最後過戶日', '發放日']


class Rows(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []; self.cells = None; self.parts = None; self.start = None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.cells = []; self.start = self.getpos()
        if tag in ['th', 'td'] and self.cells is not None: self.parts = []

    def handle_data(self, data):
        if self.parts is not None: self.parts.append(data)

    def handle_endtag(self, tag):
        if tag in ['th', 'td'] and self.parts is not None:
            self.cells.append(re.sub(r'\s+', ' ', ''.join(self.parts)).strip()); self.parts = None
        if tag == 'tr' and self.cells is not None:
            self.rows.append(dict(line=self.start[0], column=self.start[1], cells=self.cells)); self.cells = None


def iso_roc(raw):
    y, m, d = map(int, raw.split('/'))
    return date(y + 1911, m, d).isoformat()


def derive(body):
    if len(body) != 647329 or hashlib.sha256(body).hexdigest() != SOURCE_SHA:
        raise ValueError('Exact archived original bytes required')
    text = body.decode('utf-8'); parser = Rows(); parser.feed(text)
    if '<title>中國信託法人信託部-除息(股票股利)</title>' not in text:
        raise ValueError('Source title mismatch')
    header = [row for row in parser.rows if row['cells'] == HEADERS]
    if len(header) != 1: raise ValueError('Exactly one source header with six roles required')
    prepared = [row for row in parser.rows if row['cells'] and '製表日期:' in row['cells'][-1]]
    if len(prepared) != 1: raise ValueError('One preparation label required')
    m = re.fullmatch(r'製表日期:\s*(\d+/\d+/\d+)', prepared[0]['cells'][-1])
    if not m: raise ValueError('Preparation date must come from its label')
    selected = [row for row in parser.rows if row['cells'] and row['cells'][0] in ['1101', '1101B']]
    result = []
    for row in selected:
        cells = row['cells']
        if len(cells) != 6: raise ValueError('Six exact cells required')
        code, company, amount, ex, transfer, pay = cells
        if not re.fullmatch(r'\d+(?:\.\d+)?', amount): raise ValueError('Published decimal string required')
        roles = dict(ex_trading_date=dict(raw=ex, iso=iso_roc(ex), role='EX_DIVIDEND_TRADING_DATE'),
            last_transfer_date=dict(raw=transfer, iso=iso_roc(transfer), role='LAST_TRANSFER_NOT_RECORD_DATE'),
            payment_date=dict(raw=pay, iso=iso_roc(pay), role='AGENT_COMPANY_PAYMENT_SCHEDULE_NOT_PERSONAL_RECEIPT'))
        result.append(dict(source_id='ctbc-agent-dividend-table-codex-20261023', source_sha256=SOURCE_SHA,
            source_line=row['line'], source_column=row['column'], header_line=header[0]['line'], raw_cells=cells,
            issuer_code='1101', security_code=code, company_name=company,
            instrument='1101_ORDINARY' if code == '1101' else '1101B_PREFERRED_B',
            amount=amount, amount_unit='TWD_PER_THIS_INSTRUMENT_SHARE',
            published_decimal_places=len(amount.split('.')[1]) if '.' in amount else 0,
            ex_trading_calendar_year=roles['ex_trading_date']['iso'][:4], earnings_year=None,
            dates=roles, record_date=None, personal_receipt_at=None, personal_net_amount=None,
            personal_entitled_shares=None, final_adjusted_amount=None, tax_origin_subtype=None,
            announced_at=None, historical_signal_eligible=False, qualification='COMPANY_SOURCE_CROSS_CORROBORATION_NOT_LEDGER'))
    return dict(source_url=SOURCE_URL, source_sha256=SOURCE_SHA, source_bytes=len(body),
        preparation_date=dict(raw=m[1], iso=iso_roc(m[1]), role='DOCUMENT_PREPARATION_NOT_PUBLICATION_OR_COVERAGE'),
        source_headers=HEADERS, header_line=header[0]['line'], selected_rows=result,
        code_2884_rows_in_this_response=sum(bool(row['cells']) and row['cells'][0] == '2884' for row in parser.rows),
        absence_proves_no_2884_events=False, complete_action_coverage=False,
        ledger_events_added=0, independent_market_samples_added=0,
        execution_qualified=False, imputed_close=None, valuation=None,
        historical_signal_eligible=False, primary_pressure_id=None, policy_authorized=False)


def verify(folder):
    folder = Path(folder); body = (folder / 'raw/ctbc-dividend.response').read_bytes()
    actual = derive(body); saved = json.loads((folder / 'ctbc-dividend.selection.json').read_text())
    if actual != saved: raise ValueError('Saved source selection/roles/unknowns differ from actual source')
    meta = json.loads((folder / 'raw/ctbc-dividend.meta.json').read_text())
    if (meta['http'] != 200 or meta['url'] != SOURCE_URL or meta['final_url'] != SOURCE_URL
            or meta['bytes'] != len(body) or meta['sha256'] != SOURCE_SHA
            or meta['retries'] != 0 or meta['redirects_followed'] is not False
            or meta['work_archive_obtained'] is not False or meta['announced_at'] is not None
            or meta['work_github_readback_at'] is not None or meta['historical_signal_eligible'] is not False):
        raise ValueError('New capture/source/time roles mismatch')
    times = [datetime.fromisoformat(meta[k]) for k in ['requested_at', 'completed_at', 'local_source_readback_at']]
    if any(t.tzinfo is None for t in times) or times != sorted(times): raise ValueError('Capture/readback time roles mismatch')
    if meta['captured_at'] != meta['completed_at']: raise ValueError('Capture is not Work observation or preparation date')
    if any(k.lower() in ['set-cookie', 'set-cookie2', 'cookie', 'authorization', 'proxy-authorization'] for k in meta['headers']):
        raise ValueError('Private session headers must not be in public archive')
    return dict(status='PASS', scope='OFFLINE_SOURCE_ARCHIVE_VERIFICATION_NOT_PRODUCT_TESTS',
        actual_source_bytes=len(body), source_sha256=SOURCE_SHA, selected_rows=len(actual['selected_rows']),
        six_header_roles_verified=True, raw_decimal_strings_preserved=True,
        preparation_not_announcement=True, record_and_personal_rights_unknown=True,
        exact_source_and_selection_equal=True, company_scope_only=True, product_tests_run=0)


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent), ensure_ascii=False))
