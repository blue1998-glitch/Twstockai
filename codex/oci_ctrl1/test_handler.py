import unittest,copy,json,hashlib,base64
from unittest.mock import patch
from . import handler as h
class Fake:
 def __init__(self):
  self.calls=[];self.rows=[];self.failpost=False;self.badbot=False;self.source=b'SYNTHETIC_CONTROLLER';self.workflow=h.render_workflow(self.source)
  self.policy=dict(schema='oci-ctrl-release/0.1',version=h.VERSION,repository_id=h.REPO_ID,actor_id=h.OWNER_ID,source_app_id=400,installation_id=500,bot_id=600,bot_app_id=700,workflow_blob=h.git_blob(self.workflow),controller_blob=h.git_blob(self.source),controller_sha256=hashlib.sha256(self.source).hexdigest())
  self.comment=dict(id=800,issue_url='https://api.github.com/repos/'+h.REPO+'/issues/1',user={'id':h.OWNER_ID,'login':'blue1998-glitch'},performed_via_github_app={'id':400},body='{"schema":"oci-ctrl/0.1","operation":"ping"}',created_at='2026-11-05T00:00:00Z',updated_at='2026-11-05T00:00:00Z')
  self.run=dict(id=42,run_attempt=1,event='issue_comment',head_sha='a'*40,head_branch='main',actor={'id':h.OWNER_ID},repository={'id':h.REPO_ID},path=h.PATH,status='in_progress',created_at='2026-11-05T00:00:01Z')
 def request(self,method,path,data=None):
  self.calls.append((method,path,data))
  if method=='GET':
   if path=='':return dict(id=h.REPO_ID,private=True,full_name=h.REPO,default_branch='main')
   if path=='/actions/runs/42':return self.run
   if path=='/issues/comments/800':return self.comment
   if path=='/collaborators/blue1998-glitch/permission':return dict(user={'id':h.OWNER_ID},permission='admin')
  if method=='POST':
   if self.failpost:raise h.Refused('GITHUB_API_UNAVAILABLE_NO_RETRY')
   row=dict(id=900+len(self.rows),body=data['body'],user={'id':999 if self.badbot else 600},performed_via_github_app={'id':700});self.rows.append(row);return row
  if method=='PATCH':
   row=self.rows[-1];row['body']=data['body'];return row
  raise AssertionError('Unexpected path')
 def content(self,path,sha):
  if path==h.PATH:return self.workflow,h.git_blob(self.workflow)
  return json.dumps(self.policy).encode(),'b'*40
 def comments(self):return self.rows
