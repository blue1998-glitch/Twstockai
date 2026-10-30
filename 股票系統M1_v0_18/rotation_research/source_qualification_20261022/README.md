# 官方來源資格補充 0.1（2026-10-22，本輪最新）

**指定資料窗的TWSE觀察交易日已核；公司行動完整性及總淨報酬仍未合格。** 原P1-7、獨立事件帳0.1、其44項測試及ZIP均保持。

新取得16份TWSE市場成交月報；2025-07-01～2026-10-16共473曆日、317個官方報告交易日。1101／2884各317保存日期完全相符。兩筆null在市場開市日，不補價也不猜停牌原因。這不認證五年日曆、其他交易所、券商交割日或歷史公布可得。

閱讀 [實測／資料缺口](REPORT.md)、[來源契約](SOURCE_CONTRACT.md)、[完整回Work指令](WORK_HANDOFF.md)。成果包、SHA與GitHub固定提交收據在根 `deliveries/m1-source-qualification-20261022/README.md`。

- `observed-calendar.json`／`calendar.csv`：逐日開市狀態、官方原件定位；CSV原股價格仍只來自舊RAW，null保留。
- `quote-calendar-comparison.json`：兩股日期／兩筆無報價、原計畫假日日曆對照。
- `action-source-audit.json`：減資預告／申報表的實際涵蓋限制與歷史減資HTTP307；沒有命中不等於無事件。原五事件組件完整保留。
- `window-qualification.json`：70窗日曆條件已核，但公司行動／淨分配／期初權利仍拒算；2窗40筆不足。沒有新的六方案成交、排名或報酬。
- `real-input-probe.json`／`real-input-refusal.json`：新日曆綁定後的實際拒算證據。
- `entitlement-requirements.json`：配股比、可交易日、零股、淨分配及期初權利所需來源；未知是null，不假設零。
- `source-manifest.json`／`raw/`：25份成功原件、1份HTTP307失敗；全部URL／時間／SHA與原件保存。
- `verification.json`、`tests.log`（本輪新15項）、`bootstrap.log`、`configuration-review.json`：實測及未套用設定草稿。

完整checkout依根AGENTS準備後，在股票系統M1_v0_18執行：

```bash
python3 -m unittest rotation_research.test_source_qualification -v
python3 -m rotation_research.source_qualification
```

這兩命令不連網、只寫本輪新資料夾；不執行舊study、不更新舊庫。沒有新UI，瀏覽器及Android本輪皆未測。下一步仍用Codex；先於環境設定檢閱／套用官方網域草稿，再核實特定來源是否可讀，繼續缺口。儲存草稿不是目前存取已開通。
