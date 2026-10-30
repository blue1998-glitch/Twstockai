"""Evidence IO and fresh-process READ guard, separate from the pure renderer."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
REPO = PROJECT.parent
OLD = ROOT.parent / 'research_choice_20261027'

GUARD = r'''
import sys, os, runpy, importlib.abc
allowed = {'capital_research.research_choice', 'capital_research.research_choice_workflow',
 'capital_research.research_choice_cli', 'capital_research.research_choice_view',
 'capital_research.quantity_choice_rules', 'capital_research.lifecycle', 'rotation_research.store'}
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self, fullname, path=None, target=None):
  if fullname.startswith('graph_core') or (fullname.startswith(('capital_research.', 'rotation_research.')) and fullname not in allowed):
   raise RuntimeError('ENGINE_IMPORT:' + fullname)
sys.meta_path.insert(0, Guard())
def audit(event, args):
 if event == 'open':
  mode, flags = args[1:3]
  if (mode and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
   raise RuntimeError('READ_WRITE_FORBIDDEN')
 if event in ('os.mkdir','os.remove','os.rename','subprocess.Popen','socket.connect'):
  raise RuntimeError('READ_SIDE_EFFECT:' + event)
def profile(frame, event, arg):
 if event == 'call':
  name = frame.f_code.co_name; path = frame.f_code.co_filename
  if (name == 'choose_saved' and path.endswith('/research_choice.py') or
      name == 'select_and_save' and path.endswith('/research_choice_workflow.py') or
      name == 'save' and path.endswith('/rotation_research/store.py')):
   raise RuntimeError('READ_RESELECTION_OR_SAVE_FORBIDDEN')
sys.addaudithook(audit)
sys.setprofile(profile)
sys.argv = ['capital_research.research_choice_cli'] + sys.argv[1:]
runpy.run_module('capital_research.research_choice_cli', run_name='__main__')
'''


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def run_cli(args):
    p = subprocess.run([sys.executable, '-B', '-c', GUARD] + args,
        cwd=PROJECT, text=True, capture_output=True)
    return dict(exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr,
        guard='FRESH_NO_ENGINE_NO_RESELECT_NO_SAVE_NO_WRITE_NO_NETWORK')
