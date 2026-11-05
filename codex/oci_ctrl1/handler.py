"""M-OCI-CTRL1. Stdlib-only PING receiver; no OCI, Secrets or shell execution."""
import base64,datetime,hashlib,json,os,re,sys,urllib.request,urllib.error
VERSION="M-OCI-CTRL1/0.1"
REPO="blue1998-glitch/Twstockai-oci-bridge-private"
REPO_ID=1446437252
OWNER_ID=319797247
PATH=".github/workflows/ctrl1.yml"
SCHEMA="oci-ctrl/0.1"
MARKER="<!-- twstockai-ctrl1:"
WORKFLOW_TEMPLATE = r"""name: M-OCI-CTRL1 private PING
"on":
  issue_comment:
    types: [created]
permissions:
  contents: read
  actions: read
  issues: write
concurrency:
  group: twstockai-ctrl1-repository-1446437252
  cancel-in-progress: false
jobs:
  ping:
    if: >-
      github.event_name == 'issue_comment' &&
      github.event.action == 'created' &&
      github.repository_id == '1446437252' &&
      github.event.issue.number == 1 &&
      github.event.sender.id == 319797247 &&
      !github.event.issue.pull_request
    runs-on: ubuntu-24.04
    timeout-minutes: 2
    steps:
      - name: Verify fixed receiver bytes and process native event
        env:
          CTRL1_TOKEN: ${{ github.token }}
        shell: bash
        run: |
          python3 - <<'CTRL1_BOOTSTRAP'
          import base64,hashlib,json,os,subprocess,sys,tempfile,urllib.request
          from pathlib import Path
          BLOB='__CTRL1_BLOB__'
          SHA='__CTRL1_SHA__'
          class NoRedirect(urllib.request.HTTPRedirectHandler):
           def redirect_request(self,*a,**kw):return None
          try:
           url='https://api.github.com/repos/blue1998-glitch/Twstockai-oci-bridge-private/git/blobs/'+BLOB
           req=urllib.request.Request(url,headers={'Authorization':'Bearer '+os.environ['CTRL1_TOKEN'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
           with urllib.request.build_opener(NoRedirect()).open(req,timeout=15) as response:
            if response.status!=200:raise ValueError()
            obj=json.loads(response.read(131073))
           if obj.get('encoding')!='base64':raise ValueError()
           raw=base64.b64decode(obj['content'])
           if len(raw)>65536 or hashlib.sha256(raw).hexdigest()!=SHA or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=BLOB:raise ValueError()
          except Exception:sys.exit('CTRL1_SOURCE_VERIFICATION_FAILED_NO_RETRY')
          with tempfile.TemporaryDirectory(prefix='twstockai-ctrl1-',dir=os.environ['RUNNER_TEMP']) as folder:
           path=Path(folder)/'handler.py';path.write_bytes(raw);path.chmod(0o600)
           raise SystemExit(subprocess.run([sys.executable,str(path)]).returncode)
          CTRL1_BOOTSTRAP
"""
def render_workflow(source):
 return WORKFLOW_TEMPLATE.replace('__CTRL1_BLOB__',git_blob(source)).replace('__CTRL1_SHA__',hashlib.sha256(source).hexdigest()).encode()

class Refused(Exception):pass

def strict(raw):
 def pairs(rows):
  d={}
  for k,v in rows:
   if k in d:raise Refused('DUPLICATE_KEY')
   d[k]=v
  return d
 try:return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Refused('NONFINITE_JSON')))
 except (ValueError,TypeError):raise Refused('INVALID_JSON')

def git_blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def timestamp(value):
 try:
  d=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
  if d.tzinfo is None:raise ValueError()
  return d.timestamp()
 except (AttributeError,ValueError):raise Refused('INVALID_TIME')

class API:
 def __init__(self,token):
  if not token:raise Refused('MISSING_JOB_TOKEN')
  self.token,self.calls=token,0
 def request(self,method,path,data=None):
  self.calls+=1
  if self.calls>20:raise Refused('API_CALL_BOUND')
  class NoRedirect(urllib.request.HTTPRedirectHandler):
   def redirect_request(self,*a,**kw):return None
  request=urllib.request.Request('https://api.github.com/repos/'+REPO+path,method=method,data=None if data is None else json.dumps(data).encode(),headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'Twstockai-CTRL1'})
  try:
   with urllib.request.build_opener(NoRedirect()).open(request,timeout=10) as response:raw=response.read(2097153)
   if len(raw)>2097152:raise Refused('API_RESPONSE_BOUND')
   return strict(raw)
  except Refused:raise
  except Exception:raise Refused('GITHUB_API_UNAVAILABLE_NO_RETRY')
 def content(self,path,sha):
  if not re.fullmatch('[a-f0-9]{40}',sha):raise Refused('COMMIT_FORMAT')
  value=self.request('GET','/contents/'+path+'?ref='+sha)
  try:
   if value.get('encoding')!='base64' or value.get('type')!='file':raise ValueError()
   raw=base64.b64decode(value['content'])
   if len(raw)>65536 or git_blob(raw)!=value['sha']:raise ValueError()
   return raw,value['sha']
  except Exception:raise Refused('SOURCE_BYTES_INVALID')
 def comments(self):
  rows=[]
  for page in range(1,11):
   part=self.request('GET','/issues/1/comments?per_page=100&page='+str(page))
   if not isinstance(part,list):raise Refused('LEDGER_UNKNOWN')
   rows+=part
   if len(part)<100:return rows
  raise Refused('LEDGER_BOUND_NO_TRUNCATION')

