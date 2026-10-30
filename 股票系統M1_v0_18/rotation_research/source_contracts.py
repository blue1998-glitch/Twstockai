"""Pure, source-only contract research 0.8. No IO, allocations or net ledger."""
from copy import deepcopy
from datetime import date, datetime
import re

from .action_scope import identify, verify, resolve_field
from . import source_followup as parent

SCHEMA = 'rotation-source-contract-research/0.8'
PARENT_ID = 'sha256:49528167bede030b29359a77abebd3f8947c88e58aeaaeede62c42a76465cc89'
PROSPECTUS = 'esun-prospectus-20260722'
FOLLOWUP = 'esun-follow-up-2026'
EVIDENCE_SHA = {
    PROSPECTUS:'69ce063c9d1ec7fd1ba8c38075e5d08f3fb2830e19ffdbe6ae5f6b1b56663f47',
    FOLLOWUP:'80b4c0a4e92a1a9f743f91f1133db7ff9bb3ce0699c0c90c02c6b27061497552',
}
compact, one, field = parent.compact, parent.one, parent.field


def parse_prospectus(pages, party_a_code, party_b_code, meeting_year):
    if set(pages) != {'162','163','175','176','461'} or (party_a_code,party_b_code)!=('2884','2867'):
        raise ValueError('Explicit selected pages and known company-code identities required')
    a,b,c,d,e = (compact(pages[str(n)]) for n in (162,163,175,176,461))
    parties=one(r'係由(玉山金融控股股份有限公司)\(統一編號為:(\d+),以下稱「甲方」\)與(三商美邦人壽保險股份有限公司)\(統一編號為:(\d+),以下稱「乙方」\)',a)
    if parties[2]!='70796305' or parties[4]!='84443471':
        raise ValueError('Contract party/company identity mismatch')
    signed=parent.roc(one(r'於民國\(下同\)(\d+)年(\d+)月(\d+)日',a).groups())
    conditional=one(r'倘甲乙任一方之股東就股份轉換依法表示異議並請求買回其持股時,該方應依法令規定收買該異議股東所持有之股份。因本條所買回之股份,應依相關法令規定出售或銷除。',c)[0]
    if '第9條異議股份之處理' not in c or '第10條乙方員工之權益保障' not in c:
        raise ValueError('Article 9/10 boundaries missing')
    ratio=one(r'以乙方每一股普通股股份換發甲方([\d.]+)股普通股之比例',b)[1]
    one(r'如本交易經甲乙雙方股東會分別決議通過,並取得主管機關許可後',b)
    one(r'乙方股東因股份轉換取得不滿甲方普通股一股之畸零股部分',b)
    one(r'股份轉換基準日前之最後交易日收盤價',b)
    one(r'不足1元部分應四捨五入至新台幣「元」為止',b)
    estimated=one(r'已發行普通股預計為([\d,]+)股',b)[1].replace(',','')
    rights=one(r'甲方所發行之新股普通股之權利義務與甲方已發行之上市普通股相同。',b)[0]
    taxes=one(r'除本契約另有約定者外,因本契約之協商、簽訂或履行所生之一切稅捐及費用.*?應由甲方、乙方及/或其股東各自負擔。',d)[0]
    if '第14條稅捐及費用' not in d or '15.2' not in d or '共同另行議定之' not in d:
        raise ValueError('Tax/amendment scope missing')
    matches=list(re.finditer(r'母公司(\d+)年股東常會決議,自(\d+)年度盈餘分派股東紅利([\d,]+)仟元及員工酬勞([\d,]+)仟元轉增資發行新股,共計發行新股([\d,]+)仟股。是項增資案已向金管會申報生效,並已向經濟部辦妥變更登記。',e))
    selected=[m for m in matches if str(int(m[1])+1911)==meeting_year]
    if len(selected)!=1: raise ValueError('One explicitly requested capitalization meeting year required')
    capital=selected[0]
    par=one(r'已發行之普通股每股面額為([\d.]+)元',e)[1]
    return dict(party_a_name=parties[1],party_a_uniform_id=parties[2],party_a_code=party_a_code,
        party_b_name=parties[3],party_b_uniform_id=parties[4],party_b_code=party_b_code,
        contract_signed_date=signed,dissent_clause=conditional,original_exchange_ratio=ratio,
        estimated_post_exchange_total_shares=estimated,new_share_rights_clause=rights,tax_expense_clause=taxes,
        meeting_year=str(int(capital[1])+1911),earnings_year=str(int(capital[2])+1911),
        shareholder_bonus_thousand_twd=capital[3].replace(',',''),employee_remuneration_thousand_twd=capital[4].replace(',',''),
        combined_new_thousand_shares=capital[5].replace(',',''),par_twd_per_share=par,
        registration_stage='ISSUER_REPORTED_REGISTRATION_COMPLETED_NOT_LISTING')


