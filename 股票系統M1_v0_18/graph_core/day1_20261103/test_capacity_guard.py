"""Four new synthetic reserve controls; no source calls or market analysis."""
import tempfile,unittest
from pathlib import Path
from rotation_research import artifact_codec as c
from rotation_research.store import Journal
from graph_core.day1_20261103.capacity_guard import guarded_writes,MINIMUM

class GuardTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
 def test_codec_piece_refused_before_creation_and_existing_bytes_untouched(self):
  old=self.root/'old';c.immutable(old,b'SYNTHETIC')
  with guarded_writes(self.root,space=lambda:MINIMUM+1):
   c.immutable(old,b'SYNTHETIC')
   with self.assertRaises(OSError):c.immutable(self.root/'new',b'NEW')
  self.assertEqual(old.read_bytes(),b'SYNTHETIC');self.assertFalse((self.root/'new').exists())
 def test_plain_journal_metadata_refused_without_new_directory(self):
  with guarded_writes(self.root,space=lambda:MINIMUM+1),self.assertRaises(OSError):Journal(self.root/'new-journal').save('id',dict(synthetic=True))
  self.assertFalse((self.root/'new-journal').exists())
 def test_pending_head_refused_and_old_head_retained(self):
  old=self.root/'current-increment-run.json';old.write_bytes(b'SYNTHETIC_OLD_HEAD')
  with guarded_writes(self.root,space=lambda:MINIMUM+1),self.assertRaises(OSError):(self.root/'current-increment.pending').open('wb')
  self.assertEqual(old.read_bytes(),b'SYNTHETIC_OLD_HEAD');self.assertFalse((self.root/'current-increment.pending').exists())
 def test_sufficient_capacity_exact_bytes_and_no_lower_reserve(self):
  with guarded_writes(self.root,space=lambda:MINIMUM+1024*1024):
   c.immutable(self.root/'new',b'SYNTHETIC_EXACT');Journal(self.root/'runs').save('id',dict(synthetic=True))
  self.assertEqual((self.root/'new').read_bytes(),b'SYNTHETIC_EXACT');self.assertEqual(Journal(self.root/'runs').read('id')['value'],dict(synthetic=True))
  with self.assertRaises(ValueError):
   with guarded_writes(self.root,minimum_free=1):pass
if __name__=='__main__':unittest.main()