class Controller:
 def __init__(self,api,context,event,source,now):
  self.api,self.ctx,self.event,self.source,self.now=api,context,event,source,now
  self.policy=None;self.comment_id=None;self.reply_authorized=False
 def verify_scope(self):
  c=self.ctx;e=self.event
  if c.get('GITHUB_ACTIONS')!='true' or c.get('GITHUB_EVENT_NAME')!='issue_comment' or c.get('GITHUB_REPOSITORY')!=REPO or c.get('GITHUB_REPOSITORY_ID')!=str(REPO_ID) or c.get('GITHUB_ACTOR_ID')!=str(OWNER_ID):raise Refused('NATIVE_JOB_SCOPE')
  if c.get('GITHUB_RUN_ATTEMPT')!='1':raise Refused('RERUN_NOT_ALLOWED')
  if c.get('GITHUB_REF')!='refs/heads/main' or c.get('GITHUB_WORKFLOW_REF')!=REPO+'/'+PATH+'@refs/heads/main':raise Refused('WORKFLOW_REF')
  sha=c.get('GITHUB_WORKFLOW_SHA','')
  if not re.fullmatch('[a-f0-9]{40}',sha) or c.get('GITHUB_SHA')!=sha:raise Refused('COMMIT_PIN')
  if e.get('action')!='created' or e.get('repository',{}).get('id')!=REPO_ID or e.get('repository',{}).get('private') is not True or e.get('sender',{}).get('id')!=OWNER_ID:raise Refused('NATIVE_EVENT_SCOPE')
  issue=e.get('issue',{})
  if issue.get('number')!=1 or 'pull_request' in issue:raise Refused('ISSUE_SCOPE')
  comment=e.get('comment',{});cid=comment.get('id')
  if type(cid) is not int or cid<=0:raise Refused('COMMENT_ID')
  runid=c.get('GITHUB_RUN_ID','')
  if not re.fullmatch('[1-9][0-9]{0,19}',runid):raise Refused('RUN_ID')
  repo=self.api.request('GET','')
  if repo.get('id')!=REPO_ID or repo.get('private') is not True or repo.get('full_name')!=REPO or repo.get('default_branch')!='main':raise Refused('CANONICAL_REPOSITORY')
  run=self.api.request('GET','/actions/runs/'+runid)
  if run.get('id')!=int(runid) or run.get('run_attempt')!=1 or run.get('event')!='issue_comment' or run.get('head_sha')!=sha or run.get('head_branch')!='main' or run.get('actor',{}).get('id')!=OWNER_ID or run.get('repository',{}).get('id')!=REPO_ID or run.get('path')!=PATH or run.get('status')!='in_progress':raise Refused('CANONICAL_RUN')
  release_raw,_=self.api.content('ctrl1/release.json',sha);policy=strict(release_raw)
  expected={'schema','version','repository_id','actor_id','source_app_id','installation_id','bot_id','bot_app_id','workflow_blob','controller_blob','controller_sha256'}
  if not isinstance(policy,dict) or set(policy)!=expected or policy['schema']!='oci-ctrl-release/0.1' or policy['version']!=VERSION or policy['repository_id']!=REPO_ID or policy['actor_id']!=OWNER_ID:raise Refused('RELEASE_POLICY')
  if any(type(policy[k]) is not int or policy[k]<=0 for k in ['source_app_id','installation_id','bot_id','bot_app_id']):raise Refused('NATIVE_ID_BINDINGS')
  if policy['controller_blob']!=git_blob(self.source) or policy['controller_sha256']!=hashlib.sha256(self.source).hexdigest():raise Refused('CONTROLLER_PIN')
  workflow_raw,workflow_blob=self.api.content(PATH,sha)
  if workflow_blob!=policy['workflow_blob'] or workflow_raw!=render_workflow(self.source):raise Refused('WORKFLOW_BLOB_PIN')
  canonical=self.api.request('GET','/issues/comments/'+str(cid))
  if canonical.get('id')!=cid or canonical.get('issue_url')!='https://api.github.com/repos/'+REPO+'/issues/1' or canonical.get('user',{}).get('id')!=OWNER_ID or canonical.get('user',{}).get('login')!='blue1998-glitch' or (canonical.get('performed_via_github_app') or {}).get('id')!=policy['source_app_id']:raise Refused('CANONICAL_COMMENT_ACTOR_APP')
  permission=self.api.request('GET','/collaborators/blue1998-glitch/permission')
  if permission.get('user',{}).get('id')!=OWNER_ID or permission.get('permission') not in ('write','maintain','admin'):raise Refused('ACTOR_PERMISSION')
  if canonical.get('body')!=comment.get('body') or canonical.get('updated_at')!=canonical.get('created_at'):raise Refused('EDITED_COMMENT')
  created=timestamp(canonical.get('created_at'))
  if not 0<=self.now-created<=300 or timestamp(run.get('created_at'))<created:raise Refused('COMMENT_TIME_WINDOW')
  self.policy=policy;self.comment_id=cid;self.reply_authorized=True
  # Never invent a missing native installation field or silently downgrade it.
  native_installation=(e.get('installation') or {}).get('id')
  if type(native_installation) is not int:raise Refused('NATIVE_INSTALLATION_MISSING')
  if native_installation!=policy['installation_id']:raise Refused('NATIVE_INSTALLATION_MISMATCH')
  body=canonical.get('body')
  if not isinstance(body,str) or len(body.encode())>256:raise Refused('COMMAND_BOUND')
  value=strict(body)
  if not isinstance(value,dict) or set(value)!={'schema','operation'} or value['schema']!=SCHEMA or value['operation']!='ping':raise Refused('ONLY_FIXED_PING')
 def receipt(self,status,reason=None):
  value={'schema':'oci-ctrl-receipt/0.1','controller_version':VERSION,'status':status,'operation':'ping','request_comment_id':self.comment_id,'run_id':int(self.ctx['GITHUB_RUN_ID']),'run_attempt':1,'run_url':'https://github.com/'+REPO+'/actions/runs/'+self.ctx['GITHUB_RUN_ID'],'workflow_commit_sha':self.ctx['GITHUB_WORKFLOW_SHA'],'workflow_blob_sha':self.policy['workflow_blob'],'controller_sha256':hashlib.sha256(self.source).hexdigest(),'oracle_status':'NOT_CONNECTED','oracle_calls':0}
  if reason:value['reason']=reason
  return value
 def body(self,value):return MARKER+str(self.comment_id)+' -->\n```json\n'+json.dumps(value,sort_keys=True,indent=2)+'\n```'
 def prior(self):
  marker=MARKER+str(self.comment_id)+' -->'
  for row in self.api.comments():
   if row.get('user',{}).get('id')==self.policy['bot_id'] and (row.get('performed_via_github_app') or {}).get('id')==self.policy['bot_app_id'] and row.get('body','').startswith(marker):return True
  return False
 def post(self,value):
  row=self.api.request('POST','/issues/1/comments',{'body':self.body(value)})
  if type(row.get('id')) is not int or row.get('user',{}).get('id')!=self.policy['bot_id'] or (row.get('performed_via_github_app') or {}).get('id')!=self.policy['bot_app_id'] or row.get('body')!=self.body(value):raise Refused('RECEIPT_OUTCOME_UNKNOWN_NO_RETRY')
  return row['id']
 def execute(self):
  try:self.verify_scope()
  except Refused as err:
   # Only an authenticated owner request in the canonical private issue can get a refusal receipt.
   if self.reply_authorized and not self.prior():self.post(self.receipt('REJECTED',str(err)))
   raise
  if self.prior():return {'status':'DUPLICATE_NO_ACTION','request_comment_id':self.comment_id}
  rid=self.post(self.receipt('STARTED')) # Durable before PING, serialized by workflow concurrency.
  value=self.receipt('PING_OK')
  updated=self.api.request('PATCH','/issues/comments/'+str(rid),{'body':self.body(value)})
  if updated.get('id')!=rid or updated.get('body')!=self.body(value) or updated.get('user',{}).get('id')!=self.policy['bot_id'] or (updated.get('performed_via_github_app') or {}).get('id')!=self.policy['bot_app_id']:raise Refused('RECEIPT_UPDATE_NOT_CONFIRMED')
  return value

