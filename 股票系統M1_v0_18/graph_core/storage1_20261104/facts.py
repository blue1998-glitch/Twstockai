"""Pure source-fact projection using the existing official parser only.
No history joining, indicators, recognition, account calculation or IO.
"""
from decimal import Context,localcontext,ROUND_HALF_EVEN
from graph_core import market_daily as d
LABELS={'SOURCE_BAR_AVAILABLE':'行情可用','DATA_QUALITY_FAILURE':'價量資料不合格','MISSING_QUOTE':'缺少當日行情','NO_TRADE_REPORTED_ZERO_VOLUME':'當日無成交','NO_VALID_CLOSE_SUSPENSION_NOT_AUTHENTICATED':'無有效收盤，未認證停牌','ISIN_CHANGED_CONTINUITY_REFUSED':'股票身分變動，拒絕接續'}
def project(member,raw,*,as_of,capture_id,daily_sha256,parent_isin=None):
    market=member['market'];code=member['code']
    if market not in ('TWSE','TPEX') or not member['cfi'].startswith('ES') or not member.get('isin'):raise ValueError('ORDINARY_IDENTITY_REQUIRED')
    key='Code' if market=='TWSE' else 'SecuritiesCompanyCode'
    if raw is not None and (str(raw[key]).strip()!=code or d.day(raw['Date'])!=as_of):raise ValueError('OFFICIAL_STOCK_OR_DATE_CONFLICT')
    state='SOURCE_BAR_AVAILABLE';bar=None;error=None
    if parent_isin is not None and parent_isin!=member['isin']:state='ISIN_CHANGED_CONTINUITY_REFUSED'
    elif raw is None:state='MISSING_QUOTE'
    else:
        try:
            with localcontext(Context(prec=34,rounding=ROUND_HALF_EVEN)):bar,reason=d.candle(raw,market)
            if reason:state=reason
        except (ValueError,KeyError,ArithmeticError) as exc:state='DATA_QUALITY_FAILURE';error=type(exc).__name__
    return dict(schema='official-daily-fact/0.1',identity=market+':'+code,code=code,name=member['name'],market=market,isin=member['isin'],cfi=member['cfi'],as_of=as_of,
        source_status=state,source_label=LABELS[state],bar=bar,original_record=raw,parser_error_type=error,
        source=dict(capture_id=capture_id,daily_sha256=daily_sha256,volume_unit='SHARES_REPORTED',price_mode='RAW_CANDIDATE',price_basis_id=market+':'+code+'-OFFICIAL-RAW-UNBRIDGED-'+as_of,announced_at=None,historical_publication_timing='UNKNOWN'),
        analysis_status='NOT_EXECUTED',continuity='NOT_CERTIFIED_NO_HISTORY_APPENDED',execution_qualified=False,historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False,imputed_close=None,valuation=None)
