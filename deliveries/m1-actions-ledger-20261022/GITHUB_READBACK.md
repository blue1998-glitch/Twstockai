# GitHub固定交付與逐檔回讀（2026-10-22）

儲存庫blue1998-glitch/Twstockai，分支dev/m1-v018-chart-annotations。

- 使用者已核起點：354a9c01dd37209b6397bb9ca5daa24617216e48，已確認為所有本輪提交祖先。
- 官方原件事件表節點：e3cadaf88ff6cf3a62374df262f73ad6b5a26c1a，6檔逐位元GitHub讀回已保存。
- **固定完整成品：ced3cc531084cee1b666b05d33e5eb90275edfff**，從e3cadaf正常提交／非強制推送；提交前核對遠端預期父提交，沒有從main或舊ZIP覆寫。
- 成品提交與初始354a9c01相比的全部44個變更檔案，均用固定SHA的raw.githubusercontent.com URL實際下載；HTTP200、檔案長度／SHA256及本地bytes全部相同，無失敗。逐檔URL、指紋與核對時點見 [GITHUB_READBACK.json](GITHUB_READBACK.json)。來源節點的事件原件數不是本次變更檔數。
- 下載包已從GitHub讀回498439 bytes，SHA256 b31bb240bd47536ab03fb627da37f0ceaa0d33460328caa328d38428d3ac80b5；本地CRC、293成員與manifest292檔SHA全通過。在新目錄解壓44測試全通過、資料研究重現後292檔仍逐位元一致。
- 分支ref在讀回前後皆指向ced3cc531084cee1b666b05d33e5eb90275edfff。main仍9c5b168c09ba80010c74f03b9c537e8b7474256a，未改。

[固定成品ZIP](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/ced3cc531084cee1b666b05d33e5eb90275edfff/deliveries/m1-actions-ledger-20261022/m1-actions-ledger-v01-20261022.zip) · [固定事件表](https://github.com/blue1998-glitch/Twstockai/blob/ced3cc531084cee1b666b05d33e5eb90275edfff/股票系統M1_v0_18/rotation_research/action_data_20261022/events.json) · [固定實測報告](https://github.com/blue1998-glitch/Twstockai/blob/ced3cc531084cee1b666b05d33e5eb90275edfff/股票系統M1_v0_18/rotation_research/action_data_20261022/REPORT.md)

本收據在成品之後單獨保存；收據自身最新提交請查分支ref，不與固定成品SHA混淆，也不宣稱自指指紋。舊P1-7交付完全保留，根三入口及rotation三交接只前加新狀態並保留舊原文；起點2990追蹤檔，2984檔bytes不變、6文件原文後綴完整、無刪除，細節preservation-audit.json。

**會計工程測試通過不等於來源／投資策略合格**：本輪44新測試、122原件核對及70拒算＋2不足是實際結果；舊18／9982／Chrome36沒有重跑。真實總淨報酬比較合格0、無新策略績效或勝出比例。完整行動／配股比及可交易日／淨分配／日曆／期初權利仍缺；一次官方PDF403具體保存，不繞過。無新瀏覽器／Android，正式分類、全換／分批／飛輪與SQLite未知照留。

下一步Codex補有來源的資料後再接顯式成交比較；完整可貼Work指令在股票系統M1_v0_18/rotation_research/action_data_20261022/WORK_HANDOFF.md。不可因已新增事件帳就再重問P0～P1答案或擅自訂參數。main、原引擎／策略／庫／歷史／舊頁／舊ZIP保持；不部署付費交易訊息或子代理。
