# B 案例價格口徑：官方事件已讀通，雙來源比較已完成

2026-10-22（台北）；接續 `17a480ec770bfbeb0c179115a48d99a4647b978c`，分支 `dev/m1-v018-chart-annotations`。本輪為資料補核與獨立研究，無原產品／引擎變更。

## 已完成與新發現

1. 最新六提交的父子鏈、三根交接入口與最新 WORK_HANDOFF 已核讀。`17a480ec → 99a332e8 → 7ffb2dca → d0aa0f13` 表示價格口徑答覆晚於七月 Raw 圖；以此提交關係及原驗證範圍處理記載，沒有只按日期判新舊。
2. 前輪 web 工具未讀通的 TWSE TWT49U，這輪經標準 HTTPS 直接取得官方 JSON；沒有修改 TLS／代理、登入、繞過封鎖或覆原資料。2026/1/1～7/24 查詢中，2884 一列：7/1、前收 34.45、除息參考 33.05、息值 1.400000、類別「息」。這提升的是該事件列與前收對帳資格，不是完整公司行動鏈。
3. 重新擷取六月與七月 STOCK_DAY，截止 7/24 共 38 筆、190 個 OHLCV 欄位，全等原保存資料；原來源完整 Git blob／SHA256 相符。7/1 收 32.90，較前收低 1.55 元，但較除息參考價低 0.15 元，不能將全部差額當賣壓。
4. 新取得一月至七月官方 FMTQIK；分析只取至 7/24 共 133 個收盤，日期與這段個股保存 K 完全對齊。這不等於已驗完整交易日曆。選加權指數僅作背景，不代表政策大盤指標已批准；截止收 43,654.84，視窗收盤高點 6/22 為 47,741.51。回落約 8.56%，相對 1/2 約上漲 48.74%；不由此代使用者判空頭。
5. 另產單次除息換算研究：僅 7/1 前 OHLC 乘 `(34.45-1.40)/34.45 = 33.05/34.45`，50 位 Decimal 商；量仍為原始股數。沿用既有 cash-only candidate 的公式背景，但本輪是另版研究、沒有呼叫／修改原還原引擎，也沒有選定正式政策調整法。

| 參照來源 | 原始高點 | 單次換算研究 | 除息後／來源後首次較高收盤 |
|---|---:|---:|---|
| 2026/2/26 當日高 | 35.50 | 約 34.06 | 7/6，收 34.45 |
| 2026/7/17 當日高 | 35.50 | 35.50 | 7/20，收 35.85 |

比較使用完整精度，表格只顯示兩位。兩個同價原高仍屬不同來源；前者的七月比較價不能混用舊 Raw 35.50。這是手動指定原高的事後比較，不是自動轉折、正式整帶、成功突破或交易資格。六月本來已有越過二月原高的舊事實保留；表中「首次」特指本輪除息後／指定來源後範圍，非該參照生命週期首次突破。新換算不倒填成歷史當時訊號。

## 成品

- [三頁可放大 PDF](output/pdf/b-basis-source-review.pdf)：大盤收盤線、原始 K 量、單次除息研究 K 量。
- [大盤背景](market-context.png)、[原始參照](raw-reference.png)、[換算參照](single-event-reference.png)。
- [數值證據](evidence.json)、[比較資料](comparison-data.json)、[原始擷取及 SHA](source-capture.json)、[42 項核對](verification.json)、[視覺檢查](manual-qa.json)、[恢復稽核](recovery-audit.json)。

三張皆 1/2～7/24，超過六個月；兩 K 圖同一 133 根、同樣價格軸，未使用截止後價格補證。網路月報原件含七月完整資料；研究嚴格裁至 7/24。指數僅取得收盤資料，明示畫收盤線，不冒充 K 線。

## 驗證與範圍

實跑新 study 1 次、builder 3 次（第二次移開事件標籤並改字型嵌入方式，第三次驗原子寫入）、verifier 4 次；前兩次 39 項，補圖檔完整性後兩次皆 42 項通過。首次 PDF 渲染有字型嵌入類型警告，第二次已消除；交付前另發現第三張 PNG 不完整，先由完整 PDF 恢復，再補 PNG/PDF 暫存檢查後替換機制，第三次 builder 正常完成，三 PNG 完整性皆通過。最終三頁重新渲染並全看。驗證含原 blob／11 原件 SHA、38 OHLCV 對帳、同日序列、獨立有理數判跨、七截止前綴及未來價量污染、7/1 事件不回填六月、股數不變、輸入不變與三頁向量結構。這些驗證資料與研究計算，不是分類準確率、策略成效或新產品驗收。

## 仍未完成

- 完整公司行動鏈仍未認證；TWT49U 自列不含除息併案退還股款減資／分割減資，不能拿此表證全部事件不存在。2025 全年該表另取得 2884 的 7/22 權息列；未因此解釋 10/27 急變或 11/6 X 註記。含 2025 年事件的更長圖尚未建立完整同口徑。
- 官方事件列擷取時點是 10/22，歷史公告時間未認證；表內最近財報欄亦屬當前資訊，本研究未用這些欄位。
- 本輪是單次事件換算，`complete_adjusted_history=false`；舊 Raw 圖仍保持其原資格。新政策完成資格仍不足，不能稱已依政策選定 Raw／Adjusted。
- 大盤指標、空頭定義／生效及約 2～3 月期滿切換、正式因子方法仍未定；市場身份 `NOT_ESTABLISHED`、政策首選口徑 null，無自動切換。
- 原分類 `NOT_VALIDATED`、用途 `NOT_ESTABLISHED`、行動／閉環 `NOT_EVALUATED`、新 Android `NOT_TESTED_NEW_BUILD`；`historical_signal_eligible=false`。原 source_gaps 保持，沒有補假 K 或解除舊限制。

下一步仍 Work：先在本輪充分大盤圖上釐清使用者所稱空頭的具體範圍，再擴增對照與可核還原來源；原右往左完整帶、量非硬門檻及所有已答案例維持。不要重問 2～3 月口徑方向、B 甲乙、A／ABC／G2 或微小段。研究版本可供看圖，未經確認不可當正式市況／完整還原產品功能。

## 重現

不需重跑全專案；從完整版本庫根執行（只會重建本輪獨立研究輸出）：

```bash
python docs/visual-discussion/20261022_b_basis_source_work_review/study.py --source docs/visual-discussion/20261020_independent_source_levels_work_review/source-data-2884.json
python docs/visual-discussion/20261022_b_basis_source_work_review/build_figures.py --font /path/to/NotoSansCJKtc-Regular.otf
python docs/visual-discussion/20261022_b_basis_source_work_review/verify.py --source docs/visual-discussion/20261020_independent_source_levels_work_review/source-data-2884.json
```

圖形腳本需 matplotlib、驗證 PDF 結構需 pypdf，字型來自 Noto CJK（來源見 figure-manifest）。原件已保存；`fetch_sources.py` 僅在原件不存在時建立，既有檔案拒絕覆寫、每查詢最多兩次。本輪 11 個查詢皆首次 HTTP 200；事先探測三讀取成功後正式擷取一次。最初探測曾因系統 Python 沒有 requests 而未發出網路請求，改用標準庫 urllib 完成，無新增套件。
