# 資金決策第一階段交付

本輪固定工程／最新GitHub已核提交見 [GITHUB_READBACK.md](GITHUB_READBACK.md) 及 [JSON收據](GITHUB_READBACK.json)；工程與收據分開提交，避免自指。指定分支 `dev/m1-v018-chart-annotations`，起始 `392b94a4f29b2e53fbfc0b7bda8a3fc1d0592b25`，保留1085b17／3b6fe93及全部後續，不改main。

直接可讀：

- [實作與驗證報告](../../股票系統M1_v0_18/capital_research/REPORT.md)
- [可重用模組／欄位差異](../../股票系統M1_v0_18/capital_research/INVENTORY.md)
- [輸入輸出契約](../../股票系統M1_v0_18/capital_research/CONTRACT.md)
- [實際執行／46方法計數](../../股票系統M1_v0_18/capital_research/validation_20261024/execution.json)
- [合成反例與完整輸入](../../股票系統M1_v0_18/capital_research/validation_20261024/artifacts/synthetic-cases.json)
- [資金／費用／交割證據](../../股票系統M1_v0_18/capital_research/validation_20261024/artifacts/accounting-evidence.json)
- [未來隔離證據](../../股票系統M1_v0_18/capital_research/validation_20261024/artifacts/future-isolation.json)
- [單次正式0.10拒算接線probe](../../股票系統M1_v0_18/capital_research/validation_20261024/real-source-gate-probe.json)
- [完整Work／原Codex接續指令](../../M1_CAPITAL_RESEARCH_PHASE1_HANDOFF.md)

[本輪新獨立小包](M1_capital_phase1_20261024.zip) 只含新研究、合成證據與必要未改依賴的精確source副本；不含任何私人原件或Astra全文，不覆蓋舊專案。包內MANIFEST逐成員長度／SHA及CRC驗證、新解壓數值重現範圍見[封包核對](package-verification.json)，包SHA見[SHA256SUMS](SHA256SUMS)。純合成重現不需網頁／網路／資料庫；真實來源gate重跑需完整repo的既有catalog鏈，包內保存的拒算結果不冒新來源認證。

本階段46個唯一新方法PASS，中間40／43及builder、CLI、包重現不累加；舊測試0、真實市場六方案0。真實0.10的70拒算／2不足／8不支援／總淨合格0是保存狀態核對，本輪另做1次拒算接線probe而非整個producer重跑。首次數值型別、測試容量假設及舊probe事件版本錯配診斷都保留。

Astra Library全文未取得／未讀；依使用者完整第一階段指令實作。全部數值為合成研究，不能支持投資績效／最佳比例或實盤授權。R2／F、信用帳務、期初應付／既有待成交完整重播未實作並明確拒絕。全部來源／歷史／資格／null／UNKNOWN／警告及正式策略保留。下一步 **Work唯讀研究驗收**，具體工程回原既有唯一Codex，完整指令在上方handoff；無子代理、部署、下單、付費或訊息。
