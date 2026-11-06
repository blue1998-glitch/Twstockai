"""Credential-free read protocol. No listener, workflow, auth bootstrap or CLI."""
import datetime,hashlib,hmac,json,re,os,fcntl
from dataclasses import dataclass
from pathlib import Path

VERSION="oci-read-bridge/0.1"
OPS={"get_account_plan_kind","list_pilot_compartment_resources"}
class Refused(Exception):pass

def encode(value):return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def strict(raw):
 def unique(pairs):
  d={}
  for k,v in pairs:
   if k in d:raise Refused("DUPLICATE_KEY")
   d[k]=v
  return d
 try:
  if not isinstance(raw,bytes) or len(raw)>4096:raise Refused("INPUT_BOUND")
  return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(Refused("NONFINITE")))
 except (ValueError,TypeError):raise Refused("INVALID_JSON")

@dataclass(frozen=True)
class Trust:
 repository_id:int
 installation_id:int
 actors:frozenset
 commit:str
 branch:str="dev/m1-v018-chart-annotations"

def authorize(raw,signature,key,trust,now):
 if not isinstance(raw,bytes) or len(raw)>4096:raise Refused("INPUT_BOUND")
 if not isinstance(key,bytes) or len(key)<32:raise Refused("NO_TRUSTED_CHANNEL")
 if not isinstance(signature,str) or not hmac.compare_digest(signature,hmac.new(key,raw,hashlib.sha256).hexdigest()):raise Refused("AUTHENTICATION_FAILED")
 e=strict(raw)
 fields={"version","operation","request_id","issued_at","expires_at","repository_id","installation_id","actor_id","private_repository","commit","branch","event"}
 if not isinstance(e,dict) or set(e)!=fields:raise Refused("REQUEST_FIELDS")
 if any(type(e[k]) is not str for k in ("version","operation","request_id","commit","branch","event")):raise Refused("REQUEST_TYPES")
 if e["version"]!=VERSION or e["operation"] not in OPS:raise Refused("OPERATION_OR_VERSION")
 if not re.fullmatch(r"[a-f0-9]{32}",e["request_id"]):raise Refused("REQUEST_ID")
 if e["private_repository"] is not True or e["repository_id"]!=trust.repository_id or e["installation_id"]!=trust.installation_id or e["actor_id"] not in trust.actors:raise Refused("PRINCIPAL_SCOPE")
 for k in ("repository_id","installation_id","actor_id"):
  if type(e[k]) is not int or e[k]<=0:raise Refused("PRINCIPAL_TYPE")
 if not re.fullmatch(r"[a-f0-9]{40}",trust.commit) or e["commit"]!=trust.commit or e["branch"]!=trust.branch or e["event"]!="verified_issue_command":raise Refused("CODE_OR_CHANNEL_DRIFT")
 if type(e["issued_at"]) is not int or type(e["expires_at"]) is not int or not e["issued_at"]<=now<e["expires_at"] or e["expires_at"]-e["issued_at"]>300:raise Refused("EXPIRED_OR_FUTURE")
 return e

class ReplayStore:
 """Single-host private append ledger; cross-runner deployments require one authority."""
 def __init__(self,path):
  self.path=Path(path)
  if any(p.is_symlink() for p in (self.path,*self.path.parents)):raise Refused("REPLAY_PATH")
  if any((p/".git").exists() for p in self.path.parents):raise Refused("REPLAY_IN_GIT")
  if not self.path.parent.is_dir() or self.path.parent.stat().st_mode&0o077:raise Refused("REPLAY_NOT_PRIVATE")
 def consume(self,request_id):
  fd=os.open(self.path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,"r+b") as f:
   fcntl.flock(f,fcntl.LOCK_EX)
   if os.fstat(f.fileno()).st_mode&0o077:raise Refused("REPLAY_NOT_PRIVATE")
   raw=f.read(131073)
   if len(raw)>131072 or (raw and not raw.endswith(b"\n")):raise Refused("REPLAY_LEDGER_INVALID")
   rows=raw.splitlines()
   if any(not re.fullmatch(b"[a-f0-9]{32}",x) for x in rows) or len(rows)!=len(set(rows)):raise Refused("REPLAY_LEDGER_INVALID")
   if request_id.encode() in rows:raise Refused("REPLAY")
   if len(rows)>=1024:raise Refused("REPLAY_CAPACITY")
   f.write(request_id.encode()+b"\n");f.flush();os.fsync(f.fileno())

