"""Exact-codec source IO for NEW saved scan; original cache/get/record logic."""
from pathlib import Path
import json,time,threading
from collections import OrderedDict,deque
from rotation_research import artifact_codec as c
from rotation_research.store import Journal
from graph_core.scan1_20261104.provider import Provider as OriginalSaved
from graph_core.graph_lazy1_20261104.provider import Refused
from graph_core.prod_core1_20261105.flow import bound
class LogicalArtifact:
    def __init__(self,path):self.path=Path(path)
    def is_symlink(self):return self.path.is_symlink()
    def read_bytes(self):return c.read_bytes(self.path)
class Provider(OriginalSaved):
    def __init__(self,path,digest):
        self.path=LogicalArtifact(path);self.digest=digest;self.clock=time.monotonic;self.runner=self.hydrate
        raw=c.read_bytes(c.regular(path))
        if len(raw)>2*1024**2 or c.sha(raw)!=digest:raise Refused('CATALOGUE_BINDING')
        self.spec=json.loads(raw)
        if self.spec['schema']!='private-lazy-graph-actions/0.1':raise Refused('CATALOGUE_SCHEMA')
        self.actions={r['route']:r for r in self.spec['actions']}
        if len(self.actions)!=len(self.spec['actions']):raise Refused('DUPLICATE_ACTION')
        self.cache=OrderedDict();self.used=0;self.lock=threading.Lock();self.calls=deque();self.metrics=dict(core_calls=0,cache_hits=0,refusals=0,evictions=0,peak_cache_bytes=0,last_wall_seconds=0,last_worker_peak_RSS_KiB=0)
        self.check_sources()
        self.index=bound(self.spec['scan_index']);self.numeric=bound(self.spec['scan_manifest'])
        if self.numeric.get('journal_encoding')!='MINIFIED_UTF8_V1' or self.numeric['id']!=self.index['scan_id']:raise Refused('SCAN_VERSION_MISMATCH')
        self.rows={r['identity']:r for r in self.index['records']};self.stocks={s['identity']:s for s in self.numeric['stocks']};self.journal=Journal(Path(self.spec['scan_index']['path']).parent/'results')
        if set(self.rows)!=set(self.stocks):raise Refused('INCOMPLETE_SCAN_INDEX')
    def check_sources(self):
        for d in self.spec['original_daily_sources'].values():
            c.read_bytes(d.get('logical_path',d['path']),expected_bytes=d['logical_bytes'],expected_sha=d['sha256'])
            p=c.regular(d['path']);s=p.stat()
            if [s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev]!=d['metadata']:raise Refused('ORIGINAL_SOURCE_METADATA_CHANGED')
    def get(self,route,allowed):
        self.check_sources() # include DU2 dependencies before a RAM HIT
        return super().get(route,allowed)