def parse_followup(pages, issuer_code):
    if set(pages)!={'1'} or issuer_code!='2884':
        raise ValueError('Exact official Esun archive owner and page required')
    s=compact(pages['1'])
    if '2026年第一次股東臨時會議案後續執行情形及檢討' not in s:
        raise ValueError('Wrong follow-up report')
    approval=one(r'本案業於(\d{4})\.(\d{2})\.(\d{2})取得金管會核准。',s)
    approval_date=date(*map(int,approval.groups())).isoformat()
    # Column extraction interleaves the approval sentence with the issuer name.
    rest=s.replace(approval[0],'')
    dates=re.findall(r'(\d{4})\.(\d{2})\.(\d{2})',rest)
    if len(dates)!=1: raise ValueError('One meeting table date required')
    meeting=date(*map(int,dates[0])).isoformat()
    target=re.sub(r'\d{4}\.\d{2}\.\d{2}','',rest)
    one(r'通過以股份轉換方式取得三商美邦人壽保險股份有限公司全部已發行股份案',target)
    if meeting>approval_date: raise ValueError('Approval precedes the reported meeting')
    return dict(meeting_resolution_date=meeting,regulatory_approval_date=approval_date,
        stage='ISSUER_REPORTED_SHAREHOLDER_RESOLUTION_AND_REGULATORY_APPROVAL',
        issuer_identity_basis='OFFICIAL_ESUNFHC_ARCHIVE_URL_AND_BYTE_PIN_NOT_CODE_PRINTED_IN_BODY')