class OCIReadAdapter:
 """Only injected official SDK clients, server-bound pilot compartment/ADs."""
 def __init__(self,compute,block,compartment,ads):
  if not re.fullmatch(r"ocid1\.compartment\.[a-zA-Z0-9._-]+",compartment) or not 1<=len(ads)<=8:raise Refused("SERVER_SCOPE")
  self.compute,self.block,self.compartment,self.ads=compute,block,compartment,tuple(ads)
 @classmethod
 def from_oci_sdk(cls,config,signer,compartment,ads):
  # Called ONLY in a future authorized isolated executor, never in public CI.
  import oci
  kwargs=dict(signer=signer,retry_strategy=oci.retry.NoneRetryStrategy(),timeout=(5,15))
  return cls(oci.core.ComputeClient(config,**kwargs),oci.core.BlockstorageClient(config,**kwargs),compartment,ads)
 def _list(self,method,extra):
  rows=[];page=None;seen=set()
  for _ in range(16):
   if self.remaining<=0:raise Refused("API_BUDGET")
   self.remaining-=1
   kwargs=dict(compartment_id=self.compartment,limit=100,**extra)
   if page:kwargs["page"]=page
   response=method(**kwargs)
   if not isinstance(response.data,list):raise Refused("API_DATA_UNKNOWN")
   rows.extend(response.data)
   if len(rows)>500:raise Refused("RESOURCE_BOUND")
   page=response.headers.get("opc-next-page")
   if not page:return rows
   if page in seen:raise Refused("PAGE_CYCLE")
   seen.add(page)
  raise Refused("PAGE_BOUND")
 def read(self,operation):
  if operation=="get_account_plan_kind":return {"status":"UNKNOWN","reason":"NO_SUPPORTED_ACCOUNT_PLAN_API","plan_kind":None,"resources":{}}
  if operation!="list_pilot_compartment_resources":raise Refused("OPERATION")
  self.remaining=32
  results={}
  for kind in ("compute","boot","block"):
   try:
    if kind=="compute":rows=self._list(self.compute.list_instances,{})
    elif kind=="block":rows=self._list(self.block.list_volumes,{})
    else:
     rows=[]
     for ad in self.ads:rows+=self._list(self.block.list_boot_volumes,{"availability_domain":ad})
    if len(rows)>500:raise Refused("RESOURCE_BOUND")
    # Only aggregate states. Never IDs, names, tags, IPs, account or raw errors.
    allowed={"RUNNING","STOPPED","STARTING","STOPPING","PROVISIONING","AVAILABLE","ATTACHED","TERMINATED","TERMINATING","DELETED","FAULTY"}
    states={}
    for row in rows:
     state=getattr(row,"lifecycle_state",None);state=state if state in allowed else "OTHER_OR_UNKNOWN"
     states[state]=states.get(state,0)+1
    results[kind]={"status":"KNOWN","count":len(rows),"states":states}
   except Exception:results[kind]={"status":"UNKNOWN","count":None,"states":{}}
  return {"status":"KNOWN" if all(x["status"]=="KNOWN" for x in results.values()) else "PARTIAL","reason":"PILOT_SCOPE_ONLY","plan_kind":None,"resources":results}

def sanitize(value):
 if not isinstance(value,dict) or value.get("status") not in {"KNOWN","PARTIAL","UNKNOWN"} or value.get("plan_kind") is not None:raise Refused("ADAPTER_OUTPUT")
 reasons={"NO_SUPPORTED_ACCOUNT_PLAN_API","PILOT_SCOPE_ONLY"}
 if value.get("reason") not in reasons:raise Refused("ADAPTER_OUTPUT")
 resources=value.get("resources")
 if not isinstance(resources,dict) or set(resources)-{"compute","boot","block"}:raise Refused("ADAPTER_OUTPUT")
 clean={}
 allowed={"RUNNING","STOPPED","STARTING","STOPPING","PROVISIONING","AVAILABLE","ATTACHED","TERMINATED","TERMINATING","DELETED","FAULTY","OTHER_OR_UNKNOWN"}
 for kind,row in resources.items():
  count=row.get("count");states=row.get("states")
  if row.get("status") not in {"KNOWN","UNKNOWN"} or not isinstance(states,dict) or set(states)-allowed:raise Refused("ADAPTER_OUTPUT")
  if any(type(v) is not int or v<0 for v in states.values()):raise Refused("ADAPTER_OUTPUT")
  if row["status"]=="KNOWN":
   if type(count) is not int or not 0<=count<=500 or sum(states.values())!=count:raise Refused("ADAPTER_OUTPUT")
  elif count is not None or states:raise Refused("ADAPTER_OUTPUT")
  clean[kind]={"status":row["status"],"count":count,"states":dict(states)}
 if value["reason"]=="PILOT_SCOPE_ONLY":
  if set(clean)!={"compute","boot","block"}:raise Refused("ADAPTER_OUTPUT")
  expected="KNOWN" if all(r["status"]=="KNOWN" for r in clean.values()) else "PARTIAL"
  if value["status"]!=expected:raise Refused("ADAPTER_OUTPUT")
 elif clean or value["status"]!="UNKNOWN":raise Refused("ADAPTER_OUTPUT")
 return {"status":value["status"],"reason":value["reason"],"plan_kind":None,"resources":clean}

class Bridge:
 def __init__(self,trust=None,key=None,replay=None,adapter=None):self.trust,self.key,self.replay,self.adapter=trust,key,replay,adapter
 def receive(self,raw,signature,now):
  # Public prototype deliberately has no configured issuer, credential or executor.
  if any(x is None for x in (self.trust,self.key,self.replay,self.adapter)):return {"status":"NOT_CONNECTED","oracle_query_executed":False}
  e=authorize(raw,signature,self.key,self.trust,now);self.replay.consume(e["request_id"])
  safe=sanitize(self.adapter.read(e["operation"]))
  expected="PILOT_SCOPE_ONLY" if e["operation"]=="list_pilot_compartment_resources" else "NO_SUPPORTED_ACCOUNT_PLAN_API"
  if safe["reason"]!=expected:raise Refused("ADAPTER_OPERATION_MISMATCH")
  return {"protocol":VERSION,"request_id":e["request_id"],"operation":e["operation"],"result":safe}

if __name__=="__main__":print(json.dumps(Bridge().receive(b"", "",0)))
