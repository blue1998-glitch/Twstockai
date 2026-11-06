# 單位感知全換有界搜尋

入口仍是 `capital_research.quantity_candidates.generate(request)`，明示 `schema=capital-quantity-candidates-input/0.4`。直接例子：[主例輸入](cases/manual-93/input.json)、[凍結預期](cases/manual-93/expected.json)、[實際結果](actual/manual-93/actual.json)、[22案摘要](actual/summary.json)。不需新CLI、回放、帳本或READ包裝。

原A100、B0、C2及權利保留；指定A單位2、B單位3後，逐一檢查111、108、105、102、99、96、93，找出本數量域機械全換端點B93。B96含成本超出共同資金；B93仍須等原股賣出交割並重新評估，沒有成交或自動推薦。原整股端點94仍在舊0.3診斷，不取整那份結果。

- [契約](CONTRACT.md)：完整輸入、來源時點、資源限制及未知／拒絕界線。
- [報告](REPORT.md)：完成／未完成、測試診斷、自審與精確入口。
- [凍結清單](frozen.json)、[來源](intake.json)：實作前input／expected、舊source及三版控制原件。
- [實際來源版本](actual/source-versions.json)、[驗證索引](validation-summary.json)：每個方法對應真實log，不把中間批加總。
- [非單調例](actual/non-monotone/actual.json)：同一原帳B0拒絕、B1／B2可行、B3拒絕，搜尋得B2。
- [未知批次例](actual/outer-unknown/actual.json)：相同財務數量仍不能繞過C-family及UNKNOWN防線。
- [原帳承接收據](validation/continuity.json)：latest、原opening、權利、reserve及全部token沿原resume核對。

只證合成數量機制；不證策略績效。新增0.4未接下游選擇／成交，舊版READ及歷史結果原樣保持。一般使用者無需搬檔、修檔或操作。
