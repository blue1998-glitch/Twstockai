"""Pure company-level component research 0.9; no prices, personal grants or IO."""
from copy import deepcopy
from datetime import date,datetime
import re
import unicodedata

from .action_scope import identify,verify,resolve_field
from . import source_contracts as parent
from .source_followup import compact,one,field,evidence_sha,roc,QUALIFICATION

SCHEMA='rotation-capital-components-research/0.9'
PARENT_ID='sha256:77e3dfa0e10ff3b64f67e1613575c26158d814efe025753d5138c8b76641cd80'
SOURCE_ID='esun-prospectus-20260722'
EVIDENCE_SHA='f529d6e10c866fb111a3da0e73d577255d82c69c21a6d48b7ca31931486e9683'
PROVENANCE_SHA='26b3712a0bec64b518f294a707b20fd55f18d000f965fcbe33fdc12b5dfbf78c'
COLUMNS=[('share_count','股數(仟股)','THOUSAND_SHARES'),('ordinary_share_capital','普通股股本','THOUSAND_TWD'),
    ('capital_surplus','資本公積','THOUSAND_TWD'),('legal_reserve','法定盈餘公積','THOUSAND_TWD'),
    ('special_reserve','特別盈餘公積','THOUSAND_TWD'),('unappropriated_earnings','未分配盈餘','THOUSAND_TWD'),
    ('translation','國外營運機構財務報表換算之兌換差額','THOUSAND_TWD'),
    ('fvoci','透過其他綜合損益按公允價值衡量之金融資產未實現評價損益','THOUSAND_TWD'),
    ('own_credit','指定按公允價值衡量之金融負債信用風險變動影響數','THOUSAND_TWD'),
    ('non_controlling','非控制權益','THOUSAND_TWD'),('total_equity','權益總額','THOUSAND_TWD')]


def row_cells(section,code,label):
    pattern=re.compile(r'^'+re.escape(code)+r'\s+'+r'\s*'.join(map(re.escape,label))+r'\s+(.+)$')
    rows=[m for line in section.splitlines() if (m:=pattern.match(line))]
    if len(rows)!=1:raise ValueError('One explicit row required: '+code)
    text=rows[0][1];token=r'\(\s*(?:\$\s*)?[\d,]+\s*\)|(?:\$\s*)?[\d,]+|-'
    cells=re.findall(token,text)
    if len(cells)!=len(COLUMNS) or re.sub(token,'',text).strip():raise ValueError('Expected eleven numeric columns')
    result={}
    for (name,title,unit),raw in zip(COLUMNS,cells):
        s=re.sub(r'[\s,$]','',raw)
        value=None if s=='-' else ('-'+s[1:-1] if s.startswith('(') else s)
        result[name]=dict(value=value,unit=unit,column_label=title,raw_cell=raw,source_marker='DASH_NOT_DEFAULTED_TO_ZERO' if value is None else 'REPORTED_NUMBER')
    return dict(row_code=code,row_label=label,cells=result)


