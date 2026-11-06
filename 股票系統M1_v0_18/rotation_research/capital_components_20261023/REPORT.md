# 本輪工程與實測

本既有唯一Codex從遠端4f9b10603756419b11f7bb90e39ba9a721fd8c74接續，已核包含固定0.8工程776877b98f0938ec1d4e789fcd8a34b145d90dea，沒有後續待合併；main仍9c5b168c09ba80010c74f03b9c537e8b7474256a。重新bootstrap成功0補缺／7差異保留後才工程，既有未追蹤歷史產物未動。Work本輪沒有bootstrap、工程、產品測試或寫入。

官方原件新增0、官方及原PDF GitHub請求0。重用已存公開說明書14,607,733bytes、SHA926f1f871a294702d3e4f5e4d89cf5aeb5e64808593efa2d99b95ed7375388fa與原meta／全文native，沒有重抓官方PDF或2026Follow-up。兩頁實際pdftotext -layout重抽，與原全文對應頁逐位元同；兩頁pdftoppm轉圖後已視讀，所有return0，抽字及轉圖均留xref num5429重建警告，本輪無Fontconfig警告。原PDF不改，765頁未全書核閱。

新增獨立capital_components純事實核心／離線producer、catalog-v09、component-reconciliation與來源／精度／時間角色紀錄，精確嵌完整parent0.8。三筆觀察只涵蓋公司股東群組、員工群組與董事會計算參照；不增加個人權利、交易事件或市場樣本，不改parent的null。

| 來源 | 明確選取 | 公司層級新事實 |
| --- | --- | --- |
| 實體391／印刷11 | Z1 113/12/31後、Z1 114/12/31前，113年度盈餘分配 | B9 160,200仟股；N1 18,000仟股；N1股本180,000／資本公積342,900／總權益522,900仟元 |
| 實體456／印刷76 | 113年度，114/3/7董事會 | 員工18,000仟股、29.05元公司報告計算參照 |
| 同頁另一版 | 114年度，115/3/13董事會 | 33.05元另存，不借給113年度 |

160,200＋18,000＝178,200仟股只同一增資來源家族對帳，連parent第461頁；員工科目180,000＋342,900＝522,900仟元。未由酬勞除面額反推股數，29.05未補Raw／個人交易價／估值，也未由年末股數或總額推出個人比率。

首次真原文解析probe失敗：先移除所有空白導致前列餘額253474357與113年度標題黏接。已改保留native列邊界後核年度標題，數值／日期／原件不改；parser-initial-diagnostic.json保留原因與修正，並有對應回歸反例。此時產品測試尚未跑；其後首輪29項新測全通過，最終29新＋本輪實跑0.8相關31＝60項通過。前輪60＝31新＋29回歸屬歷史，不能因總數相同混稱沿用；新解壓同60也不加總120。

實際執行：

```bash
python3 codex/bootstrap_m1.py --hydrate-missing
# 在 股票系統M1_v0_18
python3 -m unittest rotation_research.test_capital_components -v
python3 -m unittest rotation_research.test_capital_components rotation_research.test_source_contracts -v
python3 -m rotation_research.capital_components_sources
```

測試涵蓋雙年界線／年度與日期欄配對、十一欄／股數金額單位、持有人與instrument、來源／meta／原件竄改拒用、公司分項不借個人、同家族不重計、精確parent與舊null、時間角色及全旗標不能覆來源缺口。合成竄改只是反例，不是市場樣本。

producer實核122價量原件／16日曆，依保存design／實際輸入重算70資格呼叫皆拒算、2不足、8換股影響未支援、真正總淨報酬0；由window rows核統計，沒有硬編摘要。daily／journal空、numeric replay／六方案0，缺價診斷精確等parent0.8，execution_qualified=false及估值null保持。

原官方捕捉、前輪Codex固定讀回、本輪本機讀取／研究觀察分存。使用者提供Work本機重用時間11:37:58.421958Z只記使用者陳述，沒有把它當官方或GitHub時點。舊Work附件／meta本環境仍未取得／未讀，work_github_readback_at=null；可見附件仍只有舊v0.17包，未要求手機搬檔。announced_at／歷史可得不倒填。

公司分組股數本輪已核，但個人未圓整比率、實配、股利畸零期限／處置、2025上市可交易、個人淨款、九起日期初權利及既有2884換股實際影響仍未知。完整行動減資及7/25後權息、直接復牌／可交易證據、台泥最後調整／最細稅源等缺口不因公司總數對帳而解除。其他0.8／0.7／正式0.4與歷史來源資格全保留。

所有原碼／策略參數／庫／資料／原件／舊頁成品／main保持，僅三根交接新增前綴。無UI／瀏覽器／Android新測，Raw／五年Adjusted／歷史公布／主檔／SQLite未知與research旗標不變。受拒入口／三舊403網域未重試／繞過，沒有部署、付費、交易、訊息或子代理。封包、manifest／新解壓及固定逐檔GitHub讀回以delivery實際收據為準。
