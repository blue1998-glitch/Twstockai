"""Read-only export behavior, actual failed writers and safe file boundaries."""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from analysis_store import AnalysisStore
from contracts import DataError
from saved_viewer import export_saved, render_html, write_html
from test_analysis_store import fixture


def embedded(html):
    return json.loads(re.search(r'<script id="saved-data" type="application/json">(.*?)</script>', html, re.S).group(1))


class SavedViewerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.q, cls.r, cls.e = fixture()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.db = self.root/'source.sqlite3'
        self.store = AnalysisStore.create(self.db)
        self.receipt = self.store.save(self.q, self.r, self.e, reason='saved viewer fixture')

    def test_exact_bundles_and_no_writes_or_recovery(self):
        before = self.db.read_bytes(); expected = self.store.load(self.receipt['record_id'])
        with patch.object(AnalysisStore, 'save', side_effect=AssertionError('save called')), patch.object(AnalysisStore, 'recover', side_effect=AssertionError('recover called')), patch.object(AnalysisStore, 'create', side_effect=AssertionError('create called')):
            payload = export_saved(self.db)
        self.assertEqual(payload['records'], [expected]); self.assertEqual(before, self.db.read_bytes())
        self.assertEqual(payload['classification_quality'], 'NOT_VALIDATED')

    def test_export_runs_with_engine_and_workflow_imports_blocked(self):
        script = """import sys,importlib.abc
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname in ['structure','moving_averages','analysis_jobs','jobs','analysis_workflow']:raise AssertionError('Engine import '+fullname)
sys.meta_path.insert(0,Block())
sys.path.insert(0,sys.argv[1])
from saved_viewer import export_saved
assert len(export_saved(sys.argv[2])['records'])==1
"""
        p = subprocess.run([sys.executable, '-c', script, str(ROOT/'src'), str(self.db)], capture_output=True, text=True, timeout=15)
        self.assertEqual(p.returncode, 0, p.stdout+p.stderr)

    def test_explicit_versions_and_evidence_are_not_merged(self):
        e = deepcopy(self.e); e['records'].append({'status':'UNVERIFIED', 'revision':'display test'})
        second = self.store.save(self.q, self.r, e, reason='second evidence')
        p = export_saved(self.db, [second['record_id'], self.receipt['record_id']])
        self.assertEqual([b['record_id'] for b in p['records']], [second['record_id'], self.receipt['record_id']])
        self.assertNotEqual(p['records'][0]['evidence'], p['records'][1]['evidence'])

    def test_exact_missing_duplicate_and_empty_selection_rejected(self):
        for ids in [[], ['missing'], [self.receipt['record_id']]*2, 'latest', [42]]:
            with self.assertRaises(DataError): export_saved(self.db, ids)

    def test_empty_store_is_exportable(self):
        other = self.root/'empty.db'; AnalysisStore.create(other)
        self.assertEqual(export_saved(other)['records'], [])

    def test_missing_bad_and_unknown_database_remain_unchanged(self):
        missing = self.root/'absent.db'
        with self.assertRaises(DataError): export_saved(missing)
        self.assertFalse(missing.exists())
        bad = self.root/'bad.db'; bad.write_bytes(b'not a sqlite database')
        with self.assertRaises(DataError): export_saved(bad)
        self.assertEqual(bad.read_bytes(), b'not a sqlite database')
        with sqlite3.connect(self.db) as db: db.execute('PRAGMA user_version=999')
        before = self.db.read_bytes()
        with self.assertRaisesRegex(DataError, 'STORE_VERSION'): export_saved(self.db)
        self.assertEqual(before, self.db.read_bytes())

    def test_tampered_saved_content_is_rejected(self):
        with sqlite3.connect(self.db) as db:
            db.execute('DROP TRIGGER immutable_objects_update')
            db.execute("UPDATE objects SET payload='{}' WHERE kind='result'")
        with self.assertRaisesRegex(DataError, 'STORE_INTEGRITY'): export_saved(self.db)

    def test_hot_journal_is_preserved_until_explicit_recovery(self):
        script="import sqlite3,sys,os;db=sqlite3.connect(sys.argv[1]);db.execute('PRAGMA cache_size=8');db.execute('BEGIN IMMEDIATE');db.execute('INSERT INTO objects VALUES(?,?,?,?)',('fault','request','fault','x'*2000000));os._exit(17)"
        p = subprocess.run([sys.executable,'-c',script,str(self.db)], timeout=15)
        self.assertEqual(p.returncode,17)
        journal = Path(str(self.db)+'-journal'); self.assertTrue(journal.exists())
        before = (self.db.read_bytes(), journal.read_bytes())
        with self.assertRaisesRegex(DataError,'STORE_DATABASE'): export_saved(self.db)
        self.assertEqual(before, (self.db.read_bytes(),journal.read_bytes()))
        self.store.recover()
        self.assertEqual(export_saved(self.db)['records'][0]['record_id'],self.receipt['record_id'])

    def test_html_embeds_exact_json_and_blocks_script_breakout(self):
        p = export_saved(self.db); p['records'][0]['reason'] = '</script><script>alert("&")</script>\u2028\u2029'
        html = render_html(p)
        self.assertEqual(embedded(html),p)
        self.assertEqual(html.count('<script'),2)
        self.assertIn("connect-src 'none'",html)

    def test_bad_template_and_schema_are_explicit(self):
        p = export_saved(self.db)
        with self.assertRaisesRegex(DataError,'VIEW_TEMPLATE'): render_html(p,'none')
        with self.assertRaisesRegex(DataError,'VIEW_SCHEMA'): render_html({'schema_version':'future'})

    def test_database_sidecar_and_file_alias_output_collisions(self):
        before = self.db.read_bytes()
        for path in [self.db]+[Path(str(self.db)+s) for s in ['-journal','-wal','-shm']]:
            with self.assertRaisesRegex(DataError,'VIEW_OUTPUT_COLLISION'): write_html(self.db,path)
        hard = self.root/'hard.html'; os.link(self.db,hard)
        sym = self.root/'symbolic.html'; sym.symlink_to(self.db)
        for path in [hard,sym]:
            with self.assertRaisesRegex(DataError,'VIEW_OUTPUT_COLLISION'): write_html(self.db,path)
        self.assertEqual(before,self.db.read_bytes())

    def test_atomic_export_failure_preserves_previous_file_and_database(self):
        output = self.root/'viewer.html'; output.write_text('previous export')
        before = self.db.read_bytes()
        with patch('saved_viewer.os.replace',side_effect=OSError('injected export failure')):
            with self.assertRaises(OSError): write_html(self.db,output)
        self.assertEqual(output.read_text(),'previous export'); self.assertEqual(before,self.db.read_bytes())
        self.assertEqual(list(self.root.glob('.saved-view-*')),[])

    def test_cli_export_and_failed_export_are_read_only(self):
        before = self.db.read_bytes(); output = self.root/'viewer.html'
        command = [sys.executable,str(ROOT/'src/saved_viewer.py'),'--db',str(self.db),'--output']
        good = subprocess.run(command+[str(output)],capture_output=True,text=True,timeout=15)
        self.assertEqual(good.returncode,0,good.stdout+good.stderr)
        self.assertEqual(json.loads(good.stdout)['snapshots'],24)
        self.assertEqual(embedded(output.read_text())['records'][0],self.store.load(self.receipt['record_id']))
        bad = subprocess.run(command+[str(self.root/'missing'/'viewer.html')],capture_output=True,text=True,timeout=15)
        self.assertEqual(bad.returncode,2); self.assertEqual(before,self.db.read_bytes())


if __name__=='__main__': unittest.main()
