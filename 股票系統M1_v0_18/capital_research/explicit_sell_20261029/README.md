# 已結清原帳的明示減碼／退出 0.2

此版補足原帳的 SELL 行動接線。使用者或外部研究輸入明示股票、股數、時點、委託、日曆與 tape；程式檢查後交給既有執行器，不選賣點、比例或策略。所有案例均為合成帳務診斷。

## 使用入口

1. `capital_research.cash_action.evaluate(action_input)`：檢查單一減碼／退出意圖，不建單、不成交。
2. `capital_research.cash_action_execution.execute(execution_input)`：綁完整原輸入與 checked 結果，檢查外部委託後接原 `execution.simulate`／`continuity.make_checkpoint`。
3. 新賣單部分成交後，直接重用 `execution_continuation.resume_orders`；本輪沒有另建續播器或帳本。

新行動版本 `capital-cash-action-input/0.2`，輸出 `capital-cash-action/0.2`。新執行版本 `capital-cash-action-execution-input/0.2`，輸出 `capital-cash-action-execution/0.2`。原 HOLD／現金買進沿 0.1；不交叉借用 checked 或隱式遷移保存結果。

action 的完整必要欄位：

```json
{"id":"sell-B-explicit","kind":"REDUCE_HOLDING","code":"B","sell_shares":"3","reason":"EXPLICIT_SYNTHETIC_REDUCTION_NOT_USER_RULE"}
```

`REDUCE_HOLDING` 必須留下指定股持股；`EXIT_SELLABLE_HOLDING` 必須明示恰等於當期可賣量的股數。兩者只接受已結清、無活單／應付的完整合成原 checkpoint。其他持股與權利不動，不推定限售解除。完整可用輸入見 [減碼](cases/reduce-B3/action-input.json)、[退出](cases/exit-B7/action-input.json) 與 [完整執行請求](initial/exit-B7/execution-input.json)。

執行只能送核准股票的 SELL，拆單總量不得超過核准量。空單、少送、部分／未成交都不會補齊或假裝退出完成。新版本不能夾 BUY 或另一檔股票。原買進資格／新批 token 規則不變；減碼本身不新增或清除買進觸發。

## 白話合成結果

原本金 1180、一般 reserve 100；主要當期帳為現金 858.86、B7／C2，另有現金權利 80 與 C2 股份權利。沿保存的 1/9 tape、1/12 交割與窗口，不加行情。

| 外部明示行動 | 實際新成交 | 1/12 現金 | 1/12 持股 | 結果意義 |
| --- | --- | --- | --- | --- |
| 減 B3 | SELL 3 | 996.80 | B4／C4 | 賣出應收 57.94 到期入帳一次 |
| 退出可賣 B7 | SELL 7 | 1076.72 | B0／C4 | 指定股退出；其他股票及權利保留 |
| B7 拆成 3＋4 | SELL 3＋4 | 1074.72 | B0／C4 | 原逐 fill 費稅，拆單多付 2 |
| 跌停／容量零 | 0 | 938.86 | B7／C4 | 沒有假賣出；原 80 權利仍到位 |
| 空 orders | 0 | 938.86 | B7／C4 | 只有意圖，不自動生成新單 |
| 原 B20 退出 20，容量 7 | SELL 7 | 816.46 | B13／C4 | 此分支期初現金 598.6；剩 13 到期，不冒稱全退 |

19.98 是外部明示的合成執行參數（原價格 20、既有滑價模型），不是市場成交證明或新增賣出門檻。應收、費稅及每天淨值核算見 [報告](REPORT.md)／[逐日手算](test-evidence/daily-handcheck.json)。

## 證據入口

- [事前契約](CONTRACT.md)、[輸入／來源清單](intake.json)、[事前凍結指紋](frozen.json)、[23 組預期](case-index.json)。
- [舊版不支援的修前結果](before/actual.json)、[新版 23 案總表](initial/summary.json)；`initial` 綁本輪最終兩個產品 source，不是歷史舊 source 重算。
- [部分賣出續播](controls/partial/actual.json)、[完整一次執行與續播比較](controls/partial/comparison.json)：逐明示觀察、逐日、完整 execution／checkpoint 相同。
- [未來隔離](controls/future/comparison.json)、[完整 Decimal Context 控制](controls/context/actual.json)、[不具買進資格仍可檢查減碼](controls/not-new-capital-qualified/actual.json)。
- [三份 0.1 原結果完整相容](controls/legacy/summary.json)、[其他股票委託拒絕](controls/wrong-order-code/actual.json)。
- [8 個唯一測試方法及保存 log](tests-final.log)、[測試程式](test_sell.py)、[環境恢復診斷](diagnostics/environment-recovery.json)。未重跑舊 suite／真實 producer。
- `preservation.json` 與 `CHANGE_MANIFEST.json` 在保存前產生；manifest 不含自身，舊 oracle／before／source 快照不修改。

## 範圍

只支援完整原窗的明示合成帳。活單／未交割應付先走原單續播，結清後才能作新的減碼決策。來源不明、未知權利、限售解除、信用、未知期初應付、R2/F、市場回放及策略仍未支援；不是靠改版解除拒算。資料缺口、70／2／其中8／真實合格0、全部正式資格 false、primary_pressure_id=null 與來源 parents 保持。Work／Astra／第一工作區救援原件未讀，不稱 Work 獨立驗收。

本輪由原唯一 Codex 按里程碑自審、正常保存及 GitHub 固定 SHA 讀回，不需人工搬檔或例行轉 Work。若接續，先依有效優先順序核對已定義缺口；本項完成後不另建相同 READ／摘要／並列包裝。
