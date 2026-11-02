"""Synthetic governance gates only; no market/core/source tests."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from codex import unified_workspace as g
from rotation_research.private_portability import encode,digest,VERSION

class UnifiedWorkspaceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);base=Path(self.temp.name);self.root=base/'synthetic-fm3';self.root.mkdir();(self.root/'fm3-continuation.json').write_text('{}');self.lock=base/'engineering.lock';self.lock.touch();self.manifest=base/'private-manifest.json'
  path=self.root/'fm3-continuation.json';st=path.stat();entry=dict(path=path.name,bytes=st.st_size,mtime_ns=st.st_mtime_ns,source_inode=st.st_ino,source_device=st.st_dev,sha256=digest(path.read_bytes()),hardlink_group='h1')
  # Synthetic saved audit receipt tests the metadata gate, not FM3 semantics.
  report=dict(schema=VERSION,status='PREFLIGHT_COMPLETE',observed_root=str(self.root),journal_references_verified=True,preview_capture_edges=[],issues=[],files=[entry]);report['manifest_id']=digest(encode(report));self.manifest.write_bytes(encode(report))
  self.policy=dict(environment_id='SYNTHETIC_CLOUD_A',repository_root='/synthetic/repo',branch='dev/research',fm3_root=str(self.root),private_manifest=str(self.manifest),private_manifest_id=report['manifest_id'],engineering_lock=str(self.lock))
  self.state=dict(root='/synthetic/repo',branch='dev/research',head='a'*40,remote='a'*40)
 def call(self,env='SYNTHETIC_CLOUD_A'):return g.check(self.policy,env,git_state=self.state)
 def test_same_cloud_receipt_and_idle_locks_pass_without_data_hash(self):
  r=self.call();self.assertEqual(r['status'],'READY_FOR_AUTHORIZED_TASK',r);self.assertFalse(r['data_sha_repeated']);self.assertEqual(r['fm3']['unchanged_metadata_paths'],1)
 def test_same_path_different_cloud_blocks_before_source_reads(self):
  self.policy['private_manifest']='/unreadable/path';r=self.call('SYNTHETIC_CLOUD_B');self.assertEqual(r['issues'],['WRONG_CLOUD_DO_NOT_WRITE'])
 def test_wrong_branch_or_advanced_remote_refused(self):
  self.state['branch']='main';self.assertEqual(self.call()['status'],'BLOCKED');self.state['branch']='dev/research';self.state['remote']='b'*40;self.assertIn('REFS_DIFFER_READ_LATEST_HANDOFF_BEFORE_WRITE',self.call()['issues'])
 def test_missing_source_is_local_unavailable_not_global_loss(self):
  self.policy['fm3_root']=str(self.root.parent/'missing');r=self.call();self.assertIn('FM3_UNAVAILABLE_HERE_NOT_PROOF_OF_GLOBAL_LOSS',r['issues']);self.assertFalse(Path(self.policy['fm3_root']).exists())
 def test_changed_metadata_or_tampered_receipt_refused(self):
  path=self.root/'fm3-continuation.json';path.write_text('changed');self.assertEqual(self.call()['status'],'BLOCKED');self.manifest.write_text('{}');self.assertEqual(self.call()['status'],'BLOCKED')
 def test_single_writer_lease_blocks_other_process_and_releases(self):
  code='import fcntl,sys;f=open(sys.argv[1],"rb");fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)'
  with g.engineering_lease(self.lock):
   self.assertIn('ENGINEERING_WRITER_BUSY_DO_NOT_START_SECOND_WRITER',self.call()['issues'])
   r=subprocess.run([sys.executable,'-c',code,str(self.lock)],capture_output=True);self.assertNotEqual(r.returncode,0);self.assertIn(b'BlockingIOError',r.stderr)
  self.assertEqual(self.call()['status'],'READY_FOR_AUTHORIZED_TASK')
 def test_existing_source_writer_lock_blocks_and_is_preserved(self):
  p=self.root/'fm3-writer.lock';p.write_text('SYNTHETIC');self.assertEqual(self.call()['status'],'BLOCKED');self.assertEqual(p.read_text(),'SYNTHETIC')

if __name__=='__main__':unittest.main()
