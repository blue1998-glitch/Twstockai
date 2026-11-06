"""Directed display lineage and fail-closed rebuilding; no engine evaluation."""
import base64
from contextlib import redirect_stdout
import gzip
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

from structure_state_chart.build_readable import PARENT, HERE, DATA, NAME, build, transform


class DisplayLineage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def run_build(self, out, parent=PARENT):
        with redirect_stdout(io.StringIO()):
            return build(out, parent)

    def test_all_five_numeric_and_role_files_identical(self):
        self.run_build(self.root/'out')
        for name in DATA:
            self.assertEqual((PARENT/name).read_bytes(), (self.root/'out'/name).read_bytes())

    def test_inline_numeric_and_state_payloads_preserved(self):
        self.run_build(self.root/'out')
        old=(PARENT/'M1_P03_structure_state_v01.html').read_text()
        new=(self.root/'out'/NAME).read_text()
        for pattern in [r'<script type="application/json" id="payload">(.*?)</script>',
                        r"const p03Compressed=Uint8Array.from\(atob\('([^']+)'\)"]:
            a=re.search(pattern,old,re.S).group(1);b=re.search(pattern,new,re.S).group(1)
            self.assertEqual(a,b)
        layer=json.loads(gzip.decompress(base64.b64decode(b)))
        self.assertEqual(layer['result'],json.loads((PARENT/'structure-state.json').read_bytes()))

    def test_frozen_source_tampering_refused(self):
        parent=self.root/'parent';shutil.copytree(PARENT,parent)
        target=parent/'structure-state.json';target.write_bytes(target.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'Frozen parent bytes mismatch'):
            self.run_build(self.root/'out',parent)
        self.assertFalse((self.root/'out').exists())

    def test_unknown_geometry_hook_refused(self):
        old=(PARENT/'M1_P03_structure_state_v01.html').read_bytes().replace(b'R=manual?140:110',b'R=999')
        with self.assertRaisesRegex(ValueError,'geometry hook mismatch'):
            transform(old,(HERE/'readability.js').read_text())

    def test_existing_different_output_not_overwritten(self):
        out=self.root/'out';self.run_build(out)
        (out/NAME).write_bytes(b'preserve local edit')
        with self.assertRaisesRegex(ValueError,'Refuse to overwrite'):
            self.run_build(out)
        self.assertEqual((out/NAME).read_bytes(),b'preserve local edit')

    def test_rebuild_is_byte_reproducible_and_display_only(self):
        report=self.run_build(self.root/'a');self.run_build(self.root/'b')
        for p in (self.root/'a').iterdir():
            self.assertEqual(p.read_bytes(),(self.root/'b'/p.name).read_bytes())
        self.assertFalse(report['numeric_producer_executed'])
        self.assertFalse(report['numeric_schema_changed'])
        self.assertEqual(report['physical_android'],'NOT_TESTED_NEW_BUILD')


if __name__=='__main__':
    unittest.main()
