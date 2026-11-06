# K線範圍價量區域主圖 0.4

新增獨立`candle_region_chart/`，不改0.1／0.2／0.3、引擎、策略、庫、Raw來源、人工原JSON或手機證據。使用凍結0.3數值payload，加獨立`candle_region_extents`；主下載契約`manual-region-chart-selection/0.2`新增`region_display`，原`manual_regions`／`manual_hurdles`及舊數值欄位完整保留。

G2精確2023-01-16～2023-08-16，含136筆真實來源。價圖外框包完整選段影線低35.90(1/17)／高40.25(5/2)，日期邊緣對齊起終日K寬；量圖另框零基線至同段最高保存柱82,247,780股(4/24)。不貫穿MACD，也不由目前畫面最高低取代完整選段。**這些是顯示外包範圍，不是正式壓力價格區界、整區量／量口徑、策略最大量、分價或剩餘持股。** formal price_bounds仍null，原5/2／40.25代表點不變。

G1沿原九月顯示錨至C(2024-01-19)的97筆近似閱讀範圍包影線31.35～35.50；九月上／下緣虛線且左邊未閉合，精確起日／正式歸屬仍未知，2023-09-01只是已保存顯示來源第一筆。不是批准9/1為策略起日或整區計量窗。C後僅開放參照，無封閉價／量框、無固定4/26／4/30終點，不能分類所有後續K線。原11/28高35.50、9/14同高、10/18與11/30來源量峰、①④與G3五日均保留。

縮放／平移只改座標及裁切，完整選段extent固定，不為外框拉伸價軸；真實界線畫外時不貼到畫面邊緣冒充新價位。價框及量框分別clip於各pane，區域覆畫後MACD與pane間隙像素不變。低透明底色／細框不遮K／價格刻度／關卡標籤／縮放鈕。量缺值使量框height未知而不畫假高度，證據顯示資料不足；真0仍是0柱，不混為缺值。

預設拖曳查詢與明選移圖分開，K／量／MACD游標同步；完整OHLCV、跨休市逐交易日前後、24月486與約五年1213、來源證據及草稿均保留。聚焦／查詢／縮放／圖窗不改分析日；明按「以游標日回看分析」才改日。精確source／frame／basis／1101／新Raw／10/16才載入人工與顯示層，較早日期／其他股票或基底不套。草稿只存記憶體，重開／換來源或分析日清空；未提交／批准、逆序不交換、不寫案例。

## 重建與驗證

根目錄依AGENTS先跑`python3 codex/bootstrap_m1.py --hydrate-missing`，保留差異；以下在`股票系統M1_v0_18/`。使用新的output葉目錄，immutable publisher拒絕覆蓋不同內容。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m candle_region_chart.build --output-dir candle_region_chart/output/my-v04
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_candle_region_extents.py -v
PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/product_candidate/tmp" python3 -m unittest discover -s tests -v
python3 -m candle_region_chart.verify_artifact --html candle_region_chart/output/my-v04/M1_v0_19_candle_regions_v04.html --history pressure_chart/data/history-20261018/history-candidate.json --oracle candle_region_chart/output/my-v04/selection-oracle.json --report candle_region_chart/output/my-v04/artifact-verification.json
M1_HURDLE_DIR="$PWD/candle_region_chart/output/my-v04" M1_HURDLE_BROWSER_OUTPUT_DIR="$PWD/candle_region_chart/output/http-checks" CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium node candle_region_chart/test_browser.cjs
M1_HURDLE_DIR="$PWD/candle_region_chart/output/my-v04" M1_LABEL_BROWSER_OUTPUT_DIR="$PWD/candle_region_chart/output/label-checks" CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium node candle_region_chart/test_labels.cjs
M1_HURDLE_DIR="$PWD/candle_region_chart/output/my-v04" M1_REGION_BROWSER_OUTPUT_DIR="$PWD/candle_region_chart/output/region-checks" CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium node candle_region_chart/test_regions.cjs
M1_HURDLE_DIR="$PWD/candle_region_chart/output/my-v04" M1_EXTENT_BROWSER_OUTPUT_DIR="$PWD/candle_region_chart/output/extent-checks" CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium node candle_region_chart/test_extent_browser.cjs
python3 -m candle_region_chart.package --html candle_region_chart/output/my-v04/M1_v0_19_candle_regions_v04.html --output-dir candle_region_chart/output/package-v04
```

Playwright／Chromium沿環境現有安裝，無新增依賴或常駐服務。`extents.py`用Decimal比較並保留原字串／來源日期／選段指紋；`build.py`只加獨立顯示層；JS讀prepared extent作座標映射和各pane裁切，不算指標／策略／窗口extrema。最終成品、測試與實際前後畫面見[驗收報告](validation_20261019/驗收報告.md)、[小ZIP／SHA／完整Work指令](../../deliveries/m1-v019-candle-regions-v04-20261019/README.md)。

## 狀態與限制

本版Android **NOT_TESTED_NEW_BUILD**；舊0.3-family兩張新手機圖是PARTIAL_EVIDENCE_OBSERVED_VERSION_UNCONFIRMED（頁頂版號／1101未入鏡、無新JSON），不是完整通過。原圖與0.2部分證據保留，不重索同檔；Work只驗0.4新外框差異。HTTP真實Chromium不當Android或file開檔成功；原file://管理政策阻擋未重試／未繞過。

G1精確起日、價格區界、整區量／量口徑、增量、自動分區／選關、強度／衰減及生命階段未定，不新增門檻。UI更正不是核心用途認可（NOT_ESTABLISHED／NOT_VALIDATED／NOT_EVALUATED）。Raw完整公司行動／五年Adjusted／歷史公布可得、TWSE六日補證尚未接入原稽核／TPEx主證及零量缺價等原資料缺口、SQLite未知根因不變；Raw舊高不認證共同校正壓力，五年高不是完整歷史高。Darvas箱型正文未完整讀，沒有採入其規則。
