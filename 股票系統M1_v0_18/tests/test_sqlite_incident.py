"""A diagnostic must retain a failed database, not silently repair it."""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reliability'))
from sqlite_probe import files, probe


class IncidentProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'a #中文?.sqlite3'

    def test_missing_database_not_created(self):
        result = probe(self.path)
        self.assertEqual(result['observation']['status'], 'READ_FAILED')
        self.assertTrue(result['observed_files_unchanged'])
        self.assertFalse(self.path.exists())

    def test_normal_database_unchanged_and_not_claimed_store_valid(self):
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE sample(value)')
        result = probe(self.path)
        self.assertEqual(result['observation']['status'], 'READABLE')
        self.assertEqual(result['observation']['application_id'], 0)
        self.assertTrue(result['observed_files_unchanged'])
        self.assertEqual(result['root_cause'], 'NOT_ESTABLISHED')

    def test_corrupt_database_retained_with_extended_error(self):
        self.path.write_bytes(b'invalid sqlite file' * 100)
        before = files(self.path)
        result = probe(self.path)
        self.assertEqual(result['observation']['sqlite_errorname'], 'SQLITE_NOTADB')
        self.assertEqual(files(self.path), before)

    def test_hot_journal_is_preserved_without_recovery(self):
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE sample(value)')
            db.execute('INSERT INTO sample VALUES(42)')
        child = subprocess.run([sys.executable, '-c',
            "import sqlite3,sys,os;c=sqlite3.connect(sys.argv[1]);c.execute('PRAGMA cache_size=8');c.execute('BEGIN IMMEDIATE');c.execute('INSERT INTO sample VALUES(?)',('x'*2000000,));os._exit(17)",
            str(self.path)], capture_output=True, timeout=20)
        self.assertEqual(child.returncode, 17)
        before = files(self.path)
        result = probe(self.path)
        self.assertEqual(result['observation']['sqlite_errorname'], 'SQLITE_READONLY_ROLLBACK')
        self.assertEqual(result['observation']['sqlite_errorcode'], 776)
        self.assertEqual(files(self.path), before)
        self.assertGreater(result['after']['-journal']['bytes'], 512)

    def test_cli_fresh_process_without_numeric_engines(self):
        runner = """import importlib.abc,runpy,sys
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in ('analysis_jobs','analysis_workflow','structure','moving_averages','period_ma','period_jobs','analysis_store'):
   raise RuntimeError('Forbidden import: '+fullname)
sys.meta_path.insert(0,Block());sys.argv=[sys.argv[1],'--db',sys.argv[2]];runpy.run_path(sys.argv[0],run_name='__main__')
"""
        p = subprocess.run([sys.executable, '-c', runner,
                            str(ROOT / 'reliability/sqlite_probe.py'), str(self.path)],
                           capture_output=True, text=True, timeout=20)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertEqual(json.loads(p.stdout)['access'], 'READ_ONLY_NO_RECOVERY')
        self.assertFalse(self.path.exists())

    def test_clean_wal_header_refused_without_creating_sidecars(self):
        db = sqlite3.connect(self.path)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE sample(value)')
        db.close()
        self.assertFalse(Path(str(self.path) + '-wal').exists())
        before = files(self.path)
        result = probe(self.path)
        self.assertEqual(result['observation']['status'], 'READ_REFUSED_WAL')
        self.assertEqual(files(self.path), before)
        self.assertTrue(result['observed_files_unchanged'])

    def test_wal_with_existing_sidecars_refused_without_changing_them(self):
        db = sqlite3.connect(self.path)
        self.addCleanup(db.close)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE sample(value)')
        db.commit()
        self.assertTrue(Path(str(self.path) + '-wal').exists())
        before = files(self.path)
        result = probe(self.path)
        self.assertEqual(result['observation']['status'], 'READ_REFUSED_WAL')
        self.assertEqual(files(self.path), before)
        self.assertTrue(result['observed_files_unchanged'])
