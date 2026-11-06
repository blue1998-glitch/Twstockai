"""Offline company-component producer. Zero official or PDF network fetches."""
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path

from .action_sources import ROOT,HERE,dump
from .action_scope import identify
from .action_study import verified_quotes
from .source_qualification import build_calendar
from . import source_contracts_sources as parent_source
from . import source_followup as quote_core
from .capital_components import (SCHEMA,PARENT_ID,SOURCE_ID,EVIDENCE_SHA,PROVENANCE_SHA,
    evidence_sha,parse_equity,parse_board,observations,reconcile,validate,qualify)

OUT=HERE/'capital_components_20261023'
OLD=HERE/'source_diagnostics_20261023/raw'
PDF_SHA='926f1f871a294702d3e4f5e4d89cf5aeb5e64808593efa2d99b95ed7375388fa'
FULL_NATIVE_SHA='6bb2eab5c6f23cff537051807ae98bee47c3f0d121af33b91f07715c8e2f38cf'
MANIFEST_SHA='2577a0d46b24f0facfeb102ba518ac0feb2170855d393a309b1679994d28d4df'
META_SHA='f19086ec5076617df87e6f303d84f966c09b842f8416041423b45d746bf87dc6'
TEXT_SHA={'391':'efa5d40c43d9b24bedcac12ab7d2b4a214913193bbd08264b5c360beacd27499',
    '456':'0fe99f17884a20383fbfc8820e207e132c1981f270e1bfee0ebe0e2e9b1a70f6'}


def sha(b):return hashlib.sha256(b).hexdigest()


def load_source(folder=OUT,old=OLD):
    folder,old=Path(folder),Path(old);m_raw=(folder/'source-manifest.json').read_bytes()
    if sha(m_raw)!=MANIFEST_SHA:raise ValueError('Actual reuse manifest bytes changed')
    m=json.loads(m_raw)
    if evidence_sha(m)!=PROVENANCE_SHA:raise ValueError('Provenance mismatch')
    body=(old/(SOURCE_ID+'.response')).read_bytes();meta_raw=(old/(SOURCE_ID+'.meta.json')).read_bytes()
    if len(body)!=14607733 or sha(body)!=PDF_SHA or not body.startswith(b'%PDF-') or sha(meta_raw)!=META_SHA:
        raise ValueError('Original PDF/meta bytes do not match known archive')
    meta=json.loads(meta_raw)
    if (meta!=m['original_official_capture'] or meta['http']!=200 or meta['status']!='CAPTURED'
            or meta['url']!=parent_source.URLS[SOURCE_ID] or meta['final_url']!=meta['url']
            or meta['sha256']!=sha(body) or meta['bytes']!=len(body)
            or meta['redirects_followed'] is not False or meta['retries']!=0):raise ValueError('Official capture/URL/HTTP identity mismatch')
    prior=json.loads((parent_source.OUT/'raw/esun-prospectus-20260722.github-readback.json').read_text())
    if m['prior_codex_fixed_github_readback']!=prior:raise ValueError('Prior Codex readback cannot be replaced by local reuse')
    local=m['local_reuse']
    if (local['bytes']!=len(body) or local['sha256']!=sha(body)
            or local['source_path']!='股票系統M1_v0_18/rotation_research/source_diagnostics_20261023/raw/esun-prospectus-20260722.response'
            or local['role']!='CODEX_LOCAL_ORIGINAL_REUSE_NOT_OFFICIAL_FETCH_OR_GITHUB_READBACK'
            or m['official_network_requests']!=0 or m['source_pdf_github_requests']!=0):raise ValueError('Local read is not a new official/GitHub capture')
    if any(datetime.fromisoformat(local[k]).tzinfo is None for k in ['started_at','completed_at','observed_at']):raise ValueError('Aware local observation timestamps required')
    native=(old/(SOURCE_ID+'.txt')).read_bytes();ext=json.loads((old/(SOURCE_ID+'.extraction.json')).read_text())
    if (sha(native)!=FULL_NATIVE_SHA or ext['text_sha256']!=sha(native) or ext['pdf_sha256']!=PDF_SHA
            or ext['pages']!=765 or native.count(b'\f')!=765 or ext['returncode']!=0 or 'xref num 5429' not in ext['stderr']):
        raise ValueError('Archived native text/page count/xref diagnostic changed')
    e=json.loads((folder/'raw/selected-pages.evidence.json').read_text());pages=native.decode().split('\f')
    if set(e)!={'391','456'}:raise ValueError('Exactly the two reviewed physical pages required')
    for n in e:
        text=(folder/'raw'/('esun-prospectus-p'+n+'.txt')).read_bytes()
        if sha(text)!=TEXT_SHA[n] or text.decode()!=e[n] or text.decode().rstrip('\f')!=pages[int(n)-1]:
            raise ValueError('Re-extracted selected page not bound to same original/full native')
    if evidence_sha(e)!=EVIDENCE_SHA:raise ValueError('Selected source evidence changed')
    return dict(manifest=deepcopy(m),native_evidence=e,original_official_capture=deepcopy(meta),
        prior_codex_github_readback_at=prior['readback_at'],local_reuse_completed_at=local['completed_at'],
        codex_analysis_observed_at=m['codex_analysis_observed_at'],work_github_readback_at=None,announced_at=None,
        issuer_code='2884',scope='COMPANY_AGGREGATE_COMPONENTS_NOT_PERSONAL_RIGHTS',
        historical_publication_time='NOT_AUTHENTICATED')


