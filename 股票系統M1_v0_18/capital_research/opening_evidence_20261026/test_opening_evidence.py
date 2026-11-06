"""Only the new finite opening-evidence contract; no old suite or producer."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from capital_research.opening_evidence import check

HERE = Path(__file__).parent
PATH = 'entitlements.1101.cash_claims'


def saved(name, kind='input'):
    return json.loads((HERE/'cases'/name/(kind+'.json')).read_text())


def assert_saved(test, name):
    data, expected = saved(name), saved(name, 'expected')
    result = check(data)
    test.assertEqual(result['status'], expected['status'])
    row = result['fields'][expected['field']]
    test.assertEqual(row['classification'], expected['classification'])
    test.assertEqual(row['declared_value'], expected['preserved_value'])
    if expected['required_gap']:
        test.assertIn(expected['required_gap'], row['gaps'])
    if expected['required_unsupported']:
        test.assertIn(dict(field=expected['field'], reason=expected['required_unsupported']), result['unsupported_capabilities'])
    for k in ('authenticity_verified', 'opening_entitlements_verified', 'ledger_called', 'legacy_qualification_updates'):
        test.assertEqual(result[k], expected[k])
    return result


class OpeningEvidenceTests(unittest.TestCase):
    def test_empty_list_never_proves_zero(self):
        result=assert_saved(self,'empty-is-unknown')
        self.assertIsNone(result['fields'][PATH]['diagnostic_value'])

    def test_missing_declaration_is_not_default_zero(self):
        assert_saved(self,'missing-is-unknown')

    def test_sourced_zero_is_only_a_declaration(self):
        result=assert_saved(self,'sourced-zero')
        self.assertFalse(result['opening_entitlements_verified'])
        self.assertEqual(result['fields'][PATH]['diagnostic_value'],[])

    def test_hypothetical_zero_stays_an_assumption(self):
        result=assert_saved(self,'hypothetical-zero')
        self.assertIsNone(result['fields'][PATH]['diagnostic_value'])

    def test_account_and_scenario_evidence_cannot_be_borrowed(self):
        for name in ('wrong-account_id','wrong-scenario_id'):
            with self.subTest(name=name):assert_saved(self,name)

    def test_stock_and_price_identity_cannot_be_borrowed(self):
        for name in ('wrong-code','wrong-price_source_id','wrong-basis_id','wrong-adjustment_version'):
            with self.subTest(name=name):assert_saved(self,name)

    def test_incomplete_inventory_cannot_declare_zero(self):
        assert_saved(self,'incomplete-zero')

    def test_source_reference_cannot_describe_a_different_value(self):
        assert_saved(self,'content-conflict')

    def test_old_entitlement_survives_zero_current_holdings(self):
        result=assert_saved(self,'prior-right-without-holding')
        self.assertEqual(result['fields']['holdings.1101.shares']['diagnostic_value'],'0')
        self.assertEqual(result['fields'][PATH]['diagnostic_value'][0]['amount_net'],'9')
        self.assertEqual(result['cash_or_share_postings'],[])
        self.assertEqual(result['usable_cash'],'NOT_COMPUTED_NO_LEDGER_CALL')

    def test_late_proof_cannot_be_backdated_by_early_capture(self):
        data=saved('late-proof');data['sources']['fixture']['captured_at']='2026-01-02T16:10:00+08:00'
        assert_saved(self,'late-proof')
        self.assertIn('EVIDENCE_NOT_YET_AVAILABLE',check(data)['fields'][PATH]['gaps'])

    def test_equal_availability_and_equivalent_timezones(self):
        result=assert_saved(self,'equal-timezone-boundary')
        data=saved('equal-timezone-boundary');data['decision_at']='2026-01-02T09:00:00+00:00'
        data['evidence']['evidence:'+PATH]['as_of']='2026-01-02T08:00:00Z'
        other=check(data)
        self.assertEqual(result['fields'],other['fields'])
        self.assertEqual(result['status'],other['status'])

    def test_unknown_net_and_payment_date_are_preserved(self):
        result=assert_saved(self,'unknown-net-and-pay-date')
        self.assertIn('PAYMENT_DATE_UNKNOWN',result['fields'][PATH]['gaps'])
        self.assertIsNone(result['fields'][PATH]['declared_value'][0]['amount_net'])

    def test_unknown_share_dates_do_not_promote_delivery_or_sellability(self):
        result=assert_saved(self,'unknown-share-dates')
        row=result['fields']['entitlements.1101.share_claims']
        self.assertIn('TRADABLE_DATE_UNKNOWN',row['gaps'])
        self.assertIsNone(row['declared_value'][0]['tradable_date'])

    def test_fractional_right_is_retained_but_replay_not_implemented(self):
        assert_saved(self,'fractional-right')

    def test_opening_payables_and_external_orders_remain_unsupported(self):
        for name in ('nonempty-payables','nonempty-pending_orders'):
            with self.subTest(name=name):assert_saved(self,name)

    def test_future_entitlement_does_not_become_an_opening_right(self):
        assert_saved(self,'future-entitlement')

    def test_duplicate_right_identity_is_not_silently_deduplicated(self):
        result=assert_saved(self,'duplicate-right')
        self.assertIn('DUPLICATE_ACCOUNT_ITEM_ID',result['fields'][PATH]['gaps'])
        self.assertEqual(len(result['fields'][PATH]['declared_value']),1)

    def test_unknown_source_time_and_locator_fail_closed(self):
        for container,key in [('source','available_at'),('evidence','available_at'),('evidence','locator')]:
            data=saved('sourced-zero')
            row=data['sources']['fixture'] if container=='source' else data['evidence']['evidence:'+PATH]
            row[key]=None
            with self.subTest(container=container,key=key):
                self.assertEqual(check(data)['fields'][PATH]['classification'],'UNKNOWN')

    def test_invalid_quantity_and_month_only_date_are_not_filled(self):
        for value in ('NaN','-1','0.5',0,None):
            data=saved('sourced-zero');path='holdings.1101.shares'
            data['declarations'][path]['value']=value
            data['evidence']['evidence:'+path]['declared_value']=value
            with self.subTest(value=value):self.assertEqual(check(data)['fields'][path]['classification'],'UNKNOWN')
        data=saved('prior-right-without-holding');data['declarations'][PATH]['value'][0]['pay_date']='2026-01'
        data['evidence']['evidence:'+PATH]['declared_value']=deepcopy(data['declarations'][PATH]['value'])
        self.assertIn('PAYMENT_DATE_UNKNOWN',check(data)['fields'][PATH]['gaps'])

    def test_real_input_fake_verified_and_unbound_clocks_are_rejected(self):
        for mutation in ('real','verified','naive','cutoff'):
            data=saved('sourced-zero')
            if mutation=='real':data['synthetic']=False
            elif mutation=='verified':data['declarations'][PATH]['state']='VERIFIED'
            elif mutation=='naive':data['decision_at']='2026-01-02T17:00:00'
            else:data['data_cutoff']='2026-01-05T16:00:00+08:00'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):check(data)

    def test_no_mutation_determinism_and_no_automatic_authorization(self):
        data=saved('sourced-zero');original=deepcopy(data)
        first,second=check(data),check(data)
        self.assertEqual(data,original);self.assertEqual(first,second)
        for flag in ('data_qualified','execution_model_qualified','historical_signal_eligible',
                     'policy_authorized','live_execution_authorized','authenticity_verified','opening_entitlements_verified'):
            self.assertIs(first[flag],False)
        self.assertIsNone(first['primary_pressure_id'])
        self.assertEqual(first['legacy_qualification_updates'],{})


if __name__=='__main__':unittest.main()
