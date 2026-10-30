"""One source-only p58 supplement. No IO, ledger, coverage or strategy update."""
from copy import deepcopy
from datetime import datetime
import hashlib
import re
from .action_scope import identify, verify, resolve_field
from .source_followup import compact, one, field, QUALIFICATION

SCHEMA='rotation-treasury-date-roles/0.1'
SOURCE='tcc-2026-q2-consolidated-report'
PDF_SHA='e8a8ca682a242180a908a68030dc80ee0321ddf92217586f59230b1d3e584d2d'
NATIVE_SHA='b3bf4f18757b595a8019cf304fd3e72c61deb2c31c8d50a29ea1ea9954bb6ce8'
PAGE_SHA='2e6bcab6a95d1d284011167e40a3c9e40227fd1c30b813c7bf4c61013e72493c'
CATALOG_ID='sha256:49528167bede030b29359a77abebd3f8947c88e58aeaaeede62c42a76465cc89'
PRIOR_ID='sha256:2416ebd2dd3f52971a48df9af53ab491393797fc0aa3220e29b81871972a9b89'
URL='https://media.taiwancement.com/web_tcc/comm/pdf/report/2026/TCC%20115%E5%B9%B4%E7%AC%AC%E4%BA%8C%E5%AD%A3%E5%90%88%E4%BD%B5%E8%B2%A1%E5%A0%B1.pdf'
NULL_FIELDS={
    'exact_board_approval_date':('ISO_DATE','EXACT_BOARD_DAY_NOT_STATED'),
    'exact_registration_completed_date':('ISO_DATE','EXACT_REGISTRATION_DAY_NOT_STATED'),
    'exact_effective_date':('ISO_DATE','CANCELLATION_EFFECTIVE_DAY_NOT_ESTABLISHED'),
    'announced_at':('ISO_TIMESTAMP','HISTORICAL_PUBLIC_AVAILABILITY_NOT_AUTHENTICATED'),
    'holder_conversion_ratio':('SHARES_PER_OLD_SHARE','NO_PERSONAL_SHARE_CONVERSION_ESTABLISHED'),
    'holder_cashflow':('TWD','NO_PERSONAL_CASHFLOW_ESTABLISHED'),
    'personal_entitlement':('UNKNOWN','NO_PERSONAL_ENTITLEMENT_ESTABLISHED'),
}


def _month(year,month):
    y,m=int(year)+1911,int(month)
    if not 1912<=y<=9999 or not 1<=m<=12:raise ValueError('Invalid stated ROC month')
    return f'{y:04d}-{m:02d}'


def parse_page(text):
    """Read the two stated months; never manufacture any day or effective date."""
    s=compact(text)
    if not s.endswith('-58-'):raise ValueError('Explicit printed page58 required')
    m=one(r'本公司於(\d+)年(\d+)月經董事會通過註銷庫藏股((?:\d{1,3}(?:,\d{3})+)|\d+)仟股,並於(\d+)年(\d+)月辦理變更登記完成。',s)
    approval,registration=_month(m[1],m[2]),_month(m[4],m[5])
    if registration<approval:raise ValueError('Registration month precedes board approval')
    return dict(board_approval_month=approval,registration_completed_month=registration,
                cancellation_quantity=m[3].replace(',',''),quantity_unit='THOUSAND_SHARES')


def _time(value):
    t=datetime.fromisoformat(value.replace('Z','+00:00'))
    if t.utcoffset() is None:raise ValueError('Explicit timezone required')
    return t


def observe(data):
    if data['schema']!='rotation-treasury-date-roles-input/0.1':raise ValueError('Explicit supplement input required')
    s=data['source'];prior=data['prior_observation'];verify(prior)
    if data['source_followup_catalog_id']!=CATALOG_ID or prior['id']!=PRIOR_ID:
        raise ValueError('Exact saved source/observation link required')
    expected=dict(source_id=SOURCE,issuer_code='1101',url=URL,pdf_bytes=3320224,
        pdf_sha256=PDF_SHA,native_sha256=NATIVE_SHA,page_number=58,printed_page='58',page_sha256=PAGE_SHA,
        official_captured_at='2026-10-23T08:33:10.538370+00:00',
        original_readback_at='2026-10-23T08:33:10.538392+00:00',
        announced_at=None,historical_publication_time='NOT_AUTHENTICATED',
        evidence_kind='SAVED_NATIVE_TEXT_FROM_HASH_BOUND_PDF_EXTRACTION')
    if any(s.get(k)!=v for k,v in expected.items()):raise ValueError('Pinned source/page identity conflict')
    if hashlib.sha256(s['page_text'].encode()).hexdigest()!=PAGE_SHA:raise ValueError('Selected page content conflict')
    times=[_time(s['official_captured_at']),_time(s['original_readback_at']),
           _time(data['local_source_read_at']),_time(data['observed_at'])]
    if times!=sorted(times):raise ValueError('Source capture/read/observation chronology conflict')
    facts=parse_page(s['page_text'])
    def known(name,unit,role):
        proof=dict(source_id=SOURCE,pdf_sha256=PDF_SHA,native_sha256=NATIVE_SHA,
            physical_pdf_page=58,printed_page='58',page_sha256=PAGE_SHA,
            locator='First paragraph: board approval month and registration-completed month',
            raw_excerpt=s['page_text'].split('二六、',1)[0],normalized_value=facts[name])
        return field(facts[name],unit,role,[proof],QUALIFICATION)
    fields=dict(board_approval_month=known('board_approval_month','ISO_MONTH','BOARD_APPROVAL_MONTH_NOT_EFFECTIVE_DATE'),
        registration_completed_month=known('registration_completed_month','ISO_MONTH','REGISTRATION_COMPLETION_MONTH_NOT_EFFECTIVE_DATE'),
        cancellation_quantity=known('cancellation_quantity','THOUSAND_SHARES','ISSUER_TREASURY_QUANTITY_NOT_PERSONAL_RIGHT'))
    fields.update({k:field(None,unit,role,[],QUALIFICATION) for k,(unit,role) in NULL_FIELDS.items()})
    return identify(dict(schema=SCHEMA,input=deepcopy(data),family=prior['family'],issuer_code='1101',
        entitled_old_code=prior['entitled_old_code'],old_instrument=prior['old_instrument'],
        action_type='TREASURY_CANCELLATION_DATE_ROLE_SUPPLEMENT',source_ids=[SOURCE],
        linked_prior_observation_id=prior['id'],source_followup_catalog_id=CATALOG_ID,
        relationship='EXPLICIT_SAME_SAVED_SOURCE_SUPPLEMENT_NOT_NEW_ACCOUNTING_EVENT',
        observed_at=data['observed_at'],announced_at=None,fields=fields,
        numeric_ledger_events_added=0,independent_market_samples_added=0,
        data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,
        accounting_eligible=False,policy_authorized=False,live_execution_authorized=False,
        primary_pressure_id=None))


def validate(record):
    verify(record)
    if record!=observe(record['input']):raise ValueError('Supplement content/qualification differs from source input')
    return record


def resolve(record,name,request):
    validate(record)
    return resolve_field(record,name,request)