def parse_equity(text,statement_year,earnings_year):
    native=unicodedata.normalize('NFKC',text);s=compact(text)
    if '玉山金融控股股份有限公司及子公司合併權益變動表' not in s:raise ValueError('Wrong issuer/table')
    header=native.split('\nA1',1)[0];h=compact(header)
    for title in ['單位:新臺幣仟元','股本(附註三九)資本公積保留盈餘','股數(仟股)普通股股本','權益總額']:
        if title not in h:raise ValueError('Column/unit header missing or reordered: '+title)
    if not re.search(r'法定盈餘公積特別盈餘公積未分配盈餘.*?權益總額',h):raise ValueError('Reserve/total column order mismatch')
    boundaries=list(re.finditer(r'^Z1\s+(\d+)\s*年\s*12\s*月\s*31\s*日餘額',native,re.M))
    opening=[m for m in boundaries if int(m[1])+1911==int(statement_year)-1]
    closing=[m for m in boundaries if int(m[1])+1911==int(statement_year)]
    if len(opening)!=1 or len(closing)!=1 or opening[0].start()>=closing[0].start():raise ValueError('Explicit consecutive closing-balance boundaries required')
    section=native[opening[0].end():closing[0].start()]
    # Preserve the row boundary: compacting joins the prior balance's final number to the year.
    years=re.findall(r'^\s*(\d+)\s*年\s*度\s*盈\s*餘\s*分\s*配\s*$',section,re.M)
    if years!=[str(int(earnings_year)-1911)]:raise ValueError('Wrong profit-distribution year within selected statement span')
    rows={code:row_cells(section,code,label) for code,label in [('B9','股東紅利-股票'),('N1','股份基礎給付交易-員工酬勞轉增資')]}
    required={'B9':['share_count','ordinary_share_capital'],'N1':['share_count','ordinary_share_capital','capital_surplus','total_equity']}
    if any(rows[k]['cells'][c]['value'] is None for k,cols in required.items() for c in cols):raise ValueError('Required published component is unknown')
    n=rows['N1']['cells']
    if int(n['ordinary_share_capital']['value'])+int(n['capital_surplus']['value'])!=int(n['total_equity']['value']):raise ValueError('Employee equity-account reconciliation fails')
    return dict(statement_year=statement_year,earnings_year=earnings_year,
        start_after_balance_date=f'{int(statement_year)-1}-12-31',end_before_balance_date=statement_year+'-12-31',
        money_unit_header='單位:新臺幣仟元',share_column_header='股數(仟股)',rows=rows)


def parse_board(text,earnings_year):
    s=compact(text)
    head=one(r'母公司分別於(\d+)年(\d+)月(\d+)日及(\d+)年(\d+)月(\d+)日董事會決議配發(\d+)及(\d+)年度員工酬勞及董事酬勞如下:',s)
    headers=one(r'如下:(\d+)年度(\d+)年度員工酬勞-現金',s)
    body=one(r'母公司(\d+)及(\d+)年度員工酬勞股數皆為([\d,]+)仟股,係分別按董事會決議之金額除以董事會決議日前一日之收盤價([\d.]+)元及([\d.]+)元計算',s)
    years=[head[7],head[8]]
    if years!=list(headers.groups()) or years!=[body[1],body[2]]:raise ValueError('Board/table/reference-year column pairing mismatch')
    versions=[]
    for i,parts in enumerate([head.groups()[:3],head.groups()[3:6]]):
        versions.append(dict(earnings_year=str(int(years[i])+1911),board_date=roc(parts),
            employee_quantity=body[3].replace(',',''),quantity_unit='THOUSAND_SHARES',
            calculation_reference=body[4+i],reference_unit='TWD_PER_SHARE',
            reference_role='ISSUER_REPORTED_CALCULATION_REFERENCE_NOT_RAW_PRICE_TRADE_OR_VALUATION',
            source_column_ordinal=i+1,source_column_label=years[i]+'年度'))
    selected=[v for v in versions if v['earnings_year']==earnings_year]
    if len(selected)!=1:raise ValueError('One explicit earnings-year version required')
    return dict(selected=selected[0],versions=versions,selection='EXPLICIT_EARNINGS_YEAR_NOT_LATEST_OR_FIRST_COLUMN')


