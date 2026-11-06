# 離線原件來源附層0.6

接續遠端f65a894，已保留a52cff2接收阻礙checkpoint與8aecb50／f65a894橋接附件交付。這次已實際取得ZIP原始bytes，不再停在附件不可見；舊阻礙紀錄保留為歷史。

- [來源契約](CONTRACT.md)、[本輪實作／實測／失敗及限制](REPORT.md)、[完整Work唯讀續接](WORK_HANDOFF.md)。
- [精確parent0.5與新來源](catalog-v06.json)、[兩缺價日新診斷](missing-quotes.json)、[資格拒算](window-qualification.json)、[實跑摘要](verification.json)。
- [本次GitHub原件取得](bridge-acquisition.json)、[91項實測](tests.log)、[首輪失敗](tests-initial.log)、[原parser相容性診斷](compatibility-diagnostic.json)、[兩PDF重抽／視讀](pdf-extraction-verification.json)。
- 下載／SHA／新解壓驗證及固定GitHub回讀：根 `deliveries/m1-offline-source-layer-20261023/README.md`。

新純數值 `offline_source_bridge.py`，外部離線 `offline_source_bridge_sources.py`；精確嵌入parent0.5，原0.5／正式action_resolution 0.4／parent0.3、原引擎策略與資料不改。實際橋接41成員，40manifest列項全核；原研究包91項只屬Work封存證詞，Codex本輪未取得完整前身大包，不冒稱重新驗全部91項。

完整checkout工程依最新AGENTS先重新bootstrap成功。重現使用新解壓目錄，進入股票系統M1_v0_18：

```bash
python3 -m unittest rotation_research.test_offline_source_bridge rotation_research.test_source_diagnostics rotation_research.test_action_resolution rotation_research.test_resolution_validation -v
python3 -m rotation_research.offline_source_bridge_sources
```

標準Python離線即可；原件ZIP、抽字及觀察紀錄均已封存。producer不連線官方、不重抽PDF、不覆寫不同結果，原觀察時點與固定GitHub讀回時點分存。30新測試加本輪實際重跑61舊回歸，共91項；新解壓是同91項重驗，不加總成182項。

新診斷證1101自2025/8/13、2884自2025/11/5起停牌，只限起日；復牌與終點不自動推定。新原因附於原UNKNOWN診斷之外，Raw null／缺價拒算／execution_qualified=false保持。真實API接入只證一般函釋，非台泥最細資金來源、個人稅籍／免稅／零稅費／淨入帳。70拒算、2不足、8換股影響未支援、真正總淨報酬合格0，沒有每日數值帳／六方案或新UI／Android。
