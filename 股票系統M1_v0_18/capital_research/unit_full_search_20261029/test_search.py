"""Targeted mechanism tests; saved inputs/expected are immutable oracles."""
from copy import deepcopy
from decimal import Context,Decimal,ROUND_UP,Inexact,Rounded,localcontext
import hashlib,json,os,socket
from unittest import TestCase
from unittest.mock import patch
from capital_research import quantity_candidates as qc,allocation
from .freeze import ROOT,REPO,PROJECT,load,save,info

STAGE=os.environ.get('UNIT_FULL_STAGE','actual')
OUT=os.environ.get('UNIT_FULL_TEST_STAGE','validation')
def request(name):return load(ROOT/'cases'/name/'input.json')
def actual(name):return load(ROOT/STAGE/name/'actual.json')
def research(name):return actual(name)['result']['research']
def full(r):return next(c for c in r['candidates'] if 'FULL_TRANSFER' in c['kinds'])

class UnitFullSearch(TestCase):
    def test_frozen_sources_and_saved_expectations(self):
        for row in load(ROOT/'frozen.json')['files']:self.assertEqual(info(REPO/row['path']),row)
        intake=load(ROOT/'intake.json')
        for row in intake['protected']+intake['source_originals']:self.assertEqual(info(REPO/row['path']),row)
        for row in load(ROOT/STAGE/'source-versions.json')['files']:self.assertEqual(info(REPO/row['path']),row)
        for name in load(ROOT/'case-index.json')['cases']:
            with self.subTest(name=name):
                e=load(ROOT/'cases'/name/'expected.json');a=actual(name);self.assertTrue(a['input_unchanged'])
                if e['status']=='VALUE_ERROR':
                    self.assertEqual(a['status'],'VALUE_ERROR');self.assertEqual(a['core_evaluations'],0);continue
                r=a['result']['research'];self.assertEqual(r['status'],e['status'])
                receipt=r['full_search_receipt']
                for key in ('full_status','target_B','classification','probe_count','legal_count','probes'):
                    if key not in e:continue
                    v={'full_status':r['full_proposal_status'],'target_B':(receipt['selected_target'] or {}).get('B'),
                        'classification':full(r)['classification'] if r['candidates'] else None,'probe_count':receipt['probe_count'],
                        'legal_count':receipt['legal_candidate_count'],'probes':[p['targets']['B'] for p in receipt['probe_trace']]}[key]
                    self.assertEqual(v,e[key])
                if 'same_research_as' in e:self.assertEqual(r,research(e['same_research_as']))

    def test_manual_funding_and_legal_trace(self):
        r=research('manual-93');c=full(r);x=c['core_evaluation'];receipt=r['full_search_receipt']
        self.assertEqual(x['available_settled_cash'],'900')
        self.assertEqual(Decimal(x['sale_receivable_estimate']),Decimal('995'))
        self.assertEqual(Decimal(x['purchase_payable_estimate']),Decimal('1863.86'))
        self.assertEqual(Decimal('900')+Decimal(x['sale_receivable_estimate']),Decimal('1895'))
        self.assertLess(Decimal('1895'),Decimal('1923.92'))
        self.assertEqual(x['funding'],'WAIT_SALE_SETTLEMENT_AND_REEVALUATE')
        self.assertTrue(c['feasible_for_research']);self.assertEqual(c['plan']['targets'],dict(A='0',B='93',C='2'))
        self.assertEqual(len(receipt['probe_trace']),7)
        self.assertTrue(all(not p['feasible_for_research'] for p in receipt['probe_trace'][:-1]))
        self.assertTrue(all('JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS' in p['reasons'] for p in receipt['probe_trace'][:-1]))
        self.assertIsNone(r['selected_id']);self.assertIsNone(r['ranking'])

    def test_nonmonotone_and_complete_outer_gate(self):
        r=research('non-monotone');expected=load(ROOT/'cases/non-monotone/expected.json')['grid_classes']
        seen={c['additional_B']:c['classification'] for c in r['candidates'] if c.get('in_explicit_grid')}
        self.assertEqual(seen,expected);self.assertEqual(full(r)['plan']['targets']['B'],'2')
        r=research('outer-unknown');self.assertEqual(r['full_proposal_status'],'NO_FEASIBLE_TARGET')
        self.assertIsNone(full(r)['plan'])
        for c in r['candidates']:
            if c['plan'] and int(c['additional_B'])>0:
                self.assertIn('BATCH_PHASE_UNKNOWN',c['reasons']);self.assertFalse(c['feasible_for_research'])
        # UNKNOWN intentionally uses the additional-batch C gate, not first-entry E.
        # The same financial quantities pass the explicit FIRST_ENTRY positive;
        # UNKNOWN must keep both the missing trigger and outer phase refusal.
        core=[c for c in r['candidates'] if c.get('in_explicit_grid') and c['additional_B'] in ('1','2')]
        self.assertEqual(len(core),2)
        self.assertTrue(all('NO_NEW_INDEPENDENT_TRIGGER' in c['core_evaluation']['reasons'] for c in core))
        self.assertTrue(all('BATCH_PHASE_UNKNOWN' in p['reasons'] for p in r['full_search_receipt']['probe_trace'] if int(p['additional_B'])>0))

    def test_increment_units_trigger_history_and_account(self):
        r=research('existing-B3');c=full(r)
        self.assertEqual(c['plan']['targets']['B'],'97');self.assertEqual(c['additional_B'],'94')
        self.assertTrue(all((int(p['targets']['B'])-3)%2==0 for p in r['full_search_receipt']['probe_trace']))
        r=research('additional-old-trigger');self.assertEqual(r['full_proposal_status'],'FOUND_ZERO_ADDITION')
        self.assertEqual(full(r)['additional_B'],'0')
        self.assertTrue(all('NO_NEW_INDEPENDENT_TRIGGER' in p['reasons'] for p in r['full_search_receipt']['probe_trace'] if int(p['additional_B'])>0))
        rows=[]
        for name in ('additional-independent','first-old-fact-reviewed','additional-old-trigger'):
            req=request(name);before=deepcopy(req);result=qc.generate(req);self.assertEqual(result,actual(name)['result']);self.assertEqual(req,before)
            r=result['research'];base=r['baseline'];cp=req['continuation']['checkpoint'];previous=req['continuation']['previous_decision']['decision']
            self.assertEqual(base['common_account_id'],qc.fingerprint(req['decision_input']['account']))
            self.assertTrue(set(previous['reviewed_evidence_tokens'])<=set(base['reviewed_evidence_tokens']))
            self.assertTrue(set(cp['state']['reviewed_evidence_tokens'])<=set(base['reviewed_evidence_tokens']))
            self.assertEqual(base['continuity']['latest_predecessor_id'],previous['decision_id'])
            self.assertEqual(cp['origin_ledger_input'],before['continuation']['checkpoint']['origin_ledger_input'])
            if name!='additional-old-trigger':self.assertTrue(full(r)['feasible_for_research']);self.assertGreater(int(full(r)['additional_B']),0)
            if name=='first-old-fact-reviewed':self.assertEqual(base['new_evidence_tokens'],[])
            rows.append(dict(case=name,common_account_id=base['common_account_id'],checkpoint_id=cp['checkpoint_id'],
                previous_decision_id=previous['decision_id'],opening=cp['origin_ledger_input']['opening'],
                all_tokens=base['reviewed_evidence_tokens'],account=req['decision_input']['account']))
        save(ROOT/OUT/'continuity.json',dict(rows=rows,new_account_or_postings=False,original_ledger_validation_reused=True))

    def test_limits_preconditions_and_unknown_higher_point(self):
        r=research('search-limit');self.assertEqual(r['candidates'],[]);self.assertFalse(r['enumeration_complete']);self.assertEqual(r['full_search_receipt']['probe_count'],0)
        self.assertEqual(actual('search-limit')['core_evaluations'],1) # Baseline is needed to obtain NAV bound.
        for name,status in [('full-A-unit-mismatch','REJECTED_DOMAIN'),('not-fully-sellable','REJECTED_PRECONDITION')]:
            r=research(name);self.assertEqual(r['full_proposal_status'],status);self.assertIsNone(full(r)['plan'])
        req=request('manual-93');base=research('manual-93')['baseline'];d=req['decision_input'];seen=[]
        def unsupported(targets):
            seen.append(targets)
            return dict(additional_B=targets['B'],classification='NOT_IMPLEMENTED',feasible_for_research=False,
                reasons=['EXPLICIT_TEST_UNSUPPORTED_HIGHER_POINT'],core_decision_id='synthetic-control')
        _,receipt=allocation._unit_full_search(d,'A','B',baseline=base,units={'A':2,'B':3},max_probes=128,probe=unsupported)
        self.assertEqual(receipt['status'],'NOT_IMPLEMENTED');self.assertEqual(len(seen),1);self.assertIsNone(receipt['selected_target'])
        with patch.object(qc,'_evaluate',side_effect=AssertionError('No baseline for malformed policy')):
            for value in ('0','-1','1.5',None,True):
                bad=deepcopy(req);bad['full_search']['max_probes']=value
                with self.assertRaises(ValueError):qc.generate(bad)
        bad=deepcopy(req);bad['full_search']['max_probes']='20001';r=qc.generate(bad)['research']
        self.assertEqual(r['status'],'REFUSED_SEARCH_LIMIT');self.assertEqual(r['full_search_receipt']['probe_count'],0)
        for path in [('batch_context','account_id'),('quantity_domain','account_id')]:
            bad=deepcopy(req);bad[path[0]][path[1]]='wrong'
            with self.assertRaises(ValueError):qc.generate(bad)
        save(ROOT/OUT/'unsupported-higher.json',receipt)

    def test_cost_capacity_risk_reserve_and_rejected_buy(self):
        for name in ('liquidity-limit','common-risk-limit','cost-cannot-be-free'):
            r=research(name)
            for c in r['candidates']:
                if not c['plan']:continue
                self.assertEqual(c['feasible_for_research'],c['core_evaluation']['feasible'] and not c['batch_gate_reasons'])
            receipt=r['full_search_receipt']
            for p in receipt['probe_trace'][:-1]:self.assertFalse(p['feasible_for_research'])
            if receipt['selected_target']:
                c=full(r);self.assertTrue(c['core_evaluation']['feasible']);self.assertFalse(c['batch_gate_reasons'])
        req=request('manual-93');req['decision_input']['account']['reserved_cash']='950'
        req['batch_context']['account_id']=qc.fingerprint(req['decision_input']['account']);req['quantity_domain']['account_id']=req['batch_context']['account_id']
        r=qc.generate(req)['research'];self.assertLess(int(full(r)['additional_B']),93)
        self.assertEqual(r['baseline']['common_account_id'],qc.fingerprint(req['decision_input']['account']))
        # Actual full gate must reject a known unqualified new-capital review.
        req=request('manual-93');req['batch_context']['phase']='UNKNOWN';r=qc.generate(req)['research']
        self.assertTrue(all(not p['feasible_for_research'] for p in r['full_search_receipt']['probe_trace'] if int(p['additional_B'])>0))
        save(ROOT/OUT/'high-reserve.json',r)

    def test_legacy_exact_compatibility(self):
        for version in ('0.1','0.2','0.3'):
            prior=load(ROOT/'legacy'/version/'before.json');current=load(ROOT/STAGE/'legacy'/version/'actual.json')
            self.assertEqual(current,prior)
        # The original standalone builder is unchanged in meaning, too.
        req=request('manual-93');d=deepcopy(req['decision_input']);d['full_transfer_edge_budget']=req['policy']['edge_budget']
        self.assertEqual(allocation.full_transfer(d,incumbent='A',destination='B')['targets']['B'],'94')

    def test_future_decimal_purity_and_no_execution(self):
        req=request('manual-93');before=deepcopy(req);expected=actual('manual-93')['result']
        with (patch('socket.socket',side_effect=AssertionError('No network')),
              patch('capital_research.execution.simulate',side_effect=AssertionError('No execution'))):
            self.assertEqual(qc.generate(req),expected)
        self.assertEqual(req,before)
        for name in ('future-A-wins','future-B-wins','future-both-fall'):
            self.assertEqual(research(name),expected['research'])
            self.assertNotEqual(actual(name)['result']['source_integrity_metadata'],expected['source_integrity_metadata'])
        with localcontext(Context(prec=3,rounding=ROUND_UP,Emin=-2,Emax=2,clamp=1)) as ambient:
            ambient.traps[Inexact]=True;ambient.traps[Rounded]=True
            old=deepcopy(ambient);self.assertEqual(qc.generate(req),expected)
            self.assertEqual(str(ambient),str(old))
        for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'):
            self.assertIs(expected['research'][k],False)
        self.assertIsNone(expected['research']['primary_pressure_id'])
        save(ROOT/OUT/'controls.json',dict(future_paths=3,decimal_context_preserved=True,input_unchanged=True,
            new_execution_calls=0,network_calls=0,original_market_samples=0,ranking=None))
