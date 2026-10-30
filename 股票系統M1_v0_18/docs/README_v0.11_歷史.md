# 股票系統 M1 v0.11：已保存分析唯讀瀏覽

先開「已保存分析瀏覽.html」，選股票、價格模式、保存版本與日期，查看已保存的均線、轉折、區域、待確認候選與當日事件，並下載當日快照 JSON。這是離線歷史資料，需下載 HTML 後以支援 JavaScript 的瀏覽器開啟，沒有已發布網址。約 24 MB，尚未實測 Android 載入時間。

實際接入 v0.10 保存庫：8069 原始／還原候選各 283 筆、1101 原始 179 筆，共三組分析、745 個版本×日期。頁面沒有分析引擎或行情連線；均線與候選直接讀保存快照，原始 OHLC 分開標示。舊「價格結構重播.html」保留原樣。

147 項 Python、28 項 Node 模擬頁面檢查、JS 語法與舊功能回歸通過。745 個前端快照與 Python 完整快照指紋一致，首／中／末共九次公開 snapshot 讀取相同；資料庫雜湊及數量不變。38 份既有核心／資料庫／歷史產物逐位元組不變。真實 Chromium 啟動失敗：缺少執行檔，狀態 BLOCKED，不能視為桌面／手機驗收。

1101 原生股數依來源正確標示，但部分舊結構 evidence.volume_precision 仍誤寫張數換算；本頁揭露並保留原文。下一階段以新輸出版本修正文字、驗證數值不變及歷史可讀，不改舊紀錄。

```bash
python src/saved_viewer.py --db workflow/output/分析流程_v0_10.sqlite3 --output 已保存分析瀏覽.html
python saved_viewer/run_acceptance.py
node tests/test_saved_viewer_logic.cjs
python -m unittest discover -s tests -v
python validate_release.py
node tests/check_viewer_syntax.cjs
node tests/test_viewer_logic.cjs
```

具備 Playwright 與 Chromium 的環境另跑 `node tests/test_saved_viewer_browser.cjs`。缺少瀏覽器退出 2、記錄 BLOCKED，不下載或偽報成功。匯出、保存與核心只需 Python 標準庫；Node 用於頁面測試。

先讀 AGENTS.md、候選規則、docs/保存結果唯讀瀏覽契約.md 與 docs/CODEX交接.md。最新驗收在 saved_viewer/output/保存結果瀏覽驗收.md，機器證據在 output/v0_11_checks.json；較早報告是歷史紀錄。RUN／READ／LOOKUP 與保存／復原入口沿用 v0.10，見 docs/單一分析流程契約.md。

326 筆仍 UNREVIEWED，分類 NOT_VALIDATED、交易資格 NOT_EVALUATED。未新增公司行動核實、週月均線、正式整理型態、持股、正式訊號或雲端服務。

下一步繼續工作模式，修正成交量證據文字與版本相容性。Codex 交接完整；外部專案環境仍未接入驗證。