def observations(facts,source):
    table,board=facts['equity_table'],facts['board_reference']['selected'];result=[]
    def add(kind,holder,instrument,values,page,locator):
        fs={}
        for key,(value,unit,role) in values.items():
            proof=[] if value is None else [dict(source_id=SOURCE_ID,physical_pdf_page=page,printed_page={391:11,456:76}[page],locator=locator,native_evidence_sha256=EVIDENCE_SHA,normalized_value=value)]
            fs[key]=field(value,unit,role,proof,QUALIFICATION)
        result.append(identify(dict(family='2884-2025-capitalization-source-reconciliation',issuer_code='2884',
            entitled_old_code=holder,old_instrument=instrument,action_type=kind,source_ids=[SOURCE_ID],fields=fs,
            source_captured_at=source['original_official_capture']['completed_at'],observed_at=source['codex_analysis_observed_at'],
            announced_at=None,accounting_eligible=False,historical_signal_eligible=False)))
    def v(value,unit='TEXT',role='COMPANY_AGGREGATE_NOT_PERSONAL'):return value,unit,role
    common=dict(statement_year=v(table['statement_year'],'YEAR','FINANCIAL_STATEMENT_YEAR'),
        earnings_year=v(table['earnings_year'],'YEAR','DISTRIBUTED_EARNINGS_YEAR'),
        span_start=v(table['start_after_balance_date'],'ISO_DATE','AFTER_PRIOR_CLOSING_BALANCE_NOT_PAYMENT'),
        span_end=v(table['end_before_balance_date'],'ISO_DATE','BEFORE_CURRENT_CLOSING_BALANCE_NOT_LISTING'),
        personal_allotted_shares=v(None,'SHARES'),personal_unrounded_ratio=v(None,'SHARES_PER_OLD_SHARE'),
        fractional_deadline=v(None,'ISO_DATE'),fractional_disposition=v(None),listing_date=v(None,'ISO_DATE'),
        tradable_date=v(None,'ISO_DATE'),personal_net_cash=v(None,'TWD'),opening_entitlement=v(None,'SHARES'))
    for code,kind,holder in [('B9','SHAREHOLDER_STOCK_BONUS_GROUP_REPORTED','2884_SHAREHOLDERS_COMPANY_GROUP_NOT_PERSONAL'),
            ('N1','EMPLOYEE_CAPITALIZATION_GROUP_REPORTED','2884_EMPLOYEES_COMPANY_GROUP_NOT_PERSONAL')]:
        row=table['rows'][code];fs=dict(common,row_code=v(code),row_label=v(row['row_label']))
        for name in (['share_count','ordinary_share_capital'] if code=='B9' else ['share_count','ordinary_share_capital','capital_surplus','total_equity']):
            c=row['cells'][name];fs[name]=v(c['value'],c['unit'],'REPORTED_COLUMN:'+c['column_label'])
        add(kind,holder,'2884_ORDINARY_COMPANY_GROUP_NOT_PERSONAL_ALLOTMENT',fs,391,
            table['start_after_balance_date']+' closing row < '+table['earnings_year']+' earnings / '+code+' '+row['row_label']+' < '+table['end_before_balance_date']+' closing row; exact column labels in equity_table')
    add('EMPLOYEE_BOARD_CALCULATION_REFERENCE','2884_EMPLOYEES_COMPANY_GROUP_NOT_PERSONAL','2884_EMPLOYEE_REMUNERATION_NOT_RAW_QUOTE',dict(
        earnings_year=v(board['earnings_year'],'YEAR','EMPLOYEE_EARNINGS_YEAR'),board_date=v(board['board_date'],'ISO_DATE','BOARD_RESOLUTION_NOT_PERSONAL_RECEIPT_OR_LISTING'),
        employee_quantity=v(board['employee_quantity'],board['quantity_unit']),
        calculation_reference=v(board['calculation_reference'],board['reference_unit'],board['reference_role']),
        personal_transaction_price=v(None,'TWD_PER_SHARE'),raw_price=v(None,'TWD_PER_SHARE'),imputed_close=v(None,'TWD_PER_SHARE'),valuation=v(None,'TWD')),
        456,'Selected '+board['source_column_label']+'; paired board date, equal-share wording and respectively paired reference')
    return result


