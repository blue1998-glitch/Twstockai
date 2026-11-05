"""Only new evidence-boundary tests; no mock OCI/GitHub execution."""
import copy,json,unittest
from pathlib import Path
from codex.oci_read1.qual_gate2.evidence import sync_observations,assessment,EvidenceConflict
ROOT=Path(__file__).resolve().parents[3]
class Tests(unittest.TestCase):
    def setUp(self):
        self.visual=json.loads((ROOT/'codex/oci_read1/qual_gate2/visual-evidence.json').read_text())
        self.account=json.loads((ROOT/'codex/oci_read1/oauth_approved/account.default.json').read_text())
    def test_visual_facts_retained_without_promoting_runtime_qualification(self):
        after=sync_observations(self.account,self.visual)
        self.assertEqual(after['observations']['domain_kind'],'Free');self.assertIn('Twstockai-Pilot displayed Active',after['observations']['pilot_scope_and_iam'])
        for field in ['findings','config','captured_at','expires_at']:self.assertEqual(after[field],self.account[field])
        self.assertEqual(after['findings']['existing_independent_pilot'],'UNKNOWN');self.assertIsNone(after['captured_at'])
    def test_visual_cannot_assert_wif_api_quota_or_unread_original(self):
        for key in ['wif.rollout','trust.remaining_quota','oracle.api_verified']:
            doc=copy.deepcopy(self.visual);doc['facts'][key]='TRUE'
            with self.assertRaises(EvidenceConflict):sync_observations(self.account,doc)
        doc=copy.deepcopy(self.visual);doc['references'][0]['codex_original_screenshot_read']=True
        with self.assertRaises(EvidenceConflict):sync_observations(self.account,doc)
    def test_conflicting_previous_observation_is_not_overwritten(self):
        self.account['observations']['domain_kind']='DIFFERENT_SAVED_SOURCE'
        with self.assertRaises(EvidenceConflict):sync_observations(self.account,self.visual)
    def test_new_visual_sync_still_refuses_original_read1_gate(self):
        from codex.oci_read1.oauth_approved.native import Gate
        from codex.oci_ctrl1.handler import Refused
        after=sync_observations(self.account,self.visual)
        class AccountOnly:
            def content(self,path,sha):
                self.expected=(path=='read1/oauth/account.json' and sha=='a'*40)
                if not self.expected:raise AssertionError('unexpected access')
                return json.dumps(after).encode(),'b'*40
        gate=Gate(AccountOnly(),{'GITHUB_WORKFLOW_SHA':'a'*40},{},b'NOT_EXECUTED',0)
        with self.assertRaisesRegex(Refused,'PREREQUISITES_UNKNOWN'):gate.qualification()
        out=assessment(after,self.visual,{'tenant_management_api_verified':False,'management_api_calls':0,'oci_tool_configured':True})
        self.assertEqual(out['status'],'BLOCKED_OWNER_AUTH');self.assertIsNone(out['pilot_resource_counts']);self.assertFalse(out['execution_authorized']);self.assertFalse(out['next_read1_command_allowed'])
if __name__=='__main__':unittest.main(verbosity=2)
