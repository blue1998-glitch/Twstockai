# 公司分項來源研究0.9

入口：[CONTRACT.md](CONTRACT.md)、[REPORT.md](REPORT.md)、[WORK_HANDOFF.md](WORK_HANDOFF.md)。獨立純事實核心 `../capital_components.py`、離線producer `../capital_components_sources.py`、測試 `../test_capital_components.py`。

精確嵌入完整parent0.8：`sha256:77e3dfa0e10ff3b64f67e1613575c26158d814efe025753d5138c8b76641cd80`。所有舊版本、策略參數、引擎、庫、Raw／UNKNOWN歷史、原件、舊頁與成品保持。

只重用已存公開說明書原bytes（14,607,733bytes／SHA926f1f871a294702d3e4f5e4d89cf5aeb5e64808593efa2d99b95ed7375388fa），本輪未請求官方PDF、Follow-up或GitHub原PDF。實際重抽及視讀實體391／印刷11、456／印刷76，xref警告保留，765頁未全書視讀。

第391頁選2024-12-31餘額之後、2025-12-31餘額之前的113年度盈餘分配：B9股東160,200仟股；N1員工18,000仟股，其普通股股本180,000／資本公積342,900／權益總額522,900皆仟元。第456頁明確選113年度（2024盈餘）、2025-03-07董事會及29.05元公司報告計算參照；另存114年度／2026-03-13／33.05元版本。

160,200＋18,000＝178,200仟股，與parent第461頁同一增資家族對帳；新三筆是來源角色觀察，新增交易事件及獨立市場樣本均0。個人未圓整比率／實配、畸零、可賣日、淨款及期初權利仍未知；原parent null不改，29.05不寫入Raw或估值。

在股票系統M1_v0_18離線重現：

```bash
python3 -m unittest rotation_research.test_capital_components rotation_research.test_source_contracts -v
python3 -m rotation_research.capital_components_sources
```

本輪29新＋實跑0.8相關31＝60項通過，與前輪60的組成不同，未沿用舊結果。新解壓同60不累加。producer重核122價量原件／16日曆，按保存輸入實算資格仍70拒算／2不足／8換股影響未支援／合格總淨報酬0，daily／journal空、numeric replay／六方案0，缺價診斷精確等parent。無新UI／Android驗收。

舊Work附件／meta本環境仍未取得／未讀，work_github_readback_at=null。使用者提供的Work本機重用觀察11:37:58.421958Z另記為USER_REPORTED_LOCAL_REUSE，不冒原官方捕捉／GitHub讀回。原捕捉、前輪Codex固定讀回、本輪Codex本機讀取及新研究觀察四者分存，announced_at不倒填。

下載、SHA、全新解壓及固定逐檔GitHub回讀見 [delivery](../../../deliveries/m1-capital-components-20261023/README.md)。不以離線包覆完整checkout；工程仍按最新AGENTS重新bootstrap。
