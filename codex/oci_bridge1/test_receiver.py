import unittest,json,copy
from unittest.mock import patch
from . import receiver as r
from .bridge import Refused
class Rest:
 def __init__(self,event):self.e=event;self.rows=[];self.role='write'
 def repository(self):return dict(id=100,full_name='SYNTHETIC/private',private=True)
 def comment(self,ident):return self.e['comment']
 def permission(self,actor):return self.role
 def checks(self,sha):return self.rows
 def start_check(self,sha,ident):
  row=dict(id=len(self.rows)+1,external_id=ident);self.rows.append(row);return row
class Tests(unittest.TestCase):
 def setUp(self):
  self.p=r.Policy('SYNTHETIC/private',100,300,400,500,1,'a'*40,'SYNTHETIC/private/.github/workflows/read.yml@refs/heads/main')
  self.event=dict(action='created',installation={'id':500},repository={'id':100},sender={'id':300},issue={'number':1},comment=dict(id=600,user={'id':300},performed_via_github_app={'id':400},body='{"schema":"oci-read/0.1","operation":"list_pilot_compartment_resources"}',issue_url='https://api.github.com/repos/SYNTHETIC/private/issues/1',created_at='2026-11-05T00:00:00Z',updated_at='2026-11-05T00:00:00Z'))
  self.claims=dict(event_name='issue_comment',repository_id='100',repository_visibility='private',actor_id='300',workflow_sha='a'*40,workflow_ref=self.p.workflow_ref);self.now=1793836801
  import datetime;self.now=datetime.datetime(2026,11,5,tzinfo=datetime.timezone.utc).timestamp()+1
  self.rest=Rest(copy.deepcopy(self.event));self.factory_calls=0
 def validate(self):return r.validate(self.event,self.claims,self.p,self.rest,self.now)
 def test_native_event_and_rest_binding(self):
  ident,op=self.validate();self.assertEqual(len(ident),32);self.assertEqual(op,'list_pilot_compartment_resources')
 def test_oidc_required_and_not_oci_token_exchange(self):
  with self.assertRaises(Refused):r.verify_oidc('SYNTHETIC_INVALID_TOKEN')
 def test_private_actor_commit_job_and_event_checks(self):
  for key,bad in [('repository_id','101'),('repository_visibility','public'),('actor_id','301'),('workflow_sha','b'*40),('event_name','pull_request')]:
   old=self.claims[key];self.claims[key]=bad
   with self.assertRaises(Refused):self.validate()
   self.claims[key]=old
 def test_missing_or_wrong_installation_refused(self):
  self.event['installation']={}
  with self.assertRaises(Refused):self.validate()
 def test_canonical_app_sender_and_permissions(self):
  self.rest.e['comment']['performed_via_github_app']=None
  with self.assertRaises(Refused):self.validate()
  self.rest.e=copy.deepcopy(self.event);self.rest.role='read'
  with self.assertRaises(Refused):self.validate()
 def test_comment_edited_expired_or_wrong_issue(self):
  self.rest.e['comment']['updated_at']='2026-11-05T00:00:01Z'
  with self.assertRaises(Refused):self.validate()
  self.rest.e=copy.deepcopy(self.event);self.now+=600
  with self.assertRaises(Refused):self.validate()
 def test_no_arbitrary_shell_url_or_compartment(self):
  for body in ['sh -c anything','{"schema":"oci-read/0.1","operation":"create"}','{"schema":"oci-read/0.1","operation":"get_account_plan_kind","compartment":"PRIVATE"}']:
   self.event['comment']['body']=body;self.rest.e=copy.deepcopy(self.event)
   with self.assertRaises(Refused):self.validate()
 def test_no_zero_paid_proof_no_factory_or_persistent_write(self):
  def factory():raise AssertionError('must not touch secrets')
  receiver=r.Receiver(self.p,self.rest,r.PersistentChecks(self.rest,'a'*40),factory)
  with patch.object(r,'verify_oidc',return_value=self.claims):out=receiver.receive(self.event,'SYNTHETIC',self.now)
  self.assertEqual(out['status'],'NOT_CONNECTED');self.assertEqual(self.rest.rows,[])
 def test_cross_run_persistent_check_prevents_retry(self):
  ident,_=self.validate();r.PersistentChecks(self.rest,'a'*40).consume(ident)
  with self.assertRaises(Refused):r.PersistentChecks(self.rest,'a'*40).consume(ident)
  self.assertEqual(len(self.rest.rows),1)
 def test_safe_response_never_leaks_exception(self):
  receiver=r.Receiver(self.p,self.rest,None,None)
  with patch.object(r,'verify_oidc',side_effect=RuntimeError('PRIVATE_SECRET')):out=receiver.receive_safe(self.event,'SYNTHETIC',self.now)
  self.assertNotIn('PRIVATE',json.dumps(out));self.assertEqual(out['status'],'NOT_CONNECTED')
 def test_rest_repository_and_permission_binding(self):
  with self.assertRaises(Refused):r.GitHubRest('https://evil.test','SYNTHETIC')
  api=r.GitHubRest('SYNTHETIC/private','SYNTHETIC');api.actor={'id':300,'login':'owner'}
  with patch.object(api,'_request',return_value={'user':{'id':301},'permission':'admin'}):
   with self.assertRaises(Refused):api.permission(300)
 def test_rest_check_history_does_not_truncate(self):
  api=r.GitHubRest('SYNTHETIC/private','SYNTHETIC')
  with patch.object(api,'_request',return_value={'total_count':1,'check_runs':[]}):
   with self.assertRaises(Refused):api.checks('a'*40)
 def test_rest_receipt_only_uses_projected_fields(self):
  api=r.GitHubRest('SYNTHETIC/private','SYNTHETIC')
  safe={'result':dict(status='UNKNOWN',reason='NO_SUPPORTED_ACCOUNT_PLAN_API',plan_kind=None,resources={},secret='PRIVATE')}
  with patch.object(api,'_request',return_value={}) as post:api.finish_check(1,safe)
  self.assertNotIn('PRIVATE',json.dumps(post.call_args.args))
if __name__=='__main__':unittest.main(verbosity=2)
