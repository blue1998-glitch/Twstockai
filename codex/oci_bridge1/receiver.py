"""Prepared private receiver. No listener/workflow is installed or enabled."""
import hashlib,json,datetime,re,urllib.request,urllib.error,urllib.parse
from dataclasses import dataclass
from .bridge import Refused,strict,sanitize,OPS,OCIReadAdapter
ISSUER="https://token.actions.githubusercontent.com"
AUDIENCE="twstockai-oci-read"

def verify_oidc(token):
 """GitHub job identity ONLY; this does not exchange OIDC for OCI credentials."""
 try:
  import jwt
  key=jwt.PyJWKClient(ISSUER+"/.well-known/jwks",timeout=10).get_signing_key_from_jwt(token)
  return jwt.decode(token,key.key,algorithms=["RS256"],audience=AUDIENCE,issuer=ISSUER,options={"require":["exp","iat","nbf","iss","aud","repository_id","repository_visibility","actor_id","workflow_sha","workflow_ref","event_name"]})
 except Exception:raise Refused("OIDC_NOT_VERIFIED")

@dataclass(frozen=True)
class Policy:
 repository:str
 repository_id:int
 actor_id:int
 app_id:int
 installation_id:int
 issue_number:int
 workflow_sha:str
 workflow_ref:str
 zero_paid_usage_verified:bool=False


def validate(event,claims,policy,rest,now):
 # claims must come from verify_oidc, not user JSON or author_association.
 if event.get("action")!="created" or claims.get("event_name")!="issue_comment":raise Refused("EVENT")
 if claims.get("repository_id")!=str(policy.repository_id) or claims.get("repository_visibility")!="private" or claims.get("actor_id")!=str(policy.actor_id):raise Refused("JOB_SCOPE")
 if claims.get("workflow_sha")!=policy.workflow_sha or claims.get("workflow_ref")!=policy.workflow_ref:raise Refused("WORKFLOW_PIN")
 if event.get("installation",{}).get("id")!=policy.installation_id:raise Refused("INSTALLATION_NOT_VERIFIED")
 repo=rest.repository()
 if repo.get("id")!=policy.repository_id or repo.get("full_name")!=policy.repository or repo.get("private") is not True:raise Refused("PRIVATE_REPOSITORY")
 if event.get("repository",{}).get("id")!=policy.repository_id or event.get("sender",{}).get("id")!=policy.actor_id:raise Refused("SENDER")
 issue=event.get("issue",{})
 if issue.get("number")!=policy.issue_number or "pull_request" in issue:raise Refused("ISSUE_SCOPE")
 comment=event.get("comment",{});comment_id=comment.get("id")
 if type(comment_id) is not int or comment_id<=0:raise Refused("COMMENT_ID")
 canonical=rest.comment(comment_id)
 if canonical.get("id")!=comment_id or canonical.get("user",{}).get("id")!=policy.actor_id or (canonical.get("performed_via_github_app") or {}).get("id")!=policy.app_id:raise Refused("CANONICAL_ACTOR_OR_APP")
 expected_issue="https://api.github.com/repos/"+policy.repository+"/issues/"+str(policy.issue_number)
 if canonical.get("issue_url")!=expected_issue:raise Refused("CANONICAL_ISSUE")
 if rest.permission(policy.actor_id) not in ("write","maintain","admin"):raise Refused("REST_PERMISSION")
 if canonical.get("body")!=comment.get("body") or canonical.get("updated_at")!=canonical.get("created_at"):raise Refused("COMMENT_CHANGED")
 try:
  created=datetime.datetime.fromisoformat(canonical['created_at'].replace('Z','+00:00')).timestamp()
  if not 0<=now-created<=300:raise Refused("COMMENT_EXPIRED")
  raw=canonical['body'].encode()
 except (KeyError,ValueError,AttributeError):raise Refused("COMMENT_TIME")
 if len(raw)>256:raise Refused("COMMENT_BOUND")
 request=strict(raw)
 if not isinstance(request,dict) or set(request)!={"schema","operation"} or request['schema']!="oci-read/0.1" or type(request['operation']) is not str or request['operation'] not in OPS:raise Refused("NARROW_COMMAND_ONLY")
 # Immutable comment ID is the nonce. No nonce, URL, shell or compartment from body.
 ident=hashlib.sha256((str(policy.repository_id)+":"+str(policy.issue_number)+":"+str(comment_id)).encode()).hexdigest()[:32]
 return ident,request['operation']

