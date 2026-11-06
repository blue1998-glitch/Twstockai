"""Fresh-process API/READ audit; diagnostic writes belong to the parent."""
import argparse
from contextlib import redirect_stdout
import decimal
import io
import json
from pathlib import Path
import sys
from .prepare import ROOT,PROJECT,load,info
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from capital_research.lifecycle import _fp


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['pure','read']);p.add_argument('--record');a=p.parse_args()
    setting=load(ROOT/'controls.json')['preset'];seed=context(setting)
    for name in ('prec','rounding','Emin','Emax','capitals','clamp'):setattr(decimal.DefaultContext,name,getattr(seed,name))
    decimal.DefaultContext.traps.update(seed.traps);decimal.DefaultContext.flags.update(seed.flags)
    decimal.setcontext(seed.copy());before=snapshot(decimal.getcontext());default=snapshot(decimal.DefaultContext)
    if a.mode=='pure':
        from rotation_research.action_ledger import replay
        item=load(ROOT/'input.json')['cases'][0];data=item['input'];input_id=_fp(data)
    else:
        sys.modules['rotation_research.action_ledger']=None
        from rotation_research.action_cli import main as cli
        record=ROOT/a.record;original=info(record)
        argv=['action_cli','READ','--store',str(record.parent),'--id',record.stem]
    effects=[];qualifier_context=[];engine_calls=[]
    def audit(event,args):
        write=event=='open' and ((isinstance(args[1],str) and any(c in args[1] for c in 'wax+')) or
            (isinstance(args[2],int) and args[2]&(__import__('os').O_WRONLY|__import__('os').O_RDWR|__import__('os').O_CREAT|__import__('os').O_TRUNC)))
        forbidden=write or event.startswith(('socket.','subprocess.')) or event in ('os.system','os.rename','os.remove','os.mkdir')
        if forbidden:effects.append(event);raise AssertionError('FORBIDDEN_IO:'+event)
    def profile(frame,event,arg):
        if event=='call' and frame.f_code.co_filename.endswith('/rotation_research/action_ledger.py'):
            engine_calls.append(frame.f_code.co_name)
            if frame.f_code.co_name in ('qualify','_replay'):qualifier_context.append(dict(function=frame.f_code.co_name,context=snapshot(decimal.getcontext())))
    sys.addaudithook(audit);sys.setprofile(profile)
    if a.mode=='pure':
        result=replay(data);matched=result==item['expected'];unchanged=_fp(data)==input_id
        output=dict(actual_id=_fp(result),equal_original=matched,input_unchanged=unchanged,qualifier_context=qualifier_context)
    else:
        out=io.StringIO();sys.argv=argv
        with redirect_stdout(out):cli()
        output=dict(receipt=json.loads(out.getvalue()),stdout=out.getvalue(),record_unchanged=info(record)==original,
            ledger_import_blocked=sys.modules['rotation_research.action_ledger'] is None)
    sys.setprofile(None)
    output.update(mode=a.mode,forbidden_effects=effects,engine_calls=engine_calls,
        caller_before=before,caller_after=snapshot(decimal.getcontext()),caller_context_unchanged=before==snapshot(decimal.getcontext()),
        default_context_unchanged=default==snapshot(decimal.DefaultContext))
    print(json.dumps(output,ensure_ascii=False,sort_keys=True,allow_nan=False))


if __name__=='__main__':main()
