# 後續獨立三關版本入口（2026-10-18）

1101新Raw／10/16人工G1 35.50、G2 40.25、G3 50.20已接入**新**hurdle_chart/，請讀[新版契約](../hurdle_chart/README.md)與root最新交接。舊pressure_chart程式、generated HTML及下方原0.1契約保留。新版Android另開NOT_TESTED_NEW_BUILD，原pressure頁部分實機證據不沿用；這個入口更新不代表改動原數值／策略或批准自動選關。

---

# 左側壓力主圖 pressure-chart-view/0.1

本輪接續指定a3a58d4972d1efb5da8196e83954be574b0670c9，新增獨立主圖、官方歷史接入與描述事實候選，原technical_chart／product_candidate／src、策略參數、共同schema、所有舊庫及頁面未改。全市場自動辨識、正式高牆／魔王選取與交易價值不是本輪完成項。

## 使用入口

開啟generated/M1_v0_19_pressure_chart.html，直接顯示1101、新官方Raw、固定收集截止日2026-10-16，預設24日曆月的**日K**。不是即時行情。10組來源可選：4檔新Raw五年候選，加原6組保存Raw／Adjusted；原Adjusted仍僅舊樣本，不冒充五年還原資料。切來源／分析日是明選；不能把新Raw與舊Adjusted跨基底混比。

18月／24月／約5年、左右、全段、最早及回近期只改顯示時間窗；K／量／MACD共用軸與游標。縮小仍畫逐根日K，不換成週K。單指預設捲頁，切「單指移圖／雙指縮放」後可操作圖。＋／−在K面板右下角，44×44觸控區另留空間，不覆蓋價格軸、K或標記；圖例與縮放點擊不移動分析日或誤觸游標。

「價牆依據」列全段當時已供左側最高high，「量牆依據」列全段已供最高日量；來源在畫外仍提示並可定位。它們是兩種來源事實，不是最高價／最高量自動等於正式高牆，更不是單一強度總分。所有月份來源片段都保留，不按最近N日剔除老區；年代、量價與後續路徑各自保存，時間衰減與異常門檻為未知。最高區可稱魔王是使用者思想，但正式區域未選定時不自動加魔王標籤。

## 四檔真實資料與價格基底

| 股票 | 新Raw日K | 根數 | 官方月回應 |
|---|---|---:|---:|
| 1101 | 2021-10-18～2026-10-16 | 1213 | 61 |
| 2884 | 2021-10-18～2026-10-16 | 1213 | 61 |
| 6488 | 2021-10-18～2026-10-16 | 1214 | 61 |
| 8069 | 2021-10-18～2026-10-16 | 1214 | 61 |

收集目標2021-10-16～2026-10-16；起點週末，第一個供應價格日10/18。244份原回應＋metadata保存在data/history-20261018/raw，每份有官方URL、抓取UTC時間、SHA；身分、月份、欄位與量單位皆驗證。TWSE原生股數不乘1000；TPEX較舊「成交仟股」及較新「成交張數」分辨原欄位後乘1000，保留其來源精度，不假裝還原精細至每一股。新來源正規化schema獨立，不新增或遷移stock-analysis/1.0的volume_unit。

新Raw數列逐一核對所有原保存來源日OHLCV，數字有衝突即拒絕，不覆寫舊結果。新MA直接呼叫未改的moving_averages.curves，MACD呼叫未改的product_candidate.macd，版本與精度沿用；Raw MACD只依保留的已知樣本事件重置。**新五年沒有再算原價格結構引擎**，空的結構／正式型態保留未知，不偽造原庫snapshot；新source/frame及原保存來源各自標示。

12份官方計畫年曆（兩交易所×2021～2026）在data/calendars-20261018。完整性不能只由月檔齊全推論：[最終日期稽核](data/history-20261018/coverage-audit.json) 才是缺漏主表。與初步known_calendar_missing_dates不同之處，有明確原文依據：TWSE2022/1/27、1/28僅結算無交易；2023/1/17是最後交易日，說明欄另指1/18、1/19無交易，不能將1/17誤刪。

仍需原始臨時休市／個股停牌證據的6日期：2023-08-03、2024-07-24、2024-07-25、2024-10-02、2024-10-03、2024-10-31。不因四股同時沒資料就自動認證休市。1101的2025-08-13、2884的2025-11-05，原回應各有成交0且OHLC全為「--」，保留原列／SHA，沒有生成0價K或補前收。最終計畫日曆意外價格日0；來源月檔齊全不等於完整官方交易日／個股停牌認證。

[公司行動證據清單](data/history-20261018/company-action-evidence.json) 保存原已知樣本（6488兩筆、8069一筆）、官方原欄位的12個待查提示；提示不是已核實除權息事件，沒有推導還原因子。**五年公司行動與歷史公布時間仍未完整驗證，未製作五年Adjusted**。依AGENTS沒有重試先前明確安全拒絕的TWSE除權息端點。Raw跨年舊高與下跌數字不等於已調整共同基底壓力或經濟報酬。

只有這五年，不能宣稱完整上市歷史新高或五年前沒有更高套牢區；上市首日也未由「無資料」推論。

## 區間量價與下跌證據

