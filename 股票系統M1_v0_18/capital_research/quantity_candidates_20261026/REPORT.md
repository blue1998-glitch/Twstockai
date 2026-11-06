# 分批換股數量候選0.1：功能里程碑交付

本輪已完成可重用純API `capital_research.quantity_candidates.generate(request)`。在明示有限整股域完整列舉A保留量／B新增量，另列續抱、退A留現金及原full_transfer端點；其他資產／權利不變。每個候選沿現行0.8可行性及跨輪歷史／token接線，輸出當期可行、等待交割重評、拒絕或未支援。無最佳比例、批數、固定天數、策略勝者、委託或成交。

## 實際使用與證據

先讀CONTRACT，再以已準備的明示合成request呼叫generate。所有數量／參數來源都要在request明示；部分域步長1，硬上限1024格，full_transfer沿原20000搜索界線。沒有預設交易比例。一般輸入合法域不會只列前綴冒充完整；超限候選空、enumeration_complete=false。

保存輸入／預期在 `cases/案名/input.json`、`expected.json`；修前actual同目錄留史。**最終source結果只看 `after-final/案名/actual.json`**、`after-final/summary.json`，與source-versions-final.json綁定。READ直接讀JSON，不import或呼叫生成器重算。build已執行且已有輸出，再執行會拒絕；新研究版本另存目錄。

合法例 `legal-grid`：A保留98～100股、B新增0～2股共9格，並加現金／全換端點。所有候選保留C實股2股，以及同一帳戶的100元一般reserve、80元應收及10股A待交權利。A99/B1是當期可行部分換股；這不是其數量最佳或未來獲利證明。

|能力／反例|最終保存位置及判斷|
|---|---|
|合法域與全換重用|after-final/legal-grid：完整9格，續抱／減碼／部分／全換端點；full_transfer只提案，返回後重新沿目前0.8／歷史查核，新增B固定family C|
|同事件／共柱不得重複觸發|consumed-trigger、shared-volume-trigger：所有新增買進拒絕。共用token只判相依，不合併事實身分|
|觸發不能借股或借未來資料|foreign-trigger、future-foreign-ownership：本股已知前綴不足即拒絕；future案例research與foreign-trigger完全相同|
|失效與未知|unknown-capital、invalidated-fact、history-revocation-not-erased：新增B拒絕；最後一案即使當期刪撤銷，仍由原checkpoint來源重建限制|
|有效舊事實與獨立新事實|review-old-valid：舊B-event可接受當期review，但不是新批觸發；review-independent-new加入真正獨立token後可提出新買進，不強迫所有舊事實變新事件|
|資金與保留額|reserve-insufficient：101已結現金減100一般reserve只剩1，A100/B1拒絕，不吃80應收或待交股份；wait-settlement的A95/B1明示WAIT_SETTLEMENT_REASSESSMENT|
|部分成交／交付不是新觸發|after-fill-no-new-event保留原兩筆部分fill與同日明示撤銷剩餘單；after-settlement-no-new-event現金1080、原待交股份已交付，兩者仍不能用舊事件批准新買進|
|非單調可行集合|non-monotone：固定A100，B=0拒絕、1與2可行、3拒絕；完整保留中間可行格，不用二分或首拒即停。超限A-zero不列可行組|
|兩種搜索超限|grid-over-limit與full-over-limit：REFUSED_SEARCH_LIMIT／候選空／完整性false，不抽樣|
|未支援|existing-order-full-unsupported：原full builder有外部既有單時NOT_IMPLEMENTED；其他0.8可檢查意圖仍保留。信用入口仍NOT_IMPLEMENTED|
|一般未來尾段隔離|future-A-wins／future-B-wins／future-both-fall的整個research與legal-grid相同；外層source_integrity_metadata按完整原件不同而不同|

## 實作過程與失敗留史

先保存CONTRACT／fixture來源版本；準備跨輪fixture時被既有「所有未成交單須明示取消」擋住，見preparation-diagnostic.json及diagnostics/prefix-before-explicit-cancellation.json。只補合成輸入的同日撤單宣告；原防線不改，也沒有更改已保存oracle。最終四個prefix在prefixes/；它們是既有0.8合成帳務來源，不是本生成器建立的委託／成交。

