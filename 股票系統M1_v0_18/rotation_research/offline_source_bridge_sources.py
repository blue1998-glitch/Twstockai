"""Offline bridge reader/producer. Never downloads or rewrites parent outputs."""
from copy import deepcopy
from datetime import datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urljoin
import zipfile

from .action_sources import HERE, ROOT, dump
from .action_scope import identify
from .action_scope_sources import field
from . import source_diagnostics_sources as parent_source
from .action_resolution_sources import input_for
from .action_study import verified_quotes
from .source_qualification import build_calendar
from .offline_source_bridge import SCHEMA, QUALIFICATION, TAX_TITLE, parse_suspension, parse_mof_api, validate, qualify, quote_diagnostic

OUT = HERE / 'offline_source_bridge_20261023'
BRIDGE = ROOT / 'deliveries/m1-offline-source-bridge-20261023/TWstockai_Offline_Source_Bridge_20261023.zip'
BRIDGE_SHA = 'ecc413ca28fce87085666b87b3c3a6d1bf784ef553b32d2198b8bb72bebeedce'
CONTENT_SHA = 'f591e40736d7e0ad1d2b64175a0d83885c80050bb8a90fec4d1156333a8691c3'
SOURCE_URLS = {
    'twse-tcc-suspension-20250812': 'https://wwwc.twse.com.tw/staticFiles/news/news/tsecnews/8a8216d697fc438f01989dd5fa3502a6.pdf',
    'twse-esun-suspension-20251104': 'https://investoredu.twse.com.tw/Mobile_pages/..%2FFileSystem%2FFileUpload%2Fdae59521-69e0-4856-90fc-d349fb6013eb.pdf',
    'mof-tax-api-143802': 'https://ttc.mof.gov.tw/Api/PostData',
    'mof-tax-rule-143802': 'https://ttc.mof.gov.tw/FB/FB120/143802',
    'mof-tax-page-script': 'https://ttc.mof.gov.tw/Views/FB/FB120.cshtml.js?v=IsBcIc5oNYoVOKOQFowGyPug7tdjcdrclPyBhI_mG5I',
    'mof-tax-site-script': 'https://ttc.mof.gov.tw/js/site.js?v=oxjiyo8aCBqX8ph2JO14cCSEEFEQSOtAkTWmhqRv164',
    'mof-tax-search-10100097670': 'https://ttc.mof.gov.tw/Api/GetData',
}


def read_bridge(path=BRIDGE):
    body = Path(path).read_bytes()
    if len(body) != 941229 or hashlib.sha256(body).hexdigest() != BRIDGE_SHA:
        raise ValueError('Exact original bridge bytes required; no substitutions')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if (z.testzip() is not None or len(names) != len(set(names))
                or any(Path(n).is_absolute() or '..' in Path(n).parts
                    or (z.getinfo(n).external_attr >> 16) & 0o170000 == 0o120000 for n in names)):
            raise ValueError('Invalid/unsafe bridge ZIP')
        members = {n:z.read(n) for n in names}
    manifest = json.loads(members['MANIFEST.json'])
    entries = manifest['members']
    if len(entries) != 40 or len({e['path'] for e in entries}) != 40 or set(members) != {'MANIFEST.json'} | {e['path'] for e in entries}:
        raise ValueError('Exact 40 manifest entries and 41 members required')
    for e in entries:
        body = members[e['path']]
        if len(body) != e['bytes'] or hashlib.sha256(body).hexdigest() != e['sha256']:
            raise ValueError('Bridge member fingerprint mismatch: ' + e['path'])
    return members, {e['path']:e for e in entries}


