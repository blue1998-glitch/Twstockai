# 真實跨尺度K線比較 0.1

解壓後開`M1_v019_cross_scale_real_v01.html`，標頭「M1 真實跨尺度比較 0.1」。可直接看真實K線／成交量／原保存MACD，不需要Python、網路資產、CDN或瀏覽器gzip解壓。固定1101／Raw／2026-10-16收27.30，非即時今日。

「跨尺度全景」同看七組證據；「主帶／拒絕串」「39筆／同幾何」「近期／反證」縮近相應脈絡。主圖上方保留對應色彩簡短圖例，詳細勾選在圖下，不把大量文字蓋在K線上。來源外框與填色用所選**完整真實K影線**外包，不是正式壓力界；成交量底色留在量面板，MACD不染色。

＋／−、滾輪、約五年／24月、移圖及返回近期都只改閱讀窗。「拖曳查詢」改游標，「移圖／雙指縮放」才平移；「捲頁」可讓觸控往下捲。逐日選單／前後鍵使用真正保存記錄，不補休市K。K／量／MACD與下方證據日期軸共用x座標、時間窗與游標；單指及雙指沿瀏覽器原生Pointer Events。手機直／橫向都可操作，但這不代表Android實機驗收。

選證據→「定位來源及時點」同看來源末轉折、確認／被拒判定及研究首次界外；「定位來源」只看原段。點時間軸或日期按鈕可查詢當日真實K，不移分析日。○是來源末轉折，◆為確認／被拒判定，▼為首次研究界外，■僅人工已確認整箱終點；後來人工覆核不是歷史當時已知訊號，這不是分析日重播。

## 來源取得與契約

`build.py`只讀固定成品提交57e3d9e55c226c5dd0e69fcbd26883d0da81667e的診斷ZIP，重新核ZIP SHA、8成員CRC／SHA、HTML SHA及1101診斷與保留gzip相等。定向解碼該HTML的1101資料，不需要重建原60前綴或執行任何辨識／MACD引擎。原`graph_core`／參數／資料庫／歷史／舊頁／案例／證據不改。

完整1,213根真實日OHLCV，2021-10-18～2026-10-16；原MACD、SMA、Raw基底、source/frame/prefix與完整原核心結果逐值保留。MACD原檔每列沒有日期，以保存的相同長度／順序綁定K線索引，不替它製造日期欄。價格／MACD顯示約兩位，獨立`comparison-data.json`及下載保留全部原字串精度。新下載schema=`cross-scale-comparison-selection/0.1`，`data`為原值及獨立比較附層，`display`另存閱讀窗／勾選／游標，不覆寫舊JSON。

逐根OHLCV目前沒有空值不等於完整交易日曆；原來源仍列9個待核日期、日曆非窮盡、公司行動及歷史公布可得未核，詳`source-acquisition.json`。不補假K、不新抓行情、不造五年Adjusted、不認證Raw共同校正壓力。

七組圖層的人工日期只讀既有人工audit，原候選及被拒串只讀原核心／診斷ID；不以日期硬編成自動規則。人工月份主帶採原月份內真實交易記錄的**閱讀外包**，463根、兩端漸淡，精確端點與正式價格界仍null；月份首末讀圖日期不是使用者新批准端點。人工39筆保留原4/7～6/2；B44/B80同四來源幾何只畫一組，確認分列5/14與5/27，來源25筆不等39筆。B77左拒高群6.05／容許3.5700／餘量−2.4800，右拒低群3.25／容許2.4675／餘量−0.7825，保持原證人與判定時間。

## 重現

在根目錄按AGENTS重新執行`python3 codex/bootstrap_m1.py --hydrate-missing`，保留既有差異。成功後於`股票系統M1_v0_18/`：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_cross_scale_chart.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m cross_scale_chart.build --output-dir cross_scale_chart/output/new-build
PYTHONDONTWRITEBYTECODE=1 python3 -m cross_scale_chart.verify --artifact-dir cross_scale_chart/output/new-build
M1_CROSS_DIR="$PWD/cross_scale_chart/output/new-build" M1_CROSS_BROWSER_OUT="$PWD/cross_scale_chart/output/new-browser" CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium node cross_scale_chart/test_browser.cjs
PYTHONDONTWRITEBYTECODE=1 python3 -m cross_scale_chart.package --artifact-dir cross_scale_chart/output/new-build --output-dir cross_scale_chart/output/new-package
```

使用新output葉目錄，拒覆寫不同內容。新圖不需新增依賴或常駐服務。HTTP用於本機內部測試，不是網站部署。完整checkout既有來源取得成功另有本輪收據，不把先前Work的NameResolutionError抹除或冒充同環境成功。

## 保留未知

工程圖完成不等主壓力辨識／核心用途獲認可。89候選版本／84幾何組非獨立型態數；同尺度前綴版本、跨尺度同幾何、不同局部串及廣義後來候選分開，直接承接未知。383／349／340／31筆後續窗不同，不能作公平重要性比較。正式區界、量口徑／增量、衰減／強度／重要性、合併、直接承接、生命階段未知；primary_pressure_id=null。B88的10/12～16失敗／重越原事件保留，不升有效突破或持股沉澱。

新Android **NOT_TESTED_NEW_BUILD**；原file://政策不重試不繞過。Raw公司行動／五年Adjusted／歷史可得、資料缺口／Darvas正文／SQLite根因未知保留。五年高不是全史高，日OHLCV不證精確分價／剩餘持股。核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED。不重讀101圖，不重開0.4.3或舊Android按鈕。

[本輪實測、失敗、畫面與範圍](validation_20261020/驗收報告.md)；[成品及完整Work續接](../../deliveries/m1-v019-cross-scale-real-20261020/README.md)。
