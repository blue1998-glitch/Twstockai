"""Targeted saved-operation import and READ controls; no numeric RUN."""
from copy import deepcopy
from decimal import Context,Inexact,Rounded,ROUND_UP,localcontext
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from .freeze import ROOT,REPO,PROJECT,load,save,info,fp
from capital_research import research_operation as op
from rotation_research.store import Journal

OUT=ROOT/os.environ.get('OPERATION_IMPORT_TEST_STAGE','validation')
def request(name):return load(ROOT/'cases'/name/'input.json')
def receipt(name):return load(ROOT/'actual'/name/'import.json')
def meta(root):return {str(p.relative_to(root)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file()}
def store_values(root,identity):return {k:Journal(root).read(v)['value'] for k,v in op._keys(identity).items()}

class ImportOperation(TestCase):
    def test_frozen_expectations_and_protected_sources(self):
        intake=load(ROOT/'intake.json')
        for row in load(ROOT/'frozen.json')['files']+intake['protected']+intake['source_originals']+load(ROOT/'actual/source-versions.json')['files']:
            self.assertEqual(info(REPO/row['path']),row)
        rows=load(ROOT/'actual/summary.json')['cases'];self.assertEqual(len(rows),19)
        for row in rows:
            with self.subTest(case=row['case']):
                e=load(ROOT/'cases'/row['case']/'expected.json');self.assertEqual(row['workflow_status'],e['workflow_status']);self.assertTrue(row['input_unchanged'])
                if 'source_check_calls' in e:self.assertEqual(row['source_check_calls'],e['source_check_calls'])
                if row['workflow_status']=='INPUT_REFUSED':
                    self.assertIsNone(receipt(row['case'])['operation']);self.assertEqual(row['source_check_calls'],0)
                else:self.assertEqual(row['read_status'],'READ_ONLY')
        positive={fp(request(r['case'])) for r in rows if r['workflow_status']!='INPUT_REFUSED'}
        negative={fp(request(r['case'])) for r in rows if r['workflow_status']=='INPUT_REFUSED'}
        self.assertFalse(positive&negative)
        save(OUT/'case-audit.json',dict(original_cases=19,all_expected=True,negative_positive_overlap=0,numeric_producer_runs=0))

    def test_exact_originals_qualification_and_account_chain(self):
        records=[]
        for name in ('general-full','conditional-full','checkpoint-new-trigger','zero-addition','hold','outer-unknown'):
            x=request(name);identity='import-'+name;values=store_values(ROOT/'actual/runs'/name,identity);c=x['choice']['choice'];b=c['source_binding']
            self.assertEqual(values['generation'],x['saved_source']);self.assertEqual(values['choice'],x['choice'])
            self.assertEqual(json.loads(values['request']['request_json']),x)
            result=values['result'];self.assertEqual(result['schema'],op.RESULT_IMPORT);self.assertEqual(result['generation_id'],fp(x['saved_source']))
            self.assertEqual(result['choice_record_id'],c['record_id']);self.assertEqual(result['choice_status'],c['status'])
            self.assertEqual(b['account_snapshot'],x['saved_source']['quantity_request']['decision_input']['account'])
            self.assertEqual(b['quantity_domain'],x['saved_source']['quantity_request']['quantity_domain'])
            self.assertEqual(b['full_search_receipt'],x['saved_source']['generation']['research']['full_search_receipt'])
            if name=='outer-unknown':self.assertEqual(result['outcome'],'CHOICE_REFUSED');self.assertIsNone(result['source_check'])
            else:self.assertEqual(result['source_check']['check_status'],'MATCHED')
            for key in op.FLAGS:self.assertIs(result[key],False)
            self.assertIsNone(result['primary_pressure_id']);self.assertFalse(result['execution_authorized'])
            q=x['saved_source']['quantity_request']
            if q['continuation']:
                cp=q['continuation']['checkpoint'];self.assertEqual(b['latest_decision_id'],cp['execution_result']['latest_decision_id'])
                self.assertEqual(b['origin_initial_capital'],cp['state']['origin_initial_capital'])
                self.assertEqual(b['historical_reviewed_tokens'],cp['state']['reviewed_evidence_tokens'])
                self.assertTrue(set(b['historical_reviewed_tokens'])<=set(b['decision_reviewed_tokens']))
            else:self.assertIsNone(b['checkpoint_id'])
            records.append(dict(case=name,outcome=result['outcome'],source_kind=b['source_kind'],account_id=b['account_id'],
                reserve=b['account_snapshot']['reserved_cash'],latest=b['latest_decision_id'],historical_tokens=b['historical_reviewed_tokens'],
                decision_tokens=b['decision_reviewed_tokens'],unchanged_source=fp(values['generation']),unchanged_choice=fp(values['choice'])))
        save(OUT/'originals.json',dict(rows=records,no_account_reconstruction=True,no_orders_or_fills=True))

    def test_existing_id_and_conflict_preserve_all_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);x=request('conditional-full');first=op.import_operation(root,'same',x)
            self.assertEqual(first['workflow_status'],'COMPLETED_CONDITIONAL_INTENT');before=meta(root)
            with (patch.object(op,'_persist',side_effect=AssertionError('No existing-ID writes')),
                  patch.object(op,'_generation',side_effect=AssertionError('No generation')),
                  patch.object(op,'_selection',side_effect=AssertionError('No selection'))):
                same=op.import_operation(root,'same',x);other=op.import_operation(root,'same',request('general-full'))
            self.assertEqual(same['workflow_status'],'OPERATION_EXISTS_READ_REQUIRED');self.assertEqual(other['workflow_status'],'OPERATION_ID_CONFLICT')
            self.assertEqual(meta(root),before)
            # Wrong public route must refuse before any of the four saves.
            bad=op.run_operation(root,'wrong-route',x);self.assertEqual(bad['workflow_status'],'INPUT_REFUSED');self.assertEqual(meta(root),before)
        save(OUT/'identity.json',dict(same='OPERATION_EXISTS_READ_REQUIRED',different='OPERATION_ID_CONFLICT',no_file_changes=True,run_does_not_import=True))

    def test_each_storage_unknown_preserves_prefix_and_requires_read(self):
        rows=[];original=op._persist;x=request('conditional-full')
        for fail_stage in op.STAGES:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                def uncertain(store,key,value):
                    result=original(store,key,value)
                    if key.endswith('--'+fail_stage):return 'UNKNOWN',None,['EXPLICIT_AFTER_WRITE_RESPONSE_LOSS']
                    return result
                with patch.object(op,'_persist',side_effect=uncertain):r=op.import_operation(root,'uncertain',x)
                self.assertEqual(r['workflow_status'],'STOPPED_STORAGE');self.assertEqual(r['storage'][fail_stage],'UNKNOWN')
                before=meta(root)
                with (patch.object(op,'_source_check',side_effect=AssertionError('READ does not check again')),
                      patch.object(op,'_generation',side_effect=AssertionError('No generation')),
                      patch.object(op,'_selection',side_effect=AssertionError('No selection')),
                      patch.object(Journal,'save',side_effect=AssertionError('No READ saves'))):
                    read=op.read_operation(root,'uncertain')
                self.assertEqual(meta(root),before)
                self.assertEqual(read['workflow_status'],'READ_ONLY' if fail_stage=='result' else 'INCOMPLETE_SAVED_PREFIX')
                retry=op.import_operation(root,'uncertain',x);self.assertEqual(retry['workflow_status'],'OPERATION_EXISTS_READ_REQUIRED');self.assertEqual(meta(root),before)
                rows.append(dict(stage=fail_stage,import_status=r['workflow_status'],storage=r['storage'],read_status=read['workflow_status'],retry_status=retry['workflow_status']))
        save(OUT/'storage-unknown.json',dict(rows=rows,fault='Persisted new temp-store bytes then response lost; not real power-loss evidence'))

    def test_missing_middle_and_crossed_stage_refuse_without_repair(self):
        source=store_values(ROOT/'actual/runs/conditional-full','import-conditional-full');other=store_values(ROOT/'actual/runs/general-full','import-general-full');rows=[]
        for scenario in ('no-result','missing-generation','missing-choice','crossed-choice','crossed-result'):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);keys=op._keys('import-conditional-full');values=deepcopy(source)
                if scenario=='no-result':values.pop('result')
                if scenario=='missing-generation':values.pop('generation')
                if scenario=='missing-choice':values.pop('choice')
                if scenario=='crossed-choice':values['choice']=other['choice']
                if scenario=='crossed-result':values['result']=other['result']
                for stage,value in values.items():Journal(root).save(keys[stage],value)
                before=meta(root)
                with patch.object(op,'_source_check',side_effect=AssertionError('No recheck')),patch.object(Journal,'save',side_effect=AssertionError('No repair')):
                    read=op.read_operation(root,'import-conditional-full')
                self.assertEqual(meta(root),before)
                self.assertEqual(read['workflow_status'],'INCOMPLETE_SAVED_PREFIX' if scenario=='no-result' else 'UNREADABLE')
                rows.append(dict(scenario=scenario,status=read['workflow_status'],reasons=read['reasons']))
        save(OUT/'missing-and-crossed.json',dict(rows=rows))

    def test_fresh_cli_import_read_without_engines_selection_network_or_recheck(self):
        script='''import sys,importlib.abc,json,socket,tempfile,io,contextlib
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname in {"capital_research.core","capital_research.execution","capital_research.continuity","capital_research.quantity_candidates","capital_research.quantity_after_retry","capital_research.allocation","rotation_research.action_ledger"}:raise AssertionError("Forbidden numeric import "+fullname)
sys.meta_path.insert(0,Block())
def denied(*a,**k):raise AssertionError("Forbidden generation, choice, IO or network")
socket.socket=denied
from pathlib import Path
from capital_research import research_operation as op,research_choice as choice,quantity_choice_rules as rules,research_operation_cli as cli
from rotation_research.store import Journal
choice.choose_saved=denied;choice.select_candidate=denied;rules.select_candidate=denied
op._generation=denied;op._selection=denied;op._choice_request=denied
check=op._source_check;calls=[]
def counted(*a):calls.append(1);return check(*a)
op._source_check=counted
with tempfile.TemporaryDirectory() as tmp:
 sys.argv=["research_operation_cli","IMPORT","--store",tmp,"--id","fresh","--input",sys.argv[1],"--format","json"]
 out=io.StringIO()
 with contextlib.redirect_stdout(out):rc=cli.main()
 imported=json.loads(out.getvalue());assert rc==0 and imported["workflow_status"]=="COMPLETED_CONDITIONAL_INTENT" and len(calls)==1
 op._source_check=denied;Journal.save=denied;Path.write_text=denied;Path.write_bytes=denied;Path.mkdir=denied
 sys.argv=["research_operation_cli","READ","--store",tmp,"--id","fresh","--format","json"];out=io.StringIO()
 with contextlib.redirect_stdout(out):rc=cli.main()
 read=json.loads(out.getvalue());assert rc==0 and read["workflow_status"]=="READ_ONLY" and read["operation"]==imported["operation"]
 print(json.dumps({"import_check_calls":len(calls),"read_check_calls":0,"numeric_imports":0,"generation_calls":0,"selection_calls":0,"read_writes":0,"network_calls":0}))
'''
        run=subprocess.run([sys.executable,'-B','-c',script,str(ROOT/'cases/conditional-full/input.json')],cwd=PROJECT,
            env={**os.environ,'PYTHONPATH':str(PROJECT),'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
        save(OUT/'fresh-cli.json',dict(returncode=run.returncode,stdout=run.stdout,stderr=run.stderr));self.assertEqual(run.returncode,0,run.stderr)

    def test_legacy_read_exact_and_existing_run_no_producer(self):
        for row in load(ROOT/'case-index.json')['legacy']:
            prior=load(ROOT/'legacy'/row['name']/'before.json');after=load(ROOT/'actual/legacy'/row['name']/'read.json')
            self.assertEqual(prior,after)
        control=load(ROOT/'case-index.json')['legacy'][0];root=REPO/control['store'];keys=op._keys(control['identity'])
        req=json.loads(Journal(root).read(keys['request'])['value']['request_json']);before=meta(root)
        with (patch.object(op,'_generation',side_effect=AssertionError('Old existing RUN does not generate')),
              patch.object(op,'_selection',side_effect=AssertionError('No old selection')),
              patch.object(op,'_persist',side_effect=AssertionError('No old writes'))):
            result=op.run_operation(root,control['identity'],req)
        self.assertEqual(result['workflow_status'],'OPERATION_EXISTS_READ_REQUIRED');self.assertEqual(meta(root),before)
        save(OUT/'legacy.json',dict(exact_read_controls=5,existing_run_no_producer=True,old_files_unchanged=True))

    def test_decimal_context_input_and_qualification_are_unchanged(self):
        x=request('checkpoint-new-trigger');before=deepcopy(x)
        with tempfile.TemporaryDirectory() as tmp:
            with localcontext(Context(prec=2,rounding=ROUND_UP,Emin=-2,Emax=2,clamp=1)) as ctx:
                ctx.traps[Inexact]=True;ctx.traps[Rounded]=True;saved=str(ctx)
                r=op.import_operation(tmp,'import-checkpoint-new-trigger',x);read=op.read_operation(tmp,'import-checkpoint-new-trigger')
                self.assertEqual(str(ctx),saved)
            self.assertEqual(r['workflow_status'],'COMPLETED_CONDITIONAL_INTENT');self.assertEqual(r,receipt('checkpoint-new-trigger'))
            self.assertEqual(read['workflow_status'],'READ_ONLY')
        self.assertEqual(x,before)
        save(OUT/'purity.json',dict(input_unchanged=True,full_decimal_context_preserved=True,account_changes=0,orders=0,fills=0,numeric_runs=0,market_samples=0))
