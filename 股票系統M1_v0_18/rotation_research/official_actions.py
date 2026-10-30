"""Offline issuer evidence supplement; no strategy, fills or old-result writes.

Published monetary precision is retained. An issuer completion report is not a
share-listing notice, investor receipt, exhaustive register or historical signal.
"""
from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from graph_core.core import fingerprint
from .action_sources import ROOT, HERE, dump
from .action_study import verified_quotes
from .source_qualification import build_calendar, window_audit
from .official_action_capture import OUT, HOSTS


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_capture(name, out=OUT):
    meta = json.loads((Path(out) / 'raw' / (name + '.meta.json')).read_text())
    if meta['status'] != 'CAPTURED' or meta.get('http') != 200:
        raise ValueError('Failed capture is not valid source data')
    if any(urlsplit(meta[k]).scheme != 'https' or urlsplit(meta[k]).netloc not in HOSTS for k in ('url', 'final_url')):
        raise ValueError('Unapproved source origin')
    path = Path(out) / 'raw' / (name + '.response')
    body = path.read_bytes()
    if sha(body) != meta['sha256'] or len(body) != meta['bytes']:
        raise ValueError('Capture fingerprint mismatch')
    source = dict(path=str(path.relative_to(ROOT)), url=meta['url'], sha256=sha(body),
                  captured_at=meta['attempted_at'], kind='OFFICIAL_ARCHIVE',
                  historical_publication_time='NOT_AUTHENTICATED')
    return body, source, meta


def security_denial(body):
    text = body.decode('utf-8', errors='replace')
    return any(s in text for s in ('FOR SECURITY REASONS', '因為安全性考量', 'THIS PAGE CAN NOT BE ACCESSED'))


def read_pdf_text(name, out=OUT, variant=''):
    body, source, meta = read_capture(name, out)
    if security_denial(body) or not body.startswith(b'%PDF-') or 'application/pdf' not in meta.get('content_type', ''):
        raise ValueError('Not an official PDF document')
    text_name = name + variant
    extracted = json.loads((Path(out) / 'raw' / (text_name + '.extraction.json')).read_text())
    text = (Path(out) / 'raw' / (text_name + '.txt')).read_bytes()
    if extracted['pdf_sha256'] != sha(body) or extracted['text_sha256'] != sha(text):
        raise ValueError('PDF/text extraction fingerprint mismatch')
    source['derived_text'] = dict(path=str((Path(out) / 'raw' / (text_name + '.txt')).relative_to(ROOT)),
                                  sha256=sha(text), extraction=extracted)
    return text.decode('utf-8'), source


def compact(text):
    return re.sub(r'\s+', '', text)


def parse_minutes(text):
    """Extract this issuer's approved issue, distinguishing approximate proposal.

    No fixed meeting date, par value, final ratio or event ID is supplied here.
    """
    all_text = compact(text)
    meeting = re.search(r'時間[：:](\d+)年(\d+)月(\d+)日', all_text)
    if not meeting or '玉山金融控股股份有限公司' not in all_text:
        raise ValueError('Unknown issuer/meeting document')
    meeting_date = date(int(meeting[1]) + 1911, int(meeting[2]), int(meeting[3])).isoformat()
    pages = text.split('\f')
    issue = [(i, compact(page)) for i, page in enumerate(pages)
             if '盈餘暨員工酬勞轉增資' in compact(page) and '每股面額' in compact(page)]
    if len(issue) != 1:
        raise ValueError('Missing/ambiguous approved issuance section')
    index, section = issue[0]
    pars = set(re.findall(r'每股面額([\d.]+)元', section))
    capital = re.search(r'股東股票股利([\d,]+)元[，,]發行([\d,]+)股', section)
    fiscal = re.search(r'本公司(\d+)年度盈餘分派案', all_text)
    proposal = re.search(r'每千股無償配發約([\d.]+)股', section)
    if len(pars) != 1 or not capital or not fiscal or not proposal:
        raise ValueError('Required issue fields not found unambiguously')
    par = next(iter(pars))
    amount, shares = [x.replace(',', '') for x in capital.groups()]
    if Decimal(par) <= 0 or Decimal(amount) / Decimal(shares) != Decimal(par):
        raise ValueError('Issue amount/share count conflicts with stated par')
    following = compact(pages[index + 1]) if index + 1 < len(pages) else ''
    if '本案表決通過' not in following or '配股率因此發生變動' not in following:
        raise ValueError('Approved resolution/adjustable ratio qualification absent')
    if '按面額折發現金（至元為止）' not in section or '元以下捨去' not in all_text:
        raise ValueError('Fraction/cash rounding wording not authenticated')
    fraction_clause = re.search(r'配股不足一股之畸零股.*?按面額認購。', section)
    if not fraction_clause:
        raise ValueError('Full fractional policy clause not found')
    return dict(issuer='2884', meeting_date=meeting_date, fiscal_year=int(fiscal[1]) + 1911,
                par_value=par, shareholder_issue_amount=amount, shareholder_issue_shares=shares,
                approximate_proposed_shares_per_thousand=proposal[1],
                proposal_is_final_ratio=False, ratio_adjustment_authorized=True,
                issue_pdf_page=index + 1, resolution_pdf_page=index + 2,
                fractional_policy='POOL_BEFORE_UNSPECIFIED_DEADLINE_THEN_PAR_CASH_TO_WHOLE_TWD',
                fractional_policy_raw=fraction_clause[0],
                fractional_deadline=None, actual_fraction_cash_received=None,
                cash_distribution_rounding='FLOOR_TO_WHOLE_TWD_REMAINDER_TO_ISSUER',
                announced_at=None, historical_signal_eligible=False)


