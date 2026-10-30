"""Evaluate only new frozen inputs; no market, replay, ledger or source producer."""
from decimal import localcontext
import json
from capital_research.account_metrics import evaluate_saved,_curve_statistics,render_text
from capital_research.lifecycle import _fp
from .prepare import ROOT,PROJECT,load,save,file_info
from .fixtures import resolve


def main():
    dest=ROOT/'final'
    before={x['path']:file_info(PROJECT/x['path']) for x in load(ROOT/'intake.json')['originals']}
    index=[]
    for folder in sorted((ROOT/'arithmetic').iterdir()):
        rows=load(folder/'input.json')
        with localcontext() as ctx:
            ctx.prec=50;actual=_curve_statistics(rows)
        save(dest/'arithmetic'/folder.name/'result.json',actual)
        index.append(dict(kind='ARITHMETIC_ONLY',name=folder.name))
    for folder in sorted((ROOT/'cases').iterdir()):
        request=resolve(load(folder/'input.json'));identity=_fp(request)
        actual=evaluate_saved(request)
        assert identity==_fp(request),'INPUT_CHANGED'
        save(dest/'saved'/folder.name/'result.json',actual)
        save(dest/'saved'/folder.name/'input-integrity.json',dict(resolved_request_id=identity,
            source_recipe_id=_fp(load(folder/'input.json')),unchanged_after_evaluation=True,
            role='ORIGINAL_SAVED_JSON' if load(folder/'input.json')['recipe']=='NONE' else 'EXPLICIT_STRUCTURAL_FIXTURE_NOT_ENGINE_OUTPUT'))
        p=dest/'saved'/folder.name/'readable.txt'
        p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('x') as f:f.write(render_text(actual))
        index.append(dict(kind='SAVED_STRUCTURAL_EVALUATION',name=folder.name,status=actual['status'],reasons=actual['reasons']))
        print(folder.name,actual['status'],[r['reason'] for r in actual['reasons']],flush=True)
    after={path:file_info(PROJECT/path) for path in before}
    assert before==after,'ORIGINAL_CHANGED'
    save(dest/'preservation.json',dict(before=before,after=after))
    save(dest/'summary.json',index)
    save(dest/'source-versions.json',[file_info(ROOT.parent/name) for name in ('account_metrics.py','account_metrics_read.py','lifecycle.py')])


if __name__=='__main__':main()
