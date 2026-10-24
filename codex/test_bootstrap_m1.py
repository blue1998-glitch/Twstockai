"""Fresh-source checkout hydration preserves edits and verifies every input ZIP."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


class BootstrapHydrationTests(unittest.TestCase):
    def test_fresh_source_hydrates_missing_assets_repeats_safely_and_preserves_edits(self):
        with tempfile.TemporaryDirectory(dir=REPO.parent) as temporary:
            repo = Path(temporary)
            shutil.copytree(REPO / 'codex', repo / 'codex')
            for name in ['M1_v0_17_01.zip', 'M1_v0_17_02.zip', 'M1_v0_17_03.zip']:
                os.link(REPO / name, repo / name)
            target = repo / '股票系統M1_v0_18'
            changed = target / 'src/cross_view_export.py'
            changed.parent.mkdir(parents=True)
            changed.write_text('# preserved local source change\n')
            extra = target / 'user-note.txt'
            extra.write_text('preserve this too')
            command = [sys.executable, str(repo / 'codex/bootstrap_m1.py')]
            first = subprocess.run(command + ['--hydrate-missing'], capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            result = json.loads(first.stdout)
            self.assertEqual(result['status'], 'HYDRATED_PRESERVING_CHANGES')
            self.assertEqual(result['restored_files'], 851)
            self.assertEqual(result['differing_files_preserved'], ['src/cross_view_export.py'])
            self.assertFalse(result['current_tree_matches_baseline'])
            manifest = json.loads((target / 'output/交付檔案指紋.json').read_text())
            for row in manifest['files']:
                if row['file'] != 'src/cross_view_export.py':
                    self.assertEqual(hashlib.sha256((target / row['file']).read_bytes()).hexdigest(), row['sha256'])
            before = changed.stat().st_mtime_ns
            second = subprocess.run(command + ['--hydrate-missing'], capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout)['restored_files'], 0)
            self.assertEqual(changed.stat().st_mtime_ns, before)
            strict = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(strict.returncode, 2)
            self.assertEqual(json.loads(strict.stderr)['status'], 'PREPARATION_FAILED')
            self.assertEqual(changed.read_text(), '# preserved local source change\n')
            self.assertEqual(extra.read_text(), 'preserve this too')


if __name__ == '__main__':
    unittest.main()
