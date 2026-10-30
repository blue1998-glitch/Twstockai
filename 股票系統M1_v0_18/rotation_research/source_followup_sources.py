"""Offline producer for three actually captured official originals, version 0.7."""
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path

from .action_sources import ROOT, HERE, dump
from .action_scope import identify
from .action_resolution_sources import input_for
from .action_study import verified_quotes
from .source_qualification import build_calendar
from . import offline_source_bridge_sources as parent_source
from .source_followup import (SCHEMA, PARENT_ID, TAIFEX, ESUN, TCC, EVIDENCE_SHA,
    evidence_sha, article_text, parse_taifex, parse_esun, parse_tcc, observations,
    validate, qualify, quote_diagnostic, precision_comparison)

OUT = HERE/'source_followup_20261023'
URLS = {
    TAIFEX:'https://www.taifex.com.tw/file/taifex/CHINESE/11/attach/%E7%8E%89%E5%B1%B1%E9%87%911106%E6%81%A2%E5%BE%A9%E4%BA%A4%E6%98%93%E5%85%AC%E5%91%8A.pdf',
    ESUN:'https://www.esunfhc.com/zh-tw/news-center/news-center/news/detail?id=D0565FF2DAE34916B079E1F26A048B1C&p=148DB1EBDC2B47629ED09DC9820A2155',
    TCC:'https://media.taiwancement.com/web_tcc/comm/pdf/report/2026/TCC%20115%E5%B9%B4%E7%AC%AC%E4%BA%8C%E5%AD%A3%E5%90%88%E4%BD%B5%E8%B2%A1%E5%A0%B1.pdf',
}
PINS = {
    TAIFEX:(81441,'9699a6d1349a1f4e14d78601af4874f724df5c24224dbe49906b1ce4ee712320','08c707bcdc25b966ffbc1a4091d7e594c511176fd79f94189bd8f8fa119d4ed3'),
    ESUN:(103632,'74c34ecf911d5bc6b994f4e8735e77f8da3770b043f4d5baefba3ef2cb4028ee','c56a16c1a8195bb4871fd34efdb0e98782f8a36de6d80e5ef38c044440d0c39a'),
    TCC:(3320224,'e8a8ca682a242180a908a68030dc80ee0321ddf92217586f59230b1d3e584d2d','814befcb1241280e17ccb215cef2a59d297dfacf86c6faea1ae95b20cff9da69'),
}
TEXT_PINS = {
    TAIFEX:'17ad26146848dce013bc2d48d3ffe922e2d3265526484d13bc95c1a720cc91c0',
    TCC:'b3bf4f18757b595a8019cf304fd3e72c61deb2c31c8d50a29ea1ea9954bb6ce8',
}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def validate_original(sid, raw, meta):
    size, digest, _ = PINS[sid]
    if (len(raw)!=size or sha(raw)!=digest or meta['bytes']!=size or meta['sha256']!=digest
            or meta['url']!=URLS[sid] or meta['final_url']!=URLS[sid]
            or meta['http']!=200 or meta['status']!='CAPTURED' or meta['method']!='GET'
            or meta['redirects_followed'] is not False or meta['retries']!=0):
        raise ValueError('Original bytes/URL/HTTP/SHA/length mismatch: '+sid)
    times=[datetime.fromisoformat(meta[k]) for k in ('requested_at','completed_at','captured_at','readback_at')]
    if any(t.tzinfo is None for t in times) or times!=sorted(times):
        raise ValueError('Original observation time roles mismatch')
    mime = meta['headers']['Content-Type']
    if (sid!=ESUN and (not raw.startswith(b'%PDF-') or mime!='application/pdf')) or (sid==ESUN and 'text/html' not in mime):
        raise ValueError('Original format mismatch')


