"""Bounded source preflight only; stops at missing market-source qualification.

This is diagnostic evidence, not the M-R2 diary producer or a new store/engine.
No HTTP, market fetching, follow-up classification or trading decisions.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from graph_core.finmind_adapter import analyze_response
from graph_core.finmind_run import _parse, external_path
from rotation_research.store import Journal

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
LOCAL = Path('/workspace/twstockai-local-data')


def main():
    expected = json.loads((HERE/'expected.json').read_text())
    frozen = json.loads((HERE/'baseline.json').read_text())
    for name, digest in frozen['frozen'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == digest
    for source in frozen['protected_files']:
        assert hashlib.sha256((PROJECT/source['path']).read_bytes()).hexdigest() == source['sha256']
    original = external_path(LOCAL/'m2-3-finmind-20261030/response.json')
    raw = original.read_bytes()
    receipt = json.loads(original.with_name('acquisition.json').read_text())
    assert receipt['response_sha256'] == hashlib.sha256(raw).hexdigest()
    response = _parse(raw)
    journal = Journal(external_path(LOCAL/'mr2-20261101/journal'))
    public_days = []
    for day in ('2026-07-21', '2026-07-22'):
        saved = json.loads((LOCAL/f'm2-3-finmind-final-20261030/input-{day}.json').read_text())
        request = saved['request']; assert request['as_of'] == day and request['code']=='2884'
        # Check retained official sources using the existing intake path, no query.
        from graph_core.finmind_run import _retained_sources
        official, _, warnings = _retained_sources()
        assert request['expected_dates'] == [r['date'] for r in official]
        assert request['basis_warnings'] == warnings
        result = analyze_response(response, request)
        core = result['analysis']; assert core['schema_version'] == expected['core_version']
        fresh = [deepcopy(p) for p in core['pivots'] if p['confirmed_at']==day]
        assert len(fresh) == expected['new_confirmed_event_counts'][day]
        if day=='2026-07-22':
            assert fresh[0]['kind']=='HIGH'
            assert fresh[0]['occurred_at']==expected['confirmed_high_occurrence']
            assert fresh[0]['confirmed_at']==expected['confirmed_high_confirmation']
        diagnostic = dict(schema_version='mr2-source-preflight-diagnostic/0.1', status='BLOCKED',
            m_r2_accepted=False, code='2884', analysis_date=day,
            purpose='RESEARCH_SOURCE_PREFLIGHT_ONLY_NOT_A_COMPLETED_EVENT_DIARY',
            source_contract_validated=True, price_basis_id=core['context']['price_basis_id'],
            source_id=core['context']['source_id'], source_response_sha256=receipt['response_sha256'],
            historical_available_at='UNKNOWN', full_calendar_completeness='UNKNOWN',
            corporate_action_type='UNKNOWN', basis_break_dates=core['data_gaps']['basis_resets'],
            graph_result=core, newly_confirmed_original_pivots=fresh,
            requested_market_date=day, market_observation_date=None,
            markets={m:dict(status='BLOCKED', index=None, advancing=None, declining=None,
                           historical_available_at='UNKNOWN',
                           reason='DATE_SPECIFIC_ORIGINAL_AND_ACCESS_SCOPE_NOT_CONFIRMED')
                     for m in ('TWSE','TPEX')},
            followup=dict(status='UNKNOWN', window=None, reason='NOT_EXECUTED_SOURCE_PREFLIGHT_BLOCKED'),
            all_market_success_rate=None, all_market_failure_rate=None, real_net_performance=None,
            data_qualified=False, execution_model_qualified=False, historical_signal_eligible=False,
            policy_authorized=False, live_execution_authorized=False,
            primary_pressure_id=core['comparison']['primary_pressure_id'])
        key='mr2-blocked-2884-'+day
        record = journal.save(key, diagnostic)
        assert journal.read(key)==record and record['value']==diagnostic
        public_days.append(dict(code='2884', analysis_date=day, status='BLOCKED',
            source_contract_validated=True, core_version=core['schema_version'],
            source_records=core['source_records'], original_basis_break_dates=core['data_gaps']['basis_resets'],
            newly_confirmed_event_count=len(fresh),
            event_types=['CONFIRMED_HIGH_PIVOT' if p['kind']=='HIGH' else 'CONFIRMED_LOW_PIVOT' for p in fresh],
            original_event_ids_and_times_preserved=True,
            occurred_at=[p['occurred_at'] for p in fresh], confirmed_at=[p['confirmed_at'] for p in fresh],
            first_observed_at=[p['first_observed_at'] for p in fresh],
            market_observation_date=None, markets_joined=False, followup_status='UNKNOWN',
            policy_authorized=False, live_execution_authorized=False,
            primary_pressure_id=core['comparison']['primary_pressure_id'],
            existing_journal_save_read_equal=True))
    result = dict(schema='mr2-public-preflight/0.1', status='BLOCKED', m_r2_accepted=False,
        actual_joined_real_market_days=0, real_stock_diagnostics=public_days,
        market_quote_download_requests=0, finmind_download_requests=0,
        library_originals='NOT_OBTAINED_NOT_READ',
        case_2408='BLOCKED_NO_AUTHENTICATED_ORIGINAL_IN_SCOPED_SOURCE_INTAKE',
        independent_market_samples=0, all_market_success_rate=None, all_market_failure_rate=None,
        real_net_performance=None, historical_common_stock_universe='UNKNOWN',
        product_tests_executed=0, regressions_executed=0,
        note='Stock-only source preflight and Journal readback assertions are not M-R2 acceptance tests')
    with(HERE/'actual-preflight.json').open('x') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__=='__main__': main()
