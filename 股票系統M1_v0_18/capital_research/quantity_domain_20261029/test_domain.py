"""New unit-domain mechanism, saved manual grid and focused compatibility only."""
from copy import deepcopy
import decimal,json,os,subprocess,sys,unittest
from unittest.mock import patch
from .freeze import ROOT,PROJECT,REPO,load,save,info
from .build import normalize
from capital_research.lifecycle import FLAGS,_fp

OUT=ROOT/os.environ.get('QUANTITY_DOMAIN_TEST_STAGE','validation')
def request(name):return load(ROOT/'cases'/name/'input.json')
def actual(name):return load(ROOT/'final'/name/'actual.json')
def grid(r):return sorted([c['sold_A'],c['additional_B']] for c in r['candidates'] if c.get('in_explicit_grid'))


class UnitDomainTests(unittest.TestCase):
    def test_01_frozen_sources_and_diagnosed_fixture_preserved(self):
        intake=load(ROOT/'intake.json')
        for m in load(ROOT/'frozen.json')['files']+intake['protected']+intake['source_originals']+load(ROOT/'final/source-versions.json')['files']:
            self.assertEqual(info(REPO/m['path']),m)
        for pair in intake['changing_sources']:self.assertEqual(info(REPO/pair['archived']['path']),pair['archived'])
        rows=load(ROOT/'final/summary.json')['cases'];bad=[r['name'] for r in rows if not r['matched']]
        self.assertEqual(bad,['existing-B3-add2'])
        self.assertEqual(load(ROOT/'cases/existing-B3-add2/expected.json')['status'],'COMPLETE')
        self.assertIn('authoritative cash, rights, holdings or orders',actual('existing-B3-add2')['error'])
        self.assertTrue(all(r['input_unchanged'] and r['readback_equal'] for r in rows))
        for row in rows:
            a=actual(row['name'])
            if a['research'] is not None:
                r=a['research'];self.assertTrue(all(r[k] is False for k in FLAGS));self.assertIsNone(r['selected_id']);self.assertIsNone(r['ranking']);self.assertIsNone(r['primary_pressure_id'])
                self.assertEqual(r['order_generation'],'NOT_PERFORMED');self.assertEqual(r['execution'],'NOT_PERFORMED')
        save(OUT/'preservation.json',dict(frozen_and_originals_unchanged=True,diagnosed_fixture_not_silently_marked_passed=True,production_account_guard_unchanged=True))

    def test_02_manual_exhaustive_grid_1000_and_empty_domains(self):
        rows=[]
        for name in ('manual-grid','retain-existing-odd-shares','explicit-1000-no-partial','empty-grid'):
            r=actual(name)['research'];e=load(ROOT/'cases'/name/'expected.json')
            self.assertEqual(grid(r),sorted(e['grid']),name);self.assertEqual(r['grid_points'],e['grid_points']);self.assertTrue(r['enumeration_complete'])
            self.assertEqual(r['domain_axes']['sell_A']['count']*r['domain_axes']['additional_B']['count'],r['grid_points'])
            self.assertEqual(r['quantity_domain_id'],_fp(request(name)['quantity_domain']))
            if 'raw_points' in e:self.assertEqual(r['raw_integer_grid_points'],e['raw_points'])
            if e.get('no_strict_partial_A'):self.assertFalse(r['quantity_domain_diagnostics']['has_strict_partial_A_sale'])
            if e.get('grid_empty'):
                self.assertTrue(r['quantity_domain_diagnostics']['grid_empty']);self.assertIn('NO_LEGAL_GRID_QUANTITIES_IN_EXPLICIT_BOUNDS',r['domain_reasons'])
                self.assertTrue(any('HOLD' in c['kinds'] for c in r['candidates']))
            rows.append(dict(name=name,manual_pairs=e['grid'],complete=True,not_a_strategy_comparison=True))
        save(OUT/'manual-grid.json',rows)

    def test_03_every_endpoint_has_the_same_delta_unit_gate(self):
        for name in ('manual-grid','full-unit-mismatch','exit-unit-mismatch','retain-existing-odd-shares','explicit-1000-no-partial','empty-grid'):
            q=request(name);r=actual(name)['research'];a,b=q['incumbent'],q['destination'];opening=q['decision_input']['account']['holdings'];ua=int(q['quantity_domain']['assets'][a]['unit_shares']);ub=int(q['quantity_domain']['assets'][b]['unit_shares'])
            for c in r['candidates']:
                if c['plan'] is None:
                    self.assertFalse(c['feasible_for_research']);self.assertEqual(c['classification'],'NOT_IMPLEMENTED');continue
                sold=int(opening[a]['shares'])-int(c['plan']['targets'][a]);added=int(c['plan']['targets'][b])-int(opening[b]['shares'])
                legal=sold%ua==0 and added%ub==0
                self.assertEqual(not c['unit_gate_reasons'],legal)
                if not legal:self.assertFalse(c['feasible_for_research']);self.assertEqual(c['classification'],'REJECTED')
                for code in set(opening)-{a,b}:self.assertEqual(c['plan']['targets'][code],opening[code]['shares'])
            hold=next(c for c in r['candidates'] if 'HOLD' in c['kinds']);self.assertEqual(hold['unit_gate_reasons'],[])
        r=actual('manual-grid')['research'];self.assertEqual(r['full_proposal_status'],'LEGACY_ENDPOINT_IN_DECLARED_DOMAIN')
        r=actual('full-unit-mismatch')['research'];full=next(c for c in r['candidates'] if 'FULL_TRANSFER' in c['kinds'])
        self.assertEqual(full['classification'],'NOT_IMPLEMENTED');self.assertIsNone(full['plan']);self.assertEqual(full['legacy_full_endpoint']['targets']['B'],'94')
        self.assertIn('BUY_QUANTITY_OUTSIDE_DECLARED_UNIT:B',full['unit_gate_reasons'])
        exit=next(c for c in actual('exit-unit-mismatch')['research']['candidates'] if 'EXIT_A_KEEP_CASH' in c['kinds'])
        self.assertEqual(exit['classification'],'REJECTED');self.assertIn('SELL_QUANTITY_OUTSIDE_DECLARED_UNIT:A',exit['unit_gate_reasons'])
        save(OUT/'endpoint-gates.json',dict(all_target_deltas_checked=True,full_not_silently_rounded=True,exit_not_silently_rounded=True,zero_trade_preserves_existing_odd_shares=True))

    def test_04_declared_B3_add2_and_untouched_checkpoint_continuity(self):
        p=ROOT/'corrections/existing-B3-add2-declared-opening';q=load(p/'input.json');r=load(p/'actual.json')['research'];e=load(p/'expected.json')
        self.assertEqual(r['status'],e['status']);self.assertEqual(grid(r),e['grid'])
        c=next(c for c in r['candidates'] if c.get('in_explicit_grid'));self.assertEqual(c['plan']['targets']['B'],'5');self.assertEqual(c['additional_B'],'2');self.assertEqual(c['unit_gate_reasons'],[])
        self.assertIsNone(q['continuation']);self.assertEqual(q['batch_context']['phase'],'ADDITIONAL_BATCH')
        p=ROOT/'controls/continuity';q=load(p/'input.json');r=load(p/'actual.json')['research'];cp=q['continuation']['checkpoint'];base=r['baseline']
        self.assertEqual(r['status'],'COMPLETE');self.assertEqual(base['continuity']['checkpoint_id'],cp['checkpoint_id'])
        self.assertEqual(base['continuity']['latest_predecessor_id'],cp['execution_result']['latest_decision_id'])
        self.assertLessEqual(set(cp['state']['reviewed_evidence_tokens']),set(base['reviewed_evidence_tokens']))
        self.assertEqual(cp['state']['origin_initial_capital'],'2180');self.assertEqual(q['quantity_domain']['account_id'],_fp(q['decision_input']['account']))
        self.assertTrue(all(c['plan'] is None or c['plan']['targets']['C']==q['decision_input']['account']['holdings']['C']['shares'] for c in r['candidates']))
        save(OUT/'delta-and-continuity.json',dict(separate_declared_opening_B3_plus_2_targets_5=True,original_invalid_checkpoint_case_still_rejected=True,
            preserved_original_capital='2180',latest_and_all_prior_tokens_bound=True))

    def test_05_unit_one_preserves_original_financial_batch_and_legacy_results(self):
        for name in ('additional-independent','additional-old-trigger','unknown-batch-phase','wait-sale-settlement','non-monotone','common-risk-limit','liquidity-limit','cost-cannot-be-free'):
            self.assertEqual(normalize(actual(name)),load(ROOT/'final'/name/'legacy-actual.json')['research'],name)
        for name in ('legacy-v1','legacy-v2'):
            self.assertEqual(load(ROOT/'controls'/name/'actual.json'),load(ROOT/'before'/name/'actual.json'),name)
        self.assertEqual(normalize(actual('unit-one')),load(ROOT/'before/legacy-v2/actual.json')['research'])
        buys=lambda name:[c for c in actual(name)['research']['candidates'] if int(c.get('additional_B') or '0')>0]
        self.assertTrue(all(not c['feasible_for_research'] for c in buys('additional-old-trigger')))
        self.assertTrue(all(not c['feasible_for_research'] for c in buys('unknown-batch-phase')))
        self.assertTrue(any(c['classification']=='WAIT_SETTLEMENT_REASSESSMENT' for c in buys('wait-sale-settlement')))
        r=actual('non-monotone')['research'];mapping={c['additional_B']:c['classification'] for c in r['candidates'] if c['plan'] and c['plan']['targets']['A']=='100'}
        self.assertEqual(mapping,{'0':'REJECTED','1':'CURRENTLY_FEASIBLE','2':'CURRENTLY_FEASIBLE','3':'REJECTED'})
        save(OUT/'compatibility.json',dict(legacy_v1_and_v2_envelopes_exact=True,unit_one_normalized_research_equal=True,
            financial_risk_liquidity_settlement_batch_gates_reused=True,not_assuming_monotone_feasibility=True))

    def test_06_unknown_future_or_mismatched_domain_and_search_overflow_before_core(self):
        rows=load(ROOT/'final/summary.json')['cases']
        for row in rows:
            e=load(ROOT/'cases'/row['name']/'expected.json')
            if e.get('core_calls')==0:self.assertEqual(row['decision_entry_calls'],0,row['name'])
        r=actual('search-limit')['research'];self.assertEqual(r['status'],'REFUSED_SEARCH_LIMIT');self.assertEqual(r['candidates'],[]);self.assertFalse(r['enumeration_complete'])
        for name in ('future-A-wins','future-B-wins','future-both-fall'):
            self.assertEqual(actual(name)['research'],actual('manual-grid')['research'])
            self.assertNotEqual(actual(name)['source_integrity_metadata'],actual('manual-grid')['source_integrity_metadata'])
        for name in ('unknown-domain-time','unknown-unit-time'):
            a=load(ROOT/'diagnostics'/name/'final-actual.json')
            self.assertEqual(a['error_type'],'ValueError');self.assertIsNone(a['research'])
        save(OUT/'source-time-and-search.json',dict(invalid_domain_and_search_limit_core_calls=0,future_research_equal=True,integrity_metadata_compared_separately=True))

    def test_07_complete_decimal_context_no_io_network_and_input_mutation(self):
        from capital_research.quantity_candidates import generate
        from capital_research.decimal_context_20261027.reproduce import context,snapshot
        specs=[dict(prec=3,rounding='ROUND_UP',Emin=-2,Emax=2,capitals=0,clamp=1,traps=['Inexact','Overflow','Clamped'],flags=[]),
            dict(prec=7,rounding='ROUND_DOWN',Emin=-9,Emax=9,capitals=1,clamp=0,traps=['Rounded'],flags=['Inexact'])]
        save(OUT/'context/specifications.json',specs);q=request('manual-grid');before=deepcopy(q);default=snapshot(decimal.DefaultContext);rows=[]
        for spec in specs:
            with decimal.localcontext(context(spec)) as caller:
                original=snapshot(caller)
                with patch('builtins.open',side_effect=AssertionError('NO_IO')),patch('socket.socket',side_effect=AssertionError('NO_NETWORK')):r=generate(q)
                row=dict(full_result_equal=r==actual('manual-grid'),caller_unchanged=snapshot(caller)==original,default_unchanged=snapshot(decimal.DefaultContext)==default,input_unchanged=q==before)
                self.assertTrue(all(row.values()));rows.append(row)
        save(OUT/'context/actual.json',rows)

    def test_08_fresh_generate_does_not_import_execution_or_ledger(self):
        code='''import sys,json,importlib.abc
from pathlib import Path
from unittest.mock import patch
request=json.loads(Path(sys.argv[1]).read_text())
bad=('capital_research.execution','capital_research.execution_continuation','capital_research.quantity_replay','capital_research.cash_action_execution','rotation_research.action_ledger')
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if any(fullname==x or fullname.startswith(x+'.') for x in bad):raise AssertionError('FORBIDDEN_EXECUTION_OR_LEDGER:'+fullname)
sys.meta_path.insert(0,Guard())
from capital_research.quantity_candidates import generate
with patch('builtins.open',side_effect=AssertionError('NO_IO')),patch('socket.socket',side_effect=AssertionError('NO_NETWORK')):result=generate(request)
print(json.dumps(result,ensure_ascii=False))
'''
        p=subprocess.run([sys.executable,'-c',code,str(ROOT/'cases/manual-grid/input.json')],cwd=PROJECT,text=True,capture_output=True)
        save(OUT/'fresh/actual.json',dict(returncode=p.returncode,stderr=p.stderr,stdout=p.stdout))
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),actual('manual-grid'))

if __name__=='__main__':unittest.main()
