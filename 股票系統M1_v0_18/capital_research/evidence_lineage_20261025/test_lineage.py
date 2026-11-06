"""Fact continuity counterexamples; no real producer or strategy assessment."""
from copy import deepcopy
from decimal import Decimal
import json
import unittest
from graph_core.core import fingerprint
from capital_research.core import decide, resume_decision
from capital_research.execution import simulate
from capital_research.continuity import make_checkpoint
from capital_research.fact_lineage import history_at
from capital_research.repair_20261025.fixtures import advance, continuation_job
from .fixtures import EXPECTED, first_input, pair


def resume(job):
    c = job['continuation']
    return resume_decision(c['previous_decision'], job['decision_input'],
                           checkpoint=c['checkpoint'], cancelled_order_ids=c['cancelled_order_ids'])


def alias(job, *, keep_invalid=False):
    job = deepcopy(job); a = job['decision_input']['assets']['B']; f = a['evidence'][0]
    original = deepcopy(f); f['id'] = 'B-alias'
    f['fact_link'] = dict(schema='capital-fact-alias/0.1', code='B',
        **{k: a[k] for k in ('source_id','basis_id','adjustment_version')},
        target_id=original['id'], target_content_id=fingerprint(original),
        available_at=job['decision_input']['data_cutoff'], source_ids=['fixture'])
    a['capital_eligibility']['evidence_ids'] = [f['id']]
    return job


class FactLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = {name: pair(name, first_input(name)) for name in EXPECTED}

    def result(self, name):
        return resume(self.pairs[name]['next'])['decision']

    def test_known_revocation_cannot_disappear_into_a_new_review(self):
        job = self.pairs['drop-known-revocation']['next']; d = self.result('drop-known-revocation')
        self.assertFalse(d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        self.assertNotIn('E-partial', d['research_recommendation']['candidate_ids'])
        self.assertTrue(any('VALIDITY_REWRITE' in x for x in d['layer2']['B']['capital_eligibility']['reasons']))
        self.assertEqual(simulate(job)['fills'], [])

    def test_finite_expiry_cannot_be_removed_or_extended(self):
        for name in ('extend-expiry-to-null', 'extend-expiry-later'):
            d = self.result(name)
            self.assertFalse(d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
            self.assertTrue(any('HISTORY_EXPIRED' in x for x in d['layer2']['B']['capital_eligibility']['reasons']))
            self.assertEqual(simulate(self.pairs[name]['next'])['fills'], [])

    def test_explicit_alias_preserves_the_original_revocation(self):
        d = self.result('alias-drop-revocation'); h = d['fact_history']
        self.assertFalse(d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        roots = [r for r in h['roots'].values() if r['identity']['code']=='B' and r['identity']['kind']=='EVIDENCE']
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0]['fact']['validity']['invalidation']['evidence_id'], 'B-revocation-1')

    def test_renaming_without_removing_revocation_stays_rejected(self):
        self.assertFalse(self.result('rename-keep-revocation')['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        self.assertEqual(simulate(self.pairs['rename-keep-revocation']['next'])['status'], 'REFUSED')

    def test_valid_old_fact_keeps_identity_and_does_not_become_new_event(self):
        p = self.pairs['valid-old-fact']; d = self.result('valid-old-fact')
        self.assertTrue(d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        self.assertEqual(d['new_evidence_tokens'], [])
        self.assertEqual(d['fact_history'], p['first_decision']['decision']['fact_history'])
        self.assertEqual([f['shares'] for f in simulate(p['next'])['fills'] if f['side']=='BUY'], ['20'])

    def test_independent_new_fact_does_not_erase_or_inherit_old_invalidity(self):
        d = self.result('independent-new-fact'); roots = d['fact_history']['roots'].values()
        old = next(r for r in roots if r['identity']['code']=='B' and r['identity']['id']=='B-event')
        self.assertIsNotNone(old['fact']['validity']['invalidation'])
        self.assertTrue(d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        self.assertTrue(d['new_evidence_tokens'])
        self.assertEqual([f['shares'] for f in simulate(self.pairs['independent-new-fact']['next'])['fills'] if f['side']=='BUY'], ['20'])

    def test_future_revocation_is_absent_from_numeric_prefix_but_kept_in_integrity(self):
        p = self.pairs['future-revocation']; plain = deepcopy(p['first']['decision_input'])
        plain['assets']['B']['evidence'][0]['validity']['invalidation'] = None
        self.assertEqual(decide(plain)['decision'], p['first_decision']['decision'])
        self.assertNotIn('B-revocation-1', json.dumps(p['first_decision']['decision']))
        self.assertIn('B-revocation-1', json.dumps(p['first_execution']['fact_sources']))

    def test_revocation_applies_at_the_known_observation(self):
        out = simulate(self.pairs['future-revocation']['next'])
        self.assertEqual([f for f in out['fills'] if f['side']=='BUY'], [])
        self.assertEqual(out['order_states']['next-B-buy']['status'], 'CANCELLED_EVIDENCE')
        self.assertTrue(any(e['at']=='2026-01-09T09:01:00+08:00' and e['status']=='CANCELLED_EVIDENCE' for e in out['execution_events']))

    def test_prior_future_declaration_survives_a_review_that_omits_it(self):
        self.assertTrue(self.result('future-stripped-at-review')['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        out = simulate(self.pairs['future-stripped-at-review']['next'])
        self.assertEqual([f for f in out['fills'] if f['side']=='BUY'], [])
        self.assertEqual(out['order_states']['next-B-buy']['status'], 'CANCELLED_EVIDENCE')

    def test_known_revocation_also_cancels_at_watermark_without_later_market_tape(self):
        job = deepcopy(self.pairs['future-stripped-at-review']['next'])
        job['tape'] = job['tape'][:1]
        out = simulate(job)
        self.assertEqual(out['order_states']['next-B-buy']['status'], 'CANCELLED_EVIDENCE')
        self.assertTrue(any(e.get('reason')=='KNOWN_FACT_HISTORY_AT_WATERMARK' for e in out['execution_events']))

    def test_late_available_revocation_does_not_cancel_an_earlier_fill(self):
        first = first_input('future-revocation')
        first['decision_input']['assets']['B']['evidence'][0]['validity']['invalidation']['available_at'] = '2026-01-09T09:02:00+08:00'
        p = pair('future-stripped-at-review', first); out = simulate(p['next'])
        self.assertEqual([f['shares'] for f in out['fills'] if f['side']=='BUY'], ['20'])
        self.assertEqual(out['order_states']['next-B-buy']['status'], 'FILLED')

    def test_sourced_alias_of_valid_fact_is_not_an_independent_trigger(self):
        job = alias(self.pairs['valid-old-fact']['next']); d = resume(job)['decision']
        self.assertTrue(d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        self.assertEqual(d['new_evidence_tokens'], [])

    def test_alias_cannot_borrow_another_scope_or_unknown_content(self):
        for field, value in [('code','A'),('source_id','wrong'),('basis_id','wrong'),('adjustment_version','wrong'),('target_id','missing'),('target_content_id','wrong')]:
            job = alias(self.pairs['valid-old-fact']['next'])
            job['decision_input']['assets']['B']['evidence'][0]['fact_link'][field] = value
            self.assertFalse(resume(job)['decision']['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])

    def test_same_identity_content_rewrite_is_not_an_implicit_correction(self):
        job = deepcopy(self.pairs['valid-old-fact']['next'])
        job['decision_input']['assets']['B']['evidence'][0]['value'] = 'UNSOURCED_REWRITE'
        d = resume(job)['decision']
        self.assertTrue(any('CONTENT_REWRITE' in x for x in d['layer2']['B']['capital_eligibility']['reasons']))

    def test_identical_renamed_valid_fact_requires_explicit_link(self):
        job = deepcopy(self.pairs['valid-old-fact']['next']); a = job['decision_input']['assets']['B']
        a['evidence'][0]['id'] = 'renamed-without-proof'; a['capital_eligibility']['evidence_ids'] = ['renamed-without-proof']
        d = resume(job)['decision']
        self.assertFalse(d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        self.assertTrue(any('RENAME_LINK_REQUIRED' in x for x in d['layer2']['B']['capital_eligibility']['reasons']))

    def test_shared_bar_or_formation_does_not_merge_distinct_facts(self):
        job = deepcopy(self.pairs['independent-new-fact']['next']); a = job['decision_input']['assets']['B']
        a['evidence'][1].update(formation_id='B-formation', volume_bar_id='B-bar')
        d = resume(job)['decision']
        self.assertTrue(d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        self.assertEqual(d['new_evidence_tokens'], [])
        self.assertEqual(len([r for r in d['fact_history']['roots'].values() if r['identity']['code']=='B' and r['identity']['kind']=='EVIDENCE']), 2)

    def test_missing_fact_identity_and_unsupported_correction_fail_closed(self):
        job = deepcopy(self.pairs['valid-old-fact']['next']); job['decision_input']['assets']['B']['evidence'][0].pop('id')
        with self.assertRaisesRegex(ValueError, 'FACT_IDENTITY_REQUIRED'): resume(job)
        job = deepcopy(self.pairs['valid-old-fact']['next'])
        job['decision_input']['assets']['B']['evidence'][0]['fact_correction'] = dict(available_at=job['decision_input']['data_cutoff'], source_ids=['fixture'])
        d = resume(job)['decision']
        self.assertTrue(any('CORRECTION_NOT_IMPLEMENTED' in x for x in d['layer2']['B']['capital_eligibility']['reasons']))

    def test_entry_and_reference_snapshot_validity_cannot_be_reset(self):
        for reference in (False, True):
            first = first_input('valid-old-fact'); entry = first['decision_input']['assets']['B']['entry_context']
            target = entry['formal_reference'] if reference else entry
            target['validity']['valid_until'] = '2026-01-07T16:00:00+08:00'
            p = pair('valid-old-fact', first); fresh = p['next']['decision_input']['assets']['B']['entry_context']
            target = fresh['formal_reference'] if reference else fresh; target['validity']['valid_until'] = None
            self.assertFalse(resume(p['next'])['decision']['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])

    def test_rehashed_prior_declaration_edit_cannot_match_decision_history(self):
        p = self.pairs['drop-known-revocation']; r = deepcopy(p['first_execution'])
        source = r['fact_sources'][r['decision_id']]
        fact = next(x['fact'] for x in source['records'] if x['identity']['code']=='B' and x['identity']['kind']=='EVIDENCE')
        fact['validity']['invalidation'] = None
        r['result_id'] = fingerprint({k:v for k,v in r.items() if k!='result_id'})
        with self.assertRaisesRegex(ValueError, 'Fact history differs'):
            make_checkpoint(p['first']['ledger_input'], r, through_at=r['observed_until'])

    def test_dropping_one_round_of_raw_declarations_is_refused(self):
        p = self.pairs['valid-old-fact']; r = simulate(p['next']); r['fact_sources'].pop(r['decision_ids'][0])
        r['result_id'] = fingerprint({k:v for k,v in r.items() if k!='result_id'})
        with self.assertRaisesRegex(ValueError, 'Complete fact declaration history'):
            make_checkpoint(p['first']['ledger_input'], r, through_at=r['observed_until'])

    def test_rounds_keep_capital_claims_fills_reserve_and_all_tokens(self):
        p = self.pairs['valid-old-fact']; r = simulate(p['next'])
        self.assertEqual(r['ledger']['initial_equity'], '2180')
        self.assertEqual(r['fills'][:len(p['first_execution']['fills'])], p['first_execution']['fills'])
        cp = make_checkpoint(p['first']['ledger_input'], r, through_at=r['observed_until'])
        self.assertEqual(cp['state']['general_reserved_cash'], '100')
        self.assertEqual(cp['state']['row']['shares']['A'], '60')
        self.assertTrue(set(p['first_decision']['decision']['reviewed_evidence_tokens']) <= set(r['reviewed_evidence_tokens']))
        for row in r['ledger']['daily']:
            rights = {c:sum(Decimal(x['shares']) for x in row['share_receivables'] if x['code']==c) for c in row['shares']}
            nav = Decimal(row['settled_cash']) + Decimal(row['cash_receivable']) - Decimal(row['purchase_payable'])
            nav += sum((Decimal(n)+rights[c])*Decimal(row['marks'][c]['value']) for c,n in row['shares'].items())
            self.assertEqual(nav, Decimal(row['net_accrual_equity']))

    def test_omitting_a_fact_in_the_middle_round_does_not_drop_old_revocation(self):
        p = self.pairs['drop-known-revocation']; job = deepcopy(p['next'])
        job.update(plan_id='A-zero', orders=[])
        a = job['decision_input']['assets']['B']; a['evidence'] = []
        a['capital_eligibility'].update(status='UNKNOWN', evidence_ids=[])
        r = simulate(job); cp = make_checkpoint(job['ledger_input'], r, through_at=r['observed_until'])
        fresh, ids = advance(job['decision_input'], cp)
        a = fresh['assets']['B']; fact = deepcopy(p['first']['decision_input']['assets']['B']['evidence'][0])
        fact['validity']['invalidation'] = None; a['evidence'] = [fact]
        a['capital_eligibility'].update(status='QUALIFIED_SYNTHETIC_RESEARCH', evidence_ids=[fact['id']])
        old = dict(decision=r['decision_records'][r['latest_decision_id']])
        d = resume_decision(old, fresh, checkpoint=cp, cancelled_order_ids=ids)['decision']
        self.assertFalse(d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])

    def test_rejected_rewrite_does_not_permanently_taint_unchanged_valid_fact(self):
        p = self.pairs['valid-old-fact']; job = deepcopy(p['next'])
        job.update(plan_id='A-zero', orders=[])
        job['decision_input']['assets']['B']['evidence'][0]['value'] = 'REJECT_THIS_REWRITE'
        r = simulate(job); cp = make_checkpoint(job['ledger_input'], r, through_at=r['observed_until'])
        fresh, ids = advance(job['decision_input'], cp)
        fresh['assets']['B']['evidence'][0]['value'] = p['first']['decision_input']['assets']['B']['evidence'][0]['value']
        old = dict(decision=r['decision_records'][r['latest_decision_id']])
        d = resume_decision(old, fresh, checkpoint=cp, cancelled_order_ids=ids)['decision']
        self.assertTrue(d['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])

    def test_later_revocation_cannot_replace_earlier_expiry_without_tape(self):
        job = deepcopy(self.pairs['future-stripped-at-review']['next']); job['tape'] = []
        buy = next(o for o in job['orders'] if o['side']=='BUY')
        buy['expires_at'] = '2026-01-09T08:59:00+08:00'
        out = simulate(job)
        self.assertEqual(out['order_states'][buy['id']]['status'], 'EXPIRED_UNFILLED')

    def test_no_tape_revocation_records_effective_and_observed_times_separately(self):
        job = deepcopy(self.pairs['future-stripped-at-review']['next']); job['tape'] = []
        out = simulate(job)
        event = next(e for e in out['execution_events'] if e['order_id']=='next-B-buy' and e['status']=='CANCELLED_EVIDENCE')
        self.assertEqual(event['at'], '2026-01-09T09:01:00+08:00')
        self.assertEqual(event['observed_at'], job['observed_until'])


if __name__ == '__main__': unittest.main()
