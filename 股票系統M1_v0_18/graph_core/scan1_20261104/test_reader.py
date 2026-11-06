import unittest
from pathlib import Path
from unittest.mock import patch
from . import engine as e
from .present import present
from .provider import Provider
from rotation_research.store import Journal
class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.w=e.WORK/"synthetic-tests/test_01_all_unique_terminals_and_no_core_on_refused";self.spec=e.read(self.w/"manifest-private.json");self.index=e.read(self.w/"complete-index.json");self.provider=object.__new__(Provider);self.provider.rows={r["identity"]:r for r in self.index["records"]};self.provider.stocks={s["identity"]:s for s in self.spec["stocks"]};self.provider.numeric=self.spec;self.provider.journal=Journal(self.w/"results")
    def test_saved_presentation_uses_exact_result_without_core(self):
        s=self.spec["stocks"][0];v=self.provider.record(s["identity"]);f=e.fact(self.spec,s)
        with patch("graph_core.core.analyze",side_effect=AssertionError("NO_CORE_ON_READ")):result=present(f,v)
        self.assertEqual(result["series"]["results"][0],v["result"]);self.assertEqual(result["core_calls"],0);self.assertFalse(result["history_joined"])
    def test_saved_record_tamper_rejected_before_cache(self):
        original=Path.read_bytes;target=self.provider.journal.path(self.index["records"][0]["key"])
        with patch.object(Path,"read_bytes",lambda p:b"SYNTHETIC_CHANGED" if p==target else original(p)):
            with self.assertRaises(ValueError):self.provider.record(self.spec["stocks"][0]["identity"])
    def test_cross_stock_saved_reference_rejected(self):
        a,b=self.spec["stocks"][:2];self.provider.rows[a["identity"]]=self.provider.rows[b["identity"]]
        with self.assertRaises(ValueError):self.provider.record(a["identity"])
