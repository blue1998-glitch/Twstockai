"""READ1 native gate. Shares CTRL1 primitives, never broadens PING permissions."""
import datetime,hashlib,json,os,re,sys,zipfile
from codex.oci_ctrl1.handler import API,Refused,strict,timestamp,git_blob,REPO,REPO_ID,OWNER_ID
from codex.oci_read1.protocol import parse_command
from codex.oci_bridge1.bridge import Refused as BridgeRefused
PATH=".github/workflows/read1.yml"
VERSION="M-OCI-READ1/OAUTH-0.2"
MARKER="<!-- twstockai-read1:"
REVIEW_FLAGS={"free_domain_wif","existing_independent_pilot","minimum_list_iam","oauth_client_no_admin","repository_secret_risk_accepted","zero_paid_block_unchanged","writers_and_workflows_reviewed"}

def render_workflow(package):
    with zipfile.ZipFile(__import__('io').BytesIO(package)) as z:
        template=z.read("workflow.template").decode()
    return template.replace("__BLOB__",git_blob(package)).replace("__SHA__",hashlib.sha256(package).hexdigest()).encode()

class Gate:
    def __init__(self,api,ctx,event,package,now):
        self.api,self.c,self.e,self.package,self.now=api,ctx,event,package,now
        self.release=None;self.cid=None
    def verify(self):
        c,e=self.c,self.e
        for key,want in {"GITHUB_ACTIONS":"true","GITHUB_EVENT_NAME":"issue_comment","GITHUB_REPOSITORY":REPO,"GITHUB_REPOSITORY_ID":str(REPO_ID),"GITHUB_ACTOR_ID":str(OWNER_ID),"GITHUB_RUN_ATTEMPT":"1","GITHUB_REF":"refs/heads/main","GITHUB_WORKFLOW_REF":REPO+"/"+PATH+"@refs/heads/main"}.items():
            if c.get(key)!=want:raise Refused("READ1_NATIVE_SCOPE")
        sha=c.get("GITHUB_WORKFLOW_SHA","")
        if not re.fullmatch("[a-f0-9]{40}",sha) or c.get("GITHUB_SHA")!=sha:raise Refused("READ1_COMMIT")
        if e.get("action")!="created" or e.get("repository",{}).get("id")!=REPO_ID or e.get("repository",{}).get("private") is not True or e.get("sender",{}).get("id")!=OWNER_ID:raise Refused("READ1_EVENT")
        if e.get("issue",{}).get("number")!=1 or "pull_request" in e["issue"]:raise Refused("READ1_ISSUE")
        cid=e.get("comment",{}).get("id");rid=c.get("GITHUB_RUN_ID","")
        if type(cid) is not int or cid<=0 or not re.fullmatch("[1-9][0-9]{0,19}",rid):raise Refused("READ1_IDS")
        repo=self.api.request("GET","");run=self.api.request("GET","/actions/runs/"+rid)
        if repo.get("id")!=REPO_ID or repo.get("private") is not True or repo.get("full_name")!=REPO or repo.get("default_branch")!="main":raise Refused("READ1_REPOSITORY")
        expected={"id":int(rid),"event":"issue_comment","head_sha":sha,"head_branch":"main","path":PATH,"run_attempt":1,"status":"in_progress"}
        if any(run.get(k)!=v for k,v in expected.items()):raise Refused("READ1_RUN")
        if any(run.get(k,{}).get("id")!=OWNER_ID for k in ("actor","triggering_actor")) or any(run.get(k,{}).get("id")!=REPO_ID for k in ("repository","head_repository")):raise Refused("READ1_RUN_ACTOR_REPOSITORY")
        wid=run.get("workflow_id")
        if type(wid) is not int:raise Refused("READ1_WORKFLOW")
        wf=self.api.request("GET","/actions/workflows/"+str(wid))
        if wf.get("id")!=wid or wf.get("path")!=PATH or wf.get("state")!="active":raise Refused("READ1_WORKFLOW")
        raw,_=self.api.content("read1/oauth/release.json",sha);release=strict(raw)
        fields={"schema","version","source_app_id","bot_id","bot_app_id","package_sha256","package_blob"}
        if set(release)!=fields or release.get("schema")!="read1-oauth-release/0.2" or release.get("version")!=VERSION:raise Refused("READ1_RELEASE")
        if any(type(release[k]) is not int or release[k]<=0 for k in ("source_app_id","bot_id","bot_app_id")):raise Refused("READ1_SOURCE_BINDINGS")
        if release["package_sha256"]!=hashlib.sha256(self.package).hexdigest() or release["package_blob"]!=git_blob(self.package):raise Refused("READ1_CODE_PIN")
        workflow,_=self.api.content(PATH,sha)
        if workflow!=render_workflow(self.package):raise Refused("READ1_WORKFLOW_BYTES")
        comment=self.api.request("GET","/issues/comments/"+str(cid));perm=self.api.request("GET","/collaborators/blue1998-glitch/permission")
        if comment.get("id")!=cid or comment.get("issue_url")!="https://api.github.com/repos/"+REPO+"/issues/1" or comment.get("user",{}).get("id")!=OWNER_ID or comment.get("user",{}).get("login")!="blue1998-glitch" or (comment.get("performed_via_github_app") or {}).get("id")!=release["source_app_id"]:raise Refused("READ1_CANONICAL_COMMENT")
        if perm.get("user",{}).get("id")!=OWNER_ID or perm.get("permission") not in ("admin","maintain","write"):raise Refused("READ1_PERMISSION")
        event_comment=e["comment"]
        if event_comment.get("user",{}).get("id")!=OWNER_ID or event_comment.get("body")!=comment.get("body") or comment.get("created_at")!=comment.get("updated_at"):raise Refused("READ1_EDITED_OR_ACTOR")
        created=timestamp(comment.get("created_at"))
        if not 0<=self.now-created<=300 or timestamp(run.get("created_at"))<created:raise Refused("READ1_FRESHNESS")
        try:parse_command(comment["body"].encode())
        except BridgeRefused as error:raise Refused(str(error))
        self.cid,self.release=cid,release
        return self
    def qualification(self):
        sha=self.c["GITHUB_WORKFLOW_SHA"]
        qraw,_=self.api.content("read1/oauth/account.json",sha);q=strict(qraw)
        fields={"schema","source","captured_at","expires_at","config_binding","observations","findings","config"}
        if not isinstance(q,dict) or set(q)!=fields or q["schema"]!="read1-owner-account/0.2" or q["source"]!="OWNER_CONSOLE_OBSERVATION_NOT_ORACLE_API":raise Refused("READ1_ACCOUNT_EVIDENCE_UNKNOWN")
        if not isinstance(q["findings"],dict) or set(q["findings"])!=REVIEW_FLAGS or any(x!="OWNER_CONFIRMED" for x in q["findings"].values()):raise Refused("READ1_ACCOUNT_PREREQUISITES_UNKNOWN")
        if q["config_binding"]!="SAME_IMMUTABLE_WORKFLOW_COMMIT":raise Refused("READ1_ACCOUNT_CONFIG_BINDING")
        observed=q["observations"]
        names={"domain_kind","wif_feature_and_region","pilot_scope_and_iam","quota_and_billing","private_writers_review"}
        if not isinstance(observed,dict) or set(observed)!=names or observed["domain_kind"]!="Free" or any(not isinstance(x,str) or not 1<=len(x)<=4000 or x=="UNKNOWN" for x in observed.values()):raise Refused("READ1_ACCOUNT_EVIDENCE_UNKNOWN")
        start,end=timestamp(q["captured_at"]),timestamp(q["expires_at"])
        if not start<=self.now<end or end-start>86400:raise Refused("READ1_ACCOUNT_EVIDENCE_EXPIRED")
        from .federation import validate_config
        config=validate_config(q["config"])
        self.account_sha256=hashlib.sha256(qraw).hexdigest()
        self.config_sha256=hashlib.sha256(json.dumps(config,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        return config
    def receipts(self):
        prefix=MARKER+str(self.cid)+" -->"
        return [r for r in self.api.comments() if r.get("user",{}).get("id")==self.release["bot_id"] and (r.get("performed_via_github_app") or {}).get("id")==self.release["bot_app_id"] and r.get("body","").startswith(prefix)]
    def value(self,status,**extra):
        return dict(schema="oci-read-receipt/0.2",version=VERSION,status=status,request_comment_id=self.cid,native_run_id=int(self.c["GITHUB_RUN_ID"]),workflow_sha=self.c["GITHUB_WORKFLOW_SHA"],package_sha256=hashlib.sha256(self.package).hexdigest(),installation_attestation="NOT_ATTESTED",account_evidence_sha256=getattr(self,"account_sha256",None),config_sha256=getattr(self,"config_sha256",None),**extra)
    def body(self,value):return MARKER+str(self.cid)+" -->\n```json\n"+json.dumps(value,sort_keys=True,indent=2)+"\n```"
    def write(self,value,ident=None):
        method,path=("POST","/issues/1/comments") if ident is None else ("PATCH","/issues/comments/"+str(ident))
        r=self.api.request(method,path,{"body":self.body(value)})
        if type(r.get("id")) is not int or (ident is not None and r["id"]!=ident) or r.get("body")!=self.body(value) or r.get("user",{}).get("id")!=self.release["bot_id"] or (r.get("performed_via_github_app") or {}).get("id")!=self.release["bot_app_id"]:raise Refused("READ1_RECEIPT_OUTCOME_UNKNOWN_NO_RETRY")
        return r["id"]
    def prior_value(self,row):
        try:return strict(row["body"].split("```json\n",1)[1].split("\n```",1)[0])
        except Exception:raise Refused("READ1_LEDGER_UNKNOWN")
    def authorize(self):
        if self.receipts():return False
        try:self.qualification()
        except Refused as e:
            self.write(self.value("BLOCKED_ACCOUNT_QUALIFICATION",reason=str(e),oracle_calls=0));return False
        self.write(self.value("AUTHORIZED",oracle_calls=0))
        return True
    def claim(self):
        self.qualification();rows=self.receipts()
        if len(rows)!=1:raise Refused("READ1_NONCE_UNAVAILABLE")
        row=rows[0];v=self.prior_value(row)
        if v.get("status")!="AUTHORIZED" or v.get("native_run_id")!=int(self.c["GITHUB_RUN_ID"]) or v.get("workflow_sha")!=self.c["GITHUB_WORKFLOW_SHA"] or v.get("package_sha256")!=hashlib.sha256(self.package).hexdigest():raise Refused("READ1_NONCE_ALREADY_CONSUMED")
        self.write(self.value("EXCHANGING",oracle_calls="UNKNOWN_UNTIL_FINAL_RECEIPT"),row["id"])
        return row["id"]
    def read(self):
        config=self.qualification();rows=self.receipts()
        if len(rows)!=1:raise Refused("READ1_NONCE_UNAVAILABLE")
        row=rows[0];v=self.prior_value(row)
        if v.get("status")!="EXCHANGING" or v.get("native_run_id")!=int(self.c["GITHUB_RUN_ID"]) or v.get("workflow_sha")!=self.c["GITHUB_WORKFLOW_SHA"] or v.get("package_sha256")!=hashlib.sha256(self.package).hexdigest():raise Refused("READ1_NONCE_ALREADY_CONSUMED")
        # All native/qualification/nonce gates precede reading the OAuth secret.
        from .federation import execute
        result=execute(config,self.c,self.now)
        self.write(self.value(**result),row["id"])
        return result["status"]
