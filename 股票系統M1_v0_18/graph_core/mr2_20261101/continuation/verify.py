"""Save bounded actuals for the same M-R2 continuation; no HTTP/graph replay."""
import hashlib
import json
from pathlib import Path
from graph_core.event_diary import build, public_summary
from graph_core.finmind_adapter import _validate
from graph_core.finmind_run import _parse
from rotation_research.store import Journal
from .fixtures import frozen, request_for, HERE


def write_new(path,value):
    with path.open('x') as stream:stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def main():
    local=Path('/workspace/twstockai-local-data');private=local/'mr2-20261101/continuation'
    req=json.loads((private/'research-input.json').read_text())
    raw=(local/'m2-3-finmind-20261030/response.json').read_bytes()
    receipt=json.loads((local/'m2-3-finmind-20261030/acquisition.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==receipt['response_sha256']
    response=_parse(raw);journal=Journal(local/'mr2-20261101/journal');entries=[];records=[]
    expected=json.loads((HERE/'expected.json').read_text())
    for index,day in enumerate(expected['joined_research_dates']):
        original=json.loads((local/f'm2-3-finmind-final-20261030/input-{day}.json').read_text())
        assert _validate(response,original['request'])==req['snapshots'][index]['input']
        record=journal.read('mr2-diary-research-2884-'+day.replace('-','')+'-v01')
        result=record['value'];assert result==build(req,as_of=day)
        for snapshot,row in zip(req['snapshots'],result['daily_entries']):
            assert row['original_graph_result']==snapshot['result']
            for market,m in row['markets'].items():
                original_market=next(v for v in req['market_summaries'] if v['date']==row['analysis_date'] and v['market']==market)
                assert m==original_market
                assert not m['provenance']['original_read_by_codex']
                assert m['provenance']['official_reverification']=='NOT_PERFORMED'
        entries.append(public_summary(result));records.append(result)
    assert records[0]['daily_entries'][0]==records[1]['daily_entries'][0]
    assert [len(row['events']) for row in records[-1]['daily_entries']]==[0,1]
    pivot=records[-1]['daily_entries'][1]['events'][0]
    assert {key:pivot[key] for key in expected['confirmed_high']}==expected['confirmed_high']
    assert records[-1]['daily_entries'][1]['initial_followup'][0]['status']=='IMMATURE'
    assert all(v is False for v in records[-1]['qualification'].values())
    real=dict(status='PARTIAL',limited_research_connection_executed=True,
        original_stock_response_read_by_codex_this_round=True,stock_retained_response_sha_matched=True,
        original_market_reports_read_by_codex=False,reported_market_report_sha_claims_independently_verified=False,
        market_input_role='DIRECTOR_READBACK_RESEARCH_SUMMARY',market_summary_values_published=False,
        historical_available_at='UNKNOWN',strict_common_stock_universe='UNKNOWN',redistribution_permission='UNKNOWN',
        daily_prefix_preserved=True,original_graph_and_market_values_preserved=True,
        journal_records_saved_and_read_back=2,summaries=entries,
        actual_market_joins_with_reported_summary=2,official_market_revalidation_passes=0,
        library_originals='NOT_OBTAINED_NOT_READ',case_2408='BLOCKED_ORIGINAL_NOT_OBTAINED',network_quote_requests=0)
    write_new(HERE/'real-actual-final-summary.json',real)
    f=frozen();synthetic=[]
    for case in f['cases']:
        result=build(request_for(case['variant'],no_window=case.get('no_window',False)),as_of=case['as_of'])
        actual=next(v for v in result['followup_updates'] if v['event_key']==f['origin_event_key'])
        assert actual['status']==case['status'] and actual['known_failure'] is case['known_failure']
        synthetic.append(dict(id=case['id'],expected_status=case['status'],actual=actual,matched=True))
    write_new(HERE/'synthetic-actual.json',dict(kind='SYNTHETIC_ONLY_NOT_MARKET_PERFORMANCE',cases=synthetic))
    project=HERE.parents[2]
    files=['graph_core/event_diary.py','graph_core/event_diary_run.py','graph_core/core.py','rotation_research/store.py']
    versions={p:hashlib.sha256((project/p).read_bytes()).hexdigest() for p in files}
    write_new(HERE/'source-versions.json',versions)
    write_new(private/'source-readback-receipt.json',dict(stock_response_sha256=receipt['response_sha256'],
        research_input_sha256=hashlib.sha256((private/'research-input.json').read_bytes()).hexdigest(),source_versions=versions,
        market_report_sha_role='REPORTED_ONLY_NOT_INDEPENDENTLY_READ_BACK'))
    print('PARTIAL: two real research-summary dates joined; original graphs/prefix and markets preserved; nine synthetic outcomes matched')


if __name__=='__main__':main()