來源區間選單提供**明示的月份來源容器**；不是系統已認定整理區邊界。初始／末月可為目標裁切的片段，點開列actual_start／actual_end。區間提供原日列、真實high／low及日期、已供日列總量、最高日量與日期、離開來源後經過日曆日／供應K數、到其後最低low所用時間、最大供應收盤對收盤跌幅、完整逐日OHLCV路徑。

區間總量與最高日量分名；若區間有量缺值，總量與確定最高量均未知，部分已知總量／最高量另名保存，不能當確定基準。量是歷史換手，不是精確仍未解套持股，也沒有日OHLCV推導分價籌碼。急跌／整理緩跌、下跌強度方向、重要性、衰減／異常門檻及剩餘持股比例都未定，不補分數。

每日分析都有當時全段價量事實；為控制離線手機檔大小，**月份詳表只匯出各月最後供應日及本次截止日**。其他分析日明示未匯出，不讀後來明細；逐日OHLCV、SMA／MACD及全段最高high／最高日量仍可用。CLI可用--regions明選具體來源區間，格式為陣列，每筆id、code、price_mode、basis_id、start、end；基底須來自對應下載，來源選擇不是正式策略批准。

來源區間的已收盤越其high／之後跌回另存事件ID；仍開放中的月份不回填固定上緣事件。不把日期分組當正式型態，也不以原引擎兩日失效條件改寫使用者已定的逐日價格事實。

## 1101①→④與之後真實資料

「1101原覆核①→④」精確開原Raw／9/30／原source／snapshot，與docs/visual-discussion/20261018_1101_user_reviewed_case.json逐值核對：只突出①與④，②③保留背景。①26.10與④26.85是原pivot點價；1/27真實high26.95另列，不把26.85說成全區上緣。

新Raw來源逐日等值核對原179日後，另連結這份原覆核，提供9/30之後到所選日的真實OHLCV，保留兩點的原收盤越過及之後跌回事件。增量基準／門檻／持續時間仍null，9/23不能取代9/30之後資料，最高量也不自動當增量硬門檻。

**覆核時間10/18晚於原分析9/30及新資料截止10/16**，故畫面及JSON明示回溯人工註記／追蹤，不能冒充當時已自動選出的重要性或回測訊號。原案例契約與當時缺證狀態未回寫。其他股票及9/30之前不套本例；來源日／snapshot不符會拒絕或不顯示。

## 下載與版本

pressure-chart-bundle/0.1、pressure-chart-selection/0.1、left-pressure-source-facts/0.1、official-history-candidate/0.1、official-raw-indicator-selection/0.1是獨立候選。原數值bundle逐值全等；沒有共同schema遷移。下載分開saved_analysis與new_history_analysis，後者original_record_id=null，明示未寫舊庫。保留精度、原量單位、日期、全段當時前綴、來源ID、原事件及回溯註記；UI不計算策略、MA、MACD、區間量、強度或關卡條件。

移圖不改分析或JSON；「以游標日回看分析」才換前綴。整份HTML含可明選的後來資料，當前數字只取當時前綴；整檔source指紋／抓取時間是出處，不是歷史可得認證。JSON傳輸重用可逆去重樹，沒有把小數或來源股數轉成不安全JS數字；Number僅座標與顯示。

## 重現

Git checkout先在repository root `python3 codex/bootstrap_m1.py --hydrate-missing` 保留差異；完整離線三包已有資產，不需bootstrap。以下在股票系統M1_v0_18：

```bash
# 既有官方證據可離線驗證；不必重新連網抓244份。
PYTHONDONTWRITEBYTECODE=1 python3 -m pressure_chart.build \
  --history pressure_chart/data/history-20261018/history-candidate.json \
  --output-dir pressure_chart/output/rebuild-new
PYTHONDONTWRITEBYTECODE=1 python3 -m pressure_chart.verify_artifact \
  --html pressure_chart/output/rebuild-new/M1_v0_19_pressure_chart.html \
  --history pressure_chart/data/history-20261018/history-candidate.json \
  --report pressure_chart/output/rebuild-new/source-report.json
M1_PRESSURE_DIR="$PWD/pressure_chart/output/rebuild-new" \
M1_PRESSURE_BROWSER_OUTPUT_DIR="$PWD/pressure_chart/output/browser-new" \
CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium \
  node pressure_chart/test_browser.cjs
mkdir -p product_candidate/tmp
TMPDIR="$PWD/product_candidate/tmp" PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -v
```

重新取得資料才明確執行history命令，先核對當時環境網路與已收盤日期：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pressure_chart.history \
  --start 2021-10-16 --end 2026-10-16 \
  --cache pressure_chart/data/history-20261018 \
  --calendars pressure_chart/data/calendars-20261018 \
  --output-dir pressure_chart/output/intake-new --fetch
```

建立新目錄；原回應與SHA逐份重用，若增補月才連網，請求間隔3秒。被拒絕的host當輪停止，不繞路；來源欄位不符另記，不造價。歷史端點／新公司行動仍需按實際錯誤診斷。重建相同成品回報EXISTING；不同成品用新output版本，所有驗證報告同樣防覆寫。

實測見validation_20261018/驗收報告.md；此新頁Android NOT_TESTED。原technical-chart-view/0.1的PARTIAL_EVIDENCE_OBSERVED與舊attempt證據分開保存。分類NOT_VALIDATED／交易NOT_EVALUATED；全市場、正式型態／生命階段、重要性與資金閉環未完成，SQLite原事故根因未證實。
