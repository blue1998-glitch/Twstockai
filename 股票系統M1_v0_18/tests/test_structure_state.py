"""P0-3 independent oracles. Synthetic prices never stand for market samples."""
from copy import deepcopy
from decimal import localcontext
from pathlib import Path
import json
import unittest
from unittest.mock import patch
import subprocess
import sys
import tempfile

from graph_core.core import fingerprint
from reaction_facts.core import BINDING
from structure_state.core import evaluate
from structure_state.source import prepare

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    """Explicit engineering-only sequence, no ticker/date/threshold in core."""
    values = [('9','10','6','9'), ('9','12','8','11'), ('10','10.5','7','9.5'),
              ('10','10.5','9','10.5'), ('10.5','10.6','10','10.6'),
              ('9','9','8','8'), ('8','8','6','6'), ('6','6','5.9','5.9'),
              ('6','11','6','11')]
    bars = [dict(date=f'2000-01-{i+1:02}', open=o, high=h, low=l, close=c,
                 volume_shares_scaled=str(100-i*10)) for i,(o,h,l,c) in enumerate(values)]
    c = dict(code='ENGINEERING_NOT_MARKET', source_id='engineering-source', price_basis_id='engineering-raw',
             source_frame_id='engineering-frame', source_prefix_fingerprint=fingerprint(bars),
             volume_unit='SHARES_REPORTED', price_mode='RAW_CANDIDATE', adjustment_version='NOT_APPLICABLE_RAW')
    refs = []; roles = {}
    for name,index,field in [('PULLBACK_HIGH',2,'high'),('ORIGINAL_BOX_FLOOR',0,'low'),
                              ('ORIGINAL_BOX_UPPER',0,'high'),('SHALLOW_OBSERVATION',2,'close')]:
        row = bars[index]; id_ = 'ref-'+name
        refs.append(dict(id=id_, binding={k:c[k] for k in BINDING},price=row[field],
                         origin_id=fingerprint(row),source_kind='BAR_FIELD',source_field=field,
                         occurred_at=row['date'],known_on=row['date'],selected_at='2030-01-01T00:00:00+00:00',
                         historical_signal_eligible=False,qualification='EXPLICIT_RESEARCH_QUERY'))
        roles[name]=dict(role=name,reference_id=id_,qualification='ENGINEERING_FIXTURE',
                         known_on=row['date'],valid_from=row['date'],valid_until=None,invalidated_on=None,
                         selected_at='2030-01-01T00:00:00+00:00',evidence={'engineering_only':True,'source_field':field})
    p=dict(schema_version='reaction-facts-input/0.1',context=c,bars=bars,
           macd=[dict(dif='-0.1',dea='0.1',histogram='-0.4',reason='ENGINEERING_SAVED_INPUT') for _ in bars],references=refs,
           known_gap_dates=[],basis_break_dates=[])
    s=dict(schema_version='p03-explicit-roles/0.1',scenario_id='engineering-only',binding=deepcopy(c),roles=roles,
           post_breakout_return=dict(qualification='ENGINEERING_FIXTURE',context_start_on='2000-01-01',breakout_on='2000-01-02',return_on='2000-01-03',known_on='2000-01-03',evidence={'engineering_only':True}))
    return p,s


def rebind(p,s):
    c=p['context'];c['source_prefix_fingerprint']=fingerprint(p['bars']);s['binding']=deepcopy(c)
    for r in p['references']:
        r['binding']={k:c[k] for k in BINDING}
        bar=next((b for b in p['bars'] if b['date']==r['occurred_at']),None)
        if bar:r['origin_id']=fingerprint(bar);r['price']=bar[r['source_field']]
    return p,s


