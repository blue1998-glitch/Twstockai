# 股票系統 M1：重播頁 v0.3／數值核心 v0.2

本階段修正重播頁，候選策略門檻、獨立數值核心與四份完整輸出皆維持 v0.2。不是新增交易資格。

## 本次修正

- 含千分位逗號的真實價格（例如 1,370.00）正確轉為繪圖數值。舊頁面此項會出現無效座標，已以同一測試重現舊版失敗。
- 成交量缺值不再當成零量；提示「未提供」，不畫成有資料的量柱。合法的零量仍顯示零。
- 日曆不一致明確提示需檢查；符合提供日曆也註明來源尚未認證。新增成交量資料狀態。
- 前後／最後日期依實際資料長度決定；切換日期／股票清除舊價格提示。

## 實測與限制

32 個 Python 測試及 11 項頁面邏輯測試通過。後者執行真實頁面 JavaScript，但使用模擬頁面元件與畫布；不是實際瀏覽器，不驗證外觀、水平溢出、無障礙或觸控。

1,132 組真實股票／價格模式／日期狀態繪圖座標皆有效；26 組除息前、當日、後日及端點價格投影與獨立核心一致。這些檢查不代表分類品質或交易價值。

已實際嘗試啟動瀏覽器測試，因缺少 Chromium 執行檔失敗，保持 NOT_VERIFIED。沒有把模擬測試改稱瀏覽器通過。

最新狀態見 output/M1_v0_3_驗收摘要.json；舊版本文件與報告保留作歷史參考。326 筆覆核目標仍全部未經人工覆核。

## 重現

```bash
python build_review.py
python validate_release.py
python -m unittest discover -s tests -v
python tests/make_price_fixtures.py
node tests/check_viewer_syntax.cjs
node tests/test_viewer_logic.cjs
```

產圖需 matplotlib；requirements-render.txt 記錄本次使用版本。核心本身使用 Python 標準工具。Node 用於頁面檢查；邏輯測試不需安裝瀏覽器。

只有在接手環境已有 Playwright 與 Chromium 時，才執行：

```bash
node tests/test_viewer.cjs
```

可透過 QA_CHROMIUM_EXECUTABLE 指定已安裝的 Chromium；不要把檔案路徑有值當成測試成功。最新交接見 docs/CODEX交接.md。

## 下一步用什麼模式

目前繼續工作模式。可存取 GitHub 專案清單此次回傳空陣列，尚未建立或驗證 Codex 環境；不能推論使用者完全沒有 GitHub 專案或帳號。交接資料已備齊，專案環境可讀取並可執行後，再轉 Codex 完成真實瀏覽器驗收。這次沒有發布、部署、建立外部專案或使用付費服務。
