"""Owner-authenticated exact action allowlist and bounded RAM-only LRU.
No route accepts a ticker, arbitrary path, schema/config override or source URL.
"""
from collections import OrderedDict,deque
from graph_core.core import fingerprint
from pathlib import Path
import json,hashlib,threading,subprocess,sys,time,os
MAX_ENTRIES=8
MAX_BYTES=2*1024**2
MAX_RESULT=262144
TTL=600
MAX_NEW_PER_MINUTE=12
class Refused(ValueError):pass
class Busy(RuntimeError):pass
sha=lambda b:hashlib.sha256(b).hexdigest()
class Provider:
    def __init__(self,path,digest,*,runner=None,clock=time.monotonic):
        self.path=Path(path);self.digest=digest;self.clock=clock;self.runner=runner or self._worker
        if self.path.is_symlink():raise Refused('CATALOGUE_SYMLINK')
        raw=self.path.read_bytes()
        if len(raw)>2*1024**2 or sha(raw)!=digest:raise Refused('CATALOGUE_BINDING')
        self.spec=json.loads(raw)
        if self.spec['schema']!='private-lazy-graph-actions/0.1':raise Refused('CATALOGUE_SCHEMA')
        self.actions={r['route']:r for r in self.spec['actions']}
        if len(self.actions)!=len(self.spec['actions']):raise Refused('DUPLICATE_ACTION')
        self.cache=OrderedDict();self.used=0;self.lock=threading.Lock();self.calls=deque();self.metrics=dict(core_calls=0,cache_hits=0,refusals=0,evictions=0,peak_cache_bytes=0,last_wall_seconds=0,last_worker_peak_RSS_KiB=0)
        for name,row in self.spec['original_daily_sources'].items():
            p=Path(row['path'])
            if p.is_symlink():raise Refused('SOURCE_SYMLINK')
            h=hashlib.sha256()
            with p.open('rb') as f:
                while b:=f.read(1024**2):h.update(b)
            if h.hexdigest()!=row['sha256']:raise Refused('ORIGINAL_SOURCE_SHA_CHANGED')
            s=p.stat()
            if [s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev]!=row['metadata']:raise Refused('SOURCE_METADATA_CHANGED')
    def routes(self):return [*self.actions,*([self.spec['metrics_route']] if self.spec.get('metrics_route') else [])]
    def _worker(self,fact):
        project=Path(__file__).resolve().parents[2];env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(project)+os.pathsep+str(project/'src'))
        r=subprocess.run([sys.executable,'-m','graph_core.graph_lazy1_20261104.worker'],input=json.dumps(fact,ensure_ascii=False).encode(),capture_output=True,timeout=8,env=env,cwd=project.parent)
        if r.returncode or len(r.stdout)>MAX_RESULT:raise Refused('RESOURCE_OR_CORE_REFUSAL')
        return json.loads(r.stdout)
    def get(self,route,allowed):
        if route==self.spec.get('metrics_route'):
            return json.dumps(dict(schema='lazy-resource-status/0.1',**self.metrics,cache_entries=len(self.cache),cache_bytes=self.used,max_entries=MAX_ENTRIES,max_bytes=MAX_BYTES,TTL_seconds=TTL,worker_AS_bytes=256*1024**2,worker_CPU_seconds=3,worker_wall_seconds=8),sort_keys=True).encode(),'STATUS'
        if route not in self.actions:raise KeyError('UNKNOWN_ACTION')
        if not self.lock.acquire(blocking=False):raise Busy('ONE_LAZY_WORKER_ALREADY_RUNNING')
        t=self.clock()
        try:
            if self.path.is_symlink() or sha(self.path.read_bytes())!=self.digest:raise Refused('CATALOGUE_CHANGED')
            for row in self.spec['original_daily_sources'].values():
                p=Path(row['path']);s=p.stat()
                if p.is_symlink() or [s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev]!=row['metadata']:raise Refused('ORIGINAL_SOURCE_CHANGED')
            for file,digest in self.spec['protected_code'].items():
                if sha(Path(file).read_bytes())!=digest:raise Refused('CODE_CHANGED_INVALIDATE_CACHE')
            a=self.actions[route];item=allowed.get(a['fact_route'])
            if not item or str(item.get('path'))!=a['fact_path'] or (item['bytes'],item['sha256'])!=(a['fact']['bytes'],a['fact']['sha256']):raise Refused('FACT_NOT_STATIC_ALLOWLISTED')
            p=Path(item['path'])
            if any(x.is_symlink() for x in (p,*p.parents)) or p.stat().st_size>65536:raise Refused('FACT_BOUND')
            b=p.read_bytes()
            if len(b)!=a['fact']['bytes'] or sha(b)!=a['fact']['sha256']:raise Refused('FACT_CHANGED_INVALIDATE_CACHE')
            f=json.loads(b)
            for key in ('identity','code','market','isin','cfi','as_of'):
                if f[key]!=a[key]:raise Refused('IDENTITY_ROLE_OR_DATE_MISMATCH')
            if f['source']['capture_id']!=self.spec['capture_id'] or f['source']['daily_sha256']!=self.spec['original_daily_sources'][f['market']]['sha256'] or f['source']['volume_unit']!='SHARES_REPORTED':raise Refused('SOURCE_BASIS_BINDING')
            if not f['cfi'].startswith('ES') or f['source']['price_mode']!='RAW_CANDIDATE' or f['source']['price_basis_id']!=f["market"]+':'+f["code"]+'-OFFICIAL-RAW-UNBRIDGED-'+f['as_of'] or f['continuity']!='NOT_CERTIFIED_NO_HISTORY_APPENDED':raise Refused('ROLE_BASIS_OR_CONTINUITY')
            if f['source_status']!='SOURCE_BAR_AVAILABLE' or f['bar'] is None:
                self.metrics['refusals']+=1
                return json.dumps(dict(schema='lazy-segment-analysis/0.1',identity=f['identity'],as_of=f['as_of'],status='SOURCE_REFUSED',reason=f['source_label'],fact_sha256=a['fact']['sha256'],request_id=a['request_id'],core_calls=0,series=None,meaningful_structure=False,history_joined=False,policy_authorized=False,execution_qualified=False,historical_signal_eligible=False,primary_pressure_id=None),ensure_ascii=False).encode(),'REFUSED'
            key=sha(json.dumps(dict(fact=a['fact'],code=self.spec['protected_code'],as_of=f['as_of']),sort_keys=True).encode())
            for k,(stamp,raw) in list(self.cache.items()):
                if t-stamp>TTL:self.used-=len(raw);del self.cache[k];self.metrics['evictions']+=1
            if key in self.cache:
                stamp,raw=self.cache.pop(key);self.cache[key]=(stamp,raw);self.metrics['cache_hits']+=1;return raw,'HIT'
            while self.calls and t-self.calls[0]>60:self.calls.popleft()
            if len(self.calls)>=MAX_NEW_PER_MINUTE:raise Busy('LAZY_RESOURCE_RATE_BOUND')
            self.calls.append(t);start=time.monotonic();value=self.runner(f);self.metrics['core_calls']+=value['core_calls']
            rr=value['series']['results'][0];check=dict(rr);rid=check.pop('result_id')
            if value['identity']!=f['identity'] or value['as_of']!=f['as_of'] or value['series']['bars']!=[f['bar']] or rr['source_records']!=1 or fingerprint(check)!=rid or value['history_joined'] is not False or value['meaningful_structure'] is not False:raise Refused('CORE_OUTPUT_BINDING')
            for file,digest in self.spec['protected_code'].items():
                if sha(Path(file).read_bytes())!=digest:raise Refused('CODE_CHANGED_DURING_JOB')
            if p.read_bytes()!=b:raise Refused('FACT_CHANGED_DURING_JOB')
            value.update(fact_sha256=a['fact']['sha256'],request_id=a['request_id']);raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
            if len(raw)>MAX_RESULT:raise Refused('RESULT_TOO_LARGE')
            while self.cache and (len(self.cache)>=MAX_ENTRIES or self.used+len(raw)>MAX_BYTES):
                _,(_,old)=self.cache.popitem(last=False);self.used-=len(old);self.metrics['evictions']+=1
            self.cache[key]=(t,raw);self.used+=len(raw);self.metrics['peak_cache_bytes']=max(self.metrics['peak_cache_bytes'],self.used);self.metrics['last_wall_seconds']=time.monotonic()-start;self.metrics['last_worker_peak_RSS_KiB']=value['metrics']['peak_RSS_KiB']
            return raw,'MISS'
        except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired) as exc:
            self.cache.clear();self.used=0;self.metrics['refusals']+=1;raise Refused('VALIDATION_OR_RESOURCE_REFUSED') from exc
        finally:self.lock.release()
