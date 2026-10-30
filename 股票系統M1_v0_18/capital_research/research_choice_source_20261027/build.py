"""New READ evidence only; immutable references and explicit temporary wrappers."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from capital_research.research_choice_source import check_saved
from capital_research.research_choice_source_view import render_text
from .fixtures import ROOT, PROJECT, load, materialize, fp

GUARD = r'''
import sys,os,runpy,importlib.abc
allowed={'capital_research.research_choice_source','capital_research.research_choice_source_view',
 'capital_research.research_choice_source_read','capital_research.research_choice',
 'capital_research.research_choice_workflow','capital_research.quantity_choice_rules',
 'capital_research.lifecycle','rotation_research.store'}
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith('graph_core') or (fullname.startswith(('capital_research.','rotation_research.')) and fullname not in allowed):raise RuntimeError('ENGINE_IMPORT:'+fullname)
sys.meta_path.insert(0,Guard())
def audit(event,args):
 if event=='open':
  mode,flags=args[1:3]
  if (mode and any(c in mode for c in 'wax+')) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('READ_WRITE_FORBIDDEN')
 if event in ('os.mkdir','os.remove','os.rename','subprocess.Popen','socket.connect'):raise RuntimeError('READ_SIDE_EFFECT:'+event)
def profile(frame,event,arg):
 if event=='call':
  name=frame.f_code.co_name;path=frame.f_code.co_filename
  if (name=='choose_saved' and path.endswith('/research_choice.py') or
      name=='select_candidate' and path.endswith('/quantity_choice_rules.py') or
      name=='select_and_save' and path.endswith('/research_choice_workflow.py') or
      name=='save' and path.endswith('/rotation_research/store.py')):raise RuntimeError('READ_RESELECT_OR_SAVE_FORBIDDEN')
sys.addaudithook(audit);sys.setprofile(profile)
sys.argv=['capital_research.research_choice_source_read']+sys.argv[1:]
runpy.run_module('capital_research.research_choice_source_read',run_name='__main__')
'''


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def run_cli(args):
    p = subprocess.run([sys.executable, '-B', '-c', GUARD] + args,
        cwd=PROJECT, capture_output=True, text=True)
    return dict(exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr,
        guard='FRESH_NO_ENGINE_NO_RESELECT_NO_SAVE_NO_WRITE_NO_NETWORK')


def files(folder):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in folder.rglob('*') if p.is_file()}


def main():
    rows = []
    for spec in load(ROOT / 'input-expected.json'):
        i = spec['input']; expected = spec['expected']; name = i['name']
        request = materialize(i)
        assert fp(request) == i['materialized_input_id']
        original = deepcopy(request)
        result = check_saved(**request)
        save(ROOT / 'actual' / name / 'result.json', result)
        with (ROOT / 'actual' / name / 'readable.txt').open('x') as f:
            f.write(render_text(result))
        assert request == original
        assert result['check_status'] == expected['check_status'], result
        assert len(result['columns']) == expected['columns']
        if expected['reason']:
            assert expected['reason'] in result['reasons'], result
        else:
            assert all(result[k] == expected[k] for k in ('choice_status','candidate_check','candidate_qualification'))
        with tempfile.TemporaryDirectory() as folder:
            temp = Path(folder); store = temp / 'store'; store.mkdir()
            # Literal READ fixture envelope; not a new choice or Journal.save invocation.
            save(store / 'case.json', dict(schema='rotation-record/0.1',id='case',value=request['choice_value']))
            save(temp / 'source.json', request['explicit_source'])
            before = files(temp)
            args = ['--store',str(store),'--id','case','--source',str(temp/'source.json')]
            receipt = run_cli(args + ['--format','json'])
            save(ROOT / 'actual' / name / 'cli-json.json', receipt)
            assert receipt['exit_code'] == expected['exit_code'], receipt
            if receipt['stdout']:
                assert not receipt['stderr']
                assert json.loads(receipt['stdout'])['result'] == result
            else:
                assert expected['reason'] in receipt['stderr'], receipt
            if name in ('general','conditional','rejected','wrong-source-same-candidate-id'):
                text = run_cli(args)
                save(ROOT / 'actual' / name / 'cli-text.json', text)
                assert text['exit_code'] == expected['exit_code'] and not text['stderr']
                assert text['stdout'] == render_text(result)
            after = files(temp)
            assert before == after
            save(ROOT / 'actual' / name / 'read-preservation.json',dict(before=before,after=after))
        rows.append(dict(name=name,status='PASS',check_status=result['check_status'],
            choice_status=result['choice_status'],columns=len(result['columns'])))
        print(name,'PASS',flush=True)
    save(ROOT / 'actual' / 'summary.json', rows)
    with tempfile.TemporaryDirectory() as folder:
        temp = Path(folder); store = temp / 'store'; store.mkdir()
        first = materialize(load(ROOT/'input-expected.json')[0]['input'])
        save(store/'case.json',dict(schema='rotation-record/0.1',id='other',value=first['choice_value']))
        save(temp/'source.json',first['explicit_source'])
        before = files(temp); errors = []
        for spec in load(ROOT/'io-input-expected.json'):
            source = temp / ('missing-source.json' if spec['name']=='missing-source' else 'source.json')
            if spec['name']=='missing-source':
                # Same valid original Journal input via an explicit alternate fixture.
                save(store/'valid.json',dict(schema='rotation-record/0.1',id='valid',value=first['choice_value']))
                before = files(temp)
            key = 'valid' if spec['name']=='missing-source' else 'case'
            receipt = run_cli(['--store',str(store),'--id',key,'--source',str(source),'--format','json'])
            assert receipt['exit_code']==2 and not receipt['stdout'] and spec['reason'] in receipt['stderr'],receipt
            errors.append(dict(name=spec['name'],actual=receipt))
        after=files(temp);assert before==after
        save(ROOT/'io-actual.json',dict(results=errors,before=before,after=after))


if __name__ == '__main__':
    main()