class GitHubRest:
 """Fixed GitHub API paths; token stays in runner memory. No generic public endpoint."""
 def __init__(self,repository,token):
  if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository) or not token:raise Refused('GITHUB_CONFIG')
  self.repo,self.token,self.actor=repository,token,None
 def _request(self,method,path,data=None):
  class NoRedirect(urllib.request.HTTPRedirectHandler):
   def redirect_request(self,*a,**kw):return None
  request=urllib.request.Request('https://api.github.com/repos/'+self.repo+path,method=method,data=None if data is None else json.dumps(data).encode(),headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'Twstockai-OCI-Read'})
  try:
   with urllib.request.build_opener(NoRedirect()).open(request,timeout=15) as response:raw=response.read(2097153)
   if len(raw)>2097152:raise Refused('GITHUB_RESPONSE_BOUND')
   return json.loads(raw)
  except Exception:raise Refused('GITHUB_API_UNAVAILABLE')
 def repository(self):return self._request('GET','')
 def comment(self,ident):
  if type(ident) is not int or ident<=0:raise Refused('COMMENT_ID')
  result=self._request('GET','/issues/comments/'+str(ident));self.actor=result.get('user');return result
 def permission(self,actor_id):
  if not self.actor or self.actor.get('id')!=actor_id or not re.fullmatch(r'[A-Za-z0-9-]{1,39}',self.actor.get('login','')):raise Refused('ACTOR_BINDING')
  value=self._request('GET','/collaborators/'+self.actor['login']+'/permission')
  if value.get('user',{}).get('id')!=actor_id:raise Refused('PERMISSION_ACTOR')
  return value.get('permission')
 def checks(self,sha):
  if not re.fullmatch('[a-f0-9]{40}',sha):raise Refused('CHECK_SHA')
  rows=[]
  for page in range(1,21):
   value=self._request('GET','/commits/'+sha+'/check-runs?check_name=twstockai-oci-read&filter=all&per_page=100&page='+str(page))
   part=value.get('check_runs');total=value.get('total_count')
   if not isinstance(part,list) or type(total) is not int or total>2000:raise Refused('CHECK_HISTORY_UNKNOWN')
   rows+=part
   if len(rows)>=total:return rows
   if not part:raise Refused('CHECK_HISTORY_PARTIAL')
  raise Refused('CHECK_HISTORY_BOUND')
 def start_check(self,sha,ident):
  if not re.fullmatch('[a-f0-9]{40}',sha) or not re.fullmatch('[a-f0-9]{32}',ident):raise Refused('CHECK_BINDING')
  return self._request('POST','/check-runs',dict(name='twstockai-oci-read',head_sha=sha,external_id=ident,status='in_progress'))
 def finish_check(self,check_id,safe):
  if type(check_id) is not int or check_id<=0:raise Refused('CHECK_ID')
  # The caller supplies only the already projected result, never raw OCI objects.
  result=sanitize(safe['result']);summary=json.dumps(result,sort_keys=True)
  return self._request('PATCH','/check-runs/'+str(check_id),dict(status='completed',conclusion='success' if result['status']=='KNOWN' else 'neutral',output=dict(title='OCI read-only receipt',summary=summary)))

 def publish_result(self,issue_number,safe):
  if type(issue_number) is not int or issue_number<=0:raise Refused('ISSUE_SCOPE')
  result=sanitize(safe['result'])
  body='Twstockai OCI read receipt\n```json\n'+json.dumps(result,sort_keys=True)+'\n```'
  return self._request('POST','/issues/'+str(issue_number)+'/comments',{'body':body})

class PersistentChecks:
 """Used only behind one private workflow concurrency group. No pending auto-retry."""
 def __init__(self,rest,sha):self.rest,self.sha=rest,sha
 def consume(self,ident):
  # rest.checks must paginate completely or refuse; never truncate history.
  rows=self.rest.checks(self.sha)
  if any(r.get('external_id')==ident for r in rows):raise Refused('REPLAY_OR_PRIOR_OUTCOME_UNKNOWN')
  result=self.rest.start_check(self.sha,ident)
  if result.get('external_id')!=ident or type(result.get('id')) is not int:raise Refused('CHECK_WRITE_NOT_CONFIRMED')
  return result['id']

class Receiver:
 def __init__(self,policy,rest,replay,adapter_factory):self.policy,self.rest,self.replay,self.adapter_factory=policy,rest,replay,adapter_factory
 def receive(self,event,oidc_token,now):
  claims=verify_oidc(oidc_token)
  ident,op=validate(event,claims,self.policy,self.rest,now)
  # Missing billing/budget evidence must never activate Secrets/OCI clients.
  if self.policy.zero_paid_usage_verified is not True:return {'status':'NOT_CONNECTED','reason':'ZERO_PAID_USAGE_NOT_VERIFIED','oracle_query_executed':False}
  self.replay.consume(ident)
  adapter=self.adapter_factory() # Only here may a future private executor read OCI secrets.
  result=sanitize(adapter.read(op))
  expected='NO_SUPPORTED_ACCOUNT_PLAN_API' if op=='get_account_plan_kind' else 'PILOT_SCOPE_ONLY'
  if result['reason']!=expected:raise Refused('RESULT_OPERATION')
  return {'request_id':ident,'operation':op,'result':result}

 def receive_safe(self,event,oidc_token,now):
  try:return self.receive(event,oidc_token,now)
  except Refused:return {'status':'NOT_CONNECTED','reason':'AUTHORIZATION_OR_REPLAY_REFUSED','oracle_query_executed':'UNKNOWN'}
  except Exception:return {'status':'NOT_CONNECTED','reason':'TRUSTED_EXECUTOR_FAILURE','oracle_query_executed':'UNKNOWN'}
