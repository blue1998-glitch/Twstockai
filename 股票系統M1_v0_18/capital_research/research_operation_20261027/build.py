"""Five new explicit synthetic RUNs; READ guards and bounded injected faults."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback
from unittest.mock import patch
from rotation_research.store import Journal
from capital_research import research_operation as op
from capital_research.research_operation_cli import render_text
from .fixtures import ROOT,PROJECT,load,materialize,fp

READ_GUARD = r'''
import sys,os,runpy,importlib.abc
allowed={'capital_research.research_operation','capital_research.research_operation_cli',
 'capital_research.research_choice','capital_research.quantity_choice_rules',
 'capital_research.lifecycle','rotation_research.store'}
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith('graph_core') or (fullname.startswith(('capital_research.','rotation_research.')) and fullname not in allowed):raise RuntimeError('READ_ENGINE_IMPORT:'+fullname)
sys.meta_path.insert(0,Guard())
def audit(event,args):
 if event=='open':
  mode,flags=args[1:3]
  if (mode and any(c in mode for c in 'wax+')) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('READ_WRITE_FORBIDDEN')
 if event in ('os.mkdir','os.remove','os.rename','subprocess.Popen','socket.connect'):raise RuntimeError('READ_SIDE_EFFECT:'+event)
def profile(frame,event,arg):
 if event=='call' and frame.f_code.co_name in ('_generation','_selection','_source_check','choose_saved','select_candidate','select_and_save','check_saved','save'):
  if '/capital_research/' in frame.f_code.co_filename or frame.f_code.co_filename.endswith('/rotation_research/store.py'):raise RuntimeError('READ_RUN_FORBIDDEN')
sys.addaudithook(audit);sys.setprofile(profile)
sys.argv=['operation','READ']+sys.argv[1:]
runpy.run_module('capital_research.research_operation_cli',run_name='__main__')
'''

RUN_TRACE = r'''
import sys,os,json,runpy
root=os.path.abspath(sys.argv[1]);args=sys.argv[2:];counts=dict(generation=0,choice=0,source_check=0)
def audit(event,args):
 if event=='open':
  mode,flags=args[1:3];writing=(mode and any(c in mode for c in 'wax+')) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
  if writing:
   path=os.readlink('/proc/self/fd/'+str(args[0])) if isinstance(args[0],int) else os.path.abspath(str(args[0]))
   if not path.startswith(root+os.sep):raise RuntimeError('RUN_WRITE_OUTSIDE_STORE')
 if event=='os.mkdir' and os.path.abspath(args[0])!=root and not os.path.abspath(args[0]).startswith(root+os.sep):raise RuntimeError('RUN_MKDIR_OUTSIDE_STORE')
 if event in ('os.remove','os.rename','subprocess.Popen','socket.connect'):raise RuntimeError('RUN_SIDE_EFFECT:'+event)
def profile(frame,event,arg):
 if event=='call':
  p=frame.f_code.co_filename;n=frame.f_code.co_name
  if p.endswith('/quantity_after_retry.py') and n=='generate_after_retry':counts['generation']+=1
  if p.endswith('/research_choice.py') and n=='choose_saved':counts['choice']+=1
  if p.endswith('/research_choice_source.py') and n=='check_saved':counts['source_check']+=1
sys.addaudithook(audit);sys.setprofile(profile);sys.argv=['operation','RUN']+args
try:runpy.run_module('capital_research.research_operation_cli',run_name='__main__')
except SystemExit as exc:code=exc.code
sys.setprofile(None);print('__CALL_COUNTS__'+json.dumps(counts),file=sys.stderr);raise SystemExit(code)
'''


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def files(folder):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}


def read_cli(store,identity,fmt='json'):
    p=subprocess.run([sys.executable,'-B','-c',READ_GUARD,'--store',str(store),'--id',identity,'--format',fmt],
        cwd=PROJECT,text=True,capture_output=True)
    return dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,
        guard='FRESH_READ_NO_ENGINE_NO_GENERATION_NO_SELECTION_NO_SOURCE_CHECK_NO_SAVE_NO_WRITE_NO_NETWORK')


def no_run_read(store,identity):
    with patch.object(op,'_generation',side_effect=AssertionError('READ_GENERATE')), \
         patch.object(op,'_selection',side_effect=AssertionError('READ_SELECT')), \
         patch.object(op,'_source_check',side_effect=AssertionError('READ_CHECK')), \
         patch.object(Journal,'save',side_effect=AssertionError('READ_SAVE')):
        return op.read_operation(store,identity)


def main(stage):
    out=ROOT/stage;out.mkdir(exist_ok=False);rows=[];requests={}
    for row in load(ROOT/'input-expected.json'):
        spec=row['input'];expected=row['expected'];name=spec['name'];identity='demo-'+name
        request=materialize(spec);before=deepcopy(request);assert fp(request)==spec['materialized_input_id']
        requests[name]=request;store=out/'runs'/name;store.mkdir(parents=True)
        try:
            if name=='general':
                p=subprocess.run([sys.executable,'-B','-c',RUN_TRACE,str(store),'--store',str(store),
                    '--id',identity,'--input',str(ROOT/'example-request.json'),'--format','json'],
                    cwd=PROJECT,text=True,capture_output=True)
                trace_line=next(s for s in p.stderr.splitlines() if s.startswith('__CALL_COUNTS__'))
                counts=json.loads(trace_line[len('__CALL_COUNTS__'):]);receipt=json.loads(p.stdout)
                assert p.returncode==0 and p.stderr.strip()==trace_line
                save(out/'actual'/name/'CLI-run.json',dict(exit_code=p.returncode,stdout=p.stdout,
                    stderr='',call_counts=counts,guard='RUN_ONLY_WRITES_EXPLICIT_STORE_NO_NETWORK'))
            else:
                real_generation=op._generation
                with patch.object(op,'_generation',wraps=real_generation) as generated:
                    receipt=op.run_operation(store,identity,request)
                counts=dict(generation=generated.call_count)
            save(out/'actual'/name/'run.json',receipt)
            assert request==before
            assert receipt['workflow_status']==expected['workflow_status'],receipt['reasons']
            assert receipt['observed']['choice_status']==expected['choice_status']
            assert receipt['observed']['check_status']==expected['check_status']
            assert counts['generation']==expected['generator_calls']
            saved_before=files(store);read=read_cli(store,identity)
            save(out/'actual'/name/'CLI-read.json',read)
            assert not read['stderr'],read
            read_value=json.loads(read['stdout'])
            assert read_value['workflow_status']=='READ_ONLY' and read_value['operation']==receipt['operation']
            assert files(store)==saved_before
            save(out/'actual'/name/'READ-preservation.json',dict(before=saved_before,after=files(store)))
            with (out/'actual'/name/'readable.txt').open('x') as f:f.write(render_text(receipt))
            rows.append(dict(name=name,status='PASS',generator_calls=counts['generation'],
                workflow_status=receipt['workflow_status'],read_outcome=read_value['operation']['outcome']))
            print(name,'PASS',flush=True)
        except Exception:
            rows.append(dict(name=name,status='FAIL',error=traceback.format_exc()))
            print(name,'FAIL',traceback.format_exc(),flush=True)
    save(out/'summary.json',rows)
    if any(v['status']!='PASS' for v in rows):raise SystemExit(1)
    general_store=out/'runs/general';general_id='demo-general';request=requests['general']
    before=files(general_store)
    with patch.object(op,'_generation',side_effect=AssertionError('DUPLICATE_GENERATION')):
        repeat=op.run_operation(general_store,general_id,request)
        changed=deepcopy(request);changed['selection']['reason']='DIFFERENT_EXPLICIT_REASON'
        conflict=op.run_operation(general_store,general_id,changed)
    assert repeat['workflow_status']=='OPERATION_EXISTS_READ_REQUIRED'
    assert conflict['workflow_status']=='OPERATION_ID_CONFLICT'
    assert files(general_store)==before
    save(out/'idempotence.json',dict(repeat=repeat,conflict=conflict,before=before,after=files(general_store)))
    cached=Journal(general_store).read(general_id+'--generation')['value'];fault_rows=[]
    original_save=Journal.save
    for fault in load(ROOT/'fault-input-expected.json')['rows']:
        with tempfile.TemporaryDirectory() as folder:
            store=Path(folder);identity='fault'
            def injected(self,key,value):
                record=original_save(self,key,value)
                if key.endswith(fault['key']):raise OSError('INJECTED_AFTER_SAVE:'+fault['key'])
                return record
            with patch.object(Journal,'save',injected),patch.object(op,'_generation',return_value=deepcopy(cached)) as generated, \
                 patch.object(op,'_selection',wraps=op._selection) as selected, \
                 patch.object(op,'_source_check',wraps=op._source_check) as checked:
                receipt=op.run_operation(store,identity,request)
            assert receipt['workflow_status']=='STOPPED_STORAGE',receipt
            assert receipt['storage'][fault['key'][2:]]=='UNKNOWN'
            assert generated.call_count==fault['expected_calls']
            assert checked.call_count==(1 if fault['key']=='--result' else 0)
            before=files(store);read=no_run_read(store,identity);assert files(store)==before
            expected_read='READ_ONLY' if fault['key']=='--result' else 'INCOMPLETE_SAVED_PREFIX'
            assert read['workflow_status']==expected_read,read
            fault_rows.append(dict(name=fault['name'],backend='INJECTED_SAVED_GENERATION_NOT_NEW_NUMERIC_RUN',
                cached_backend_calls=generated.call_count,selection_calls=selected.call_count,source_check_calls=checked.call_count,
                actual=receipt,explicit_READ=read,before_READ=before,after_READ=files(store)))
    save(out/'fault-actual.json',fault_rows)
    corruptions=[]
    for name in ['cross-generation','missing-choice','cross-result','missing-choice-token']:
        with tempfile.TemporaryDirectory() as folder:
            store=Path(folder)/'copy';shutil.copytree(general_store,store)
            if name=='cross-generation':
                p=store/(general_id+'--generation.json');row=load(p)
                row['value']=load(out/'runs/old-trigger'/('demo-old-trigger--generation.json'))['value']
                p.write_text(json.dumps(row,ensure_ascii=False))
            elif name=='missing-choice':
                (store/(general_id+'--choice.json')).unlink()
            elif name=='cross-result':
                p=store/(general_id+'--result.json');row=load(p)
                row['value']=load(out/'runs/conditional'/'demo-conditional--result.json')['value']
                p.write_text(json.dumps(row,ensure_ascii=False))
            else:
                p=store/(general_id+'--choice.json');row=load(p);c=row['value']['choice']
                c['source_binding']['historical_reviewed_tokens']=[]
                c['record_id']=fp({k:v for k,v in c.items() if k!='record_id'})
                p.write_text(json.dumps(row,ensure_ascii=False))
            before=files(store);read=no_run_read(store,general_id)
            assert read['workflow_status']=='UNREADABLE',read
            assert files(store)==before
            corruptions.append(dict(name=name,actual=read,before=before,after=files(store)))
    save(out/'corruption-actual.json',corruptions)
    with tempfile.TemporaryDirectory() as folder:
        store=Path(folder)/'must-not-create';bad=deepcopy(request);del bad['selection']
        with patch.object(op,'_generation',side_effect=AssertionError('BAD_INPUT_GENERATED')):
            receipt=op.run_operation(store,'invalid-input',bad)
        assert receipt['workflow_status']=='INPUT_REFUSED' and not store.exists()
        save(out/'missing-selection-field.json',receipt)


if __name__=='__main__':main(sys.argv[1])
