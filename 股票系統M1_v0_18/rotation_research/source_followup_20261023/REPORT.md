# 本輪實作與實測

起點4aca730f42a47f94cd8c5c411f5ae2b3fa25c2f2，保留2d2dbf1以來全部後續與前輪阻擋收據。使用者說已發布並授權再試；runtime spec4／observed4、observations_current=true，network state仍unknown，僅以三個精確URL的實際HTTP200證可讀。繼承代理與CA，無改主機／路徑、無redirect／自動重試、無TLS放寬；舊受拒來源未請求。bootstrap本輪重新成功，0補缺／7差異保留，見bootstrap.log。

三原件實際取得：

| 原件 | bytes | SHA256 | 本輪適用範圍 |
| --- | ---: | --- | --- |
| 期交所復牌公文 | 81441 | 9699a6d1349a1f4e14d78601af4874f724df5c24224dbe49906b1ce4ee712320 | p1：DN復牌主旨／說明二2884復牌佐證，非TWSE直接普通股公告 |
| 玉山併購完成新聞 | 103632 | 74c34ecf911d5bc6b994f4e8735e77f8da3770b043f4d5baefba3ef2cb4028ee | 公司報告完成，日期矛盾與股東權利未知保留 |
| 台泥115年第2季合併財報 | 3320224 | e8a8ca682a242180a908a68030dc80ee0321ddf92217586f59230b1d3e584d2d | 124頁保存，僅視讀7／52／54／55／57 |

兩PDF與Work比較SHA一致。HTML本次版本與Work SHA不同，全文bytes另存；不能判定未取得的Work bytes哪些位置不同，只核本次文章語義與已提供研究內容相符。沒有宣稱字節差異原因。來源URL／要求、完成、捕捉、讀回時點及Work原時點見source-manifest，各meta固定SHA，未倒填announced_at。

新增source_followup純事實／資格附層與離線producer、catalog-v07、五個角色觀察、精度比較及缺價關聯，精確嵌入parent0.6。新層不改舊UNKNOWN，不把TAIFEX佐證當TWSE直接公告。C的註銷月份及仟股單位、公司新聞完成／日期矛盾／董事會批准階段與保戶適用對象分開保存。原5,994,545,394元仍原值，財報5,994,545仟元只精度不同；不是最終調整或細項稅源證明。

實際命令與結果：

```bash
python3 codex/bootstrap_m1.py --hydrate-missing
# 以下在 股票系統M1_v0_18
python3 -m unittest rotation_research.test_source_followup -v
python3 -m unittest rotation_research.test_source_followup rotation_research.test_offline_source_bridge -v
python3 -m rotation_research.source_followup_sources
```

首輪29新測全通過，後續最終29新＋30相關回歸＝59全通過。中間澄清proof的normalized_value／原文指紋，以及summary欄名，不改來源事實；最終已重測，重跑不累加獨立測試項數。原前輪61／91不冒本輪全重跑。新定向測試涵蓋bytes／meta／來源／issuer／instrument／日期／單位錯配、TAIFEX不冒TWSE、公司完成不借個人、月份不變精確日、仟股／仟元與掃描空字、淨額／coverage／期初權利拒算及精確parent。

本輪離線producer實際重核122價量原件與16日曆報告，70資格呼叫全拒算、2不足、8窗換股影響未支援、真正總淨報酬0。daily／journal仍空、原numeric replay／六方案0，不是每日淨帳或新績效。新解壓同59測與producer見delivery package-verification，不加成118。實際原件native抽字兩PDFreturn0無stderr，6頁PNG本輪已視讀，非整本財報或瀏覽器驗收。

本輪沒有產品測試失敗。檔案定位曾錯猜catalog-v04.json及events-v04內observations，實際為正式嵌入inventory；只讀失敗後按rg結果修正，未改舊資料，見compatibility-diagnostic.json。開發中尚未交付的JSON proof／summary澄清前版本封存於本機scratch，最終producer輸出與封包定稿一致。

仍缺完整1101／2884公司行動減資及2026/7/25～10/16權息、2884直接TWSE復牌／2025可賣日／未圓整實配／畸零期限與處置／既有股東換股影響、台泥最後調整及最細資金來源、個人淨分配與九研究起日期初權利。缺資料未知／拒算，搜尋未找到不等無事件；私人券商／集保原件不公開。

Raw／五年Adjusted／歷史公布／主檔／SQLite未知與所有research旗標保持。沒有UI／Android／瀏覽器新測；沒有改策略或main、部署／付費／交易／訊息／子代理。原所有tracked成果核對及606舊封包成員保留詳見preservation與delivery。GitHub保存是否通過以固定GITHUB_READBACK收據為準。
