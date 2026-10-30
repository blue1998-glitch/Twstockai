"""Prepare only this frozen case; no old window producer or ledger replay."""
from copy import deepcopy
import argparse
import sys
import traceback
from graph_core.core import fingerprint
from rotation_research.market_case import prepare_case,CaseError
from rotation_research.market_case_io import load_saved,prepare_and_save
from .freeze import ROOT,REPO,PROJECT,load,save,info


def check_frozen():
    for file in ['frozen.json','frozen-cases.json']:
        for item in load(ROOT/file)['files']:
            assert info(REPO/item['path'])==item,'FROZEN_BYTES_CHANGED:'+item['path']
    for item in load(ROOT/'intake.json')['unchanged_originals']:
        assert info(REPO/item['path'])==item,'OLD_SOURCE_CHANGED:'+item['path']


def inspect(request,saved):
    before=fingerprint(request);source_before=fingerprint(saved);calls=dict(prepare=0,source_qualify=0,ledger_replay=0,capital_simulate=0,
        quantity_replay=0,legacy_compare=0,old_source_producer=0)
    def profile(frame,event,arg):
        if event!='call':return
        path=frame.f_code.co_filename;name=frame.f_code.co_name
        pairs=[('prepare','/market_case.py','prepare_case'),('source_qualify','/subsidiary_proposal.py','qualify'),
            ('ledger_replay','/action_ledger.py','replay'),('capital_simulate','/capital_research/execution.py','simulate'),
            ('quantity_replay','/quantity_replay.py','replay_sequence'),('legacy_compare','/rotation_research/core.py','compare')]
        for k,suffix,n in pairs:
            if path.endswith(suffix) and name==n:calls[k]+=1
        if path.endswith('_sources.py') and name in ('run','main','build_catalog'):calls['old_source_producer']+=1
    sys.setprofile(profile)
    try:actual=prepare_case(request,saved);error=None;trace=None
    except CaseError as exc:actual=None;error=str(exc);trace=traceback.format_exc()
    finally:sys.setprofile(None)
    return dict(actual=actual,error=error,traceback=trace,calls=calls,input_unchanged=fingerprint(request)==before,
        sources_unchanged=fingerprint(saved)==source_before)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',default='');args=parser.parse_args()
    out=ROOT/args.stage
    check_frozen();saved=load_saved(REPO,load(ROOT/'source-spec.json'))
    versions=[info(PROJECT/'rotation_research'/n) for n in ['market_case.py','market_case_io.py']]
    save(out/'source-versions-before-run.json',dict(files=versions,source_spec=info(ROOT/'source-spec.json')))
    rows=[]
    for name,file in [('draft','input.json'),('explicit-control','controls/source-bound-input.json')]:
        request=load(ROOT/file);r=inspect(request,saved);save(out/'actual'/name/'actual.json',r)
        rows.append(dict(case=name,status=r['actual']['status'] if r['actual'] else None,error=r['error'],calls=r['calls']))
    for name in load(ROOT/'cases/index.json')['rejected_cases']:
        r=inspect(load(ROOT/'cases'/name/'input.json'),saved);expected=load(ROOT/'cases'/name/'expected.json')
        save(out/'actual'/name/'actual.json',r);rows.append(dict(case=name,error=r['error'],expected=expected['error'],matched=r['error']==expected['error'],calls=r['calls']))
    save(out/'summary.json',rows)
    # Real case draft remains missing external parameters. Journal stores it as-is.
    receipt=prepare_and_save(REPO,load(ROOT/'input.json'),load(ROOT/'source-spec.json'),out/'saved','market-case-draft')
    save(out/'saved-receipt.json',dict(id=receipt['id'],status=receipt['value']['result']['status'],
        request_id=fingerprint(receipt['value']['request']),numeric_replay='NOT_PERFORMED'))
    print({x['case']:x.get('status') or x.get('error') for x in rows},flush=True)


if __name__=='__main__':main()
