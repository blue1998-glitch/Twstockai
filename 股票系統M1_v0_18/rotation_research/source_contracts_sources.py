"""Offline 0.8 producer. Reuse the archived prospectus; never refresh sources."""
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path

from .action_sources import ROOT,HERE,dump
from .action_scope import identify
from .action_study import verified_quotes
from .source_qualification import build_calendar
from . import source_followup_sources as parent_source
from .source_contracts import (SCHEMA,PARENT_ID,PROSPECTUS,FOLLOWUP,EVIDENCE_SHA,
    parse_prospectus,parse_followup,observations,validate,qualify,ratio_versions,parent)

OUT=HERE/'source_contracts_20261023'
OLD=HERE/'source_diagnostics_20261023/raw'
URLS={PROSPECTUS:'https://www.esunbank.com/zh-tw/-/media/ESUNFHC/Files/Investor-Relations/mna/mna08_2026Prospectus.pdf',
    FOLLOWUP:'https://www.esunbank.com/zh-tw/-/media/ESUNFHC/Files/Investor-Relations/Shareholders/Shareholder-Meeting/2026Follow-up.pdf'}
PINS={PROSPECTUS:(14607733,'926f1f871a294702d3e4f5e4d89cf5aeb5e64808593efa2d99b95ed7375388fa'),
    FOLLOWUP:(56705,'02899d55a0ce5431e3ec9787652a928fd5cc2d35abf56669942db52440e2fcdf')}
META_SHA={PROSPECTUS:'f19086ec5076617df87e6f303d84f966c09b842f8416041423b45d746bf87dc6',
    FOLLOWUP:'59bf4b46b7567c3f27b7fb47e74868cd99d9c2977108763a8021b617db85528e'}
GITHUB_META_SHA='c8cbfa0e0aaae42763a9f7ea927edafc8403922b47aefcbd95606a8e7029fcb0'
TEXT_SHA={PROSPECTUS:'6bb2eab5c6f23cff537051807ae98bee47c3f0d121af33b91f07715c8e2f38cf',
    FOLLOWUP:'a3cc0a0062e93cce31ac36492fd39447b1171793516f17ef296870f37e17ae7a'}


def sha(b):return hashlib.sha256(b).hexdigest()


def validate_original(sid,body,meta):
    n,digest=PINS[sid]
    if (len(body)!=n or sha(body)!=digest or not body.startswith(b'%PDF-')
            or meta['bytes']!=n or meta['sha256']!=digest or meta['url']!=URLS[sid]
            or meta['final_url']!=URLS[sid] or meta['http']!=200 or meta['status']!='CAPTURED'
            or meta['method']!='GET' or meta['redirects_followed'] is not False or meta['retries']!=0):
        raise ValueError('Original bytes/meta/URL/HTTP mismatch')
    a,b=(datetime.fromisoformat(meta[k]) for k in ('requested_at','completed_at'))
    if a.tzinfo is None or b.tzinfo is None or a>b: raise ValueError('Original capture times invalid')


def load_sources(folder=OUT,old=OLD):
    folder,old=Path(folder),Path(old);result={}
    manifest=json.loads((folder/'source-manifest.json').read_text())
    if set(manifest)!={PROSPECTUS,FOLLOWUP}:raise ValueError('Two explicit sources required')
    for sid in (PROSPECTUS,FOLLOWUP):
        prefix=(old/sid) if sid==PROSPECTUS else (folder/'raw'/sid)
        body=prefix.with_suffix('.response').read_bytes();meta_raw=Path(str(prefix)+'.meta.json').read_bytes()
        if sha(meta_raw)!=META_SHA[sid]:raise ValueError('Original archived metadata changed')
        meta=json.loads(meta_raw);validate_original(sid,body,meta)
        if manifest[sid]['official_capture']!=meta:raise ValueError('Official manifest/meta mismatch')
        if sid==PROSPECTUS:
            text=prefix.with_suffix('.txt').read_bytes();ext=json.loads(Path(str(prefix)+'.extraction.json').read_text())
            if (sha(text)!=TEXT_SHA[sid] or ext['pdf_sha256']!=PINS[sid][1]
                    or ext['text_sha256']!=sha(text) or ext['returncode']!=0 or ext['pages']!=765
                    or text.count(b'\f')!=765 or 'xref num 5429' not in ext['stderr']):
                raise ValueError('Archived prospectus native extraction/xref diagnostic mismatch')
            e=json.loads((folder/'raw/esun-prospectus-selected.evidence.json').read_text())
            pages=text.decode().split('\f')
            if e!={str(n):pages[n-1] for n in (162,163,175,176,461)}:
                raise ValueError('Selected physical pages not bound to archived full native text')
            github_raw=(folder/'raw/esun-prospectus-20260722.github-readback.json').read_bytes()
            if sha(github_raw)!=GITHUB_META_SHA:raise ValueError('New Codex GitHub readback metadata changed')
            github=json.loads(github_raw)
            if (github!=manifest[sid]['codex_github_readback'] or github['http']!=200
                    or github['bytes']!=len(body) or github['sha256']!=sha(body)
                    or not github['expected_size_and_sha_match']):raise ValueError('Actual GitHub original readback mismatch')
            readback=github['readback_at']
        else:
            text=(folder/'raw/esun-follow-up-2026-p1.txt').read_bytes()
            if sha(text)!=TEXT_SHA[sid] or text.count(b'\f')!=1:raise ValueError('One-page native text changed')
            e=json.loads((folder/'raw/esun-follow-up-2026.evidence.json').read_text())
            if e!={'1':text.decode()}:raise ValueError('Follow-up page/native mismatch')
            readback=meta['readback_at']
        if parent.evidence_sha(e)!=EVIDENCE_SHA[sid]:raise ValueError('Evidence SHA mismatch')
        if manifest[sid]['work_github_readback_at'] is not None:
            raise ValueError('Work readback time was not supplied in a readable original report')
        result[sid]=dict(url=meta['url'],sha256=meta['sha256'],bytes=meta['bytes'],http=meta['http'],
            requested_at=meta['requested_at'],completed_at=meta['completed_at'],captured_at=meta.get('captured_at',meta['completed_at']),
            readback_at=readback,work_github_readback_at=None,announced_at=None,native_evidence=e,
            source_path=str(prefix.with_suffix('.response').relative_to(ROOT)) if prefix.is_relative_to(ROOT) else 'TEST_COPY_NOT_PUBLISHED',
            capture_role='ORIGINAL_OFFICIAL_CAPTURE',readback_role='NEW_CODEX_FIXED_GITHUB_READBACK' if sid==PROSPECTUS else 'NEW_CODEX_OFFICIAL_CAPTURE_LOCAL_READBACK',
            work_report_status='NOT_AVAILABLE_IN_THIS_ENVIRONMENT',historical_publication_time='NOT_AUTHENTICATED')
    return result


