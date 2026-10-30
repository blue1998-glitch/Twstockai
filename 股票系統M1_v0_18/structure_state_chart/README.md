> 最新明示研究段最大量對照：[BAND_VOLUME.md](BAND_VOLUME.md)、[本輪驗收](validation_band_volume_20261024/驗收報告.md)、[新PNG／JSON／HTML／ZIP](../../deliveries/m1-explicit-band-volume-20261024/README.md)。沿用0.2主圖與原五JSON，P0-3及來源0.10不改，密集量峰代表線未實作。本輪32 Python／88 Chromium，不累加下方歷史。

> 顯示最新0.2：讀[READABILITY.md](READABILITY.md)、[本輪實測](validation_readability_20261024/驗收報告.md)及[新版PNG／HTML／JSON／ZIP入口](../../deliveries/m1-p03-readability-20261024/README.md)。原0.1核心、五份JSON及下方舊工程／驗收保持；不是來源0.11，不重跑歷史65／94。

# P0-3：接入既有人工模式研究主圖

[獨立純數值附層](../structure_state/README.md)接到原manual_basis_chart；沿用人工Raw／Adjusted解析、不可fallback、localStorage與JSON選擇紀錄，以及原K／SMA／MACD與全部既有操作。未修改原頁、舊引擎、參數或來源。不是重做整套UI，也不是來源0.11。

[交付入口、直接可看的廣角／局部PNG及HTML／ZIP](../../deliveries/m1-p03-structure-state-20261024/README.md)。PNG可直接在GitHub查看，不要求使用者搬手機檔案、開終端或架伺服器。HTML為完整自含可重現成品，實際以臨時loopback HTTP驗證；原file://政策未重試，file://可用及Android實機不冒通過。沒有網站部署。

## 主圖操作

1. 按「開啟1101真實研究案例」明示選此Raw來源；或沿原人工模式選股票、模式、來源與精確日期。這個按鈕是選定固定案例，不是自動選股或系統代決價格模式。
2. 主圖列所選日狀態、回檔高點、研究箱下緣、狀態變更日／原因與支持／反面／缺證；24月486根、約五年1213根及局部31根可互切，K／量／MACD共窗共游標。畫窗不限制計算範圍，移圖／定位／查詢不改分析日。
3. 價格軸內畫對價水平線與來源K圓點；來源日期在畫外仍有線標籤。局部視窗20.25在軸外時只明示提示，不把它畫在錯價或壓扁近期K。點線標籤或狀態標記看來源與原過線事實。
4. 10/12最初突破保留；10/13整理→10/14轉強→10/15整理→10/16轉強可逐日／重播。證據抽屜以中文列事件路徑，完整ID與JSON折疊。原關卡／區域保留且可選疊加，預設關閉避免相同價位不同來源混淆，不改其數值。
5. 下載JSON保留原保存選擇、完整精度與目前分析日前的狀態／事件／參照資格。參照原始artifact綁定是後來選取來源，display source_binding與evaluated_prefix是所選日期的實際同源前綴；不把來源檔較晚frame冒成歷史當時已選。
6. 換股或模式只沿原manual_basis，不套用此案例到其他來源／基底。無P0-3明示角色顯示證據不足；缺Adjusted資料照舊UNAVAILABLE，不默轉Raw。

## 案例資格

真實行情，但B88正式邊界及此回檔階段角色沒有人工核定。這是明示研究參照下的條件式結構描述，主圖清楚標示，不是已通過全市場分類、完整原箱自動辨識或交易信號。回檔高點26.85出自10/13，與原④的5/13即使同價也不合併。研究箱下緣20.25原K為2025-11-19；來源末轉折、確認、角色可知與後來選取分開。

## 工程重現

根依最新AGENTS bootstrap成功後，在本專案目錄：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_structure_state.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m structure_state_chart.build --output-dir structure_state_chart/output/NEW_EMPTY_LEAF
P03_ARTIFACT_DIR=structure_state_chart/output/NEW_EMPTY_LEAF CODEX_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium node structure_state_chart/test_browser.cjs
```

可選`--data`與`--selection`明示其他同契約保存來源，不自動挑選或補參照；不同現有輸出拒絕覆寫。不是給一般使用者架伺服器的要求；正常查看直接用GitHub PNG。原父版0.4.3 ZIP先核SHA／CRC，interned數值JSON36,717,209 bytes／SHA a632ac6200b87f8fdc44d2a80c05056019f89e356e0815ec69ac2ad5287d3d30保持。MA／MACD沒有重算。

實際測試、視讀與所有失敗／修正／未測見[驗收報告](validation_20261024/驗收報告.md)。只原唯一Codex工程寫入，不改main；不部署付費交易訊息或子代理。原來源限制、false/null資格及Android NOT_TESTED_NEW_BUILD不變。
