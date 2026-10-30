# 開發交接：M1 v0.11 保存結果唯讀瀏覽

先讀 AGENTS.md、README.md、候選規則、docs/保存結果唯讀瀏覽契約.md 及 saved_viewer/output/保存結果瀏覽驗收.md。v0.10 工作流程與資料庫維持原樣，歷史交接在 docs/CODEX交接_v0.10_歷史.md。

## 已實際執行

147 項 Python（新增 13 項匯出／檔案邊界／故障測試）、15 項新頁面及 13 項舊頁面 Node VM 邏輯檢查通過；JS 語法、validate_release 回歸通過。output/v0_11_checks.json、各 log 及 saved_viewer/output/*.json 為證據。真實 Chromium 已嘗試啟動，缺少執行檔、退出 2、BLOCKED；沒有真實版面／觸控成功宣稱。

src/saved_viewer.py 僅呼叫 AnalysisStore.list_records/load，沒有恢復或計算；完整嵌入已驗證 bundle，輸出「已保存分析瀏覽.html」。CLI、路徑防撞、原子輸出、JSON 跳脫與契約見新契約。七個核心、三個保存模組、兩個 workflow 模組、兩份資料庫、舊重播頁與歷史證據等共 38 份既有檔案逐位元組不變。

saved_viewer/run_acceptance.py 使用實際 v0.10 庫：三分析、三紀錄、九去重物件、745 日期索引。HTML 解析的 bundle 全等 load，首／中／末九次公開 snapshot 全等；對 745 份快照產生期望指紋。tests/test_saved_viewer_logic.cjs 執行實際 inline script，每個日期構造下載快照，完整 canonical SHA256 全部一致。注意 JSON 數字鍵：須手動按字串排序輸出；JS Object.fromEntries 後 stringify 會重排數字鍵，不能充當 Python canonical。

股票／模式／版本／日期相互鎖定。多版本不擅選最新；缺失日期不找近似日期。錯誤清空舊數字、圖表、JSON 與懸浮讀值，停用下載。新頁只繪保存均線 curves，來源 OHLC 另列原始價格；沒有還原乘法、平均或候選辨識。窗不足維持 null。下載 saved-analysis-selection/1.0 的 snapshot 與 AnalysisStore.snapshot 相同，record 另附版本／證據來源。

test_saved_viewer.py 實跑 os._exit(17) 中止寫入者並留下 hot journal：唯讀匯出失敗且 DB／journal 位元組不變，獨立 recover 後恢復可讀；匯出不能替代復原。禁止所有引擎／workflow 匯入的獨立程序仍可匯出。缺失／壞庫／未知 schema／篡改指紋／硬連結／符號連結／sidecar 防撞／輸出失敗都有必要測試。

多版本前端測試包含「僅供選取測試的新證據紀錄」記憶體 fixture，不是官方新證據或新演算法。Node DOM/canvas doubles 不驗證 CSS、無障礙、觸控、真實下載或 Android 效能。browser 腳本已備，待有執行檔時跑。HTML 約 24 MB 整份載入，不聲稱全市場效能。

## 下一個合理階段：成交量證據文字與版本相容

1101 source.volume_unit=SHARES_REPORTED、volume_normalization=NATIVE_SHARE_COUNT_NO_SCALING，數值本來就是原生股數；但 structure 的部分 pivot evidence.volume_precision 固定寫 Source lots scaled to shares。頁面依來源正確標示並揭露矛盾，保存內容未改。先定位 structure.py、jobs.py、analysis_jobs.py 的生成責任及契約，不要乘除成交量來「修」文字。

1. 讓核心保持獨立，依明確 volume_unit 傳遞正確來源精度說明；舊張數換算工作單維持原義。錯誤／缺失單位依契約處理，不猜測。可採明確配置，不引入儲存、UI 或網路依賴。
2. 改過證據的輸出標記明確新版本，讓 analysis_id、snapshot_id、規則資訊可區分新舊，避免同 analysis_id 產生不同結果。候選策略門檻不得改。
3. 跑來源張數換算及 1101 原生股數的回歸：價格、成交量比、發生／觀察／確認日期、區域、狀態及均線相同；只允許預期的文字／版本／衍生身分變更。
4. 建新獨立驗收庫或追加新紀錄，不修改 v0.9／v0.10 歷史庫。READ／LOOKUP／唯讀頁能明選新舊紀錄，不偷偷升級；重跑去重仍成立。
5. 更新單位 fixtures、契約、交接及實際證據；舊三紀錄保持可讀。多版本瀏覽跑實際新舊資料，不只 synthetic fixture。

## 模式與邊界

繼續工作模式；原始碼、資料、測試及重現命令已備妥可供 Codex 接手，外部專案環境仍未接入驗證。每次結尾都須說明模式選擇。

326 筆仍 UNREVIEWED，分類 NOT_VALIDATED、交易資格 NOT_EVALUATED。新公司行動證據仍 staging；紀錄日／付款日／衍生契約調整日不能自動升級股票除權息日，X0.00 不等於零。不要重試／繞過已拒絕 TWSE 介面。不發布、部署、付費、交易、發訊息或啟動子代理，不改核心策略。HTTP、正式訊號、週月均線、完整日曆／來源及手機驗收尚未完成。
