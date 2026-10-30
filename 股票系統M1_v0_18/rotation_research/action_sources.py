"""Offline field-level extraction of archived exchange/issuer action evidence.

No network, guessed par value, reference-price inversion, or event-free claim.
Run explicitly with python3 -m rotation_research.action_sources.
"""
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import re
from graph_core.core import fingerprint, number

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = HERE / 'action_data_20261022'
REVIEW = ROOT / 'docs/visual-discussion/20261022_b_basis_source_work_review'


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


class TableRows(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.cells=None; self.texts=None

    def handle_starttag(self, tag, attrs):
        if tag=='tr': self.cells=[]
        if tag in ('td','th') and self.cells is not None: self.texts=[]

    def handle_data(self, text):
        if self.texts is not None: self.texts.append(text)

    def handle_endtag(self, tag):
        if tag in ('td','th') and self.texts is not None:
            self.cells.append(' '.join(''.join(self.texts).split())); self.texts=None
        if tag=='tr' and self.cells is not None:
            if self.cells: self.rows.append(self.cells)
            self.cells=None


def iso(text, roc=False):
    parts=list(map(int,re.findall(r'\d+',text)))
    if len(parts)!=3: raise ValueError('Unrecognized source date: '+text)
    y,m,d=parts
    return date(y+1911 if roc else y,m,d).isoformat()


def checked_source(path, meta, captured_key):
    raw=path.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    if sha!=meta['sha256'] or len(raw)!=meta['bytes']: raise ValueError('Archive hash/length mismatch: '+str(path))
    return dict(path=str(path.relative_to(ROOT)), sha256=sha, url=meta['url'],
                captured_at=meta[captured_key], kind='OFFICIAL_ARCHIVE',
                historical_publication_time='NOT_AUTHENTICATED')


def build_catalog():
    old=json.loads((HERE/'generated/input.json').read_text())
    captures=json.loads((REVIEW/'source-capture.json').read_text())
    sources={}; exchange=[]; issuer={}
    for capture in captures:
        if capture['name'] not in ('exright-2025','exright-2026-to-cutoff'): continue
        sid=capture['name']; path=REVIEW/'raw'/f'{sid}.json'
        sources[sid]=checked_source(path,capture,'observed_at')
        data=json.loads(path.read_text())
        if data['stat']!='OK': raise ValueError('Exchange status not OK')
        for i,row in enumerate(data['data']):
            fields=dict(zip(data['fields'],row))
            if fields['股票代號'] not in old['assets']: continue
            when=iso(fields['資料日期'],True)
            if old['assets'][fields['股票代號']]['bars'][0]['date']<=when<=old['assets'][fields['股票代號']]['bars'][-1]['date']:
                exchange.append((sid,i,fields,when))
    for code, filename in [('1101','tcc_dividends.html'),('2884','esun_shareholders.html')]:
        path=HERE.parent/'event_audit/raw'/filename
        meta=json.loads(path.with_name(path.name+'.meta.json').read_text())
        sid='issuer-'+code; sources[sid]=checked_source(path,meta,'fetched_at_utc')
        parser=TableRows();parser.feed(path.read_text())
        issuer[code]=parser.rows
        expected='股利所屬盈餘年度' if code=='1101' else '除息基準日'
        if not any(expected in row for row in parser.rows): raise ValueError('Issuer table header changed')
    events=[]
    for sid, idx, row, when in exchange:
        code=row['股票代號']; year=int(when[:4]); isid='issuer-'+code
        if code=='1101':
            matches=[(i,r) for i,r in enumerate(issuer[code]) if len(r)==8 and re.fullmatch(r'\d{4}/\d{2}/\d{2}',r[5]) and iso(r[5])==when]
        else:
            matches=[(i,r) for i,r in enumerate(issuer[code]) if len(r)==7 and r[0]==str(year)]
        if len(matches)!=1: raise ValueError('Ambiguous/missing issuer row')
        ii, ir=matches[0]
        def exproof(column): return [dict(source_id=sid,locator=f'data[{idx}].{column}',raw_value=row[column])]
        def iproof(column): return [dict(source_id=isid,locator=f'html_table_rows[{ii}][{column}]',raw_value=ir[column])]
        base=dict(code=code,mode='RAW',basis_id=old['assets'][code]['basis_id'],ex_date=when,
                  announced_at=None, historical_signal_eligible=False, observed_at=sources[sid]['captured_at'],
                  source_ids=[sid,isid], field_sources={'ex_date':exproof('資料日期')},
                  exchange_row_index=idx,exchange_raw_fields=row,issuer_row_index=ii,issuer_raw_cells=ir,
                  date_semantics='EXCHANGE_EX_TRADING_DATE_NOT_ISSUER_RECORD_DATE',
                  completeness='PARTIAL_COMPONENT_EVIDENCE_NOT_FULL_ACTION_COVERAGE')
        gross, pay = (ir[2],iso(ir[7])) if code=='1101' else (ir[2],iso(ir[3]))
        if number(gross)<0: raise ValueError('Invalid issuer amount')
        # Pure cash events can be cross-checked directly; mixed rights cannot be inverted.
        if row['權/息']=='息' and number(gross)!=number(row['權值+息值']): raise ValueError('Cash amount conflict')
        cash=dict(base,type='CASH_DIVIDEND',gross_per_share=gross,net_per_share=None,pay_date=pay,
                  record_date=None if code=='1101' else iso(ir[1]),
                  pay_date_role='ISSUER_SCHEDULE_NOT_INVESTOR_RECEIPT',
                  missing=['announced_at','investor_net_per_share','investor_actual_receipt'],
                  field_sources={**base['field_sources'],'gross_per_share':iproof(2),'pay_date':iproof(7 if code=='1101' else 3)})
        if code=='2884': cash['field_sources']['record_date']=iproof(1)
        cash['id']=fingerprint(cash);events.append(cash)
        if '權' in row['權/息']:
            if code!='2884' or ir[5] in ('-','0'): raise ValueError('Unparsed stock dividend')
            stock=dict(base,type='STOCK_DIVIDEND',stock_dividend_money_per_share=ir[5],shares_per_share=None,
                       par_value=None,record_date=iso(ir[4]),delivery_date=iso(ir[6]),tradable_date=None,
                       delivery_role='ISSUER_DISTRIBUTION_SCHEDULE_NOT_VERIFIED_LISTING_DATE',
                       missing=['announced_at','sourced_share_ratio_or_par_value','tradable_date','fractional_disposition'],
                       field_sources={**base['field_sources'],'stock_dividend_money_per_share':iproof(5),
                                      'record_date':iproof(4),'delivery_date':iproof(6)})
            stock['id']=fingerprint(stock);events.append(stock)
    events.sort(key=lambda e:(e['ex_date'],e['code'],e['type']))
    coverage={c:dict(status='INCOMPLETE_DO_NOT_ASSUME_NO_EVENTS',start=old['assets'][c]['bars'][0]['date'],
                   end=old['assets'][c]['bars'][-1]['date'],event_ids=[e['id'] for e in events if e['code']==c],
                   source_ids=list(sources),types=['CASH_DIVIDEND','STOCK_DIVIDEND'],other_actions_checked=False,
                   gaps=['NO_EXHAUSTIVE_CAPITAL_REDUCTION_OR_OTHER_ACTION_REGISTER',
                         'EXCHANGE_2026_CAPTURE_ENDS_2026-07-24_MISSING_2026-07-25_TO_2026-10-16',
                         'EXRIGHT_ENDPOINT_EXCLUSIONS_NOT_COMPLETE_CORPORATE_ACTION_UNIVERSE']) for c in old['assets']}
    return dict(schema='rotation-action-catalog/0.1',mode='RAW',sources=sources,events=events,coverage=coverage,
                quote_input_path=str((HERE/'generated/input.json').relative_to(ROOT)),
                quote_input_sha256=hashlib.sha256((HERE/'generated/input.json').read_bytes()).hexdigest(),
                primary_pressure_id=None,policy_authorized=False,historical_signal_eligible=False,
                known_time_rule='captured_at proves this archive observation only; announced_at remains null',
                total_net_return_qualified=False)


def main():
    OUT.mkdir(exist_ok=True); catalog=build_catalog();dump(OUT/'events.json',catalog)
    print(json.dumps(dict(events=len(catalog['events']),sources=len(catalog['sources']),
                          id=fingerprint(catalog),total_net_return_qualified=False)))


if __name__=='__main__': main()
