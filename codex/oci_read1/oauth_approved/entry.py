"""Pinned package entry. No raw exceptions/credential values on stdout."""
import datetime,hashlib,json,os,sys,zipfile
from codex.oci_ctrl1.handler import API,Refused
from codex.oci_read1.oauth_approved.native import Gate

def integrity(raw):
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip() is not None:raise Refused("READ1_PACKAGE_CRC_OR_DUPLICATE")
        manifest=json.loads(z.read("MANIFEST.json"));rows=manifest["files"]
        if set(names)!={r["path"] for r in rows}|{"MANIFEST.json"}:raise Refused("READ1_PACKAGE_MANIFEST")
        for r in rows:
            path=r["path"]
            if path.startswith("/") or ".." in path.split("/") or "\\" in path:raise Refused("READ1_PACKAGE_PATH")
            data=z.read(path)
            if len(data)!=r["bytes"] or hashlib.sha256(data).hexdigest()!=r["sha256"]:raise Refused("READ1_PACKAGE_FINGERPRINT")

def output(key,value):
    if not isinstance(value,str) or "\n" in value or "\r" in value:raise Refused("READ1_JOB_OUTPUT")
    with open(os.environ["GITHUB_OUTPUT"],"a") as f:f.write(key+"="+value+"\n")

def main():
    try:
        raw=open(sys.argv[0],"rb").read();integrity(raw)
        mode=sys.argv[1:] or ["inspect"]
        if mode==["inspect"]:
            print(json.dumps({"version":"M-OCI-READ1/OAUTH-0.2","status":"DEFAULT_DENY_PENDING_ACCOUNT_EVIDENCE","oracle_calls":0,"oauth_repository_secret_authorized":True}));return 0
        if mode not in [["authorize"],["prepare"],["read"]]:raise Refused("READ1_FIXED_MODE")
        with open(os.environ["GITHUB_EVENT_PATH"],"rb") as f:event_raw=f.read(2097153)
        if len(event_raw)>2097152:raise Refused("READ1_EVENT_BOUND")
        from codex.oci_ctrl1.handler import strict
        event=strict(event_raw)
        keys=["GITHUB_ACTIONS","GITHUB_EVENT_NAME","GITHUB_REPOSITORY","GITHUB_REPOSITORY_ID","GITHUB_ACTOR_ID","GITHUB_RUN_ATTEMPT","GITHUB_REF","GITHUB_WORKFLOW_REF","GITHUB_WORKFLOW_SHA","GITHUB_SHA","GITHUB_RUN_ID"]
        c={k:os.environ.get(k,"") for k in keys}
        gate=Gate(API(os.environ.get("READ1_GITHUB_TOKEN")),c,event,raw,datetime.datetime.now(datetime.timezone.utc).timestamp()).verify()
        if mode==["authorize"]:
            approved=gate.authorize();output("approved","true" if approved else "false");print("READ1_AUTHORIZED" if approved else "READ1_BLOCKED_OR_NONCE_CONSUMED");return 0
        if mode==["prepare"]:
            gate.claim()
            # Only extract the pinned lockfile; no arbitrary ZIP extraction.
            with zipfile.ZipFile(sys.argv[0]) as z:lock=z.read("requirements.lock")
            folder=os.path.dirname(os.path.abspath(sys.argv[0]));path=os.path.join(folder,"requirements.lock")
            with open(path,"xb") as f:f.write(lock)
            os.chmod(path,0o600)
            output("package_path",os.path.abspath(sys.argv[0]));output("requirements_path",path);output("ready","true");print("READ1_NONCE_CLAIMED_NO_SECRET_READ");return 0
        print(gate.read());return 0
    except Refused as e:print("READ1_REFUSED:"+str(e));return 2
    except Exception:print("READ1_REFUSED:EXECUTION_OUTCOME_UNKNOWN_NO_RETRY");return 2
if __name__=="__main__":raise SystemExit(main())
