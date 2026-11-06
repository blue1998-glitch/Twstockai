import unittest
from .audit import field_matches,diagnostic_status,FIELDS
class EvidenceTests(unittest.TestCase):
    def test_native_shares_over_JS_integer_limit_keep_exact_precision(self):
        a=dict(zip(FIELDS,["10.0000","11.5000","9.0","10.25","9007199254740993"]));b=dict(a);self.assertTrue(all(field_matches(a,b).values()));b["volume_shares_scaled"]="9007199254740992";self.assertFalse(field_matches(a,b)["volume_shares_scaled"])
    def test_equivalent_decimal_lexemes_do_not_change_original_values(self):
        a=dict.fromkeys(FIELDS,"10.000");b=dict.fromkeys(FIELDS,"10");before=dict(a);self.assertTrue(all(field_matches(a,b).values()));self.assertEqual(a,before)
    def test_volume_thousand_conversion_is_not_silently_accepted(self):
        a=dict.fromkeys(FIELDS,"10");b=dict(a);b["volume_shares_scaled"]="10000";self.assertEqual(diagnostic_status(True,field_matches(a,b)),"SOURCE_CONFLICT")
    def test_same_price_does_not_override_wrong_identity(self):
        self.assertEqual(diagnostic_status(False,dict.fromkeys(FIELDS,True)),"SOURCE_CONFLICT")
    def test_point_match_does_not_certify_interval(self):
        self.assertEqual(diagnostic_status(True,dict.fromkeys(FIELDS,True)),"NEEDS_INTERVAL_BASIS_ACTION_EVIDENCE")
    def test_existing_rejected_history_not_upgraded_by_current_quote(self):
        self.assertEqual(diagnostic_status(True,dict.fromkeys(FIELDS,True),existing_refusal=True),"REFUSED_EXISTING_HISTORY_QUALITY")
if __name__=="__main__":unittest.main(verbosity=2)
