"""Only targeted saved-choice/Journal tests; no numeric producers permitted."""
from copy import deepcopy
from decimal import Context,Inexact,Rounded,ROUND_UP,localcontext
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from .freeze import ROOT,REPO,PROJECT,load,save,info,fp
from capital_research.research_choice import choose_saved,validate_record,bind_saved_source
from capital_research.research_choice_workflow import select_and_save,read_choice
from capital_research.research_choice_source import check_saved

OUT=ROOT/os.environ.get('CHOICE_V04_TEST_STAGE','validation')
def req(name):return load(ROOT/'cases'/name/'input.json')
def choice(name):return load(ROOT/'final'/name/'read.json')['record']['value']
def metadata(p):return {str(f.relative_to(p)):(hashlib.sha256(f.read_bytes()).hexdigest(),f.stat().st_mtime_ns) for f in p.rglob('*') if f.is_file()}

class ChoiceV04(TestCase):
    def test_preservation_and_saved_expected(self):
        intake=load(ROOT/'intake.json')
        for row in load(ROOT/'frozen.json')['files']+intake['protected']+intake['source_originals']+load(ROOT/'corrections/frozen.json')['files']:
            self.assertEqual(info(REPO/row['path']),row)
        for row in load(ROOT/'final/source-versions.json')['files']:self.assertEqual(info(REPO/row['path']),row)
        matched=0
        for name in load(ROOT/'case-index.json')['cases']:
            with self.subTest(case=name):
                e=load(ROOT/'cases'/name/'expected.json');c=choice(name)['choice'];validate_record(choice(name))
                if name=='missing-token':
                    self.assertEqual(req(name),req('checkpoint-new-trigger'));self.assertEqual(e['status'],'REFUSED')
                    self.assertEqual(c['status'],'RECORDED_CONDITIONAL_RESEARCH_INTENT');continue
                self.assertEqual(c['status'],e['status']);matched+=1
                if 'target_B' in e:self.assertEqual(c['selected']['plan']['targets']['B'],e['target_B'])
                if 'additional_B' in e:self.assertEqual(c['selected']['additional_B'],e['additional_B'])
        self.assertEqual(matched,31)
        save(OUT/'oracle-audit.json',dict(frozen_cases=32,matching_original_expectations=31,
            invalid_negative='missing-token is byte-identical to checkpoint-new-trigger; original oracle not edited',
            corrected_negative='corrections/missing-baseline-token',market_samples=0))

    def test_complete_binding_and_qualification(self):
        rows=[]
        for name in ('conditional-full','general-full','hold','grid','exit-A','checkpoint-new-trigger','checkpoint-valid-old-fact','zero-addition','hold-when-full-rejected'):
            x=req(name);before=deepcopy(x);saved=choose_saved(x);self.assertEqual(saved,choice(name));self.assertEqual(x,before)
            c=saved['choice'];b=c['source_binding'];source=x['saved_result'];q=source['quantity_request'];g=source['generation'];r=g['research']
            self.assertEqual(b,x['source_binding']);self.assertEqual(b['account_snapshot'],q['decision_input']['account'])
            self.assertEqual(b['quantity_domain'],q['quantity_domain']);self.assertEqual(b['full_search_policy'],q['full_search'])
            self.assertEqual(b['full_search_receipt'],r['full_search_receipt']);self.assertEqual(b['generation_document_id'],fp(g))
            self.assertEqual(c['source_roles'],dict(incumbent=q['incumbent'],destination=q['destination']))
            check=check_saved(saved,source);self.assertEqual(check['check_status'],'MATCHED')
            self.assertEqual(check['columns'][0]['candidate'],check['columns'][1]['candidate'])
            self.assertFalse(c['execution_authorized']);self.assertIsNone(c['primary_pressure_id']);self.assertEqual(c['execution'],'NOT_PERFORMED')
            if q['continuation']:
                cp=q['continuation']['checkpoint'];e=cp['execution_result']
                self.assertEqual(b['latest_decision_id'],e['latest_decision_id']);self.assertEqual(b['origin_initial_capital'],cp['state']['origin_initial_capital'])
                self.assertEqual(b['historical_reviewed_tokens'],cp['state']['reviewed_evidence_tokens'])
                self.assertTrue(set(b['historical_reviewed_tokens'])<=set(b['decision_reviewed_tokens']))
                self.assertEqual(b['received_attempt_ids'],[a['attempt_id'] for a in e['reassessment_attempts']])
            else:self.assertEqual(b['source_kind'],'DECLARED_SYNTHETIC_OPENING');self.assertIsNone(b['checkpoint_id']);self.assertIsNone(b['latest_decision_id'])
            if name=='zero-addition':self.assertEqual(c['selected']['additional_B'],'0')
            rows.append(dict(case=name,status=c['status'],account_id=b['account_id'],source_kind=b['source_kind'],
                latest=b['latest_decision_id'],historical_tokens=len(b['historical_reviewed_tokens']),decision_tokens=len(b['decision_reviewed_tokens'])))
        save(OUT/'bindings.json',dict(rows=rows,ledger_or_execution_recomputed=False))

    def test_component_mismatch_and_real_missing_token(self):
        for name in ('wrong-domain','missing-domain','wrong-policy','wrong-receipt','wrong-account','wrong-cutoff','wrong-latest','wrong-reserve','bad-unit-time','fake-opening','borrow-binding','bad-selected-quantity','downgrade'):
            c=choice(name)['choice'];self.assertEqual(c['status'],'REFUSED');self.assertIsNone(c['selected'])
        x=load(ROOT/'corrections/missing-baseline-token/input.json');expected=load(ROOT/'corrections/missing-baseline-token/expected.json')
        saved=choose_saved(x);self.assertEqual(saved['choice']['status'],expected['status']);self.assertEqual(saved['choice']['reasons'],[expected['reason']])
        receipt=select_and_save(OUT/'correction-journal','missing-token',x);self.assertEqual(receipt['storage_status'],'SAVED_AND_READ_BACK')
        save(OUT/'missing-baseline-token.json',receipt)
        self.assertEqual(check_saved(choice('conditional-full'),req('general-full')['saved_result'])['check_status'],'REFUSED')
        self.assertEqual(check_saved(choice('checkpoint-new-trigger'),req('conditional-full')['saved_result'])['check_status'],'REFUSED')

    def test_journal_idempotency_conflict_and_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);x=req('conditional-full');first=select_and_save(root,'choice',x);self.assertEqual(first['storage_status'],'SAVED_AND_READ_BACK')
            before=metadata(root);again=select_and_save(root,'choice',x);self.assertEqual(again,first);self.assertEqual(metadata(root),before)
            other=req('general-full');conflict=select_and_save(root,'choice',other)
            self.assertEqual(conflict['storage_status'],'NOT_SAVED');self.assertEqual(metadata(root),before)
            with (patch('capital_research.research_choice_workflow.choose_saved',side_effect=AssertionError('READ must not choose')),
                  patch('rotation_research.store.Journal.save',side_effect=AssertionError('READ must not save')),
                  patch('pathlib.Path.write_text',side_effect=AssertionError('READ must not write'))):
                read=read_choice(root,'choice');check=check_saved(read['record']['value'],x['saved_result'])
            self.assertEqual(check['check_status'],'MATCHED');self.assertEqual(metadata(root),before)
            with patch('rotation_research.store.Journal.save',side_effect=OSError('explicit IO uncertainty')):
                uncertain=select_and_save(root,'other',x)
            self.assertEqual(uncertain['storage_status'],'UNKNOWN');self.assertEqual(metadata(root),before)
        save(OUT/'journal-controls.json',dict(same_content_preserved=True,identity_conflict_preserved=True,read_did_not_choose_or_write=True,io_uncertainty='UNKNOWN'))

    def test_read_rejects_tampered_unit_receipt_and_roles(self):
        for field in ('unit_gate','delta','receipt','roles','account'):
            x=deepcopy(choice('conditional-full'));c=x['choice']
            if field=='unit_gate':c['selected']['unit_gate_reasons']=['BUY_QUANTITY_OUTSIDE_DECLARED_UNIT:B']
            if field=='delta':c['selected']['additional_B']='90'
            if field=='receipt':c['source_binding']['full_search_receipt']['selected_target']['B']='90'
            if field=='roles':c['source_roles']=dict(incumbent='B',destination='A')
            if field=='account':c['source_binding']['account_snapshot']['reserved_cash']='0'
            c['record_id']=fp({k:v for k,v in c.items() if k!='record_id'})
            with self.subTest(field=field),self.assertRaises(ValueError):validate_record(x)

    def test_fresh_process_no_numeric_import_or_network(self):
        script='''import sys,json,importlib.abc,socket
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname in {"capital_research.core","capital_research.execution","capital_research.continuity","capital_research.quantity_candidates","capital_research.quantity_after_retry","capital_research.allocation","rotation_research.action_ledger"}:raise AssertionError("Forbidden producer import "+fullname)
sys.meta_path.insert(0,Block())
socket.socket=lambda *a,**k: (_ for _ in ()).throw(AssertionError("Network forbidden"))
from pathlib import Path
from capital_research.research_choice import choose_saved
from capital_research.research_choice_source import check_saved
from capital_research.research_choice_workflow import read_choice
req=json.loads(Path(sys.argv[1]).read_text());c=choose_saved(req);r=read_choice(sys.argv[2],"checkpoint-new-trigger")
assert c==r["record"]["value"]
assert check_saved(c,req["saved_result"])["check_status"]=="MATCHED"
print(json.dumps({"status":c["choice"]["status"],"forbidden_imports":0,"network_calls":0}))
'''
        run=subprocess.run([sys.executable,'-B','-c',script,str(ROOT/'cases/checkpoint-new-trigger/input.json'),str(ROOT/'final/journal')],
            cwd=PROJECT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(PROJECT)},capture_output=True,text=True)
        save(OUT/'fresh-process.json',dict(returncode=run.returncode,stdout=run.stdout,stderr=run.stderr))
        self.assertEqual(run.returncode,0,run.stderr)

    def test_legacy_exact_compatibility_and_text_read(self):
        from capital_research.research_choice_view import render_text
        for name in ('grid-new-trigger','exit-A-cash','unknown-refused'):
            prior=load(ROOT/'legacy'/name/'before.json');current=load(ROOT/'final/legacy'/name/'actual.json')
            self.assertEqual(current,prior);validate_record(prior);self.assertTrue(render_text(prior))
        self.assertIn('條件研究意圖',render_text(choice('conditional-full')))
        self.assertIn('一般研究意圖',render_text(choice('general-full')))
        self.assertIn('遭拒',render_text(choice('outer-unknown')))

    def test_decimal_environment_and_input_purity(self):
        x=req('checkpoint-new-trigger');before=deepcopy(x);expected=choice('checkpoint-new-trigger')
        with localcontext(Context(prec=2,rounding=ROUND_UP,Emin=-2,Emax=2,clamp=1)) as ctx:
            ctx.traps[Inexact]=True;ctx.traps[Rounded]=True;old=str(ctx)
            self.assertEqual(choose_saved(x),expected);self.assertEqual(check_saved(expected,x['saved_result'])['check_status'],'MATCHED')
            self.assertEqual(str(ctx),old)
        self.assertEqual(x,before)
        for name in ('conditional-full','general-full','outer-unknown'):
            c=choice(name)['choice']
            for key in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'):
                self.assertIs(c[key],False)
        save(OUT/'purity.json',dict(input_unchanged=True,ambient_context_unchanged=True,numeric_producer_runs=0,new_orders=0,new_fills=0))
