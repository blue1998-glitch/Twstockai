"""Save only the newly frozen v0.2 context cases; no market or old producer."""
import sys
import traceback
from graph_core.core import fingerprint
from rotation_research.market_case_v2 import prepare_context,CaseError
from rotation_research.market_case_io import load_saved
from rotation_research.market_case_v2_io import prepare_and_save_context
from .freeze import ROOT,REPO,PROJECT,load,save,info


def check_frozen():
    for meta in load(ROOT/'frozen.json')['files']+load(ROOT/'intake.json')['original_files']:
        assert info(REPO/meta['path'])==meta,'ORIGINAL_OR_FROZEN_BYTES_CHANGED:'+meta['path']


def probe(request,saved,summary):
    before=fingerprint(request);source_before=fingerprint(saved);summary_before=fingerprint(summary)
    calls=dict(context=0,source_validate=0,qualify=0,ledger_replay=0,capital_simulate=0,quantity_replay=0,legacy_prepare=0)
    pairs=[('context','/market_case_v2.py','prepare_context'),('source_validate','/subsidiary_proposal.py','validate'),
        ('qualify','/action_ledger.py','qualify'),('ledger_replay','/action_ledger.py','replay'),
        ('capital_simulate','/capital_research/execution.py','simulate'),('quantity_replay','/quantity_replay.py','replay_sequence'),
        ('legacy_prepare','/market_case.py','prepare_case')]
    def profile(frame,event,arg):
        if event=='call':
            for k,suffix,name in pairs:
                if frame.f_code.co_filename.endswith(suffix) and frame.f_code.co_name==name:calls[k]+=1
    sys.setprofile(profile)
    try:actual=prepare_context(request,saved,summary);error=None;trace=None
    except CaseError as exc:actual=None;error=str(exc);trace=traceback.format_exc()
    finally:sys.setprofile(None)
    return dict(actual=actual,error=error,traceback=trace,calls=calls,input_unchanged=fingerprint(request)==before,
        sources_unchanged=fingerprint(saved)==source_before,summary_unchanged=fingerprint(summary)==summary_before)


def main():
    check_frozen();spec=load(ROOT/'source-spec.json');saved=load_saved(REPO,spec);summary=load(ROOT/'work-summary.json')
    save(ROOT/'source-versions-before-run.json',dict(files=[info(PROJECT/'rotation_research'/n) for n in ['market_case_v2.py','market_case_v2_io.py']],
        frozen=info(ROOT/'frozen.json')))
    rows=[];cases=[dict(name='draft-II',input=load(ROOT/'input.json'),expected=load(ROOT/'expected.json'))]+load(ROOT/'cases.json')
    for case in cases:
        r=probe(case['input'],saved,summary);save(ROOT/'actual'/str(case['name']+'.json'),r)
        want=case['expected'];matched=r['error']==want['error'] if 'error' in want else r['error'] is None and r['actual']['status']==want['status']
        rows.append(dict(name=case['name'],status=r['actual']['status'] if r['actual'] else None,error=r['error'],matched=matched,calls=r['calls']))
    save(ROOT/'summary.json',rows)
    receipt=prepare_and_save_context(REPO,load(ROOT/'input.json'),spec,summary,ROOT/'saved','II-context-draft')
    save(ROOT/'save-readback.json',dict(id=receipt['id'],equal_readback=True,result_id=fingerprint(receipt['value']['result']),
        request_id=fingerprint(receipt['value']['request']),status=receipt['value']['result']['status'],numeric_replay='NOT_PERFORMED'))
    print(rows,flush=True)


if __name__=='__main__':main()
