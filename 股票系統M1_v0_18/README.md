# 股票系統 M1 v0.18：手機閱讀修正

新增成品：**日週月研究對照_結構標記_v0_18.html**。在日線上顯示原引擎已保存的主要／次級轉折候選，以及支撐／壓力區候選。可點圖或用證據清單查看發生／首次觀察／確認日期與狀態；可切換歷史區域、60／130 筆／全部。

若要同時看 Raw K 線、點及有效色帶，可選 TWSE / 1101 → Raw → 2026-09-30 → structure-0.3-research → 可用週月版本。8069 Raw 該日沒有有效主要區域，顯示 0 是原保存結果；可明選歷史區域。Adjusted 仍不生成還原日 K，只畫保存均線和同錨定結構證據。

標記版與原手機版各已在本環境通過 72 次真實 Chromium JSON 下載核對；新版實體 Android 尚未測試。最新證據見 annotations/validation_20261017/驗收報告.md，顯示邊界見 docs/結構標記顯示契約.md。以下手機閱讀修正說明及歷史驗收狀態保留作沿革。

開啟「日週月研究對照_手機版_v0_18.html」。價格與均線顯示小數兩位；下載保留原始精度。日週月圖按畫面寬度繪製，週月資料期間移到數字下方，缺資料保留原因。舊版 HTML、引擎與保存資料完整保留。

先選 TPEX / 8069 → 原始價候選（Raw）→ 2026-09-30 → structure-0.3-research 日線版本 → 可用週月版本 →「讀取所選對照」。

使用者三張實體 Android 截圖證實舊頁開檔與三圖顯示，另回報可下載。新版實機仍 NOT_TESTED；真實瀏覽器在本環境缺 Chromium 而 BLOCKED。不能把舊頁成功或 Node 檢查套用為新版實機通過。實際檢查見 mobile_viewer/output/手機顯示修正驗收.md。

唯讀匯出與檢查：

```bash
python3 src/cross_view_cli.py --config cross_view/sources.json --html --mobile --output 日週月研究對照_手機版_v0_18.html
python3 mobile_viewer/build_display_oracle.py
node tests/test_mobile_viewer.cjs
```

完整交接、瀏覽器命令與限制見 docs/CODEX交接.md；顯示契約見 docs/手機顯示修正_v0.18.md。原 README、交接、AGENTS 與指紋另存歷史。

這是四檔股票、兩個指定日期的歷史研究原型，沒有即時報價。分類 NOT_VALIDATED、交易資格 NOT_EVALUATED、326 筆覆核 UNREVIEWED；SQLite 原事故根因 NOT_ESTABLISHED。即時全市場、持股、交易價值與部署尚未完成。
