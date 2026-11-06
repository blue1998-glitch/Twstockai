# 本環境驗收固定提交逐檔GitHub回讀

指定分支：`dev/m1-v018-chart-annotations`。

- 正式金融工程固定提交：`dae1f6e580f466c4f44cb271a350f4b420d5b5eb`；後續既有收據`e3a76eb2eac8dfd50bb5f6b7794fb77d84224b30`完整保留。
- 本輪驗收／入口／新封包固定提交：`33fe700499f4ea951e3564902f36ef338bea8dc6`，父e3a76eb；未發布本地重複來源草稿。
- 本輪30個變更檔於2026-10-23T02:48:58.650092+00:00從固定GitHub raw逐檔讀回，HTTP200、完整位元與SHA全同，見[GITHUB_READBACK.json](GITHUB_READBACK.json)。含2個新增測試／打包helper、PDF差異與失敗、31測試、保存／交接、新ZIP及SHA。
- 正式金融成品28檔亦已獨立固定讀回，見[canonical-product-readback](../../股票系統M1_v0_18/rotation_research/resolution_validation_20261023/canonical-product-readback.json)；原兩份e3a76eb收據另核byte一致，見canonical-receipt-closure.json。
- 遠端分支核得本輪固定驗收提交；main仍`9c5b168c09ba80010c74f03b9c537e8b7474256a`。

[直接下載固定驗收包](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/33fe700499f4ea951e3564902f36ef338bea8dc6/deliveries/m1-resolution-validation-20261023/m1-resolution-verified-v04-20261023.zip)，6,697,710bytes；[SHA256SUMS](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/33fe700499f4ea951e3564902f36ef338bea8dc6/deliveries/m1-resolution-validation-20261023/SHA256SUMS)。SHA256 `526d6510e5c2ce416565c11e2389e9f2df9e270b546720e11f6a14d3071e14a9`。

本環境正式29＋新增2＝31項通過；新封包解壓重驗同31與正式producer通過，不當62項獨立測試。原511成員逐位元相同，六層manifest527／510／469／409／374／292全通過。正式金融程式／catalog／舊數值結果／ZIP未改，僅新增驗收與入口前綴，見entrypoint-preservation.json。

新解壓producer實跑70窗仍拒算、2不足、8換股影響未支援，真正總淨報酬0合格、numeric replay／六方案0。股東會批准與每人總額圓整已接，但假想毛額不等淨額／到款／期初權利。PDF全文byte差異與首個assert失敗保持，所用頁／正式解析欄位精確同；保存helper工作目錄錯誤亦已記錄修正。沒有新官方請求、安全拒絕重試、UI／Android。

下一步Work補來源，明確工程Codex；[完整可貼指令](../../股票系統M1_v0_18/rotation_research/resolution_validation_20261023/WORK_HANDOFF.md)。完整覆蓋、實配／可賣日／零股、最終調整與稅務、淨分配／期初權利仍缺。原0.3及所有策略、引擎、庫、歷史與main保持。

此收據兩檔後續另提交，避免自含提交SHA；推送後實際讀回兩檔並核分支頭後，才提供最新已核提交。
