"""Read saved Journal checkpoints behind the ORIGINAL owner/whitelist/cache.
Only fixed descriptors; never calculate recognition or accept arbitrary paths.
"""
from pathlib import Path
import json
from rotation_research import artifact_codec as c
from rotation_research.store import Journal
from graph_core.graph_lazy1_20261104.provider import Provider as Original,Refused
from .engine import read,sha,validate
from .present import present
class Provider(Original):
    def __init__(self,path,digest):
        super().__init__(path,digest,runner=self.hydrate)
        item=self.spec["scan_index"];p=c.regular(Path(item["path"]));b=p.read_bytes()
        if len(b)>2097152 or len(b)!=item["bytes"] or sha(b)!=item["sha256"]:raise Refused("SAVED_INDEX_BINDING")
        self.index=json.loads(b);desc=self.spec["scan_manifest"];raw=c.regular(Path(desc["path"])).read_bytes()
        if len(raw)!=desc["bytes"] or sha(raw)!=desc["sha256"]:raise Refused("SCAN_MANIFEST_BINDING")
        self.numeric=json.loads(raw)
        if self.numeric["id"]!=self.index["scan_id"]:raise Refused("SCAN_VERSION_MISMATCH")
        self.rows={r["identity"]:r for r in self.index["records"]};self.stocks={s["identity"]:s for s in self.numeric["stocks"]};self.journal=Journal(p.parent/"results")
        if set(self.rows)!=set(self.stocks):raise Refused("INCOMPLETE_SCAN_INDEX")
    def record(self,identity):
        row=self.rows[identity];p=c.regular(self.journal.path(row["key"]));b=p.read_bytes()
        if len(b)>8192 or len(b)!=row["bytes"] or sha(b)!=row["record_sha256"]:raise Refused("SAVED_RESULT_TAMPERED")
        v=self.journal.read(row["key"])["value"];validate(v,self.stocks[identity],self.numeric);return v
    def hydrate(self,f):
        v=self.record(f["identity"])
        if v["status"]!="EXECUTED_INSUFFICIENT_HISTORY":raise Refused("NO_SUCCESSFUL_SAVED_CORE")
        return present(f,v)
    def get(self,route,allowed):
        if route==self.spec.get("metrics_route"):
            raw,flag=super().get(route,allowed);v=json.loads(raw);v.update(saved_scan=True,new_numeric_core_calls=0,scan_id=self.index["scan_id"]);return json.dumps(v,sort_keys=True).encode(),flag
        if route not in self.actions:raise KeyError("UNKNOWN_ACTION")
        identity=self.actions[route]["identity"];v=self.record(identity) # Validate before a RAM cache HIT too.
        raw,flag=super().get(route,allowed);body=json.loads(raw);row=self.rows[identity]
        body.update(scan_status=v["status"],scan_id=self.index["scan_id"],scan_record_sha256=row["record_sha256"],scan_core_calls=v["core_calls"])
        return json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode(),flag
