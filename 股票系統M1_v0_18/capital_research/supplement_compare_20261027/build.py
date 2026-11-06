"""New stdout READ evidence only. No producer, choice or account calls."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from .prepare import ROOT,PROJECT,load,save

GUARD=r'''
import sys,os,json,runpy,importlib.abc
allowed={'capital_research.supplement_compare','capital_research.supplement_compare_read',
 'capital_research.selection_supplement','capital_research.research_operation',
 'capital_research.research_choice','capital_research.quantity_choice_rules',
 'capital_research.lifecycle','capital_research.lifecycle_compare','rotation_research.store'}
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith('graph_core') or (fullname.startswith(('capital_research.','rotation_research.')) and fullname not in allowed):raise RuntimeError('NUMERIC_IMPORT_FORBIDDEN:'+fullname)
sys.meta_path.insert(0,Guard());reads=[]
def audit(event,args):
 if event=='open':
  m,f=args[1:3]
  if (m and any(c in m for c in 'wax+')) or f&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('WRITE_FORBIDDEN')
 if event in ('os.mkdir','os.remove','os.rename','subprocess.Popen','socket.connect'):raise RuntimeError('SIDE_EFFECT:'+event)
def profile(frame,event,arg):
 p=frame.f_code.co_filename;n=frame.f_code.co_name
 if event=='call' and ('/capital_research/' in p or p.endswith('/rotation_research/store.py')):
  if n in ('_generation','generate_after_retry','simulate','decide','resume_decision','choose_saved','select_candidate','select_and_save','check_saved','save'):raise RuntimeError('READ_RUN_OR_SAVE_FORBIDDEN:'+n)
 if event=='return' and p.endswith('/selection_supplement.py') and n=='read_supplement' and isinstance(arg,dict):
  b=arg.get('parent_binding') or {};s=b.get('source_binding') or {}
  reads.append(dict(status=arg.get('workflow_status'),supplement_id=arg.get('supplement_id'),parent_id=b.get('parent_operation_id'),parent_result_id=b.get('parent_result_id'),generation_id=b.get('generation_id'),account_id=s.get('account_id'),data_cutoff=s.get('data_cutoff')))
sys.addaudithook(audit);sys.setprofile(profile);sys.argv=['compare']+sys.argv[1:]
try:runpy.run_module('capital_research.supplement_compare_read',run_name='__main__')
except SystemExit as exc:code=exc.code
sys.setprofile(None);print('__READ_TRACE__'+json.dumps(reads),file=sys.stderr);raise SystemExit(code)
'''


def command(path,fmt=None):
    args=['--input',str(path)]+(['--format',fmt] if fmt else [])
    p=subprocess.run([sys.executable,'-B','-c',GUARD]+args,cwd=PROJECT,text=True,capture_output=True)
    marker=next((s for s in p.stderr.splitlines() if s.startswith('__READ_TRACE__')),None)
    return dict(exit_code=p.returncode,stdout=p.stdout,stderr='\n'.join(s for s in p.stderr.splitlines() if s!=marker),
        original_READ_trace=json.loads(marker[len('__READ_TRACE__'):]) if marker else None,
        guard='FRESH_NO_ENGINE_NO_GENERATION_NO_SELECTION_NO_SOURCE_VERDICT_NO_SAVE_NO_WRITE_NO_NETWORK')


def sources():
    intake=load(ROOT/'intake.json')
    paths=[PROJECT/v['path'] for v in intake['originals']]
    paths+=list((ROOT/'fixtures').rglob('*.json'))
    return {str(p.relative_to(PROJECT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def main():
    before=sources();rows=[]
    for row in load(ROOT/'case-index.json'):
        name=row['name'];path=ROOT/'cases'/name/'input.json';expected=load(path.with_name('expected.json'))
        receipt=command(path,'json');save(ROOT/'actual'/name/'CLI-json.json',receipt)
        assert not receipt['stderr'],receipt
        result=json.loads(receipt['stdout'])['comparison'];save(ROOT/'actual'/name/'result.json',result)
        assert result['status']==expected['status'] and len(result['columns'])==expected['columns'],result
        if expected['reason']:assert any(v['reason']==expected['reason'] for v in result['refusals']),result
        assert receipt['exit_code']==(0 if expected['status']=='COMPARABLE' else 2)
        text=command(path);save(ROOT/'actual'/name/'CLI-text.json',text)
        assert not text['stderr'] and text['exit_code']==receipt['exit_code'],text
        with (ROOT/'actual'/name/'readable.txt').open('x') as f:f.write(text['stdout'])
        if name in ('duplicate-label','resource-limit'):assert receipt['original_READ_trace']==[]
        rows.append(dict(name=name,status='PASS',comparison_status=result['status'],columns=len(result['columns'])))
        print(name,'PASS',flush=True)
    after=sources();assert before==after
    save(ROOT/'preservation.json',dict(before=before,after=after))
    save(ROOT/'summary.json',rows)


if __name__=='__main__':main()
