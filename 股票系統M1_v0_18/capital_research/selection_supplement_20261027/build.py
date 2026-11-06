"""New explicit SELECT/READ evidence; all parents are immutable saved operations."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
from rotation_research.store import Journal
from capital_research import selection_supplement as supplement
from capital_research.selection_supplement_cli import render_text
from capital_research.lifecycle import _fp

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]

GUARD=r'''
import sys,os,json,runpy,importlib.abc
mode,root=sys.argv[1:3];root=os.path.abspath(root);args=sys.argv[3:];counts=dict(generation=0,choice=0,source_check=0)
allowed={'capital_research.selection_supplement','capital_research.selection_supplement_cli',
 'capital_research.research_operation','capital_research.research_choice',
 'capital_research.research_choice_workflow','capital_research.quantity_choice_rules',
 'capital_research.lifecycle','rotation_research.store'}
if mode=='SELECT':allowed.add('capital_research.research_choice_source')
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith('graph_core') or (fullname.startswith(('capital_research.','rotation_research.')) and fullname not in allowed):raise RuntimeError('NUMERIC_IMPORT_FORBIDDEN:'+fullname)
sys.meta_path.insert(0,Guard())
def audit(event,args):
 if event=='open':
  m,f=args[1:3];write=(m and any(c in m for c in 'wax+')) or f&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
  if write:
   path=os.readlink('/proc/self/fd/'+str(args[0])) if isinstance(args[0],int) else os.path.abspath(str(args[0]))
   if mode=='READ' or not path.startswith(root+os.sep):raise RuntimeError('WRITE_FORBIDDEN')
 if event=='os.mkdir' and (mode=='READ' or (os.path.abspath(args[0])!=root and not os.path.abspath(args[0]).startswith(root+os.sep))):raise RuntimeError('MKDIR_FORBIDDEN')
 if event in ('os.remove','os.rename','subprocess.Popen','socket.connect'):raise RuntimeError('SIDE_EFFECT:'+event)
def profile(frame,event,arg):
 if event!='call':return
 p=frame.f_code.co_filename;n=frame.f_code.co_name
 if '/capital_research/' in p and n in ('_generation','generate_after_retry','simulate','decide','resume_decision'):raise RuntimeError('GENERATION_FORBIDDEN')
 if p.endswith('/research_choice.py') and n=='choose_saved':
  if mode=='READ':raise RuntimeError('READ_SELECTION_FORBIDDEN')
  counts['choice']+=1
 if p.endswith('/research_choice_source.py') and n=='check_saved':
  if mode=='READ':raise RuntimeError('READ_CHECK_FORBIDDEN')
  counts['source_check']+=1
 if mode=='READ' and p.endswith('/rotation_research/store.py') and n=='save':raise RuntimeError('READ_SAVE_FORBIDDEN')
sys.addaudithook(audit);sys.setprofile(profile);sys.argv=['supplement',mode]+args
try:runpy.run_module('capital_research.selection_supplement_cli',run_name='__main__')
except SystemExit as exc:code=exc.code
sys.setprofile(None);print('__SUP_COUNTS__'+json.dumps(counts),file=sys.stderr);raise SystemExit(code)
'''


def load(p):return json.loads(p.read_text())


def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def files(folder):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}


def command(mode,parent,pid,store,identity,input_path=None,fmt='json'):
    args=['--parent-store',str(parent),'--parent-id',pid,'--store',str(store),'--id',identity,'--format',fmt]
    if input_path is not None:args+=['--input',str(input_path)]
    p=subprocess.run([sys.executable,'-B','-c',GUARD,mode,str(store)]+args,cwd=PROJECT,text=True,capture_output=True)
    marker=next((s for s in p.stderr.splitlines() if s.startswith('__SUP_COUNTS__')),None)
    return dict(exit_code=p.returncode,stdout=p.stdout,
        stderr='\n'.join(s for s in p.stderr.splitlines() if s!=marker),
        calls=json.loads(marker[len('__SUP_COUNTS__'):]) if marker else None,
        guard='NO_NUMERIC_IMPORT_OR_GENERATION_NO_NETWORK;SELECT_ONLY_CHILD_WRITE;READ_NO_SELECT_CHECK_SAVE_WRITE')


def no_compute_read(parent,pid,store,identity):
    with patch.object(supplement,'_choose',side_effect=AssertionError('READ_SELECT')), \
         patch.object(supplement,'_check',side_effect=AssertionError('READ_CHECK')), \
         patch.object(Journal,'save',side_effect=AssertionError('READ_SAVE')):
        return supplement.read_supplement(parent,pid,store,identity)


def main():
    rows=[];specs=load(ROOT/'input-expected.json')
    for spec in specs:
        name=spec['name'];expected=spec['expected'];parent=PROJECT/spec['parent_store'];pid=spec['parent_id']
        for ref in spec['parent_sources']:
            b=(PROJECT/ref['path']).read_bytes()
            assert len(b)==ref['bytes'] and hashlib.sha256(b).hexdigest()==ref['sha256']
        assert _fp(spec['request'])==spec['input_id']
        store=parent if spec['overlap'] else ROOT/'runs'/name
        if not spec['overlap']:store.mkdir(parents=True,exist_ok=False)
        identity=pid if spec['overlap'] else 'supp-'+name
        input_path=ROOT/'inputs'/(name+'.json');save(input_path,spec['request'])
        parent_before=files(parent)
        receipt=command('SELECT',parent,pid,store,identity,input_path)
        save(ROOT/'actual'/name/'CLI-select.json',receipt)
        assert not receipt['stderr'],receipt
        value=json.loads(receipt['stdout']);save(ROOT/'actual'/name/'select.json',value)
        assert value['workflow_status']==expected['status'],value
        if expected['reason']:assert expected['reason'] in value['reasons'],value
        assert receipt['calls']==dict(generation=0,choice=expected['choice_calls'],source_check=expected['check_calls']),receipt
        assert files(parent)==parent_before
        save(ROOT/'actual'/name/'parent-preservation.json',dict(before=parent_before,after=files(parent)))
        with (ROOT/'actual'/name/'readable.txt').open('x') as f:f.write(render_text(value))
        if expected['choice_calls']:
            before=files(store);read=command('READ',parent,pid,store,identity)
            save(ROOT/'actual'/name/'CLI-read.json',read)
            assert not read['stderr'] and read['calls']==dict(generation=0,choice=0,source_check=0),read
            read_value=json.loads(read['stdout'])
            assert read_value['workflow_status']=='READ_ONLY' and read_value['supplement']==value['supplement']
            assert files(store)==before
            save(ROOT/'actual'/name/'child-preservation.json',dict(before=before,after=files(store)))
            text=command('READ',parent,pid,store,identity,fmt='text')
            save(ROOT/'actual'/name/'CLI-read-text.json',text)
            assert not text['stderr'] and text['stdout']==render_text(read_value),text
        elif not spec['overlap']:
            assert not list(store.iterdir())
        rows.append(dict(name=name,status='PASS',workflow_status=value['workflow_status'],calls=receipt['calls']))
        print(name,'PASS',flush=True)
    save(ROOT/'summary.json',rows)
    base=specs[0];parent=PROJECT/base['parent_store'];pid=base['parent_id'];request=base['request'];store=ROOT/'runs/general';identity='supp-general'
    before=files(store)
    with patch.object(supplement,'_choose',side_effect=AssertionError('DUPLICATE_SELECTION')):
        repeat=supplement.select_supplement(parent,pid,store,identity,request)
        changed=deepcopy(request);changed['selection']['reason']='DIFFERENT_EXPLICIT_REASON'
        conflict=supplement.select_supplement(parent,pid,store,identity,changed)
    assert repeat['workflow_status']=='SUPPLEMENT_EXISTS_READ_REQUIRED'
    assert conflict['workflow_status']=='SUPPLEMENT_ID_CONFLICT' and files(store)==before
    save(ROOT/'idempotence.json',dict(repeat=repeat,conflict=conflict,before=before,after=files(store)))
    fault_rows=[];real_save=Journal.save
    for fault in load(ROOT/'fault-input-expected.json'):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder);child='fault'
            def injected(self,key,value):
                record=real_save(self,key,value)
                if key.endswith('--'+fault['stage']):raise OSError('INJECTED_AFTER_CHILD_SAVE:'+fault['stage'])
                return record
            with patch.object(Journal,'save',injected),patch.object(supplement,'_choose',wraps=supplement._choose) as chosen, \
                 patch.object(supplement,'_check',wraps=supplement._check) as checked:
                value=supplement.select_supplement(parent,pid,target,child,request)
            assert value['workflow_status']=='STOPPED_STORAGE' and value['storage'][fault['stage']]=='UNKNOWN',value
            assert chosen.call_count==fault['expected_select_calls'] and checked.call_count==fault['expected_check_calls']
            before=files(target);read=no_compute_read(parent,pid,target,child)
            assert read['workflow_status']==fault['READ_status'] and files(target)==before,read
            fault_rows.append(dict(stage=fault['stage'],actual=value,explicit_READ=read,
                choice_calls=chosen.call_count,check_calls=checked.call_count,before=before,after=files(target)))
    save(ROOT/'fault-actual.json',fault_rows)
    corruptions=[]
    for name in ['cross-result','missing-choice','missing-choice-token']:
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'child';shutil.copytree(store,target)
            if name=='cross-result':
                p=target/(identity+'--result.json');r=load(p)
                r['value']=load(ROOT/'runs/conditional/supp-conditional--result.json')['value'];p.write_text(json.dumps(r,ensure_ascii=False))
            elif name=='missing-choice':(target/(identity+'--choice.json')).unlink()
            else:
                p=target/(identity+'--choice.json');r=load(p);c=r['value']['choice']
                c['source_binding']['historical_reviewed_tokens']=[];c['record_id']=_fp({k:v for k,v in c.items() if k!='record_id'})
                p.write_text(json.dumps(r,ensure_ascii=False))
            before=files(target);read=no_compute_read(parent,pid,target,identity)
            assert read['workflow_status']=='UNREADABLE' and files(target)==before,read
            corruptions.append(dict(name=name,actual=read,before=before,after=files(target)))
    with tempfile.TemporaryDirectory() as folder:
        temp=Path(folder);prefix=temp/'parent';shutil.copytree(parent,prefix)
        (prefix/(pid+'--result.json')).unlink();before=files(prefix);target=temp/'must-not-create'
        value=supplement.select_supplement(prefix,pid,target,'new',request)
        assert value['workflow_status']=='PARENT_REFUSED' and value['reasons']==['PARENT_NOT_COMPLETE']
        assert not target.exists() and files(prefix)==before
        corruptions.append(dict(name='parent-prefix-only',actual=value,before=before,after=files(prefix)))
    save(ROOT/'corruption-actual.json',corruptions)


if __name__=='__main__':main()
