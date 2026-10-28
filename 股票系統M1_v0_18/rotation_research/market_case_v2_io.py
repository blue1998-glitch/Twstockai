"""Explicit IO for v0.2; reuse the original source loader and Journal."""
from .market_case_io import load_saved
from .market_case_v2 import prepare_context
from .market_case import CaseError
from .store import Journal


def prepare_and_save_context(repo,request,source_spec,work_summary,store,identity):
    saved=load_saved(repo,source_spec)
    result=prepare_context(request,saved,work_summary)
    record=dict(request=request,source_spec=source_spec,work_summary=work_summary,result=result)
    journal=Journal(store);journal.save(identity,record);receipt=journal.read(identity)
    if receipt['value']!=record:raise CaseError('SAVED_CONTEXT_READBACK_MISMATCH')
    return receipt
