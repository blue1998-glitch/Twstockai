# 本輪取得、工程與實測

唯一既有Codex從遠端5a5ccab381b8fc37d2c0a869a653188aa8183d0a接續，唯讀核包含固定0.9工程1976b944b5abb92e18aad5f9ffe28afd23c5bc0c。沒有後續需合併；main仍9c5b168c09ba80010c74f03b9c537e8b7474256a。重新bootstrap實際成功0補缺／7差異保留後才工程。原3566追蹤檔在交接前綴更新前全數byte不變，既有未追蹤產物不動，保留結果見preservation.json。

Work本輪只研究；附件／meta本環境不可見，未取得／未讀，不要求手機搬檔。依使用者完整指令及庫內原索引href，兩新精確官方URL各一次GET，HTTP200，原件bytes／大小／SHA與Work報告的比對值一致。實際完整headers及要求／完成／捕捉存raw/*.meta.json；兩官方請求、零重導／重試、受拒端點請求0。未重抓舊公開說明書或Follow-up。acquisition-script.py僅保存實際取得命令，不是離線producer需要執行的步驟，也不得重跑舊拒絕入口。

實際pdftotext -layout／pdfinfo／pdftoppm轉五頁，全部return0，本次抽字與轉圖stderr空，未出現xref或Fontconfig警告；舊公開說明書xref歷史警告沒有抹除。議事錄原native為4bytes（四formfeed），四頁PNG均已視讀，不稱空白頁。表決1頁native及PNG已核。議事錄p1第二次與索引／路徑第一次矛盾保留，表決正文無場次；p4四列權數與表決原文全同。詳細掃描條款未做自動parser，p2／p3只人工盤點；未偽造OCR／native或湊精確策略欄位。

新增獨立純事實層subsidiary_proposal／離線producer及可反查JSON。不是只新增文件：對來源bytes／meta／圖／人工證據固定綁定；原生表決解析、同來源案例核對；issuer／子公司／instrument／公司持有人分離；只診斷用途與未知拒用；百分比角色、場次矛盾及時間角色防誤用；精確嵌完整parent0.9並委派資格拒算。兩文件只一來源案例，不當兩行動／市場樣本。

初次實際來源probe通過（parser-initial-diagnostic.json）；首輪24新測全過（tests-initial.log），最後24新＋實跑0.9相關29＝53通過（tests.log）。新增測試涵蓋來源／meta／native／圖竄改拒用、issuer／子公司／日期／持有人／instrument錯配、提案非完成、票百分比非配股／報酬、掃描空字、場次矛盾、人工對原生票數、公告與生效時間不互借、未可知截止、精確parent／null留史與完整旗標不能蓋缺口。合成竄改僅工程反例，非市場樣本。

實際命令：

```bash
python3 codex/bootstrap_m1.py --hydrate-missing
# 在股票系統M1_v0_18
python3 -m unittest rotation_research.test_subsidiary_proposal -v
python3 -m unittest rotation_research.test_subsidiary_proposal rotation_research.test_capital_components -v
python3 -m rotation_research.subsidiary_proposal_sources
```

producer按保存design與真實輸入重核122份價量原件／16份日曆，實際70資格呼叫全部REFUSED，2窗資料不足、8有換股影響未支援，合格總淨報酬窗0。daily／journal空，numeric replay及六方案0；統計由實際window rows計算，沒有硬編70／2／8。missing-quotes與parent精確相同，Raw null、舊UNKNOWN、execution_qualified=false、估值null不變。原60＝0.9的29新＋31回歸屬歷史，本輪沒冒稱重跑該組；新解壓同53不加總106。

執行輔助讀取舊資料時曾使用不存在的tests.json檔名，實際舊紀錄為tests.log；以及測試後顯示tail曾多加一層專案前綴，兩者僅讀取／顯示失誤，已改正、未改產品或原件，execution-diagnostic記錄。無來源取得／產品probe或產品測試失敗。

仍未完成：IPO實際完成／上市與日期數量、個人款股及帳務影響；議事錄詳細掃描條款自動解析；完整行動／7/25後權息、直接復牌／可交易、個人實配畸零與既有2884影響、台泥最後調整／最細稅源、個人淨收及九期初權利。沒有合法每日淨帳或新六方案績效，不借公司方案造績效。無新UI／瀏覽器／Android驗收，Android NOT_TESTED_NEW_BUILD保持。全部原策略參數／引擎／庫／資料／歷史／舊頁／舊成品及main保留；受拒入口不重試繞過。

可重現來源包／manifest／全新解壓實測與GitHub固定SHA逐檔原bytes讀回以delivery實際收據為準，沒有把本機成功或push文字代替遠端讀回。
