# 本輪實際工程、實測與限制

從a52cff2安全fast-forward至遠端f65a894，保留新增橋接附件8aecb50及其收據。根交接的「附件未收到」為先前歷史，本輪實際取得941229bytes原ZIP、SHA符合，41唯一成員／40manifest列項全部SHA、長度與CRC通過，並從固定GitHub raw獨立讀回全bytes相同。已全文讀包內CODEX_HANDOFF、REPORT、bridge-facts、prior_archive_readback及MANIFEST，再重新bootstrap成功（0補缺／7差異保留）才開始工程。沒有新worktree、平行寫入或子代理。

新增獨立offline_source_bridge純核心、offline_source_bridge_sources離線producer與新版本0.6。精確嵌入parent0.5及其正式0.4／parent0.3，原始catalog、所有舊輸出與原0.5 UNKNOWN保持。github_reference及原facts沒有覆蓋專案；前身大包91項是Work證詞，本輪實際驗的是橋接40項，兩者不混用。

實際讀取2停牌PDF、真實財政部API、官方頁面、2 script及搜尋回應，共7原件，不當7獨立事件。逐項核URL／原觀察時點／HTTP／長度／SHA，官方頁面實際連結與查詢meta綁定。本輪重新pdftotext25.03抽字及渲染兩份一頁PDF並視讀，文字SHA與封存逐位元相同、無抽字／渲染stderr。來源原captured_at與新ingested_at、obs.observed_at分存，announced_at仍null；沒有對任何受拒網域重抓來源。

新診斷證明1101從8/13、2884從11/5起暫停交易；只限明示起日，不將復牌提示當自動終點或推所有後續日。兩缺價日保留parent原UNKNOWN、Raw close null；新原因另記DIRECT_OFFICIAL_SUSPENSION_START_ON_DATE，市場session仍true、個股不可成交，execution_qualified=false、imputed／valuation仍null。缺價拒算不變。

真API接入前實際嘗試既有parse_mof_api，因真回應採101/08/17、舊合成parser預期101年8月17日而拒絕，compatibility-diagnostic保留。依授權新增獨立parser，不改原parser／原文字／容差。新parser核TaxAct／TaxVer／Title／Article／Terms／Subsection、Code及一筆Table、完整Content／函令；官方page／script／query／搜尋鏈相符。實際適用範圍限一般函釋，未核台泥最細來源或個人稅籍，稅／保費／匯費／淨額／實收全unknown。ViewCount變動測試只是對真回應拷貝做工程反例；原完整封存SHA不變，不冒稱新官網捕捉。

首輪91測試90通過、1失敗：變更PDF內文起日後，parser沒有同時核標題起日，未拒矛盾。保留tests-initial.log，修正為核所有「自…起暫停交易」日期一致且包含普通股內文；沒有更改原件或數字／策略。修正後30新＋本輪重跑61回歸＝91項實際通過，包含原件／metadata錯配與改bytes、issuer／instrument／日期角色、終點／其他日期不延伸、真API身分／內容／query錯配、來源與input完整旗標防升格、淨收／期初權利拒算、parent及舊成果保持。新解壓重驗另見delivery，不加總為182項不同測試。

producer在新版本實際重核122行情原件、16月報及70資格窗，仍70拒算、2不足、8換股影響未支援、真正總淨報酬合格0；assert所有daily／journal空、淨額null且未呼叫numeric replay，沒有六方案績效／排名。完整資料、淨到款與各研究起日期初權利等缺口不因來源解釋而解除。舊31／61之歷史與本輪重跑有明確區分，無關舊全套驗收未重跑。

新封包沿用原來源0.5包全部575成員逐位元，再追加新來源層、原橋接ZIP與證據；保存、manifest、可重現性及固定GitHub回讀以delivery收據為準。前代ZIP／橋接ZIP均保留，不用舊封包覆蓋完整checkout。

仍缺2884直接復牌、完整1101／2884行動減資及2026/7/25～10/16權息、2884直接2025可交易日／未圓整實配／畸零處置與既有股東換股影響、台泥最後調整與稅務細項、個人淨分配及九起日期初權利。一般法規不足以證個人免稅／零費用，媒體上市線索未升直接官方原件；員工、原2867及既有2884權利仍分開。Raw／五年Adjusted／歷史公布／主檔／SQLite未知保持。

無新UI、瀏覽器或Android實機驗收，Android NOT_TESTED_NEW_BUILD，交易／飛輪NOT_EVALUATED、historical_signal_eligible=false、primary_pressure_id=null、policy_authorized=false。全部禁止入口、三網域403及未套用草稿照舊；未部署、付費、交易、發訊息或啟動子代理，main保持。下一步Work唯讀補來源；已定工程仍回此既有唯一Codex。
