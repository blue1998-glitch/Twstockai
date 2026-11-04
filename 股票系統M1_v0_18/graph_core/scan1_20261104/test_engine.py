import unittest,json,shutil,io,contextlib
from pathlib import Path
from unittest.mock import patch
from graph_core.graph_lazy1_20261104.worker import run as original
from . import engine as e
SYNTHETIC_CORE_CALLS=0
def synthetic_runner(f):
    global SYNTHETIC_CORE_CALLS
    v=original(f);SYNTHETIC_CORE_CALLS+=1;return v
class ScanTests(unittest.TestCase):
    def setup(self,n=2,refused=True):
        w=e.WORK/"synthetic-tests"/self._testMethodName;w.mkdir(parents=True,exist_ok=False);(w/"baseline-private.json").write_bytes(e.encode(dict(free_bytes=shutil.disk_usage(w).free)))
        stocks=[]
        for i in range(n+int(refused)):
            code="SYN"+str(i);identity="TWSE:"+code;dt="2026-11-03";bad=i==n
            f=dict(identity=identity,code=code,name="合成",market="TWSE",isin="SYNTHETIC",cfi="ESVUFR",as_of=dt,source_status="SOURCE_REFUSED" if bad else "SOURCE_BAR_AVAILABLE",source_label="合成測試",bar=None if bad else dict(date=dt,open="10.000",high="12",low="9",close="11.50",volume_shares_scaled="12345678901234567"),continuity="NOT_CERTIFIED_NO_HISTORY_APPENDED",source=dict(capture_id="c"*64,daily_sha256="d"*64,price_mode="RAW_CANDIDATE",volume_unit="SHARES_REPORTED",price_basis_id=identity+"-OFFICIAL-RAW-UNBRIDGED-"+dt))
            b=e.encode(f);p=w/("fact-"+str(i)+".json");p.write_bytes(b);stocks.append(dict(**{k:f[k] for k in ["identity","code","market","isin","cfi","as_of"]},fact_path=str(p),fact=dict(bytes=len(b),sha256=e.sha(b),path=p.name)))
        spec=dict(version=e.VERSION,fixture="SYNTHETIC_ONLY",as_of=dt,capture_id="c"*64,daily_sources={"TWSE":"d"*64},protected_code={},original_sources={},stocks=stocks);spec["id"]=e.sha(e.encode(spec));(w/"manifest-private.json").write_bytes(e.encode(spec));return w,spec
    def test_01_all_unique_terminals_and_no_core_on_refused(self):
        w,s=self.setup();r=e.run(w,runner=synthetic_runner);self.assertEqual((r["processed"],r["new_core_calls"]),(3,2));self.assertEqual(r["counts"],dict(EXECUTED_INSUFFICIENT_HISTORY=2,SOURCE_REFUSED=1));self.assertEqual(len(e.read(w/"complete-index.json")["records"]),3)
    def test_02_limit_then_resume_does_not_repeat(self):
        w,s=self.setup();a=e.run(w,limit=1,runner=synthetic_runner);b=e.run(w,runner=synthetic_runner);self.assertEqual((a["status"],a["new_core_calls"],b["new_core_calls"]),("PARTIAL",1,1))
    def test_03_complete_replay_zero_core_and_zero_writes(self):
        w,s=self.setup();e.run(w,runner=synthetic_runner);before={str(p):p.read_bytes() for p in w.rglob("*") if p.is_file()};r=e.run(w,runner=lambda _:self.fail("NO_REPEAT"));self.assertEqual((r["new_core_calls"],r["new_records"]),(0,0));self.assertEqual(before,{str(p):p.read_bytes() for p in w.rglob("*") if p.is_file()})
    def test_04_unknown_core_outcome_never_reexecuted(self):
        w,s=self.setup(n=1,refused=False)
        def interrupted(f):synthetic_runner(f);raise KeyboardInterrupt("SYNTHETIC_CRASH_AFTER_CORE")
        with self.assertRaises(KeyboardInterrupt):e.run(w,runner=interrupted)
        r=e.run(w,runner=lambda _:self.fail("UNKNOWN_MUST_NOT_REPEAT"));self.assertEqual(r["counts"],dict(ENGINEERING_FAILURE_UNKNOWN_OUTCOME=1));self.assertEqual(r["unknown_core_outcomes"],1)
    def test_05_checkpoint_tamper_is_not_repaired_or_recomputed(self):
        w,s=self.setup();e.run(w,runner=synthetic_runner);record=next((w/"results").glob("*.json"));record.write_bytes(record.read_bytes()+b" ")
        with self.assertRaises(ValueError):e.run(w,runner=lambda _:self.fail("NO_REPAIR"))
    def test_06_source_fact_tamper_prevents_core_for_stock(self):
        w,s=self.setup(n=1,refused=False);Path(s["stocks"][0]["fact_path"]).write_bytes(b"SYNTHETIC_TAMPER");r=e.run(w,runner=lambda _:self.fail("NO_WRONG_SOURCE_CORE"));self.assertEqual(r["counts"],dict(ENGINEERING_FAILURE=1));self.assertEqual(r["new_core_calls"],0)
    def test_07_worker_error_isolated_from_other_stocks(self):
        w,s=self.setup()
        def runner(f):
            if f["code"]=="SYN0":raise RuntimeError("SYNTHETIC_WORKER_REFUSAL")
            return synthetic_runner(f)
        r=e.run(w,runner=runner);self.assertEqual(r["processed"],3);self.assertEqual(r["counts"]["ENGINEERING_FAILURE"],1);self.assertEqual(r["counts"]["SOURCE_REFUSED"],1)
    def test_08_manifest_change_refuses_before_core(self):
        w,s=self.setup();s["as_of"]="2026-11-04";(w/"manifest-private.json").write_bytes(e.encode(s))
        with self.assertRaises(ValueError):e.run(w,runner=lambda _:self.fail("NO_CHANGED_BINDING"))
    def test_09_partial_log_unknown_is_not_truncated(self):
        w,s=self.setup();(w/"attempts.jsonl").write_bytes(b"{SYNTHETIC_PARTIAL")
        with self.assertRaises(ValueError):e.run(w,runner=lambda _:self.fail("NO_PARTIAL_LOG_REPLAY"))
        self.assertEqual((w/"attempts.jsonl").read_bytes(),b"{SYNTHETIC_PARTIAL")
    def test_10_capacity_rejects_before_core(self):
        w,s=self.setup()
        with patch.object(e.shutil,"disk_usage",return_value=type("Usage",(),dict(free=e.RESERVE))()):
            with self.assertRaises(OSError):e.run(w,runner=lambda _:self.fail("NO_SPACE_NO_CORE"))
if __name__=="__main__":unittest.main(verbosity=2)