def main():
 try:
  file=os.environ['GITHUB_EVENT_PATH']
  with open(file,'rb') as f:raw=f.read(2097153)
  if len(raw)>2097152:raise Refused('EVENT_BOUND')
  event=strict(raw)
  source=open(__file__,'rb').read()
  context={k:os.environ.get(k,'') for k in ['GITHUB_ACTIONS','GITHUB_EVENT_NAME','GITHUB_REPOSITORY','GITHUB_REPOSITORY_ID','GITHUB_ACTOR_ID','GITHUB_RUN_ATTEMPT','GITHUB_REF','GITHUB_WORKFLOW_REF','GITHUB_WORKFLOW_SHA','GITHUB_SHA','GITHUB_RUN_ID']}
  result=Controller(API(os.environ.get('CTRL1_TOKEN','')),context,event,source,datetime.datetime.now(datetime.timezone.utc).timestamp()).execute()
  print(json.dumps({'status':result['status'],'request_comment_id':result.get('request_comment_id'),'run_id':result.get('run_id')}));return 0
 except Refused as err:print('CTRL1_REFUSED:'+str(err));return 2
 except Exception:print('CTRL1_REFUSED:UNEXPECTED_FAILURE_NO_RETRY');return 2
if __name__=='__main__':raise SystemExit(main())
