"""M-DU1: immutable daily continuation coordinator; no new numerical engine.

No certified cross-feed/company-action bridge exists. Preserve old bars and
explicitly reset at each unqualified boundary; never certify a continuous band.
All real inputs, checkpoints, results and previews stay outside Git.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import date, datetime
from decimal import Context, localcontext, ROUND_HALF_EVEN
import fcntl
import json
import os
import shutil
from pathlib import Path
from zoneinfo import ZoneInfo

from graph_core.market_daily import (ROOT, URLS, encode, digest, classify, quote_map,
    candle, capture, Journal, analyze, fingerprint)
from graph_core_chart.mobile_private import external
from product_candidate.build import publish_immutable

VERSION = 'official-market-increment/0.1'


def sources(root, capture_id, now=None):
    """Read/validate captured originals before looking up any cached analysis."""
    if not isinstance(capture_id, str) or len(capture_id) != 64 or any(c not in '0123456789abcdef' for c in capture_id):
        raise ValueError('Invalid capture identity')
    raw = (root/'captures'/(capture_id+'.json')).read_bytes()
    receipts = json.loads(raw)
    if digest(encode(receipts)) != capture_id or len(receipts) != len(URLS) or {r['name'] for r in receipts} != set(URLS):
        raise ValueError('Complete unique fingerprinted source receipt required')
    decoded = {}; signatures = {}
    for r in receipts:
        if r['url'] != URLS[r['name']] or r['status'] != 'RECEIVED':
            raise ValueError('Official source incomplete; last good batch preserved')
        sha = r['sha256']
        if len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError('Invalid raw source identity')
        p = root/'raw'/sha
        if p.is_symlink(): raise ValueError('Source symlink refused')
        b = p.read_bytes()
        if digest(b) != sha or len(b) != r['bytes']: raise ValueError('Source bytes changed')
        decoded[r['name']] = b; signatures[r['name']] = sha
    maps = {}; markets = {}; dates = []
    for m, lower in [('TWSE','twse'), ('TPEX','tpex')]:
        dt, maps[m] = quote_map(json.loads(decoded[lower+'-daily.json']), m); dates.append(dt)
    if len(set(dates)) != 1: raise ValueError('Markets have different dates')
    as_of = dates[0]
    clock = now or datetime.now(ZoneInfo('Asia/Taipei'))
    if clock.tzinfo is None: raise ValueError('Timezone-aware qualification clock required')
    if as_of >= clock.astimezone(ZoneInfo('Asia/Taipei')).date().isoformat():
        raise ValueError('Completion publication not proven; accept prior closed date only')
    if date.fromisoformat(as_of).weekday() >= 5: raise ValueError('Weekend session not authenticated')
    for m, lower in [('TWSE','twse'), ('TPEX','tpex')]:
        markets[m] = classify(json.loads(decoded[lower+'-universe.json']), decoded[m+'-classification.html'], m, as_of)
        if not markets[m]['members']: raise ValueError('Empty ordinary-stock reference refused')
    return as_of, maps, markets, signatures


def seed(root, run_id):
    batch = Journal(root/'runs').read(run_id)['value']
    if not (batch['version'].startswith('finmind-market-history/') or batch['version'] == VERSION):
        raise ValueError('Unsupported seed producer; no inferred bridge')
    rows = batch['stocks']; identities = [s['identity'] for s in rows]
    if len(identities) != len(set(identities)): raise ValueError('Duplicate seed identity')
    if batch['summary']['processed'] != len(rows): raise ValueError('Incomplete seed batch')
    if batch['version'] == VERSION and batch['engine_sha256'] != digest((ROOT/'graph_core/core.py').read_bytes()):
        raise ValueError('Engine changed; explicit migration required')
    return batch


def stock_history(root, row, batch):
    if not row or not row.get('result_key'): return None
    key = row['result_key']; saved = Journal(root/'results').read(key)['value']
    if key.startswith('fm3-result-') and key != 'fm3-result-'+digest(encode(saved)):
        raise ValueError('Seed result fingerprint mismatch')
    if key.startswith('du1-result-') and key != 'du1-result-'+digest(encode(saved)):
        raise ValueError('Increment result fingerprint mismatch')
    if not key.startswith(('fm3-result-', 'du1-result-')): raise ValueError('Unsupported result binding')
    payload = saved['input']; r = saved['result']; context = payload['context']
    if r['schema_version']!='graph-recognition-research/0.2':raise ValueError('Unsupported saved core contract')
    if context['code'] != row['code'] or context['exchange'] != row['market'] or context['price_mode'] != 'RAW_CANDIDATE' or context['volume_unit'] != 'SHARES_REPORTED':
        raise ValueError('Stock/source/basis binding conflict')
    # Core input and result must agree; exact source is retained, never relabelled.
    if r['context'] != context or r['as_of'] != batch['as_of'] or payload['bars'][-1]['date'] != batch['as_of']:
        raise ValueError('Seed cutoff/context conflict')
    h = Journal(root/'histories').read(row['history_key'])['value']
    if h['bars'] != payload['bars'] or h['basis_break_dates'] != payload.get('basis_break_dates', []):
        raise ValueError('Seed history differs from saved numerical input')
    if r['source_records'] != len(payload['bars']): raise ValueError('Seed source length conflict')
    check = deepcopy(r); rid = check.pop('result_id')
    if fingerprint(check) != rid: raise ValueError('Seed numerical result fingerprint changed')
    return saved


def pending_storage_estimate(root, previous, members, run_id):
    """Conservative metadata-only budget, not a promise of exact output size."""
    total=0
    for member in members:
        identity=member['market']+':'+member['code']
        checkpoint='stock-'+digest(encode([run_id,identity]))
        if Journal(root/'du1-checkpoints').path(checkpoint).exists():continue
        old=previous.get(identity,{})
        if old.get('result_key'):
            # New result plus lazy projection, and retained source history.
            try:
                total+=2*Journal(root/'results').path(old['result_key']).stat().st_size
                if old.get('history_key'):total+=Journal(root/'histories').path(old['history_key']).stat().st_size
            except FileNotFoundError:total+=65536  # per-stock dependency refusal is handled below
        else:total+=65536  # bounded one-day input/result/preview estimate
    return total


def process(root, capture_id, *, seed_run, correction_of=None, correction_reason=None, now=None):
    root = external(root)
    as_of, maps, markets, signatures = sources(root, capture_id, now)
    parent = seed(root, seed_run)
    producer = digest(Path(__file__).read_bytes()); engine = digest((ROOT/'graph_core/core.py').read_bytes())
    if parent['version'] == VERSION and parent.get('producer_sha256') != producer:
        raise ValueError('Coordinator changed; explicit migration required')
    # Repeat of a completed batch does not append the same date again.
    if parent['version'] == VERSION and signatures == parent['sources']:
        return dict(id=seed_run, reused=True, new_core_calls=0, summary=parent['summary'])
    if as_of < parent['as_of']: raise ValueError('Cannot append older source')
    if as_of == parent['as_of'] and (correction_of != seed_run or not correction_reason):
        raise ValueError('Same-date revision requires explicit predecessor and reason')
    run_id = 'du1-'+digest(encode(dict(version=VERSION,producer=producer,engine=engine,sources=signatures,
        seed=seed_run,correction_of=correction_of,reason=correction_reason)))
    runs = Journal(root/'runs')
    try:
        saved = runs.read(run_id)['value']
        return dict(id=run_id,reused=True,new_core_calls=0,summary=saved['summary'])
    except FileNotFoundError: pass
    previous = {s['identity']:s for s in parent['stocks']}
    members = [s for market in markets.values() for s in market['members']]
    identities = [s['market']+':'+s['code'] for s in members]
    if len(identities) != len(set(identities)): raise ValueError('Duplicate ordinary-stock member')
    estimated_bytes=pending_storage_estimate(root,previous,members,run_id)
    if shutil.disk_usage(root).free<estimated_bytes:raise OSError('Insufficient private capacity for retained versions; no deletion, migration or analysis attempted')
    results = Journal(root/'results'); histories = Journal(root/'histories'); checkpoints = Journal(root/'du1-checkpoints')
    rows = []; calls = 0
    for member, identity in zip(members, identities):
        checkpoint = 'stock-'+digest(encode([run_id,identity]))
        try: cached = checkpoints.read(checkpoint)['value']
        except FileNotFoundError: cached = None
        if cached is not None:
            if (cached['identity'],cached['code'],cached['market'],cached['as_of'])!=(identity,member['code'],member['market'],as_of):raise ValueError('Checkpoint identity/cutoff conflict')
            if cached.get('result_key'):
                retained=stock_history(root,cached,dict(as_of=as_of))
                binding=retained['increment_source_binding']
                if binding['official_sources']!=signatures or binding['seed_run']!=seed_run:raise ValueError('Checkpoint source/seed conflict')
            rows.append(cached); continue
        old = previous.get(identity)
        row = dict(member,identity=identity,as_of=as_of,history_key=None,result_key=None,
            prior_status=old['status'] if old else 'NEW_REFERENCE_MEMBER',
            data_qualified=False,execution_qualified=False,execution_model_qualified=False,live_execution_authorized=False,historical_signal_eligible=False,
            policy_authorized=False,primary_pressure_id=None,imputed_close=None,valuation=None,
            corporate_action_coverage='UNKNOWN',historical_available_at='UNKNOWN',
            continuity_qualification='SEGMENTED_NOT_CERTIFIED',classification_quality='NOT_VALIDATED')
        stage = 'DATA_QUALITY_FAILURE'
        try:
            raw = maps[member['market']].get(member['code'])
            if raw is None:
                row.update(status='MISSING_QUOTE',reason='Ordinary member absent from daily feed; not proof of suspension/delisting')
            else:
                bar, reason = candle(raw, member['market'])
                if reason: row.update(status=reason,reason=reason)
                else:
                    prior = stock_history(root,old,parent)
                    bars = deepcopy(prior['input']['bars']) if prior else []
                    breaks = sorted(set(prior['input'].get('basis_break_dates',[])+prior['result']['data_gaps']['basis_resets'])) if prior else []
                    if old and old.get('isin') != member.get('isin'): raise ValueError('ISIN changed; continuity refused')
                    # No certified company-action coverage for the new interval.
                    # The full old segment remains visible, but comparison/MA/MACD
                    # restart at the official feed boundary, including revisions.
                    bars = [b for b in bars if b['date'] < as_of] + [bar]
                    breaks = sorted(set([d for d in breaks if d < as_of]+([as_of] if len(bars)>1 else [])))
                    payload = dict(schema_version='graph-recognition-input/0.1',context=dict(
                        code=member['code'],exchange=member['market'],source_id=fingerprint(dict(seed=seed_run,identity=identity,sources=signatures)),
                        price_basis_id=identity+'-RAW-SEGMENTED-UNVERIFIED',price_mode='RAW_CANDIDATE',volume_unit='SHARES_REPORTED',
                        source_kind='EXPLICITLY_SEGMENTED_RETAINED_HISTORY_AND_OFFICIAL_DAILY',
                        corporate_action_comparability='UNKNOWN_RESET_AT_NEW_OFFICIAL_DATE',historical_publication_timing='UNKNOWN'),
                        bars=bars,basis_break_dates=breaks,expected_dates=sorted(set([b['date'] for b in bars]+([d for d in prior['input'].get('expected_dates',[]) if d<=as_of] if prior else []))))
                    stage = 'CORE_FAILURE'; calls += 1
                    with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999)):
                        result = analyze(payload,as_of=as_of)
                    stage = 'STORAGE_FAILURE'
                    value = dict(input=payload,result=result,increment_source_binding=dict(seed_run=seed_run,
                        seed_result_key=old.get('result_key') if old else None,seed_context=prior['input']['context'] if prior else None,
                        retained_prefix_fingerprint=fingerprint(prior['input']['bars']) if prior else None,
                        new_date=as_of,capture_id=capture_id,official_sources=signatures,
                        source_boundary_reset=as_of,company_action_coverage='UNKNOWN',cross_feed_comparability='NOT_CERTIFIED'))
                    hk = 'history-'+fingerprint(dict(bars=bars,basis_break_dates=breaks)).split(':')[1]
                    rk = 'du1-result-'+digest(encode(value))
                    histories.save(hk,dict(bars=bars,basis_break_dates=breaks)); results.save(rk,value)
                    row.update(status='SEGMENTED_RESEARCH' if len(bars)>1 else 'INSUFFICIENT_HISTORY',
                        history_key=hk,result_key=rk,history_records=len(bars),current_comparable_records=1,
                        reason='Unknown cross-feed/action interval: reset new segment; old bars retained, no continuous-band certification',
                        source_binding=value['increment_source_binding'],missing_expected_dates=result['data_gaps']['missing_expected_dates'])
                    stock_history(root,row,dict(as_of=as_of))  # actual saved-byte dependency readback
        except FileNotFoundError:
            if stage!='DATA_QUALITY_FAILURE':raise
            row.update(status='DATA_QUALITY_FAILURE',reason='Saved seed dependency missing; no fabricated fallback history',result_key=None)
        except (OSError, RuntimeError): raise  # infrastructure failure cannot publish a partial head
        except Exception as e:
            if stage == 'STORAGE_FAILURE': raise
            row.update(status=stage,reason=type(e).__name__+': '+str(e),result_key=None)
        checkpoints.save(checkpoint,row); rows.append(row)
    removed = [dict(identity=k,status='ABSENT_FROM_CURRENT_REGISTRY_NOT_PROOF_OF_DELISTING') for k in previous if k not in identities]
    prior_isins = {r['isin']:r for r in previous.values() if r.get('isin')}
    changes = [dict(isin=s['isin'],old_identity=prior_isins[s['isin']]['identity'],new_identity=s['identity'],
        status='MARKET_CHANGE_OBSERVED_NO_HISTORY_MERGE') for s in rows if s.get('isin') in prior_isins and prior_isins[s['isin']]['identity'] != s['identity']]
    summary = dict(as_of=as_of,expected=len(members),processed=len(rows),expected_by_market={m:len(v['members']) for m,v in markets.items()},
        processed_by_market=dict(Counter(r['market'] for r in rows)),terminal_counts=dict(Counter(r['status'] for r in rows)),
        multiday_retained_by_market=dict(Counter(r['market'] for r in rows if r.get('history_records',0)>1)),
        continuous_new_interval_certified=0,charts=sum(bool(r['result_key']) for r in rows),actual_core_calls=calls,
        estimated_pending_storage_bytes=estimated_bytes,all_known_members_have_terminal=len(rows)==len(members),both_market_universes_read=True,both_market_quotes_read=True,
        source_policy='UNKNOWN_INTERVAL_ALWAYS_SEGMENTED_NOT_UNCONDITIONAL_FINMIND_MERGE',
        status='PARTIAL_SEGMENTED',scheduling='NOT_ENABLED',fixed_android_url='NOT_DEPLOYED')
    runs.save(run_id,dict(version=VERSION,as_of=as_of,producer_sha256=producer,engine_sha256=engine,sources=signatures,
        capture_id=capture_id,parent_run=seed_run,correction_of=correction_of,correction_reason=correction_reason,
        markets=markets,observed_sessions=sorted(set(parent.get('observed_sessions',[])+[as_of])),stocks=rows,
        removed_registry_entries=removed,market_changes=changes,summary=summary))
    return dict(id=run_id,reused=False,new_core_calls=calls,summary=summary)


def blocked_terminals(root, capture_id, parent_id, reason):
    """Keep each observable ordinary member, even when no new batch can publish."""
    parent=seed(root,parent_id);fallback={s['identity']:s for s in parent['stocks']}
    receipt=json.loads((root/'captures'/(capture_id+'.json')).read_bytes())
    decoded={}
    if digest(encode(receipt))!=capture_id:raise ValueError('Corrupt refusal receipt')
    for r in receipt:
        if r.get('status')!='RECEIVED' or r.get('url')!=URLS.get(r.get('name')):continue
        sha=r.get('sha256','')
        if len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):continue
        raw=(root/'raw'/sha).read_bytes()
        if digest(raw)==r['sha256'] and len(raw)==r['bytes']:decoded[r['name']]=raw
    observed_dates={}
    for market,lower in [('TWSE','twse'),('TPEX','tpex')]:
        try:observed_dates[market]=quote_map(json.loads(decoded[lower+'-daily.json']),market)[0]
        except (KeyError,ValueError):observed_dates[market]=None
    reference_cutoff=max([parent['as_of']]+[d for d in observed_dates.values() if d])
    rows=[];references={}
    for market,lower in [('TWSE','twse'),('TPEX','tpex')]:
        try:
            registry=classify(json.loads(decoded[lower+'-universe.json']),decoded[market+'-classification.html'],market,reference_cutoff)
            members=registry['members'];references[market]=dict(role='OBSERVED_CLASSIFICATION_NOT_ACCEPTED_QUOTE_SESSION',date=registry['observed_at'])
        except (KeyError,ValueError):
            members=[r for r in fallback.values() if r['market']==market];references[market]=dict(role='PRIOR_REFERENCE_FALLBACK_NOT_CURRENT_MEMBERSHIP',date=parent['as_of'])
        rows.extend(dict(identity=market+':'+s['code'],code=s['code'],market=market,status='BATCH_NOT_APPLIED',reason=reason,
            result_key=None,reference=references[market]) for s in members)
    return dict(observed_quote_dates=observed_dates,reference_roles=references,expected_by_market=dict(Counter(r['market'] for r in rows)),
        terminals=len(rows),stocks=rows,diagnostic_core_calls=0,not_accepted_new_session=True)


def update(root, *, seed_run=None, capture_id=None, fetch=False, correction_of=None, correction_reason=None, now=None):
    """One explicit RUN, single writer; publish head only after readable preview."""
    from graph_core.market_preview import build
    root = external(root)
    if not root.is_dir(): raise ValueError('Existing private Journal root required')
    with (root/'daily.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        head = root/'current-increment-run.json'
        previous = json.loads(head.read_bytes()) if head.exists() else None
        parent = previous['id'] if previous else seed_run
        if not parent: raise ValueError('Explicit saved FM3 seed required on first run')
        if bool(fetch) == bool(capture_id): raise ValueError('Choose one: single capture fetch or saved capture')
        cap = capture(root) if fetch else capture_id
        committed=False
        try:
            result = process(root,cap,seed_run=parent,correction_of=correction_of,correction_reason=correction_reason,now=now)
            if previous and result['reused'] and result['id']==previous['id']:
                p=Path(previous['private_preview']['path'])
                if digest(p.read_bytes())!=previous['private_preview']['sha256']: raise ValueError('Last preview changed')
                from graph_core_chart.mobile_private import batch_index
                batch_index(previous['batch_index'])
                return dict(result,private_preview=previous['private_preview'],batch_index=previous['batch_index'],head_unchanged=True)
            preview = build(root,result['id'])
            from graph_core_chart.mobile_private import preview_index
            preview_index(preview['path'])
            if digest(Path(preview['path']).read_bytes())!=preview['sha256']: raise ValueError('Preview readback mismatch')
            entries=[dict(run_id=result['id'],as_of=result['summary']['as_of'],path=preview['path'],
                bytes=preview['bytes'],sha256=preview['sha256'])]
            if previous and previous.get('batch_index'):
                prior_index=json.loads(Path(previous['batch_index']).read_bytes())
                entries.extend(prior_index['batches'])
            else:
                old_page=root/'preview'/parent/'market-fm3-v02.html'
                if old_page.is_file():
                    raw=old_page.read_bytes(); old_batch=seed(root,parent)
                    entries.append(dict(run_id=parent,as_of=old_batch['as_of'],path=str(old_page),bytes=len(raw),sha256=digest(raw)))
            catalogue=encode(dict(schema='private-saved-batches/0.1',batches=entries))
            catalogue_path=root/'du1-batches'/(digest(catalogue)+'.json')
            publish_immutable(catalogue_path,catalogue)
            from graph_core_chart.mobile_private import batch_index
            batch_index(catalogue_path)
            value = dict(id=result['id'],private_preview=preview,batch_index=str(catalogue_path),prior=previous['id'] if previous else parent)
            pending = root/'current-increment.pending'
            if pending.is_symlink() or head.is_symlink():raise ValueError('Head/pending symlink refused')
            with pending.open('wb') as f:f.write(encode(value));f.flush();os.fsync(f.fileno())
            os.replace(pending,head)
            committed=True
            fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
            try: os.fsync(fd)
            finally: os.close(fd)
            return dict(result,private_preview=preview,batch_index=str(catalogue_path),head_unchanged=False)
        except Exception as e:
            if committed:
                return dict(status='COMMITTED_DURABILITY_UNKNOWN',id=result['id'],private_preview=preview,
                    batch_index=str(catalogue_path),reason=type(e).__name__+': '+str(e),head_unchanged=False,
                    new_capture_applied=True,new_core_calls=result['new_core_calls'],summary=result['summary'])
            failure=dict(status='BLOCKED',reason=type(e).__name__+': '+str(e),capture_id=cap,last_saved_run=previous['id'] if previous else parent,
                new_capture_applied=False,head_unchanged=True)
            try:failure['terminal_diagnostic']=blocked_terminals(root,cap,parent,failure['reason'])
            except Exception as diagnostic_error:failure['terminal_diagnostic']={'status':'UNAVAILABLE','reason':type(diagnostic_error).__name__+': '+str(diagnostic_error)}
            publish_immutable(root/'du1-failures'/(digest(encode(failure))+'.json'),encode(failure))
            return failure


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True);p.add_argument('--seed-run');p.add_argument('--capture');p.add_argument('--fetch',action='store_true')
    p.add_argument('--correction-of');p.add_argument('--correction-reason');a=p.parse_args()
    result=update(a.root,seed_run=a.seed_run,capture_id=a.capture,fetch=a.fetch,correction_of=a.correction_of,correction_reason=a.correction_reason)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result.get('status') in ('BLOCKED','COMMITTED_DURABILITY_UNKNOWN'):raise SystemExit(2)

if __name__=='__main__':main()
