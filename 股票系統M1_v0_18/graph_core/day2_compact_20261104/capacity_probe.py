"""Actual new-day, MEMORY-ONLY core/DU2 profile. No synthetic prices or writes to FM3.
Six deterministic resource samples (short/median/max per market), not market ranking.
Full-result wire bytes are checked losslessly in memory; only opaque receipts persist.
"""
from copy import deepcopy
from collections import Counter
from decimal import Context,localcontext,ROUND_HALF_EVEN
from pathlib import Path
import gc,gzip,json,math,resource,shutil,time
from graph_core import market_daily as d,market_increment as inc
from rotation_research.store import Journal
from rotation_research import artifact_codec as c
from technical_chart.interned_json import pack,unpack
from graph_core.day1_20261103.probe_once import heads
from .capture_once import ROOT,WORK,MIN_FREE


def allocated(n):return math.ceil(n/4096)*4096

def measure_wire(wire,anchor,virtual_existing=()):
    base=c.base_index(anchor,ROOT);new=set();cost={6:0,9:0};stored={6:0,9:0};pieces=0;reused=0
    for at,part in c.chunks(wire):
        h=c.sha(part);pieces+=1
        if h in base and base[h]['bytes']==len(part):reused+=len(part);continue
        if c.blob_path(ROOT,h).exists() or h in new or h in virtual_existing:continue
        new.add(h)
        for level in (6,9):
            body=gzip.compress(part,compresslevel=level,mtime=0)
            if gzip.decompress(body)!=part:raise ValueError('LOSSLESS_GZIP_CHECK_FAILED')
            cost[level]+=allocated(len(body));stored[level]+=len(body)
    # Exact-body gzip blocks measured; 4KiB per actual wire manifest + recipe.
    # Manifest size depends on all piece refs; budget 320 bytes/piece + header.
    overhead=allocated(pieces*320+512)+4096
    return dict(new_gzip_block_bytes={str(k):v for k,v in cost.items()},new_gzip_payload_bytes={str(k):v for k,v in stored.items()},
        descriptor_budget_bytes=overhead,descriptor_is_budget_not_actual_write=True,pieces=pieces,source_span_bytes_reused=reused,
        planned_result_bytes={str(k):v+overhead for k,v in cost.items()},new_piece_count=len(new))


