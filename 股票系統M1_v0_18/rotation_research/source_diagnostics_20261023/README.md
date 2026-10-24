# 獨立來源診斷／資格附層 0.5

接續固定0d6e86a及正式0.4 dae1f6e。這是新來源診斷，不取代正式action_resolution／action_resolution_sources，不使用本地平行草稿。無UI、無新淨帳或策略績效。

- [實作、實測、失敗與限制](REPORT.md)、[契約](CONTRACT.md)、[完整Work唯讀續接](WORK_HANDOFF.md)。
- [來源欄位／精確parent0.4](catalog-v05.json)、[兩缺價日診斷](missing-quotes.json)、[70窗拒算](window-qualification.json)、[實跑摘要](verification.json)。
- [原件與擷取metadata](source-manifest.json)、[定向61測試](tests.log)、[PDF視讀範圍](visual-review.json)、[失敗紀錄](diagnostics.json)、[網路草稿未套用](network-configuration.json)。
- 可下載完整離線重現包：repository根 `deliveries/m1-source-diagnostics-20261023/README.md`；包含前代原包，不需網路取來源。

完整checkout工程先在根依AGENTS重新bootstrap成功。重現請用新解壓資料夾，進入 `股票系統M1_v0_18`：

```bash
python3 -m unittest rotation_research.test_source_diagnostics rotation_research.test_action_resolution rotation_research.test_resolution_validation -v
python3 -m rotation_research.source_diagnostics_sources
```

30新＋31正式回歸＝61項本輪實測；不能加上未重跑的舊測試數字。producer只寫本新目錄，既有結果不同即拒覆寫，相同則不寫。純核心source_diagnostics不讀檔、不連網、不回放數值帳；來源producer離線核原件及原0.4。

6個明示URL各嘗試一次：取得3份PDF，另3網域代理403。附件ZIP本環境不可見；沒有讀Work包內facts或文字副本，也未整包覆蓋。台泥復牌文件不能取代未取得的停牌起日原件；兩缺價日的新、舊原因仍UNKNOWN、Raw仍null。一般法律API只測合成契約，沒有取得或驗過真實API回應。

70窗仍拒算、2不足、8換股影響未支援、真正總淨報酬合格0。公司發放完成不是個人收款，預計新股不是發行完成，員工與原2867權利不能加到既有2884股東。完整行動／減資、7/25後權息、個人淨額及九起日期初權利仍缺。
