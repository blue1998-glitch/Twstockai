# 股票系統 M1 v0.4：日均線與價格結構重播

本版加入已確認的日線週期：5、20、60、130、260。均線是收盤價的簡單算術平均（SMA），由獨立模組計算，頁面只讀取核心數值。既有價格結構核心與四份完整輸出維持 v0.3，沒有新買賣規則。

## 使用方式

開啟「價格結構重播.html」，選股票、價格模式與日期。圖下新增五個均線開關，預設顯示20與60日；下方列出五種均線當日數值，顏色與線條對應。尚未取得完整筆數就顯示「尚未形成」，例如259筆時沒有260日均線，不以零或較短平均冒充。

均線依提供的日線筆數計算。完整官方交易日曆與停牌尚未核對，不能據此認證窗口完全涵蓋應有交易日。

Raw均線沿原始價格序列計算，跨除息日可能保留價格落差；既有Raw結構候選仍按自己的規則重設並暖機。還原候選以當天已生效的純現金除息事件建立同一價格基準，再計算當天快照內的整段均線。之前的快照不覆寫。此方法不是已認證的歷史公告時點回測。

## 已實際完成

- 42個Python測試通過，包含完整窗口、260筆邊界、格式化價格、除息基準、未來資料隔離、原資料不變及完整頁面資料一致性。
- 13項頁面邏輯測試通過，執行真實JavaScript搭配模擬元件／畫布；覆蓋1,132組真實股票／模式／日期狀態、均線開關及資料不足提示。
- 新增四份*_MA.json核心輸出；檢查頁面壓縮資料與每一天完整核心曲線一致。
- 產出並目視檢查6488真實資料均線PNG。這是核心輸出繪圖，不是瀏覽器截圖。
- 實際啟動瀏覽器仍因缺少Chromium失敗；真實外觀、水平溢出與手機觸控尚未驗收。

最新結果：output/M1_v0_4_驗收摘要.json與v0_4執行紀錄。歷史報告保留，不作為本版完成依據。

## 重現

```bash
python build_review.py
python validate_release.py
python -m unittest discover -s tests -v
python tests/make_price_fixtures.py
node tests/check_viewer_syntax.cjs
node tests/test_viewer_logic.cjs
python render_ma_preview.py
```

產圖需要requirements-render.txt列出的matplotlib；核心只需Python標準工具。真實瀏覽器測試另需Playwright及可用Chromium，執行node tests/test_viewer.cjs；無法啟動不得列為通過。

src/moving_averages.py提供analyze_daily_ma介面；build_review.py已接入。既有src/jobs.py仍執行原價格結構工作單，尚未整合為含均線的新版工作單；不要宣稱此項完成。

## 下一步

繼續工作模式，處理後續已確認功能與資料驗收；Codex交接資料已備齊，但專案環境尚未接入或驗證。接入可用後轉Codex補做真實瀏覽器驗收。週線4/13/26/52、月線3/6/12/24尚未實作，需正確處理未完成週月與日曆問題後再做。

三種正式整理型態、分類品質、完整公司行動與交易價值仍未驗收；326筆仍UNREVIEWED，行動資格維持NOT_EVALUATED。
