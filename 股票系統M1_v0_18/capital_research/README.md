# 資金決策獨立研究 0.1｜第一階段

本目錄驗證資訊與資金機制，**不是策略批准、真實績效或正式持倉系統**。全部數值案例都是合成研究。Astra Library 報告全文未取得／未讀；本輪依使用者第一階段完整指令實作，沒有將指令或摘要冒稱全文。

先讀 [CONTRACT.md](CONTRACT.md)、[INVENTORY.md](INVENTORY.md)、[REPORT.md](REPORT.md)。下一輪完整指令在 root `M1_CAPITAL_RESEARCH_PHASE1_HANDOFF.md`。工程固定提交／GitHub讀回在 root `deliveries/m1-capital-research-phase1-20261024/`。

在 `股票系統M1_v0_18` 可無網頁執行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest capital_research.test_mechanisms -v
PYTHONDONTWRITEBYTECODE=1 python3 -m capital_research.build_evidence --output /tmp/NEW-capital-synthetic-artifacts
python3 -m capital_research.cli RUN --input capital_research/validation_20261024/artifacts/input.json --store /tmp/NEW-capital-records --id decision-v1
python3 -m capital_research.cli EXECUTE --input capital_research/validation_20261024/artifacts/execution-input.json --store /tmp/NEW-capital-records --id execution-v1
python3 -m capital_research.cli READ --store /tmp/NEW-capital-records --id execution-v1
```

新 checkout 依最新 AGENTS 準備；上述命令供重現，不代表下輪必須重跑。`build_evidence` 不覆寫不同檔案，CLI 沿用 `rotation_research.store.Journal`。READ不匯入決策或帳務引擎；同ID不同結果拒絕，中斷檔保留。單檔exclusive/fsync限制與舊Journal相同，沒有新增跨檔交易／斷電保證。

`core.decide` 分開三層證據／新資金／移轉，`allocation.full_transfer` 只枚舉成本與風控允許的最大整股數，`execution.simulate` 處理明示委託／撮合觀察並重用既有 `action_ledger.replay`。沒有第二套帳務公式。`resume_decision`／CLI `RUN --prior-id` 帶入先前已看證據身分，避免同一事件再次當新證據。

R1為明示事件／研究預算與風險限制的可行性框架；C／E的數量是外部合成提案，不是演算法找出的最佳比例。R2／F只保留契約，`NOT_IMPLEMENTED`。券商額度只作另列且明示資格的合成可行性情境，既有帳務不支援，所以拒絕數值重播。期初應付及既有待成交的決策預留已支援，其完整帳務重播明確拒絕。

沒有UI、人工模式重製、正式規則／歷史schema變更、真實公司行動producer、六方案市場績效或Android執行。來源0.10及全部parent、原件、null／UNKNOWN與false資格保持。
