# 分批換股數量候選：入口

純API：`from capital_research.quantity_candidates import generate`，以CONTRACT.md的完整request呼叫`generate(request)`。不依賴網頁、檔案、網路或資料庫；既有0.8核心負責全部數值可行性與原帳checkpoint查核。

結果只作研究意圖。務必以外層候選`classification`與`feasible_for_research`判讀；內層`core_evaluation`是0.8原始對照，不能略過新增batch gate。當期可行也不是建單批准；待交割重評、拒絕與未支援分開列。沒有可執行訂單、最佳比例或勝者。

只讀成果：REPORT.md、CONTRACT.md、cases/*/{input,expected}.json、after-final/*/actual.json、after-final/summary.json、tests-final.log、self-review.json。cases/*/actual.json及根summary.json／build.log是修前中間階段，原樣保留，不能當最終source結果。

修前source快照在diagnostics/；完整oracle指紋在intake.json與additional-cases.json。source-versions-final.json綁最終程式／fixture／契約／測試版本；文件／自審／manifest於驗證後另存。不能把現行source拿去覆寫修前actual。

build已完成，重跑會拒絕覆寫。一般閱讀不執行build或測試。原instruction與來源歷史保留；目前工作方式只沿根AGENTS／CONTINUE，沒有另一套工作規則。正式市場／私人權利／來源認證不足與原未支援帳務不由本功能解除。
