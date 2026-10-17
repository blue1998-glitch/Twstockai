> 最新獨立主圖交付：請讀repository root CONTINUE_IN_WORK_MODE.md最上方及本專案 technical_chart/README.md、technical_chart/validation_20261017/驗收報告.md。新頁technical-chart-view/0.1直接呈現真實日K／量／MACD、導航、原保存證據與JSON。1101／2884僅179根、6488／8069僅283根，無多年或真實盤中。新主圖Android NOT_TESTED；舊嘗試頁PARTIAL_EVIDENCE_OBSERVED獨立保留。原引擎、策略、schema、庫與舊頁不改；下方舊狀態按其歷史時點閱讀。

# 最新：嘗試關卡／量先價已接入畫面

接續45aaeec，新增 attempt-view-adapter/0.1 與獨立 `M1_v0_19_attempt_candidate.html`。原 attempt_evidence.py、原src、舊candidate計算／UI、schema與歷史保持不變。先讀root最新CONTINUE與 M1_V019_ATTEMPT_CORE_HANDOFF，再讀 product_candidate/ATTEMPT_VIEW.md 及 validation_attempt_view_20261017/驗收報告.md。新頁先啟用、明選來源／觀察；核心在離線Python計算，JS只渲染既有子條件／事件與原精度下載。

本輪325 Python通過，7假想來源／28成品核心前綴一致，新頁真實Chromium87檢查／56精確下載通過；84個原受保護檔SHA不變。初輪連續高速下載逾時保留FAIL診斷，修正測試節奏後全部重新核對。沒有新增真實行情、盤中供應、自動選取、正式分類／勝率或交易績效；Android實機未測，SQLite根因仍未知。三大最終目標未完成。

下一步工作模式檢視新頁與Android實測，真正未定核心才再用圖討論，不重問101必須等106；明確規則或程式故障回Codex。GitHub成品與交接更新同一獨立分支，main保留，禁止部署／付費／交易／訊息／子代理。

---

## 以下為先前交接沿革

# 最新 Codex 交接：v0.19 獨立候選

2026-10-17最新使用者回饋要求修正核心用途，取代下面歷史「只做Android／不新增必要功能」範圍。先讀root CONTINUE_IN_WORK_MODE.md、M1_V018_PRODUCT_GAP_HANDOFF.md、M1_V019_REQUIREMENTS_TRACE.md；source在 product_candidate/，新規則為 product-context-candidate/0.1 及 macd-12-26-9-sma-seed/0.1，未改原引擎、共同schema、舊庫或舊頁。

已補逐日已保存證據上下文／波段關係／主要低點參照、支持／反證／缺證與狀態連結、任意日期／時間及價格尺度、共用時間軸的K／量／MACD。Adjusted候選K是新離線投影，明示並非舊日線保存OHLC；UI不計算分析。最近低點參照不是已驗證重要性排名。生命週期／修正／正式型態保留UNKNOWN，盤中與持有人資訊缺少；不得為填滿畫面創造規則。

本環境實際驗證286 Python，最後純顯示調整後16項候選重測；真實保存1490frame與12截短前綴；最後HTML真實Chromium66檢查／48次精確下載。Android實機NOT_TESTED，核心用途NOT_ESTABLISHED，分類NOT_VALIDATED、交易NOT_EVALUATED，原SQLite根因NOT_ESTABLISHED。原始log／hash／截圖與精確執行範圍在 product_candidate/validation_20261017/驗收報告.md；可重現命令在 product_candidate/README.md。舊套件／72下載與三輪SQLite測試本輪未另重跑，保留為歷史。

下一步工作模式用root M1_V019_CORE_RULE_DECISIONS.md 的具體時點處理真正未定義核心思想，並可做新版Android實機驗收；有具體規則／程式故障再回Codex。常態授權允許成品與source更新同一GitHub獨立分支，main保留；不部署、付費、交易、發訊息或開子代理。

---

## 以下為 v0.18 交接沿革（當時狀態）

# Codex 交接：M1 v0.18 手機閱讀修正

## 本環境最新接續（2026-10-17）

原 v0.18 新手機頁已完成真實 Chromium HTTP 驗收，72 次下載核對通過。使用者新增兩張點位／色帶範例後，另交付「日週月研究對照_結構標記_v0_18.html」；同樣完成 72 次下載核對，另測證據清單、滑鼠／觸控標記、層級／歷史／視窗過濾與旋轉重畫。先讀 docs/結構標記顯示契約.md 與 annotations/validation_20261017/驗收報告.md。

現在是 270 項 Python 全通過（新增5項只讀匯出相容／防護）、根目錄 bootstrap hydration 整合測試1項通過、原頁16＋手機基礎16＋手機顯示6＋標記8項 Node 檢查通過。未重跑無改動的三輪 SQLite fault runner，不能算成本輪新增結果。原手機版與舊頁輸出仍逐字相同，原保存數值及引擎不變。以下 BLOCKED 是來源環境歷史狀態；新證據另存，未覆蓋歷史報告。

標記版重現：`python3 src/cross_view_cli.py --config cross_view/sources.json --html --annotations --output 日週月研究對照_結構標記_v0_18.html`。瀏覽器命令在原指令加 `M1_BROWSER_HTML=日週月研究對照_結構標記_v0_18.html`，輸出至新的證據目錄。若只驗原手機版，省略此變數。日線標記來自原 structure 快照，週月不自行新增結構，Adjusted 不生成 OHLC，原策略／門檻不變。

Git 現在追蹤可審查 source；新 checkout 先從 repository root 跑 `python3 codex/bootstrap_m1.py --hydrate-missing` 補齊未追蹤資產，再匯出標記頁。該選項只補缺檔，保留並報告差異；預設 bootstrap 仍為嚴格歷史基準驗證。不要以覆蓋或刪除方式讓歷史指紋看似通過。

下一步使用工作模式對話，針對新標記頁做實體 Android 開檔、點選證據、選單／旋轉／下載內容驗收。若實機有程式問題，再轉 Codex 修正。原 SQLite 根因、分類與交易資格維持原限制，不新增功能階段。

## 原交接沿革

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
