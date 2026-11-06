"""Only evaluate saved JSON under frozen ambient contexts, with no replay."""
import argparse
from copy import deepcopy
import decimal
from capital_research.account_metrics import evaluate_saved,INPUT
from capital_research.lifecycle import _fp
from .prepare import ROOT,PROJECT,load,save,info


def context(spec):
    return decimal.Context(**{k:v for k,v in spec.items() if k not in ('traps','flags')},
        traps=[getattr(decimal,k) for k in spec['traps']],flags=[getattr(decimal,k) for k in spec['flags']])


def snapshot(ctx):
    return {**{k:getattr(ctx,k) for k in ('prec','rounding','Emin','Emax','capitals','clamp')},
        'traps':{k.__name__:v for k,v in ctx.traps.items()},'flags':{k.__name__:v for k,v in ctx.flags.items()}}


def request():
    spec=load(ROOT/'input.json')
    for k in ('saved_source','baseline_expected'):
        meta=spec[k];assert info(PROJECT/meta['path'])==meta,'ORIGINAL_FINGERPRINT_CONFLICT'
    return dict(schema=INPUT,synthetic=True,evaluation_at=spec['evaluation_at'],saved_result=load(PROJECT/spec['saved_source']['path']))


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('before','after'));p.add_argument('--extra',action='store_true');a=p.parse_args()
    spec=load(ROOT/'input.json');expected=load(PROJECT/spec['baseline_expected']['path']);data=request();original=_fp(data);rows=[]
    controls=load(ROOT/'additional-controls.json')['contexts'] if a.extra else spec['contexts']
    for item in controls:
        with decimal.localcontext(context(item['context'])) as ctx:
            before=snapshot(ctx)
            try:actual=evaluate_saved(data);error=None
            except Exception as exc:actual=None;error=dict(type=type(exc).__name__,detail=str(exc))
            after=snapshot(ctx)
        row=dict(name=item['name'],actual=actual,error=error,equal_original_normal=actual==expected,
            caller_before=before,caller_after=after,caller_context_unchanged=before==after,input_unchanged=_fp(data)==original,
            source_version=info(ROOT.parent/'account_metrics.py'))
        save(ROOT/a.stage/item['name']/'actual.json',row)
        rows.append(dict(name=item['name'],equal_original_normal=row['equal_original_normal'],error=error,
            caller_context_unchanged=row['caller_context_unchanged'],input_unchanged=row['input_unchanged']))
        print(item['name'],row['equal_original_normal'],error,flush=True)
    save(ROOT/a.stage/('summary-extra.json' if a.extra else 'summary.json'),rows)


if __name__=='__main__':main()
