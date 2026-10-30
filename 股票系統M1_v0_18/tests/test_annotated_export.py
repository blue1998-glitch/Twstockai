import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from cross_view_export import render, protect, TEMPLATE, MOBILE_TEMPLATE, ANNOTATED_TEMPLATE, ANNOTATION_SCRIPT
from cross_view_cli import read_config
from contracts import DataError
from period_store import StoreFailure


def embedded(text):
    return json.loads(re.search(r'<script id="cross-data" type="application/json">(.*?)</script>', text, re.S)[1])


class AnnotatedExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = (ROOT / '日週月研究對照.html').read_text()
        cls.payload = embedded(cls.old)

    def test_original_and_mobile_pages_remain_exactly_reproducible(self):
        self.assertEqual(render(self.payload), self.old)
        self.assertEqual(render(self.payload, template=MOBILE_TEMPLATE),
                         (ROOT / '日週月研究對照_手機版_v0_18.html').read_text())
        annotated = render(self.payload, template=ANNOTATED_TEMPLATE)
        self.assertEqual(embedded(annotated), self.payload)
        self.assertNotIn('@@ANNOTATION_CODE@@', annotated)
        self.assertIn('function savedAnnotations', annotated)

    def test_script_escaping_and_offline_policy_are_preserved(self):
        payload = dict(self.payload, source_aliases={'x': '</script><script>BAD()</script>'})
        text = render(payload, template=ANNOTATED_TEMPLATE)
        self.assertEqual(embedded(text), payload)
        self.assertNotIn('</script><script>BAD()', text)
        self.assertIn("connect-src 'none'", text)

    def test_all_modes_protect_every_template_and_the_annotation_module(self):
        config = read_config(ROOT / 'cross_view/sources.json')
        for mode in [TEMPLATE, MOBILE_TEMPLATE, ANNOTATED_TEMPLATE]:
            for target in [TEMPLATE, MOBILE_TEMPLATE, ANNOTATED_TEMPLATE, ANNOTATION_SCRIPT]:
                with self.subTest(mode=mode.name, target=target.name):
                    with self.assertRaises((DataError, StoreFailure)):
                        protect(config, target, template=mode)

    def test_annotation_cli_without_html_rejects_before_access(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'not-created'
            run = subprocess.run([sys.executable, str(ROOT / 'src/cross_view_cli.py'),
                                  '--config', str(Path(directory) / 'missing'),
                                  '--annotations', '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn('--annotations requires --html', run.stderr)
            self.assertFalse(output.exists())

    def test_annotation_export_uses_read_only_saved_data_without_engine_or_recovery(self):
        code = '''import sys,importlib.abc
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname in ('structure','moving_averages','analysis_jobs','analysis_workflow','period_ma','period_jobs','period_workflow','jobs','prepare_daily'):raise RuntimeError('FORBIDDEN '+fullname)
sys.meta_path.insert(0,Block())
from analysis_store import AnalysisStore
AnalysisStore.recover=lambda *a:(_ for _ in ()).throw(RuntimeError('RECOVERY FORBIDDEN'))
from cross_view_cli import main
assert main(['--config',sys.argv[1],'--html','--annotations','--output',sys.argv[2]])==0
'''
        config = read_config(ROOT / 'cross_view/sources.json')
        stores = list(map(Path, config['daily_stores'].values()))
        before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in stores}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'annotated.html'
            run = subprocess.run([sys.executable, '-c', code, str(ROOT / 'cross_view/sources.json'), str(output)],
                                 capture_output=True, text=True, env={**os.environ, 'PYTHONPATH': str(ROOT / 'src')})
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(embedded(output.read_text()), self.payload)
        self.assertEqual(before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in stores})
