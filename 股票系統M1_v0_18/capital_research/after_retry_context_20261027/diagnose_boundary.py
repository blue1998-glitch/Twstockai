"""Locate the already-reproduced failure before the protected inner generator."""
from decimal import localcontext
import sys
import traceback
from capital_research.quantity_after_retry import generate_after_retry
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .reproduce import case,controls
from .prepare import ROOT,save,info


def main():
    data,_,spec=case('new-independent-trigger')
    for c in controls():
        if c['name'] not in ('inexact-trap','narrow-exponents'):continue
        counts=dict(bridge=0,generate=0,ledger_replay=0,simulate=0,retry=0)
        def profile(frame,event,arg):
            if event!='call':return
            p=frame.f_code.co_filename;n=frame.f_code.co_name
            for key,path,name in [('bridge','/quantity_after_retry.py','generate_after_retry'),
                    ('generate','/quantity_candidates.py','generate'),('ledger_replay','/action_ledger.py','replay'),
                    ('simulate','/execution.py','simulate'),('retry','/conditional_retry.py','retry_rejected')]:
                if p.endswith(path) and n==name:counts[key]+=1
        with localcontext(context(c['context'])) as ctx:
            before=snapshot(ctx);sys.setprofile(profile)
            try:
                generate_after_retry(data);error=None;trace=None
            except Exception as exc:
                error=dict(type=type(exc).__name__,detail=str(exc));trace=traceback.format_exc()
            finally:sys.setprofile(None)
            after=snapshot(ctx)
        save(ROOT/'before/boundary'/c['name']/'actual.json',dict(input_id=spec['materialized_input_id'],
            context=c['context'],error=error,traceback=trace,calls=counts,caller_before=before,caller_after=after,
            source_version=info(ROOT.parent/'quantity_after_retry.py')))
        print(c['name'],error,counts,flush=True)


if __name__=='__main__':main()
