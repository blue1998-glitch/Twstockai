import unittest,copy,json
from . import handler as h
from .test_handler import Fake
class Tests(unittest.TestCase):
 def setUp(self):
  self.api=Fake();self.ctx=dict(GITHUB_ACTIONS='true',GITHUB_EVENT_NAME='issue_comment',GITHUB_REPOSITORY=h.REPO,GITHUB_REPOSITORY_ID=str(h.REPO_ID),GITHUB_ACTOR_ID=str(h.OWNER_ID),GITHUB_RUN_ATTEMPT='1',GITHUB_REF='refs/heads/main',GITHUB_WORKFLOW_REF=h.REPO+'/'+h.PATH+'@refs/heads/main',GITHUB_WORKFLOW_SHA='a'*40,GITHUB_SHA='a'*40,GITHUB_RUN_ID='42')
  self.event=dict(action='created',repository={'id':h.REPO_ID,'private':True},sender={'id':h.OWNER_ID},issue={'number':1},comment=copy.deepcopy(self.api.comment))
  self.now=h.timestamp('2026-11-05T00:00:02Z')
 def controller(self):return h.Controller(self.api,self.ctx,self.event,self.api.source,self.now)
 def test_missing_webhook_installation_allows_only_verified_ping_profile(self):
  before=copy.deepcopy(self.event);out=self.controller().execute();self.assertEqual(out['status'],'PING_OK');self.assertEqual(out['installation_attestation'],'NOT_ATTESTED');self.assertEqual(out['trust_profile'],h.TRUST_PROFILE);self.assertEqual(out['oracle_calls'],0);self.assertEqual(self.event,before);self.assertNotIn('installation_id',json.dumps(out));self.assertNotIn('installation_id',self.api.policy)
 def test_injected_installation_is_neither_read_nor_claimed_as_proof(self):
  self.event['installation']={'id':'SYNTHETIC_FORGED_INSTALLATION'}
  out=self.controller().execute();self.assertEqual(out['installation_attestation'],'NOT_ATTESTED');self.assertNotIn('SYNTHETIC_FORGED',json.dumps(out))
 def test_canonical_owner_app_permission_and_private_scope_still_required(self):
  for kind in ['owner','app','permission','private']:
   self.setUp()
   if kind=='owner':self.api.comment['user']['id']=1
   elif kind=='app':self.api.comment['performed_via_github_app']['id']=401
   elif kind=='permission':
    original=self.api.request
    self.api.request=lambda method,path,data=None:dict(user={'id':h.OWNER_ID},permission='read') if path=='/collaborators/blue1998-glitch/permission' else original(method,path,data)
   else:self.event['repository']['private']=False
   with self.assertRaises(h.Refused):self.controller().verify_scope()
   self.assertFalse(any(x[0]!='GET' for x in self.api.calls))
 def test_replacement_native_run_and_workflow_fields_missing_fail_closed(self):
  for field in ['triggering_actor','head_repository','workflow_id']:
   self.setUp();self.api.run.pop(field)
   with self.assertRaises(h.Refused):self.controller().verify_scope()
  self.setUp();original=self.api.request
  self.api.request=lambda method,path,data=None:dict(id=999,path=h.PATH,state='active') if path=='/actions/workflows/43' else original(method,path,data)
  with self.assertRaises(h.Refused):self.controller().verify_scope()
 def test_installation_claim_or_other_operation_cannot_escalate_profile(self):
  for request in [dict(schema=h.SCHEMA,operation='list_pilot_compartment_resources'),dict(schema=h.SCHEMA,operation='get_account_plan_kind'),dict(schema=h.SCHEMA,operation='shell'),dict(schema=h.SCHEMA,operation='ping',installation_id=500)]:
   self.setUp();body=json.dumps(request);self.api.comment['body']=body;self.event['comment']['body']=body
   with self.assertRaises(h.Refused):self.controller().verify_scope()
  self.setUp();self.api.policy['installation_attestation']='VERIFIED'
  with self.assertRaises(h.Refused):self.controller().verify_scope()
 def test_code_pin_and_time_window_are_not_bypassed(self):
  self.api.policy['controller_sha256']='0'*64
  with self.assertRaises(h.Refused):self.controller().verify_scope()
  self.setUp();self.now+=301
  with self.assertRaises(h.Refused):self.controller().verify_scope()
 def test_prior_rejected_v01_receipt_is_still_consumed_nonce(self):
  self.api.rows.append(dict(id=900,user={'id':600},performed_via_github_app={'id':700},body=h.MARKER+'800 -->\n{"controller_version":"M-OCI-CTRL1/0.1","status":"REJECTED"}'))
  out=self.controller().execute();self.assertEqual(out['status'],'DUPLICATE_NO_ACTION');self.assertFalse(any(x[0]!='GET' for x in self.api.calls))
 def test_no_schema_relaxation_or_missing_profile_acceptance(self):
  self.api.policy.pop('trust_profile')
  with self.assertRaises(h.Refused):self.controller().verify_scope()
  self.setUp();self.event['sender']['id']=1
  with self.assertRaises(h.Refused):self.controller().verify_scope()
if __name__=='__main__':unittest.main(verbosity=2)
