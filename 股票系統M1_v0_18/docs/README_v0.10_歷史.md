# 股票系統 M1 v0.10：單一分析與保存流程

最新報告：workflow/output/單一分析與保存流程驗收.md；固定格式：docs/單一分析流程契約.md。

已建立RUN／READ／LOOKUP三種操作的單一本地入口。RUN完成工作單驗證、獨立引擎計算、保存及指定日期讀回；READ／LOOKUP不重算。錯誤明示尚未保存、結果不明或已保存，回覆匯出失敗仍能查回，重跑去重。

真實樣本8069原始／還原候選各283筆、1101原始179筆，完整結果與既有引擎相同，歷史快照及未核實狀態保留。新流程資料庫3分析版本、3保存紀錄、745版本×日期索引。舊v0.9資料庫保持不變。

134項Python、13項模擬頁面邏輯、JS語法與舊功能回歸通過；31份既有檔案與v0.9逐位元組相同。326筆仍UNREVIEWED，沒有分類、交易價值或真實手機驗收宣稱。核心仍可在禁止儲存／workflow匯入時獨立計算。

```bash
python workflow/run_acceptance.py
python -m unittest discover -s tests -v
python validate_release.py
node tests/check_viewer_syntax.cjs
node tests/test_viewer_logic.cjs
```

另建全新驗收檔：python workflow/run_acceptance.py --db workflow/output/另一份流程資料.sqlite3。單一請求範例與命令見docs/單一分析流程契約.md。全部離線；新入口及核心只需Python標準庫，模擬頁面檢查需Node。

先讀AGENTS.md、候選規則與docs/CODEX交接.md。最新證據是output/v0_10_checks.json；較早的報告為歷史紀錄。本版未改重播頁、未發布服務，手機介面、HTTP服務、持股與正式訊號尚未建立。

下一步繼續工作模式，接入已保存結果的唯讀瀏覽與匯出，維持計算與顯示分離。Codex交接已備，外部專案環境尚未接入驗證。
