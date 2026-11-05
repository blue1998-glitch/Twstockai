import unittest,tempfile,os,json,hmac,hashlib
from pathlib import Path
from types import SimpleNamespace as NS
from . import bridge as b
class SDK:
 def __init__(self):self.calls=[];self.fail=False;self.pages=False
 def _call(self,kind,kw):
  self.calls.append((kind,kw))
  if self.fail:raise RuntimeError("PRIVATE_SECRET_ocid1_NOT_FOR_OUTPUT")
  return NS(data=[NS(id="ocid1.PRIVATE",display_name="PERSONAL_NAME",ip="PRIVATE_IP",lifecycle_state="RUNNING" if kind=="compute" else "AVAILABLE")],headers={"opc-next-page":"cycle"} if self.pages else {})
 def list_instances(self,**kw):return self._call("compute",kw)
 def list_volumes(self,**kw):return self._call("block",kw)
 def list_boot_volumes(self,**kw):return self._call("boot",kw)
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(dir=os.environ['BRIDGE_TEST_ROOT']);self.addCleanup(self.t.cleanup);os.chmod(self.t.name,0o700)
  self.key=b"SYNTHETIC_TEST_ONLY_NOT_A_DEPLOYED_KEY";self.trust=b.Trust(100,200,frozenset({300}),"a"*40)
  self.msg=dict(version=b.VERSION,operation="list_pilot_compartment_resources",request_id="1"*32,issued_at=1000,expires_at=1100,repository_id=100,installation_id=200,actor_id=300,private_repository=True,commit="a"*40,branch=self.trust.branch,event="verified_issue_command")
  self.sdk=SDK();self.adapter=b.OCIReadAdapter(self.sdk,self.sdk,"ocid1.compartment.SYNTHETIC",["SYNTHETIC_AD"])
  self.replay=b.ReplayStore(Path(self.t.name)/"nonce.log");self.bridge=b.Bridge(self.trust,self.key,self.replay,self.adapter)
 def send(self,**changes):
  message={**self.msg,**changes};raw=b.encode(message);sig=hmac.new(self.key,raw,hashlib.sha256).hexdigest();return self.bridge.receive(raw,sig,1001)
 def test_disconnected_no_real_call(self):
  self.assertEqual(b.Bridge().receive(b"", "",1001),dict(status="NOT_CONNECTED",oracle_query_executed=False));self.assertEqual(self.sdk.calls,[])
 def test_local_full_protocol_aggregate_and_no_private_output(self):
  out=self.send();self.assertEqual(out['result']['status'],'KNOWN');self.assertEqual(out['result']['resources']['compute']['count'],1)
  for word in ['ocid1','PERSONAL_NAME','PRIVATE_IP','actor_id','repository_id']:self.assertNotIn(word,json.dumps(out))
  self.assertEqual(len(self.sdk.calls),3)
 def test_account_plan_unknown_not_user_claim_as_api(self):
  self.assertEqual(self.send(operation='get_account_plan_kind')['result']['status'],'UNKNOWN');self.assertEqual(self.sdk.calls,[])
 def test_arbitrary_operation_url_shell_and_extra_field_denied(self):
  for changes in [dict(operation='create_instance'),dict(operation='https://example.test'),dict(operation='sh -c anything'),dict(compartment_id='other'),dict(url='https://example.test')]:
   with self.assertRaises(b.Refused):self.send(**changes)
  self.assertEqual(self.sdk.calls,[])
 def test_actor_repo_private_installation_checks(self):
  for changes in [dict(actor_id=301),dict(repository_id=101),dict(installation_id=201),dict(private_repository=False),dict(actor_id=True)]:
   with self.assertRaises(b.Refused):self.send(**changes)
  self.assertEqual(self.sdk.calls,[])
 def test_event_commit_and_branch_pinning(self):
  for changes in [dict(commit='b'*40),dict(branch='main'),dict(event='pull_request'),dict(version='future')]:
   with self.assertRaises(b.Refused):self.send(**changes)
 def test_signature_rejection_before_io(self):
  with self.assertRaises(b.Refused):self.bridge.receive(b.encode(self.msg),'0'*64,1001)
  self.assertEqual(self.sdk.calls,[])
 def test_duplicate_keys_and_input_bound(self):
  for raw in [b'{"x":1,"x":2}',b'a'*4097]:
   with self.assertRaises(b.Refused):self.bridge.receive(raw,hmac.new(self.key,raw,hashlib.sha256).hexdigest(),1001)
 def test_expiry_and_future_prefix(self):
  for changes in [dict(expires_at=1001),dict(issued_at=1002),dict(expires_at=1400)]:
   with self.assertRaises(b.Refused):self.send(**changes)
 def test_replay_persists_across_handler_instances(self):
  self.send();self.bridge=b.Bridge(self.trust,self.key,b.ReplayStore(self.replay.path),self.adapter)
  with self.assertRaisesRegex(b.Refused,'REPLAY'):self.send()
  self.assertEqual(len(self.sdk.calls),3)
 def test_failure_is_unknown_not_zero_or_exception_leak(self):
  self.sdk.fail=True;out=self.send();self.assertEqual(out['result']['status'],'PARTIAL');self.assertIsNone(out['result']['resources']['boot']['count']);self.assertNotIn('SECRET',json.dumps(out))
 def test_pagination_cycle_bounded_unknown(self):
  self.sdk.pages=True;out=self.send();self.assertEqual(out['result']['status'],'PARTIAL');self.assertLessEqual(len(self.sdk.calls),6)
 def test_output_extra_fields_removed_and_bad_semantics_rejected(self):
  value=self.adapter.read('list_pilot_compartment_resources');value['secret']='PRIVATE';value['resources']['compute']['secret']='PRIVATE';self.assertNotIn('PRIVATE',json.dumps(b.sanitize(value)))
  value['resources']['compute']['count']=True
  with self.assertRaises(b.Refused):b.sanitize(value)
 def test_replay_corruption_and_private_permissions(self):
  self.replay.path.write_bytes(b'bad-partial')
  with self.assertRaises(b.Refused):self.send()
  self.assertEqual(self.sdk.calls,[])
 def test_global_query_budget_and_no_partial_count_claim(self):
  self.adapter.remaining=0
  with self.assertRaises(b.Refused):self.adapter._list(self.sdk.list_instances,{})
  self.assertEqual(self.sdk.calls,[])
 def test_excessive_resource_output_not_truncated_into_known(self):
  self.sdk.list_instances=lambda **kw:NS(data=[NS(lifecycle_state='RUNNING')]*501,headers={})
  out=self.send();self.assertEqual(out['result']['resources']['compute']['status'],'UNKNOWN');self.assertIsNone(out['result']['resources']['compute']['count'])
if __name__=='__main__':unittest.main(verbosity=2)
