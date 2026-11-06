"""Bounded before/after API and embedded CLI RUN; never a real producer."""
import argparse
from contextlib import redirect_stdout,redirect_stderr
from copy import deepcopy
from decimal import localcontext,DefaultContext
import io
from pathlib import Path
import sys
import traceback
from unittest.mock import patch
from rotation_research.action_ledger import replay
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from capital_research.lifecycle import _fp
from .prepare import ROOT,PROJECT,load,save,info


def check_frozen():
    for item in load(ROOT/'frozen.json')['files']+load(ROOT/'intake.json')['unchanged_originals']:
        assert info(PROJECT/item['path'])==item,'FROZEN_ORIGINAL_CHANGED:'+item['path']


def cases():return load(ROOT/'input.json')['cases']


def equal_expected(value,item):
    if value is None:return False
    expected=item['expected']
    if item['kind']=='EXACT_SAVED_SYNTHETIC':return value==expected
    return all(k in value and value[k]==v for k,v in expected.items()) and value['input_id']==item['input_id']


def calls_counter():
    counts=dict(replay=0,qualify=0,ledger_kernel=0,save=0,simulate=0,generate=0,replay_sequence=0)
    mapping=[('replay','/rotation_research/action_ledger.py','replay'),
        ('qualify','/rotation_research/action_ledger.py','qualify'),
        ('ledger_kernel','/rotation_research/action_ledger.py','_replay'),
        ('save','/rotation_research/store.py','save'),('simulate','/capital_research/execution.py','simulate'),
        ('generate','/quantity_candidates.py','generate'),('replay_sequence','/quantity_replay.py','replay_sequence')]
    def profile(frame,event,arg):
        if event=='call':
            for k,suffix,name in mapping:
                if frame.f_code.co_filename.endswith(suffix) and frame.f_code.co_name==name:counts[k]+=1
    return counts,profile


def probe(data,setting,fn=replay):
    original=_fp(data);default_before=snapshot(DefaultContext);counts,profile=calls_counter()
    with localcontext(context(setting)) as ctx:
        before=snapshot(ctx);sys.setprofile(profile)
        try:value=fn(data);error=None;trace=None
        except Exception as exc:value=None;error=dict(type=type(exc).__name__,detail=str(exc));trace=traceback.format_exc()
        finally:sys.setprofile(None)
        after=snapshot(ctx)
    return value,dict(error=error,traceback=trace,calls=counts,caller_before=before,caller_after=after,
        caller_context_unchanged=before==after,default_context_unchanged=default_before==snapshot(DefaultContext),
        input_id=original,input_unchanged=_fp(data)==original,source_version=info(ROOT.parent/'action_ledger.py'))


def cli_probe(stage,item):
    from rotation_research.action_cli import main
    store=ROOT/stage/'cli'/item['name']/'records';out=io.StringIO();err=io.StringIO()
    source=PROJECT/load(ROOT/'input.json')['primary_input']['path'];original=info(source)
    argv=['action_cli','RUN','--store',str(store),'--id','cash-probe','--input',str(source)]
    def run(_):
        with patch.object(sys,'argv',argv),redirect_stdout(out),redirect_stderr(err):main()
        return load(store/'cash-probe.json')
    value,record=probe(load(source),item['context'],run)
    record.update(actual=value,stdout=out.getvalue(),stderr=err.getvalue(),saved=(store/'cash-probe.json').exists(),
        input_file_unchanged=info(source)==original,equal_original=value is not None and value['value']==cases()[0]['expected'])
    if value is not None:assert out.getvalue().strip()==__import__('json').dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False)
    save(ROOT/stage/'cli'/item['name']/'actual.json',record)
    return dict(path=str((ROOT/stage/'cli'/item['name']/'actual.json').relative_to(ROOT)),
        equal_original=record['equal_original'],error=record['error'],saved=record['saved'])


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['before','after']);a=p.parse_args();check_frozen()
    controls=load(ROOT/'controls.json');rows=[]
    for item in cases():
        settings=controls['contexts'] if item['name']=='cash-net-withholding' else [controls['contexts'][0],dict(name='preset',context=controls['preset'])]
        for ctl in settings:
            value,record=probe(deepcopy(item['input']),ctl['context'])
            record.update(actual=value,equal_expected=equal_expected(value,item))
            path=ROOT/a.stage/item['name']/ctl['name']/'actual.json';save(path,record)
            rows.append(dict(case=item['name'],context=ctl['name'],path=str(path.relative_to(ROOT)),
                equal_expected=record['equal_expected'],error=record['error'],calls=record['calls'],
                input_unchanged=record['input_unchanged'],caller_context_unchanged=record['caller_context_unchanged']))
            print(item['name'],ctl['name'],record['equal_expected'],record['error'],flush=True)
    cli=[cli_probe(a.stage,x) for x in [controls['contexts'][0],dict(name='preset',context=controls['preset'])]]
    save(ROOT/a.stage/'summary.json',dict(api=rows,cli=cli))
    save(ROOT/a.stage/'source-versions.json',dict(ledger=info(ROOT.parent/'action_ledger.py'),
        runner=info(Path(__file__)),frozen=info(ROOT/'frozen.json')))
    print('cli',cli,flush=True)


if __name__=='__main__':main()