def observations(facts, sources):
    result=[];a=facts[PROSPECTUS];b=facts[FOLLOWUP]
    def v(value,unit='TEXT',role='SOURCE_FACT_NOT_ENTITLEMENT',pages=None):return value,unit,role,pages
    def add(sid,holder,instrument,kind,values,default_pages):
        fs={}
        for name,(value,unit,role,pages) in values.items():
            physical=pages or default_pages
            proof=[] if value is None else [dict(source_id=sid,physical_pdf_pages=physical,
                native_evidence_sha256=EVIDENCE_SHA[sid],normalized_value=value)]
            fs[name]=field(value,unit,role,proof,parent.QUALIFICATION)
        result.append(identify(dict(family='source-contracts:'+kind,issuer_code='2884',entitled_old_code=holder,
            old_instrument=instrument,action_type=kind,source_ids=[sid],fields=fs,
            source_captured_at=sources[sid]['captured_at'],observed_at=sources[sid]['readback_at'],
            announced_at=None,accounting_eligible=False,historical_signal_eligible=False)))
    fs={k:v(a[k],pages=[162]) for k in ['party_a_name','party_a_uniform_id','party_a_code','party_b_name','party_b_uniform_id','party_b_code']}
    fs.update(contract_signed_date=v(a['contract_signed_date'],'ISO_DATE','CONTRACT_SIGNATURE_NOT_ANNOUNCEMENT',[162]),
        dissent_clause=v(a['dissent_clause'],pages=[175]),
        condition=v('IF_EITHER_PARTY_SHAREHOLDER_LAWFULLY_DISSENTS_AND_REQUESTS_REPURCHASE',pages=[175]),
        disposal_rule=v('SELL_OR_CANCEL_AS_REQUIRED_BY_LAW_NOT_OBSERVED_DISPOSAL',pages=[175]))
    for k,u in [('personal_eligibility','BOOLEAN'),('person_exercised','BOOLEAN'),('request_date','ISO_DATE'),
        ('repurchase_price','TWD_PER_SHARE'),('quantity','SHARES'),('payment','TWD'),('actual_disposition','TEXT'),('later_amendment_applicability','BOOLEAN')]:
        fs[k]=v(None,u,'PERSONAL_OR_LATER_APPLICABILITY_NOT_AUTHENTICATED')
    add(PROSPECTUS,'BOTH_2884_AND_2867_CONDITIONAL_DISSENTERS','BOTH_PARTIES_ORDINARY_HOLDERS_CONDITIONAL_NOT_GRANT',
        'CONTRACT_PARTIES_AND_CONDITIONAL_DISSENT',fs,[162,175,176])
    add(PROSPECTUS,'2867','2867_ORDINARY_OLD_SHARES','ORIGINAL_EXCHANGE_TERMS',dict(
        original_ratio=v(a['original_exchange_ratio'],'NEW_2884_SHARES_PER_OLD_2867_SHARE','ORIGINAL_CONTRACT_CONDITIONAL_NOT_FINAL_GRANT'),
        approval_condition=v('BOTH_SHAREHOLDER_MEETINGS_AND_REGULATORY_APPROVAL_REQUIRED'),
        fractional_scope=v('ORIGINAL_2867_SHARE_EXCHANGE_ONLY_NOT_2025_DIVIDEND_OR_OLD_2884'),
        fractional_reference=v('LAST_2884_CLOSE_BEFORE_EXCHANGE_RECORD_DATE_NOT_FIXED_AMOUNT'),
        fractional_rounding=v('ROUND_TO_WHOLE_TWD','POLICY','THIS_CONDITIONAL_EXCHANGE_ONLY'),
        estimated_post_exchange_total_shares=v(a['estimated_post_exchange_total_shares'],'SHARES','ESTIMATED_TOTAL_NOT_ACTUAL_NEW_ISSUANCE'),
        new_share_rights_clause=v(a['new_share_rights_clause']),actual_issued_shares=v(None,'SHARES'),
        personal_fractional_payment=v(None,'TWD'),existing_2884_impact=v(None),personal_final_ratio=v(None,'SHARES_PER_OLD_SHARE')),[163])
    add(PROSPECTUS,'EMPLOYEES_AND_CONTRACT_PARTIES_NOT_GENERIC_2884_HOLDERS','CONTRACT_EMPLOYMENT_AND_TAX_NOT_SHARE_GRANT',
        'CONTRACT_EMPLOYEE_AND_TAX_SCOPE',dict(
        protected_employees=v('2867_EMPLOYEES_WITH_CONTRACT_EXCLUSIONS_NOT_2884_SHAREHOLDER_GRANT',pages=[175]),
        tax_expense_clause=v(a['tax_expense_clause'],pages=[176]),employee_share_grant=v(None,'SHARES'),
        personal_tax=v(None,'TWD'),nhi=v(None,'TWD'),fees=v(None,'TWD'),personal_net_cash=v(None,'TWD'),tax_exempt=v(None,'BOOLEAN')),[175,176])
    shared=dict(meeting_year=v(a['meeting_year'],'YEAR','AGM_YEAR_NOT_LISTING_DATE'),
        earnings_year=v(a['earnings_year'],'YEAR','EARNINGS_REFERENCE_YEAR_NOT_PAYMENT_DATE'))
    add(PROSPECTUS,'2884','2884_ORDINARY_OLD_SHARES','SHAREHOLDER_BONUS_CAPITALIZATION_REPORTED',dict(shared,
        bonus_amount=v(a['shareholder_bonus_thousand_twd'],'THOUSAND_TWD','SHAREHOLDER_BONUS_NOT_EMPLOYEE_REMUNERATION'),
        personal_allotted_shares=v(None,'SHARES'),personal_unrounded_ratio=v(None,'SHARES_PER_OLD_SHARE'),
        tradable_date=v(None,'ISO_DATE')),[461])
    add(PROSPECTUS,'EMPLOYEES','EMPLOYEE_REMUNERATION_NOT_OLD_SHARE_ENTITLEMENT','EMPLOYEE_REMUNERATION_CAPITALIZATION_REPORTED',dict(shared,
        remuneration_amount=v(a['employee_remuneration_thousand_twd'],'THOUSAND_TWD','EMPLOYEE_REMUNERATION_NOT_SHAREHOLDER_BONUS'),
        par_value=v(a['par_twd_per_share'],'TWD_PER_SHARE','PAR_VALUE_NOT_EMPLOYEE_ISSUE_PRICE'),
        employee_issued_shares=v(None,'SHARES'),employee_issue_price=v(None,'TWD_PER_SHARE')),[461])
    add(PROSPECTUS,'MIXED_SHAREHOLDERS_AND_EMPLOYEES','2884_COMBINED_NEW_ISSUANCE_NOT_PERSONAL',
        'COMBINED_CAPITALIZATION_SHARES_REPORTED',dict(shared,
        combined_quantity=v(a['combined_new_thousand_shares'],'THOUSAND_SHARES','COMBINED_ISSUANCE_NOT_ALL_SHAREHOLDERS'),
        shareholder_quantity=v(None,'SHARES'),employee_quantity=v(None,'SHARES'),
        registration_stage=v(a['registration_stage']),registration_date=v(None,'ISO_DATE'),listing_date=v(None,'ISO_DATE')),[461])
    add(FOLLOWUP,'NOT_AN_ENTITLEMENT','ISSUER_APPROVAL_REPORT_NOT_PERSONAL_RIGHTS','FOLLOWUP_APPROVAL_REPORT',dict(
        stage=v(b['stage']),issuer_identity_basis=v(b['issuer_identity_basis']),
        meeting_resolution_date=v(b['meeting_resolution_date'],'ISO_DATE','MEETING_RESOLUTION_NOT_CLOSING'),
        regulatory_approval_date=v(b['regulatory_approval_date'],'ISO_DATE','REGULATORY_APPROVAL_NOT_CLOSING'),
        canonical_effective_at=v(None,'ISO_DATE'),actual_personal_receipt=v(None,'TWD')),[1])
    return result


