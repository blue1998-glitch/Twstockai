# 一次承接已保存的來源與研究選擇

既有 `research_operation` 現在提供明示IMPORT：完整0.4來源與既有choice 0.2原樣存入同一操作，之後可沿原READ讀回。不重新生成候選或選擇，不改帳、不接成交。原RUN與舊READ保持相容。

- [契約](CONTRACT.md)、[結果與限制](REPORT.md)。
- [B93條件匯入請求](cases/conditional-full/input.json)／[IMPORT結果](actual/conditional-full/import.json)／[READ](actual/conditional-full/read.json)。
- [B2一般意圖](actual/general-full/read.json)、[原checkpoint及全部token](actual/checkpoint-new-trigger/read.json)、[UNKNOWN保持拒絕](actual/outer-unknown/read.json)。
- [19案摘要](actual/summary.json)、[原帳與來源核對](validation/originals.json)、[四階段UNKNOWN](validation/storage-unknown.json)、[缺漏與錯鏈](validation/missing-and-crossed.json)。
- [實作前凍結](frozen.json)、[來源指紋](intake.json)、[actual版本](actual/source-versions.json)、[本輪測試](tests-initial.log)。

在股票系統M1_v0_18下可直接使用原CLI：

```bash
python -B -m capital_research.research_operation_cli IMPORT --store /tmp/twstockai-operation-import --id explicit-B93 --input capital_research/operation_import_20261030/cases/conditional-full/input.json --format json
python -B -m capital_research.research_operation_cli READ --store /tmp/twstockai-operation-import --id explicit-B93 --format json
```

IMPORT請求只含明示schema／synthetic／saved_source／choice。來源與choice已完整保存在例子內，不需使用者搬檔或重跑producer。程式API為 `import_operation(root, identity, request)`；Journal四階段沿原key，generation階段實際保存明示舊來源，不產生新數值。來源、單位／搜尋收據、原帳權利／reserve、latest與全部token均在原件中保留。

相同ID已存在就停，必須明示READ；異內容同ID拒絕。UNKNOWN不是保存成功，也不自動續跑。缺檔顯示不完整或無法讀取，不從header副本補檔。既有REFUSED可完成保存而仍顯示CHOICE_REFUSED，CLI退出碼2表示意圖未獲准，不能當成未保存或改選成功。

一般／條件／拒絕意圖及保存狀態分開；條件意圖仍須交割後重評，沒有可直接執行的訂單。僅合成機制，不認證來源或策略績效。新IMPORT結果未接補選、多份比較或成交；本項結清後不自行增加同類READ工具。人工操作不需要。
