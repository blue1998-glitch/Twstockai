# 外部明示交易單位的候選數量域 0.3

`quantity_candidates.generate` 現在可接外部明示的A／B交易單位，只列舉合法賣出／新增買進量。單位、通道、來源與可知時間均須明示；沒有預設1000股、選本金N、比例、賣點或策略，也沒有委託／成交。原0.1／0.2輸入及結果行為保持。

## 使用入口

純API：`capital_research.quantity_candidates.generate(request)`，新請求schema為`capital-quantity-candidates-input/0.3`，輸出`capital-quantity-candidates/0.3`。沿原0.2全部欄位，另加quantity_domain。完整實際輸入見 [人工9格](cases/manual-grid/input.json)、[明示1000股](cases/explicit-1000-no-partial/input.json)、[原checkpoint續接](controls/continuity/input.json)。

quantity_domain的完整結構：

```json
{"schema":"capital-quantity-domain/0.1","version":"EXPLICIT_SYNTHETIC_UNITS/0.1","parameter_source":"FROZEN_SYNTHETIC_QUANTITY_UNITS_NOT_MARKET_RULE","available_at":"2026-01-05T14:00:00+08:00","account_id":"原account完整指紋","assets":{"A":{"code":"A","channel_id":"DECLARED_SYNTHETIC_A","unit_shares":"2","source_id":"fixture","basis_id":"RAW:fixture:A","adjustment_version":"RAW:synthetic/1","available_at":"2026-01-05T14:00:00+08:00"},"B":{"code":"B","channel_id":"DECLARED_SYNTHETIC_B","unit_shares":"2","source_id":"fixture","basis_id":"RAW:fixture:B","adjustment_version":"RAW:synthetic/1","available_at":"2026-01-05T14:00:00+08:00"}}}
```

以上是格式說明，實際執行應用完整input原件。account、股票、source／basis／adjustment精確核對，available_at不晚於decision_at；未知／錯配／缺來源或無效單位在數值決策前拒絕，不猜一般盤或零股規則。此為當期明示合成模型，不是交易所規則認證。

## 數量如何處理

- 單位限制本次賣出／新增買進量，不限制既有持股或權利。原A105按單位100可賣100留5；另立明示期初B3可新增2達B5，不能因目標5不整除2就誤擋。
- bounds內完整列舉合法倍數，再算合法格點乘積及既有搜尋上限；不先跑所有整股、不抽樣、不推可行性單調。每個合法格點仍沿原資格、成本、資金、reserve、流動性、共同風險、fact／token與批次檢查。
- HOLD是變動量0，保留原股。EXIT若賣出量不符單位就REJECTED，不取整或清掉餘股。其他資產／權利仍在原帳。
- FULL重用原allocation.full_transfer。原端點符合單位才接原當期閘門；不符時NOT_IMPLEMENTED、plan=null，保留legacy_full_endpoint診斷，不自動向下取整或宣稱不存在其他合法全換量。
- enumeration_complete僅指明示合法grid列舉完整；不代表已完成單位感知全換求解。full_proposal_status另列。所有候選互斥，不加總共享現金，不排名或自動選勝者。

| 明示合成條件 | 實際數量域結果 |
| --- | --- |
| A／B單位2，賣0～4、增B0～4 | 9格：兩軸各0、2、4 |
| A1000、單位1000，賣0～1000、增B0，上限2格 | 只有0或1000兩格；原整股域1001點，沒有合法嚴格部分A賣量 |
| bounds兩軸1～1、單位2 | grid為空，端點另列；不判分批策略輸掉 |
| 原全換端點新增B94、B單位3 | 明確NOT_IMPLEMENTED，不改成93或冒稱完成最大量搜尋 |
| 原EXIT賣A100、A單位3 | 明確REJECTED，不改成99或清掉餘1 |

## 結果及證據

- [事前契約](CONTRACT.md)、[凍結指紋](frozen.json)、[原件來源／保護清單](intake.json)、[33個原凍結案例](case-index.json)。
- [生成總表](final/summary.json)：32案符合原預期；1案是fixture組裝錯誤而被正確拒絕，不能把all_statuses_matched=false改稱全部通過。
- [人工9格actual](final/manual-grid/actual.json)、[1000股actual](final/explicit-1000-no-partial/actual.json)、[空grid](final/empty-grid/actual.json)、[端點核對](validation-final/endpoint-gates.json)。
- [fixture診斷](fixture-diagnostic.json)：原existing-B3-add2錯改checkpoint持股，原expected=COMPLETE及actual拒絕原樣保留；未放寬原帳防線。另存[合法明示期初B3正例](corrections/existing-B3-add2-declared-opening/input.json)／[actual](corrections/existing-B3-add2-declared-opening/actual.json)，是獨立合成opening，不冒同一連續帳。
- [合法原checkpoint](controls/continuity/actual.json)、[原資本／latest／token證據](validation-final/delta-and-continuity.json)。
- [8唯一方法log](tests-final.log)、[人工點集](validation-final/manual-grid.json)、[舊版／unit1相容](validation-final/compatibility.json)、[來源時間／搜尋上限／未來隔離](validation-final/source-time-and-search.json)、[完整Context](validation-final/context/actual.json)、[新程序無成交／ledger](validation-final/fresh/actual.json)。
- [詳細報告](REPORT.md)、`preservation.json`及`CHANGE_MANIFEST.json`；manifest不含自身。before僅保存舊版不支援新契約的結果及兩份必要相容基線，不覆寫舊研究actual。

新輸出提供quantity_domain_id、domain_axes、raw_integer_grid_points、domain_reasons、每候選unit_gate_reasons／in_explicit_grid及full_proposal_status。candidate ID仍是目標身分，不能跨generation只靠ID推資格；必須綁完整generation與domain。外層feasible_for_research包含單位閘門，原core_evaluation只反映原財務／結構閘門。

## 限制及後續

本版沒有單位感知全換求解、混合通道、數量／容量撮合取整、零股實際成交、畸零權利轉換或市場回放。既有選擇／回放入口尚未接收新0.3，不隱式轉舊版去掉單位限制。原checkpoint核對重用既有resume_decision及原帳校驗；本輪不新增單、fills、交割或第二帳本。

1101期初cash_claims UNKNOWN、70／2／其中8／真實合格0、正式false／主壓力null、來源parents、P0-3/P0-4／圖形人工及原未支援保持。合成點集不是市場績效或比例建議；Work／Astra／救援原件未讀。

本項由唯一既有Codex自審、原分支正常保存及GitHub固定SHA讀回，無需人工搬檔或Work例行驗收。下一個具體未完成邊界是單位約束下的機械全換端點，須有限授權後重用原有界搜尋及財務閘門；本輪保持NOT_IMPLEMENTED，不先擴做。

版本界線：final/與tests-final.log／validation-final才綁現行source；actual/、tests.log及validation保留初版。自審另存兩份未知available_at反例，修前是AttributeError、修後是明確ValueError，不補日期；詳diagnostics/unknown-domain-time、unknown-unit-time，修前helper在diagnostics封存。兩批同8方法均過，不累加16。controls／corrections的已知日期正例保留生成時版本，未因純未知時點檢查重跑原帳結果。