class StructureState(unittest.TestCase):
    def setUp(self):self.p,self.s=fixture()
    def run_case(self,day='2000-01-09'):return evaluate(self.p,self.s,as_of=day)
    def states(self):return [r['state'] for r in self.run_case()['records']]

    def test_exact_three_states_and_equal_boundaries(self):
        r=self.run_case();self.assertEqual(self.states()[2:],['CONSOLIDATING','CONSOLIDATING','STRENGTHENING','CONSOLIDATING','CONSOLIDATING','WEAKENING','STRENGTHENING'])
        self.assertIn('PULLBACK_HIGH',r['records'][3]['equal_boundaries'])
        self.assertIn('ORIGINAL_BOX_FLOOR',r['records'][6]['equal_boundaries'])

    def test_shallow_observation_break_is_not_weakening(self):
        row=self.run_case()['records'][5]
        self.assertEqual(row['price_facts']['SHALLOW_OBSERVATION']['close']['relation'],'BELOW')
        self.assertEqual(row['state'],'CONSOLIDATING')

    def test_low_volume_and_negative_macd_do_not_veto_strict_cross(self):
        row=self.run_case()['records'][4]
        self.assertEqual(row['state'],'STRENGTHENING')
        self.assertTrue(any('VOLUME_BELOW' in x for x in row['evidence']['opposing']))
        self.assertIn('MACD_HISTOGRAM_NEGATIVE_DESCRIPTION_ONLY',row['evidence']['opposing'])

    def test_missing_volume_macd_are_missing_support_not_price_failure(self):
        self.p['bars'][4]['volume_shares_scaled']=None;self.p['macd'][4]=None;rebind(self.p,self.s)
        row=self.run_case()['records'][4];self.assertEqual(row['state'],'STRENGTHENING')
        self.assertIn('MACD_HISTOGRAM_UNAVAILABLE',row['evidence']['missing'])

    def test_missing_role_not_forced_into_three_states(self):
        del self.s['roles']['ORIGINAL_BOX_FLOOR']
        self.assertEqual(self.run_case()['records'][-1]['state'],'INSUFFICIENT')

    def test_wrong_semantic_role_refused(self):
        self.s['roles']['PULLBACK_HIGH']['role']='LATEST_PIVOT'
        self.assertIn('WRONG_SEMANTIC_ROLE:PULLBACK_HIGH',self.run_case()['records'][-1]['reasons'])

    def test_wrong_source_field_not_relabelled_high(self):
        self.p['references'][0]['source_field']='close';rebind(self.p,self.s)
        self.assertIn('WRONG_SOURCE_FIELD:PULLBACK_HIGH',self.run_case()['records'][-1]['reasons'])

    def test_role_without_evidence_unqualified(self):
        self.s['roles']['PULLBACK_HIGH']['evidence']=None
        self.assertEqual(self.run_case()['records'][-1]['state'],'INSUFFICIENT')

    def test_unknown_selection_time_refused(self):
        self.s['roles']['PULLBACK_HIGH']['selected_at']=None
        self.assertIn('UNKNOWN_ROLE_SELECTION_TIME:PULLBACK_HIGH',self.run_case()['records'][-1]['reasons'])

    def test_cross_basis_scenario_no_fallback(self):
        self.s['binding']['price_basis_id']='other-adjusted-basis'
        self.assertIn('SCENARIO_SOURCE_BASIS_VERSION_MISMATCH',self.run_case()['records'][-1]['reasons'])

    def test_adjustment_version_and_price_mode_must_match(self):
        for key in ['adjustment_version','price_mode']:
            p,s=fixture();s['binding'][key]='wrong'
            self.assertEqual(evaluate(p,s,as_of='2000-01-09')['records'][-1]['state'],'INSUFFICIENT')

    def test_role_and_event_identity_separates_adjustment_versions(self):
        self.p['context'].update(price_mode='ADJUSTED_CANDIDATE',adjustment_version='explicit-version-1');rebind(self.p,self.s)
        a=self.run_case();self.p['context']['adjustment_version']='explicit-version-2';rebind(self.p,self.s);b=self.run_case()
        self.assertNotEqual(a['reference_catalog'][0]['role_id'],b['reference_catalog'][0]['role_id'])
        self.assertEqual(a['records'][-1]['state'],b['records'][-1]['state'])

    def test_wrong_reference_binding_source_refused(self):
        self.p['references'][0]['binding']['source_id']='different'
        self.assertEqual(self.run_case()['source_qualification'],'INPUT_REFUSED')

    def test_role_value_not_available_until_semantic_known_date(self):
        self.s['roles']['PULLBACK_HIGH'].update(known_on='2000-01-05',valid_from='2000-01-05')
        r=self.run_case('2000-01-04');self.assertIsNone(r['reference_catalog'][0]['source_reference']['price'])
        self.assertEqual(r['records'][-1]['state'],'INSUFFICIENT')

    def test_expired_and_invalidated_roles(self):
        for key in ['valid_until','invalidated_on']:
            p,s=fixture();s['roles']['PULLBACK_HIGH'][key]='2000-01-05'
            r=evaluate(p,s,as_of='2000-01-09');self.assertEqual(r['records'][-1]['state'],'INSUFFICIENT')
            self.assertEqual(r['records'][3]['state'],'CONSOLIDATING')

    def test_missing_price_breaks_structure_until_explicit_new_context(self):
        self.p['bars'][5]['close']=None;rebind(self.p,self.s)
        r=self.run_case();self.assertTrue(all(x['state']=='INSUFFICIENT' for x in r['records'][5:]))
        self.assertTrue(any(e['to_state']=='STRENGTHENING' for e in r['events']))

    def test_explicit_calendar_gap_is_not_forward_filled(self):
        self.p['known_gap_dates']=['2000-01-06'];r=self.run_case()
        self.assertTrue(all(x['state']=='INSUFFICIENT' for x in r['records'][5:]))
        self.assertEqual(len(r['records']),len(self.p['bars']))

    def test_basis_interruption_does_not_reuse_old_roles(self):
        self.p['basis_break_dates']=['2000-01-06'];r=self.run_case()
        self.assertTrue(all(x['state']=='INSUFFICIENT' for x in r['records'][5:]))

    def test_ref_geometry_contradiction(self):
        # Explicit low source above the later pullback high: valid OHLC inputs,
        # contradictory role geometry, rather than a fabricated daily candle.
        self.p['bars'][0].update(open='15',high='16',low='14',close='15')
        rebind(self.p,self.s)
        self.assertIn('CONTRADICTORY_REFERENCE_GEOMETRY',self.run_case()['records'][-1]['reasons'])

    def test_original_breakout_must_be_supported(self):
        self.s['post_breakout_return']['breakout_on']='2000-01-01'
        self.assertEqual(self.run_case()['records'][-1]['state'],'INSUFFICIENT')

    def test_return_must_be_after_breakout(self):
        self.s['post_breakout_return']['return_on']='2000-01-02'
        self.assertEqual(self.run_case()['records'][-1]['state'],'INSUFFICIENT')

    def test_future_append_and_change_do_not_rewrite_any_prior_state_or_event(self):
        before=self.run_case('2000-01-05')
        self.p['bars'].append(dict(date='2000-01-10',open='999',high='1000',low='1',close='900',volume_shares_scaled='999'))
        self.p['macd'].append(dict(dif='1000',dea='-1000',histogram='4000'))
        self.p['bars'][7].update(open='80',high='90',low='70',close='85')
        rebind(self.p,self.s)
        after=self.run_case('2000-01-05')
        self.assertEqual(before['records'],after['records']);self.assertEqual(before['events'],after['events'])

    def test_even_invalid_future_ohlc_not_read_at_old_cutoff(self):
        before=self.run_case('2000-01-05');self.p['bars'][-1]['low']='1000';rebind(self.p,self.s)
        after=self.run_case('2000-01-05');self.assertEqual(before['records'],after['records'])

    def test_full_later_evaluation_preserves_prefix_records_and_event_ids(self):
        old=self.run_case('2000-01-05');later=self.run_case()
        self.assertEqual(old['records'],later['records'][:5])
        self.assertEqual(old['events'],[e for e in later['events'] if e['date']<='2000-01-05'])

    def test_return_and_restrengthening_preserve_breakout_and_weakness(self):
        r=self.run_case();events=r['events']
        self.assertEqual(len([x for x in events if x['kind']=='ORIGINAL_BREAKOUT_CLOSE']),1)
        self.assertTrue(any(x['to_state']=='WEAKENING' for x in events))
        self.assertEqual(r['records'][-1]['state'],'STRENGTHENING')

    def test_daily_both_wicks_outside_do_not_invent_intraday_order(self):
        self.p['bars'][5].update(high='20',low='1');rebind(self.p,self.s)
        row=self.run_case()['records'][5];self.assertEqual(row['state'],'CONSOLIDATING')
        self.assertEqual(row['intraday_sequence'],'UNKNOWN_FROM_DAILY_OHLC')

    def test_decimal_precision_independent_and_strict(self):
        self.p['bars'][4].update(close='10.500000000000000000000000000000001',high='10.500000000000000000000000000000001')
        rebind(self.p,self.s)
        with localcontext() as ctx:
            ctx.prec=3;row=self.run_case()['records'][4]
        self.assertEqual(row['state'],'STRENGTHENING')
        self.assertEqual(row['price_facts']['PULLBACK_HIGH']['close']['delta'],'0.000000000000000000000000000000001')

    def test_later_selection_never_historical_or_trade_eligible(self):
        r=self.run_case();self.assertFalse(r['historical_signal_eligible']);self.assertFalse(r['execution_qualified'])
        self.assertIsNone(r['primary_pressure_id']);self.assertIsNone(r['valuation']);self.assertFalse(r['policy_authorized'])
        self.assertTrue(all(not x['historical_signal_eligible'] for x in r['records']))

    def test_pure_core_has_no_file_or_network_access(self):
        with patch('builtins.open',side_effect=AssertionError('No core file IO')), patch('socket.socket',side_effect=AssertionError('No core network')):
            self.assertEqual(self.run_case()['records'][-1]['state'],'STRENGTHENING')

    def test_inputs_and_role_evidence_not_mutated(self):
        p,s=deepcopy(self.p),deepcopy(self.s);self.run_case()
        self.assertEqual(self.p,p);self.assertEqual(self.s,s)

    def test_semantic_upper_must_be_known_at_initial_breakout(self):
        self.s['roles']['ORIGINAL_BOX_UPPER'].update(known_on='2000-01-03',valid_from='2000-01-03')
        r=self.run_case();self.assertEqual(r['records'][-1]['state'],'INSUFFICIENT')
        self.assertFalse(any(e['kind']=='ORIGINAL_BREAKOUT_CLOSE' for e in r['events']))

    def test_headless_cli_readback_and_existing_result_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'input.json').write_text(json.dumps(self.p));(p/'scenario.json').write_text(json.dumps(self.s))
            command=[sys.executable,'-m','structure_state.cli','--input',str(p/'input.json'),'--scenario',str(p/'scenario.json'),'--as-of','2000-01-09','--output',str(p/'out.json')]
            run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(json.loads((p/'out.json').read_text()),self.run_case())
            (p/'out.json').write_text('existing history')
            run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0);self.assertEqual((p/'out.json').read_text(),'existing history')


class RealSourceRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'cross_scale_chart/generated/comparison-data.json').read_text())
        cls.choice=json.loads((ROOT/'structure_state/examples/retained-case.json').read_text())
    def test_real_conditional_case_matches_independent_close_oracle(self):
        p,s=prepare(self.data,self.choice);r=evaluate(p,s,as_of='2026-10-16')
        self.assertEqual([(x['date'],x['state']) for x in r['records'][-4:]], [('2026-10-13','CONSOLIDATING'),('2026-10-14','STRENGTHENING'),('2026-10-15','CONSOLIDATING'),('2026-10-16','STRENGTHENING')])
        self.assertEqual(r['source_qualification'],'EXPLICIT_RESEARCH_ROLES_NOT_FORMAL_BOX')
        self.assertFalse(any(x['state']=='WEAKENING' for x in r['records']))
        self.assertTrue(any(x['kind']=='ORIGINAL_BREAKOUT_CLOSE' and x['date']=='2026-10-12' for x in r['events']))
    def test_candidate_never_silently_promoted_to_human_box(self):
        q=deepcopy(self.choice);q['roles']['ORIGINAL_BOX_FLOOR']['qualification']='HUMAN_CONFIRMED'
        with self.assertRaises(ValueError):prepare(self.data,q)
    def test_wrong_artifact_refused(self):
        q=deepcopy(self.choice);q['comparison_artifact_id']='wrong'
        with self.assertRaises(ValueError):prepare(self.data,q)
    def test_arbitrary_recent_high_outside_pullback_phase_refused(self):
        q=deepcopy(self.choice);q['references'][0]['date']='2026-10-14'
        with self.assertRaises(ValueError):prepare(self.data,q)
    def test_unavailable_phase_members_refused(self):
        q=deepcopy(self.choice);q['roles']['PULLBACK_HIGH']['evidence']['source_member_dates']=['2026-10-10']
        with self.assertRaises(ValueError):prepare(self.data,q)
    def test_wrong_original_k_witness_refused(self):
        q=deepcopy(self.choice);q['roles']['ORIGINAL_BOX_FLOOR']['evidence']['source_k_dates']=['2026-10-13']
        with self.assertRaises(ValueError):prepare(self.data,q)
    def test_context_cannot_drop_earlier_box_records(self):
        q=deepcopy(self.choice);q['post_breakout_return']['context_start_on']='2026-10-01'
        with self.assertRaises(ValueError):prepare(self.data,q)


if __name__=='__main__':unittest.main()
