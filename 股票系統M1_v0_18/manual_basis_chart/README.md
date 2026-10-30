# 人工分析模式 0.1（獨立研究主圖）

以原保存 0.4.3 淡底色主圖為固定父版，新增人工選擇「原始日 K／還原 K（研究候選）」。模式是分析資料選擇，並非顯示標籤。新頁載入相符的保存 K、均線、MACD、價量結構與人工標註；缺資料、日期或多來源時停在待選／不可用，不轉用另一模式或日期。市場空頭分類不參與切換。

父版 ZIP SHA-256：`ee5362de516d52f43b2d09f76b46c04345fd147a2beced4a32e208fbfaf41212`。建置保留其 36,717,209 bytes interned 數值 JSON；壓縮後在單頁內解壓，原數值樹位元組相同。新解析層僅有 6,344 個已存 frame 的精確來源對照，沒有新價格、指標、策略或交易引擎計算。

## 範圍

| 個股 | 原始日 K | 還原 K 研究候選 |
|---|---|---|
| 1101、2884 | 既存短期保存結果，以及 2021-10-18～2026-10-16 官方原始五年候選 | 無，要求時明示不可用 |
| 6488、8069 | 同上 | 既存 2025-08-01～2026-09-30 的現金事件候選 283 根；不是完整公司行動驗證 |

原始候選的短期與五年來源在重疊日會要求再選「資料來源」。新五年 Raw 的官方歷史／公司行動及原始資料缺口仍依舊報告限制；Adjusted 來源缺少完整公司行動鏈、調整方法版本及歷史發布可得驗證，故顯示 `NOT_RECORDED_IN_SOURCE_SEE_SAVED_PROJECTION`，不假稱完整還原。量沿既存原口徑，不生成還原量。

## 使用

下載交付 ZIP 後解壓，透過本機 HTTP 伺服器開啟 HTML（例如於解壓目錄執行 `python3 -m http.server 8765 --bind 127.0.0.1`）。先選模式，再選資料來源／精確日期；「使用最後保存日」只在人工點擊後改日期。切換個股保留目前模式；無來源時空白且停用主圖，並保留該次人工選擇。頁面儲存在同一瀏覽器的 localStorage，可下載 JSON 留存；它不是雲端或跨裝置同步，儲存失敗有明確訊息。以前保存的分析數值不被修改。

`manual_basis` 是獨立的純解析及不可覆寫選擇紀錄層，與瀏覽器分離：

```bash
python3 -m manual_basis.cli LOOKUP --catalogue catalogue.json --request request.json
python3 -m manual_basis.cli SAVE --catalogue catalogue.json --request request.json --journal /your/choice-records
python3 -m manual_basis.cli READ --journal /your/choice-records --selection-id your-id
```

`request.json` 必須明示 `schema_version=manual-basis-request/0.1`、`selection_id`、含時區 `selected_at`、`code`、`price_mode`、`as_of`、`series_key`（可為 null）；來源重疊時要填精確 key。LOOKUP/SAVE 均不執行數值引擎；SAVE 僅以新 ID 建不可覆寫 JSON，READ 核對內容雜湊與身分，不自動挑新版本。瀏覽器下載的 `request` 可單獨送至此 CLI，UI 匯出同時附父版保存 selection 作逐項核對。檔案讀寫失敗時不可推論成功。

重建：`python3 -m manual_basis_chart.build --output-dir manual_basis_chart/output/NEW_EMPTY_DIRECTORY`。輸出若已有不同內容會拒絕覆寫。已驗證輸出與測試見 `validation_20261022/驗收報告.md`。實體 Android、新資料完整性、圖形辨識品質、交易資格與資金飛輪均未因此驗證。B 案使用者未指定哪一模式，仍不代選。
