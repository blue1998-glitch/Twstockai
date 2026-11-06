"""Fresh pure-context audit, with a hostile caller and DefaultContext."""
import decimal
import json
import os
import sys
from rotation_research.market_case_v2 import prepare_context
from rotation_research.market_case_io import load_saved
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .freeze import ROOT,PROJECT,REPO,load


def main():
    request=load(ROOT/'input.json');saved=load_saved(REPO,load(ROOT/'source-spec.json'));summary=load(ROOT/'work-summary.json')
    seed=context(load(PROJECT/'capital_research/quantity_context_20261027/test-controls.json')['preset'])
    for k in ('prec','rounding','Emin','Emax','capitals','clamp'):setattr(decimal.DefaultContext,k,getattr(seed,k))
    decimal.DefaultContext.traps.update(seed.traps);decimal.DefaultContext.flags.update(seed.flags);decimal.setcontext(seed.copy())
    caller=snapshot(decimal.getcontext());default=snapshot(decimal.DefaultContext);effects=[];calls=dict(context=0,qualify=0,replay=0)
    def audit(event,args):
        write=event=='open' and ((isinstance(args[1],str) and any(k in args[1] for k in 'wax+')) or
            (isinstance(args[2],int) and args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)))
        if write or event.startswith(('socket.','subprocess.')) or event in ('os.mkdir','os.remove','os.rename','os.system'):
            effects.append(event);raise AssertionError('FORBIDDEN_IO:'+event)
    def profile(frame,event,arg):
        if event!='call':return
        path=frame.f_code.co_filename;name=frame.f_code.co_name
        if path.endswith('/market_case_v2.py') and name=='prepare_context':calls['context']+=1
        if path.endswith('/action_ledger.py') and name in ('qualify','replay','_replay'):
            calls['qualify' if name=='qualify' else 'replay']+=1;raise AssertionError('FORBIDDEN_ENGINE:'+name)
        if path.endswith(('/capital_research/execution.py','/quantity_replay.py')) and name in ('simulate','replay_sequence'):raise AssertionError('FORBIDDEN_ENGINE:'+name)
    sys.addaudithook(audit);sys.setprofile(profile);result=prepare_context(request,saved,summary);sys.setprofile(None)
    print(json.dumps(dict(status=result['status'],calls=calls,forbidden_effects=effects,
        caller_unchanged=caller==snapshot(decimal.getcontext()),default_unchanged=default==snapshot(decimal.DefaultContext),
        caller_before=caller,caller_after=snapshot(decimal.getcontext()),numeric_replay=result['numeric_replay']),sort_keys=True))


if __name__=='__main__':main()
