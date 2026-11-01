# M2-5｜F-01 跨基底相對錨點數值修復

**F-01已修復；本項只修正不可比物件的數值輸出，不是圖形品質或交易策略驗收。**

| 不可比物件 | 修前0.1 | 修後0.2 |
|---|---|---|
| 舊箱pressure_distance_fraction | 仍有數值 | null |
| 舊箱relative_width_to_anchor | 仍有數值 | null |
| 停止舊高點distance_to_anchor | 仍有數值 | null |

新anchor_comparison_reason指明`OBSERVATION_STOPPED_AT_DATA_OR_BASIS_GAP`；原停止事件與日期、參照、箱、轉折、局部歷史統計完整保留。可比物件reason=null且原數值不變。舊箱依舊排除目前壓力候選，primary_pressure_id仍null，不能推論曾發生錯誤交易。

## 直接唯讀驗收

- [最小核心差異](../core.py)：`_compare`與`analyze`兩處數值輸出；輸入0.1不變，新結果0.2。
- [修前真實摘要](official-before-summary.json)／[修後真實摘要](official-after-summary.json)：2884兩截點各3個舊箱、4個停止舊高點；違規非null計數歸零。
- [實際報告](REPORT.md)、[事前凍結契約](CONTRACT.md)、[輸入與預期](cases.json)、[預期規格](expected.json)。
- [修前合成actual](synthetic-before.json)／[修後合成actual](synthetic-after.json)、[12項定向測試log](tests-targeted.log)、[原功能保全](preservation.json)。

六份合成輸入與兩個真實截點的全結果差異核對，只容許契約列明的三欄、reason及版本／result_id；其餘逐值相同，不只比物件數。真實完整輸入／結果保存在Git外`/workspace/twstockai-local-data/m2-5-f01-20261101/`，公開摘要沒有價格、距離數值或可還原行情的完整輸出。沒有讀取或新查FinMind行情。

## 必要時重用測試入口

在`股票系統M1_v0_18`執行`PYTHONDONTWRITEBYTECODE=1 python -m unittest graph_core.f01_20261101.test_f01 -v`可核8個新方法；本輪另已實跑4個既有核心回歸，完整方法名在log。驗收可直接讀保存證據，無需重跑。`evidence.py`是本次凍結before／after的明示診斷腳本，不是新引擎／READ框架；既存證據檔採x模式，不能重跑後覆寫。before綁固定基線0.1、after綁0.2，禁止混淆版本或以目前source重算舊證據。

Library M2-4報告／ZIP未取得／未讀，不能冒稱Work原件驗收。來源時間、公司行動、正式圖形品質及全部舊資格限制保持；不改M-R1／不執行M-R2，達標即停止，不新增里程碑。人工操作：不需要。
