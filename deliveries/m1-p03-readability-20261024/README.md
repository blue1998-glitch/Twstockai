# P0-3用途檢視後的顯示修正版0.2

只改善預設事件可讀性、手機K線區及來源日期／量觀察語義。原核心0.1、1213日／14事件、五份JSON、角色與ID／精度全部保留；不建來源0.11。B88正式price_bounds仍null，顯示改善不代表正式原箱／完整回檔已核定。

## GitHub直接看新圖

|裝置|廣角24月486根|局部31根|
|---|---|---|
|桌面1280|[廣角](images/wide-1280.png)|[局部](images/local-1280.png)|
|手機直向390|[廣角](images/wide-390.png)|[局部](images/local-390.png)|
|手機橫向844|[廣角](images/wide-844.png)|[局部](images/local-844.png)|

- [10/12原突破與返回後不足同時顯示](images/breakout-prefix-390.png)
- [獨立事件列：桌面](images/events-1280.png)／[手機](images/events-390.png)
- [獨立來源日期：桌面](images/source-dates-1280.png)／[手機](images/source-dates-390.png)
- 完整來源日期連主圖：[桌面](images/sources-1280.png)／[直向](images/sources-390.png)／[橫向](images/sources-844.png)

不要求使用者手機搬檔、開終端或架伺服器。PNG是真實Chromium畫面；手機模擬不等Android通過。

## 下載與溯源

- [新自含HTML](artifacts/M1_P03_structure_state_readable_v02.html?raw=true)
- [完整結構JSON](artifacts/structure-state.json)、[chart-layer](artifacts/chart-layer.json)、[facts-input](artifacts/facts-input.json)、[scenario](artifacts/scenario.json)、[角色與來源](artifacts/role-selection.json)：五份與0.1完整bytes相同。
- [離線可重現包](M1_P03_readability_v02_20261024.zip?raw=true)：22,642,782 bytes、81成員／80項manifest。
- ZIP SHA256：`c8adfa7da448619cd9e59eb3b0a8a0c4ac10dd83ad2c6eeaccc85818de8f044a`；[SHA256SUMS](SHA256SUMS)、[實際CRC／全成員／新解壓重建收據](package-verification.json)。
- [本輪顯示契約／完整原碼入口](../../股票系統M1_v0_18/structure_state_chart/READABILITY.md)、[實測](../../股票系統M1_v0_18/structure_state_chart/validation_readability_20261024/驗收報告.md)、[來源及數值保留](../../股票系統M1_v0_18/structure_state_chart/validation_readability_20261024/source-lineage.json)、[完整Work接續指令](WORK_HANDOFF.md)。
- [固定GitHub逐檔原bytes回讀](GITHUB_READBACK.md)／[JSON](GITHUB_READBACK.json)，收據在固定工程後另存，不自指。
- [保留原0.1入口](../m1-p03-structure-state-20261024/README.md)。

本輪6個新Python定向驗收及最終94個新腳本Chromium呈現檢查通過；與歷史65／94不同批，不重跑或相加。ZIP全成員CRC／長度／SHA通過，新解壓同6及建置7輸出完整bytes相同，同6不加總12。首次新節點缺parent的載入失敗與修正留史；中間91／91／94不累加。

## 看什麼差異

先看直向局部與事件列：原突破26.95、返回高26.85、研究下緣20.25不混來源；10/12原突破已記錄，但當日返回後角色尚不可知。10/13整理→14轉強→15整理→16轉強仍是同一條件式研究案例。原state_changed_on沒有改，前情境不足畫面避免拿其最早2021日期冒今日突破日。

390寬plot225→309像素，價格範圍／K／MA／MACD不變；縮放44px按鈕在K／量間獨立空間。按三參照或「狀態與來源證據」沿用抽屜，原價位K／候選末轉折／確認／角色可知／後來選取分欄，量較前筆只作中性觀察。定位、移圖、縮放不改分析日；分析日截止不洩漏未來高點或事件。下載封裝view_version為0.2，結構snapshot仍0.1。

HTML以臨時loopback HTTP實測，未部署網站；file://未重試，Android NOT_TESTED_NEW_BUILD。無新來源GET、數值producer、每日淨帳／六方案或績效。來源0.10全部parent、Raw／UNKNOWN／庫／歷史／原件／舊成品／main及全部舊警告保持。

未完成參照選取品質、全自動完整帶／主壓力、全市場、換股與資金飛輪；公司行動／個人權利／淨分配等來源缺口不解除。execution_qualified=false、imputed_close／valuation=null、historical_signal_eligible=false、primary_pressure_id=null、policy_authorized=false。下一步只Work看新圖用途差異，不重問P0-3、不重抓來源／重試受拒入口，不部署、付費、交易、訊息或子代理。
