# 獨立決議來源契約0.4

1. 新catalog schema `rotation-resolution-catalog/0.4`嵌入逐位元語義相同的parent0.3，保留其ID、五來源版本與五原帳務組件。新加三來源版本：台泥通過決議、第六及第七次庫藏股報告。八版本不是八個獨立公司行動；提案與決議只連文件階段，不認證同一帳務事件的最終可用版本，也不默選較晚版本。
2. 離線producer先重建核等parent0.3，再核兩Work原件：固定URL／SHA／HTTP200／長度／meta與manifest／抽字雙指紋、HTMLParser真實href、57頁文字分隔、常會日期及第6～7頁第一討論案。來源標籤與總額／每股額／表決總數及94.64%重核；不借前一個特別股盈餘分配案的表決／圓整條款。未新增網路原件或重試任何阻擋。
3. approved_cash_per_share=0.8、approved_total_twd=5994545394及原文來源標籤只屬已通過決議。比率仍授權調整、基準與發放日另訂；final_cash_per_share、稅務細項、實際日期／投資人收款及net_per_share均null。會議日不作除息日／基準日／到款日；announced_at=null，歷史可知未認證。
4. resolve必指定catalog／來源版本、issuer、受領原股、instrument、事件類型、欄位、單位、日期角色與帶時區觀察截止。舊提案仍可明選，未知欄位拒用。新通過欄位也只允許來源診斷，FINAL_LEDGER不合格；不得以批准階段冒稱最後實配。
5. `preview_shareholder_cash`只接受明示`HYPOTHETICAL_ENTITLED_SHARES`、假設說明與版本綁定的整數權利股數字串（最多30位）。當前持股、成交量、空白或缺值不是權利證明。正數毛額先乘批准比率，再對每人總額捨去小於1元部分；保留餘額。例3股×0.8＝2.4→2元，不能將每股先捨去再累加，也不以2/3填通用每股淨額。
6. 顯式假想0股可有工程毛額0，但仍不認證零期初應收／零權利或零淨入帳；tax／fees／net／實收／實際日期／報酬維持null。輸出清楚標HYPOTHETICAL_APPROVED_RATIO_GROSS_ONLY，不是正式淨額模型，無稅籍適用推斷。
7. 第六次「無」僅THIS_TRANCHE；第七次28,000張已銷除保留原單位，生效日／每股轉換比／股東退資均未知。不取買回結束日作註銷生效，不將公司庫藏股消除寫入股東減資／現金帳。原兩缺價原因不推斷。
8. `refuse_accounting`是只有來源資格與拒算的adapter，沒有numeric replay路徑。明確綁新catalog、逐股驗全部新舊known IDs；原scope驗parent精確版本，並重用原qualify。來源catalog完整性不足不能被input完整旗標蓋掉；新版本新增圓整／淨帳不合格與庫藏股非股東減資的限制。後者是無生效日的來源資格觀察，不聲稱發生在特定研究窗。
9. 新資格實跑原72窗中70可研究窗，2窗仍40筆不足；70均拒算、8窗保留換股影響不支援，daily／journal空、所有淨報酬null。原帳replay／六方案0次、無排名。此adapter不聲稱支持完成資料後的成功淨帳路徑；需另有完整契約與實測才可新增。
10. 2884公開精度仍非未圓整／個人實配；2025可交易日及零股未知。完整行動／減資、7/25後權息、既有2884換股影響、淨分配與九研究起日期初權利仍缺。不補零、不公開私人券商／集保資料。
11. 保存原action_scope／source producer／official_actions／action_ledger／core／策略參數／庫／歷史／catalog／舊頁ZIP及main。無UI、無Android新驗收；Android NOT_TESTED_NEW_BUILD，圖形NOT_VALIDATED、交易／飛輪NOT_EVALUATED；policy_authorized=false、primary_pressure_id=null。全換／分批仍研究變數。
