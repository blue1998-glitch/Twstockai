# 明示研究帶最大量對照｜沿P0-3主圖增量接線

只重用既有段量統計，補來源／時間／完整成員資格及主圖、精確JSON接線；不重寫最大量算法、不重跑graph_core／P0-3／指標或人工模式路由。原五JSON、狀態／事件／ID、全部舊成品保持，不是來源0.11。

## 直接看圖

|裝置|廣角24月486根|局部31根|
|---|---|---|
|桌面1280|[廣角](images/wide-1280.png)|[局部](images/local-1280.png)|
|手機直向390|[廣角](images/wide-390.png)|[局部](images/local-390.png)|
|手機橫向844|[廣角](images/wide-844.png)|[局部](images/local-844.png)|

[確認前不露完整參照、保留廣角](images/not-yet-known-390.png)；原量K／候選確認／後來選取：[桌面證據](images/source-evidence-1280.png)、[直向證據](images/source-evidence-390.png)、[橫向證據](images/source-evidence-844.png)。全部真實Chromium新畫面，手機模擬不是Android；不要求使用者手機搬檔、開終端或架伺服器。

## 本次真實對照

1101 Raw／B88研究候選：來源2025-11-19～2026-07-14共155根；最大量1/12的98,217,134股，原K開23.85／高25.10／低23.80／收24.95。最高價26.95的1/27不是此量峰K。10/16原量57,437,884股，BELOW、差額-40,779,250股；未越只記未越，不判壞，也不取消當日轉強。

前筆量與完整段最大量獨立顯示；量圖紫虛線只表示這段最高日量，不是密集量峰代表線，也不穿MACD。廣角／局部不改155來源段；畫外不偽造當日來源，定位不改分析日。完整成員、全部同量日及原K可在抽屜／JSON核對。

B88 formal_price_bounds仍null，非核定正式原箱／完整帶。原量日、候選確認／量參照可知9/1、本輪實際後來選取分存；確認前reference=null。完整指明示保存成員，不認證完整市場日曆、公司行動或歷史公開可得。密集量峰代表線保持NOT_IMPLEMENTED及原因，不借平均／中位數／比例。

## JSON、HTML、封包與工程

- [新自含HTML](artifacts/M1_P03_explicit_band_volume_v03.html?raw=true)
- [完整量對照JSON](artifacts/band-volume.json)、[本輪明示選取](artifacts/band-volume-selection.json)、[建置驗證](artifacts/volume-build-verification.json)
- 原五份完整bytes相同：[結構狀態](artifacts/structure-state.json)、[chart-layer](artifacts/chart-layer.json)、[facts-input](artifacts/facts-input.json)、[scenario](artifacts/scenario.json)、[原價格角色](artifacts/role-selection.json)
- [可重現離線ZIP](M1_explicit_band_volume_v03_20261024.zip?raw=true)：19,157,290 bytes，82成員／81項manifest。
- ZIP SHA256：`c6bd5acbe661322e813168adee4a5f15cf3b667fb8692238f1bf5bf7a008e1c3`；[SHA256SUMS](SHA256SUMS)／[實際CRC、全成員及新解壓重建](package-verification.json)。
- [完整契約／工程入口](../../股票系統M1_v0_18/structure_state_chart/BAND_VOLUME.md)、[本輪驗收](../../股票系統M1_v0_18/structure_state_chart/validation_band_volume_20261024/驗收報告.md)、[來源／數值保留](../../股票系統M1_v0_18/structure_state_chart/validation_band_volume_20261024/source-lineage.json)、[完整可貼Work指令](WORK_HANDOFF.md)
- [固定工程逐檔GitHub原bytes回讀](GITHUB_READBACK.md)／[JSON](GITHUB_READBACK.json)，收據另存避免自指。
- [原0.2成品保留](../m1-p03-readability-20261024/README.md)。

真正實跑26新Python＋6相關回歸＝32，最後88項新Chromium檢查、三視窗／4份實際下載通過。初次mock函式名稱錯誤及截圖廣角調整留史；中間88、新解壓同26與歷史65／94、上一輪6／94不相加。ZIP全成員CRC／長度／SHA通過，新解壓同26及建置九輸出完整bytes與交付相同。

HTML用僅測試期間127.0.0.1 HTTP實測，非部署；Android NOT_TESTED_NEW_BUILD，file://不重試。不執行每日淨帳／六方案／獲利驗證。正式來源0.10及parent、原策略／引擎／庫、Raw null／UNKNOWN、歷史、main及全部警告／來源缺口保持。execution_qualified=false、imputed_close／valuation=null、historical_signal_eligible=false、primary_pressure_id=null、policy_authorized=false。

未完成密集量峰、自動完整帶切段／主壓力、全市場、換股／飛輪；原公司行動、個人權利／淨分配等缺口未解除，不把它們當圖形工程無限前置。下一步只Work做用途檢視，不重問已答P0-3／P0-4，不重抓舊來源或重試受拒入口。不部署、付費、交易、發訊息或啟動子代理。
