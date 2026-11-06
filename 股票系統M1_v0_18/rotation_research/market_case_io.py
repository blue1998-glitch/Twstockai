"""Explicit saved-source IO and one preparation/save operation; no READ tool."""
import argparse
import hashlib
import json
from pathlib import Path
from .market_case import prepare_case,CaseError
from .store import Journal


def load_saved(repo,spec):
    if spec.get('schema')!='rotation-market-source-spec/0.1' or set(spec['files'])!={'quotes','quote_manifest','catalog','calendar'}:
        raise CaseError('EXPLICIT_SOURCE_SPEC_REQUIRED')
    root=Path(repo).resolve();saved={}
    for key,meta in spec['files'].items():
        p=root/meta['path']
        if p.is_symlink() or not p.resolve().is_relative_to(root):raise CaseError('SOURCE_PATH_OUTSIDE_REPOSITORY')
        raw=p.read_bytes()
        if len(raw)!=meta['bytes'] or hashlib.sha256(raw).hexdigest()!=meta['sha256']:raise CaseError('SAVED_SOURCE_BYTES_MISMATCH')
        saved[key]=json.loads(raw)
    return saved


def prepare_and_save(repo,request,spec,store,identity):
    saved=load_saved(repo,spec);result=prepare_case(request,saved)
    record=dict(request=request,source_spec=spec,result=result)
    journal=Journal(store);journal.save(identity,record)
    receipt=journal.read(identity)
    if receipt['value']!=record:raise CaseError('SAVED_PREPARATION_READBACK_MISMATCH')
    return receipt


def main():
    p=argparse.ArgumentParser(description='Prepare the named market case; no numeric replay or trade')
    for name in ['repo','input','source-spec','store','id']:p.add_argument('--'+name,required=True)
    a=p.parse_args();request=json.loads(Path(a.input).read_text());spec=json.loads(Path(a.source_spec).read_text())
    receipt=prepare_and_save(a.repo,request,spec,a.store,a.id)
    print(json.dumps(dict(id=receipt['id'],status=receipt['value']['result']['status'],numeric_replay='NOT_PERFORMED'),ensure_ascii=False))


if __name__=='__main__':main()
