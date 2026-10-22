# 官方公司行動來源補充契約 0.2

1. 這是新producer official_actions.py及新schema rotation-action-catalog/0.2-issuer-supplement；原action_sources、action_ledger及所有原輸入／結果不變。先用原reader重核122份價量原件，再核原四份事件原件與五組件；只在新路徑寫出新事件表與窗口拒算紀錄。
2. 官方PDF必須由原已封存玉山股東資訊HTML實際連結，HTTPS指定issuer域、HTTP200、PDF格式、長度及SHA均核對。pdftotext衍生文字另有PDF／文字雙SHA及工具版本，不把文字當第二份獨立原始證據。人工或程式不得任意補原件內容。
3. 議事錄抽出實際會議日、盈餘年度、同次轉增資面額、發行額／股數並相互核算，另核通過決議與允許調整配股率的條文。議事錄「每千股約10股」是當次概數，不作最終直接比率。
4. 原2884最終公開每股股票股利金額0.10015129元／本次有來源面額10元，按Decimal導出0.010015129股／原股，保留原金額精度。這是**依公開金額精度推導**，不是已驗的未四捨五入精確配股比或投資人實配股數；不得由除權參考價反推或假設面額。新組件保留supersedes_event_id、原值、雙來源欄位定位與新指紋。
5. 原ex_date=2025-07-22、公司除權息基準日=2025-07-28、公司報告2025-08-27發放完畢分開。公司事後完成報告只支持公司層級執行情形，不能認證特定投資人已淨入帳、新股掛牌或可賣日。tradable_date、investor_receipt_at、net_amount仍null。
6. 本次決議有零股得合併、逾期未併按面額折現至元及現金股利元以下捨去的規定；只存政策證據。實際併湊期限、個人選擇／股數、淨稅費及入帳未核，不在原帳新增無來源的圓整或補貼。fractional_disposition保持null；不能把理論小數權利當已可賣零股。
7. 原件擷取時點是目前觀察證明，不是歷史公開可得時點。新組件observed_at取包含新PDF的最晚擷取時點，另保留original_component_observed_at；announced_at=null，historical_signal_eligible=false。會議日不是上傳公開時點。
8. 新來源擷取create-only、驗既存原件、不自動重試／跳轉、不改proxy或TLS。兩域加入runtime後才各查必要入口；MOPS雖HTTP200卻是明確安全拒絕頁，記為不可用來源，不當零事件名冊、不重試、不換路徑繞過、不載入其外部IP腳本。原TWT49U/TWT48U、TWTAUU歷史失敗及file://限制繼續保留。
9. 原coverage仍INCOMPLETE、other_actions_checked=false；2025-07-01～2026-10-16完整公司行動／減資、2026-07-25後權息、淨分配／期初權利未補完。新catalog只更新一組件的來源與ID，不把5組件說成已涵蓋所有事件。
10. 本輪重用原window_audit及已核官方日曆，70價格研究窗均仍REFUSED_INCOMPLETE_EVENT_ACCOUNTING，2窗不足；真正總淨報酬合格0、無每日真實淨資金路徑／六策略再算或排名。全換／分批／比例／觸發仍研究變數，primary_pressure_id=null、policy_authorized=false。Raw公司行動、五年Adjusted、歷史公布、主檔及SQLite未知持續；無瀏覽器／Android新驗收。
