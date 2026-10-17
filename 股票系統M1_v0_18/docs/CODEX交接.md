# Codex 交接：M1 v0.18 手機閱讀修正

先讀 AGENTS.md、README.md、docs/手機顯示修正_v0.18.md，再讀原 docs/日週月唯讀對照契約.md。數值規則與資料限制仍有效。

本版因使用者實機截圖與兩位小數要求而修正顯示，新增 日週月研究對照_手機版_v0_18.html 和 src/cross_view_mobile_template.html。價格顯示採十進位字串進位；內部、曲線來源、快照和下載 JSON 均保留原值。Responsive canvas 使用實際 CSS 尺寸及 DPR，表格換行、期間放數字下方。原 HTML 與原模板保留。

cross_view_export.py 的 render/protect/export 增加 template 關鍵字參數，原預設輸出逐字相同；CLI 新增 --mobile，必須與 --html 同用。沒有更動核心引擎、schema、保存庫、策略門檻或規則版本。兩份模板皆須防輸出碰撞。

使用者提供的三張截圖是舊頁實體 Android 的開檔與三圖顯示證據。另回報可下載，但檔案類型與內容未獨立確認；不能標記全選單、18 組切換或 JSON 語意實機通過。新版實機仍 NOT_TESTED。詳細證據範圍在 mobile_viewer/output/Android實機部分驗收.json。

已執行的結果見 mobile_viewer/output/手機顯示修正驗收.md。Node VM/canvas 替身不代表實際排版。新版真實瀏覽器已準備且嘗試啟動，缺 Chromium 而 BLOCKED／exit 2，完成案例 0。不要重跑無改動核心，也不要盲試安裝或部署繞過限制。

有真正存在的 Chromium 時，下一個具體任務如下。以實際路徑替換最後一個環境變數；本機 HTTP 伺服器只提供單份 HTML、無資料庫及目錄、測試完自動關閉，不是公開部署。

```bash
M1_BROWSER_TRANSPORT=http \
M1_BROWSER_OUTPUT_DIR="$PWD/mobile_viewer/output/browser-http" \
CODEX_BROWSER_EXECUTABLE_PATH=/實際存在的Chromium路徑 \
node tests/test_mobile_viewer_browser.cjs
```

目標：1280×900 桌面與 390×844 手機模擬、橫向切換，18 組×兩種週月口徑×兩種畫面，預期72次精確 JSON 下載；檢查兩位顯示、真實 canvas 繪製與 backing、頁面／主表無橫向溢位、沒有 JS 錯誤或外部請求。這是尚待執行的目標，當前完成0，不是已通過72案。手機模擬通過後仍需新版實體 Android。

可重現唯讀匯出：

```bash
python3 src/cross_view_cli.py --config cross_view/sources.json --html --mobile --output 日週月研究對照_手機版_v0_18.html
python3 mobile_viewer/build_display_oracle.py
node tests/test_mobile_viewer.cjs
```

若新改動需要全套回歸，暫存目錄須在同一檔案系統，避免 hardlink 測試 EXDEV：

```bash
mkdir -p mobile_viewer/tmp
TMPDIR="$PWD/mobile_viewer/tmp" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

若原 Codex 環境保有之前雲端測試修改，先比對並保留，不可被本包原始 v0.17 歷史腳本覆蓋。一般可逆修正自主完成，核心策略／重大架構／必要授權才詢問。不開子代理、不部署、付費、交易或發訊息。讀取層不可恢復資料庫、補算或挑新版。NOT_VALIDATED、NOT_EVALUATED、326 UNREVIEWED 和 SQLite 原因未知均保持。

下一步建議轉回原先有 Chromium 的 Codex 環境，完成新版介面驗收。不要憑空增加例行功能階段。
