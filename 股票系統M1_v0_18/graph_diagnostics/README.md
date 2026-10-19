# 圖形辨識追溯診斷 0.1

本版只解釋凍結的 `graph-recognition-research/0.1`，不修訂辨識規則或原結果。`diagnose(payload, result)`為純數值附層：先驗來源／基底／前綴及result指紋、重現已確認轉折，再逐串核原`_range`，逐筆核原`_boxes`產生順序與ID；不一致即拒絕。人工案例不得輸入。不把可追溯診斷當成整體主壓力已辨識完成。

下載ZIP後解壓開`M1_v019_graph_diagnostics_v01.html`，標頭「M1 圖形辨識追溯診斷 0.1」。原固定1101／Raw／2026-10-16收27.30，非即時行情。不需執行Python才能看成品。

## 可追溯內容

- 原算法每次新轉折確認時實際檢查的全部同段後綴串：檢查當時、全部適用失敗條件、首個失敗、數值餘量、極值來源證人；通過幾何但未選最長／四轉折種子另列。不是只列成功箱，也不是所有任意日線區間的窮舉。
- `source_turn_slice`指向`enumeration_scope.source_turn_sequences`同scale/segment序列的含端點start/end。可還原完整原轉折ID，不重複保存每串長ID陣列。不存在轉折的任意日／月端點**未被枚舉**，不能說該日被幾何拒絕。原ambiguities／pending資格保留。
- 同尺度、同段、精確來源ID前綴延長，方向只向後來確認時間。嚴格局部子串另列。跨尺度同幾何以完整有序發生日期／種類／價位／同價來源日相同為準，排除確認時間與尺度；關係首次可觀察日取兩者確認較晚者。這些只分辨來源關係，不定義正式合併、獨立經濟型態數或成功票數。
- source末轉折、確認、首次研究界外收盤、前一筆觀察記錄、研究破底與正式整箱終點分開。形成時已在外，前一筆已觀察inside記錄為null，並解釋舊`first_departure_range_end`會clamp到形成日。人工終點不輸入本核心；後來人工資格只留原外部audit。
- 來源量窗、前等筆數量窗、確認到分析日或缺口的後續觀察窗、最大跌幅所用完整窗及到最低的筆數分列。每個事件與錨的前1／5／20筆量比較保留實際窗口／缺量／排除當日資格。不同箱後續長度不同，不補時間權重、不把下跌幅直接認成公平重要性。
- 原`successor_after_breakdown_ids`保留不改，附層改稱「破底後廣義後來候選」，逐個列來源起日、確認及關係可知時間；`direct_successor_id=null`，不由時間先後推直接承接。幾何parent也不當人工意義階層。
- 原UI多樣性五條選擇條件、eligible／winner／穩定同值順序、每箱未選及原研究支配者均保留。預設未顯示不等引擎漏檢，未改原呈現集合或Pareto比較。

## 成品與重現

先按根AGENTS在完整checkout實跑`python3 codex/bootstrap_m1.py --hydrate-missing`。下列命令在`股票系統M1_v0_18/`執行；使用新output葉目錄，不覆寫舊成品。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_graph*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m graph_diagnostics.build --output-dir graph_diagnostics/output/my-build
PYTHONDONTWRITEBYTECODE=1 python3 -m graph_diagnostics.verify --html graph_diagnostics/output/my-build/M1_v019_graph_diagnostics_v01.html --oracle graph_diagnostics/output/my-build/selection-oracle.json --report graph_diagnostics/output/my-build/artifact-verification.json
M1_DIAG_DIR="$PWD/graph_diagnostics/output/my-build" M1_DIAG_BROWSER_OUT="$PWD/graph_diagnostics/output/my-browser" CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium node graph_diagnostics/test_browser.cjs
```

從保留的原0.1 HTML核SHA後讀取同一60前綴，不把舊ZIP當最新checkout。4854根OHLCV／SMA／MACD／來源frame／原核心／人工audit／預設呈現全部逐值不變。新HTML以gzip＋原lossless interned JSON內嵌，瀏覽器原生DecompressionStream解壓，無CDN或分析補算；沒有這個瀏覽器能力時顯示明確載入失敗，不偽填成功。下載`graph-diagnostic-selection/0.1`保留原core，新增diagnostics，原0.1 schema與產物不變。

完整latest診斷JSON於小ZIP內，Git的generated採`diagnostics-股票代碼-latest.json.gz`存放以免重複大文字；`DIAGNOSTIC_GZIP_VERIFICATION.json`列解壓前後精確SHA。可用Python標準庫`gzip.decompress(Path(...).read_bytes())`讀原JSON。Work優先讀小型`generated/review-diagnostics.json`，再定位全來源。`refresh_view`可保留封包逐位元重繪文字；`verify_render`核前輪真正重算報告、封包與目前顯示原碼，不將這一步誤稱再次重算核心。每份HTML仍須實際HTTP檢查。

開「追溯診斷」→選原候選→讀日期／窗口／版本關係。切換「同末轉折的所有起點」或「同起點的後來末轉折」，選被拒或未選串→「看此串與原候選」。黃色虛線只標該實際診斷串的原K影線外包，原箱保留；可放大、平移、逐日查詢、24月返回，不移分析日。不是正式箱／新自動訊號。

最新已算分析日仍每股15個，共60；查詢所有真實K不等每日均已分析。數值、畫面與Android資格分開；新Android NOT_TESTED_NEW_BUILD，file://政策不重試不繞過。原101圖片／0.4.3／舊按鈕驗收不重開。正式成員／區界、整區量／增量、重要性／衰減／生命階段與Raw公司行動／五年Adjusted／歷史公布可得／原資料缺口／Darvas正文／SQLite未知全保留。核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED。

本輪實際數字／失敗及畫面見[驗收報告](validation_20261019/驗收報告.md)，[新交付及完整Work指令](../../deliveries/m1-v019-graph-diagnostics-20261019/README.md)。