class Tests(unittest.TestCase):
 def setUp(self):
  self.api=Fake();self.ctx=dict(GITHUB_ACTIONS='true',GITHUB_EVENT_NAME='issue_comment',GITHUB_REPOSITORY=h.REPO,GITHUB_REPOSITORY_ID=str(h.REPO_ID),GITHUB_ACTOR_ID=str(h.OWNER_ID),GITHUB_RUN_ATTEMPT='1',GITHUB_REF='refs/heads/main',GITHUB_WORKFLOW_REF=h.REPO+'/'+h.PATH+'@refs/heads/main',GITHUB_WORKFLOW_SHA='a'*40,GITHUB_SHA='a'*40,GITHUB_RUN_ID='42')
  self.event=dict(action='created',repository={'id':h.REPO_ID,'private':True},sender={'id':h.OWNER_ID},issue={'number':1},comment=copy.deepcopy(self.api.comment),installation={'id':500})
  self.now=h.timestamp('2026-11-05T00:00:02Z')
 def controller(self):return h.Controller(self.api,self.ctx,self.event,self.api.source,self.now)
 def test_ping_posts_pending_then_patches_same_native_receipt(self):
  value=self.controller().execute();self.assertEqual(value['status'],'PING_OK');self.assertEqual(value['run_id'],42);self.assertEqual(value['oracle_calls'],0)
  self.assertEqual([x[0] for x in self.api.calls if x[0]!='GET'],['POST','PATCH']);self.assertEqual(len(self.api.rows),1);self.assertIn('PING_OK',self.api.rows[0]['body'])
 def test_other_actor_and_non_native_context_have_no_api_writes(self):
  for key,value in [('GITHUB_ACTOR_ID','1'),('GITHUB_ACTIONS','false'),('GITHUB_REPOSITORY','other/repo'),('GITHUB_EVENT_NAME','pull_request')]:
   old=self.ctx[key];self.ctx[key]=value
   with self.assertRaises(h.Refused):self.controller().execute()
   self.ctx[key]=old
  self.assertEqual(self.api.calls,[])
 def test_private_repo_issue_and_pr_scope(self):
  for issue in [dict(number=2),dict(number=1,pull_request={})]:
   self.event['issue']=issue
   with self.assertRaises(h.Refused):self.controller().execute()
  self.assertEqual(self.api.calls,[])
 def test_arbitrary_commands_extra_fields_duplicate_keys_denied(self):
  for body in ['sh -c BAD','{"schema":"oci-ctrl/0.1","operation":"shell"}','{"schema":"oci-ctrl/0.1","operation":"ping","url":"PRIVATE"}','{"schema":"oci-ctrl/0.1","operation":"ping","operation":"ping"}']:
   self.api.comment['body']=body;self.event['comment']['body']=body
   with self.assertRaises(h.Refused):self.controller().verify_scope()
  self.assertFalse(any(x[0]!='GET' for x in self.api.calls))
 def test_missing_or_wrong_installation_is_refused(self):
  for installation in [{},{'id':501}]:
   self.event['installation']=installation
   with self.assertRaisesRegex(h.Refused,'INSTALLATION'):self.controller().verify_scope()
 def test_edited_future_expired_comment_refused(self):
  for time in ['2026-11-05T00:00:03Z','2026-11-04T23:00:00Z']:
   self.api.comment['created_at']=time;self.api.comment['updated_at']=time
   with self.assertRaises(h.Refused):self.controller().verify_scope()
  self.api.comment['created_at']='2026-11-05T00:00:00Z';self.api.comment['updated_at']='2026-11-05T00:00:01Z'
  with self.assertRaisesRegex(h.Refused,'EDITED'):self.controller().verify_scope()
 def test_canonical_actor_app_and_run_forgery_denied(self):
  self.api.comment['performed_via_github_app']['id']=401
  with self.assertRaises(h.Refused):self.controller().execute()
  self.assertFalse(any(x[0]!='GET' for x in self.api.calls))
 def test_controller_workflow_code_sha_drift_denied(self):
  self.api.policy['controller_sha256']='0'*64
  with self.assertRaisesRegex(h.Refused,'CONTROLLER_PIN'):self.controller().execute()
  self.api.policy['controller_sha256']=hashlib.sha256(self.api.source).hexdigest();self.api.policy['workflow_blob']='0'*40
  with self.assertRaisesRegex(h.Refused,'WORKFLOW_BLOB'):self.controller().execute()
 def test_native_run_binding_and_reruns_denied(self):
  for key,bad in [('event','push'),('run_attempt',2),('head_sha','b'*40),('status','completed')]:
   old=self.api.run[key];self.api.run[key]=bad
   with self.assertRaisesRegex(h.Refused,'CANONICAL_RUN'):self.controller().execute()
   self.api.run[key]=old
  self.ctx['GITHUB_RUN_ATTEMPT']='2'
  with self.assertRaisesRegex(h.Refused,'RERUN'):self.controller().execute()
 def test_replay_persists_in_bot_comment_across_controllers(self):
  self.controller().execute();before=len(self.api.calls);out=self.controller().execute();self.assertEqual(out['status'],'DUPLICATE_NO_ACTION');self.assertEqual(len(self.api.rows),1);self.assertFalse(any(x[0]!='GET' for x in self.api.calls[before:]))
 def test_copying_marker_as_owner_is_not_a_trusted_receipt(self):
  self.api.rows.append(dict(id=99,user={'id':h.OWNER_ID},performed_via_github_app={'id':400},body=h.MARKER+'800 --> FORGED'))
  self.assertEqual(self.controller().execute()['status'],'PING_OK')
 def test_unknown_post_outcome_never_retries_or_claims_success(self):
  self.api.failpost=True
  with self.assertRaises(h.Refused):self.controller().execute()
  self.assertEqual(len([x for x in self.api.calls if x[0]=='POST']),1);self.assertFalse(any(x[0]=='PATCH' for x in self.api.calls))
 def test_bad_receipt_author_cannot_become_success(self):
  self.api.badbot=True
  with self.assertRaisesRegex(h.Refused,'RECEIPT_OUTCOME'):self.controller().execute()
 def test_refusal_receipt_does_not_echo_private_command(self):
  self.api.comment['body']='PRIVATE_SECRET';self.event['comment']['body']='PRIVATE_SECRET'
  with self.assertRaises(h.Refused):self.controller().execute()
  self.assertNotIn('PRIVATE_SECRET',self.api.rows[-1]['body']);self.assertIn('REJECTED',self.api.rows[-1]['body'])
 def test_content_parser_checks_git_blob(self):
  api=h.API('SYNTHETIC_TEST_ONLY')
  with patch.object(api,'request',return_value=dict(type='file',encoding='base64',content=base64.b64encode(b'fake').decode(),sha='0'*40)):
   with self.assertRaises(h.Refused):api.content('ctrl1/release.json','a'*40)
 def test_workflow_is_derived_from_receiver_not_mutable_release_claim(self):
  self.api.workflow+=b'\n# DRIFT';self.api.policy['workflow_blob']=h.git_blob(self.api.workflow)
  with self.assertRaisesRegex(h.Refused,'WORKFLOW_BLOB'):self.controller().execute()
 def test_workflow_has_only_minimum_permissions_and_no_untrusted_interpolation(self):
  import yaml
  data=yaml.safe_load(h.render_workflow(self.api.source))
  self.assertEqual(data['on'],{'issue_comment':{'types':['created']}})
  self.assertEqual(data['permissions'],{'contents':'read','actions':'read','issues':'write'})
  self.assertNotIn('env',data['jobs']['ping']);self.assertEqual(data['jobs']['ping']['steps'][0]['env'],{'CTRL1_TOKEN':'${{ github.token }}'});self.assertFalse(data['concurrency']['cancel-in-progress']);self.assertEqual(data['jobs']['ping']['timeout-minutes'],2)
  text=h.render_workflow(self.api.source).decode()
  for forbidden in ['secrets.','uses:','pull_request_target','${{ github.event.comment','schedule:','workflow_dispatch:']:self.assertNotIn(forbidden,text)
 def test_fixed_source_bootstrap_is_python_and_not_shell_interpolated(self):
  import yaml
  script=yaml.safe_load(h.render_workflow(self.api.source))['jobs']['ping']['steps'][0]['run']
  code=script.split("python3 - <<'CTRL1_BOOTSTRAP'\n",1)[1].rsplit('CTRL1_BOOTSTRAP',1)[0];compile(code,'bootstrap','exec')
  self.assertIn(hashlib.sha256(self.api.source).hexdigest(),code);self.assertNotIn('event.comment.body',code)
if __name__=='__main__':unittest.main(verbosity=2)
