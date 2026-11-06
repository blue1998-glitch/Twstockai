"""New milestone only: frozen cases, timeline identities and bounded regressions."""
import ast
import decimal
import unittest
from copy import deepcopy
from unittest.mock import patch
from .freeze import ROOT, PROJECT, REPO, load, save, info
from capital_research.execution_continuation import resume_orders
from capital_research.cash_action_execution import execute
from capital_research.decimal_context_20261027.reproduce import snapshot

D=decimal.Decimal
FLAGS=('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized')
EVIDENCE=ROOT/'after-final/test-evidence'


def req(name):return load(ROOT/'cases'/name/'input.json')
def actual(name):return load(ROOT/'after-final'/name/'actual.json')
def control(name):return load(ROOT/'controls'/name/'actual.json')


class StandingTests(unittest.TestCase):
    def test_01_preservation_and_original_initialization_and_trading_loop(self):
        for meta in load(ROOT/'intake.json')['protected']+load(ROOT/'frozen.json')['files']:
            self.assertEqual(info(REPO/meta['path']),meta)
        self.assertEqual(info(ROOT/'baseline/execution.py'),load(ROOT/'intake.json')['archived_execution'])
        old=ast.parse((ROOT/'baseline/execution.py').read_text())
        new=ast.parse((PROJECT/'capital_research/execution.py').read_text())
        o=next(x for x in old.body if isinstance(x,ast.FunctionDef) and x.name=='_simulate')
        n=next(x for x in new.body if isinstance(x,ast.FunctionDef) and x.name=='_simulate')
        end=next(i for i,x in enumerate(o.body) if isinstance(x,ast.FunctionDef) and x.name=='knowledge')
        self.assertEqual(ast.dump(ast.Module(body=o.body[:end],type_ignores=[])),
            ast.dump(ast.Module(body=n.body[0].body,type_ignores=[])))
        loop=lambda f:next(x for x in f.body if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='obs')
        old_loop=loop(o);new_loop=deepcopy(loop(n));new_loop.body.pop() # new audit hook only
        self.assertEqual(ast.dump(old_loop),ast.dump(new_loop))
        save(EVIDENCE/'preservation.json',dict(original_initialization_ast_identical=True,
            original_observation_trading_loop_ast_identical=True,all_frozen_and_protected_bytes_matched=True))

    def test_02_all_saved_oracles_and_refusal_before_tail(self):
        index=load(ROOT/'case-index.json')
        for name in index['all']:
            a=actual(name);e=load(ROOT/'cases'/name/'expected.json')
            self.assertEqual(a['status'],e['status'],name)
            self.assertTrue(all(a[k] is False for k in FLAGS))
            if name in index['negative']:
                self.assertIn(e['reason'],a['refusal_reasons'],name)
                self.assertEqual(a['tail_observations_processed'],0)
                self.assertIsNone(a['execution']);self.assertIsNone(a['checkpoint']);continue
            ex=a['execution'];row=a['checkpoint']['state']['row'];r=req(name)
            self.assertEqual(ex['orders'],r['checkpoint']['execution_result']['orders'])
            self.assertEqual(a['checkpoint']['origin_ledger_input'],r['root_job']['ledger_input'])
            if 'final_cash' in e:
                self.assertEqual(D(row['settled_cash']),D(e['final_cash']),name)
                self.assertEqual(D(row['shares']['B']),D(e['final_B']))
                self.assertEqual(D(row['shares']['C']),D(e['final_C']))
                self.assertEqual(D(r['checkpoint']['state']['row']['purchase_payable']),D(e['prefix_payable']))
                st=ex['order_states']['explicit-order'];self.assertEqual(st['status'],e['order_status']);self.assertEqual(st['remaining'],e['remaining'])
                self.assertEqual(len(a['new_fill_ids_this_segment']),e['new_segment_fills'])

    def test_03_each_day_cash_payables_reserve_and_rights_handcheck(self):
        a=actual('partial-fill');cp=req('partial-fill')['checkpoint'];ex=a['execution']
        self.assertEqual(cp['state']['origin_initial_capital'],'1180')
        self.assertEqual(cp['state']['general_reserved_cash'],'100')
        self.assertEqual(cp['state']['order_states']['explicit-order']['reserved_cash'],'261.65039')
        rows={r['date']:r for r in ex['ledger']['daily']}
        expected={'2026-01-06':('1000','141.140','858.860','7','2','80'),
            '2026-01-08':('858.860','0','858.860','7','2','80'),
            '2026-01-09':('858.860','261.260','597.600','20','2','80'),
            '2026-01-12':('677.600','0','677.600','20','4','0')}
        for day,vals in expected.items():
            row=rows[day];got=[row[k] for k in ('settled_cash','purchase_payable','available_cash_strict')]+[row['shares'][c] for c in ('B','C')]+[row['cash_receivable']]
            self.assertEqual(list(map(D,got)),list(map(D,vals)),day)
        for row in rows.values():
            values=sum(D(n)*D(row['marks'][c]['value']) for c,n in row['shares'].items())
            rights=sum(D(x['shares'])*D(row['marks'][x['code']]['value']) for x in row['share_receivables'])
            self.assertEqual(D(row['settled_cash'])+D(row['cash_receivable'])-D(row['purchase_payable'])+values+rights,D(row['net_accrual_equity']))
        self.assertEqual(len(ex['fills']),2);self.assertEqual(len(set(f['id'] for f in ex['fills'])),2)
        self.assertEqual(ex['fills'][0],cp['state']['accepted_fills'][0])
        self.assertEqual(rows['2026-01-12']['cash_claims'],[]);self.assertEqual(rows['2026-01-12']['share_receivables'],[])
        self.assertEqual(a['checkpoint']['state']['general_reserved_cash'],'100')
        save(EVIDENCE/'daily-handcheck.json',dict(expected=expected,all_daily_balance_identities_matched=True,fees_total='2',origin_capital='1180',general_reserve='100',new_tail_orders=0))

    def test_04_every_observation_and_daily_row_and_two_resumes_equal(self):
        for name in load(ROOT/'case-index.json')['positive']:
            comparison=load(ROOT/'after-final'/name/'comparison.json')
            self.assertTrue(all(comparison.values()),(name,comparison))
        for name in ('partial-fill','expired'):
            first=control(name+'-to-Jan8');last=control(name+'-to-Jan12')
            self.assertEqual(first['tail_observations_processed'],0)
            self.assertEqual(first['new_fill_ids_this_segment'],[])
            self.assertEqual(last['execution'],load(ROOT/'before'/name/'full-execution.json'))
            self.assertEqual(last['integrity']['predecessor_checkpoint_id'],first['checkpoint']['checkpoint_id'])
        events=control('expired-to-Jan12')['execution']['execution_events']
        self.assertEqual(sum(e['status']=='EXPIRED_UNFILLED' for e in events),1)

    def test_05_future_knowledge_and_watermark_release_without_tape(self):
        normal=control('partial-fill-to-Jan8');future=control('future-changed')
        self.assertEqual(normal['checkpoint']['state'],future['checkpoint']['state'])
        self.assertEqual(normal['execution'],future['execution'])
        self.assertNotEqual(normal['integrity'],future['integrity'])
        early=control('no-tape-before-known');known=control('no-tape-after-known');end=control('no-tape-to-Jan12')
        self.assertEqual(early['checkpoint']['state']['order_states']['explicit-order']['reserved_cash'],'261.65039')
        for a in (known,end):
            st=a['checkpoint']['state']['order_states']['explicit-order'];self.assertEqual(st['status'],'CANCELLED_EVIDENCE');self.assertEqual(st['reserved_cash'],'0')
            self.assertEqual(a['checkpoint']['state']['row']['shares']['B'],'7')
        self.assertEqual(end['checkpoint']['state']['row']['settled_cash'],'938.860')
        late=actual('late-published')['execution'];self.assertEqual(late['fills'][0]['shares'],'7')
        cancel=next(e for e in late['execution_events'] if e['status']=='CANCELLED_EVIDENCE')
        self.assertGreaterEqual(timestamp(cancel['at']),timestamp('2026-01-09T12:00:00+08:00'))

    def test_06_latest_and_full_accepted_rejected_receipts_and_tokens(self):
        for name,a,r in [('rejected',actual('past-reassessment-current'),req('past-reassessment-current')),
                ('accepted',control('accepted-history-resume'),load(ROOT/'controls/accepted-history-resume/input.json'))]:
            before=r['checkpoint']['execution_result'];ex=a['execution']
            for field in ('decision_ids','decision_records','latest_decision_id','latest_common_account_id','origin_common_account_id',
                          'fact_sources','reassessment_attempts','reviewed_evidence_tokens','order_history','opening_unavailable_shares'):
                self.assertEqual(ex[field],before[field],(name,field))
            self.assertEqual(len(ex['reassessment_attempts']),1)
            self.assertEqual(ex['reassessment_attempts'][0]['outcome'],name.upper())
        self.assertEqual(control('accepted-history-resume')['execution'],load(ROOT/'controls/accepted-history/baseline-full.json'))
        self.assertEqual(control('new-decision')['research']['status'],'NOT_IMPLEMENTED')
        self.assertEqual(control('new-decision')['research']['reasons'],['ACTIVE_ORDER_CONTINUATION_NOT_IMPLEMENTED'])

    def test_07_decimal_isolation_input_immutability_and_no_io_or_generation(self):
        from capital_research.execution import decide
        from capital_research import execution_continuation as module
        contexts=[decimal.Context(prec=3,rounding=decimal.ROUND_UP,Emin=-2,Emax=2,clamp=1,traps=[decimal.Inexact,decimal.Overflow,decimal.Clamped]),
            decimal.Context(prec=7,rounding=decimal.ROUND_DOWN,Emin=-9,Emax=9,flags=[decimal.Inexact],traps=[decimal.Rounded])]
        default=snapshot(decimal.DefaultContext);rows=[]
        for name,r,expected in [('partial',req('partial-fill'),actual('partial-fill')),
                ('accepted',load(ROOT/'controls/accepted-history-resume/input.json'),control('accepted-history-resume'))]:
            before=deepcopy(r)
            for i,ctx in enumerate(contexts):
                with decimal.localcontext(ctx) as caller:
                    context_before=snapshot(caller)
                    with patch('builtins.open',side_effect=AssertionError('PURE_NO_IO')), \
                         patch('socket.socket',side_effect=AssertionError('NO_NETWORK')), \
                         patch('capital_research.quantity_candidates.generate',side_effect=AssertionError('NO_NEW_BATCH')), \
                         patch('capital_research.execution.decide',wraps=decide) as decision:
                        result=resume_orders(r)
                    self.assertEqual(snapshot(caller),context_before)
                self.assertEqual(result,expected);self.assertEqual(r,before)
                # Root proof reconstruction uses the original decision once;
                # the carried tail must use zero additional decision calls.
                self.assertEqual(decision.call_count,1)
                rows.append(dict(case=name,context=i,all_json_equal=True,input_unchanged=True,caller_unchanged=True,root_decision_calls=1,tail_decision_calls=0))
        self.assertEqual(snapshot(decimal.DefaultContext),default)
        save(EVIDENCE/'context-and-purity.json',dict(controls=rows,default_context_unchanged=True))

    def test_08_two_legacy_action_results_remain_exact(self):
        rows=[]
        for directory,name in [('cash_execution_20261028','partial-7-active-13'),('cash_two_rounds_20261028','independent-B20')]:
            root=PROJECT/'capital_research'/directory;r=load(root/'cases'/name/'input.json');saved=load(root/'actual'/name/'result.json')
            got=execute(r);self.assertEqual(got,saved,(directory,name))
            rows.append(dict(directory=directory,case=name,complete_saved_json_equal=True))
        save(EVIDENCE/'necessary-legacy.json',dict(cases=rows,old_suites_run=0))

    def test_09_sale_receivable_is_not_cash_and_unreceived_review_is_not_history(self):
        root=ROOT/'supplement/receivable';a=load(root/'actual.json');e=load(root/'expected.json');r=load(root/'input.json')
        self.assertEqual(a['status'],e['status']);self.assertTrue(all(load(root/'comparison.json').values()))
        prior=r['checkpoint']['state']['row']
        for field,key in [('settled_cash','prefix_cash'),('purchase_payable','prefix_payable'),
                          ('cash_receivable','prefix_receivable'),('available_cash_strict','prefix_available')]:
            self.assertEqual(D(prior[field]),D(e[key]))
        rows={x['date']:x for x in a['execution']['ledger']['daily']}
        self.assertEqual(D(rows['2026-01-08']['settled_cash']),D(e['Jan8_cash']))
        self.assertEqual(D(rows['2026-01-08']['cash_receivable']),D(e['Jan8_receivable']))
        self.assertEqual(D(rows['2026-01-12']['settled_cash']),D(e['final_cash']))
        self.assertEqual(rows['2026-01-12']['shares'],dict(A=e['final_A'],B=e['final_B'],C=e['final_C']))
        self.assertEqual(a['checkpoint']['state']['origin_initial_capital'],e['origin_capital'])
        self.assertEqual(a['checkpoint']['state']['general_reserved_cash'],e['general_reserve'])
        self.assertEqual(a['execution']['fills'],r['checkpoint']['state']['accepted_fills'])
        bad=load(ROOT/'supplement/unreceived-review/actual.json')
        self.assertEqual(bad['status'],'REFUSED');self.assertEqual(bad['refusal_reasons'],['UNRECEIVED_REASSESSMENT_NOT_IMPLEMENTED'])
        self.assertFalse(bad['tail_processing_started']);self.assertEqual(bad['tail_observations_processed'],0)


from capital_research.core import timestamp

if __name__=='__main__':unittest.main()