def ratio_versions(catalog):
    validate(catalog)
    current=catalog['parent_catalog']
    while 'inventory' not in current: current=current['parent_catalog']
    versions=[deepcopy(o) for o in current['inventory'] if o['family']=='2884-acquires-2867' and 'shares_per_share' in o['fields']]
    new=next(o for o in catalog['observations'] if o['action_type']=='ORIGINAL_EXCHANGE_TERMS')
    return dict(new_contract_observation_id=new['id'],contract_ratio=new['fields']['original_ratio'],
        exact_parent_versions=versions,selection='NO_AUTOMATIC_ACTIVE_VERSION_OR_PERSONAL_GRANT',
        existing_2884_allotment=None,later_amendment_applicability=None)


def validate(catalog):
    verify(catalog)
    if catalog['schema']!=SCHEMA: raise ValueError('Explicit source contract version required')
    parent.validate(catalog['parent_catalog'])
    if (catalog['parent_catalog_id']!=PARENT_ID or catalog['parent_catalog']['id']!=PARENT_ID
            or catalog['coverage']!=catalog['parent_catalog']['coverage']):
        raise ValueError('Exact complete parent0.7 and incomplete coverage required')
    for k,v in dict(historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False).items():
        if catalog[k]!=v: raise ValueError('Research-only flags required')
    sources=catalog['sources']
    if set(sources)!={PROSPECTUS,FOLLOWUP}: raise ValueError('Two explicit source versions required')
    for sid,s in sources.items():
        if parent.evidence_sha(s['native_evidence'])!=EVIDENCE_SHA[sid]: raise ValueError('Native evidence changed')
        times=[datetime.fromisoformat(s[k]) for k in ('requested_at','completed_at','captured_at','readback_at')]
        if any(t.tzinfo is None for t in times) or times!=sorted(times) or s['announced_at'] is not None:
            raise ValueError('Original capture and new readback roles must remain separate')
        if s['work_github_readback_at'] is not None:
            raise ValueError('Unavailable Work report cannot supply an invented readback timestamp')
    facts={PROSPECTUS:parse_prospectus(sources[PROSPECTUS]['native_evidence'],'2884','2867','2025'),
        FOLLOWUP:parse_followup(sources[FOLLOWUP]['native_evidence'],'2884')}
    if catalog['facts']!=facts or catalog['observations']!=observations(facts,sources):
        raise ValueError('Parsed fact/issuer/holder/condition/date/unit/unknown qualification mismatch')
    return catalog


def resolve(catalog, name, request):
    validate(catalog)
    matches=[o for o in catalog['observations'] if o['id']==request.get('version_id')]
    if len(matches)!=1: raise ValueError('One explicit source observation required')
    return resolve_field(matches[0],name,request)


def qualify(data,catalog):
    validate(catalog)
    if data.get('source_contracts_catalog_id')!=catalog['id']: raise ValueError('Exact new catalog binding required')
    old=deepcopy(data);old.pop('source_contracts_catalog_id')
    return dict(deepcopy(parent.qualify(old,catalog['parent_catalog'])),source_contracts_catalog_id=catalog['id'])
