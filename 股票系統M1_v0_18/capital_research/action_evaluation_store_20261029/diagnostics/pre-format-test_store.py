"""Targeted immutable IMPORT/READ checks; no evaluation or account producer."""
from copy import deepcopy
import ast,decimal,json,os,subprocess,sys,tempfile,unittest,hashlib
from pathlib import Path
from unittest.mock import patch
from .freeze import ROOT,PROJECT,REPO,load,save,info,resign
from capital_research.lifecycle import _fp,FLAGS
from capital_research.action_evaluation_store import import_evaluation,read_evaluation,CHECKED,DECLARED
from rotation_research.store import Journal

OUT=ROOT/os.environ.get('ACTION_STORE_TEST_STAGE','validation')
def request(name='exit-B7'):return load(ROOT/'cases'/name/'input.json')
def imported(name):return load(ROOT/'actual'/name/'import.json')
def content(p):return hashlib.sha256(p.read_bytes()).hexdigest()


class ImportReadTests(unittest.TestCase):
    def test_01_all_frozen_originals_and_expected_statuses(self):
        intake=load(ROOT/'intake.json')
        for m in load(ROOT/'frozen.json')['files']+intake['protected']+intake['source_originals']+load(ROOT/'actual/source-versions.json')['files']:
            self.assertEqual(info(REPO/m['path']),m)
        for pair in intake['changing_sources']:self.assertEqual(info(REPO/pair['archived']['path']),pair['archived'])
        summary=load(ROOT/'actual/summary.json');self.assertTrue(summary['all_expected_matched']);self.assertTrue(summary['all_inputs_unchanged'])
        for name in load(ROOT/'case-index.json')['cases']:
            a=imported(name);expected=load(ROOT/'cases'/name/'expected.json')
            self.assertEqual(a['storage_status'],expected['storage_status']);self.assertTrue(all(a[k] is False for k in FLAGS));self.assertIsNone(a['primary_pressure_id'])
            if expected['storage_status']=='NOT_SAVED':self.assertIsNone(a['record']);self.assertFalse((ROOT/'actual/records'/(name+'.json')).exists())
        save(OUT/'preservation.json',dict(all_frozen_originals_and_source_versions_matched=True,old_catalog_qualifications_unchanged=True))

    def test_02_full_payload_rights_token_preservation_and_refused_separation(self):
        rows=[]
        for name in ('exit-B7','reduce-B3','continued-partial','partial-prefix','stopped-action'):
            q=request(name);r=imported(name);v=r['record'];read=load(ROOT/'actual'/name/'read.json')
            self.assertEqual(v['import_input'],q);self.assertEqual(v['evaluation_input_id'],_fp(q['evaluation_input']))
            self.assertEqual(v['source_document_id'],_fp(q['evaluation_input']['saved_result']));self.assertEqual(v['evaluation_id'],q['evaluation']['evaluation_id'])
            self.assertEqual(read['record'],v);self.assertEqual(read['storage_status'],'READ_ONLY')
            self.assertEqual(load(ROOT/'actual/records'/(name+'.json'))['value'],v)
            expected_scope=CHECKED if q['evaluation']['status']=='EVALUATED' else DECLARED
            self.assertEqual(v['association_scope'],expected_scope);self.assertEqual(read['evaluation_status'],q['evaluation']['status'])
            if q['evaluation']['status']=='REFUSED':self.assertIsNone(v['import_input']['evaluation']['statistics'])
            else:
                a=v['import_input']['evaluation']['account'];self.assertEqual(a['origin_initial_capital'],'1180');self.assertEqual(a['general_reserved_cash'],'100');self.assertEqual(len(a['reviewed_evidence_tokens']),9)
            rows.append(dict(name=name,storage=r['storage_status'],evaluation=r['evaluation_status'],scope=expected_scope,original_payload_exact=True))
        save(OUT/'payload-preservation.json',rows)

    def test_03_source_validator_move_and_evaluator_body_are_byte_exact(self):
        old=(ROOT/'baseline/action_account_metrics.py').read_text();new=(PROJECT/'capital_research/saved_action_source.py').read_text()
        wrapper=(PROJECT/'capital_research/action_account_metrics.py').read_text()
        def funcs(s):return {n.name:ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
        previous=funcs(old);moved=funcs(new);current=funcs(wrapper)
        self.assertEqual(previous['evaluate_saved'],current['evaluate_saved'])
        for name in ('_research','_close','_pair','_account_binding','_action','_continuation','_snapshots'):self.assertEqual(previous[name],moved[name],name)
        self.assertNotIn('account_metrics',new.split('from copy')[1].split('SOURCE=')[0])
        save(OUT/'pure-move-regression.json',dict(source_functions_byte_identical=7,evaluator_body_byte_identical=True,new_evaluations=0))

    def test_04_identity_idempotence_conflict_invalid_ids_and_symlink(self):
        rows=[]
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'records';q=request();before=deepcopy(q)
            first=import_evaluation(root,'fixed',q);p=root/'fixed.json';b=p.read_bytes();time=p.stat().st_mtime_ns
            same=import_evaluation(root,'fixed',q);self.assertEqual(first,same);self.assertEqual(p.read_bytes(),b);self.assertEqual(p.stat().st_mtime_ns,time)
            different=import_evaluation(root,'fixed',request('reduce-B3'));self.assertEqual(different['storage_status'],'NOT_SAVED');self.assertEqual(p.read_bytes(),b)
            for key in ('../escape','', 'x'*91):self.assertEqual(import_evaluation(root,key,q)['storage_status'],'NOT_SAVED')
            target=Path(temp)/'target';target.write_text('ORIGINAL');link=root/'linked.json';link.symlink_to(target)
            self.assertEqual(import_evaluation(root,'linked',q)['storage_status'],'NOT_SAVED');self.assertEqual(read_evaluation(root,'linked')['storage_status'],'UNREADABLE')
            self.assertEqual(target.read_text(),'ORIGINAL');self.assertTrue(link.is_symlink());self.assertEqual(q,before)
            rows.append(dict(same_content_no_write=True,different_content_preserved=True,invalid_identity_refused=True,symlink_preserved=True,input_unchanged=True))
        save(OUT/'identity-controls.json',rows)

    def test_05_unknown_before_after_write_readback_and_partial_file(self):
        q=request();rows=[];original=Journal.save
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'before'
            with patch.object(Journal,'save',side_effect=OSError('SYNTHETIC_BEFORE_WRITE')):a=import_evaluation(root,'case',q)
            self.assertEqual(a['storage_status'],'UNKNOWN');self.assertEqual(read_evaluation(root,'case')['storage_status'],'NOT_FOUND')
            rows.append(dict(fault='before-write',import_status=a['storage_status'],read_status='NOT_FOUND'))
            def after_write(store,key,value):original(store,key,value);raise OSError('SYNTHETIC_AFTER_WRITE')
            root=Path(temp)/'after'
            with patch.object(Journal,'save',after_write):a=import_evaluation(root,'case',q)
            self.assertEqual(a['storage_status'],'UNKNOWN');b=read_evaluation(root,'case');self.assertEqual(b['storage_status'],'READ_ONLY')
            rows.append(dict(fault='after-write',import_status=a['storage_status'],read_status=b['storage_status'],evaluation=b['evaluation_status']))
            root=Path(temp)/'readback'
            with patch.object(Journal,'read',return_value={'value':{'WRONG_READBACK':True}}):a=import_evaluation(root,'case',q)
            self.assertEqual(a['storage_status'],'UNKNOWN');self.assertEqual(read_evaluation(root,'case')['storage_status'],'READ_ONLY')
            rows.append(dict(fault='readback-mismatch',import_status=a['storage_status'],read_status='READ_ONLY'))
            def partial(store,key,value):
                store.root.mkdir(parents=True);store.path(key).write_bytes(b'{"schema":');raise OSError('SYNTHETIC_PARTIAL_WRITE')
            root=Path(temp)/'partial'
            with patch.object(Journal,'save',partial):a=import_evaluation(root,'case',q)
            p=root/'case.json';before=p.read_bytes();b=read_evaluation(root,'case')
            self.assertEqual(a['storage_status'],'UNKNOWN');self.assertEqual(b['storage_status'],'UNREADABLE');self.assertEqual(p.read_bytes(),before)
            rows.append(dict(fault='partial-write',import_status=a['storage_status'],read_status=b['storage_status'],partial_bytes=before.decode(),preserved=True))
        save(OUT/'storage-faults.json',rows)

    def test_06_read_rejects_missing_corrupt_or_cross_bound_records(self):
        rows=[];base=load(ROOT/'actual/records/exit-B7.json')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.assertEqual(read_evaluation(root,'missing')['storage_status'],'NOT_FOUND')
            for name in ('wrapper-id','record-id','cross-source','qualified','record-schema'):
                entry=deepcopy(base);entry['id']=name;v=entry['value'];v['operation_id']=name
                if name=='wrapper-id':entry['id']='another'
                elif name=='record-id':v['record_id']='wrong'
                elif name in ('cross-source','qualified'):
                    v['import_input']=request(name);v['import_input_id']=_fp(v['import_input']);v['evaluation_input_id']=v['import_input']['expected_evaluation_input_id'];v['evaluation_id']=v['import_input']['expected_evaluation_id']
                elif name=='record-schema':v['schema']='unknown/99'
                if name!='record-id':v['record_id']=_fp({k:x for k,x in v.items() if k!='record_id'})
                p=root/(name+'.json');save(p,entry);before=p.read_bytes();a=read_evaluation(root,name)
                self.assertEqual(a['storage_status'],'UNREADABLE',name);self.assertIsNone(a['record']);self.assertEqual(p.read_bytes(),before)
                rows.append(dict(name=name,status=a['storage_status'],reasons=a['reasons'],original_preserved=True))
            p=root/'broken.json';p.write_bytes(b'{');self.assertEqual(read_evaluation(root,'broken')['storage_status'],'UNREADABLE');self.assertEqual(p.read_bytes(),b'{')
        save(OUT/'read-rejections.json',rows)

    def test_07_fresh_cli_import_read_forbid_numeric_and_read_writes(self):
        code='''import sys,importlib.abc,json,io,builtins
from pathlib import Path
from unittest.mock import patch
bad=('capital_research.account_metrics','capital_research.action_account_metrics','capital_research.core','capital_research.execution','capital_research.execution_continuation','capital_research.continuity','capital_research.cash_action','capital_research.cash_action_execution','capital_research.quantity_replay','capital_research.quantity_candidates','rotation_research.action_ledger')
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if any(fullname==x or fullname.startswith(x+'.') for x in bad):raise AssertionError('FORBIDDEN_PRODUCER_OR_EVALUATOR:'+fullname)
sys.meta_path.insert(0,Guard())
from capital_research.action_evaluation_store_cli import main
from rotation_research.store import Journal
mode,root,source=sys.argv[1:]
sys.argv=['storage',mode,'--root',root,'--id','fresh']+(['--input',source] if mode=='IMPORT' else [])
if mode=='IMPORT':
 with patch('socket.socket',side_effect=AssertionError('NO_NETWORK')):status=main()
else:
 original=io.open
 def read_only(file,mode='r',*args,**kwargs):
  if any(x in mode for x in 'wax+'):raise AssertionError('READ_WRITE_FORBIDDEN')
  return original(file,mode,*args,**kwargs)
 with patch.object(Journal,'save',side_effect=AssertionError('NO_SAVE_ON_READ')),patch('pathlib.Path.mkdir',side_effect=AssertionError('NO_MKDIR_ON_READ')),patch('io.open',read_only),patch('builtins.open',read_only),patch('os.open',side_effect=AssertionError('NO_OS_OPEN_ON_READ')),patch('socket.socket',side_effect=AssertionError('NO_NETWORK')):status=main()
sys.exit(status)
'''
        rows=[]
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'records';source=ROOT/'cases/exit-B7/input.json';before=None
            for mode in ('IMPORT','READ'):
                p=subprocess.run([sys.executable,'-c',code,mode,str(root),str(source)],cwd=PROJECT,text=True,capture_output=True)
                save(OUT/'fresh'/('import.json' if mode=='IMPORT' else 'read.json'),dict(returncode=p.returncode,stderr=p.stderr,stdout=p.stdout))
                self.assertEqual(p.returncode,0,p.stderr);r=json.loads(p.stdout);self.assertEqual(r['storage_status'],'SAVED_AND_READ_BACK' if mode=='IMPORT' else 'READ_ONLY')
                self.assertEqual(r['record']['import_input'],request());self.assertTrue(all(r[k] is False for k in FLAGS))
                state={p.name:content(p) for p in root.iterdir()}
                if mode=='READ':self.assertEqual(state,before)
                before=state;rows.append(dict(mode=mode,forbidden_producers_and_evaluators_not_imported=True,read_writes_blocked=mode=='READ'))
        save(OUT/'fresh/summary.json',rows)

    def test_08_hostile_contexts_do_not_change_receipts_input_or_caller(self):
        def snapshot(ctx):return dict(prec=ctx.prec,rounding=ctx.rounding,Emin=ctx.Emin,Emax=ctx.Emax,capitals=ctx.capitals,clamp=ctx.clamp,
            traps={k.__name__:v for k,v in ctx.traps.items()},flags={k.__name__:v for k,v in ctx.flags.items()})
        q=request();old=deepcopy(q);default=snapshot(decimal.DefaultContext);rows=[]
        with tempfile.TemporaryDirectory() as temp:
            normal=import_evaluation(Path(temp)/'normal','same',q)
            for i,rounding in enumerate((decimal.ROUND_UP,decimal.ROUND_DOWN)):
                with decimal.localcontext(decimal.Context(prec=3,rounding=rounding,Emin=-2,Emax=2,traps=[decimal.Inexact,decimal.Overflow,decimal.Clamped])) as caller:
                    before=snapshot(caller);a=import_evaluation(Path(temp)/str(i),'same',q);b=read_evaluation(Path(temp)/str(i),'same')
                    self.assertEqual(a,normal);self.assertEqual(b['record'],normal['record']);self.assertEqual(snapshot(caller),before)
                    self.assertEqual(snapshot(decimal.DefaultContext),default);self.assertEqual(q,old)
                    rows.append(dict(context=i,receipt_equal=True,read_record_equal=True,caller_default_and_input_unchanged=True))
        save(OUT/'context-controls.json',rows)

if __name__=='__main__':unittest.main()
