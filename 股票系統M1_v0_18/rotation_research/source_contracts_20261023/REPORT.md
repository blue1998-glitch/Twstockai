# 本輪實際工程、證據與未完成項目

起點／遠端已核6a993fd336bfb78429eed1800893651a51f8f969，包含固定0.7工程6f16549ba1074200c2e08c15b79403b79969c9ce，保留所有後續，main仍9c5b168c09ba80010c74f03b9c537e8b7474256a。重新bootstrap成功，0補缺／7差異保留，之後才工程；Work沒有本輪bootstrap、工程或產品測試。

本環境實際可見附件只有既有v0.17交付檔；/tmp/codex-remote-attachments不存在，未見Twstockai-v07-Work-source-handoff報告／原件meta，因此未取得、未讀該完整研究報告，Work讀回時點未知。已按本輪使用者完整文字要求與可核官方原件完成可確定工程，未要求手機搬檔。詳見handoff-read-inventory.json；不是把指令或研究文件當產品已接入證據。

一份既存原件重用、一份新原件取得：

| 原件 | bytes | SHA256 | 本輪核閱 |
| --- | ---: | --- | --- |
| 既存玉山2026公開說明書 | 14607733 | 926f1f871a294702d3e4f5e4d89cf5aeb5e64808593efa2d99b95ed7375388fa | 固定GitHub回讀同bytes；實體162／163／175／176／461對印刷1／2／14／15／81 |
| 官方2026Follow-up.pdf | 56705 | 02899d55a0ce5431e3ec9787652a928fd5cc2d35abf56669942db52440e2fcdf | 精確URL一次GET，HTTP200，一頁抽字與視讀 |

公開說明書沒有再請求官方網站；原3:28捕捉與本輪9:31 Codex固定GitHub讀回分存。新一頁只請求使用者指定獨立URL一次，無redirect／retry，繼承代理／CA／TLS。舊被拒端點或三網域未重試。完整原件仍在舊raw路徑，metadata及xref stderr不覆。

新增source_contracts純事實核心、離線source producer與catalog-v08，精確parent0.7完整物件；七筆為角色觀察，不認證七個獨立事件。保存雙方異議條件及個人／修約未知；初始0.2486對後續0.2596分版本；原2867畸零、員工、既有2884分開；2025股東紅利、員工酬勞、混合新股總數分欄／單位。新一頁僅決議／核准，不解決0.7完成新聞日期矛盾。稅費契約不證免稅或個人淨入帳。

本輪實際命令：

```bash
python3 codex/bootstrap_m1.py --hydrate-missing
# 在 股票系統M1_v0_18
python3 -m unittest rotation_research.test_source_contracts -v
python3 -m unittest rotation_research.test_source_contracts rotation_research.test_source_followup -v
python3 -m rotation_research.source_contracts_sources
```

首輪31新測全通過；31新＋本輪實跑0.7相關29＝60項通過。舊59＝29＋30只歷史範圍，沒有本輪再跑0.6那30項；同60封包重驗不加總120。測試覆蓋真原件／meta／來源錯配、雙方條件、持有人／instrument、日期角色與精度、比率分版、股東／員工／總數單位、原件未知及parent保留；合成竄改僅反例，不是市場樣本。

producer由保存design／實際原價量／日曆重算資格：122價量原件、16市場日曆再核；70呼叫均拒算、2不足、8換股影響未支援、真正總淨報酬0。新測試另外以實際window rows重核統計，非把70等字串寫成結果。daily／journal空、原numeric replay／六方案0。missing-quotes副本精確等0.7，Raw null／舊UNKNOWN不覆。

本輪無產品測試失敗。原公開說明書五頁抽字與舊全文對應頁逐位元相同，所有抽字／轉圖return0；xref重建警告保持，未聲稱已修PDF。轉圖曾有Fontconfig無可寫快取警告；指定本任務XDG_CACHE_HOME重試後仍有部分警告，六頁PNG bytes與已視讀初圖全相同。原stderr與重試完整保留，沒有改HOME／代理／CA／系統設定；此非瀏覽器或Android驗收。765頁未全書視讀。PDF及任何原件未為通過格式檢查而改寫。

完整行動減資及2026/7/25～10/16權息、2884直接TWSE復牌／2025可交易日／個人未圓整實配／股利畸零期限與實際處置／既有股東換股影響、台泥最後調整／最細資金來源、個人淨分配與九研究起日期初權利仍缺。原件有條款不等個人具資格或已完成，空白不補零、搜尋無結果不等無事件，私人券商／集保原件不得公開。

原版本、原核心策略參數、庫／資料／歷史／原件／舊頁ZIP／main保持；Raw／五年Adjusted／歷史公布／主檔／SQLite未知，research旗標不變。無新UI／瀏覽器／Android，NOT_TESTED_NEW_BUILD不升格。不部署、付費、交易、發訊息或子代理。成品及固定提交逐檔回讀以delivery實際收據為準；未讀研究附件與來源缺口不標完成。
