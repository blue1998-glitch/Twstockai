# 獨立來源附層0.7：實際取得三份新官方原件

使用者發布環境後，Codex唯讀核runtime spec4／observed4，按本輪明示授權僅重試三個新來源精確URL，各一次，均HTTP200。無須使用者搬檔或再調設定。舊CONNECT403 checkpoint及所有受拒入口保持，這不是其他入口限制解除。

先讀 [REPORT.md](REPORT.md)、[CONTRACT.md](CONTRACT.md) 與 [WORK_HANDOFF.md](WORK_HANDOFF.md)。來源bytes／URL／HTTP／要求、完成、捕捉、讀回時間及Work比較值見 [source-manifest.json](source-manifest.json)、raw各meta；原件在raw/*.response。PDF抽字、實際檢視六頁PNG在raw／visual；[visual-review.json](visual-review.json) 記範圍。新觀察不倒填announced_at或歷史可得。

新純數值模組 `../source_followup.py`，離線producer `../source_followup_sources.py`，29新測試 `../test_source_followup.py`。精確嵌入parent0.6，原0.6／0.5／正式action_resolution0.4／0.3完整保留。catalog-v07.json含三來源、五個不同角色觀察，不是五個獨立公司行動；來源缺口與coverage不變。

在股票系統M1_v0_18執行：

```bash
python3 -m unittest rotation_research.test_source_followup rotation_research.test_offline_source_bridge -v
python3 -m rotation_research.source_followup_sources
```

此離線命令不請求網路、不重抽PDF、不需瀏覽器；現有凍結輸出若不同就拒寫。完整checkout工程前仍先依根AGENTS重新bootstrap。下載／SHA／全新解壓與固定GitHub逐檔回讀見 [delivery](../../../deliveries/m1-source-followup-20261023/README.md)。舊成品均保留。

本輪29新＋重跑0.6相關30＝59項通過；全新解壓同59項不加總成118。舊61項與前輪91項不冒稱本輪全重跑。本輪70窗實際資格檢查仍70拒算、2不足、8換股影響未支援、真正總淨報酬合格0，daily／journal空，numeric replay／六方案0。無新UI、瀏覽器或Android驗收。
