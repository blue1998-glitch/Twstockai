# Codex 開發交接：M1 v0.17

## 任務與已完成範圍

使用者是繁體中文介面、Android 操作的非工程師，允許一般可逆開發／診斷自主完成；只在核心策略、重大架構或必要授權時詢問。每次結尾必須明講繼續工作模式或轉 Codex。本輪已完成可在目前環境執行的診斷、實作、回歸與封裝，不需憑空新增功能階段。

先讀 AGENTS.md、README.md、docs/候選規則_v0.1.md、docs/日週月唯讀對照契約.md、docs/SQLite事件診斷與接續驗收.md、reliability/output/診斷與交接驗收.md。v0.16 架構與資料詳見 docs/CODEX交接_v0.16_歷史.md。

v0.16 的日／週／月唯讀比較已完成：九日線 record／18 快照、十二週月紀錄、18 個輸入對齊對照；四檔、六組模式、兩個日期，版本／日期／來源明選，無 latest、鄰日、補算或交易結論。既有 src 及保存內容、本機 HTML 均保持。

v0.17 只新增 reliability/sqlite_probe.py、reliability/run_acceptance.py、tests/test_sqlite_incident.py、診斷資料與文件。既有引擎、SQLite 保存格式、共同 schema、工作流程與頁面沒有修改。本次 260 Python、66 Node DOM／canvas 替身、JS 語法與契約檢查已實際通過。原 v0.16 交付中 788 個非主文件逐位元組不變；四份主文件另存歷史。

## SQLite 事故：不要過度解讀

原新補齊庫曾出現 journal 與唯讀失敗；明確 recover 後只見兩筆／566 快照，再明確重跑恢復三筆／745。根因仍 NOT_ESTABLISHED，不能說本版已修復根因。原診斷保留。

本版三個獨立副本、九次跨程序 EXISTING 保存未丟資料；每輪故意未提交寫入再 exit 17，可重現 SQLITE_READONLY_ROLLBACK／776。診斷與原 cross-view CLI 不修改主檔／journal，舊輸出保留；原 store CLI 在獨立程序 recover 後，三筆／745／九 objects 及包含建立時間、證據、原因與所有結果的完整保存指紋都相同。這只證明已知未提交中斷的處理流程，不證明原 COMMITTED 後少資料的原因。

唯讀診斷不 import 引擎／workflow／AnalysisStore，不產生新庫，不 recover、刪 journal、重寫或升級資料。READABLE 不等於系統保存內容有效。WAL header 或 wal／shm 直接 READ_REFUSED_WAL，避免唯讀 SQLite 仍可能改動輔助檔；不開 SQLite、不做 immutable bypass。使用標準輸出，勿把 shell redirect 指向來源或 sidecar。若原事故復發，停止 writer、保留主檔＋全部 sidecar／程序與回覆，取得 extended error、hash、退出碼與完整 IDs。禁止讀取層自修復或自重跑。

## 下一個可執行工作

完整交接已備妥，適合轉到具現有 Chromium 的 Codex 開發環境完成介面驗收；該外部環境尚未接入／測試，不聲稱已自動移轉。解壓完整包並以頂層股票系統M1_v0_17 為工作根目錄，不必先取得新行情或重新計算保存資料。

```bash
python3 -m unittest discover -s tests -v
python3 reliability/run_acceptance.py
node tests/test_cross_view.cjs
node tests/test_cross_view_browser.cjs
```

若環境提供另一個現有 Chromium 路徑，以 CODEX_BROWSER_EXECUTABLE_PATH 指定後執行 browser 測試。Playwright 使用 CODEX_PRIMARY_RUNTIME_NODE_MODULES 中套件，無此變數則使用本地可解析 playwright；本包不內附 node_modules 或瀏覽器二進位檔。缺依賴／執行檔為 BLOCKED，其他實際失敗為 FAIL。不得重複盲試下載、以模擬代替或發布網站繞過。

真實 browser 目標：1280×900 與 390×844、18 組精確來源選取、兩種週月 basis、下載 JSON、無 pageerror／橫向溢位。先重現再依實際錯誤修正，只碰顯示與必要測試，不改數值引擎。檢視圖表、精確資料表與版本警告；對 Adjusted 日線只顯示原 MA，不能重建未保存的 OHLC。實體 Android 還要另外測本機開檔、觸控與下載。

## 狀態與禁止擴張

classification_quality NOT_VALIDATED；action_qualification NOT_EVALUATED；326 人工覆核 UNREVIEWED。正式策略、回測績效、持股、盤中全市場、雲端全天候與部署均未批准，不因診斷通過而變成已完成。

不開子代理、不發布／部署／發訊息／交易／付費，不重試被拒 TWSE 端點。不覆寫歷史庫與快照；核心架構或共同 schema 若必須修改，先提出具體相容方案。下一階段應以真正可執行的瀏覽器驗收為限，不再新增例行功能來延續版本。