20組新input／expected先凍結，generator當時尚不存在。首次執行20案，shared-volume-trigger不符合預期：同時點ID排序讓別名先取得novel資格。自審另發現使用raw evidence ID核本股，可能借用未來B列給當期A觸發；先新增future-foreign-ownership的input／expected，再以修前source重現放行。修前原碼／build／測試／契約在diagnostics/，修前actual／log原樣保留。

最小修復限新生成器：本股只取既有0.8已知layer1；若所選觸發與當期B資金review依賴的另一已知事實共用既有token，拒絕作獨立新觸發。沒有改0.8 fact_lineage／eligibility、帳務、門檻或oracle。新增買進始終family C；原始decision_input.plans不能插入其他family逃生方案。

source有實際變更，故只重跑本輪定向域並另存after-final，統一綁最終source。最終21案例全符合原oracle，**18個必要方法一次全部PASS**；方法重用保存actual，不把21案例或首20／修前反例累加成方法數。另有少量必要純API／既有core等價檢查，不是舊suite重跑。方法內格式／注入變體只有測試原碼及log，不冒完整逐案actual。沒有為更多PASS重跑同一未變集合。

## 自審與額外複核項

本里程碑由原唯一Codex完成自審，不預設另轉Work。額外複核聚焦資金／權利／未來資訊接線：所有數量從同一完整account出發；目標只動A/B；其他資產、現金／股份權利、reserve由原0.8讀取；續接精確latest／原始資本／全部token，不能以本輪baseline剛review的token反灌同輪競爭候選。每個候選是互斥替代方案，不是同時下單。計算只產生數量意圖，不新增會計或執行路徑。

兩項新增batch防線均有修前反例及修後actual。當期可行依舊不能保證途中風險、可退出、漲跌停成交、交割到款；靜態scenario_values／Pareto仍非政策支配。full_transfer端點無可新增B時可與退A留現金同目標合併，不能稱已換入B。完整性只指明示有限域及清楚標示的端點，不是所有可能資產或最適解。

消費端額外複核要求：`core_evaluation`保留原0.8對照，不含本輪額外batch gate；最終須讀候選外層`classification`、`feasible_for_research`及`batch_gate_reasons`。共柱別名等案例可能原core可行而外層拒絕，不能只抽內層core的feasible或plan當成已批准。`WAIT_SETTLEMENT_REASSESSMENT`也不能當CURRENTLY_FEASIBLE使用。本輪沒有執行消費端，所以不宣稱執行器已整合此新gate。

自審結果見self-review.json、preservation.json及CHANGE_MANIFEST；舊原碼／catalog／oracle／actual／log不變。根AGENTS／CONTINUE已整合使用者功能里程碑、自審與正常保存授權；capital_research README只加功能入口，沒有平行工作規則。

## 未實作／未執行及下一步

未實作：自動批次數量選擇、最佳比例／策略、訂單產生與新批執行接線、政策成效評比、R2/F、信用、來源認證及原未支援帳務。既有任意外部plan API沒有被改成全域策略／來源防偽引擎；本生成器不提供family覆寫。

未執行：bootstrap/hydrate、舊整套suite、九路徑競爭、真實producer／資格重算、市場績效、UI／Android及樣本外；沒有私人資料或公開來源新擷取。1101 2026-01-02期初cash_claims仍帳戶證據阻塞、UNKNOWN與拒算，不搜尋公開來源補此缺口。70／2／其中8／真實總淨合格0、全部正式false／主壓力null、來源0.10及parents、正式action_resolution0.4與圖形／人工契約保持。Astra及救援原件未取得未讀，不推定890檔存亡。

下一項建議（未自動啟動）：把數量候選接到既有逐輪合成回放，集中檢查等待／部分成交後的重評；仍不選最佳比例或預定策略勝者。沒有人工搬檔、提供私人文件或修程式需求。