def parse_follow_up(text):
    section = compact(text)
    completion = re.search(r'並已於(\d{4}\.\d{2}\.\d{2})發放完畢', section)
    record = re.search(r'已訂(\d{4}\.\d{2}\.\d{2})為盈餘分派', section)
    if not completion or not record or '通過盈餘暨員工酬勞轉增資案' not in section:
        raise ValueError('Issuer completion statement not found')
    # Meeting date comes from the document's time column, not the first date in its layout.
    times = re.findall(r'\d{4}\.\d{2}\.\d{2}', section)
    other_dates = sorted(set(times) - {completion[1], record[1]})
    if len(other_dates) != 1:
        raise ValueError('Ambiguous meeting date')
    return dict(meeting_date=other_dates[0].replace('.', '-'),
                issuer_record_date=record[1].replace('.', '-'),
                issuer_reported_distribution_completed_on=completion[1].replace('.', '-'),
                tradable_date=None, investor_receipt_at=None, investor_net_amount=None,
                status='ISSUER_REPORTED_COMPLETION_NOT_INVESTOR_RECEIPT_OR_LISTING')


def stock_ratio(money_per_share, par_value):
    try:
        money, par = Decimal(money_per_share), Decimal(par_value)
        if not money.is_finite() or not par.is_finite() or money < 0 or par <= 0:
            raise ValueError('Invalid monetary dividend/par')
        with localcontext() as ctx:
            ctx.prec = 60
            return format(money / par, 'f')
    except (InvalidOperation, TypeError, ZeroDivisionError) as exc:
        raise ValueError('Missing/invalid sourced monetary dividend/par') from exc


