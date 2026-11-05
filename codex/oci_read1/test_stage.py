"""New pure protocol/packaging checks only; no SDK/auth/network mocks."""
import hashlib,json,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from codex.oci_bridge1.bridge import Refused
from codex.oci_read1 import protocol as p
from codex.oci_read1.build import build
ROOT=Path(__file__).resolve().parents[2]
class Tests(unittest.TestCase):
    def test_fixed_two_field_command_only(self):
        self.assertEqual(p.parse_command(b'{"schema":"oci-read/0.1","operation":"list_pilot_compartment_resources"}')['operation'],p.OPERATION)
        for raw in [b'{"schema":"oci-read/0.1","operation":"ping"}',b'{"schema":"oci-read/0.1","operation":"list_pilot_compartment_resources","compartment":"PRIVATE"}',b'{"schema":"oci-read/0.1","schema":"oci-read/0.1","operation":"list_pilot_compartment_resources"}',b'x'*257]:
            with self.assertRaises(Refused):p.parse_command(raw)
    def test_pure_projection_is_not_a_native_or_oracle_attestation(self):
        result=dict(status='PARTIAL',reason='PILOT_SCOPE_ONLY',plan_kind=None,resources={k:dict(status='UNKNOWN',count=None,states={}) for k in ['compute','boot','block']},raw='DO_NOT_LEAK')
        out=p.project_result(result,request_comment_id=1,run_id=2,workflow_sha='a'*40,adapter_sha256='b'*64)
        self.assertEqual(out['attestation'],'NOT_ATTESTED_BY_PROJECTION');self.assertNotIn('DO_NOT_LEAK',json.dumps(out));self.assertIsNone(out['result']['resources']['boot']['count'])
        result['resources']['boot']['count']=0
        with self.assertRaises(Refused):p.project_result(result,request_comment_id=1,run_id=2,workflow_sha='a'*40,adapter_sha256='b'*64)
    def test_reproducible_package_keeps_original_adapter_bytes(self):
        with tempfile.TemporaryDirectory(prefix='read1-stage-',dir='/workspace/twstockai-local-data/oci_read1_20261105') as d:
            a=Path(d)/'a.pyz';b=Path(d)/'b.pyz';build(ROOT,a);build(ROOT,b);self.assertEqual(a.read_bytes(),b.read_bytes())
            with zipfile.ZipFile(a) as z:
                self.assertIsNone(z.testzip());self.assertEqual(z.read('codex/oci_bridge1/bridge.py'),(ROOT/'codex/oci_bridge1/bridge.py').read_bytes());self.assertEqual(len(z.namelist()),len(set(z.namelist())))
    def test_offline_entry_has_no_activation_or_secret_input(self):
        with tempfile.TemporaryDirectory(prefix='read1-entry-',dir='/workspace/twstockai-local-data/oci_read1_20261105') as d:
            package=Path(d)/'stage.pyz';build(ROOT,package)
            status=json.loads(subprocess.check_output([sys.executable,str(package),'inspect']))
            self.assertEqual(status['status'],'BLOCKED_CREDENTIAL_ISOLATION');self.assertEqual(status['oracle_actual_calls'],0)
            for arg in ['apply','execute','--force']:
                out=subprocess.run([sys.executable,str(package),arg],capture_output=True)
                self.assertEqual(out.returncode,2)
if __name__=='__main__':unittest.main(verbosity=2)
