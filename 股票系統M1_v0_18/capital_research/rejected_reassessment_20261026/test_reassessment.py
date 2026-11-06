"""Only directed rejected-review cases; no external data or strategy tests."""
from copy import deepcopy
import unittest
from graph_core.core import fingerprint
from capital_research.core import decide, resume_decision
from capital_research.execution import simulate
from capital_research.continuity import make_checkpoint, validate_checkpoint
from capital_research.repair_20261025.fixtures import advance
from capital_research.reassessment_history import declaration_sources
from capital_research.fact_lineage import history_at
from .fixtures import specification, materialize, observed


class RejectedReassessmentTests(unittest.TestCase):
    cache = {}

    def case(self, name):
        if name not in self.cache:
            self.cache[name] = materialize(specification(name))
        return self.cache[name]

    def test_rejected_restriction_survives_restore_with_current_review(self):
        r=self.case('restrictive-unfilled');a=observed(r)
        self.assertFalse(a['review_feasible'])
        self.assertTrue(a['review_restriction_conflicts'])
        self.assertFalse(a['restored_B_qualified'])
        self.assertNotIn('E-partial',a['restored_candidate_ids'])
        self.assertTrue(r['restored']['decision']['fact_history']['restriction_conflicts'])

    def test_pre_funded_buy_is_blocked_on_the_review_observation(self):
        r=self.case('restrictive-funded-fill');a=observed(r)
        self.assertEqual(a['B_fill_shares'],'0')
        self.assertEqual(a['order_state']['status'],'CANCELLED_EVIDENCE')
        self.assertFalse(a['order_state']['requires_reassessment'])

    def test_refused_review_is_audited_once_without_promoting_latest(self):
        r=self.case('restrictive-unfilled');e=r['execution']
        self.assertEqual(len(e['reassessment_attempts']),1)
        attempt=e['reassessment_attempts'][0]
        self.assertEqual(attempt['outcome'],'REJECTED')
        self.assertEqual(attempt['decision'],r['proposed']['decision'])
        self.assertNotIn(r['proposed']['decision']['decision_id'],e['decision_ids'])
        self.assertEqual(e['latest_decision_id'],r['initial']['decision']['decision_id'])
        self.assertEqual(e['reassessments'],[])

    def test_rejected_value_only_edit_does_not_cancel_valid_old_order(self):
        r=self.case('value-only-rejection');a=observed(r)
        self.assertFalse(a['review_feasible'])
        self.assertEqual(a['B_fill_shares'],'20')
        self.assertEqual(r['execution']['latest_decision_id'],r['initial']['decision']['decision_id'])
        self.assertEqual(len(r['execution']['reassessment_attempts']),1)

    def test_valid_review_can_authorize_the_existing_order(self):
        r=self.case('valid-review');a=observed(r)
        self.assertTrue(a['review_feasible']);self.assertEqual(a['B_fill_shares'],'20')
        self.assertEqual(r['execution']['latest_decision_id'],r['proposed']['decision']['decision_id'])
        self.assertEqual(len(r['execution']['reassessments']),1)

    def test_conditional_buy_never_falls_back_to_old_authorization(self):
        r=self.case('conditional-rejection');a=observed(r)
        self.assertFalse(a['review_feasible']);self.assertEqual(a['B_fill_shares'],'0')
        self.assertTrue(a['order_state']['requires_reassessment'])

    def test_future_restriction_cannot_change_early_numeric_prefix(self):
        r=self.case('future-prefix');spec=specification('future-prefix')
        spec['edit']['future_invalidation']=None
        plain=materialize(spec)
        self.assertEqual(r['proposed']['decision'],plain['proposed']['decision'])
        e=r['execution'];base=plain['execution']
        sources=declaration_sources(e)
        self.assertEqual(history_at(sources,e['observed_until']),
            history_at(declaration_sources(base),base['observed_until']))
        self.assertNotEqual(e['reassessment_attempts'],base['reassessment_attempts'])
        self.assertEqual(e['order_states'],base['order_states'])
        self.assertEqual(e['fills'],[])

    def test_future_restriction_applies_at_known_time_and_is_not_retried(self):
        e=self.case('future-known')['execution']
        self.assertEqual(e['fills'],[])
        self.assertEqual(len(e['reassessment_attempts']),1)
        event=next(x for x in e['execution_events'] if x['status']=='CANCELLED_EVIDENCE')
        self.assertEqual(event['at'],'2026-01-12T09:01:00+08:00')
        self.assertEqual(event['observed_at'],event['at'])
        self.assertEqual(e['order_states']['B-buy']['reserved_cash'],'0')

    def test_partial_fill_survives_later_conflict_and_settles_once(self):
        r=self.case('future-partial');e=r['execution']
        self.assertEqual([f['shares'] for f in e['fills']],['7'])
        self.assertEqual(e['fills'][0]['date'],'2026-01-09')
        self.assertEqual(e['order_states']['B-buy']['remaining'],'13')
        self.assertEqual(e['order_states']['B-buy']['status'],'CANCELLED_EVIDENCE')
        cp=make_checkpoint(specification('future-partial')['first_input']['ledger_input'],e,through_at=e['observed_until'])
        validate_checkpoint(cp)
        row=cp['state']['row']
        self.assertEqual(row['purchase_payable'],'0')
        self.assertEqual(row['shares'],dict(A='110',B='7',C='0'))
        self.assertEqual(row['settled_cash'],'938.860')
        self.assertEqual(cp['state']['general_reserved_cash'],'100')

    def test_receipt_availability_does_not_backdate_received_conflicts(self):
        e=self.case('restrictive-unfilled')['execution'];sources=declaration_sources(e)
        early=history_at(sources,'2026-01-09T09:00:59+08:00')
        known=history_at(sources,'2026-01-09T09:01:00+08:00')
        self.assertFalse(early['restriction_conflicts'])
        self.assertTrue(known['restriction_conflicts'])

    def test_restored_conflict_does_not_poison_A_or_independent_B_fact(self):
        r=self.case('restrictive-unfilled')
        self.assertTrue(r['restored']['decision']['layer2']['A']['capital_eligibility']['qualified_for_synthetic_proposal'])
        origin=specification('restrictive-unfilled')['first_input'];e=r['execution']
        cp=make_checkpoint(origin['ledger_input'],e,through_at=e['observed_until'])
        fresh,ids=advance(origin['decision_input'],cp)
        a=fresh['assets']['B'];fact=deepcopy(a['evidence'][0])
        fact.update(id='B-independent',event_id='B-independent-event',formation_id='B-independent-formation',
            volume_bar_id='B-independent-bar',value='EXPLICIT_NEW_INDEPENDENT_REPAIR',
            occurred_at=fresh['data_cutoff'],available_at=fresh['data_cutoff'])
        fact['validity'].update(valid_from=fresh['data_cutoff'],available_at=fresh['data_cutoff'])
        a['evidence']=[fact];a['capital_eligibility']['evidence_ids']=[fact['id']]
        d=resume_decision(r['initial'],fresh,checkpoint=cp,cancelled_order_ids=ids)['decision']
        self.assertTrue(d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        self.assertIn('E-partial',d['research_recommendation']['candidate_ids'])
        self.assertTrue(d['fact_history']['restriction_conflicts'])

    def test_checkpoint_keeps_original_account_rights_and_all_review_tokens(self):
        r=self.case('restrictive-unfilled');e=r['execution'];origin=specification('restrictive-unfilled')['first_input']['ledger_input']
        cp=make_checkpoint(origin,e,through_at=e['observed_until']);validate_checkpoint(cp)
        self.assertEqual(cp['origin_ledger_input'],origin)
        self.assertEqual(cp['state']['origin_initial_capital'],'2180')
        self.assertEqual(cp['state']['general_reserved_cash'],'100')
        self.assertEqual(cp['state']['accepted_fills'],[])
        self.assertEqual(cp['state']['row']['settled_cash'],'1000')
        self.assertEqual(cp['state']['row']['cash_receivable'],'80')
        self.assertEqual(cp['state']['latest_decision_id'],r['initial']['decision']['decision_id'])
        tokens=set(e['reviewed_evidence_tokens'])
        for d in [r['initial']['decision'],r['proposed']['decision']]:
            self.assertTrue(set(d['reviewed_evidence_tokens'])<=tokens)
        self.assertTrue(tokens<=set(r['restored']['decision']['reviewed_evidence_tokens']))
        self.assertTrue(cp['state']['fact_history']['restriction_conflicts'])

    def test_checkpoint_rejects_changed_receipt_and_dropped_receipt(self):
        e=deepcopy(self.case('restrictive-unfilled')['execution'])
        origin=specification('restrictive-unfilled')['first_input']['ledger_input']
        e['reassessment_attempts'][0]['fact_source']['records'][0]['fact']['available_at']='2026-01-01T00:00:00+08:00'
        e['result_id']=fingerprint({k:v for k,v in e.items() if k!='result_id'})
        with self.assertRaisesRegex(ValueError,'attempt fingerprint conflict'):
            make_checkpoint(origin,e,through_at=e['observed_until'])
        e=deepcopy(self.case('restrictive-unfilled')['execution']);e['reassessment_attempts']=[]
        e['result_id']=fingerprint({k:v for k,v in e.items() if k!='result_id'})
        with self.assertRaisesRegex(ValueError,'lost its reassessment receipt'):
            make_checkpoint(origin,e,through_at=e['observed_until'])

    def test_rejected_plan_newly_reviewed_token_is_not_dropped_or_authorized(self):
        spec=specification('restrictive-unfilled');spec['edit']['independent_C_token']=True
        r=materialize(spec);e=r['execution'];token='fixture:event_id:C-observed-new'
        self.assertIn(token,r['proposed']['decision']['reviewed_evidence_tokens'])
        self.assertIn(token,e['reviewed_evidence_tokens'])
        self.assertNotIn(token,e['decision_records'][e['latest_decision_id']]['reviewed_evidence_tokens'])
        self.assertIn(token,r['restored']['decision']['reviewed_evidence_tokens'])
        self.assertNotIn(token,r['restored']['decision']['new_evidence_tokens'])
        self.assertEqual(e['fills'],[])

    def test_old_06_result_is_readable_but_cannot_be_implicitly_resumed(self):
        from pathlib import Path
        import json
        saved=json.loads((Path(__file__).parent/'before-final/restrictive-unfilled/execution-actual.json').read_text())
        self.assertEqual(saved['schema'],'capital-execution/0.6')
        origin=specification('restrictive-unfilled')['first_input']['ledger_input']
        with self.assertRaisesRegex(ValueError,'LIFECYCLE_PROOF_REQUIRED'):
            make_checkpoint(origin,saved,through_at=saved['observed_until'])


if __name__=='__main__':unittest.main()