def build_catalog(folder=OUT):
    sources=load_sources(folder);base=parent_source.build_catalog()
    if base['id']!=PARENT_ID or base!=json.loads((parent_source.OUT/'catalog-v07.json').read_text()):
        raise ValueError('Exact complete parent0.7 required')
    facts={PROSPECTUS:parse_prospectus(sources[PROSPECTUS]['native_evidence'],'2884','2867','2025'),
        FOLLOWUP:parse_followup(sources[FOLLOWUP]['native_evidence'],'2884')}
    return validate(identify(dict(schema=SCHEMA,parent_catalog_id=base['id'],parent_catalog=deepcopy(base),
        coverage=deepcopy(base['coverage']),sources=sources,facts=facts,observations=observations(facts,sources),
        historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False)))


def study_input(old,catalog,manifest,calendar,start,end,code):
    result=parent_source.study_input(old,catalog['parent_catalog'],manifest,calendar,start,end,code)
    result['source_contracts_catalog_id']=catalog['id'];return result


def run():
    catalog=build_catalog();old,manifest=verified_quotes();calendar=build_calendar()
    missing=[parent.quote_diagnostic(catalog['parent_catalog'],c,b['date'],b['close'],b['date'] in calendar['sessions'])
        for c,a in old['assets'].items() for b in a['bars'] if b.get('missing')]
    if dict(diagnostics=missing)!=json.loads((parent_source.OUT/'missing-quotes.json').read_text()):
        raise AssertionError('New contract research must preserve exact parent missing-quote diagnostics')
    design=json.loads((HERE/'generated/design.json').read_text());dates=[b['date'] for b in old['assets']['1101']['bars']];windows=[]
    for start in design['cutoffs']:
        for a,b in [('1101','2884'),('2884','1101')]:
            for horizon in design['horizons']:
                i=dates.index(start)
                if i+horizon>=len(dates):windows.append(dict(A=a,B=b,start=start,end=None,horizon=horizon,status='INSUFFICIENT_SAVED_FORWARD_ROWS'))
                else:
                    q=qualify(study_input(old,catalog,manifest,calendar,start,dates[i+horizon],a),catalog)
                    if q['daily'] or q['journal'] or q['total_net_return'] is not None or q['original_numeric_replay_called']:
                        raise AssertionError('Incomplete source research cannot authorize numeric accounting')
                    windows.append(dict(A=a,B=b,horizon=horizon,**q))
    summary=dict(schema=SCHEMA,actual_official_originals_new=1,archived_originals_reused_and_fixed_github_readback=1,
        observations=len(catalog['observations']),distinct_new_company_actions_claimed=None,
        exact_parent_v07_id=catalog['parent_catalog_id'],original_quote_archives_rechecked=len(manifest),calendar_reports_rechecked=len(calendar['sources']),
        qualification_calls=sum(w['end'] is not None for w in windows),refused_windows=sum(w['status']=='REFUSED_INCOMPLETE_EVENT_ACCOUNTING' for w in windows),
        insufficient_windows=sum(w['end'] is None for w in windows),exchange_unsupported_windows=sum('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED' in w.get('refusal_reasons',[]) for w in windows),
        qualified_total_net_return_windows=sum(w.get('total_net_return') is not None for w in windows),numeric_replay_calls=0,six_strategy_replays=0,
        offline_producer_network_requests=0,missing_quotes_exact_parent_preserved=True,work_report='NOT_AVAILABLE_NOT_CLAIMED_READ',
        android='NOT_TESTED_NEW_BUILD',historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False)
    return {'catalog-v08.json':catalog,'ratio-versions.json':ratio_versions(catalog),
        'missing-quotes.json':dict(diagnostics=missing),'window-qualification.json':dict(windows=windows,ranking=None),'verification.json':summary}


def main():
    values=run()
    for name,value in values.items():
        p=OUT/name
        if p.exists() and json.loads(p.read_text())!=value:raise ValueError('Frozen output differs; choose a new version: '+name)
        if not p.exists():dump(p,value)
    print(json.dumps(values['verification.json']))


if __name__=='__main__':main()
