# 人工分析口徑 0.1 交付入口

分支：`dev/m1-v018-chart-annotations`。本版沿用已接受的 0.4.3 圖與原保存數值，另加人工「原始日 K／還原 K（研究候選）」選擇。直接下載同目錄 `M1_v019_manual_basis_v01.zip`，解壓後用本機 HTTP 開啟 `M1_v019_manual_basis_v01.html`。ZIP 含獨立 `catalogue.json`、四個精確對照 oracle、桌面／手機模擬截圖及使用說明；HTML 本身已內嵌資料，不需網路行情。

主頁先選模式。Raw 短期及五年來源在同日重疊時再選資料來源；缺所選模式或日期時主圖空白並標明不可用，從不偷偷換基底。切換股票保留所選模式，選擇保存於此瀏覽器並可下載 JSON。還原 K 只涵蓋 6488／8069 既存 283 根現金事件研究候選，不等完整除權息資料或交易訊號。B 案沒有使用者選定模式。

重建、CLI 保存契約及完整限制見 `股票系統M1_v0_18/manual_basis_chart/README.md`；測試與證據見 `股票系統M1_v0_18/manual_basis_chart/validation_20261022/驗收報告.md`。實體 Android 新版未測。舊 0.4.3 ZIP 與所有原引擎、策略、研究、資料庫、頁面保持。

下一次 Work 先看 `WORK_HANDOFF.md` 與根目錄最新 `CONTINUE_IN_WORK_MODE.md`，以及後續遠端新提交；不要只看本目錄日期判定優先順序。
