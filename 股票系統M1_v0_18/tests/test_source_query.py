"""Source query acceptance: saved real sources, explicit rejection and causality."""
from copy import deepcopy
from datetime import datetime
from decimal import localcontext
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from graph_core.core import fingerprint
from graph_diagnostics.source_query import inspect_sources, binding_for, QUERY_VERSION
from graph_diagnostics.source_query_adapter import inspect_packet

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'docs/visual-discussion/20261020_source_query_contract'


def saved_fixture():
    data = json.loads((ROOT/'cross_scale_chart/generated/comparison-data.json').read_text())
    audit = json.loads((REVIEW/'path-audit.json').read_text())
    route = audit['explicit_preceding_research_route']
    query = dict(schema_version=QUERY_VERSION, binding=binding_for(data['core']),
                 pivot_ids=[route['from_id'], route['turns'][-2]['id'], route['to_id']],
                 path_requests=[{k:route[k] for k in ('from_id', 'to_id')}], selected_at='2026-10-20T12:00:00+08:00')
    return data, audit, query


def resign(core):
    core['result_id'] = fingerprint({k:v for k,v in core.items() if k != 'result_id'})
    return core


def requery(core, query):
    q = deepcopy(query); q['binding'] = binding_for(core); return q


class SourceQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.audit, cls.query = saved_fixture()
        cls.core = cls.data['core']; cls.report = inspect_packet(cls.data, cls.query)

    def test_real_a_all_three_boxes_exact_original_sources_and_ordinals(self):
        previous = json.loads((ROOT.parent/'docs/visual-discussion/20261020_structure_membership_work_review/source-membership-audit.json').read_text())
        source = self.report['requested_sources'][0]
        self.assertEqual(source['pivot_id'], previous['queried_original_pivot']['id'])
        refs = source['original_box_references']; self.assertEqual([v['original_box_ordinal_1based'] for v in refs], [16,17,18])
        self.assertEqual([v['box_id'] for v in refs], [v['id'] for v in previous['pivot_source_box_memberships']])
        originals = {b['id']:b for b in self.core['boxes']}
        for ref in refs:
            b = originals[ref['box_id']]; returned = self.report['boxes'][b['id']]
            for key, value in returned.items(): self.assertEqual(value, b[key])
            self.assertEqual(b['source_turn_ids'][ref['source_turn_position_0based']], source['pivot_id'])
            self.assertEqual(ref['not_before_original_confirmations'], max(b['confirmed_at'], previous['queried_original_pivot']['confirmed_at']))
        prices = [self.report['pivots'][i]['price'] for ref in refs for i in self.report['boxes'][ref['box_id']]['source_turn_ids']]
        self.assertIn('40.25', prices)  # Kept original pre-month source, not formal whole membership.
        self.assertIsNone(self.report['formal_structure_membership'])

    def test_real_nine_turn_route_all_fields_and_119_sequence_context(self):
        path = self.report['paths'][0]; expected = self.audit['explicit_preceding_research_route']
        route = [self.report['pivots'][i] for i in path['turn_ids']]
        self.assertEqual(route, expected['turns']); self.assertEqual(path['records'], 9)
        self.assertEqual((path['sequence_records'],path['records_before'],path['records_after']), (119,33,77))
        self.assertEqual(path['not_before_original_confirmations'], max(p['confirmed_at'] for p in route))
        self.assertEqual(route[-1]['price'], '35.50'); self.assertEqual(route[-3]['price'], '34.15')
        self.assertEqual(route[3]['source_dates'], ['2023-09-08','2023-09-11'])
        # Count context is not automatic start/stop expansion.
        self.assertEqual(path['turn_ids'][0], self.query['pivot_ids'][0])

    def test_real_complete_coordinate_aliases_keep_separate_ids_confirmations(self):
        expected = self.audit['coordinate_correspondences_with_source_dates_preserved']
        for source, oracle in zip(self.report['requested_sources'][1:], expected):
            aliases = source['coordinate_correspondences']
            self.assertEqual([a['pivot_id'] for a in aliases], [oracle['original_pivot_ids'][1]])
            a = aliases[0]; p = self.report['pivots'][source['pivot_id']]; other = self.report['pivots'][a['pivot_id']]
            self.assertNotEqual(p['id'], other['id']); self.assertNotEqual(p['confirmed_at'], other['confirmed_at'])
            self.assertEqual(p['source_dates'], oracle['source_dates']); self.assertEqual(p['source_dates'], other['source_dates'])
            self.assertEqual(a['not_before_original_confirmations'], max(oracle['original_confirmations']))

    def test_all_real_pivots_reverse_index_matches_independent_box_scan(self):
        q = deepcopy(self.query); q['pivot_ids'] = [p['id'] for p in self.core['pivots']]; q['path_requests'] = []
        r = inspect_sources(self.core, q)
        for s in r['requested_sources']:
            expected = [(b['id'], b['source_turn_ids'].index(s['pivot_id'])) for b in self.core['boxes'] if s['pivot_id'] in b['source_turn_ids']]
            self.assertEqual([(b['box_id'],b['source_turn_position_0based']) for b in s['original_box_references']], expected)
        self.assertEqual(len(r['boxes']), len(self.core['boxes']))

    def test_same_price_spelling_matches_but_source_dates_or_segment_do_not(self):
        # Structural validation fixture only; altered copy is never shipped as market data.
        c = deepcopy(self.core); original = next(p for p in c['pivots'] if len(p['source_dates']) > 1)
        clones = []
        for scale, segment, dates in [('0.09', original['segment'], original['source_dates']),
                                      ('0.10', original['segment'], original['source_dates'][:1]),
                                      ('0.11', original['segment'] + 1, original['source_dates'])]:
            p = deepcopy(original); p.update(scale=scale, segment=segment, source_dates=dates, price=original['price']+'0')
            p['id'] = fingerprint({k:p[k] for k in ('kind','price','occurred_at','confirmed_at','scale','segment')})
            c['parameters']['reversals'].append(scale); c['pivots'].append(p); clones.append(p)
        resign(c); q = requery(c,self.query); q['pivot_ids'] = [original['id']];q['path_requests'] = []
        r = inspect_sources(c,q); ids = [v['pivot_id'] for v in r['requested_sources'][0]['coordinate_correspondences']]
        self.assertIn(clones[0]['id'],ids); self.assertNotIn(clones[1]['id'],ids); self.assertNotIn(clones[2]['id'],ids)

    def test_no_recursive_box_lookup_for_path_or_alias_only_sources(self):
        q = deepcopy(self.query);q['pivot_ids'] = [self.query['pivot_ids'][0]]
        r = inspect_sources(self.core,q)
        self.assertEqual(len(r['requested_sources']),1);self.assertEqual(len(r['boxes']),3)
        self.assertEqual(r['paths'][0]['records'],9)
        q['pivot_ids'] = []; r = inspect_sources(self.core,q)
        self.assertEqual(r['boxes'],{});self.assertEqual(len(r['pivots']),9)

    def test_unknown_pending_implicit_endpoint_and_reverse_paths_refused(self):
        for mutate in [lambda q:q['pivot_ids'].append('unknown-unconfirmed'),
                       lambda q:q['path_requests'][0].pop('to_id'),
                       lambda q:q.update(manual_month='not-allowed'),
                       lambda q:q['path_requests'][0].update(to_id='outside-prefix')]:
            q = deepcopy(self.query);mutate(q)
            with self.assertRaises(ValueError):inspect_sources(self.core,q)
        q = deepcopy(self.query); path = q['path_requests'][0]; path['from_id'],path['to_id'] = path['to_id'],path['from_id']
        with self.assertRaisesRegex(ValueError,'Reverse'):inspect_sources(self.core,q)

    def test_cross_scale_and_segment_refused_even_when_coordinate_matches(self):
        q = deepcopy(self.query);q['path_requests'][0]['to_id'] = self.report['requested_sources'][-1]['coordinate_correspondences'][0]['pivot_id']
        with self.assertRaisesRegex(ValueError,'Cross-scale'):inspect_sources(self.core,q)
        c = deepcopy(self.core); original = c['pivots'][-1]; other = deepcopy(original); other['segment'] += 1
        other['id'] = fingerprint({k:other[k] for k in ('kind','price','occurred_at','confirmed_at','scale','segment')})
        c['pivots'].append(other);resign(c);q = requery(c,self.query)
        q['path_requests'] = [dict(from_id=original['id'],to_id=other['id'])]
        with self.assertRaisesRegex(ValueError,'Cross-scale'):inspect_sources(c,q)

    def test_self_consistent_hash_cannot_hide_bad_pivot_box_time_or_references(self):
        mutations = [lambda c:c['pivots'][0].update(confirmed_at='2099-01-01'),
                     lambda c:c['pivots'][0].update(occurred_index=-1),
                     lambda c:c['pivots'][0].update(price='0'),
                     lambda c:c['pivots'][0]['source_dates'].reverse(),
                     lambda c:c['boxes'][0]['source_turn_ids'].append('unknown-source'),
                     lambda c:c['boxes'][0].update(formed_index=0),
                     lambda c:c['pivots'].append(deepcopy(c['pivots'][0])),
                     lambda c:c['pivots'][0].update(confirmation='UNCONFIRMED'),
                     lambda c:c['boxes'][0]['parent_ids'].append('unknown-box'),
                     lambda c:c['comparison']['pareto_frontier_ids'].append('unknown-box'),
                     lambda c:c['reference_candidates'][0].update(pivot_id='unknown-point')]
        # Reverse an actually multi-date source (first source has one date).
        mutations[3] = lambda c:next(p for p in c['pivots'] if len(p['source_dates'])>1)['source_dates'].reverse()
        for mutate in mutations:
            c = deepcopy(self.core);mutate(c);resign(c)
            with self.assertRaises(ValueError):inspect_sources(c,requery(c,self.query))

    def test_mixed_binding_and_wrong_identity_or_source_packet_refused(self):
        for key in ('result_id','source_prefix_fingerprint','context'):
            q = deepcopy(self.query);q['binding'][key] = 'different'
            with self.assertRaises(ValueError):inspect_sources(self.core,q)
        p = deepcopy(self.data);p['source']['id'] = 'other';p['artifact_id'] = fingerprint({k:v for k,v in p.items() if k!='artifact_id'})
        with self.assertRaises(ValueError):inspect_packet(p,self.query)
        p = deepcopy(self.data);p['bars'][0]['volume_shares_scaled'] = '1';p['artifact_id'] = fingerprint({k:v for k,v in p.items() if k!='artifact_id'})
        with self.assertRaises(ValueError):inspect_packet(p,self.query)
        p = deepcopy(self.data);p['core']['context']['price_basis_id'] = 'other'
        with self.assertRaises(ValueError):inspect_packet(p,self.query)

    def test_original_bar_source_dates_and_indices_verified_without_recomputation(self):
        p = deepcopy(self.data);c = p['core'];target = next(v for v in c['pivots'] if len(v['source_dates'])>1)
        target['source_dates'] = target['source_dates'][:1]
        # Keep redundant internal reference metadata coherent, so the independent
        # original-bar check (not an earlier identity check) must catch omission.
        for ref in c['reference_candidates']:
            if ref['pivot_id'] == target['id']:ref['source_dates'] = deepcopy(target['source_dates'])
        resign(c)
        p['artifact_id'] = fingerprint({k:v for k,v in p.items() if k!='artifact_id'})
        with self.assertRaisesRegex(ValueError,'source_dates'):inspect_packet(p,requery(c,self.query))
        with patch('graph_core.core.analyze',side_effect=AssertionError('No analysis')), patch('graph_core.core._pivots',side_effect=AssertionError('No pivot replay')), patch('graph_core.core._boxes',side_effect=AssertionError('No boxes')), patch('graph_diagnostics.diagnose.diagnose',side_effect=AssertionError('No diagnose')):
            self.assertEqual(inspect_packet(self.data,self.query),self.report)

    def test_explicit_original_prefix_unaffected_by_unselected_future_packet(self):
        series = {k:deepcopy(self.data[k]) for k in ['code','source','price_basis_id','bars','macd','source_gaps']}
        series.update(results=[deepcopy(self.core)],numeric_frame_ids={self.core['as_of']:self.data['source_frame_id']})
        packet = dict(schema_version='graph-recognition-chart-bundle/0.1',series=[series]);packet['artifact_id'] = fingerprint(packet)
        before = inspect_packet(packet,self.query)
        # Explicit engineering future packet, not new real OHLCV or recognition.
        row = deepcopy(series['bars'][-1]);row['date'] = '2026-10-20';series['bars'].append(row);series['macd'].append(None)
        future = deepcopy(self.core);future['as_of'] = row['date'];future['anchor']['date'] = row['date']
        future['source_records'] += 1;future['anchor']['index'] += 1;future['source_prefix_fingerprint'] = fingerprint(series['bars']);resign(future)
        series['results'].append(future);series['numeric_frame_ids'][future['as_of']] = 'engineering-future'
        packet['artifact_id'] = fingerprint({k:v for k,v in packet.items() if k!='artifact_id'})
        after = inspect_packet(packet,self.query);self.assertEqual(before,after)
        series['bars'][-1]['volume_shares_scaled'] = '999';series['macd'][-1] = dict(histogram='999')
        future['anchor']['close'] = '999';resign(future);packet['artifact_id'] = fingerprint({k:v for k,v in packet.items() if k!='artifact_id'})
        self.assertEqual(inspect_packet(packet,self.query),before)
        q = deepcopy(self.query);q['binding']['result_id'] = 'not-saved'
        with self.assertRaises(ValueError):inspect_packet(packet,q)

    def test_determinism_input_immutability_timestamp_and_qualifications(self):
        p,q = deepcopy(self.data),deepcopy(self.query)
        with localcontext() as ctx:
            ctx.prec = 3
            self.assertEqual(inspect_packet(p,q),self.report)
        self.assertEqual(p,self.data);self.assertEqual(q,self.query)
        for key in ['primary_pressure_id','formal_structure_membership','formal_merge','formal_representative','direct_successor_id','whole_pressure_clearance','historical_selection_time']:
            self.assertIsNone(self.report[key])
        self.assertFalse(self.report['historical_signal_eligible'])
        self.assertIn('SUMMARY_ONLY',self.report['source_validation']['diagnostics'])
        for stamp in [None,'2026-10-20T12:00:00']:
            q = deepcopy(self.query);q['selected_at'] = stamp
            with self.assertRaises(ValueError):inspect_sources(self.core,q)

    def test_cli_actual_timestamp_exact_json_and_conflict_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp);q = tmp/'request.json';out = tmp/'report.json';q.write_text(json.dumps(self.query))
            cmd = [sys.executable,'-m','graph_diagnostics.source_query_cli','--input',str(ROOT/'cross_scale_chart/generated/comparison-data.json'),'--query',str(q),'--output',str(out)]
            run = subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
            report = json.loads(out.read_text());self.assertEqual(report,inspect_packet(self.data,report['query']))
            self.assertIsNotNone(datetime.fromisoformat(report['query']['selected_at']).tzinfo)
            self.assertNotEqual(report['query']['selected_at'],self.query['selected_at'])
            out.write_text('original user file');run = subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0);self.assertEqual(out.read_text(),'original user file')


if __name__ == '__main__':unittest.main()
