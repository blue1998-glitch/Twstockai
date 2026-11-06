import importlib.abc
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
from cross_view_export import MOBILE_TEMPLATE, TEMPLATE, protect, render
from cross_view_cli import read_config
from contracts import DataError
from period_store import StoreFailure


def embedded(text):
    return json.loads(re.search(r'<script id="cross-data" type="application/json">(.*?)</script>', text, re.S).group(1))


class MobileExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT / '日週月研究對照.html').read_text()
        cls.payload = embedded(cls.original)

    def test_original_renderer_remains_identical_and_mobile_embeds_identical_data(self):
        self.assertEqual(render(self.payload), self.original)
        mobile = render(self.payload, template=MOBILE_TEMPLATE)
        self.assertEqual(embedded(mobile), self.payload)
        self.assertIn('手機閱讀版 v0.18', mobile)
        self.assertIn('小數兩位', mobile)

    def test_mobile_preserves_script_escaping_and_original_network_policy(self):
        payload = dict(self.payload, source_aliases={'test': '</script><script>BAD()</script>'})
        mobile = render(payload, template=MOBILE_TEMPLATE)
        self.assertNotIn('</script><script>BAD()', mobile)
        self.assertIn("connect-src 'none'", mobile)
        self.assertEqual(embedded(mobile), payload)

    def test_output_cannot_overwrite_either_template_in_either_mode(self):
        config = read_config(ROOT / 'cross_view/sources.json')
        for selected in [TEMPLATE, MOBILE_TEMPLATE]:
            for target in [TEMPLATE, MOBILE_TEMPLATE]:
                with self.subTest(selected=selected.name, target=target.name):
                    with self.assertRaises((DataError, StoreFailure)):
                        protect(config, target, template=selected)

    def test_mobile_cli_is_read_only_without_engines_or_recovery(self):
        code = '''import sys,importlib.abc
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname in ('structure','moving_averages','analysis_jobs','analysis_workflow','period_ma','period_jobs','period_workflow','jobs','prepare_daily'):raise RuntimeError('FORBIDDEN '+fullname)
sys.meta_path.insert(0,Block())
from analysis_store import AnalysisStore
AnalysisStore.recover=lambda *a:(_ for _ in ()).throw(RuntimeError('RECOVERY FORBIDDEN'))
from cross_view_cli import main
assert main(['--config',sys.argv[1],'--html','--mobile','--output',sys.argv[2]])==0
'''
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'mobile.html'
            result = subprocess.run([sys.executable, '-c', code, str(ROOT / 'cross_view/sources.json'), str(output)], env={**os.environ, 'PYTHONPATH': str(ROOT / 'src')}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(embedded(output.read_text()), self.payload)

    def test_mobile_option_without_html_fails_before_read_or_write(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'not-created'
            result = subprocess.run([sys.executable, str(ROOT / 'src/cross_view_cli.py'), '--config', str(Path(temp) / 'missing.json'), '--mobile', '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('--mobile requires --html', result.stderr)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
