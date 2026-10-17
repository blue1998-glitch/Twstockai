> 最新獨立主圖交付：請讀repository root CONTINUE_IN_WORK_MODE.md最上方及本專案 technical_chart/README.md、technical_chart/validation_20261017/驗收報告.md。新頁technical-chart-view/0.1直接呈現真實日K／量／MACD、導航、原保存證據與JSON。1101／2884僅179根、6488／8069僅283根，無多年或真實盤中。新主圖Android NOT_TESTED；舊嘗試頁PARTIAL_EVIDENCE_OBSERVED獨立保留。原引擎、策略、schema、庫與舊頁不改；下方舊狀態按其歷史時點閱讀。

# 最新：嘗試關卡／量先價獨立候選畫面

本輪依提交45aaeec接入新頁 `M1_v0_19_attempt_candidate.html`，先勾選啟用並明選來源／時點。101／106、量先價／先後未知、盤中／完成日、後來跌回與完整下載分開保存；只接7個假想工程來源，沒有自動選區、真實盤中／完整交易資格。原核心及舊頁／庫／策略不改。命令與使用見 [ATTEMPT_VIEW.md](product_candidate/ATTEMPT_VIEW.md)，本環境325 Python／Chromium87檢查及56下載證據見 [接入驗收](product_candidate/validation_attempt_view_20261017/驗收報告.md)。Android實機未測。

完整離線ZIP的新頁在 `product_candidate/generated/`；Git source先root bootstrap --hydrate-missing，下載入口及下一步見root CONTINUE_IN_WORK_MODE.md。

## 以下為原候選README沿革

# 最新：M1 v0.19 獨立產品候選

專案目錄保留v0.18名稱；最新source在 [product_candidate/README.md](product_candidate/README.md)，實測在 [候選驗收報告](product_candidate/validation_20261017/驗收報告.md)。新頁補逐日上下文／證據鏈、任意時間及價格尺度、原股數成交量與獨立MACD。原引擎／策略／門檻／schema／歷史庫／舊頁保留。生命階段、正式型態及核心用途認可仍未完成，Android實機未測。

Git checkout先在repository root跑 `python3 codex/bootstrap_m1.py --hydrate-missing`，保留修改。完整離線ZIP已附歷史資產，直接進本目錄使用；候選頁在 product_candidate/generated/。最新下載與接續入口見root CONTINUE_IN_WORK_MODE.md。

## 原 v0.18 README

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
