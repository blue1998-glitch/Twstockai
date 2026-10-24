# 自動圖形辨識研究主圖 0.1

獨立接入[純數值研究核心](../graph_core/README.md)，不是0.4.4樣式版本，沒有修改原0.4.3或重新驗其底色。主圖的箱、來源轉折、跨尺度關係與事件均來自Python自動輸出；人工案例只在預設折疊的獨立對照，不輸入核心、不冒充準確率。原策略、引擎、庫、歷史、舊頁與私人圖片庫保留。

四股真實保存Raw：1101／2884各1213根、6488／8069各1214根，2021-10-18～2026-10-16；全部K線與查詢保留，SMA／MACD直接沿用凍結數值父檔。只預算每120筆樣本與最近5交易日，共每股15個／全60分析前綴。**回放只播放已計算日期，沒有宣稱全4854日均已辨識**；如需其他日期，在CLI用`--as-of YYYY-MM-DD`追加產生新的獨立成品，UI不補算或寫DB。

## 使用

開`M1_v019_graph_recognition_v01.html`：預設1101／Raw／2026-10-16，收27.30、24月486根。縮放／約五年／平移與逐交易日查詢不改分析日；K量MACD同窗同游標。預設拖曳查詢，選移圖模式可單指移圖／雙指縮放。研究箱選單→聚焦來源或看數值與反證；所有候選可折疊查看／勾選，選擇只改顯示。圖上的虛線是研究價位參照，不宣稱其後全部日K屬於同箱。區域價／量分開、MACD不填色。

預設呈現長時間脈絡、最近上方價帶、較多轉折、近期形成與已越過箱的不同證據；這是UI多樣性選擇，**不是唯一重要性排名**。完整候選與研究Pareto關係仍全部在JSON，primary_pressure_id保持null，缺重要性權重／正式衰減／異常規則時不強迫選魔王。

`graph-recognition-selection/0.1`下載完整原字串、MACD／SMA、source／原numeric frame／basis／prefix、核心版本／參數／反證與後來人工對照。顯示約數／中文事件便於讀圖，不減少JSON精度。歷史公司行動及公布可得仍未核；明示舊事件基底重置後，舊箱保存但不冒充可比當前壓力。

## 重建與測試

根目錄先`python3 codex/bootstrap_m1.py --hydrate-missing`，保留既有差異。以下在`股票系統M1_v0_18/`，使用新的output葉目錄；有不同內容的現有成品拒絕覆寫。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_graph_core.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m graph_core_chart.build --output-dir graph_core_chart/output/my-core
PYTHONDONTWRITEBYTECODE=1 python3 -m graph_core_chart.verify_artifact --html graph_core_chart/output/my-core/M1_v019_graph_recognition_v01.html --oracle graph_core_chart/output/my-core/selection-oracle.json --report graph_core_chart/output/my-core/artifact-verification.json
PYTHONDONTWRITEBYTECODE=1 python3 -m graph_core_chart.evaluate_research --html graph_core_chart/output/my-core/M1_v019_graph_recognition_v01.html --report graph_core_chart/output/my-core/recognition-audit.json
M1_GRAPH_DIR="$PWD/graph_core_chart/output/my-core" M1_GRAPH_BROWSER_OUTPUT_DIR="$PWD/graph_core_chart/output/browser-checks" CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium node graph_core_chart/test_browser.cjs
python3 -m graph_core_chart.package --artifact-dir graph_core_chart/output/my-core --output-dir graph_core_chart/output/package
```

`render_existing`可從核過artifact_id的既算bundle重繪，不重算核心；新HTML仍需核SHA／來源／實際瀏覽器，不能沿用舊HTML測試。Playwright／Chromium沿現有環境，不加常駐服務。下載測試每份間隔700ms，保留首次快速連續下載逾時紀錄，不更改瀏覽器保護。原file://阻擋未重試／繞過。

## 實際證據與辨識缺口

[驗收報告](validation_20261019/驗收報告.md)記實際執行、前綴／反例、全部失敗與未測。[recognition-audit.json](generated/recognition-audit.json)是可由Work直接讀的小型描述報告，含參數敏感度與人工差異，不是accuracy。完整latest核心JSON及HTML在generated；[小ZIP／SHA／遠端收據／完整Work指令](../../deliveries/m1-v019-graph-core-20261019/README.md)。

現行設定對1101產生89箱／171轉折／25個研究前緣；兩尺度自動高點包含1/27／26.95，但到3/4、3/20才確認，不倒灌為1/27已知。10/12、13、14、15、16越過／跌回順序保留。**人工4/7～6/2／39筆沒有精確同起訖的自動匹配；較大月份主帶也尚未完整重現。** 不調參或硬寫日期湊答案、不以這個局部同價匹配宣稱已完成有用的主壓力辨識。候選對設定敏感，沒有訓練模型／準確率／獨立市場測試集或全市場覆蓋。

原已答G1／G2／G3／①④、6/3與6/4原高、1/27及5/13判讀保持，不重問。正式區界、量口徑、增量、強度／衰減、生命階段未定，沉澱／主力／實際剩餘持股不能由箱或低量直接推出。Raw公司行動／五年Adjusted／歷史可得、原資料缺口／Darvas正文／SQLite限制保持。核心用途NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED；**新主圖Android NOT_TESTED_NEW_BUILD**，HTTP模擬不是實機。
