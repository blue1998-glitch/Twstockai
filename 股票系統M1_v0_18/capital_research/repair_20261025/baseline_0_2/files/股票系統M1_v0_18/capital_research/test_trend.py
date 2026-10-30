"""Continuation research contract and shared-path synthetic account experiments."""
from copy import deepcopy
from decimal import Decimal,localcontext
import unittest
from .core import decide
from .continuity import describe_position_roles
from .trend import evaluate
from .trend_fixtures import path_fixture,PATHS,POLICIES
from .trend_replay import run_fixture


class TrendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures={n:path_fixture(n) for n in PATHS}
        cls.results={n:run_fixture(f) for n,f in cls.fixtures.items()}

    def test_all_nine_paths_and_five_policy_intents_really_execute(self):
        self.assertEqual(len(self.results),9)
        for r in self.results.values():
            self.assertEqual(set(r['policy_results']),set(POLICIES))
            self.assertTrue(all(v['status']=='COMPLETED_SYNTHETIC_SEQUENCE' for v in r['policy_results'].values()))
            self.assertIsNone(r['ranking']);self.assertEqual(r['R2_F'],'NOT_IMPLEMENTED')

    def test_same_prefix_all_future_paths_have_identical_initial_decision(self):
        ids={v['first_decision_id'] for r in self.results.values() for v in r['policy_results'].values()}
        self.assertEqual(len(ids),1)
        initial=[]
        for f in self.fixtures.values():
            initial.append(evaluate(f['trend_input'],decision_at=f['frames'][0]['decision_at']))
        self.assertTrue(all(x==initial[0] for x in initial))

    def test_invalid_future_evidence_and_prices_do_not_rewrite_prefix(self):
        f=deepcopy(self.fixtures['staircase_up']);when=f['frames'][0]['decision_at'];before=evaluate(f['trend_input'],decision_at=when)
        for row in f['trend_input']['records'][1:]:row.update(price='INVALID_FUTURE',structure_state='NOT_A_STATE')
        self.assertEqual(evaluate(f['trend_input'],decision_at=when),before)

    def test_continuation_is_reversible_and_prior_refutation_remains_saved(self):
        f=self.fixtures['deep_drawdown_then_resume'];r=evaluate(f['trend_input'],decision_at=f['frames'][-1]['decision_at'])
        self.assertEqual(r['records'][2]['state'],'CONTINUATION_REFUTED')
        self.assertEqual(r['records'][3]['state'],'CONTINUATION_SUPPORTED')
        prefix=evaluate(f['trend_input'],decision_at=f['frames'][2]['decision_at'])
        self.assertEqual(r['records'][:3],prefix['records'])

    def test_target_reached_or_elapsed_time_does_not_force_exit(self):
        f=self.fixtures['staircase_up'];row=evaluate(f['trend_input'],decision_at=f['frames'][1]['decision_at'])['records'][-1]
        self.assertTrue(row['reached_original_target']);self.assertEqual(row['holding_qualification'],'CONDITIONAL_RESEARCH_HOLD')
        self.assertFalse(row['automatic_exit_on_target_or_days'])
        held=self.results['staircase_up']['policy_results']['structure_hold']['rounds'][1]
        self.assertEqual(held['execution']['orders'],[])

    def test_hold_qualification_is_not_add_qualification(self):
        f=self.fixtures['staircase_up'];r=evaluate(f['trend_input'],decision_at=f['frames'][0]['decision_at'])['records'][0]
        self.assertEqual(r['holding_qualification'],'CONDITIONAL_RESEARCH_HOLD')
        self.assertEqual(r['additional_capital_qualification'],'NOT_QUALIFIED')

    def test_winner_label_cannot_relax_hard_risk(self):
        f=deepcopy(self.fixtures['staircase_up']);p=f['trend_input'];p['records'][0]['hard_risk_breaches']=['HARD_GROUP_LIMIT']
        p['records'][0]['new_capital_evidence_qualified']=True;p['winner_label']='TENFOLD_WINNER'
        r=evaluate(p,decision_at=f['frames'][0]['decision_at'])['records'][0]
        self.assertEqual(r['holding_qualification'],'RISK_REDUCTION_REQUIRED')
        self.assertEqual(r['additional_capital_qualification'],'NOT_QUALIFIED')

    def test_pressure_data_gap_checked_absence_broken_and_remaining_are_distinct(self):
        f=deepcopy(self.fixtures['staircase_up']);p=f['trend_input'];p['references']=[];p['records']=p['records'][:1]
        p['records'][0]['pressure']=dict(status='DATA_MISSING',crossed_reference_ids=[],checked_scope=None)
        a=evaluate(p,decision_at=p['records'][0]['decision_at'])['records'][0]
        p['records'][0]['pressure'].update(status='NO_IDENTIFIABLE_UPPER_PRESSURE_IN_VERIFIED_SCOPE',
            checked_scope=dict(qualification='EXPLICIT_SYNTHETIC_VERIFIED_SCOPE',source_ids=['fixture'],scope_id='bounded-history'))
        p['records'][0]['new_capital_evidence_qualified']=True
        b=evaluate(p,decision_at=p['records'][0]['decision_at'])['records'][0]
        self.assertNotEqual(a['pressure_status'],b['pressure_status']);self.assertIsNone(a['reasonable_space']);self.assertIsNone(b['reasonable_space'])
        self.assertEqual(b['additional_capital_qualification'],'NOT_QUALIFIED')
        f=self.fixtures['direct_acceleration'];r=evaluate(f['trend_input'],decision_at=f['frames'][1]['decision_at'])
        self.assertEqual(r['records'][0]['pressure_status'],'UPPER_PRESSURE_REMAINS')
        self.assertEqual(r['records'][1]['pressure_status'],'BROKEN_OLD_REFERENCE')

    def test_no_identifiable_pressure_requires_a_verified_bounded_scope(self):
        f=deepcopy(self.fixtures['staircase_up']);p=f['trend_input'];p['references']=[]
        p['records'][0]['pressure'].update(status='NO_IDENTIFIABLE_UPPER_PRESSURE_IN_VERIFIED_SCOPE',checked_scope=dict(qualification='UNKNOWN',source_ids=[],scope_id=''))
        with self.assertRaises(ValueError):evaluate(p,decision_at=f['frames'][0]['decision_at'])

    def test_small_new_step_never_clears_an_old_major_pressure(self):
        f=deepcopy(self.fixtures['direct_acceleration']);p=f['trend_input'];ref=deepcopy(p['references'][0]);ref.update(id='older-higher-major',price='80');p['references'].append(ref)
        r=evaluate(p,decision_at=f['frames'][1]['decision_at'])['records'][-1]
        self.assertEqual(r['pressure_status'],'UPPER_PRESSURE_REMAINS')
        self.assertIn('older-higher-major',r['known_upper_reference_ids'])
        self.assertIn('original-major',r['crossed_reference_ids'])

    def test_source_basis_change_is_unknown_not_a_new_buy_signal(self):
        f=self.fixtures['source_basis_change'];r=evaluate(f['trend_input'],decision_at=f['frames'][-1]['decision_at'])
        for row in r['records'][2:]:
            self.assertEqual(row['state'],'UNKNOWN');self.assertEqual(row['pressure_status'],'DATA_MISSING')
            self.assertEqual(row['additional_capital_qualification'],'NOT_QUALIFIED')

    def test_evidence_source_or_version_conflicts_are_not_accepted_support(self):
        f=deepcopy(self.fixtures['staircase_up']);f['trend_input']['records'][0]['evidence']['box'][0]['source_id']='other'
        with self.assertRaises(ValueError):evaluate(f['trend_input'],decision_at=f['frames'][0]['decision_at'])
        for p in self.results['staircase_up']['policy_results'].values():
            for rr in p['rounds']:
                state=rr['point_in_time_trend'];decision=rr['decision']['decision']
                self.assertEqual(decision['parameter_source'],'SYNTHETIC_TREND_REVIEW:'+state['record_id'])
                linked=[e['value']['original_evidence_id'] for f in decision['layer1']['A']['features'].values()
                        for stance in ('support','refutation','unknown') for e in f[stance] if 'value' in e]
                self.assertEqual(set(linked),set(state['evidence_ids']))

    def test_participation_is_variable_and_not_a_permanent_floor(self):
        f=self.fixtures['staircase_up'];sizes=[x['participation_shares'] for x in f['frames']]
        self.assertGreater(len(set(sizes)),3)
        for row in evaluate(f['trend_input'],decision_at=f['frames'][-1]['decision_at'])['records']:
            self.assertIsNone(row['permanent_participation_ratio'])

    def test_virtual_purposes_partition_holdings_and_keep_entitlements_once(self):
        r=self.results['staircase_up']['policy_results']['original_baseline']['rounds'][0]['execution']['ledger']['daily'][0]
        labels=dict(A={'trend':'60','participation':'40'},B={'other':'0'},C={'other':'0'})
        v=describe_position_roles(r,labels);self.assertEqual(v['physical_shares']['A'],'100')
        self.assertFalse(v['separate_capital_or_entitlement_accounts'])
        labels['A']['participation']='100'
        with self.assertRaises(ValueError):describe_position_roles(r,labels)

    def test_geometric_growth_uses_one_original_account_not_trade_profit_per_day(self):
        with localcontext() as c:
            c.prec=50
            for result in self.results.values():
                for p in result['policy_results'].values():
                    m=p['metrics'];self.assertEqual(m['initial_capital'],'2000')
                    self.assertEqual(Decimal(m['geometric_growth']),Decimal(m['terminal_net_liquidation_estimate'])/Decimal('2000')-1)
                    for rr in p['rounds']:self.assertEqual(rr['execution']['ledger']['initial_equity'],'2000')

    def test_market_paths_are_shared_but_realized_exposure_is_not_falsely_equal(self):
        for result in self.results.values():
            self.assertEqual(len({p['common_market_path_id'] for p in result['policy_results'].values()}),1)
            for p in result['policy_results'].values():self.assertIn('NOT_IMPLEMENTED',p['metrics']['matched_realized_exposure_control'])
        base=self.results['direct_acceleration']['policy_results']['original_baseline']
        self.assertGreater(base['observed_risk_breach_count'],0)
        self.assertIn('NOT_RISK_QUALIFIED',base['qualification'])

    def test_limit_blocks_are_real_unfilled_orders_not_assumed_exits(self):
        p=self.results['limits_unfilled']['policy_results']['structure_hold']
        events=[e for rr in p['rounds'] for e in rr['execution']['execution_events']]
        self.assertTrue(any(e.get('reason')=='MARKET_BLOCK' for e in events))
        self.assertTrue(any(st['status']=='EXPIRED_UNFILLED' and Decimal(st['remaining'])>0
                            for rr in p['rounds'] for st in rr['execution']['order_states'].values()))

    def test_exit_then_repair_reentry_uses_later_decision_and_actual_cash(self):
        p=self.results['exit_repair_reentry']['policy_results']['structure_hold'];fills=p['rounds'][-1]['execution']['fills']
        sales=[f for f in fills if f['code']=='A' and f['side']=='SELL'];buys=[f for f in fills if f['code']=='A' and f['side']=='BUY']
        self.assertTrue(sales);self.assertTrue(buys)
        self.assertGreater(buys[-1]['decision_date'],sales[0]['decision_date'])

    def test_no_participation_policy_is_preselected_as_best(self):
        up=self.results['staircase_up']['policy_results'];limits=self.results['limits_unfilled']['policy_results']
        terminal=lambda p:Decimal(p['metrics']['terminal_net_liquidation_estimate'])
        self.assertLess(terminal(up['flexible_participation']),terminal(up['structure_hold']))
        self.assertGreater(terminal(limits['flexible_participation']),terminal(limits['structure_hold']))

    def test_evaluation_labels_cannot_rewrite_any_decision(self):
        f=deepcopy(self.fixtures['staircase_up']);f['evaluation_labels']['named_asset']='B';changed=run_fixture(f)
        for p in POLICIES:
            before=self.results['staircase_up']['policy_results'][p]['rounds'];after=changed['policy_results'][p]['rounds']
            self.assertEqual([x['decision'] for x in before],[x['decision'] for x in after])


if __name__=='__main__':unittest.main()