def reconcile(catalog):
    table=catalog['facts']['equity_table'];b=table['rows']['B9']['cells'];n=table['rows']['N1']['cells']
    old=catalog['parent_catalog'];groups={o['action_type']:o for o in old['observations']}
    selected=[groups[k] for k in ['SHAREHOLDER_BONUS_CAPITALIZATION_REPORTED','EMPLOYEE_REMUNERATION_CAPITALIZATION_REPORTED','COMBINED_CAPITALIZATION_SHARES_REPORTED']]
    total=selected[2]['fields']['combined_quantity']
    if (b['share_count']['unit']!=n['share_count']['unit'] or total['unit']!=n['share_count']['unit']
            or total['unit']!='THOUSAND_SHARES'):raise ValueError('Share units cannot be borrowed from currency columns')
    if any(c['unit']!='THOUSAND_TWD' for c in [b['ordinary_share_capital'],n['ordinary_share_capital'],n['capital_surplus'],n['total_equity'],
            selected[0]['fields']['bonus_amount'],selected[1]['fields']['remuneration_amount']]):raise ValueError('Monetary account units must stay separate from shares')
    share_sum=str(int(b['share_count']['value'])+int(n['share_count']['value']))
    money_sum=str(int(n['ordinary_share_capital']['value'])+int(n['capital_surplus']['value']))
    checks=dict(group_shares_equal_parent_combined=share_sum==total['value'],
        employee_accounts_equal_reported_equity=money_sum==n['total_equity']['value'],
        employee_equity_equal_parent_remuneration=money_sum==selected[1]['fields']['remuneration_amount']['value'],
        shareholder_capital_equal_parent_bonus=b['ordinary_share_capital']['value']==selected[0]['fields']['bonus_amount']['value'],
        employee_shares_equal_board_statement=n['share_count']['value']==catalog['facts']['board_reference']['selected']['employee_quantity'])
    if not all(checks.values()):raise ValueError('Same-family source reconciliation fails')
    return dict(family='2884-2025-capitalization-source-reconciliation',qualification='SOURCE_CROSS_REFERENCE_NOT_AUTOMATIC_EVENT_MERGE_OR_PERSONAL_ALLOCATION',
        parent_p461_observation_ids=[o['id'] for o in selected],new_observation_ids=[o['id'] for o in catalog['observations']],
        share_sum=share_sum,share_unit='THOUSAND_SHARES',parent_combined_shares=total['value'],
        employee_account_sum=money_sum,money_unit='THOUSAND_TWD',checks=checks,
        numeric_ledger_events_added=0,independent_market_samples_added=0,personal_final_ratio=None,personal_allotment=None)


def validate(catalog):
    verify(catalog)
    if catalog['schema']!=SCHEMA:raise ValueError('Explicit capital component research version required')
    parent.validate(catalog['parent_catalog'])
    if catalog['parent_catalog_id']!=PARENT_ID or catalog['parent_catalog']['id']!=PARENT_ID or catalog['coverage']!=catalog['parent_catalog']['coverage']:
        raise ValueError('Exact complete parent0.8 and unchanged incomplete coverage required')
    for k,v in dict(historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False).items():
        if catalog[k]!=v:raise ValueError('Research-only flags required')
    source=catalog['source']
    if evidence_sha(source['manifest'])!=PROVENANCE_SHA:raise ValueError('Actual capture/readback/local-observation provenance changed')
    m=source['manifest']
    if (source['local_reuse_completed_at']!=m['local_reuse']['completed_at'] or source['codex_analysis_observed_at']!=m['codex_analysis_observed_at']
            or source['original_official_capture']!=m['original_official_capture']
            or source['prior_codex_github_readback_at']!=m['prior_codex_fixed_github_readback']['readback_at']
            or source['issuer_code']!='2884'):raise ValueError('Provenance role borrowing refused')
    if evidence_sha(source['native_evidence'])!=EVIDENCE_SHA:raise ValueError('Native source evidence changed')
    times=[datetime.fromisoformat(source[k]) for k in ['local_reuse_completed_at','codex_analysis_observed_at']]
    if any(t.tzinfo is None for t in times) or times[0]>times[1] or source['work_github_readback_at'] is not None or source['announced_at'] is not None:
        raise ValueError('Observation roles or unavailable historical timestamps promoted')
    facts=dict(equity_table=parse_equity(source['native_evidence']['391'],'2025','2024'),board_reference=parse_board(source['native_evidence']['456'],'2024'))
    if catalog['facts']!=facts or catalog['observations']!=observations(facts,source):raise ValueError('Company fact/holder/column/unit/date/unknown mismatch')
    if catalog['reconciliation']!=reconcile(catalog):raise ValueError('Source family cannot add independent events or personal grants')
    return catalog


def resolve(catalog,name,request):
    validate(catalog);matches=[o for o in catalog['observations'] if o['id']==request.get('version_id')]
    if len(matches)!=1:raise ValueError('One explicit company source observation required')
    return resolve_field(matches[0],name,request)


def qualify(data,catalog):
    validate(catalog)
    if data.get('capital_components_catalog_id')!=catalog['id']:raise ValueError('Exact new source version required')
    old=deepcopy(data);old.pop('capital_components_catalog_id')
    return dict(deepcopy(parent.qualify(old,catalog['parent_catalog'])),capital_components_catalog_id=catalog['id'])
