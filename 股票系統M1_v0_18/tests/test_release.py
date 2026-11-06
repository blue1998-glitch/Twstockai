import json,sys,subprocess,tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from contracts import fingerprint


class ReleaseTests(unittest.TestCase):
    def test_original_candidate_outputs_unchanged(self):
        baseline=json.loads((ROOT/'data/v0_1_功能參照指紋.json').read_text());keys=['as_of','pivots','zones','pending','daily_events','structure_status']
        for case,ref in baseline.items():
            r=json.loads((ROOT/'output'/f'{case}.json').read_text())
            self.assertEqual(fingerprint([{k:s[k] for k in keys} for s in r['snapshots']]),ref['functional_hash'])

    def test_job_cli_rejects_corrupt_input_with_error_report(self):
        with tempfile.TemporaryDirectory() as d:
            inp=Path(d)/'bad.json';out=Path(d)/'result.json';inp.write_text('broken')
            r=subprocess.run([sys.executable,str(ROOT/'src/jobs.py'),'--input',str(inp),'--output',str(out)],capture_output=True)
            self.assertEqual(r.returncode,2);report=json.loads(out.read_text())
            self.assertEqual(report['status'],'DATA_ERROR');self.assertEqual(report['action_qualification'],'NOT_EVALUATED')


if __name__=='__main__':unittest.main()
