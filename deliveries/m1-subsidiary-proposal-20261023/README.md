# 台泥子公司IPO方案來源0.10交付

完整來源／工程／實測：[研究入口](../../股票系統M1_v0_18/rotation_research/subsidiary_proposal_20261023/README.md)、[報告](../../股票系統M1_v0_18/rotation_research/subsidiary_proposal_20261023/REPORT.md)、[完整Work唯讀續接指令](../../股票系統M1_v0_18/rotation_research/subsidiary_proposal_20261023/WORK_HANDOFF.md)。固定工程SHA與逐檔GitHub原bytes回讀見 [GITHUB_READBACK.md](GITHUB_READBACK.md)／[JSON](GITHUB_READBACK.json)。

- [下載離線來源包](m1-subsidiary-proposal-v010-20261023.zip?raw=true)；40,112,206bytes（約38.25MiB，超過32MiB，未宣稱小於32MiB）。
- SHA256：`60fc2b6a4987e9ceb1dc0b49bfeea6358779bf5a6b397ec0f5d5fe492a157669`，另見 [SHA256SUMS](SHA256SUMS)。
- 762成員／12層manifest；原0.9全部723成員逐位元保留，舊成品不改。兩新PDF、原meta、原生文字、五頁人工視讀PNG、source-only程式／測試、精確parent鏈、真保存輸入與警告／限制均在包內。
- [新解壓驗證](package-verification.json)：CRC、唯一安全路徑、全部manifest、舊成員、全新解壓53測試與離線producer通過；同53不累加106，所有成員在重驗後bytes不變。
- 本輪實跑24新增＋29父版相關回歸＝53，詳 [解壓測試](extracted-tests.log)；[解壓producer](extracted-producer.log)實算70拒算／2不足／8換股影響未支援／真正總淨報酬合格0，daily／journal空、六方案0。舊60不是本輪重跑。

解壓到全新目錄，先讀SUBSIDIARY_PROPOSAL_START_HERE.md，再於股票系統M1_v0_18執行：

```bash
python3 -m unittest rotation_research.test_subsidiary_proposal rotation_research.test_capital_components -v
python3 -m rotation_research.subsidiary_proposal_sources
```

不需網路／PDF工具／瀏覽器。查看兩PDF與visual/五頁、visual-review／catalog-v010可核來源及場次矛盾。這是來源研究包，沒有新UI，不需重開手機驗收；Android NOT_TESTED_NEW_BUILD，沒有新每日淨帳或六方案績效。來源包不是完整checkout，勿覆寫專案；工程先依最新AGENTS bootstrap。

僅1101公司報告子公司Cimpor International Holdings海外IPO方案通過／授權，非IPO完成或個人1101股東減資／配股／退資／零影響。議事錄四頁掃描原native只有4個formfeed，人工盤點非OCR，詳細掃描條款parser未實作；表決一頁native已核。第一次／第二次／未載場次矛盾保留，canonical_meeting_ordinal=null。94.74%只投票比例，原四列百分比合計99.98不正規化。

會議日10/13、Last-Modified10/19、PDF建立與捕捉不證公告／10/16前可得，announced_at／actual_effective_at=null。個人款股、最終日期數量、淨額與帳務影響未知；完整公司行動、個人權利及全部parent缺口保持。Work附件／meta未取得未讀，Work時點僅使用者陳述，work_github_readback_at=null。原策略／引擎／庫／歷史／舊頁成品／main不變；受拒入口不重試繞過，不部署、付費、交易、訊息或子代理。
