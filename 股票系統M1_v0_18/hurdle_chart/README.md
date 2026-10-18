# 1101人工三關主圖 hurdle-chart-view/0.1

獨立入口：`generated/M1_v0_19_three_hurdles.html`。沿用原壓力主圖的真實日K、成交量、MACD與原有數值；舊pressure_chart、technical_chart、所有引擎／資料庫／歷史HTML不覆寫。新版只有人工案例接入及顯示工程，不是一般自動選關或策略完成。

## 開檔與操作

直接開1101／Raw｜新官方日線／2026-10-16，收27.30、24月486根。上方先列原①26.10與④26.85收盤已過點價，再列使用者後續人工G1 35.50、G2 40.25、G3 50.20。其他日期、來源、基底或股票不套這份三關。

三關來源全在近期窗之外仍保留卡片。卡片說明來源畫外及價位是否在目前價格軸內；G2／G3初始高於軸，不強拉50.20進軸壓扁K線，也不把超軸線假畫在邊界。價格軸只由可見真實K線決定。G1價位雖在近期軸內，來源日期仍在畫外，兩者分開表達。

- 點卡片標題開證據；先讀日期、點價、當前關係、10/18後來人工覆核資格及Raw限制，長ID／JSON預設折疊。
- 點「定位來源」只改瀏覽窗／游標，不改股票、來源、分析日或基底；定位後仍是10/16人工回溯案例。點24月返回近期24月；「回近期」沿用原60根近期窗。證據面板也有「返回近期24月」。
- G3未指定唯一日期，五個同價日全部保留；「定位顯示錨」只是定位最早同價日，不替使用者選唯一日。證據表每個日期可分別定位，不把五日連成正式區間。
- 來源進入視窗且點價在軸內時才畫真實座標點線；點標記可開人工證據。重疊點以畫面最上層者優先，原來源最高價證據仍可由原按鈕獨立查看。
- K／量／MACD共用窗與游標；18／24月、約5年、縮放、拖曳、原覆核及下載保留。原價量來源工具移到圖下，減少圖前文字。

## 契約與計算界線

`manual.py`在離線Python中精確匹配code／price_mode／source_id／analysis_as_of／frame_id／chart_base；核對各來源完整OHLCV、high與日期，G3必須保留全部五個同價日。失配不套；匹配後原始來源不符則拒絕建置。本成品原1490＋新4854，共6344時點中只接入1個人工層。

來源人工JSON `docs/visual-discussion/20261018_1101_selected_hurdles.json`原樣保存。其`product_integration=NOT_IMPLEMENTED`是原覆核時點歷史；新wrapper的`integration_status=EXACT_MANUAL_CASE_DISPLAY_ONLY`記錄本次接入，不回寫原契約。下載新`hurdle-chart-selection/0.1`，增加`manual_hurdles`（其他時點null），保留原選擇全部欄位／小數／事件及原案例。來源指紋包括source、frame、chart_base、前綴、原案例檔SHA及舊手機JSON SHA；舊手機SHA是來源證據，**不是新版下載JSON的SHA**。

新bundle／view／selection另有版本；pressure原schema及歷史下載未改。瀏覽器只渲染準備好的關係／證據，不計算分類、策略、MA、MACD、量或強度。

區界、整區量、增量條件、強度、衰減、自動選關、生命階段未知；不把G3認證為正式魔王。完整五年公司行動／歷史公布可得未核實，未製作五年Adjusted；Raw數字關係不認證已校正共同基底壓力，五年高不等於完整歷史高。TWSE六日主證另有Work補充，但本輪未接入原稽核；TPEX仍待主證。其餘缺口沿用pressure_chart最新交接，SQLite根因未證實。

## 重現

Git checkout先在repository root執行`python3 codex/bootstrap_m1.py --hydrate-missing`，保留原修改。之後在股票系統M1_v0_18：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m hurdle_chart.build \
  --history pressure_chart/data/history-20261018/history-candidate.json \
  --output-dir hurdle_chart/output/rebuild-three-hurdles
PYTHONDONTWRITEBYTECODE=1 python3 -m hurdle_chart.verify_artifact \
  --html hurdle_chart/output/rebuild-three-hurdles/M1_v0_19_three_hurdles.html \
  --history pressure_chart/data/history-20261018/history-candidate.json \
  --oracle hurdle_chart/output/rebuild-three-hurdles/selection-oracle.json \
  --report hurdle_chart/output/rebuild-three-hurdles/source-report.json
M1_HURDLE_DIR="$PWD/hurdle_chart/output/rebuild-three-hurdles" \
M1_HURDLE_BROWSER_OUTPUT_DIR="$PWD/hurdle_chart/output/browser-three-hurdles" \
CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium \
  node hurdle_chart/test_browser.cjs
mkdir -p product_candidate/tmp
TMPDIR="$PWD/product_candidate/tmp" PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -v
```

無新增套件、API key、官方連網抓取或持續服務。輸出只寫新目錄；原成品不覆寫。獨立模板／viewer由壓力頁分支複製，另有manual_viewer.js；原pressure viewer/style及producer只重用不修改。驗收以validation_20261018/驗收報告.md與新Android紀錄為準，舊壓力頁Android部分證據不能算新版通過。
