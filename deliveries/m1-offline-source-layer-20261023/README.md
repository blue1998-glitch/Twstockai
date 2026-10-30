# 離線原件來源附層0.6成品

- [下載ZIP](m1-offline-source-layer-v06-20261023.zip?raw=true)，23,916,142bytes（約23.9MB）。
- [SHA256SUMS](SHA256SUMS)：`e6398a1ee7863e72e0f236b51213ff21a9a2892cbc6841b79789f49a72d1e496`。
- [封包收據](bundle-receipt.json)、[新解壓實測](package-verification.json)、[91測試log](extracted-tests.log)、[離線producer](extracted-producer.log)。
- [實作／失敗／未完成報告](../../股票系統M1_v0_18/rotation_research/offline_source_bridge_20261023/REPORT.md)、[契約](../../股票系統M1_v0_18/rotation_research/offline_source_bridge_20261023/CONTRACT.md)、[完整Work唯讀續接](../../股票系統M1_v0_18/rotation_research/offline_source_bridge_20261023/WORK_HANDOFF.md)。
- [固定提交逐檔GitHub回讀](GITHUB_READBACK.md)，產品推送與實際回讀後另提交收據，避免自指SHA。

606成員，原來源0.5包575成員逐位元保留，新舊8個manifest全通過。含原橋接ZIP941229bytes，SHA與使用者指定相同；橋接41成員／40manifest已實核。原前身大包91項只屬Work核對證詞，不冒稱本輪Codex重驗前身大包。

解壓至新目錄，先讀OFFLINE_SOURCE_BRIDGE_START_HERE.md，進入股票系統M1_v0_18，標準Python離線：

```bash
python3 -m unittest rotation_research.test_offline_source_bridge rotation_research.test_source_diagnostics rotation_research.test_action_resolution rotation_research.test_resolution_validation -v
python3 -m rotation_research.offline_source_bridge_sources
```

完整checkout與新解壓皆實跑91項（30新＋61本輪重跑回歸），是同91測試重驗，不加成182個不同測試。新解壓producer再核70資格，70拒算、2不足、8換股影響未支援、真正總淨報酬合格0，全部封包成員重驗後byte exact。不需網路／pdftotext／瀏覽器。

新診斷實際接入1101自8/13、2884自11/5停牌起日，保留舊UNKNOWN／Raw null，不推終點／整段、不補價／估值或解除缺價拒算。真財政部API與官方page／script／query鏈已驗，一般函釋不代表台泥細項或個人免稅／淨到款；capture與ingestion時點分存。正式0.4、parent0.5／0.3、原策略／引擎／庫／資料／歷史／舊成品及main保持，沒有新UI／Android、每日數值帳、六方案或績效。

仍缺直接玉山復牌、完整行動減資及7/25後權息、2884實配／可賣／畸零與既有股東換股影響、台泥最後調整與稅務細項、個人淨分配及九起日期初權利。禁止入口及三網域403未重試，網路草稿未套用。下一步Work唯讀補來源；工程只回原既有唯一Codex。
