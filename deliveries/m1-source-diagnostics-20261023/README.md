# 來源診斷／資格0.5離線成品

- [下載ZIP](m1-source-diagnostics-v05-20261023.zip?raw=true)（22,611,030bytes；約22.6MB）
- [SHA256SUMS](SHA256SUMS)：`7144793cb2e359b7536fa72dd2c764144e4aee4a6aa3e986eabcaa785435a36d`
- [封包收據](bundle-receipt.json)、[新解壓實測](package-verification.json)、[61測試](extracted-tests.log)、[離線producer](extracted-producer.log)。
- [本輪工程報告](../../股票系統M1_v0_18/rotation_research/source_diagnostics_20261023/REPORT.md)、[契約](../../股票系統M1_v0_18/rotation_research/source_diagnostics_20261023/CONTRACT.md)、[完整Work唯讀續接](../../股票系統M1_v0_18/rotation_research/source_diagnostics_20261023/WORK_HANDOFF.md)。
- [固定GitHub逐檔回讀](GITHUB_READBACK.md)於產品提交推送並逐檔讀回成功後，另提交收據，避免自指SHA。

共575成員；原正式0.4完整驗收包528成員逐位元保留，新舊七manifest全部通過。新資料夾解壓後，先讀SOURCE_DIAGNOSTICS_START_HERE.md，進入股票系統M1_v0_18執行：

```bash
python3 -m unittest rotation_research.test_source_diagnostics rotation_research.test_action_resolution rotation_research.test_resolution_validation -v
python3 -m rotation_research.source_diagnostics_sources
```

標準Python離線即可，不需網路或重抽PDF。本輪在完整checkout與新解壓各執行61項，為同61測試重驗，不加成122個不同測試。新解壓producer實跑70拒算、2不足、8換股影響未支援、真正總淨報酬合格0；重驗後全部封包成員仍byte exact。

新獨立source_diagnostics不取代正式0.4，3實際PDF／5來源觀察不是5獨立行動。台泥8/14復牌不證8/13停牌起日，兩缺價日仍UNKNOWN／Raw null。另三網域代理403原件未取得，法律API只是合成測試。預計換股、員工登記／基準、公司報告發放不等個人實配／淨入帳／完整期間行動。

這不是新UI或市場績效。無新Android驗收，不需要重做舊手機截圖。完整1101／2884行動減資、7/25後權息、2884直接實配／可賣／畸零／既有股東換股影響、台泥最後調整及稅務、個人淨額及九起日期初權利仍缺。原策略／引擎／庫／資料／歷史／舊頁ZIP與main保存。下一步Work唯讀補來源，工程只回既有唯一Codex。
