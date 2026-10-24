# M1 跨尺度證據時間軸交付與限制｜2026-10-20

新檔：docs/core-recognition/20261020_cross_scale_comparison_reader.html；前一提交7b7811b1e5afd09285525eee144d829ace9d958a，GitHub fetch_file逐字回讀相等。原分支基準b13e9d299f2d8aef0390f069d66cc60041fe228b，compare_commits status=identical；固定成品57e3d9e55c226c5dd0e69fcbd26883d0da81667e保留。

## 本輪實際完成
依序以GitHub connector讀AGENTS、CONTINUE頂端、M1_V019_GRAPH_CORE_RESUME_HANDOFF頂端、deliveries/.../WORK_HANDOFF全文、20261020兩份前期Work研究文件、graph_diagnostics README/review-diagnostics.json/驗收報告、graph_core_review四份文件、PROJECT_VISION及VISUAL_RULE_NOTES最新節；另讀graph_core README。建立無合成行情的可放大、可拖曳、可點擊來源日期時間軸；明示人工月份帶、B77原候選、左右被拒串、人工39根前箱、B44/B80同幾何、B88近期箱，列來源/確認/研究離箱/人工終點區別。原診斷ZIP保留連結。所有文字／圖示均為外部閱讀輔助，不輸入原核心。

## 未完成與阻礙
這**不是**用真實OHLCV逐根重畫的新K線，也沒有同步成交量/MACD/十字線。GitHub raw ZIP 24,735,759 bytes於本執行容器requests嘗試下載時發生NameResolutionError（無法解析raw.githubusercontent.com）；本環境僅透過GitHub connector讀取GitHub文字JSON，review-diagnostics.json不包含完整逐根K量MACD資料。故沒有取得真實1213根數列、沒有重算核心、沒有執行Chromium/Android、沒有新K量MACD截圖，也沒有新圖瀏覽器實測；只驗證GitHub文字內容逐字回讀。不要將時間軸或先前Codex的35 Python/45 Chromium測試冒充本輪K線驗收。下輪須在可下載固定ZIP的Work/工程環境解包取得原始K線、成交量、MACD，生成同軸互動圖後再做真實瀏覽器／手機視窗測試，且保持原核心不變。

## 核心未決
B77高群6.05/容許3.5700/餘量-2.4800，低群3.25/容許2.4675/餘量-0.7825。89候選/84幾何組非獨立型態數，B77的32廣義後來候選非直接承接。正式區界、量口徑、增量、衰減、重要性、合併、直接承接、生命階段未知；primary_pressure_id=null。Raw公司行動、五年Adjusted、歷史可得、SQLite未知；Android NOT_TESTED_NEW_BUILD；file://不重試不繞過。原引擎、參數、庫、歷史、舊頁、案例及main不變。不部署、不付費、不交易、不發訊息、不啟動子代理。