def validate_original(sid, raw, meta, entry):
    if (meta['url'] != SOURCE_URLS[sid] or meta['status'] != 200
            or meta.get('redirects_followed') is True or meta['bytes'] != len(raw)
            or entry['bytes'] != len(raw) or meta['sha256'] != entry['sha256']
            or hashlib.sha256(raw).hexdigest() != entry['sha256']):
        raise ValueError('Original metadata/URL/HTTP/size/SHA mismatch: ' + sid)
    if datetime.fromisoformat(meta['observed_at']).tzinfo is None:
        raise ValueError('Original capture time needs timezone')
    if sid == 'mof-tax-api-143802':
        if meta.get('method') != 'POST_READ_ONLY_PUBLIC_QUERY' or meta.get('form') != {
                'FunctionID':'FB12001', 'ObjParams[TaxSN]':'143802'}:
            raise ValueError('Exact public-query function/TaxSN required')
    if sid == 'mof-tax-search-10100097670':
        form=meta.get('form', {})
        if meta.get('method') != 'POST_READ_ONLY_PUBLIC_QUERY' or any(form.get(k)!=v for k,v in {
                'FunctionID':'FB10001', 'ObjParams[TaxAct]':'所得稅法',
                'ObjParams[TaxVer]':'一一四年版', 'ObjParams[Content]':'10100097670'}.items()):
            raise ValueError('Archived search scope mismatch')


class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.scripts=[]

    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='input' and a.get('id')=='id':self.ids.append(a.get('value'))
        if tag=='script':self.scripts.append(a.get('src',''))


def validate_tax_chain(members):
    def raw(sid):return members['archived_work/'+sid+'.response'].decode('utf-8-sig')
    page=Page();page.feed(raw('mof-tax-rule-143802'))
    if page.ids != ['143802']:
        raise ValueError('Official page TaxSN mismatch')
    urls=[urljoin(SOURCE_URLS['mof-tax-rule-143802'],s) for s in page.scripts]
    if any(SOURCE_URLS[sid] not in urls for sid in ['mof-tax-page-script','mof-tax-site-script']):
        raise ValueError('Captured script not linked by official page')
    js=raw('mof-tax-page-script');site=raw('mof-tax-site-script')
    required=["id = $('#id').val()", 'function FB12001()', "const url = '/Api/PostData'",
        'FunctionID: thisFuncName()', 'TaxSN: id', 'ajaxPost(url, data, success)',
        'Table[0].TaxVer', 'Table[0].Title', 'Table[0].Content']
    if not all(s in js for s in required) or not all(s in site for s in ['return thisFuncName.caller.name', "type: 'POST'"]):
        raise ValueError('Official query script/function/fields chain mismatch')
    payload=json.loads(members['archived_work/mof-tax-api-143802.response'])
    parsed=parse_mof_api(payload, CONTENT_SHA)
    search=json.loads(members['archived_work/mof-tax-search-10100097670.response'])
    matches=[r for r in search['Data']['Table'] if r.get('TaxSN')==143802]
    if search.get('Code')!='1' or len(matches)!=1:
        raise ValueError('Independent archived search result identity mismatch')
    if any(matches[0].get(k)!=parsed[k] for k in ('TaxAct','TaxVer','Title','Content')):
        raise ValueError('Archived search and detail interpretation differ')
    return parsed


