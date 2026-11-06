# SQLite 事件診斷與接續驗收

## 已知事實與未知原因

v0.16 補齊庫曾留下 rollback journal，跨程序唯讀回報 attempt to write a readonly database。獨立恢復後只見兩筆／566 快照，明確重跑後才恢復三筆／745 快照。原始診斷與日誌保留在 cross_view/output。原事故沒有保存 extended SQLite error code、寫入程序終止訊號或完整現場副本，因此無法從後來的成功讀取追認其根因。

v0.17 在三份臨時副本刻意啟動未提交的大型交易並以程序 exit 17 中斷，測試唯讀診斷、原 cross-view 匯出拒絕、原 store CLI 明確恢復。這是刻意製造的已知故障；即使訊息相同，也不能解釋原事故中已回報 COMMITTED 的第三筆為何不見。

SQLite 官方說明，讀取前若遇到 hot journal，必須先 rollback；SQLITE_READONLY_ROLLBACK（776）表示需要恢復卻是唯讀開啟。單看 journal 存在或檔案大小，不能判定它必為 hot。刪除或拆散恢復所需檔案可能破壞恢復能力。

參考官方資料：

- https://www.sqlite.org/rescode.html#readonly_rollback
- https://www.sqlite.org/lockingv3.html#hot_journals
- https://www.sqlite.org/howtocorrupt.html
- https://www.sqlite.org/wal.html#read_only_databases

## 現場處理

1. 停止新寫入，記錄程序、時間、命令、退出碼、操作 ID、COMMITTED／UNKNOWN／NOT_SAVED 回覆。確認既有 writer 已退出，保留原檔。
2. 執行 `python3 reliability/sqlite_probe.py --db <明確資料庫路徑>`，把 stdout 保存到另一個新檔。工具用 mode=ro、timeout=0，不 recover、不建立、不刪除。它記錄 SQLite 版本、extended error code/name 及主檔與 journal／wal／shm 的前後 hash／metadata。前後相同不代表期間無並發，也不是一致備份或來源認證。
3. 保留主檔與所有 sidecar，不能只複製主檔、手刪 journal、改 immutable URI 跳過恢復或換新庫掩蓋錯誤。若需備份應先確認 writer 靜止並完整保留現場；本工具不做備份。
4. 獨立、有權寫入的 worker 才可執行原 `python3 src/store_cli.py recover --db <明確資料庫路徑>`。這不是瀏覽功能，也不是每次遇到錯誤就盲試恢復。
5. 恢復成功後用原 READ／LOOKUP 精確 IDs 核對完整 request／result／evidence、索引與預期指紋。quick_check=ok 不等於所有已回報提交都存在；不得自動補算。若缺資料，保留證據，分清 COMMITTED 與 UNKNOWN，再決定明確重跑。

## WAL 保留現場限制

SQLite WAL 的 mode=ro 仍可能建立或使用 shm／wal 輔助檔，故本工具僅查詢 rollback 模式。先讀主檔 header 和 sidecar 清單，遇到 WAL header 或 wal／shm 時，直接回報 READ_REFUSED_WAL、exit 2，不開 SQLite、不設 immutable、不做 checkpoint 或轉換模式。可保存檔案觀察結果，但不宣稱可讀性檢查通過。

已以實際 WAL 資料庫測過「正常關閉後僅剩 WAL header」及「仍有 wal／shm」兩種情形，診斷前後檔案／metadata 相同。Header 讀取不是鎖；此工具要求停止 writer，不能防止另一程序在檢查後並發切換模式。

## 可重現的隔離驗收

`python3 reliability/run_acceptance.py` 沒有使用者可輸入的目標路徑。先檢查本包補齊庫無 sidecar、完整讀取後，再建立三個臨時副本。每輪由三個獨立程序重存原三份結果，確認 EXISTING、完整保存內容不變；故障注入只在副本未提交交易中加入無效物件。

唯讀診斷須取得 776 並保留 bytes／metadata；原 cross-view CLI 須明確 STORE_DATABASE、保留舊 HTML、主檔與 journal 不變。只有原 store CLI 的獨立 recover 可改檔。恢復後須三筆／745 快照、九 objects、所有保存內容指紋完全相同，未提交 fault 不可出現；來源庫不變。這不是斷電、磁碟故障、網路檔案系統或多機耐久性認證。

## 瀏覽器與交接

`node tests/test_cross_view_browser.cjs` 使用現有 Playwright 與 Chromium。若執行檔另有位置，可設定 CODEX_BROWSER_EXECUTABLE_PATH；缺執行檔維持 BLOCKED。不要在此環境重複盲試安裝、發布頁面以繞過限制，或把 DOM 替身當瀏覽器。

目標驗收為 1280×900 桌面與 390×844 觸控手機模擬，18 組原資料切換、兩種週月 basis、JSON 下載、無 JS 錯誤與橫向溢位。另以實體 Android 測本機開檔、圖表、觸控、選單與下載；手機模擬通過不等於實機通過。

本包已具完整 Codex 開發交接，但外部環境尚未接入驗證。瀏覽器完成前不新增功能或提升分類／交易資格。若後續涉及共同 schema、核心策略、部署、付費或交易，先提出具體方案並取得必要授權。
