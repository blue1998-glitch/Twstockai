# 個股技術分析主圖：technical-chart-view/0.1

此頁優先呈現真實保存日K，重用原 product-context-candidate/0.1 數值，以及 structure-0.3-research 原保存高低點、候選區、事件。新程式只做離線接入／顯示；未改原引擎、參數、共同schema、歷史資料庫或舊頁。不是新交易策略或正式型態分類。

## 可操作範圍

開啟直接顯示1101 Raw、固定保存分析日2026-09-30的近期60根；此入口在成品manifest明列，不是自動搜尋最新行情／版本。可選4檔／6組基底。切股保留確實存在的分析日期，否則使用同一明列入口；沒有Adjusted的1101／2884僅提供Raw。資料不是即時行情。

「最早／全段／回近期」、＋／－、左右按鈕、滑鼠拖曳／滾輪、鍵盤左右，均只改顯示時間窗。手機預設單指捲頁；選「單指移圖／雙指縮放」後可在圖上平移／縮放。K／量／MACD用同一座標函式、同一時間窗與游標；「以游標日回看分析」才改分析時點。選日期、逐日或重播會讀另一份已保存frame，不從當前圖補算策略。專注主圖是頁內顯示，非原生Android全螢幕認證。

高低點畫在發生日，但只讀分析當時已確認的保存pivot，證據分列發生、首次觀察、確認日期。候選區僅從保存建立日畫到失效／分析日；原major／minor是原規則參數組，不當成已認可重要性。預設顯示major、有效候選區，可手動顯示minor與已失效區；這是顯示篩選，未新增參照選取算法。黃色／藍色高低點、區帶及「事／越」事件可點選，或用「圖中證據」按鈕列出；證據顯示原ID、snapshot／source／規則、支持／反面／缺證。收盤事件只疊與當前分析相同有效公司行動基底，其他錨定的歷史需切分析日查看；下載保留所有早於當時的原事件並各自標明基底。

原候選MACD、SMA及投影OHLC離線產生，瀏覽器Number只用於座標及顯示，沒有計算分析條件。成交量刻度以萬／億縮寫避免截斷，游標與JSON仍為股數；沒有二次股／張換算。MACD為12／26／9 SMA種子、柱2×(DIF−DEA)，缺值及Raw公司行動重置沿用原版。新候選Adjusted投影不冒充原store已存的Adjusted OHLC。

## 實際資料與缺口

| 股票 | 保存模式 | 真實日K | 根數 |
|---|---|---|---:|
| 1101 | Raw | 2026-01-02～2026-09-30 | 179 |
| 2884 | Raw | 2026-01-02～2026-09-30 | 179 |
| 6488 | Raw／Adjusted候選 | 2025-08-01～2026-09-30 | 各283 |
| 8069 | Raw／Adjusted候選 | 2025-08-01～2026-09-30 | 各283 |

1101／2884逐月核對18份專案保存的官方STOCK_DAY原回應SHA及全部OHLCV，與保存request一致。各組缺OHLC、缺量、重複日期均0；對專案提供的計畫行事曆＋已覆核例外，缺日／額外日均0。不是完整官方交易日或個股停牌認證。6488／8069舊request未內嵌expected_dates，另用保存TPEX2025／2026行事曆＋例外核對，沒有以空集合當行事曆。

**沒有多年資料，也沒有9/30之後或真實盤中序列。** 原來源涵蓋的1101／2884公司行動UNVERIFIED、另兩檔僅CASH_ONLY_VERIFIED_SAMPLE；公布可得時刻仍未驗證。現有上游ZIP沒有更早年份。不能由1490個分析frame宣稱多年或全市場覆蓋。多年延伸需新增可追溯免費官方歷史月回應／行事曆及公司行動證據，產生獨立候選輸入後再接圖；本輪未作外部抓取。當前雲端網域清單未包含www.twse.com.tw及TPEx資料站，未嘗試繞過或反覆安裝。

## 下載／回看契約

獨立schema：technical-chart-bundle/0.1、technical-chart-selection/0.1；不遷移共同stock-analysis/1.0。JSON包含原完整精度分析前綴、候選OHLC／SMA／MACD、當時完整保存結構、歷史事件及其各自錨定、frame／event／snapshot／source ID、當時前綴覆蓋與限制。移圖不影響下載分析內容；不把整份artifact中可明選的後來行情混入當時數值。

原source／bundle ID是原保存整份資料的來源指紋，可能涵蓋後來日期，僅作出處，不是當時已知資訊的認證。下載歷史事件沒有跨錨定數值合併。整份離線HTML含全部可選frame；畫面／下載只讀所選前綴，不等同保證原來源於當年即已出版。Raw公司行動及Adjusted樣本限制保留。

HTML採可逆chart-interned-json/0.1去重傳輸，保留十進位字串與JSON型別；非數值算法或資料庫架構變更。build檢查全樹roundtrip並拒絕不安全JSON數字；實際成品的全部候選數值與前版candidate.json逐值相同。瀏覽器需支援現代JavaScript與Canvas；舊Android相容性、15MB頁面真機效能尚未驗收。

## 重現（Git checkout）

repository root先跑 `python3 codex/bootstrap_m1.py --hydrate-missing`，保留差異。以下在股票系統M1_v0_18執行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m technical_chart.build \
  --config cross_view/sources.json --output-dir technical_chart/output/rebuild-new
PYTHONDONTWRITEBYTECODE=1 python3 -m technical_chart.verify_artifact \
  --html technical_chart/output/rebuild-new/M1_v0_19_technical_chart.html \
  --config cross_view/sources.json \
  --reference-candidate ../deliveries/m1-v019-context-20261017/candidate.json \
  --report technical_chart/output/rebuild-new/source-verification.json
M1_CHART_DIR="$PWD/technical_chart/output/rebuild-new" \
M1_CHART_BROWSER_OUTPUT_DIR="$PWD/technical_chart/output/browser-new" \
CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium \
  node technical_chart/test_browser.cjs
mkdir -p product_candidate/tmp
TMPDIR="$PWD/product_candidate/tmp" PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -v
```

相同成品重建回報EXISTING；不同成品用新output目錄，不覆蓋原交付。無新套件、API key、持續服務或部署；browser runner啟動自己的私人loopback HTTP服務並結束。完整離線ZIP已有資產，不需bootstrap，舊數值比對檔也位於product_candidate/generated/candidate.json。

實測紀錄見validation_20261017/驗收報告.md。新主圖Android NOT_TESTED；舊假想嘗試頁的PARTIAL_EVIDENCE_OBSERVED是另一份證據，不沿用成新版通過。全市場自動辨識、正式型態／生命階段／重要性、自動左區選取、101／106真實行情認證、交易績效、資金閉環與SQLite原事故根因仍未完成／未證實。
