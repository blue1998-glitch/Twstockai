"""Execution-scoped storage guard; original Journal/codec/core bytes unchanged.
512 MiB policy applies to new codec pieces, plain metadata and head staging.
Not a numeric engine, source qualification or filesystem migration.
"""
import contextlib,math,shutil
from pathlib import Path
from unittest.mock import patch
from rotation_research import artifact_codec as codec
from rotation_research.store import Journal
from graph_core import market_increment

MINIMUM=512*1024*1024
@contextlib.contextmanager
def guarded_writes(root,*,minimum_free=MINIMUM,space=None):
    if minimum_free<MINIMUM:raise ValueError('CANNOT_LOWER_DAY1_512MIB_RESERVE')
    root=Path(root).resolve();space=space or (lambda:shutil.disk_usage(root).free)
    original_immutable=codec.immutable;original_save=Journal.save;original_open=Path.open
    def check(path,n):
        p=Path(path).absolute()
        if not p.resolve().is_relative_to(root) or any(x.is_symlink() for x in (p,*p.parents)):raise ValueError('WRITE_OUTSIDE_AUTHORIZED_ROOT_OR_SYMLINK')
        required=minimum_free+math.ceil(n/4096)*4096+64*1024
        if space()<required:raise OSError('DAY1_512MIB_RESERVE_NO_NEW_WRITE_OLD_HEAD_PRESERVED')
    def immutable(path,raw):
        if not Path(path).exists():check(path,len(raw))
        return original_immutable(path,raw)
    def save(self,key,value,**kwargs):
        path=self.path(key)
        if not codec.exists(path):
            if kwargs.get('compact'):check(path,0)  # each actual compressed piece checked by immutable
            else:check(path,len(codec.journal_bytes(dict(schema='rotation-record/0.1',id=key,value=value))))
        return original_save(self,key,value,**kwargs)
    def path_open(path,mode='r',*args,**kwargs):
        if any(c in mode for c in ('w','a','x','+')):
            if Path(path).name not in ('daily.lock','current-increment.pending'):raise ValueError('UNEXPECTED_DIRECT_FILE_WRITE')
            check(path,64*1024)
        return original_open(path,mode,*args,**kwargs)
    with patch.object(codec,'immutable',immutable),patch.object(Journal,'save',save),patch.object(market_increment,'publish_immutable',immutable),patch.object(Path,'open',path_open):
        yield
