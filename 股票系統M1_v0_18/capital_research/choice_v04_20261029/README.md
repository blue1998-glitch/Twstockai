# 保存0.4候選的明示研究選擇

已保存0.4結果現在可沿原 `research_choice.choose_saved`／`research_choice_workflow.select_and_save` 記錄明示研究意圖，不需重新產生候選。使用choice-input/0.2，來源明示提供完整0.4 request＋generation；舊choice/0.1及其來源維持相容。

- [完整契約](CONTRACT.md)、[結果與限制](REPORT.md)。
- [B93條件選擇輸入](cases/conditional-full/input.json)／[保存讀回](final/conditional-full/read.json)／[完整來源](final/conditional-full/source.json)／[來源核對](final/conditional-full/source-check.json)。
- [B2一般意圖](final/general-full/read.json)、[原checkpoint承接](final/checkpoint-new-trigger/read.json)、[舊觸發只允許零新增](final/zero-addition/read.json)。
- [凍結來源](frozen.json)、[最終來源版本](final/source-versions.json)、[定向測試log](tests-initial.log)、[驗證與原帳token](validation/bindings.json)。
- [凍結反例錯誤說明](diagnostics/token-intake.json)、[真正漏歷史token反例](corrections/missing-baseline-token/input.json)及[拒絕actual](validation/missing-baseline-token.json)。原反例及oracle未修改。

既有CLI可直接用（以下路徑從股票系統M1_v0_18執行；只對明示研究store寫新紀錄）：

```bash
python -m capital_research.research_choice_cli SELECT --store /tmp/twstockai-choice-v04 --id explicit-B93 --input capital_research/choice_v04_20261029/cases/conditional-full/input.json
python -m capital_research.research_choice_cli READ --store /tmp/twstockai-choice-v04 --id explicit-B93
python -m capital_research.research_choice_source_read --store /tmp/twstockai-choice-v04 --id explicit-B93 --source capital_research/choice_v04_20261029/final/conditional-full/source.json --format json
```

JSON保留完整單位、通道／來源及可知時間、搜尋政策／逐點收據、原帳快照、權利／reserve／latest與全部token。一般／條件／拒絕意圖分開；B93不是現在可買或已成交。圖形、來源與正式交易資格未提升，不選最佳量或策略勝者。一般使用者無需操作、搬檔或修檔。

`actual/`是token讀取防線修正前留史；`final/`綁最後source。所有數值結果直接重用上輪保存原件，這輪數值producer／帳務回放0。新choice/0.2尚未接research_operation、supplement或比較流程，不自動降版或接成交。
