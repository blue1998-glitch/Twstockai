"""Targeted M-R2 source roles, causal rows, outcomes and existing Journal."""
from copy import deepcopy
from decimal import getcontext, setcontext, ROUND_FLOOR, Inexact
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from graph_core.core import fingerprint
from graph_core.event_diary import build, public_summary, DiaryError, _market
from graph_core.event_diary_run import run
from rotation_research.store import Journal
from .fixtures import frozen, request_for, HERE


class DiaryTests(unittest.TestCase):
    def test_frozen_followup_oracles(self):
        f=frozen(); outcomes=[]
        for case in f['cases']:
            with self.subTest(case=case['id']):
                req=request_for(case['variant'],no_window=case.get('no_window',False))
                result=build(req,as_of=case['as_of'])
                target=next(v for v in result['followup_updates'] if v['event_key']==f['origin_event_key'])
                self.assertEqual(target['status'],case['status'])
                self.assertIs(target['known_failure'],case['known_failure'])
                outcomes.append(dict(id=case['id'],status=target['status'],known_failure=target['known_failure']))
        self.assertEqual(len(outcomes),9)

    def test_original_events_times_and_graphs_preserved(self):
        req=request_for(); result=build(req,as_of=frozen()['observation_dates'][-1])
        for snapshot, row in zip(req['snapshots'],result['daily_entries']):
            self.assertEqual(snapshot['result'],row['original_graph_result'])
            for e in row['events']:
                if e['kind']=='PIVOT':
                    p=next(p for p in snapshot['result']['pivots'] if p['id']==e['original_event_id'])
                    self.assertEqual(p,e['original_event'])
                    self.assertEqual(e['confirmed_at'],row['analysis_date'])
                else:
                    box=next(b for b in snapshot['result']['boxes'] if b['id']==e['origin_object_id'])
                    self.assertEqual(e['original_event'],box['path']['events'][e['origin_index']])
                    self.assertIsNone(e['original_event_id']);self.assertIsNone(e['confirmed_at'])
        self.assertTrue(result['daily_entries'][0]['events'])

    def test_future_prefix_and_daily_rows_immutable(self):
        req=request_for(); day=frozen()['observation_dates'][0]
        early=build(req,as_of=day);later=build(req,as_of=frozen()['observation_dates'][-1])
        self.assertEqual(early['daily_entries'],later['daily_entries'][:1])
        changed=deepcopy(req)
        for s in changed['snapshots']:
            for row in s['input']['bars']:
                if row['date']>day:row.update(high='NaN',close='INVALID_FUTURE')
            if s['result']['as_of']>day:s['result']['pivots']=[]
        for m in changed['market_summaries']:
            if m['date']>day:m['values']={}
        self.assertEqual(early,build(changed,as_of=day))
        self.assertNotEqual(early['followup_updates'],later['followup_updates'])

    def test_missing_dates_fields_unknown_zero_and_source_roles(self):
        base=request_for();day=frozen()['observation_dates'][0]
        for mutation in ('date','missing-market','field','unknown-count','role','claim','hash','time','universe','permission'):
            req=deepcopy(base);m=req['market_summaries'][0]
            if mutation=='date':m['date']='2020-01-29'
            elif mutation=='missing-market':req['market_summaries'].pop(0)
            elif mutation=='field':m['values'].pop('flat')
            elif mutation=='unknown-count':m['values']['up']=None
            elif mutation=='role':m['provenance']['role']='VERIFIED_OFFICIAL'
            elif mutation=='claim':m['provenance']['original_read_by_codex']=True
            elif mutation=='hash':m['provenance']['reported_original_sha256']='UNKNOWN'
            elif mutation=='time':m['provenance']['received_at']='UNKNOWN'
            elif mutation=='universe':m['provenance']['strict_common_stock_universe']='VERIFIED'
            else:m['provenance']['redistribution_permission']='GRANTED'
            with self.subTest(mutation=mutation),self.assertRaises((DiaryError,ValueError)):
                build(req,as_of=day)
        result=build(base,as_of=day)
        self.assertEqual(result['daily_entries'][0]['markets']['TWSE']['values']['untraded'],0)
        self.assertFalse(result['qualification']['historical_signal_eligible'])
        # Exercise the director-claim branch using wholly synthetic numbers.
        claim=deepcopy(base['market_summaries'][0]);claim['provenance']['role']='DIRECTOR_READBACK_RESEARCH_SUMMARY'
        claim['provenance']['source_url']='https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date='+day.replace('-','')+'&type=MS&response=html'
        self.assertFalse(_market(claim,day=day,market='TWSE',synthetic=False)['provenance']['original_read_by_codex'])
        for url in ('https://example.invalid/wrong','https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=19990101&type=MS'):
            wrong=deepcopy(claim);wrong['provenance']['source_url']=url
            with self.assertRaisesRegex(DiaryError,'REPORTED_SOURCE_URL_DATE_OR_MARKET'):
                _market(wrong,day=day,market='TWSE',synthetic=False)

    def test_source_basis_and_f01_corruption_refused(self):
        for mutation in ('prefix','basis','fingerprint','f01-box','f01-ref','relabel'):
            req=request_for('basis-break');last=req['snapshots'][-1];r=last['result']
            if mutation=='prefix':last['input']['bars'][0]['volume_shares_scaled']='900'
            elif mutation=='basis':last['input']['context']['price_basis_id']='OTHER'
            elif mutation=='fingerprint':r['source_records']=0
            elif mutation=='f01-box':
                b=next(b for b in r['boxes'] if not b['usable_at_anchor']);b['pressure_distance_fraction']='0'
                r['result_id']=fingerprint({k:v for k,v in r.items() if k!='result_id'})
            elif mutation=='f01-ref':
                p=next(p for p in r['reference_candidates'] if p['path']['last_relation']=='NOT_COMPARABLE_AFTER_GAP');p['distance_to_anchor']='0'
                r['result_id']=fingerprint({k:v for k,v in r.items() if k!='result_id'})
            else:last['stock_source_role']='RETAINED_FINMIND_LOCAL_INTAKE'
            with self.subTest(mutation=mutation),self.assertRaises(DiaryError):build(req,as_of=r['as_of'])

    def test_later_failure_not_backfilled_and_known_failure_survives_gap(self):
        f=frozen();req=request_for('failure-then-break')
        first=build(req,as_of=f['observation_dates'][0]);early=build(req,as_of=f['observation_dates'][2]);stopped=build(req,as_of=f['observation_dates'][3])
        target=lambda result:next(v for v in result['followup_updates'] if v['event_key']==f['origin_event_key'])
        self.assertIs(target(first)['known_failure'],False)
        self.assertEqual(target(early)['status'],'KNOWN_EARLY_FAILURE')
        self.assertEqual(target(stopped)['status'],'UNKNOWN');self.assertTrue(target(stopped)['known_failure'])
        self.assertTrue(target(stopped)['original_failure_events'])
        self.assertEqual(first['daily_entries'][0],stopped['daily_entries'][0])

    def test_windows_require_source_no_hidden_policy_or_success(self):
        req=request_for();day=frozen()['observation_dates'][-1]
        for key,value in [('source_id',None),('purpose','BEST_STRATEGY'),('dates',[])]:
            changed=deepcopy(req);changed['followup_windows'][0][key]=value
            with self.subTest(key=key),self.assertRaises(DiaryError):build(changed,as_of=day)
        no_failure=build(request_for('no-failure'),as_of=day)
        self.assertIsNone(no_failure['all_market_success_rate']);self.assertIsNone(no_failure['real_net_performance'])
        self.assertTrue(all(v is False for v in no_failure['qualification'].values()))
        req['policy_authorized']=True
        with self.assertRaises(DiaryError):build(req,as_of=day)

    def test_gap_metadata_binding_and_failure_without_window(self):
        req=request_for('basis-break');day=frozen()['observation_dates'][-1]
        req['snapshots'][-1]['input']['basis_break_dates']=[]
        with self.assertRaisesRegex(DiaryError,'CORE_SOURCE_BINDING'):build(req,as_of=day)
        req=request_for(no_window=True);day=frozen()['observation_dates'][2]
        result=build(req,as_of=day)
        failed=[e for row in result['daily_entries'] for e in row['events']
                if e['original_event_type'] in ('FAILED_UP_RETURN_IN_RANGE','FAILED_UP_AND_CROSSED_BELOW_RANGE')]
        self.assertTrue(failed)
        by_id={u['event_key']:u for u in result['followup_updates']}
        for event in failed:
            self.assertTrue(by_id[event['event_key']]['known_failure'])
            self.assertEqual(by_id[event['event_key']]['status'],'UNKNOWN')
            self.assertEqual(by_id[event['event_key']]['reason'],'KNOWN_FAILURE_WITH_UNSPECIFIED_WINDOW')

    def test_pure_no_io_input_and_numeric_context_unchanged(self):
        req=request_for();before=deepcopy(req);day=frozen()['observation_dates'][0];expected=build(req,as_of=day)
        old=getcontext().copy()
        try:
            ctx=getcontext();ctx.prec=3;ctx.rounding=ROUND_FLOOR;ctx.traps[Inexact]=True
            state=repr(ctx),dict(ctx.flags),dict(ctx.traps)
            with patch('builtins.open',side_effect=AssertionError('IO')),patch('socket.socket',side_effect=AssertionError('network')), \
                    patch('graph_core.core.analyze',side_effect=AssertionError('graph recomputation')):
                self.assertEqual(build(req,as_of=day),expected)
            self.assertEqual((repr(ctx),dict(ctx.flags),dict(ctx.traps)),state)
        finally:setcontext(old)
        self.assertEqual(req,before)

    def test_journal_same_content_conflict_read_and_local_runner(self):
        req=request_for();day=frozen()['observation_dates'][0]
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'request.json';path.write_text(json.dumps(req));journal_dir=Path(temp)/'journal'
            with patch('socket.socket',side_effect=AssertionError('network')):
                out=run(path,journal_dir,as_of=day,key='sample')
                saved=(journal_dir/'sample.json').read_bytes();mtime=(journal_dir/'sample.json').stat().st_mtime_ns
                self.assertEqual(run(path,journal_dir,as_of=day,key='sample'),out)
            self.assertEqual((journal_dir/'sample.json').stat().st_mtime_ns,mtime)
            changed=deepcopy(req);changed['market_summaries'][0]['values']['up']+=1;path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError,'Identity conflict'):run(path,journal_dir,as_of=day,key='sample')
            self.assertEqual((journal_dir/'sample.json').read_bytes(),saved)
            with patch('graph_core.event_diary.build',side_effect=AssertionError('recompute')):
                self.assertEqual(Journal(journal_dir).read('sample')['value']['as_of'],day)

    def test_public_allowlist_and_frozen_sources(self):
        req=request_for();result=build(req,as_of=frozen()['observation_dates'][0]);text=json.dumps(public_summary(result))
        for token in ('index_close','reported_original_sha256','original_event_id','pressure_distance_fraction'):
            self.assertNotIn(token,text)
        baseline=json.loads((HERE/'baseline.json').read_text());root=HERE.parents[3]
        for p in baseline['protected']:
            self.assertEqual(hashlib.sha256((root/p['path']).read_bytes()).hexdigest(),p['sha256'])
        for path,digest in baseline['frozen'].items():self.assertEqual(hashlib.sha256((HERE/path).read_bytes()).hexdigest(),digest)
        f=json.loads((HERE/'synthetic-frozen.json').read_text())
        self.assertEqual(hashlib.sha256((HERE/'synthetic-input-expected.json').read_bytes()).hexdigest(),f['sha256'])

    def test_synthetic_records_never_claim_a_real_connection(self):
        result=build(request_for(),as_of=frozen()['observation_dates'][0])
        self.assertEqual(result['real_research_connection'],'NOT_APPLICABLE_SYNTHETIC')
        self.assertTrue(result['synthetic_test_only'])
        self.assertEqual(public_summary(result)['real_research_connection'],'NOT_APPLICABLE_SYNTHETIC')
        self.assertTrue(all(v is False for v in result['qualification'].values()))


if __name__=='__main__':unittest.main()