def build_catalog(folder=OUT):
    source=load_source(folder);base=parent_source.build_catalog()
    if base['id']!=PARENT_ID or base!=json.loads((parent_source.OUT/'catalog-v08.json').read_text()):raise ValueError('Exact complete parent0.8 required')
    facts=dict(equity_table=parse_equity(source['native_evidence']['391'],'2025','2024'),
        board_reference=parse_board(source['native_evidence']['456'],'2024'))
    c=dict(schema=SCHEMA,parent_catalog_id=base['id'],parent_catalog=deepcopy(base),coverage=deepcopy(base['coverage']),
        source=source,facts=facts,observations=observations(facts,source),historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False)
    c['reconciliation']=reconcile(c)
    return validate(identify(c))


def study_input(old,catalog,manifest,calendar,start,end,code):
    result=parent_source.study_input(old,catalog['parent_catalog'],manifest,calendar,start,end,code)
    result['capital_components_catalog_id']=catalog['id'];return result


def run():
    catalog=build_catalog();old,manifest=verified_quotes();calendar=build_calendar()
    missing=[quote_core.quote_diagnostic(catalog['parent_catalog']['parent_catalog'],c,b['date'],b['close'],b['date'] in calendar['sessions'])
        for c,a in old['assets'].items() for b in a['bars'] if b.get('missing')]
    if dict(diagnostics=missing)!=json.loads((parent_source.OUT/'missing-quotes.json').read_text()):raise AssertionError('Original missing-quote diagnostics must remain exact')
    design=json.loads((HERE/'generated/design.json').read_text());dates=[b['date'] for b in old['assets']['1101']['bars']];windows=[]
    for start in design['cutoffs']:
        for a,b in [('1101','2884'),('2884','1101')]:
            for horizon in design['horizons']:
                i=dates.index(start)
                if i+horizon>=len(dates):windows.append(dict(A=a,B=b,start=start,end=None,horizon=horizon,status='INSUFFICIENT_SAVED_FORWARD_ROWS'))
                else:
                    q=qualify(study_input(old,catalog,manifest,calendar,start,dates[i+horizon],a),catalog)
                    if q['daily'] or q['journal'] or q['total_net_return'] is not None or q['original_numeric_replay_called']:raise AssertionError('Company component facts cannot authorize incomplete net accounting')
                    windows.append(dict(A=a,B=b,horizon=horizon,**q))
    summary=dict(schema=SCHEMA,originals_reused=1,new_official_originals=0,official_network_requests=0,source_pdf_github_requests=0,
        physical_pages_reextracted_and_reviewed=[391,456],observations=len(catalog['observations']),
        exact_parent_v08_id=catalog['parent_catalog_id'],company_source_reconciliation='PASS_NOT_PERSONAL_ALLOCATION',
        original_quote_archives_rechecked=len(manifest),calendar_reports_rechecked=len(calendar['sources']),
        qualification_calls=sum(w['end'] is not None for w in windows),refused_windows=sum(w['status']=='REFUSED_INCOMPLETE_EVENT_ACCOUNTING' for w in windows),
        insufficient_windows=sum(w['end'] is None for w in windows),exchange_unsupported_windows=sum('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED' in w.get('refusal_reasons',[]) for w in windows),
        qualified_total_net_return_windows=sum(w.get('total_net_return') is not None for w in windows),numeric_replay_calls=0,six_strategy_replays=0,
        missing_quotes_exact_parent_preserved=True,parent_nulls_preserved=True,work_github_readback_at=None,
        android='NOT_TESTED_NEW_BUILD',historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False)
    return {'catalog-v09.json':catalog,'component-reconciliation.json':catalog['reconciliation'],
        'missing-quotes.json':dict(diagnostics=missing),'window-qualification.json':dict(windows=windows,ranking=None),'verification.json':summary}


def main():
    values=run()
    for name,value in values.items():
        p=OUT/name
        if p.exists() and json.loads(p.read_text())!=value:raise ValueError('Frozen source output differs; choose a new version: '+name)
        if not p.exists():dump(p,value)
    print(json.dumps(values['verification.json']))


if __name__=='__main__':main()
