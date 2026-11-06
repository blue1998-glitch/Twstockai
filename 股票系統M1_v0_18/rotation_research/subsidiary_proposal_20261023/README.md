# 台泥子公司IPO方案來源研究0.10

兩份官方PDF已由唯一既有Codex各一次HTTP200取得，實際大小及SHA與使用者提供的Work比對資料相同；不是依摘要或SHA字串冒稱取得。先讀 [CONTRACT.md](CONTRACT.md)、[REPORT.md](REPORT.md)、[WORK_HANDOFF.md](WORK_HANDOFF.md)。原件、meta、native在raw/，五頁實際視讀PNG在visual/；visual-review明示人工盤點，不冒充OCR或原生文字。

新純事實層 `../subsidiary_proposal.py`、離線producer `../subsidiary_proposal_sources.py`，精確嵌入完整parent0.9 `sha256:673e0815cc9f1372ab187c7aa93c9a5ad1f746a45bf87ea4687d4b2e7be048f3`。本版catalog ID：`sha256:4fd79d2e1f42e6009876bd76fd646f1037620a749e0fe827b3234a9fc677ac00`。

只記1101公司報告之Cimpor International Holdings海外IPO方案通過／授權；不是IPO完成、1101普通股股東減資或配股。索引／路徑第一次、議事錄p1第二次、表決未載場次的矛盾原樣保留，canonical_meeting_ordinal=null。94.74%只是投票比例；原百分比合計99.98不改成100。兩來源只連一個來源案例，新增帳務事件／獨立市場樣本0。

在股票系統M1_v0_18目錄，標準Python離線重現：

```bash
python3 -m unittest rotation_research.test_subsidiary_proposal rotation_research.test_capital_components -v
python3 -m rotation_research.subsidiary_proposal_sources
```

本輪24新＋實跑0.9相關29＝53項通過；全新解壓重驗同53不累加。原60屬歷史，未冒本輪重跑。producer核122價量原件／16日曆，按實際輸入重算70拒算／2不足／8換股影響未支援／合格總淨報酬0，daily／journal空、numeric replay／六方案0。個人款股、最終數量日期、淨分配與期初權利未知；Raw、缺價、舊UNKNOWN及原parent null不變。

詳細掃描條款自動parser未實作，本輪只人工盤點並核票數與原文；沒有新UI／Android測試。下載、manifest與解壓驗證及固定逐檔GitHub讀回見 [delivery](../../../deliveries/m1-subsidiary-proposal-20261023/README.md)。來源包不是完整checkout，勿覆寫專案；工程依最新AGENTS重新bootstrap。