def load_sources(folder=OUT):
    folder=Path(folder); rawdir=folder/'raw'
    manifest=json.loads((folder/'source-manifest.json').read_text())
    if set(manifest)!=set(URLS): raise ValueError('Three original captures required')
    sources={}
    for sid in URLS:
        raw=(rawdir/(sid+'.response')).read_bytes();meta_raw=(rawdir/(sid+'.meta.json')).read_bytes()
        if sha(meta_raw)!=PINS[sid][2]: raise ValueError('Archived capture metadata changed')
        meta=json.loads(meta_raw)
        if manifest[sid]!=meta: raise ValueError('Manifest/meta mismatch')
        validate_original(sid,raw,meta)
        evidence=json.loads((rawdir/(sid+'.evidence.json')).read_text())
        if evidence_sha(evidence)!=EVIDENCE_SHA[sid]: raise ValueError('Native evidence changed')
        if sid==ESUN:
            if article_text(raw.decode('utf-8-sig'))!=evidence:
                raise ValueError('Article scope/native evidence mismatch')
        else:
            text=(rawdir/(sid+'.txt')).read_bytes()
            ext=json.loads((rawdir/(sid+'.extraction.json')).read_text())
            pages=text.decode().split('\f'); expected_pages=1 if sid==TAIFEX else 124
            if (sha(text)!=TEXT_PINS[sid] or ext['text_sha256']!=sha(text)
                    or ext['pdf_sha256']!=sha(raw) or ext['returncode']!=0
                    or ext['pages']!=expected_pages or text.count(b'\f')!=expected_pages):
                raise ValueError('PDF extraction binding/page count mismatch')
            expected={'text':text.decode()} if sid==TAIFEX else {str(n):pages[n-1] for n in (7,52,54,55,57)}
            if expected!=evidence: raise ValueError('Selected native pages do not match full native text')
        sources[sid]=dict(deepcopy(meta),announced_at=None,historical_publication_time='NOT_AUTHENTICATED',
            kind='DIRECT_OFFICIAL_CAPTURE_NEW_VERSION',path=str((rawdir/(sid+'.response')).relative_to(folder.parent.parent.parent)),
            native_evidence=evidence)
    return sources


def build_catalog(folder=OUT):
    sources=load_sources(folder);parent=parent_source.build_catalog()
    if parent['id']!=PARENT_ID or parent!=json.loads((parent_source.OUT/'catalog-v06.json').read_text()):
        raise ValueError('Exact original parent0.6 required')
    facts={TAIFEX:parse_taifex(sources[TAIFEX]['native_evidence']['text'],'2884','2884_ORDINARY_OLD_SHARES'),
        ESUN:parse_esun(sources[ESUN]['native_evidence']),TCC:parse_tcc(sources[TCC]['native_evidence'])}
    return validate(identify(dict(schema=SCHEMA,parent_catalog_id=parent['id'],parent_catalog=deepcopy(parent),
        coverage=deepcopy(parent['coverage']),sources=sources,facts=facts,observations=observations(facts,sources),
        historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False)))


def study_input(old, catalog, manifest, calendar, start, end, code):
    base=catalog['parent_catalog']
    result=input_for(old,base['parent_catalog']['parent_catalog'],manifest,calendar,start,end,code)
    result.update(source_diagnostics_catalog_id=base['parent_catalog_id'],bridge_catalog_id=base['id'],
        source_followup_catalog_id=catalog['id'])
    return result


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
                    result=qualify(study_input(old,catalog,manifest,calendar,start,dates[i+horizon],a),catalog)
                    if result['daily'] or result['journal'] or result['total_net_return'] is not None or result['original_numeric_replay_called']:
                        raise AssertionError('Source followup cannot authorize incomplete accounting')
                    windows.append(dict(A=a,B=b,horizon=horizon,**result))
    summary=dict(schema=SCHEMA,new_originals_verified=3,new_observations=len(catalog['observations']),
        parent_v06_id=catalog['parent_catalog_id'],parent_v06_catalog_exact=True,
        pdfs_equal_to_work_comparison=2,html='NEW_CAPTURE_DIFFERENT_SHA_ARTICLE_CHECKED',
        direct_twse_2884_resumption_acquired=False,original_quote_archives_rechecked=len(manifest),
        calendar_reports_rechecked=len(calendar['sources']),
        qualification_calls=sum(w['end'] is not None for w in windows),
        refused_windows=sum(w['status']=='REFUSED_INCOMPLETE_EVENT_ACCOUNTING' for w in windows),
        insufficient_windows=sum(w['end'] is None for w in windows),
        exchange_unsupported_windows=sum('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED' in w.get('refusal_reasons',[]) for w in windows),
        qualified_total_net_return_windows=sum(w.get('total_net_return') is not None for w in windows),
        numeric_replay_calls=0,six_strategy_replays=0,offline_producer_network_requests=0,
        android='NOT_TESTED_NEW_BUILD',historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False)
    return {'catalog-v07.json':catalog,'missing-quotes.json':dict(diagnostics=missing),
        'window-qualification.json':dict(windows=windows,ranking=None),'verification.json':summary,
        'precision-comparison.json':precision_comparison(catalog)}


def main():
    values=run()
    for name,value in values.items():
        p=OUT/name
        if p.exists() and json.loads(p.read_text())!=value:
            raise ValueError('Different frozen output exists; choose a new version: '+name)
        if not p.exists():dump(p,value)
    print(json.dumps(values['verification.json']))


if __name__=='__main__':main()
