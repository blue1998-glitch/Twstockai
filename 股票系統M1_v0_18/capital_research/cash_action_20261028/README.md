# 原現金／退出後原帳：明示行動接線0.1

新增可用能力是 `capital_research.cash_action.evaluate(request)`：即使A已為0，也可沿原帳檢查一項明示HOLD或現金買進意圖。沒有重做quantity_candidates，也不重新生成候選、選股數、建單、成交或修改預留。

- [白話報告](REPORT.md)、[事前契約](CONTRACT.md)
- [最終31案摘要](after-final/summary.json)、[7個唯一方法log](tests-first.log)
- [原A仍在，用原現金買B](after-final/actual/original-cash-no-sale-A/result.json)
- [退出A後，原已結現金足夠的小額B意圖](after-final/actual/exit-unsettled-first-B-small/result.json)
- [應收尚未到位，較大B意圖拒絕](after-final/actual/receivable-not-buying-power/result.json)
- [到位後同較大B意圖](after-final/actual/settled-larger-B/result.json)
- [新觸發重入A](after-final/actual/reentry-independent-A/result.json)、[舊觸發拒絕](after-final/actual/reentry-old-trigger/result.json)
- [假稱首次：core雖可行，外層拒絕且candidate_ids空](after-final/actual/false-first-after-exit/result.json)
- [未來prefix／數值環境](test-evidence/prefix-context.json)、[純呼叫](test-evidence/pure.json)
- [初版手算勘誤及自審留史](diagnostics/pretest-self-review.md)

|明示意圖／狀態|保存結果|不能由此推定|
|---|---|---|
|A100仍在，現金1000／reserve100，買B20|合成候選可行，A仍100；預估支出401.4|已賣A籌資、B已成交|
|賣A100後未交割，現金1000／reserve100，買B60|拒絕，995應收不進可用額|賣出即有現金|
|原款到位，現金2075／reserve100，買B60|同原帳候選可行，原資本2180|重設本金2075、保證後續成交|
|A已退出，續用已消耗A-event|拒絕|零持股就是首次入場|
|A新獨立事實，當期資格通過|可檢查重入A20意圖，原權利及token保持|批准策略或免除重入成本|
|活單／期初應付／未知資格|未支援或拒絕|已取消／已結清／補零|

這些數字全是明示假想fixture，不是使用者本金或本例1101／2884股數。未新增②RAW來源、6488、市場回放或績效。新API限定synthetic研究，不能把真實RAW改標合成繞資格。

輸入為 `capital-cash-action-input/0.1`。以[完整原現金案例input](cases/original-cash-no-sale-A/input.json)示範：外部載入後呼叫 `evaluate(request)` 即得結果；入口內無IO。source為明示合成opening或完整checkpoint，不能覆寫account/plans/tokens。checkpoint續接自行核ledger／daily-close及latest，並取得原帳；來源／基底不變。HOLD保留全帳權利；指定A已退出也不冒稱其他C持股或權利為0。

新結果的`research`只放當時決策、行動資格與原帳綁定；完整原始`derived_decision_input`及core source metadata放`source_integrity_metadata`，不把尚未可知撤銷混入數值前綴。外層`research_recommendation.candidate_ids`只列本入口通過的意圖；保留的`core_decision`是原引擎診斷，不能跳過batch_gate_reasons直接當批准。所有正式資格false、primary_pressure_id=null、selected_id/ranking=null。

## 本輪實際驗證與未支援

先保存4個合成precondition job及手算預期，再用原引擎建fixture checkpoint；這是合成準備，非市場回放。再凍結31份完整action input/expected及版本，才實作。初版及after-final actual分存，oracle不覆寫。7個唯一方法首次全過；31案及4個準備不是新增市場樣本或35項測試，不加歷史PASS。最終source以after-final/source-versions.json為準。

新行動RUN沒有simulate／quantity generation／市場回放；checkpoint核對仍必須呼叫原ledger，不能稱帳務呼叫0。純opening呼叫的IO／網路／帳務／執行器阻擋控制通過。兩個新邊界另存於test-evidence：缺token／改opening拒絕、close到18:00才可知則17:00不能用。測試沒有重新執行舊suite或九路徑。

本輪只做**行動候選檢查**。尚未新增八行動完整dispatcher、賣A再買B的協調回放、整張數量域、現金入口接quantity回放、外部活單／期初應付完整重播、R2/F或來源認證。無市場績效／策略結論。1101帳戶證明缺口、來源0.10與全部parents、70/2/其中8/真實合格0及原圖形／人工規則皆保持。

一般工程由原唯一Codex自審及原分支正常保存。重大複核項集中於本里程碑：原帳／完整權利、預留／交割、latest／全部token、首次與新批分離、未來可知時間。不預設轉Work逐輪驗收。Work只需處理未定本金N／比例／政策／風險取捨，無需使用者下載或搬檔。
