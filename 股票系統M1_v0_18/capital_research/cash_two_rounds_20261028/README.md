# 同原帳兩輪明示合成案例0.1

**既有入口已可直接承接，不需改產品程式或新增協調器。** 第一輪重用保存結果，第二輪沿其已結清、無活單／應付的完整checkpoint，使用原1/9合成tape及原1/12截止。

- [自審報告](REPORT.md)、[事前契約](CONTRACT.md)
- [第一輪原件綁定](first-round-binding.json)、[六個第二輪互斥案例摘要](summary.json)、[4唯一方法log](tests-first.log)
- [完整第二輪input](cases/independent-B20/input.json)、[先存預期](cases/independent-B20/expected.json)、[保存actual](actual/independent-B20/result.json)
- [逐日手算核對](test-evidence/daily-balances.json)、[完整原帳／latest／token承接](test-evidence/continuity.json)
- [舊觸發拒絕](actual/reused-first-trigger/result.json)、[假首次拒絕](actual/false-first-entry/result.json)
- [reserve不能再花](actual/reserve-not-reused/result.json)、[應收不能當現金](actual/receivable-not-spendable/result.json)、[錯前身停止](actual/wrong-first-predecessor/result.json)

|時點|同一本帳的保存狀態|
|---|---|
|原始1/5|明示假想本金1180；現金1000、C2、現金權利80、另C2股份權利；一般reserve100|
|第一輪1/8結清|B20/C2；現金598.6、應付0、無活單；80與C2權利仍在；當期淨值1178.6|
|第二輪1/9成交|新獨立觸發買B20，累計B40；現金仍598.6、應付401.4、嚴格可用197.2；一般reserve100另留|
|原窗口1/12結清|現金277.2、B40/C4；應收／應付及活單0；原始資本仍1180，當期淨值1177.2|

全部金額／股數／事件是明示合成fixture，不是使用者N、比例或市場策略。兩筆費用及滑價各計一次；80從原權利轉現金，不是新注資。本例價格固定，淨值差只反映假想交易成本，不代表策略好壞。

## 重用方式

第一輪只READ：[原input](../cash_execution_20261028/cases/opening-B20/input.json)、[原actual](../cash_execution_20261028/actual/opening-B20/result.json)。本輪未重新執行第一輪。

第二輪仍是原公開契約：`cash_action.evaluate`由第一輪checkpoint取原帳及latest、保存完整checked_action，再交`cash_action_execution.execute`。不是首次買B：仍用當期review核原有效B-event，但追加必須新獨立B-step2；不能改family、假首次或重用舊事件。完整原opening、fills/order歷史、fact sources、reserve與9個舊token保持，加入3個新token後共12個。原核心／帳務／執行器與策略完全未改。

第二輪有六個**互斥分支**：一個合格B20案例進入simulate一次；五個舊觸發／假首次／reserve不足／應收不足／錯前身案例在simulate前停止，不會一起使用同一筆錢。B25需501.5高於已結扣reserve後498.6；B30需601.6高於已結598.6，即使另有80應收仍拒絕。

## 本輪驗證及範圍

先存契約、每份action-input及獨立expected，再產生checked結果並凍結完整RUN input／來源版本，才執行。4個唯一方法、4次首次全過，只讀新actual作核對，沒有再次RUN第二輪或第一輪。六案不是六個市場樣本，舊7 PASS不累加。

已核原資本與當期淨值分離、第一輪全部逐日prefix全文不變、兩筆fill與原單唯一、精確latest、所有fact sources及token、逐日現金／應付／權利到位與reserve；沒有只拿終點相等當證明。舊數值環境及未來隔離證據沿[上輪報告](../cash_execution_20261028/REPORT.md)重用，產品程式未變，未重跑同類控制。

未新增行情／日曆、1/13、委託生成、多輪自動政策或READ／並列入口；原tape全文相同、原帳窗口不變。活單／期初應付不中斷承接、限售釋放、R2/F、來源認證、完整分叉及真實市場回放仍不擴張。1101 UNKNOWN、70/2/其中8/真實合格0、正式false／主壓力null、來源0.10全部parents及圖形／人工規則保持。

一般工程已由原唯一Codex自審交付，無人工操作或Work例行工程驗收需求。現有兩輪接線沒有必修工程缺口；若要進入真實②案例，需Work與使用者先釐清尚未確認的研究比較輸入與來源證明，不能靠更多合成案例解除市場資格。Work原件／Astra／第一工作區救援原件仍未取得未讀，不要求搬檔。
