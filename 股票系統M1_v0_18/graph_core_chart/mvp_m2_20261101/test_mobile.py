from copy import deepcopy
import json
from pathlib import Path
import re
import unittest
from graph_core_chart.mobile_comparison import HERE,OUT,NAME,ROOT,validate
from graph_core_chart.comparison_export import sha
from technical_chart.build import unpack


class MobileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(OUT/NAME).read_text()
        cls.bundle=unpack(json.loads(re.search(r'id="payload"[^>]*>(.*?)</script>',cls.html,re.S)[1]))
        cls.index=json.loads((HERE.parent/'mc2_20261101/index.json').read_text())

    def test_frozen_originals_and_embedded_source_exact(self):
        frozen=json.loads((HERE/'frozen.json').read_text())
        for row in frozen['files']:
            raw=(ROOT/row['path']).read_bytes();self.assertEqual(len(raw),row['bytes']);self.assertEqual(sha(raw),row['sha256'])
        original=unpack(json.loads(re.search(r'id="payload"[^>]*>(.*?)</script>',(ROOT/frozen['files'][0]['path']).read_text(),re.S)[1]))
        self.assertEqual(self.bundle,original)
        embedded=json.loads(re.search(r'id="comparison-payload"[^>]*>(.*?)</script>',self.html,re.S)[1]);self.assertEqual(embedded,self.index)
        self.assertLess(len(json.dumps(embedded).encode()),100000)
        validate(self.bundle,self.index)

    def test_mismatch_refusals_and_input_unchanged(self):
        before=deepcopy(self.index);validate(self.bundle,self.index);self.assertEqual(self.index,before)
        for mutation in ('date','result','source','pending','box','qualification'):
            index=deepcopy(self.index)
            if mutation=='date':index['as_of']='2026-10-15'
            elif mutation=='result':index['stocks'][0]['result_id']='WRONG'
            elif mutation=='source':index['stocks'][0]['source_input_binding']['basis_break_dates']=['WRONG']
            elif mutation=='pending':index['stocks'][0]['pending_extrema']=[]
            elif mutation=='box':index['stocks'][0]['nearest_above']['candidate_ids']=['WRONG']
            else:index['stocks'][0]['primary_pressure_id']='WRONG'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):validate(self.bundle,index)


if __name__=='__main__':unittest.main()
