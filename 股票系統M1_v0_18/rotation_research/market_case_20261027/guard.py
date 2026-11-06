"""Fresh child proves pure preparation, no numeric/producer dispatch or IO."""
import decimal
import json
import os
import sys
from rotation_research.market_case import prepare_case
from rotation_research.market_case_io import load_saved
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .freeze import ROOT,REPO,PROJECT,load


def main():
    saved=load_saved(REPO,load(ROOT/'source-spec.json'));request=load(ROOT/'controls/source-bound-input.json')
    seed=context(load(PROJECT/'capital_research/quantity_context_20261027/test-controls.json')['preset'])
    for k in ('prec','rounding','Emin','Emax','capitals','clamp'):setattr(decimal.DefaultContext,k,getattr(seed,k))
    decimal.DefaultContext.traps.update(seed.traps);decimal.DefaultContext.flags.update(seed.flags);decimal.setcontext(seed.copy())
    caller=snapshot(decimal.getcontext());default=snapshot(decimal.DefaultContext);effects=[];calls=[]
    def audit(event,args):
        write=event=='open' and ((isinstance(args[1],str) and any(k in args[1] for k in 'wax+')) or
            (isinstance(args[2],int) and args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)))
        if write or event.startswith(('socket.','subprocess.')) or event in ('os.mkdir','os.remove','os.rename','os.system'):
            effects.append(event);raise AssertionError('FORBIDDEN_IO:'+event)
    def profile(frame,event,arg):
        if event!='call':return
        p=frame.f_code.co_filename;n=frame.f_code.co_name
        if p.endswith('/subsidiary_proposal.py') and n=='qualify':calls.append('source_qualify')
        if (p.endswith('/action_ledger.py') and n in ('replay','_replay')) or (p.endswith('_sources.py') and n in ('run','main','build_catalog')):
            raise AssertionError('FORBIDDEN_NUMERIC_OR_PRODUCER:'+n)
    sys.addaudithook(audit);sys.setprofile(profile);result=prepare_case(request,saved);sys.setprofile(None)
    print(json.dumps(dict(status=result['status'],source_qualification_calls=len(calls),forbidden_effects=effects,
        caller_unchanged=caller==snapshot(decimal.getcontext()),default_unchanged=default==snapshot(decimal.DefaultContext),
        numeric_replay=result['numeric_replay'],caller_before=caller,caller_after=snapshot(decimal.getcontext())),sort_keys=True))


if __name__=='__main__':main()
