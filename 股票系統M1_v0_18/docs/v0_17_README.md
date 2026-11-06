# 股票系統 M1 v0.17：日週月成品與 SQLite 事件診斷

本版接續 v0.16 的診斷與驗收工作。既有離線對照頁、數值引擎、保存格式、原資料庫與策略候選規則保留；新增唯讀診斷工具、隔離副本故障重現與可執行交接。v0.16 完整說明在 docs/README_v0.16_歷史.md。

直接開啟「日週月研究對照.html」，明確選股票、模式、日期與兩邊保存版本，再按讀取。只顯示原保存資料，沒有補算或交易結論。Adjusted 日線沒有保存還原 OHLC，僅顯示保存均線。詳細契約見 docs/日週月唯讀對照契約.md。

本次狀態與實際測試見 reliability/output/診斷與交接驗收.md；故障報告見 reliability/output/SQLite故障重現驗收.json；操作與剩餘限制見 docs/SQLite事件診斷與接續驗收.md。原事件根因仍 NOT_ESTABLISHED。真實瀏覽器缺執行檔而 BLOCKED，物理 Android NOT_TESTED。

可在專案根目錄執行：

```bash
python3 -m unittest discover -s tests -v
python3 reliability/run_acceptance.py
node tests/test_cross_view.cjs
node tests/test_cross_view_browser.cjs
```

故障驗收只操作臨時副本。唯讀診斷範例：

```bash
python3 reliability/sqlite_probe.py --db cross_view/output/補齊日線.sqlite3
```

診斷結果印到標準輸出，不建立／恢復資料庫。遇到 WAL header／sidecar 直接拒絕 SQLite 開啟，保留現場。不把輸出重新導向原庫或 sidecar。READABLE 只指 SQLite 可讀，不代表本系統完整內容、來源或策略驗證。

外部 Codex 可直接使用本完整包；先讀 AGENTS.md、docs/CODEX交接.md 與 CODEX_START_PROMPT.txt。下一個實質工作是有瀏覽器環境的驗收，無須再擴充例行功能。尚未接入或測過外部 Codex 環境。classification_quality 保持 NOT_VALIDATED，交易資格 NOT_EVALUATED，326 筆人工覆核仍 UNREVIEWED。
