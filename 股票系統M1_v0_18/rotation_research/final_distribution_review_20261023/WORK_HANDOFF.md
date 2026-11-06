# 完整續接／Codex工程指令

```text
接續blue1998-glitch/Twstockai，分支dev/m1-v018-chart-annotations。先查遠端最新，確認包含9e41ea3e444c19a8c62f95036312261602dc2542及其後final_distribution_review_20261023來源補核與GitHub回讀收據；保留983b3559及全部後續，不回退、不用main或舊ZIP覆蓋。最新已核提交見deliveries/m1-final-distribution-review-20261023/GITHUB_READBACK.md。
讀根AGENTS、CONTINUE_IN_WORK_MODE、PROJECT_VISION、M1_V019_GRAPH_CORE_RESUME_HANDOFF最新節；全文讀股票系統M1_v0_18/rotation_research/final_distribution_review_20261023的README、REPORT、facts、source-manifest、verification、preservation、prior-receipt-closure、visual-review、network-limitations、parsing-diagnostic、WORK_HANDOFF及delivery回讀收據，再讀action_scope_20261023原README／CONTRACT／REPORT／WORK_HANDOFF與events-v03。前輪事件帳／來源／日曆與所有保存契約繼續適用。
本輪Work取得台泥官方索引與57頁2026股東常會議事錄，PDF第1／4／6／7頁已實看。2026/5/22討論第一案決議通過：每股0.8、提撥5,994,545,394元、來源原文超過票面金額發行股票所得溢額，且保留比率調整及另訂基準／發放日授權。每人普通股現金總額至元以下捨去，非每股固定淨收0.8；個人淨額、稅費細項與到款仍未知。原0.3的BOARD_PROPOSAL是當時證據版本，不能覆寫。
新庫藏股盤點：第七次實際2025/8/14～8/25買回28,000張、報告已銷除28,000張；註銷生效日、對其他股東持股／現金流影響未知。不得變成每位股東按比率減資轉股或退資；第六次無註銷只屬該次，非全期間無減資。保持原兩缺價原因UNKNOWN，不推停牌原因。
工程交Codex，在實際完整checkout按最新AGENTS重新bootstrap --hydrate-missing成功後，只作獨立新來源producer／catalog版本：重新驗新原件SHA、官方索引真連結、PDF頁／段落與表決總數；新增股東會通過來源版本，保留0.3及舊ID／時間，不自動選較晚版本或倒填歷史可得。來源標籤與供稅模型的細項、每股比率與每人總額圓整、授權日期與實際入帳分開。
原action_scope.py／action_scope_sources.py／official_actions.py／action_ledger／core／策略參數／庫／歷史／舊catalog／舊頁與ZIP保持。若新每人總額圓整需不同固定輸入輸出，先做獨立明示契約，不把個人總額默除股數當通用net_per_share；缺原權利股數、稅費、到款或期初應收仍拒算。不預設零稅費／零權利，不公開私人券商集保資料。新庫藏股盤點只能帶來源與UNKNOWN影響，不能認證已支持減資／註銷會計或完整coverage。
原0.3先前24測試及70窗資格實跑是歷史。本輪Work未跑新引擎或資格，讀回原72窗為70拒算／2不足／8換股影響未支援，真正總淨報酬合格0。新工程只做必要定向實測與來源／未知防升格／圓整層級／不改舊成果核對；未測不能完成，沒有合格來源不得算六方案／排名或宣稱飛輪有效。不重問已答P0～P1／全換分批比例，不加策略門檻或自動下單。
仍優先補兩股完整行動／減資及7/25後權息、2884未圓整實配／2025可交易日／零股、換股對既有2884的影響、稅務細項法規／個人淨分配／期初權利。MOPS／TWT49U／TWT48U／TWTAUU307／file://／NHI403不重試繞過；本輪行政院公報PDF403也不換路徑重試。保留錯誤，其他獨立可讀官方來源才保存URL／時點／SHA／範圍，不用零命中、個別公告或衍生品調整證整段無事件。
Raw／五年Adjusted、歷史公布、主檔與SQLite未知保持；無新UI時不重開手機驗收，Android NOT_TESTED_NEW_BUILD、圖形NOT_VALIDATED、交易／飛輪NOT_EVALUATED，historical_signal_eligible=false、primary_pressure_id=null、policy_authorized=false。不部署付費交易訊息子代理、不改main。逐節點保存同分支、固定提交逐檔GitHub回讀，結束列實際完成／未完成、SHA／入口、最新已核提交、下一步Work或Codex並附完整指令。
```
