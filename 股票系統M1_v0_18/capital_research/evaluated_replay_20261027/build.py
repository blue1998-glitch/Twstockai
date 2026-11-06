"""Three explicit new synthetic RUNs, followed by guarded immutable READ."""
import json
import subprocess
import sys
from pathlib import Path
from .prepare import ROOT,PROJECT,load,save,info

GUARD=r'''
import os,sys,json,runpy,importlib.abc
from pathlib import Path
mode=sys.argv[1];store=Path(sys.argv[2]).resolve();args=sys.argv[3:];counts={'replay':0,'evaluation':0,'execution':0}
allowed={'capital_research.evaluated_replay','capital_research.evaluated_replay_cli','capital_research.research_operation',
 'capital_research.research_choice','capital_research.quantity_choice_rules','capital_research.lifecycle','rotation_research.store'}
if mode=='READ':
 class Guard(importlib.abc.MetaPathFinder):
  def find_spec(self,fullname,path=None,target=None):
   if fullname.startswith('graph_core') or (fullname.startswith(('capital_research.','rotation_research.')) and fullname not in allowed):raise RuntimeError('READ_NUMERICAL_IMPORT_FORBIDDEN:'+fullname)
 sys.meta_path.insert(0,Guard())
def audit(event,args):
 if event=='open':
  path,m,f=args[:3]
  if (m and any(c in m for c in 'wax+')) or f&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):
   target=os.readlink('/proc/self/fd/'+str(path)) if isinstance(path,int) else path
   if mode=='READ' or not Path(target).resolve().is_relative_to(store):raise RuntimeError('WRITE_FORBIDDEN:'+str(path))
 if event=='os.mkdir':
  if mode=='READ' or not Path(args[0]).resolve().is_relative_to(store):raise RuntimeError('MKDIR_FORBIDDEN')
 if event in ('os.remove','os.rename','subprocess.Popen','socket.connect','socket.getaddrinfo'):raise RuntimeError('SIDE_EFFECT:'+event)
def profile(frame,event,arg):
 if event!='call':return
 path=frame.f_code.co_filename;name=frame.f_code.co_name
 if path.endswith('/quantity_replay.py') and name=='replay_sequence':counts['replay']+=1
 if path.endswith('/account_metrics.py') and name=='evaluate_saved':counts['evaluation']+=1
 if path.endswith('/execution.py') and name=='simulate':counts['execution']+=1
 if mode=='READ' and ('/capital_research/' in path or path.endswith('/rotation_research/store.py')) and name in ('_replay','_evaluate','replay_sequence','evaluate_saved','generate','simulate','decide','resume_decision','save'):raise RuntimeError('READ_CALL_FORBIDDEN:'+name)
sys.addaudithook(audit);sys.setprofile(profile);sys.argv=['evaluated_replay',mode,'--store',str(store)]+args
try:runpy.run_module('capital_research.evaluated_replay_cli',run_name='__main__')
except SystemExit as exc:code=exc.code
sys.setprofile(None);print('__COUNTS__'+json.dumps(counts),file=sys.stderr);raise SystemExit(code)
'''


def command(mode,store,identity,input_path=None,fmt='json'):
    args=['--id',identity,'--format',fmt]
    if input_path:args+=['--input',str(input_path)]
    p=subprocess.run([sys.executable,'-B','-c',GUARD,mode,str(store)]+args,cwd=PROJECT,text=True,capture_output=True)
    trace=next((v for v in p.stderr.splitlines() if v.startswith('__COUNTS__')),None)
    return dict(exit_code=p.returncode,stdout=p.stdout,stderr='\n'.join(v for v in p.stderr.splitlines() if v!=trace),
        calls=json.loads(trace[len('__COUNTS__'):]) if trace else None,
        guard='FRESH_READ_NO_NUMERIC_NO_WRITE_NO_NETWORK' if mode=='READ' else 'FRESH_RUN_ONLY_EXPLICIT_STORE_WRITES_NO_NETWORK')


def main():
    originals={r['path']:info(PROJECT/r['path']) for r in load(ROOT/'intake.json')['originals']}
    (ROOT/'runs-final').mkdir();summary=[]
    for case in ('complete','incomplete','stopped'):
        folder=ROOT/'cases'/case;expected=load(folder/'expected.json');store=ROOT/'runs-final'/case;identity='evaluated-'+case
        request_before=info(folder/'input.json')
        run=command('RUN',store,identity,folder/'input.json');save(ROOT/'actual-final'/case/'CLI-run.json',run)
        assert not run['stderr'],run['stderr']
        r=json.loads(run['stdout']);save(ROOT/'actual-final'/case/'run.json',r)
        assert r['workflow_status']==expected['workflow_status'],r
        assert run['calls']==dict(replay=1,evaluation=1,execution=expected['execution_calls']),run
        before={p.name:info(p) for p in store.glob('*.json')}
        read=command('READ',store,identity);save(ROOT/'actual-final'/case/'CLI-read.json',read)
        assert not read['stderr'] and read['calls']==dict(replay=0,evaluation=0,execution=0),read
        after={p.name:info(p) for p in store.glob('*.json')}
        assert before==after and request_before==info(folder/'input.json')
        save(ROOT/'actual-final'/case/'preservation.json',dict(before=before,after=after))
        view=command('READ',store,identity,fmt='text');save(ROOT/'actual-final'/case/'CLI-text.json',view)
        assert not view['stderr'] and view['calls']==dict(replay=0,evaluation=0,execution=0)
        with (ROOT/'actual-final'/case/'readable.txt').open('x') as f:f.write(view['stdout'])
        summary.append(dict(name=case,workflow_status=r['workflow_status'],observed=r['observed'],calls=run['calls']))
        print(case,r['workflow_status'],run['calls'],flush=True)
    current={p:info(PROJECT/p) for p in originals};assert current==originals
    save(ROOT/'preservation.json',dict(before=originals,after=current))
    save(ROOT/'summary.json',summary)
    save(ROOT/'source-versions.json',[info(ROOT.parent/n) for n in ('evaluated_replay.py','evaluated_replay_cli.py','quantity_replay.py','account_metrics.py','research_operation.py')])


if __name__=='__main__':main()
