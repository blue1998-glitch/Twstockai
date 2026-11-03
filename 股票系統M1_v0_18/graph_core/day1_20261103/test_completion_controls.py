"""Four new synthetic lifecycle/measurement controls; no real provider/core."""
import os,tempfile,unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
from graph_core.day1_20261103.resume_once import resume
from graph_core.day1_20261103.apply_once import allocated


class CompletionControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.work=self.root/'work';self.work.mkdir()

    def test_live_process_refuses_resume_without_creating_marker(self):
        with self.assertRaisesRegex(ValueError,'PREVIOUS_WRITER_NOT_PROVEN_STOPPED'):
            resume(self.root,self.work,os.getpid())
        self.assertEqual(list(self.work.iterdir()),[])

    def test_existing_resume_marker_refuses_before_any_source_read(self):
        marker=self.work/'resume-started.json';marker.write_bytes(b'SYNTHETIC_PRIOR_ATTEMPT')
        with patch('graph_core.day1_20261103.resume_once.inc.sources',side_effect=AssertionError('No source read permitted')):
            with self.assertRaisesRegex(ValueError,'NO_AUTOMATIC_REPEATED_RESUME'):
                resume(self.root,self.work,2147483647)
        self.assertEqual(marker.read_bytes(),b'SYNTHETIC_PRIOR_ATTEMPT')

    def test_existing_directory_blocks_are_not_new_file_allocation(self):
        for n in range(128):(self.work/('synthetic-old-file-%04d'%n)).write_bytes(b'')
        baseline={(p.stat().st_dev,p.stat().st_ino) for p in self.root.rglob('*') if p.is_file()}
        # A nonzero existing-directory allocation is explicit synthetic FS input;
        # this Cloud's temporary directory may report zero blocks.
        original_lstat=Path.lstat
        def nonzero_directory(path):
            value=original_lstat(path)
            if path.is_dir():return SimpleNamespace(st_dev=value.st_dev,st_ino=value.st_ino,st_mode=value.st_mode,st_blocks=8)
            return value
        with patch.object(Path,'lstat',nonzero_directory):
            self.assertEqual(allocated(self.root,baseline),0)

    def test_new_hardlinks_count_once_and_existing_alias_adds_no_payload(self):
        old=self.work/'old';old.write_bytes(b'SYNTHETIC_OLD')
        baseline={(p.stat().st_dev,p.stat().st_ino) for p in [self.root,self.work,old]}
        os.link(old,self.work/'old-alias')
        new=self.work/'new';new.write_bytes(b'SYNTHETIC_NEW')
        os.link(new,self.work/'new-alias')
        self.assertEqual(allocated(self.root,baseline),new.stat().st_blocks*512)


if __name__=='__main__':unittest.main()
