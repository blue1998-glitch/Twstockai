# 股票系統 M1 v0.12：成交量來源修正與新舊版本並存

已修正新分析結果的單位證據：1101 原本就是來源股數，現在正確寫明「沒有張數換算」；8069／6488 的既有張數換算說明維持原義。沒有乘除成交量、沒有改策略或分析數值。結構版本升為 structure-0.3-research，舊版本完整保留。

先下載「成交量版本比較瀏覽.html」，用支援 JavaScript 的瀏覽器開啟。選股票 1101、原始價格候選，再選「來源單位修正版」或「歷史保存版」，按最後保存日，即可核對。多版本需明選；舊資料的歷史錯誤文字仍保留並揭露。約 48 MB，真實手機開啟／版面／效能尚未驗收，沒有已發布網址。

已實測三檔、五組 Raw／Adjusted 案例共 1311 個日期，修正前後所有數值、日期、狀態及完整日均線相同。獨立庫保存兩檔六組新舊分析、1490 個版本×日期；LOOKUP 列出兩版，重跑去重。包含兩個歷史庫與舊 HTML 在內，40 份既有產物／核心逐位元組不變。

156 項 Python、38 項 Node 模擬頁面檢查、JS 語法與舊功能回歸通過；全部 1490 份頁面快照指紋相同。這不等於真實瀏覽器／手機驗收或分類品質核准。

```bash
python volume_revision/run_acceptance.py
python saved_viewer/run_acceptance.py
node tests/test_volume_version_viewer.cjs
python -m unittest discover -s tests -v
python validate_release.py
node tests/check_viewer_syntax.cjs
node tests/test_viewer_logic.cjs
node tests/test_saved_viewer_logic.cjs
```

先讀 AGENTS.md、候選規則、docs/成交量來源與版本相容契約.md 及 docs/CODEX交接.md。最新報告在 volume_revision/output/成交量來源修正驗收.md，機器證據在 output/v0_12_checks.json。較早報告是歷史紀錄。舊 v0.9／v0.10 驗收程式會在新版本下先停止，避免覆寫歷史結果；以最新命令重現本版。

分析與資料層均獨立於網頁，Python 核心與保存只需標準庫。326 筆歷史覆核仍 UNREVIEWED，分類 NOT_VALIDATED、交易資格 NOT_EVALUATED。沒有新增公司行動認證、正式整理型態、持股、正式訊號或雲端服務。

下一步繼續工作模式，建立獨立週／月資料聚合與均線核心，先不改現有統一分析及保存格式。完整 Codex 交接已備，外部專案環境尚未接入驗證。