def build_catalog(path=BRIDGE, acquisition_path=OUT/'bridge-acquisition.json'):
    members,entries=read_bridge(path)
    acquisition=json.loads(Path(acquisition_path).read_text())
    if (acquisition['http']!=200 or acquisition['bytes']!=941229 or acquisition['sha256']!=BRIDGE_SHA
            or acquisition['manifest_members_verified']!=40 or not acquisition['byte_equal_to_git_checkout']):
        raise ValueError('Actual GitHub bridge acquisition record required')
    ingested=acquisition['new_readback_at']
    if datetime.fromisoformat(ingested).tzinfo is None:
        raise ValueError('Explicit ingestion timezone required')
    parent=parent_source.build_catalog()
    if parent!=json.loads((parent_source.OUT/'catalog-v05.json').read_text()):
        raise ValueError('Exact original parent0.5 required; do not rewrite it')
    sources={};originals={};metas={}
    for sid in SOURCE_URLS:
        prefix='archived_work/'+sid;raw=members[prefix+'.response'];meta=json.loads(members[prefix+'.meta.json'])
        validate_original(sid,raw,meta,entries[prefix+'.response'])
        originals[sid]=raw;metas[sid]=meta
        sources[sid]=dict(url=meta['url'],sha256=meta['sha256'],bytes=meta['bytes'],http=meta['status'],
            captured_at=meta['observed_at'],ingested_at=ingested,announced_at=None,
            archive_path=str(BRIDGE.relative_to(ROOT)),archive_sha256=BRIDGE_SHA,archive_member=prefix+'.response',
            metadata_member=prefix+'.meta.json',kind='OFFICIAL_ARCHIVE_VIA_OFFLINE_BRIDGE',
            method=meta.get('method','NOT_RECORDED_IN_ORIGINAL_META'),historical_publication_time='NOT_AUTHENTICATED')
    tax=validate_tax_chain(members)
    result=dict(schema=SCHEMA,parent_catalog_id=parent['id'],parent_catalog=deepcopy(parent),
        coverage=deepcopy(parent['coverage']),sources=sources,observations=[],
        archive_verification=dict(sha256=BRIDGE_SHA,bytes=941229,members=41,manifest_entries_verified=40,
            original_91_member_archive='WORK_ATTESTATION_ONLY_FULL_PREDECESSOR_NOT_INCLUDED_OR_REVERIFIED_HERE'),
        historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False)
    def f(value,unit,role,sids,locator,literal=None):
        proofs=[] if value is None else [dict(source_id=sid,locator=locator,raw_value=literal if literal is not None else value) for sid in sids]
        return field(value,unit,role,proofs,QUALIFICATION)
    def add(kind,code,holder,instrument,sids,fields):
        result['observations'].append(identify(dict(family='offline-bridge:'+kind+':'+code,
            issuer_code=code,entitled_old_code=holder,old_instrument=instrument,action_type=kind,
            source_ids=sids,source_captured_at=max(sources[s]['captured_at'] for s in sids),
            observed_at=ingested,announced_at=None,accounting_eligible=False,historical_signal_eligible=False,fields=fields)))
    reviewed=json.loads(members['bridge-facts.json'])
    for key in ('TaxAct','TaxVer','Title','Terms','Subsection','Content'):
        if reviewed['tax_evidence'][key] != tax[key]:
            raise ValueError('Work tax facts and actual archived response differ: '+key)
    for sid,code in [('twse-tcc-suspension-20250812','1101'),('twse-esun-suspension-20251104','2884')]:
        raw=originals[sid];text=members['archived_work/'+sid+'.txt'].decode()
        if not raw.startswith(b'%PDF-') or text.count('\f')!=1:
            raise ValueError('One-page suspension PDF/derivative required')
        instrument=code+'_ORDINARY_OLD_SHARES';parsed=parse_suspension(text,code,instrument)
        fact=next(x for x in reviewed['quote_evidence'] if x['code']==code)
        if fact['direct_suspension_date']!=parsed['suspension_start_date'] or fact['document_date']!=parsed['document_date']:
            raise ValueError('Work facts and actual PDF differ')
        add('SECURITY_SUSPENSION_START_NOTICE',code,code,instrument,[sid],dict(
            document_date=f(parsed['document_date'],'ISO_DATE','SOURCE_DOCUMENT_DATE_NOT_PUBLICATION',[sid],'PDF page 1 heading'),
            suspension_start_date=f(parsed['suspension_start_date'],'ISO_DATE','SECURITY_SUSPENSION_START_NOT_END',[sid],'PDF page 1 ordinary-share suspension sentence'),
            suspension_end_date=f(None,'ISO_DATE','SUSPENSION_END_NOT_AUTHENTICATED',[],'')))
    sids=[s for s in SOURCE_URLS if s.startswith('mof-')];api='mof-tax-api-143802'
    fields={k:f(tax[k],'OFFICIAL_LEGAL_TEXT','GENERAL_INTERPRETATION_NOT_ISSUER_OR_PERSONAL',[api],'Data.Table[0].'+k) for k in ['TaxAct','TaxVer','Title','Article','Terms','Subsection','Content']}
    for name in ['issuer_funding_subtype','personal_tax_residency','personal_tax','nhi','fees','personal_net_cash','actual_investor_receipt']:
        fields[name]=f(None,'UNKNOWN','NO_INVESTOR_OR_ISSUER_SPECIFIC_EVIDENCE',[],'')
    add('GENERAL_TAX_INTERPRETATION','GENERAL','NOT_INVESTOR_SPECIFIC','NOT_AN_ENTITLEMENT',sids,fields)
    return validate(identify(result))


