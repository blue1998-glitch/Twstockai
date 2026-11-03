"""Public aggregate receipt only; no candles, individual results or credentials.
Reads already-completed private receipts. Never runs source capture or analysis.
"""
import json,shutil,subprocess
from pathlib import Path
from collections import Counter
from datetime import datetime
from rotation_research import artifact_codec as c
from rotation_research.store import Journal
from graph_core.day1_20261103.apply_once import allocated


def build(root,work,out):
    r=Path(root);w=Path(work);out=Path(out)
    read=lambda p:json.loads(Path(p).read_bytes())
    probe=read(w/'attempt1/probe-private.json');resume=read(w/'resume-result-private.json');started=read(w/'increment-started.json');restart=read(w/'resume-started.json');repeat=read(w/'repeat-private.json')
    ui=read(w/'ui-verification-private.json');browser=read(w/'browser-first/summary.json');recent=read(w/'browser-first/current-day-view.json');audit=read(w/'published-inventory-private.json')
    base=read(w.parent/'port1_20261102/real-validated-inventory-private.json')
    head=read(r/'current-increment-run.json');batch=Journal(r/'runs').read(head['id'])['value'];oldbatch=Journal(r/'runs').read(batch['parent_run'])['value']
    assert head['id']==resume['id'] and batch['capture_id']==probe['capture_id']
    assert ui['status']=='PASS' and browser['status']=='PASS_REAL_PRIVATE_BROWSER' and recent['status']=='PASS'
    assert c.sha((r/'fm3-continuation.json').read_bytes())==probe['heads_before']['fm3-continuation.json']['sha256']
    old_inodes={(x['source_device'],x['source_inode']) for x in base['files']};data_bytes=allocated(r,old_inodes)
    root_inodes={(p.stat().st_dev,p.stat().st_ino) for p in r.rglob('*') if p.is_file()};seen=set();work_bytes=0
    for p in w.rglob('*'):
        if not p.is_file() or p.is_symlink():continue
        s=p.stat();key=s.st_dev,s.st_ino
        if key not in root_inodes and key not in seen:seen.add(key);work_bytes+=s.st_blocks*512
    source=dict(status='QUALIFIED_PRIOR_CLOSED_COMMON_REPORTED_SESSION',as_of=batch['as_of'],capture_id=probe['capture_id'],actual_market_dates=probe['actual_market_dates'],official_get_attempts=probe['source_get_attempts'],complete_sources=probe['complete_sources'],source_failures=probe['source_failures'],retries=0,alternate_sources=0,finmind_history_gets=0,reference_role='OBSERVED_CURRENT_REFERENCE_NOT_HISTORICAL_UNIVERSE_CERTIFICATION',actual_qualification_clock=probe['qualification_clock_taipei'],capture_elapsed_seconds=probe['wall_seconds'],capture_peak_rss_kib=probe['max_rss_kib'],source_signatures=probe['qualification']['source_signatures'])
    summary=dict(batch['summary'])
    summary.update(milestone='M-DAY1',milestone_status='REAL_NEW_SESSION_PUBLISHED_WITH_SEGMENTATION_LIMITS',run_id=head['id'],source_qualified=True,new_head_published=True,unprocessed=summary['expected']-summary['processed'],refusals=sum(not s.get('result_key') for s in batch['stocks']),registered_members_added=len(set(s['identity'] for s in batch['stocks'])-set(s['identity'] for s in oldbatch['stocks'])),registered_members_removed=len(batch['removed_registry_entries']),market_changes=len(batch['market_changes']),terminal_by_market={m:dict(Counter(x['status'] for x in batch['stocks'] if x['market']==m)) for m in ('TWSE','TPEX')},historical_signal_eligible=False,primary_pressure_id=None,policy_authorized=False,execution_qualified=False,imputed_close=None,valuation=None)
    oldset={s['identity'] for s in oldbatch['stocks'] if s.get('result_key')};newset={s['identity'] for s in batch['stocks'] if s.get('result_key')}
    summary.update(new_chart_identities=len(newset-oldset),retained_current_chart_identities=len(oldset&newset),old_chart_identities_only_in_prior_catalogue=len(oldset-newset),original_charts_retained_in_old_catalogue=len(oldset))
    free=shutil.disk_usage(r).free
    resources=dict(new_root_unique_regular_file_allocated_bytes=data_bytes,new_non_shared_private_work_regular_file_bytes_at_measurement=work_bytes,measurement_scope='Unique new regular-file inodes; shared aliases counted once. Directory and auxiliary costs included in filesystem net use.',filesystem_free_before_capture=probe['free_before_bytes'],filesystem_free_at_measurement=free,filesystem_net_used_since_pre_capture=probe['free_before_bytes']-free,minimum_required_free_bytes=536870912,writer_guard_floor_bytes=603979776,writer_capacity_refusals=0,capture_elapsed_seconds=probe['wall_seconds'],interrupted_first_worker_cpu_seconds=restart['prior_cpu_seconds'],interrupted_first_worker_wall_seconds='UNKNOWN_EXACT_TERMINATION_TIME',interrupted_first_worker_peak_rss_kib='UNKNOWN_NOT_RECONSTRUCTED',resume_publication_elapsed_seconds=resume['resume_elapsed_seconds'],resume_publication_peak_rss_kib=resume['resume_max_rss_kib'],observed_start_to_publication_seconds=(datetime.fromisoformat(resume['completed_at'])-datetime.fromisoformat(started['started_at'])).total_seconds(),start_to_publication_includes_interruption=True,logical_private_index_bytes=resume['private_preview']['bytes'],logical_index_mobile_burden='347275022 bytes; viewport tests do not certify physical Android memory/network usability',independent_backup='UNKNOWN',environment_restart_persistence='UNKNOWN',legacy_directory_inclusive_measurements_superseded_not_overwritten=True)
    preservation=dict(status='PASS_OLD_AUDIT_REUSE_AND_NEW_APPEND_HASH_CLOSURE',old_paths_unchanged=audit['append_verification']['unchanged_old_paths'],old_payload_full_sha_repeated=False,old_full_audit_manifest_id=base['manifest_id'],current_append_manifest_id=audit['manifest_id'],current_file_paths=audit['counts']['files'],new_unique_physical_hashes=audit['append_verification']['new_inode_hashes'],du2_logical_artifacts=audit['counts']['du2_logical_artifacts'],dependencies_checked=audit['counts']['dependency_edges'],original_fm3_head_sha_unchanged=True,original_fm3_terminals=len(oldbatch['stocks']),original_charts=len(oldset),pre_resume_paths_unchanged=resume['pre_resume_paths_unchanged'],old_and_new_catalogue_dates=[batch['as_of'],oldbatch['as_of']],source_backup_created=False)
    verification=dict(status='PASS_SCOPED_ENGINEERING_AND_REAL_SAVED_DATA',python_unique_methods=8,capacity_unique_methods=4,completion_unique_methods=4,intermediate_batches_not_added=True,nonzero_directory_counterexample=dict(initial_tmp_fixture='4 PASS; temporary directories reported zero blocks',explicit_nonzero_fixture_before_fix='1 failure of 4 methods; 8192 vs expected 0',after_fix='4 of 4 PASS',qualification='Synthetic filesystem metadata, not market sample'),actual_new_core_calls_first_attempt=batch['summary']['actual_core_calls'],actual_resume_core_calls=0,actual_same_source_repeat=repeat,source_crosscheck_saved_cases=4,source_crosscheck_markets=['TWSE','TPEX'],source_checks='New candles equal original official capture; old K/MA/MACD prefixes unchanged; new indicator warmup null',browser_groups=len(browser['checks'])+recent['checks'],browser_main_groups=len(browser['checks']),browser_extra_current_day_groups=recent['checks'],exact_json_downloads=browser['downloads'],browser_viewports=[[320,844],[390,844],[844,390],[1280,900]],javascript_errors=browser['page_errors'],external_origins=browser['external_origins'],owner_http_controls=ui['owner_http'],actual_current_candidate_records=ui['event_records'],actual_current_event_stock_count=ui['event_stocks'],candidate_events_are_not_independent_signals=True,permanent_service_started=False,temporary_test_listener_stopped=True,android='NOT_TESTED_NEW_BUILD',daily_schedule='NOT_ENABLED',external_deployment=False)
    verification['conditional_missing_price_query']='NOT_EXECUTED; cfg.query_date was null. Gap/reset equality checked; actual new-day query separately passed.'
    repo=Path(__file__).resolve().parents[3];protected={}
    for rel in ['graph_core/core.py','graph_core/market_increment.py','graph_core/market_daily.py','graph_core/market_preview.py','product_candidate/macd.py','src/moving_averages.py','rotation_research/store.py','rotation_research/artifact_codec.py','graph_core_chart/mobile_private.py']:
        path=Path('股票系統M1_v0_18')/rel;raw=(repo/path).read_bytes()
        assert raw==subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+str(path)])
        protected[rel]=c.sha(raw)
    protected=dict(status='ORIGINAL_NUMERIC_AND_SOURCE_MODULES_UNCHANGED',sha256=protected)
    values={'source-verification.json':source,'summary.json':summary,'resources.json':resources,'preservation.json':preservation,'verification.json':verification,'protected-source.json':protected}
    for name,value in values.items():(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    c.immutable(w/'canonical-resource-measurement-private.json',c.encoded(resources))
    return dict(status=summary['milestone_status'],terminals=summary['processed'],charts=summary['charts'],new_unique_file_bytes=data_bytes,free_bytes=free,resume_seconds=resources['resume_publication_elapsed_seconds'],resume_peak_rss_kib=resources['resume_publication_peak_rss_kib'],browser_groups=verification['browser_groups'])


if __name__=='__main__':
    import sys
    print(json.dumps(build(*sys.argv[1:])))
