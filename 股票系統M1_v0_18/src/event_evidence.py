"""Offline evidence staging. Never forwards issuer record dates to engines.

Source identity/hash must be checked by the runner. These parsers validate
captured response contents; they do not authenticate arbitrary HTML or certify
all corporate actions in a period. No network, UI or storage dependency.
"""
from datetime import date
from html.parser import HTMLParser
from decimal import localcontext, ROUND_HALF_EVEN
import re
from contracts import DataError, iso_date, number, validate_candles

TPEX_TITLE='因颱風過境，台北市政府宣布7月10日全日停止上班，櫃檯買賣有價證券市場及衍生性金融商品市場休市一日'


def parse_tpex_reviewed_closure(payload):
    """Only the manually reviewed 22926 case; unknown titles fail closed."""
    if payload.get('stat','').lower()!='ok' or payload.get('date')!='20260709~20260710':
        raise DataError('SOURCE_PERIOD_OR_STATUS','date','Expected reviewed query period and OK status')
    tables=payload.get('tables',[])
    if len(tables)!=1:raise DataError('SOURCE_FIELDS','tables','One reviewed news table required')
    t=tables[0];rows=t.get('data',[])
    if t.get('title')!='櫃買新聞稿' or t.get('fields')!=['日期','標題','id']:
        raise DataError('SOURCE_FIELDS','fields','Unexpected news schema')
    if t.get('totalCount')!=len(rows):raise DataError('SOURCE_PAGINATION','totalCount','Incomplete queried list')
    if any(len(r)!=3 for r in rows):raise DataError('SOURCE_ROW_WIDTH','data','Incomplete news row')
    matches=[r for r in rows if r[2]=='22926']
    if len(matches)!=1 or matches[0][:2]!=['民國115年07月09日',TPEX_TITLE]:
        raise DataError('UNREVIEWED_CLOSURE','data','Reviewed primary title/date/id changed or absent')
    return dict(date='2026-07-10',exchange='TPEX',announced_at_date='2026-07-09',
                verification='OFFICIAL_PRIMARY_TEXT_RETRIEVED',announcement_id='22926',
                evidence_kind='OFFICIAL_NEWS_LIST_FULL_TITLE',coverage='ONE_CASE_ONLY_NOT_EXHAUSTIVE')


class _Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.tables=[];self.table=None;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='table':
            if self.table is not None:raise DataError('SOURCE_TABLE','html','Nested tables unsupported')
            self.table=[]
        elif tag=='tr' and self.table is not None:self.row=[]
        elif tag in ('td','th') and self.row is not None:self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.row.append(re.sub(r'\s+',' ',''.join(self.cell)).strip());self.cell=None
        elif tag=='tr' and self.row is not None:
            self.table.append(self.row);self.row=None
        elif tag=='table' and self.table is not None:
            self.tables.append(self.table);self.table=None


def _table(text,headers):
    p=_Tables();p.feed(text);p.close()
    tables=[t for t in p.tables if t[:len(headers)]==headers]
    if len(tables)!=1:raise DataError('SOURCE_FIELDS','html','Exactly one table with reviewed headers required')
    return tables[0][len(headers):]


def _row(rows,key,width):
    found=[r for r in rows if r and r[0]==str(key)]
    if len(found)!=1 or len(found[0])!=width:
        raise DataError('SOURCE_ROW','year','Unique complete target row required')
    return found[0]


def _date(text):
    return iso_date(text.replace('/','-').replace('.','-'),'source.date')


def parse_tcc_dividend(text,earnings_year=2025):
    headers=[['股利所屬盈餘年度','股東會','現金股利','股票股利','股利合計','除息交易日','除權交易日','現金股利發放日']]
    r=_row(_table(text,headers),earnings_year,8)
    cash=number(r[2],'cash');stock=number(r[3],'stock')
    if cash<0 or stock<0 or number(r[4],'total')!=cash+stock:
        raise DataError('SOURCE_DIVIDEND','amount','Invalid cash/stock/total relationship')
    return dict(code='1101',earnings_year=earnings_year,cash_per_share=str(cash),stock_dividend_per_share=str(stock),
                effective_date=_date(r[5]),effective_date_kind='EX_TRADING_DATE',record_date=None,
                payment_date=_date(r[7]),cash_fact_status='VERIFIED_PRIMARY_ROW',
                other_actions_coverage='UNVERIFIED',publication_time='UNVERIFIED')


def parse_esun_dividend(text,year=2026):
    headers=[['年度','現金股利','股票股利'],['除息基準日','每股新臺幣(元)','發放日','除權基準日','每股新臺幣(元)','發放日']]
    r=_row(_table(text,headers),year,7)
    cash=number(r[2],'cash')
    if cash<0:raise DataError('SOURCE_DIVIDEND','cash','Negative dividend')
    # A dash is preserved as a source marker, never inferred as verified zero.
    stock=None if r[5]=='-' else str(number(r[5],'stock'))
    return dict(code='2884',distribution_year=year,cash_per_share=str(cash),stock_dividend_per_share=stock,
                stock_source_marker=r[5],effective_date=None,effective_date_kind='UNVERIFIED',
                record_date=_date(r[1]),record_date_kind='CASH_DIVIDEND_RECORD_DATE',payment_date=_date(r[3]),
                cash_fact_status='VERIFIED_PRIMARY_ROW',other_actions_coverage='UNVERIFIED',publication_time='UNVERIFIED')


def stage_cash_factor(fact,candles):
    """Compute a diagnostic candidate only; never return an engine event.

    All current results remain unapproved pending reference crosscheck. Coverage
    and publication timing remain separate from individual event facts.
    """
    validate_candles(candles)
    reasons=[];candidate=None;basis=None
    if fact.get('effective_date_kind')!='EX_TRADING_DATE' or not fact.get('effective_date'):
        reasons.append('EX_TRADING_DATE_NOT_VERIFIED')
    else:
        dt=iso_date(fact['effective_date'],'effective_date')
        dates=[c['date'] for c in candles]
        if dt not in dates or dates.index(dt)==0:reasons.append('PRICE_BASIS_NOT_AVAILABLE')
        elif fact.get('cash_fact_status')!='VERIFIED_PRIMARY_ROW':reasons.append('CASH_FACT_NOT_VERIFIED')
        elif fact.get('stock_dividend_per_share') is None or number(fact['stock_dividend_per_share'],'stock')!=0:
            reasons.append('CASH_ONLY_EVENT_NOT_ESTABLISHED')
        else:
            prev=candles[dates.index(dt)-1];close=number(prev['close'],'preclose');cash=number(fact['cash_per_share'],'cash')
            if cash<=0 or close<=cash:reasons.append('INVALID_CASH_FACTOR_BASIS')
            else:
                with localcontext() as ctx:
                    ctx.prec=28;ctx.rounding=ROUND_HALF_EVEN;candidate=str((close-cash)/close)
                basis=dict(date=prev['date'],close=str(close),effective_date=dt,cash_per_share=str(cash))
                reasons.append('OFFICIAL_REFERENCE_CROSSCHECK_PENDING')
    return dict(status='STAGED_NOT_ENGINE_READY',diagnostic_factor=candidate,basis=basis,blocked_reasons=reasons,
                approved_engine_events=[],period_action_coverage='UNVERIFIED',classification_quality='NOT_VALIDATED')
