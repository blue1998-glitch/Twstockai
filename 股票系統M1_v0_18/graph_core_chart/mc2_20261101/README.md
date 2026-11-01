# M-C2｜同期四股完整候選證據

先讀[四股比較表](COMPARISON.md)，再讀[小型總覽JSON](index.json)及其中明示的9份箱／事件分片。共同日期2026-10-16，使用完整M-G3 core0.2結果，非五個顯示箱；8069完整12,430,568 bytes已實讀／核SHA。沒有重新辨識或行情擷取。

四股合計558箱的完整候選集合，以及12,241筆原箱事件的指定欄位投影完整保存。為避免無聲截斷，總覽約45KB；1101／2884各1片、6488共2片、8069共5片，每片小於1MB，總量約5.3MB。**1MB目標是總覽與各分片，整組完整證據超過1MB，明示分片而非假稱總包小於1MB。** 沒有複製完整行情或核心原件。

`index.stocks[].box_shards`提供路徑、數量、bytes及SHA；各片boxes保持原先順序，重接即為完整原候選ID序列。每箱保留形成來源／原幾何／整箱位置／壓力帶位置、原父子及後繼、量統計、全部事件投影與NULL原因。事件events欄位順序見event_columns；原核心沒有獨立事件ID時，用result_id＋box.id＋events索引回查，不自行發明ID。原事件價量、逐筆K及全歷史轉折等**未匯出欄位**明列coverage，可按完整原件SHA核對，不假稱精簡輸出含完整核心全部欄位。

最新已確認高低點逐尺度保留全部最新確認日並列；pending全留。最近上方保留所有最小原距離並列，6488為977下緣八箱，並非重要性或股票強弱排名。2884無可比箱，距離null不補0。1101人工39筆與自動25筆分離；大小箱均在完整集合。原可比資格只是研究供應前綴，不認證普通股母體、完整公司行動、歷史公布可得或成交模型。

TPEx的原來源欄位是「成交仟股」或「成交張數」，換算×1000不增加申報精度；核心內SHARES_REPORTED不能覆蓋ledger的原始單位。不認證FinMind精確股數。UNKNOWN的原因在unknown_reasons與原source_gaps／qualification，所有null另有JSON pointer原因；停止／未觀察事件與未知來源不補為0。

## 重現與驗證（工程者）

既有環境於股票系統M1_v0_18執行：`PYTHONDONTWRITEBYTECODE=1 python3 -m graph_core_chart.comparison_export`。只讀凍結來源並透過原publish_immutable保存，已有相同內容不改bytes／mtime，異內容拒覆寫。`python3 -m unittest graph_core_chart.mc2_20261101.test_export -v`為本次定向驗證，已執行的結果見tests-first.log，不需要重跑舊suite。沒有新資料庫、網路抓價、READ框架或核心算法。

[凍結契約](CONTRACT.md)、[原件指紋／事前預期](frozen.json)、[初次診斷](run-first.log)、[對應最小修正](initial-fix.patch)、[正式匯出](run-second.log)、[測試](tests-first.log)。初次ledger結構映射KeyError已修正，只核既有真實欄位，不修改oracle或來源。

Work M-C1報告／ZIP Library原件未取得／未讀，依使用者指令與Git原件完成；不能稱Work已驗收本輸出。模型派工治理僅在根AGENTS新增一份，沒有自動切換其他對話模型。本輪無需人工操作；可繼續Work跨股機會研究，來源與策略仍不合格，不產生排名、買賣或正式採用。M-C2到此停止。

## 獨立回核來源位置

所有路徑相對repository root。來源ledger：`股票系統M1_v0_18/pressure_chart/data/history-20261018/history-candidate.json`；數值父檔：`股票系統M1_v0_18/region_chart/generated/M1_v0_19_manual_regions_v03.html`；完整M-G3：`股票系統M1_v0_18/graph_core_chart/output/mg3_20261101/M1_v019_graph_recognition_v02.html`。完整各股核心原件路徑／SHA在index.original，來源ledger／父檔／HTML各自SHA在同股metadata；原monthly response的SHA及申報欄位在ledger.source_records，匯出時逐月原件核對，沒有新抓來源。
