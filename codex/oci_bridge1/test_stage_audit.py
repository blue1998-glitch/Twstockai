import unittest,tempfile,os,json,hashlib
from pathlib import Path
from .stage_audit import audit,FILES
from .bridge import Refused
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=os.environ['STAGE_TEST_ROOT']);self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  for name in FILES:(self.root/name).write_text('SYNTHETIC_SOURCE')
  policy=dict(schema='oci-private-staging/0.1',repository='blue1998-glitch/Twstockai-oci-bridge-private',repository_id=1446437252,actor_id=319797247,app_id=1144995,installation_id=500,issue_number=1,workflow_sha=None,workflow_ref='UNDEPLOYED',billing_status='UNVERIFIED',execution_state='STAGED_NOT_ENABLED',pilot_configured=False)
  (self.root/'control-policy.json').write_text(json.dumps(policy));self.pin=self.manifest()
 def manifest(self):
  rows=[]
  for name in sorted(FILES):
   raw=(self.root/name).read_bytes();rows.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
  raw=json.dumps(dict(schema='oci-private-review/0.1',files=rows)).encode();(self.root/'MANIFEST.json').write_bytes(raw);return hashlib.sha256(raw).hexdigest()
 def test_good_artifact_stays_disconnected(self):self.assertEqual(audit(self.root,self.pin)['oracle_queries'],0)
 def test_unpinned_manifest_refused(self):
  with self.assertRaises(Refused):audit(self.root,'0'*64)
 def test_tampered_source_refused(self):
  (self.root/'bridge.py').write_text('CHANGED')
  with self.assertRaises(Refused):audit(self.root,self.pin)
 def test_unsafe_or_duplicate_paths_refused(self):
  raw=json.dumps(dict(schema='oci-private-review/0.1',files=[dict(path='../outside')]*5)).encode();(self.root/'MANIFEST.json').write_bytes(raw)
  with self.assertRaises(Refused):audit(self.root,hashlib.sha256(raw).hexdigest())
 def test_staging_cannot_approve_billing_or_activate(self):
  file=self.root/'control-policy.json';value=json.loads(file.read_text());value['billing_status']='VERIFIED';file.write_text(json.dumps(value));pin=self.manifest()
  with self.assertRaises(Refused):audit(self.root,pin)
 def test_symlink_refused(self):
  file=self.root/'bridge.py';file.unlink();file.symlink_to(self.root/'receiver.py')
  with self.assertRaises(Refused):audit(self.root,self.pin)
if __name__=='__main__':unittest.main(verbosity=2)