def run():
    catalog=build_catalog();old,manifest=verified_quotes();calendar=build_calendar()
    missing=[quote_diagnostic(catalog,c,b['date'],b['close'],b['date'] in calendar['sessions'])
        for c,a in old['assets'].items() for b in a['bars'] if b.get('missing')]
    design=json.loads((HERE/'generated/design.json').read_text());dates=[b['date'] for b in old['assets']['1101']['bars']];windows=[]
    for start in design['cutoffs']:
        for a,b in [('1101','2884'),('2884','1101')]:
            for horizon in design['horizons']:
                i=dates.index(start)
                if i+horizon>=len(dates):
                    windows.append(dict(A=a,B=b,start=start,end=None,horizon=horizon,status='INSUFFICIENT_SAVED_FORWARD_ROWS'))
                else:
                    data=input_for(old,catalog['parent_catalog']['parent_catalog'],manifest,calendar,start,dates[i+horizon],a)
                    data.update(source_diagnostics_catalog_id=catalog['parent_catalog_id'],bridge_catalog_id=catalog['id'])
                    result=qualify(data,catalog)
                    if (result['daily'] or result['journal'] or result['total_net_return'] is not None
                            or result['original_numeric_replay_called']):
                        raise AssertionError('Incomplete source bridge must not run numeric accounting')
                    windows.append(dict(A=a,B=b,horizon=horizon,**result))
    summary=dict(schema=SCHEMA,bridge_bytes_verified=941229,bridge_manifest_members_verified=40,
        new_originals_verified=len(catalog['sources']),new_observations=3,direct_suspension_starts=2,
        actual_archived_tax_api='VALIDATED_GENERAL_LAW_CONTEXT_ONLY',old_synthetic_tax_parser='PRESERVED_UNCHANGED',
        original_quote_archives_rechecked=len(manifest),calendar_reports_rechecked=len(calendar['sources']),
        qualification_calls=sum(w['end'] is not None for w in windows),refused_windows=sum(w['status']=='REFUSED_INCOMPLETE_EVENT_ACCOUNTING' for w in windows),
        insufficient_windows=sum(w['end'] is None for w in windows),exchange_unsupported_windows=sum('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED' in w.get('refusal_reasons',[]) for w in windows),
        qualified_total_net_return_windows=sum(w.get('total_net_return') is not None for w in windows),numeric_replay_calls=0,six_strategy_replays=0,official_network_requests=0,
        android='NOT_TESTED_NEW_BUILD',historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False)
    return {'catalog-v06.json':catalog,'missing-quotes.json':dict(diagnostics=missing),
        'window-qualification.json':dict(windows=windows,ranking=None),'verification.json':summary}


def main():
    values=run()
    for name,value in values.items():
        p=OUT/name
        if p.exists() and json.loads(p.read_text())!=value:
            raise ValueError('Different frozen output exists; choose a new version: '+name)
        if not p.exists():dump(p,value)
    print(json.dumps(values['verification.json']))


if __name__=='__main__':main()