def supplement_catalog(original, minutes, follow, sources):
    """New version only; never promote source coverage or investor-level rights."""
    result = deepcopy(original)
    result.update(schema='rotation-action-catalog/0.2-issuer-supplement',
                  supersedes_catalog_id=fingerprint(original))
    result['sources'].update(deepcopy(sources))
    selected = [e for e in result['events'] if e['code'] == minutes['issuer']
                and e['type'] == 'STOCK_DIVIDEND' and e['record_date'] == follow['issuer_record_date']
                and int(e['record_date'][:4]) == minutes['fiscal_year'] + 1]
    if len(selected) != 1 or minutes['meeting_date'] != follow['meeting_date']:
        raise ValueError('Issuer documents do not match exactly one saved stock component')
    e = selected[0]
    if e['delivery_date'] != follow['issuer_reported_distribution_completed_on']:
        raise ValueError('Completion date conflicts with saved issuer schedule')
    old_id = e.pop('id')
    e.update(supersedes_event_id=old_id, par_value=minutes['par_value'],
             original_component_observed_at=e['observed_at'],
             observed_at=max([e['observed_at']] + [s['captured_at'] for s in sources.values()]),
             shares_per_share=stock_ratio(e['stock_dividend_money_per_share'], minutes['par_value']),
             ratio_role='DERIVED_FROM_PUBLISHED_MONEY_AND_SAME_ISSUE_PAR_NOT_EXACT_UNROUNDED_ALLOTMENT',
             ratio_calculation=dict(expression='stock_dividend_money_per_share / par_value',
                                    input_unit='TWD_PER_OLD_SHARE / TWD_PER_NEW_SHARE',
                                    result_unit='NEW_SHARES_PER_OLD_SHARE'),
             issuer_completion=deepcopy(follow), fractional_policy=minutes['fractional_policy'],
             fractional_deadline=None, fractional_disposition=None,
             missing=['announced_at', 'tradable_date', 'final_allotment_precision',
                      'fractional_deadline_and_investor_disposition'])
    for sid in sources:
        e['source_ids'].append(sid)
    e['field_sources']['par_value'] = [dict(source_id='esun-2025-minutes', locator=f'PDF page {minutes["issue_pdf_page"]}: 發行新股／每股面額', raw_value=minutes['par_value'])]
    e['field_sources']['shares_per_share'] = deepcopy(e['field_sources']['stock_dividend_money_per_share']) + deepcopy(e['field_sources']['par_value'])
    e['field_sources']['issuer_completion'] = [dict(source_id='esun-2025-follow-up', locator='PDF page 1: 執行情形', raw_value=follow['issuer_reported_distribution_completed_on'])]
    e['field_sources']['fractional_policy'] = [dict(source_id='esun-2025-minutes', locator=f'PDF page {minutes["issue_pdf_page"]}: 第五項／畸零股（移除抽字空白）', raw_value=minutes['fractional_policy_raw'])]
    e['id'] = fingerprint(e)
    for coverage in result['coverage'].values():
        coverage['event_ids'] = [e['id'] if i == old_id else i for i in coverage['event_ids']]
    result['coverage'][e['code']]['source_ids'].extend(sources)
    result['source_supplement_scope'] = 'ONE_ISSUER_COMPONENT_NOT_EXHAUSTIVE_ACTION_REGISTER'
    return result


def build():
    original = json.loads((HERE / 'action_data_20261022/events.json').read_text())
    # Also ensure all four original source archives and extracted components still match.
    from .action_sources import build_catalog
    if original != build_catalog():
        raise ValueError('Original source catalog changed; do not overwrite it')
    minutes_text, ms = read_pdf_text('esun-2025-minutes')
    follow_text, fs = read_pdf_text('esun-2025-follow-up', variant='.reading-order')
    archived_link_page = (HERE.parent / 'event_audit/raw/esun_shareholders.html').read_text()
    if any(s['url'] not in archived_link_page for s in (ms, fs)):
        raise ValueError('PDF not linked by original issuer archive')
    minutes, follow = parse_minutes(minutes_text), parse_follow_up(follow_text)
    sources = {'esun-2025-minutes': ms, 'esun-2025-follow-up': fs}
    catalog = supplement_catalog(original, minutes, follow, sources)
    body, denied_source, _ = read_capture('mops-announcements-entry')
    denied = security_denial(body)
    if not denied:
        raise ValueError('MOPS response changed; inspect before automatic interpretation')
    old, manifest = verified_quotes()
    audit = window_audit(old, catalog, manifest, build_calendar())
    stock = next(e for e in catalog['events'] if e['type'] == 'STOCK_DIVIDEND')
    verification = dict(official_pdfs=2, mops_http_200_security_denial=True,
        new_company_action_events=0, enriched_stock_components=1,
        par_value=stock['par_value'], shares_per_share=stock['shares_per_share'],
        ratio_precision=stock['ratio_role'], tradable_date=None,
        calendar_qualified_windows=audit['calendar_qualified_windows'],
        total_net_return_qualified_windows=audit['total_net_return_qualified_windows'],
        original_quote_archives_rechecked=len(manifest), strategy_replays=0,
        browser_runs=0, android='NOT_TESTED_NEW_BUILD', primary_pressure_id=None)
    return dict(catalog=catalog, minutes=minutes, follow_up=follow, windows=audit,
                source_manifest=dict(sources=sources, mops=dict(source=denied_source,
                    qualification='SECURITY_DENIAL_NOT_EMPTY_DATA', usable=False,
                    retry_or_bypass=False), configuration_change='RUNTIME_SPEC_3_ALLOWED_TWO_OFFICIAL_HOSTS'),
                verification=verification)


def main():
    result = build()
    for key, filename in [('catalog', 'events-v02.json'), ('minutes', 'minutes-facts.json'),
                          ('follow_up', 'completion-facts.json'), ('windows', 'window-qualification.json'),
                          ('source_manifest', 'source-manifest.json'), ('verification', 'verification.json')]:
        dump(OUT / filename, result[key])
    print(json.dumps(result['verification'], ensure_ascii=False))


if __name__ == '__main__':
    main()
