import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from contracts import DataError
from reviews import append_review,read_journal,review_status


QUEUE=[dict(target_key='test-target',run_id='test-run',subject_id='test-subject')]


class ReviewTests(unittest.TestCase):
    def test_append_revision_retains_old_record(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.jsonl'
            a=append_review(p,QUEUE,target_key='test-target',decision='UNSURE',reason='Synthetic test fixture',reviewer='TEST_FIXTURE')
            before=p.read_text()
            append_review(p,QUEUE,target_key='test-target',decision='REJECT',reason='Revised synthetic test fixture',reviewer='TEST_FIXTURE',supersedes_id=a['review_id'])
            self.assertTrue(p.read_text().startswith(before));self.assertEqual(len(read_journal(p)),2)

    def test_conflict_and_unknown_target_do_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.jsonl';a=append_review(p,QUEUE,target_key='test-target',decision='ACCEPT',reason='Synthetic fixture',reviewer='TEST_FIXTURE');before=p.read_bytes()
            for target,revision in [('test-target',None),('unknown',a['review_id'])]:
                with self.assertRaises(DataError):append_review(p,QUEUE,target_key=target,decision='REJECT',reason='Synthetic fixture',reviewer='TEST_FIXTURE',supersedes_id=revision)
                self.assertEqual(p.read_bytes(),before)

    def test_reason_required_and_no_fake_accuracy(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(DataError):append_review(Path(d)/'r',QUEUE,target_key='test-target',decision='ACCEPT',reason='',reviewer='TEST_FIXTURE')
        r=review_status(QUEUE,[]);self.assertEqual(r['unreviewed'],1);self.assertEqual(r['classification_accuracy'],'NOT_ESTIMABLE')

    def test_corrupt_journal_is_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.jsonl';p.write_text('not json\n')
            with self.assertRaises(DataError):read_journal(p)

    def test_writer_lock_prevents_interleaving(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.jsonl';lock=Path(str(p)+'.lock');lock.touch()
            with self.assertRaises(DataError):append_review(p,QUEUE,target_key='test-target',decision='ACCEPT',reason='Synthetic fixture',reviewer='TEST_FIXTURE')
            self.assertFalse(p.exists());self.assertTrue(lock.exists())


if __name__=='__main__':unittest.main()