def run():
    finished=WORK/'capacity-probe-private.json'
    if finished.exists():
        result=json.loads(finished.read_bytes());print(json.dumps(dict(status='REUSED_PREFLIGHT',new_core_calls=0,head_unchanged=True,prior_status=result['status'])));return result
    marker=WORK/'capacity-probe-started-private.json'
    if marker.exists():raise FileExistsError('PROFILE_ALREADY_STARTED_DO_NOT_START_ANOTHER')
    source=json.loads((WORK/'repaired-source-private.json').read_bytes())
    if source['qualification']['status']!='READY_FOR_REAL_INCREMENT':raise ValueError('REAL_DUAL_MARKET_SOURCE_REQUIRED')
    as_of,maps,markets,signatures=inc.sources(WORK/'capture',source['capture_id'])
    before=heads(ROOT);parent_id=json.loads((ROOT/'current-increment-run.json').read_bytes())['id'];parent=inc.seed(ROOT,parent_id)
    if as_of<=parent['as_of']:raise ValueError('NEW_DATE_REQUIRED')
    if parent['version']==inc.VERSION and parent['producer_sha256']!=d.digest(Path(inc.__file__).read_bytes()):raise ValueError('ORIGINAL_PRODUCER_CHANGED_MIGRATION_REQUIRED')
    previous={s['identity']:s for s in parent['stocks']};members=[s for market in markets.values() for s in market['members']]
    eligibility=Counter();by_market={m:[] for m in markets};new_valid=Counter();metadata=[]
    for s in members:
        ident=s['market']+':'+s['code'];raw=maps[s['market']].get(s['code'])
        if raw is None:eligibility[(s['market'],'MISSING_QUOTE')]+=1;continue
        try:bar,reason=d.candle(raw,s['market'])
        except Exception:eligibility[(s['market'],'DATA_QUALITY_FAILURE')]+=1;continue
        if reason:eligibility[(s['market'],reason)]+=1;continue
        old=previous.get(ident)
        if old and old.get('isin')!=s.get('isin'):
            eligibility[(s['market'],'ISIN_CHANGED_CONTINUITY_REFUSED')]+=1;continue
        eligibility[(s['market'],'VALID_SOURCE_BAR_NOT_YET_ANALYZED')]+=1
        if not old or not old.get('result_key'):new_valid[s['market']]+=1;continue
        n=c.info(Journal(ROOT/'results').path(old['result_key']))['bytes']
        by_market[s['market']].append((n,s,old,bar));metadata.append(n)
    samples=[]
    for market,rows in by_market.items():
        short=sorted((r for r in rows if r[0]<65536),key=lambda r:(r[0],r[1]['code']))
        long=sorted((r for r in rows if r[0]>=65536),key=lambda r:(r[0],r[1]['code']))
        if short:samples.append((market,'short',short[len(short)//2]))
        if long:samples.append((market,'long-median',long[len(long)//2]))
        if len(long)>1:samples.append((market,'long-largest',long[-1]))
    c.immutable(marker,c.encoded(dict(as_of=as_of,source_capture_id=source['capture_id'],maximum_new_day_core_calls=len(samples),
        source_qualified=True,save_market_results=False,update_head=False,selection='Per market short median, long median and largest logical result; NOT opportunity ranking')))
    receipts=[];started=time.monotonic()
    for market,kind,(n,s,old,bar) in samples:
        ident=market+':'+s['code'];print(json.dumps(dict(phase='MEMORY_ONLY_TRUE_NEW_DAY',market=market,resource_class=kind,sample=len(receipts)+1,total=len(samples))),flush=True)
        prior=inc.stock_history(ROOT,old,parent)
        bars=[b for b in deepcopy(prior['input']['bars']) if b['date']<as_of]+[bar]
        breaks=sorted(set([x for x in prior['input'].get('basis_break_dates',[])+prior['result']['data_gaps']['basis_resets'] if x<as_of]+([as_of] if len(bars)>1 else [])))
        payload=dict(schema_version='graph-recognition-input/0.1',context=dict(code=s['code'],exchange=market,
            source_id=inc.fingerprint(dict(seed=parent_id,identity=ident,sources=signatures)),price_basis_id=ident+'-RAW-SEGMENTED-UNVERIFIED',
            price_mode='RAW_CANDIDATE',volume_unit='SHARES_REPORTED',source_kind='EXPLICITLY_SEGMENTED_RETAINED_HISTORY_AND_OFFICIAL_DAILY',
            corporate_action_comparability='UNKNOWN_RESET_AT_NEW_OFFICIAL_DATE',historical_publication_timing='UNKNOWN'),
            bars=bars,basis_break_dates=breaks,expected_dates=sorted(set([b['date'] for b in bars]+[x for x in prior['input'].get('expected_dates',[]) if x<=as_of])))
        start=time.monotonic()
        with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999)):
            result=inc.analyze(payload,as_of=as_of)
        value=dict(input=payload,result=result,increment_source_binding=dict(seed_run=parent_id,seed_result_key=old['result_key'],seed_context=prior['input']['context'],
            retained_prefix_fingerprint=inc.fingerprint(prior['input']['bars']),new_date=as_of,capture_id=source['capture_id'],official_sources=signatures,
            source_boundary_reset=as_of,company_action_coverage='UNKNOWN',cross_feed_comparability='NOT_CERTIFIED'))
        key='du1-result-'+d.digest(d.encode(value));record=dict(schema='rotation-record/0.1',id=key,value=value)
        raw=c.journal_bytes(record);base_path=Journal(ROOT/'results').path(old['result_key'])
        _,desc=c.manifest(base_path)
        if desc['schema']!=c.INTERNED:raise ValueError('EXISTING_INTERNED_PARENT_REQUIRED_NO_NEW_ANCHOR_BUDGET_GUESS')
        anchor=c.resolve(ROOT,desc['anchor_path']);transport=json.loads(c.read_bytes(anchor))
        wire=c.encoded(pack(record,base=transport))
        if c.journal_bytes(unpack(json.loads(wire)))!=raw:raise ValueError('ORIGINAL_BYTES_CHANGED_BY_TRANSPORT')
        profile=measure_wire(wire,anchor)
        receipt=dict(identity=ident,market=market,resource_class=kind,old_logical_bytes=n,new_original_bytes=len(raw),wire_bytes=len(wire),
            payload_id=inc.fingerprint(payload),result_id=result['result_id'],original_bytes_sha256=c.sha(raw),wire_sha256=c.sha(wire),
            as_of=as_of,source_records=result['source_records'],roundtrip_exact_original_bytes=True,seconds=time.monotonic()-start,profile=profile,
            real_new_day_data=True,market_result_saved=False)
        receipts.append(receipt);c.immutable(WORK/'profiles'/(str(len(receipts))+'.json'),c.encoded(receipt))
        del prior,payload,result,value,record,raw,wire,transport;gc.collect()
    estimates={6:0,9:0};groups=[]
    for market,rows in by_market.items():
        short=[x for x in rows if x[0]<65536];long=[x for x in rows if x[0]>=65536]
        measured=[x for x in receipts if x['market']==market]
        for level in (6,9):
            sm=next((x for x in measured if x['resource_class']=='short'),None)
            short_cost=(sm['profile']['planned_result_bytes'][str(level)] if sm else 65536)*len(short)
            ratios=[x['profile']['planned_result_bytes'][str(level)]/x['old_logical_bytes'] for x in measured if x['resource_class'].startswith('long')]
            long_cost=math.ceil(sum(x[0] for x in long)*max(ratios)) if ratios else 0
            fresh=new_valid[market]*65536;estimates[level]+=short_cost+long_cost+fresh
            groups.append(dict(market=market,gzip_level=level,short_count=len(short),long_count=len(long),new_valid_without_history=new_valid[market],
                short_projected_bytes=short_cost,long_projected_bytes=long_cost,fresh_budget_bytes=fresh,method='Measured short median and max observed long byte ratio times original logical sum; extrapolation NOT full-market actual'))
    free=shutil.disk_usage(ROOT).free;available=free-MIN_FREE
    result=dict(milestone='M-DAY2-COMPACT',status='CAPACITY_NOT_CERTIFIED_DO_NOT_APPLY',as_of=as_of,original_as_of=parent['as_of'],
        ordinary_reference={m:len(v['members']) for m,v in markets.items()},ordinary_total=len(members),
        source_intake_terminal_counts={m:{k:n for (mk,k),n in eligibility.items() if mk==m} for m in markets},
        source_reference_added=len({s['market']+':'+s['code'] for s in members}-set(previous)),reference_removed=len(set(previous)-{s['market']+':'+s['code'] for s in members}),
        new_day_core_calls=len(receipts),memory_only_sample_count=len(receipts),published_new_charts=0,new_full_batch_processed=0,
        result_only_projected_bytes={str(k):v for k,v in estimates.items()},
        result_only_projected_shortfall_at_gzip9=max(0,estimates[9]-available),
        forecast_is_extrapolation=True,forecast_excludes_history_preview_lite_and_directories=True,
        sample_receipts=receipts,groups=groups,free_bytes=free,minimum_free_bytes=MIN_FREE,available_above_reserve_bytes=available,
        max_parent_logical_result_bytes=max(metadata),existing_single_result_scratch_budget=64*1024**2+2*max(metadata),
        elapsed_seconds=time.monotonic()-started,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        original_heads_before=before,original_heads_after=heads(ROOT),original_root_writes=0,
        gzip9_format_compatible_and_lossless=True,gzip9_applied_to_production=False,provider_calls_this_probe=0)
    if result['original_heads_after']!=before:raise ValueError('ORIGINAL_HEAD_CHANGED')
    c.immutable(finished,c.encoded(result));print(json.dumps({k:v for k,v in result.items() if k not in ('sample_receipts','groups','original_heads_before','original_heads_after')},ensure_ascii=False),flush=True)
    return result

if __name__=='__main__':run()
