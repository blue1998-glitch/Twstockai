"""Engineered accounting cases are not market returns or strategy validation."""
from copy import deepcopy
from decimal import Decimal
import unittest
from graph_core.core import fingerprint
from .action_ledger import days, replay, compare, qualify


from .action_fixtures import fixture, event, fill


def row(result, when): return next(x for x in result['daily'] if x['date']==when)


class ActionLedger(unittest.TestCase):
    def test_cash_entitlement_not_cash_and_net_tax(self):
        d=fixture();event(d)
        d['assets']['A']['quotes'].update({day:'9' for day in d['assets']['A']['quotes'] if day>'2026-01-05'})
        r=replay(d)
        self.assertEqual(row(r,'2026-01-06')['cash_receivable'],'80.0')
        self.assertEqual(row(r,'2026-01-06')['available_cash_strict'],'0')
        self.assertEqual(row(r,'2026-01-09')['settled_cash'],'80.0')
        self.assertEqual(Decimal(r['scenario_net_return']),Decimal('-.02'))
        self.assertIsNone(r['total_net_return'])

    def test_ex_day_sale_keeps_dividend(self):
        d=fixture();event(d);fill(d,'SELL','2026-01-06')
        r=replay(d);self.assertEqual(row(r,'2026-01-09')['settled_cash'],'980.0')
        self.assertEqual(row(r,'2026-01-06')['shares']['A'],'0')

    def test_ex_day_buyer_does_not_receive_prior_owner_entitlement(self):
        d=fixture();d['opening'].update(cash='1000',shares={'A':'0','B':'0'});event(d)
        fill(d,'BUY','2026-01-06');r=replay(d)
        claim=next(x for x in r['journal'] if x['type']=='DIVIDEND_RECEIVABLE')
        self.assertEqual(claim['entitled_shares'],'0');self.assertEqual(claim['net'],'0.0')

    def test_sell_before_ex_date_no_entitlement(self):
        d=fixture();event(d,ex_date='2026-01-07');fill(d,'SELL','2026-01-06')
        r=replay(d);self.assertEqual(row(r,'2026-01-09')['settled_cash'],'900.0')

    def test_receivable_and_payment_day_not_early_buying_power(self):
        for when in ('2026-01-06','2026-01-09'):
            with self.subTest(when=when):
                d=fixture();event(d);fill(d,'BUY',when,code='B',shares='1',price='20')
                with self.assertRaisesRegex(ValueError,'buying power'):replay(d)
        d=fixture();event(d);fill(d,'BUY','2026-01-12',code='B',shares='4',price='20')
        self.assertEqual(row(replay(d),'2026-01-12')['shares']['B'],'4')

    def test_nontrading_payment_and_dated_carried_mark(self):
        d=fixture();event(d,pay_date='2026-01-10');r=replay(d)
        self.assertEqual(row(r,'2026-01-10')['settled_cash'],'80.0')
        mark=row(r,'2026-01-11')['marks']['A']
        self.assertEqual(mark['source_date'],'2026-01-09');self.assertTrue(mark['carried_nontrading_mark'])
        self.assertNotIn('2026-01-10',d['assets']['A']['quotes'])

    def test_stock_delivery_and_tradability_separate(self):
        d=fixture();event(d,'STOCK_DIVIDEND');r=replay(d)
        self.assertEqual(row(r,'2026-01-08')['shares']['A'],'100')
        self.assertEqual(row(r,'2026-01-08')['share_receivables'][0]['shares'],'10.0')
        self.assertEqual(row(r,'2026-01-09')['shares']['A'],'110')
        self.assertEqual(len([x for x in r['journal'] if x['type']=='SHARES_DELIVERED_NOT_YET_ASSUMED_TRADABLE']),1)

    def test_stock_not_sellable_before_credit(self):
        d=fixture();event(d,'STOCK_DIVIDEND');fill(d,'SELL','2026-01-08',shares='110')
        with self.assertRaisesRegex(ValueError,'unavailable'):replay(d)

    def test_stock_receivable_survives_sale_of_original_shares(self):
        d=fixture();event(d,'STOCK_DIVIDEND');fill(d,'SELL','2026-01-06')
        self.assertEqual(row(replay(d),'2026-01-09')['shares']['A'],'10')

    def test_fractional_shares_retained_and_return_refused(self):
        d=fixture();event(d,'STOCK_DIVIDEND',shares_per_share='0.015');r=replay(d)
        self.assertIn('FRACTIONAL_SHARE_DISPOSITION_UNVERIFIED',r['refusal_reasons'])
        self.assertEqual(row(r,'2026-01-12')['share_receivables'][0]['shares'],'0.500')
        self.assertIsNone(r['scenario_net_return'])

    def test_reduction_no_dividend_double_count(self):
        d=fixture();event(d,'CAPITAL_REDUCTION');r=replay(d)
        self.assertEqual(row(r,'2026-01-06')['shares']['A'],'0')
        self.assertEqual(row(r,'2026-01-08')['shares']['A'],'50')
        self.assertEqual(row(r,'2026-01-09')['settled_cash'],'500')
        self.assertEqual(Decimal(r['scenario_net_return']),0)
        self.assertFalse(any(x['type']=='DIVIDEND_RECEIVABLE' for x in r['journal']))

    def test_reduction_suspension_missing_quote_is_not_invented(self):
        d=fixture();event(d,'CAPITAL_REDUCTION');del d['assets']['A']['quotes']['2026-01-06']
        r=replay(d);self.assertIsNone(row(r,'2026-01-06')['net_accrual_equity'])
        self.assertIsNone(r['scenario_net_return']);self.assertTrue(r['quote_gaps'])

    def test_opening_claims_explicit_not_inferred_from_current_shares(self):
        d=fixture();d['opening']['shares']['A']='0';d['opening']['cash_claims']=[dict(id='old',amount='80',pay_date='2026-01-09',source_ids=['fixture'])]
        r=replay(d);self.assertEqual(r['initial_equity'],'80');self.assertEqual(row(r,'2026-01-09')['settled_cash'],'80')
        d['qualification']['opening_claims']='UNKNOWN'
        self.assertIn('OPENING_ENTITLEMENTS_UNKNOWN',replay(d)['refusal_reasons'])

    def test_missing_no_event_coverage_does_not_default_to_none(self):
        d=fixture();d['coverage']['A']['status']='INCOMPLETE'
        self.assertEqual(replay(d)['daily'],[])
        self.assertIn('ACTION_COVERAGE_INCOMPLETE:A',qualify(d))

    def test_missing_net_and_stock_ratio_refuse_without_type_error(self):
        for kind,overrides in [('CASH_DIVIDEND',dict(net_per_share=None)),('STOCK_DIVIDEND',dict(shares_per_share=None,tradable_date=None))]:
            with self.subTest(kind=kind):
                d=fixture();event(d,kind,**overrides);self.assertTrue(replay(d)['refusal_reasons'])

    def test_mixed_adjusted_and_event_identity_or_proof_tampering(self):
        d=fixture();d['mode']='ADJUSTED'
        with self.assertRaisesRegex(ValueError,'RAW'):replay(d)
        d=fixture();e=event(d);e['gross_per_share']='2'
        with self.assertRaisesRegex(ValueError,'fingerprint'):replay(d)
        d=fixture();e=event(d);e['field_sources']['pay_date'][0]['source_id']='not-a-source'
        e['id']=fingerprint({k:v for k,v in e.items() if k!='id'})
        with self.assertRaisesRegex(ValueError,'Field proof'):replay(d)

    def test_coverage_exact_list_and_calendar_gap(self):
        d=fixture();event(d);d['coverage']['A']['event_ids']=[]
        self.assertIn('COVERAGE_EVENT_LIST_MISMATCH:A',qualify(d))
        d=fixture();d['calendar'].pop(3)
        with self.assertRaisesRegex(ValueError,'calendar date'):replay(d)

    def test_explicit_sale_receivable_vs_settlement_cash(self):
        d=fixture();fill(d,'SELL','2026-01-06',settlement='2026-01-08');r=replay(d)
        self.assertEqual(row(r,'2026-01-06')['settled_cash'],'0')
        self.assertEqual(row(r,'2026-01-06')['cash_receivable'],'900')
        self.assertEqual(row(r,'2026-01-08')['settled_cash'],'900')

    def test_buy_payables_deduct_equity_and_reserve_cash(self):
        d=fixture();d['opening'].update(cash='1000',shares={'A':'0','B':'0'})
        fill(d,'BUY','2026-01-06',shares='50',price='10',fee='2',settlement='2026-01-08');r=replay(d)
        self.assertEqual(row(r,'2026-01-06')['purchase_payable'],'502')
        self.assertEqual(row(r,'2026-01-06')['net_accrual_equity'],'998')
        self.assertEqual(row(r,'2026-01-08')['settled_cash'],'498')

    def test_no_future_decision_and_no_future_quote_read(self):
        d=fixture();f=fill(d,'SELL','2026-01-06');f['decision_date']='2026-01-06'
        with self.assertRaisesRegex(ValueError,'precede'):replay(d)
        d=fixture();event(d);a=replay(d);d['assets']['A']['quotes']['2026-01-12']='99999';b=replay(d)
        self.assertEqual(a['daily'][:-1],b['daily'][:-1])

    def test_deterministic_immutable_input_exact_decimal(self):
        d=fixture();event(d,net_per_share='0.12345678901234567890123456789');old=deepcopy(d)
        a=replay(d);self.assertEqual(d,old);self.assertEqual(a,replay(d))
        self.assertEqual(row(a,'2026-01-06')['cash_receivable'],'12.34567890123456789012345678900')

    def test_terminal_cost_and_unheld_missing_quote(self):
        d=fixture();d['terminal_costs'].update(fee_rate='.001',minimum_fee='2',sell_tax='.003',slippage_bps='10')
        d['assets']['B']['quotes']={};r=replay(d)
        self.assertEqual(Decimal(r['terminal_estimated_exit_cost']),Decimal('6'))

    def test_nontrading_terminal_uses_dated_mark(self):
        d=fixture();d['end']='2026-01-11';d['calendar']=d['calendar'][:-1]
        r=replay(d);self.assertIsNotNone(r['scenario_net_return'])

    def test_comparison_refuses_empty_unqualified_or_unequal_accounts(self):
        with self.assertRaises(ValueError):compare({})
        a=fixture();b=fixture();r=compare(dict(hold=a,other=b));self.assertFalse(r['total_net_return_comparison_qualified'])
        b['opening']['cash']='1'
        with self.assertRaisesRegex(ValueError,'Unequal'):compare(dict(a=a,b=b))

    def test_cash_and_stock_same_ex_date_use_same_prior_holdings(self):
        d=fixture();event(d);event(d,'STOCK_DIVIDEND');a=replay(d)
        d['events'].reverse();b=replay(d)
        self.assertEqual(a['daily'],b['daily'])
        self.assertEqual(row(a,'2026-01-09')['shares']['A'],'110')
        self.assertEqual(row(a,'2026-01-09')['settled_cash'],'80.0')

    def test_overlap_uncredited_entitlements_refused(self):
        d=fixture();event(d,'STOCK_DIVIDEND');event(d,ex_date='2026-01-07')
        with self.assertRaisesRegex(ValueError,'Overlapping'):replay(d)

    def test_net_capital_return_greater_than_gross_rejected(self):
        d=fixture();event(d,'CAPITAL_REDUCTION',net_cash_per_old_share='6')
        with self.assertRaisesRegex(ValueError,'net capital'):replay(d)

    def test_duplicate_opening_claims_rejected(self):
        d=fixture();x=dict(id='old',amount='80',pay_date='2026-01-09',source_ids=['fixture'])
        d['opening']['cash_claims']=[x,deepcopy(x)]
        with self.assertRaisesRegex(ValueError,'Duplicate opening'):replay(d)

    def test_qualified_return_requires_complete_cash_account_and_cost_evidence(self):
        d=fixture();d['sources']['fixture']['kind']='OFFICIAL_ARCHIVE'
        d['qualification'].update(execution_costs='VERIFIED_EXPLICIT_MODEL',investor_cashflows='UNVERIFIED')
        self.assertIsNotNone(replay(d)['total_net_return'])
        self.assertIsNone(replay(d)['actual_realized_investor_return'])
        fill(d,'SELL','2026-01-06',price='10',fee='2',tax='3')
        r=replay(d);self.assertEqual(Decimal(r['total_net_return']),Decimal('-.005'))
        comparison=compare(dict(sold=d));self.assertTrue(comparison['total_net_return_comparison_qualified'])
        self.assertEqual(comparison['pairwise_end_net_equity_difference']['sold']['sold'],'0')
        self.assertIsNone(r['actual_realized_investor_return'])
        d['qualification'].update(execution_costs='VERIFIED_ACTUAL',investor_cashflows='VERIFIED_ACTUAL')
        self.assertEqual(replay(d)['actual_realized_investor_return'],r['total_net_return'])
        d['qualification']['execution_costs']='SCENARIO';self.assertIsNone(replay(d)['total_net_return'])

    def test_pending_cash_retained_not_mistaken_for_realised_return(self):
        d=fixture();event(d,pay_date='2026-01-20');r=replay(d)
        self.assertEqual(row(r,'2026-01-12')['cash_receivable'],'80.0')
        self.assertEqual(row(r,'2026-01-12')['settled_cash'],'0')

    def test_equal_capital_comparison_of_declared_cost_model(self):
        hold=fixture();hold['sources']['fixture']['kind']='OFFICIAL_ARCHIVE'
        hold['qualification']['execution_costs']='VERIFIED_EXPLICIT_MODEL'
        sold=deepcopy(hold);fill(sold,'SELL','2026-01-06',price='10',fee='2',tax='3')
        c=compare(dict(hold=hold,sold=sold))
        self.assertEqual(c['pairwise_end_net_equity_difference']['hold']['sold'],'5')
        self.assertIsNone(c['results']['hold']['actual_realized_investor_return'])
        hold['assets']['A']['quote_source_ids']=['missing']
        with self.assertRaisesRegex(ValueError,'Unbound quote'):replay(hold)


if __name__=='__main__':unittest.main()
