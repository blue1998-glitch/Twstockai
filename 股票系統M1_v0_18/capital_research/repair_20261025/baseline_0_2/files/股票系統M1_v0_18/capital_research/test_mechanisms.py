"""Directed mechanism tests. Every price, order and performance path is synthetic."""
from copy import deepcopy
from decimal import Decimal, localcontext
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from graph_core.core import fingerprint
from rotation_research.store import Journal
from rotation_research.action_fixtures import event
from .core import decide, evidence_tokens, resume_decision
from .execution import simulate, compare_jobs
from .fixtures import fixture, job, ledger, observation, CUTOFF
from .allocation import full_transfer
from .evidence import from_saved_layers


def alternatives(data):
    return {p['id']:p for p in decide(data)['decision']['layer3']['alternatives']}


def terminal(result):
    return Decimal(result['ledger']['daily'][-1]['net_accrual_equity'])


class MechanismTests(unittest.TestCase):
    def test_R1_full_deploy_respects_costs_and_risk_without_fixed_ratio(self):
        d=fixture();r=full_transfer(d,incumbent='A',destination='B')
        self.assertEqual(r['targets'],dict(A='0',B='99',C='0'))
        d['risk_limits']['single_name_value']['B']='1000'
        r=full_transfer(d,incumbent='A',destination='B')
        self.assertEqual(r['targets']['B'],'50')
        self.assertEqual(r['funding'],'WAIT_SALE_SETTLEMENT_AND_REEVALUATE')

    def saved_layers(self):
        from manual_basis.core import resolve
        binding=dict(series_key='synthetic',code='A',source_id='fixture',price_basis_id='RAW:fixture:A',
                     frame_id='synthetic-frame',adjustment_version='RAW:synthetic/1',price_mode='RAW_CANDIDATE',as_of='2026-01-05')
        cat=dict(schema_version='manual-basis-catalogue/0.1',entries=[binding]);cat['catalogue_id']=fingerprint(cat)
        request=dict(schema_version='manual-basis-request/0.1',selection_id='fixture-choice',selected_at=CUTOFF,
                     code='A',price_mode='RAW_CANDIDATE',as_of='2026-01-05',series_key='synthetic')
        manual=resolve(cat,request)
        context={k:binding[k] for k in ('code','source_id','price_basis_id','price_mode','adjustment_version')}
        context.update(source_frame_id=binding['frame_id'],source_prefix_fingerprint='synthetic-prefix')
        reaction=dict(schema_version='multi-reference-reaction-facts/0.1',context=context,as_of='2026-01-05',
                      records=[dict(date='2026-01-05',synthetic=True)],historical_signal_eligible=False)
        reaction['result_id']=fingerprint(reaction)
        structure=dict(schema_version='p03-structure-state/0.1',context=context,as_of='2026-01-05',
                       original_reaction_result_id=reaction['result_id'],records=[dict(date='2026-01-05',state='INSUFFICIENT',synthetic=True)],
                       historical_signal_eligible=False,primary_pressure_id=None)
        structure['result_id']=fingerprint(structure)
        return structure,reaction,manual

    def test_saved_layers_preserved_without_promoting_entry_or_pressure(self):
        s,r,m=self.saved_layers();v=from_saved_layers(s,r,m,available_at=CUTOFF,decision_at=fixture()['decision_at'])
        self.assertEqual(v['structure'],s);self.assertEqual(v['reaction'],r);self.assertEqual(v['manual_basis'],m)
        self.assertIsNone(v['formal_resistance']);self.assertFalse(v['historical_signal_eligible'])

    def test_saved_layers_source_time_or_fingerprint_conflict_refused(self):
        s,r,m=self.saved_layers()
        with self.assertRaises(ValueError):from_saved_layers(s,r,m,available_at='2026-01-06T14:00:00+08:00',decision_at=fixture()['decision_at'])
        s['context']=deepcopy(s['context']);s['context']['price_basis_id']='other';s['result_id']=fingerprint({k:v for k,v in s.items() if k!='result_id'})
        with self.assertRaises(ValueError):from_saved_layers(s,r,m,available_at=CUTOFF,decision_at=fixture()['decision_at'])

    def test_future_outcomes_and_invalid_future_values_do_not_change_decision(self):
        baseline=decide(fixture())['decision']
        for label,pa,pb in [('A_surge','100','1'),('B_surge','1','100'),('both_crash','1','1')]:
            d=fixture()
            for c,p in [('A',pa),('B',pb),('C','INVALID_FUTURE_VALUE')]:
                row=deepcopy(d['assets'][c]['marks'][0]);row.update(price=p,occurred_at='2026-01-06T14:00:00+08:00',available_at='2026-01-06T14:00:00+08:00')
                d['assets'][c]['marks'].append(row)
                e=deepcopy(d['assets'][c]['evidence'][0]);e.update(id='future-'+c,stance='INVALID_FUTURE_STANCE',available_at='2026-01-06T14:00:00+08:00')
                d['assets'][c]['evidence'].append(e)
            d['source_integrity_metadata']['full_source_fingerprint']=label
            r=decide(d)
            self.assertEqual(r['decision'],baseline)
            self.assertNotEqual(r['source_integrity_metadata'],decide(fixture())['source_integrity_metadata'])

    def test_delayed_availability_is_not_known_at_occurrence(self):
        d=fixture();d['assets']['B']['evidence'][0]['available_at']='2026-01-06T14:00:00+08:00'
        self.assertIn('NO_NEW_INDEPENDENT_TRIGGER',alternatives(d)['C-event']['reasons'])

    def test_cutoff_and_timezone_are_required(self):
        d=fixture();d['data_cutoff']='2026-01-06T14:00:00+08:00'
        with self.assertRaises(ValueError):decide(d)
        d=fixture();d['decision_at']='2026-01-05T15:00:00'
        with self.assertRaises(ValueError):decide(d)

    def test_missing_mark_never_fills_or_zeros(self):
        d=fixture();d['assets']['A']['marks'][0]['price']=None
        with self.assertRaises(ValueError):decide(d)
        d=fixture();d['assets']['A']['marks']=[]
        with self.assertRaises(ValueError):decide(d)

    def test_stale_mark_and_conflicting_basis_refused(self):
        d=fixture();d['assets']['A']['marks'][0]['occurred_at']='2026-01-04T14:00:00+08:00'
        with self.assertRaises(ValueError):decide(d)
        d=fixture();d['assets']['B']['marks'][0]['basis_id']='ADJUSTED:other'
        with self.assertRaises(ValueError):decide(d)

    def test_three_layers_no_probability_or_invented_pressure(self):
        d=fixture();d['assets']['B']['entry_context']['formal_reference']=None
        r=decide(d)['decision']
        self.assertEqual(r['layer1']['B']['conclusion'],'EVIDENCE_ONLY_NO_STRENGTH_RANKING')
        self.assertIsNone(r['layer1']['B']['strength_probability'])
        self.assertIsNone(r['layer2']['B']['reasonable_space'])
        self.assertIsNone(r['primary_pressure_id'])
        self.assertIn('ENTRY_EVIDENCE_UNKNOWN:B',alternatives(d)['B-full']['reasons'])

    def test_all_families_and_R2_explicitly_unimplemented(self):
        r=decide(fixture())['decision'];ps=r['layer3']['alternatives']
        self.assertEqual(set(p['family'] for p in ps),set('ABCDEF'))
        self.assertEqual(ps[-1]['status'],'NOT_IMPLEMENTED')
        self.assertEqual(len(set(p['common_account_id'] for p in ps)),1)
        self.assertEqual(len(set(p['initial_capital'] for p in ps)),1)

    def test_no_recommendation_promotes_any_qualification(self):
        d=fixture();d.update(data_qualified=True,policy_authorized=True,live_execution_authorized=True)
        r=decide(d)['decision']
        for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'):
            self.assertIs(r[k],False)
        self.assertTrue(r['research_recommendation']['candidate_ids'])

    def test_full_allocation_pays_costs_from_original_capital(self):
        r=simulate(job());self.assertEqual(terminal(r),Decimal('1991.020'))
        self.assertEqual(r['ledger']['fees_and_tax_on_fills'],'6')
        # 2000 = final 1991.02 + commissions/tax 6 + effective-price slippage 2.98.
        self.assertEqual(terminal(r)+Decimal('6')+Decimal('2.98'),Decimal('2000'))
        d=fixture();d['plans'][0]['targets']['B']='100'
        self.assertIn('JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS',alternatives(d)['B-full']['reasons'])

    def test_receivable_payable_and_cash_are_separate(self):
        r=simulate(job());rows={x['date']:x for x in r['ledger']['daily']}
        self.assertEqual(rows['2026-01-06']['settled_cash'],'1000')
        self.assertEqual(Decimal(rows['2026-01-06']['cash_receivable']),Decimal('995'))
        self.assertEqual(rows['2026-01-09']['purchase_payable'],'1983.980')
        self.assertEqual(rows['2026-01-09']['settled_cash'],'1995.000')
        for row in rows.values():
            nav=Decimal(row['settled_cash'])+Decimal(row['cash_receivable'])-Decimal(row['purchase_payable'])
            nav+=sum(Decimal(n)*Decimal(row['marks'][c]['value']) for c,n in row['shares'].items())
            nav+=sum(Decimal(x['shares'])*Decimal(row['marks'][x['code']]['value']) for x in row['share_receivables'])
            self.assertEqual(nav,Decimal(row['net_accrual_equity']))

    def test_same_NAV_with_different_rights_is_not_fair_comparison(self):
        a=job('A-zero');b=job('D-cash')
        b['decision_input']['account']['settled_cash']='920'
        b['decision_input']['account']['cash_claims']=[dict(id='right',amount='80',pay_date='2026-01-09',source_ids=['fixture'])]
        b['ledger_input']=ledger(b['decision_input'])
        self.assertEqual(decide(a['decision_input'])['decision']['initial_capital'],decide(b['decision_input'])['decision']['initial_capital'])
        with self.assertRaises(ValueError):compare_jobs(dict(a=a,b=b))

    def test_joint_multi_candidate_cash_cannot_be_used_twice(self):
        d=fixture();p=deepcopy(d['plans'][3]);p.update(id='conflict',targets=dict(A='100',B='30',C='30'))
        d['plans'].append(p)
        r=alternatives(d)['conflict']
        self.assertIn('JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS',r['reasons'])

    def test_existing_pending_buy_and_cash_reserves_count(self):
        d=fixture();d['account']['reserved_cash']='300'
        d['account']['pending_orders']=[dict(id='old-buy',code='B',side='BUY',remaining_shares='20',limit_price='20',reserved_cash='402')]
        r=alternatives(d)['E-joint']
        self.assertEqual(r['available_settled_cash'],'298')
        self.assertEqual(r['funding'],'WAIT_SALE_SETTLEMENT_AND_REEVALUATE')
        d['account']['pending_orders'][0]['reserved_cash']='1'
        with self.assertRaises(ValueError):decide(d)

    def test_pending_sell_reserves_stock(self):
        d=fixture();d['account']['pending_orders']=[dict(id='old-sell',side='SELL',code='A',remaining_shares='80')]
        self.assertIn('SELLABLE_SHARES_RESERVED_OR_UNAVAILABLE:A',alternatives(d)['D-cash']['reasons'])

    def test_opening_payable_reduces_budget_and_replay_refuses(self):
        d=fixture();d['account']['payables']=[dict(id='existing-debt',amount='300',pay_date='2026-01-08')]
        self.assertEqual(alternatives(d)['A-zero']['available_settled_cash'],'700')
        r=simulate(job('A-zero',d))
        self.assertIn('OPENING_PAYABLE_REPLAY_NOT_SUPPORTED',r['refusal_reasons'][0])

    def test_broker_credit_requires_terms_and_never_becomes_settled_cash(self):
        d=fixture();m=d['execution_model'];m['buying_power']='BROKER_CREDIT_RESEARCH'
        m['broker_credit']=dict(qualification='EXPLICIT_SYNTHETIC_TERMS',available_at=CUTOFF,source_id='synthetic-broker',version='credit-assumption/1',limit='1000')
        self.assertEqual(alternatives(d)['B-full']['broker_credit_separate'],'1000')
        self.assertEqual(alternatives(d)['B-full']['available_settled_cash'],'1000')
        self.assertIn('BROKER_CREDIT_ACCOUNTING_NOT_IMPLEMENTED',simulate(job('B-full',d))['refusal_reasons'][0])
        m['broker_credit']['qualification']='UNKNOWN'
        with self.assertRaises(ValueError):decide(d)

    def test_sale_receivable_cannot_fund_same_day_buy(self):
        r=simulate(job());buys=[f for f in r['fills'] if f['side']=='BUY']
        self.assertEqual([f['date'] for f in buys],['2026-01-09'])
        self.assertEqual(alternatives(fixture())['B-full']['funding'],'WAIT_SALE_SETTLEMENT_AND_REEVALUATE')

    def test_sale_completed_buy_limit_up_unfilled(self):
        j=job()
        for o in j['tape']:
            if o['code']=='B':o['market_state']='LIMIT_UP_NO_BUY'
        r=simulate(j)
        self.assertEqual([(f['side'],f['code']) for f in r['fills']],[('SELL','A')])
        self.assertEqual(r['ledger']['daily'][-1]['shares']['B'],'0')
        self.assertEqual(r['order_states']['B-buy']['status'],'EXPIRED_UNFILLED')

    def test_original_limit_down_cannot_exit_or_complete_rotation(self):
        j=job();j['tape'][0]['market_state']='LIMIT_DOWN_NO_SELL'
        r=simulate(j)
        self.assertEqual(r['fills'],[])
        self.assertEqual(r['ledger']['daily'][-1]['shares']['A'],'100')

    def test_partial_fill_capacity_not_full_switch(self):
        j=job();j['tape'][2]['capacity_shares']='20'
        r=simulate(j)
        self.assertEqual(r['ledger']['daily'][-1]['shares']['B'],'20')
        self.assertEqual(r['order_states']['B-buy']['remaining'],'79')
        self.assertEqual(r['order_states']['B-buy']['status'],'EXPIRED_UNFILLED')

    def test_partial_sale_leaves_original_stock_and_unfunded_buy(self):
        j=job();j['tape'][0]['capacity_shares']='20'
        r=simulate(j)
        self.assertEqual(r['ledger']['daily'][-1]['shares'],dict(A='80',B='0',C='0'))
        self.assertEqual(r['order_states']['A-sell']['remaining'],'80')

    def test_future_costs_and_policy_are_not_available_assumptions(self):
        for key in ('cost_model','risk_limits','scenario_set','execution_model'):
            d=fixture();d[key]['available_at']='2026-01-06T14:00:00+08:00'
            with self.assertRaises(ValueError):decide(d)
        d=fixture();d['policy_available_at']='2026-01-06T14:00:00+08:00'
        with self.assertRaises(ValueError):decide(d)

    def test_capacity_is_shared_by_orders_on_same_tape(self):
        j=job();o=j['orders'].pop();o['shares']='49';o['id']='B-one';j['orders'].append(o)
        two=deepcopy(o);two.update(id='B-two',shares='50');j['orders'].append(two)
        j['tape'][1]['capacity_shares']='0'
        j['tape'][2]['capacity_shares']='60'
        r=simulate(j)
        self.assertEqual(sum(Decimal(f['shares']) for f in r['fills'] if f['code']=='B'),Decimal('60'))

    def test_stop_and_limit_are_not_guaranteed_prices_or_maximum_loss(self):
        j=job('D-cash');j['orders'][0]['limit_price']='9';j['tape'][0]['price']='5'
        r=simulate(j)
        self.assertEqual(r['fills'],[])
        self.assertEqual(r['ledger']['daily'][-1]['shares']['A'],'100')

    def test_small_edge_can_choose_zero_trade(self):
        d=fixture();d['plans'][0]['edge_budget']='1'
        self.assertIn('NO_TRADE_BAND',alternatives(d)['B-full']['reasons'])
        self.assertTrue(alternatives(d)['A-zero']['feasible'])

    def test_risk_reduction_overrides_small_edge_band(self):
        d=fixture();d['risk_limits']['single_name_value']['A']='500';d['plans'][2]['edge_budget']='0'
        ps=alternatives(d)
        self.assertFalse(ps['A-zero']['feasible'])
        self.assertTrue(ps['D-cash']['feasible']);self.assertTrue(ps['D-cash']['risk_reducing'])
        self.assertNotIn('NO_TRADE_BAND',ps['D-cash']['reasons'])

    def test_single_group_account_and_liquidity_limits(self):
        for key,change in [('single',lambda d:d['risk_limits']['single_name_value'].__setitem__('B','500')),
                           ('group',lambda d:d['risk_limits']['group_value'].__setitem__('new','100')),
                           ('account',lambda d:d['risk_limits'].__setitem__('account_stress_loss','1')),
                           ('liquidity',lambda d:d['risk_limits']['max_trade_shares'].__setitem__('B','1'))]:
            d=fixture();change(d)
            self.assertFalse(alternatives(d)['B-full']['feasible'],key)

    def test_false_breakout_and_acceleration_give_opposite_staging_tradeoffs(self):
        # Same initial account/cost model, different explicitly synthetic future paths.
        for label,pa,pb,relation in [('false_breakout','15','12','greater'),('acceleration','11','32','less')]:
            full=job();stage=job('C-event')
            for j in (full,stage):
                j['ledger_input']['assets']['A']['quotes']['2026-01-12']=pa
                j['ledger_input']['assets']['B']['quotes']['2026-01-12']=pb
            f,s=terminal(simulate(full)),terminal(simulate(stage))
            self.assertTrue(s>f if relation=='greater' else s<f,label)

    def test_cash_advantage_drag_and_slow_reentry(self):
        for pa,pb,cash_wins in [('7','12',True),('15','32',False)]:
            h=job('A-zero');c=job('D-cash')
            for j in (h,c):
                j['ledger_input']['assets']['A']['quotes']['2026-01-12']=pa
                j['ledger_input']['assets']['B']['quotes']['2026-01-12']=pb
            hv,cv=terminal(simulate(h)),terminal(simulate(c))
            self.assertTrue(cv>hv if cash_wins else cv<hv)
            self.assertEqual(cv,Decimal('1995'))  # Cash nominal return 0; exit cost 5 is separate.
        late=job();late['tape'][2]['price']='32'
        r=simulate(late)
        self.assertEqual(r['ledger']['daily'][-1]['shares']['B'],'0')
        self.assertIn('CAPACITY_OR_LIMIT',[x['reason'] for x in r['execution_events'] if x['status']=='UNFILLED'])

    def test_event_dependency_and_consumed_evidence_cannot_add_again(self):
        d=fixture();d['consumed_evidence_tokens']=sorted(evidence_tokens(d['assets']['B']['evidence'][0]))
        self.assertIn('NO_NEW_INDEPENDENT_TRIGGER',alternatives(d)['C-event']['reasons'])

    def test_later_review_carries_event_identity_from_saved_predecessor(self):
        old=decide(fixture());d=fixture();d['decision_at']='2026-01-05T16:00:00+08:00'
        r=resume_decision(old,d)['decision']
        c=next(p for p in r['layer3']['alternatives'] if p['id']=='C-event')
        self.assertIn('NO_NEW_INDEPENDENT_TRIGGER',c['reasons'])
        self.assertEqual(r['new_evidence_tokens'],[])
        self.assertEqual(r['reviewed_evidence_tokens'],old['decision']['reviewed_evidence_tokens'])
        d=fixture();e=deepcopy(d['assets']['B']['evidence'][0]);e['id']='B-zsame-volume';e['formation_id']='different';e['event_id']='different'
        d['assets']['B']['evidence'].append(e);d['plans'][1]['trigger_ids']=[e['id']]
        self.assertIn('NO_NEW_INDEPENDENT_TRIGGER',alternatives(d)['C-event']['reasons'])

    def test_sell_preserves_ex_day_dividend_right(self):
        j=job('D-cash');event(j['ledger_input'])
        r=simulate(j);rows={x['date']:x for x in r['ledger']['daily']}
        self.assertEqual(Decimal(rows['2026-01-06']['cash_receivable']),Decimal('1075'))
        self.assertEqual(Decimal(rows['2026-01-09']['settled_cash']),Decimal('2075'))

    def test_opening_cash_and_share_rights_remain_in_capital(self):
        d=fixture();d['account']['cash_claims']=[dict(id='old-cash',amount='80',pay_date='2026-01-09',source_ids=['fixture'])]
        d['account']['share_claims']=[dict(id='old-shares',code='A',shares='10',delivery_date='2026-01-08',tradable_date='2026-01-09',source_ids=['fixture'])]
        self.assertEqual(Decimal(decide(d)['decision']['initial_capital']),Decimal('2180'))
        r=simulate(job('A-zero',d));self.assertEqual(terminal(r),Decimal('2180'))
        self.assertEqual(r['ledger']['daily'][-1]['shares']['A'],'110')

    def test_missing_company_action_net_still_refused(self):
        j=job('D-cash');event(j['ledger_input'],net_per_share=None)
        r=simulate(j)
        self.assertEqual(r['status'],'REFUSED');self.assertIsNone(r['ledger'])

    def test_missing_held_mark_remains_null_not_previous_price(self):
        j=job('A-zero');j['ledger_input']['assets']['A']['quotes']['2026-01-06']=None
        r=simulate(j)
        self.assertIsNone(r['ledger']['daily'][1]['net_accrual_equity'])
        self.assertIsNone(r['ledger']['scenario_net_return'])

    def test_fair_synthetic_comparison_keeps_total_return_unqualified(self):
        data=fixture();r=compare_jobs({p:job(p,data) for p in ('A-zero','B-full','C-event','D-cash','E-joint')})
        self.assertIsNone(r['ranking']);self.assertFalse(r['total_net_return_comparison_qualified'])
        self.assertEqual(len({v['common_account_id'] for v in r['results'].values()}),1)
        self.assertTrue(all(v['ledger']['total_net_return'] is None for v in r['results'].values()))

    def test_decimal_global_context_cannot_change_research_result(self):
        expected=decide(fixture())
        with localcontext() as c:
            c.prec=4
            self.assertEqual(decide(fixture()),expected)

    def test_real_flag_and_unknown_numeric_inputs_fail_closed(self):
        d=fixture();d['synthetic']=False
        with self.assertRaises(ValueError):decide(d)
        for v in (None,1.5,'NaN'):
            d=fixture();d['account']['settled_cash']=v
            with self.assertRaises((ValueError,TypeError)):decide(d)

    def test_immutable_store_conflict_and_partial_file_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            j=Journal(t);v=decide(fixture());j.save('case',v)
            original=Path(t,'case.json').read_bytes()
            with self.assertRaises(ValueError):j.save('case',{'different':True})
            self.assertEqual(Path(t,'case.json').read_bytes(),original)
            Path(t,'partial.json').write_text('{')
            with self.assertRaises(json.JSONDecodeError):j.read('partial')
            self.assertEqual(Path(t,'partial.json').read_text(),'{')

    def test_cli_READ_never_imports_or_recalculates_engines(self):
        with tempfile.TemporaryDirectory() as t:
            Journal(t).save('saved',{'opaque':'ORIGINAL_SAVED_RESULT'})
            code="""import sys
class Guard:
 def find_spec(self, name, *args):
  if name in ('capital_research.core','capital_research.execution','rotation_research.action_ledger'):
   raise RuntimeError('READ imported numeric engine')
sys.meta_path.insert(0, Guard())
from capital_research.cli import main
main()
"""
            p=subprocess.run([sys.executable,'-c',code,'READ','--store',t,'--id','saved'],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(json.loads(p.stdout)['value'],{'opaque':'ORIGINAL_SAVED_RESULT'})

    def test_ledger_orders_cannot_override_selected_plan(self):
        j=job('D-cash');j['orders'][0]['shares']='101'
        with self.assertRaises(ValueError):simulate(j)
        j=job();j['ledger_input']['opening']['cash']='1001'
        with self.assertRaises(ValueError):simulate(j)

    def test_execution_missing_price_or_settlement_date_refused(self):
        for field,v in [('price',None),('settlement_date',None)]:
            j=job();j['tape'][0][field]=v
            with self.assertRaises((ValueError,TypeError)):simulate(j)

    def test_execution_time_and_source_are_bound(self):
        j=job();j['tape'][0]['available_at']='2026-01-07T09:00:00+08:00'
        with self.assertRaises(ValueError):simulate(j)
        j=job();j['tape'][0]['basis_id']='other'
        with self.assertRaises(ValueError):simulate(j)


if __name__=='__main__':unittest.main()
